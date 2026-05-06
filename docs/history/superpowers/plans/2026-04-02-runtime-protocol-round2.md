# Runtime Protocol Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 继续把 `med-autoscience` 内部仍散落在 controller 里的 runtime 落盘协议与 watch 状态协议下沉到 `runtime_protocol`。

**Architecture:** 新增 `runtime_protocol.study_runtime` 负责 study runtime 的路径、binding、launch report 和 invalid partial quest recovery；新增 `runtime_protocol.runtime_watch` 负责 watch state/report 落盘与 apply/suppress 状态机。controller 保留医学策略与 fingerprint 语义，不再手写 runtime schema/path/state transition。

**Tech Stack:** Python 3.11, pytest, pathlib, json, yaml

---

## File Responsibilities

- `src/med_autoscience/runtime_protocol/study_runtime.py`
  负责 study-runtime 路径解析、binding 写入、launch report 写入、invalid partial quest recovery。
- `src/med_autoscience/runtime_protocol/runtime_watch.py`
  负责 watch state 读写、时间戳报告落盘、controller intervention transition 计算。
- `src/med_autoscience/runtime_protocol/__init__.py`
  暴露新增 helper。
- `src/med_autoscience/controllers/study_runtime_router.py`
  改为调用 `runtime_protocol.study_runtime`，不再自己手写 runtime binding / launch report schema。
- `src/med_autoscience/controllers/runtime_watch.py`
  改为调用 `runtime_protocol.runtime_watch`，不再直接依赖 `adapters.report_store` 与 intervention 状态机细节。
- `tests/test_runtime_protocol_study_runtime.py`
  锁定 study runtime protocol helper。
- `tests/test_runtime_protocol_runtime_watch.py`
  锁定 watch protocol helper。
- `tests/test_study_runtime_router.py`
  锁定 router 改走 protocol helper 后行为不变。
- `tests/test_runtime_watch.py`
  锁定 watch 改走 protocol helper 后行为不变。

### Task 1: 写失败测试，定义新 protocol helper

**Files:**
- Create: `tests/test_runtime_protocol_study_runtime.py`
- Create: `tests/test_runtime_protocol_runtime_watch.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `tests/test_runtime_watch.py`

- [ ] **Step 1: 给 study runtime helper 写失败测试**

```python
def test_write_runtime_binding_writes_protocol_schema(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    binding_path = tmp_path / "study" / "runtime_binding.yaml"

    module.write_runtime_binding(
        runtime_binding_path=binding_path,
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
        study_id="001-risk",
        study_root=tmp_path / "study",
        quest_id="001-risk",
        last_action="resume",
        source="test-source",
        recorded_at="2026-04-02T12:00:00+00:00",
    )

    payload = yaml.safe_load(binding_path.read_text(encoding="utf-8"))
    assert payload["runtime_root"].endswith("/ops/med-deepscientist/runtime")
    assert payload["last_action"] == "resume"
```

```python
def test_archive_invalid_partial_quest_root_moves_broken_quest_into_recovery_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    runtime_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    quest_root.mkdir(parents=True)

    result = module.archive_invalid_partial_quest_root(
        quest_root=quest_root,
        runtime_root=runtime_root,
        slug="20260402T120000Z",
    )

    assert result["status"] == "archived_invalid_partial_quest_root"
```

- [ ] **Step 2: 给 runtime watch helper 写失败测试**

```python
def test_plan_controller_intervention_applies_once_and_persists_fingerprint() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")

    result = module.plan_controller_intervention(
        previous_controller_state={},
        dry_run_result={"status": "blocked", "blockers": ["b1"]},
        fingerprint="fp-1",
        apply=True,
        scanned_at="2026-04-02T12:00:00+00:00",
        intervention_statuses={"blocked"},
    )

    assert result["action"] == "apply"
    assert result["controller_state"]["last_applied_fingerprint"] == "fp-1"
```

```python
def test_write_watch_report_uses_runtime_protocol_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.runtime_watch")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    report = {"scanned_at": "2026-04-02T12:00:00+00:00", "quest_root": str(quest_root), "quest_status": "running"}

    json_path, md_path = module.write_watch_report(
        quest_root=quest_root,
        report=report,
        markdown="# Report\n",
    )

    assert json_path.name == "2026-04-02T120000Z.json"
    assert md_path.name == "2026-04-02T120000Z.md"
```

- [ ] **Step 3: 跑定向测试并确认先红**

Run: `uv run pytest tests/test_runtime_protocol_study_runtime.py tests/test_runtime_protocol_runtime_watch.py tests/test_study_runtime_router.py tests/test_runtime_watch.py -q`

Expected: FAIL，原因是 helper 尚不存在或 controller 仍内联实现协议细节。

### Task 2: 实现 protocol helper 并收 controller

**Files:**
- Create: `src/med_autoscience/runtime_protocol/study_runtime.py`
- Create: `src/med_autoscience/runtime_protocol/runtime_watch.py`
- Modify: `src/med_autoscience/runtime_protocol/__init__.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`

- [ ] **Step 1: 实现 study_runtime helper**

```python
def resolve_study_runtime_paths(*, profile: WorkspaceProfile, study_root: Path, study_id: str, quest_id: str) -> dict[str, Path]:
    ...
```

```python
def write_runtime_binding(..., recorded_at: str) -> None:
    ...
```

```python
def write_launch_report(..., recorded_at: str) -> None:
    ...
```

```python
def archive_invalid_partial_quest_root(..., slug: str) -> dict[str, Any] | None:
    ...
```

- [ ] **Step 2: 实现 runtime_watch helper**

```python
def load_watch_state(quest_root: Path) -> dict[str, Any]:
    ...
```

```python
def plan_controller_intervention(...) -> dict[str, Any]:
    ...
```

```python
def write_watch_report(...) -> tuple[Path, Path]:
    ...
```

- [ ] **Step 3: controller 改走新 helper**

```python
paths = study_runtime_protocol.resolve_study_runtime_paths(...)
partial_quest_recovery = study_runtime_protocol.archive_invalid_partial_quest_root(...)
study_runtime_protocol.write_runtime_binding(...)
study_runtime_protocol.write_launch_report(...)
```

```python
current_state = runtime_watch_protocol.load_watch_state(quest_root)
transition = runtime_watch_protocol.plan_controller_intervention(...)
runtime_watch_protocol.save_watch_state(...)
runtime_watch_protocol.write_watch_report(...)
```

- [ ] **Step 4: 跑定向测试并确认转绿**

Run: `uv run pytest tests/test_runtime_protocol_study_runtime.py tests/test_runtime_protocol_runtime_watch.py tests/test_study_runtime_router.py tests/test_runtime_watch.py -q`

Expected: 全部 PASS。

### Task 3: 跑回归并确认散点减少

**Files:**
- Modify: `docs/superpowers/plans/2026-04-02-runtime-protocol-round2.md`

- [ ] **Step 1: 跑主回归集合**

Run: `uv run pytest tests/test_profiles.py tests/test_overlay_installer.py tests/test_workspace_contracts.py tests/test_workspace_init.py tests/test_study_runtime_router.py tests/test_runtime_watch.py tests/test_medical_startup_contract_support.py tests/test_runtime_protocol_topology.py tests/test_cli.py tests/test_mcp_server.py tests/test_submission_targets.py tests/test_submission_targets_controller.py tests/test_runtime_transport_med_deepscientist.py tests/test_runtime_protocol_layout.py tests/test_runtime_protocol_study_runtime.py tests/test_runtime_protocol_runtime_watch.py tests/test_figure_loop_guard.py tests/test_medical_publication_surface.py -q`

Expected: 全部 PASS。

- [ ] **Step 2: 精确扫描 controller 散点**

Run: `rg -n "report_store|_write_runtime_binding|_write_launch_report|_recover_invalid_partial_quest_root|load_watch_state|save_watch_state|write_watch_report" src/med_autoscience/controllers src/med_autoscience/runtime_protocol`

Expected: `runtime_watch.py` 不再直接依赖 `adapters.report_store`；`study_runtime_router.py` 不再保留上述内部 helper。
