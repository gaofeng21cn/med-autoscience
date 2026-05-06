# DeepScientist Adapter Decoupling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `DeepScientist` runtime / mailbox / paper-bundle 协议从 `med_autoscience.controllers` 中抽离到独立 adapter 层，降低 overlay 升级成本。

**Architecture:** 控制器继续负责医学规则判断、报告生成和干预策略；所有 quest 布局解析、`.ds` 协议读写、daemon control、paper bundle 发现统一下沉到 `src/med_autoscience/adapters/deepscientist/`。`runtime_watch` 只依赖控制器公开入口，不再自己理解 `.ds` 细节。

**Tech Stack:** Python 3.12, pytest, pathlib, dataclasses, urllib

---

## File Structure

- Create: `src/med_autoscience/adapters/__init__.py`
- Create: `src/med_autoscience/adapters/deepscientist/__init__.py`
- Create: `src/med_autoscience/adapters/deepscientist/runtime.py`
- Create: `src/med_autoscience/adapters/deepscientist/mailbox.py`
- Create: `src/med_autoscience/adapters/deepscientist/paper_bundle.py`
- Modify: `src/med_autoscience/controllers/publication_gate.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`
- Create: `tests/test_deepscientist_runtime_adapter.py`
- Create: `tests/test_deepscientist_mailbox_adapter.py`
- Create: `tests/test_deepscientist_paper_bundle_adapter.py`
- Modify: `tests/test_publication_gate.py`
- Modify: `tests/test_medical_publication_surface.py`
- Modify: `tests/test_runtime_watch.py`

### Task 1: 提取 runtime adapter

**Files:**
- Create: `src/med_autoscience/adapters/deepscientist/runtime.py`
- Test: `tests/test_deepscientist_runtime_adapter.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`

- [ ] **Step 1: 写失败测试，覆盖 runtime 状态读取和 active quest 发现**

```python
def test_load_runtime_state_reads_ds_runtime_json(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    dump_json(quest_root / ".ds" / "runtime_state.json", {"status": "running"})
    assert load_runtime_state(quest_root)["status"] == "running"


def test_iter_active_quests_filters_running_and_active(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_deepscientist_runtime_adapter.py`

Expected: `ModuleNotFoundError` 或 `AttributeError`

- [ ] **Step 3: 写最小实现**

```python
def load_runtime_state(quest_root: Path) -> dict[str, Any]: ...
def quest_status(quest_root: Path) -> str: ...
def iter_active_quests(runtime_root: Path) -> list[Path]: ...
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_deepscientist_runtime_adapter.py`

Expected: `passed`

- [ ] **Step 5: 改造 `runtime_watch` 只通过 adapter 读取 quest 状态**

### Task 2: 提取 mailbox / daemon adapter

**Files:**
- Create: `src/med_autoscience/adapters/deepscientist/mailbox.py`
- Test: `tests/test_deepscientist_mailbox_adapter.py`
- Modify: `src/med_autoscience/controllers/publication_gate.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`

- [ ] **Step 1: 写失败测试，覆盖消息入队、pending 计数更新、journal 追加**

```python
def test_enqueue_user_message_updates_queue_runtime_state_and_journal(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: 写失败测试，覆盖 daemon control POST**

```python
def test_post_quest_control_posts_json_payload(monkeypatch) -> None:
    ...
```

- [ ] **Step 3: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_deepscientist_mailbox_adapter.py`

Expected: `ModuleNotFoundError` 或断言失败

- [ ] **Step 4: 写最小实现**

```python
def enqueue_user_message(*, quest_root: Path, runtime_state: dict[str, Any], message: str, source: str = "cli") -> dict[str, Any]: ...
def post_quest_control(*, daemon_url: str, quest_id: str, action: str, source: str) -> dict[str, Any]: ...
```

- [ ] **Step 5: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_deepscientist_mailbox_adapter.py`

Expected: `passed`

- [ ] **Step 6: 改造两个 controller 复用 mailbox adapter**

### Task 3: 提取 paper bundle adapter

**Files:**
- Create: `src/med_autoscience/adapters/deepscientist/paper_bundle.py`
- Test: `tests/test_deepscientist_paper_bundle_adapter.py`
- Modify: `src/med_autoscience/controllers/publication_gate.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`

- [ ] **Step 1: 写失败测试，覆盖 paper root / paper bundle / submission minimal 解析**

```python
def test_resolve_latest_paper_root_prefers_latest_manifest(tmp_path: Path) -> None:
    ...


def test_resolve_submission_minimal_manifest_from_bundle_manifest(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_deepscientist_paper_bundle_adapter.py`

Expected: `ModuleNotFoundError` 或断言失败

- [ ] **Step 3: 写最小实现**

```python
def find_latest(paths: list[Path]) -> Path | None: ...
def resolve_latest_paper_root(quest_root: Path) -> Path: ...
def resolve_paper_bundle_manifest(quest_root: Path) -> Path | None: ...
def resolve_submission_minimal_manifest(paper_bundle_manifest_path: Path | None) -> Path | None: ...
```

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_deepscientist_paper_bundle_adapter.py`

Expected: `passed`

- [ ] **Step 5: 改造两个 controller 复用 paper bundle adapter**

### Task 4: 回归测试并做 CLI 验证

**Files:**
- Modify: `tests/test_publication_gate.py`
- Modify: `tests/test_medical_publication_surface.py`
- Modify: `tests/test_runtime_watch.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 更新现有 controller 测试，断言行为不变但耦合点移到 adapter**

- [ ] **Step 2: 跑全量 pytest**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q`

Expected: 全绿

- [ ] **Step 3: 跑一次真实 CLI dry-run**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src python3 -m med_autoscience.cli watch --runtime-root /Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/deepscientist/runtime/quests`

Expected: 正常输出 watch report，且不回归当前 blocker 检测

- [ ] **Step 4: 更新本轮状态说明**

包括：
- 已抽离哪些 adapter
- 仍残留哪些 policy / schema 耦合
- 下一轮该先做 `policies/` 外置还是 CLI 扩展
