# Delivery Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add an independent, screenshot-free delivery workflow with atomic browser operations, DOM assertions, fail-fast sequencing, and structured ledger output.

**Architecture:** `browser_ops.py` exposes one browser action or observation per method. `assertions.py` validates observations without side effects. `runner.py` composes those primitives into a per-job state machine and never calls image upload before greeting assertions pass.

**Tech Stack:** Python 3.8+, DrissionPage-compatible adapter, pytest, JSONL/JSON ledgers.

**Spec:** `docs/superpowers/specs/2026-09-20-delivery-workflow-design.md`

## Global Constraints

- `apply.py` remains unchanged and is not called by the new runner.
- No screenshots are captured or required for any decision.
- Browser methods perform one action or one read only.
- Greeting success is required before image upload; both are required before success ledger writes.

### Task 1: Workflow contracts and browser adapter

**Files:**
- Create: `scripts/delivery_workflow/__init__.py`
- Create: `scripts/delivery_workflow/exceptions.py`
- Create: `scripts/delivery_workflow/models.py`
- Create: `scripts/delivery_workflow/browser_ops.py`
- Test: `tests/test_delivery_workflow_contracts.py`

- [ ] Define dataclasses for `JobContext`, `Message`, `ChatSnapshot`, and `JobResult`.
- [ ] Define workflow exception classes.
- [ ] Implement `BrowserOps` protocol-like base class and `DrissionBrowserOps` adapter with one-action methods.
- [ ] Add mock-contract tests proving observations and actions are independently callable.

### Task 2: Observers, assertions, and ledger

**Files:**
- Create: `scripts/delivery_workflow/observers.py`
- Create: `scripts/delivery_workflow/assertions.py`
- Create: `scripts/delivery_workflow/ledger.py`
- Test: `tests/test_delivery_workflow_assertions.py`

- [ ] Implement pure helpers for button classification, greeting verification, image verification, and duplicate detection.
- [ ] Implement JSONL event logging and success-only `applied_history.json` updates.
- [ ] Test failed greeting/image assertions and verify no screenshot path is referenced.

### Task 3: Independent runner and state machine

**Files:**
- Create: `scripts/delivery_workflow/runner.py`
- Test: `tests/test_delivery_workflow_runner.py`

- [ ] Implement per-job state transitions, one greeting retry, skip states, and batch-level daily-limit stop.
- [ ] Enforce that upload is not invoked after greeting failure.
- [ ] Add CLI parsing for run directory, job JSON, image path, dry-run, and `--only` selection.
- [ ] Add runner mock tests for success, greeting failure, image failure, duplicate skip, and daily limit.

### Task 4: Verification

- [ ] Run focused delivery workflow tests.
- [ ] Run the existing test suite relevant to history and apply contracts.
- [ ] Confirm `git diff` contains no `apply.py` changes and no screenshot implementation.
