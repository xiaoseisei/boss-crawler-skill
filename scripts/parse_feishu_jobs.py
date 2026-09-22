#!/usr/bin/env python3
"""
解析飞书多维表格抓取到的数据包，完整还原字段映射（含单选/多选字典翻译）与职位投递数据，并导出为 JSON 与 CSV。
"""

import os
import sys
import json
import base64
import gzip
import csv
from pathlib import Path

DATA_FILE = Path("assets/feishu_data/feishu_raw_data.json")
OUTPUT_JSON = Path("assets/feishu_data/campus_jobs.json")
OUTPUT_CSV = Path("assets/feishu_data/campus_jobs.csv")

def decompress_if_needed(val):
    if isinstance(val, str) and val.startswith("H4sI"):
        try:
            raw = gzip.decompress(base64.b64decode(val)).decode("utf-8")
            return json.loads(raw)
        except Exception:
            return val
    elif isinstance(val, str):
        try:
            return json.loads(val)
        except Exception:
            return val
    return val

def build_field_and_options_map(packets):
    field_map = {}       # fid -> field_name
    options_map = {}     # fid -> {opt_id: opt_name}

    for p in packets:
        if "clientvars" in p["url"]:
            data_body = p.get("data", {}).get("data", {})
            if "table" in data_body:
                table_obj = decompress_if_needed(data_body["table"])
                if isinstance(table_obj, dict):
                    fm = table_obj.get("fieldMap", {})
                    for fid, finfo in fm.items():
                        name = finfo.get("name", fid)
                        field_map[fid] = name
                        # 处理单选/多选选项字典
                        opts = finfo.get("property", {}).get("options", [])
                        if isinstance(opts, list):
                            options_map[fid] = {opt["id"]: opt.get("name", opt["id"]) for opt in opts if "id" in opt}
            break
    return field_map, options_map

def extract_field_value(cell_dict, fid, options_map):
    if not cell_dict or not isinstance(cell_dict, dict):
        return ""
    
    val = cell_dict.get("value")
    if val is None:
        return ""
    
    # 1. 如果是选项 ID 或者是选项列表 (单选/多选)
    opt_dict = options_map.get(fid, {})
    if isinstance(val, str) and val in opt_dict:
        return opt_dict[val]
    
    if isinstance(val, list):
        parts = []
        for item in val:
            if isinstance(item, str) and item in opt_dict:
                parts.append(opt_dict[item])
            elif isinstance(item, dict):
                # 链接或富文本: {'text': '...', 'link': '...', 'type': 'url'}
                link = item.get("link")
                text = item.get("text")
                if link:
                    parts.append(link)
                elif text:
                    parts.append(text)
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return " ".join(parts).strip()

    if isinstance(val, dict):
        return str(val.get("link") or val.get("text") or val).strip()

    return str(val).strip()

def main():
    if not DATA_FILE.exists():
        print(f"[-] 数据文件不存在: {DATA_FILE}")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        packets = json.load(f)

    field_map, options_map = build_field_and_options_map(packets)

    print(f"[+] 识别到字段映射 ({len(field_map)} 个字段):")
    for fid, fname in field_map.items():
        opts_count = len(options_map.get(fid, {}))
        opt_hint = f" (包含 {opts_count} 个枚举项)" if opts_count > 0 else ""
        print(f"    - {fid}: {fname}{opt_hint}")

    all_record_map = {}
    
    for p in packets:
        url = p["url"]
        # 来自 clientvars 的初始记录
        if "clientvars" in url:
            data_body = p.get("data", {}).get("data", {})
            if "table" in data_body:
                table_obj = decompress_if_needed(data_body["table"])
                if isinstance(table_obj, dict):
                    rm = table_obj.get("recordMap", {})
                    all_record_map.update(rm)

        # 来自 records 接口的分批记录
        if "/records?" in url:
            data_body = p.get("data", {}).get("data", {})
            if "records" in data_body:
                records_obj = decompress_if_needed(data_body["records"])
                if isinstance(records_obj, dict):
                    rm = records_obj.get("recordMap", {})
                    all_record_map.update(rm)

    print(f"\n[+] 累计抓取并去重后的总岗位数: {len(all_record_map)} 条")

    # 规范表头顺序
    field_names = [
        "公司名称", "招聘岗位", "岗位链接", "招聘公告", "工作地点", 
        "招聘类型", "招聘届别", "行业类别", "公司规模", "公司类型", 
        "截止日期", "笔试信息", "更新时间"
    ]
    extra_names = [name for name in field_map.values() if name not in field_names]
    all_headers = field_names + extra_names

    job_list = []
    for rid, raw_record in all_record_map.items():
        row = {}
        for fid, fname in field_map.items():
            cell_data = raw_record.get(fid)
            row[fname] = extract_field_value(cell_data, fid, options_map)
        
        cleaned_row = {col: row.get(col, "") for col in all_headers}
        job_list.append(cleaned_row)

    # 过滤与统计
    valid_links = [j for j in job_list if j.get("岗位链接") and j.get("岗位链接").startswith("http")]
    print(f"[+] 其中有效投递链接数: {len(valid_links)} 条")

    # 保存 JSON
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(job_list, f, ensure_ascii=False, indent=2)
    print(f"[+] JSON 导出成功: {OUTPUT_JSON}")

    # 保存 CSV
    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_headers)
        writer.writeheader()
        writer.writerows(job_list)
    print(f"[+] CSV 导出成功: {OUTPUT_CSV}")

    # 打印前 5 条样本
    print("\n[+] 真实数据样本 (前 5 条有效网申岗位):")
    for i, j in enumerate(valid_links[:5]):
        print(f"[{i+1}] 公司: {j.get('公司名称')} | 岗位: {j.get('招聘岗位')}")
        print(f"    地点: {j.get('工作地点')} | 届别: {j.get('招聘届别')} | 类型: {j.get('招聘类型')}")
        print(f"    投递链接: {j.get('岗位链接')}")
        print("-" * 60)

if __name__ == "__main__":
    main()
