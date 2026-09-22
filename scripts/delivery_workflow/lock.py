"""工作流进程互斥锁模块。

用于防止多个工作流实例同时操作同一个浏览器环境或聊天会话造成冲突。
通过文件排他锁与 PID 进程存活探测实现自动孤儿锁（Stale Lock）回收。
"""
import json
import os
import time


class WorkflowLock:
    """基于文件排他锁和 PID 存活检测的单实例运行互斥锁。
    
    支持作为上下文管理器（with 语句）使用。
    """
    
    def __init__(self, run_dir: str):
        """初始化互斥锁。
        
        Args:
            run_dir: 当前批次运行输出目录，锁文件将存放在该目录下。
        """
        self.path = os.path.join(run_dir, '.delivery_workflow.lock')
        self.held = False

    def acquire(self) -> None:
        """获取互斥锁。
        
        利用底层操作系统的原子性创建文件（O_CREAT | O_EXCL）实现安全加锁。
        若锁文件已存在，则读取其中的 PID 并探测该进程是否存活：
        - 若持有锁的进程已终止（孤儿锁/僵尸锁），则自动清理并重新抢锁；
        - 若持有锁的进程仍然存活，则拒绝并发，抛出 RuntimeError。
        
        Raises:
            RuntimeError: 当检测到已有存活的投递实例正在运行，或锁被其他进程并发修改时抛出。
        """
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        payload = {'pid': os.getpid(), 'started_at': time.time()}
        try:
            # 使用 O_CREAT | O_EXCL 实现原子性创建，若文件已存在则触发 FileExistsError
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            stale = False
            try:
                with open(self.path, encoding='utf-8') as f:
                    old = json.load(f)
                pid = int(old.get('pid', 0))
                if pid <= 0:
                    stale = True
                else:
                    # 探测对应 PID 是否仍存活；若不存在或已退出会引发 OSError
                    os.kill(pid, 0)
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                # 读取失败、JSON 损坏或进程已不存在，视为残留的孤儿锁
                stale = True
                
            if stale:
                try:
                    os.remove(self.path)
                except OSError:
                    raise RuntimeError('workflow 锁正在被其他进程更新')
                # 递归重新尝试抢占锁
                return self.acquire()
            raise RuntimeError('已有 workflow 实例正在运行，拒绝并发投递')

        # 抢锁成功，写入当前进程 PID 和启动时间戳
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
        self.held = True

    def release(self) -> None:
        """释放当前持有的互斥锁并清理锁文件。"""
        if self.held:
            try:
                os.remove(self.path)
            except FileNotFoundError:
                pass
            self.held = False

    def __enter__(self):
        """上下文管理器入口：获取锁并返回 self。"""
        self.acquire()
        return self

    def __exit__(self, exc_type, exc, tb):
        """上下文管理器出口：退出时自动释放锁。"""
        self.release()

