# Runtime Boundary Convergence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 收紧 `med-autoscience -> med-deepscientist` 的 runtime 边界，让 controller 不再自己拼 daemon control 与反向 runtime 路径知识。

**Architecture:** 保持 `runtime_protocol` 负责本地 layout / quest 路径与状态读取，`runtime_transport` 负责 daemon URL 解析、quest control 与 live probe。controller 只调用更窄的协议/transport helper，不再直接知道 `quest_root.parent.parent`、`action="stop"` 之类的实现细节。

**Tech Stack:** Python 3.11, pytest, pathlib, urllib, yaml

---

## File Responsibilities

- `src/med_autoscience/runtime_protocol/layout.py`
  负责 workspace runtime layout 与反向路径解析 helper。
- `src/med_autoscience/runtime_transport/med_deepscientist.py`
  负责 daemon 解析、quest control helper 与 runtime inspection helper。
- `src/med_autoscience/runtime_transport/__init__.py`
  暴露新增的 transport helper。
- `src/med_autoscience/controllers/study_runtime_router.py`
  改为依赖 layout/runtime_root 与更窄的 transport helper。
- `src/med_autoscience/controllers/figure_loop_guard.py`
  改为通过 transport helper 停止 quest，不再自己拼 control request。
- `src/med_autoscience/controllers/medical_publication_surface.py`
  改为通过 transport helper 停止 quest，不再直接知道 control action。
- `tests/test_runtime_protocol_layout.py`
  锁定新的 layout 反向解析 helper。
- `tests/test_runtime_transport_med_deepscientist.py`
  锁定新的 transport helper 与 runtime inspection 行为。
- `tests/test_figure_loop_guard.py`
  锁定 figure guard 改走 `stop_quest` helper。
- `tests/test_medical_publication_surface.py`
  锁定 publication surface 改走 `stop_quest` helper。
- `tests/test_study_runtime_router.py`
  锁定 router 统一走 layout/runtime_root 与 runtime inspection helper。

### Task 1: 写失败测试，钉死新的 runtime helper 边界

**Files:**
- Modify: `tests/test_runtime_protocol_layout.py`
- Modify: `tests/test_runtime_transport_med_deepscientist.py`
- Modify: `tests/test_figure_loop_guard.py`
- Modify: `tests/test_medical_publication_surface.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] **Step 1: 为 layout 增加反向路径解析测试**

```python
def test_resolve_runtime_root_from_quest_root_returns_workspace_runtime_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.layout")
    quest_root = tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests" / "study-001"

    result = module.resolve_runtime_root_from_quest_root(quest_root)

    assert result == tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime"
```

- [ ] **Step 2: 为 transport 新 helper 写失败测试**

```python
def test_stop_quest_posts_stop_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_post_quest_control(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "status": "stopped"}

    monkeypatch.setattr(module, "post_quest_control", fake_post_quest_control)

    result = module.stop_quest(runtime_root=runtime_root, quest_id="q001", source="test")

    assert result == {"ok": True, "status": "stopped"}
    assert seen == {
        "runtime_root": runtime_root,
        "quest_id": "q001",
        "action": "stop",
        "source": "test",
    }
```

```python
def test_inspect_quest_runtime_reads_local_status_and_live_sessions(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    quest_root.mkdir(parents=True)

    monkeypatch.setattr(module.quest_state, "quest_status", lambda path: "running")
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda *, runtime_root, quest_id, timeout=10: {
            "ok": True,
            "status": "live",
            "live_session_count": 1,
            "live_session_ids": ["sess-1"],
        },
    )

    result = module.inspect_quest_runtime(
        runtime_root=tmp_path / "runtime",
        quest_root=quest_root,
        quest_id="q001",
    )

    assert result["quest_exists"] is True
    assert result["quest_status"] == "running"
    assert result["bash_session_audit"]["status"] == "live"
```

- [ ] **Step 3: 为 controller 调用面改走 helper 写失败测试**

```python
def test_run_controller_uses_stop_quest_helper(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.figure_loop_guard")
    quest_root, outbox_path = make_quest(tmp_path)
    seen: list[tuple[str | None, str, str]] = []

    monkeypatch.setattr(
        module.med_deepscientist_transport,
        "stop_quest",
        lambda *, daemon_url=None, runtime_root=None, quest_id, source: seen.append(
            (str(runtime_root) if runtime_root else None, quest_id, source)
        ) or {"ok": True, "status": "stopped"},
    )

    module.run_controller(
        quest_root=quest_root,
        apply=True,
        outbox_path=outbox_path,
        daemon_url="http://127.0.0.1:20999",
        accepted_figures={"F4B": "teacher approved final layout"},
        figure_tickets={"F3C": "text overflow outside panel boxes"},
        required_routes=["literature_scout", "expand_references", "revise_manuscript_body"],
        min_figure_mentions=3,
        min_reference_count=12,
    )

    assert seen == [(None, "002-early-residual-risk", "medautosci-figure-loop-guard")]
```
```

- [ ] **Step 4: 跑定向测试并确认先红**

Run: `uv run pytest tests/test_runtime_protocol_layout.py tests/test_runtime_transport_med_deepscientist.py tests/test_figure_loop_guard.py tests/test_medical_publication_surface.py tests/test_study_runtime_router.py -q`

Expected: 新增测试失败，失败原因是 helper 尚不存在或 controller 仍调用旧接口。

### Task 2: 实现 protocol/transport helper，并收 controller 调用面

**Files:**
- Modify: `src/med_autoscience/runtime_protocol/layout.py`
- Modify: `src/med_autoscience/runtime_protocol/__init__.py`
- Modify: `src/med_autoscience/runtime_transport/med_deepscientist.py`
- Modify: `src/med_autoscience/runtime_transport/__init__.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `src/med_autoscience/controllers/figure_loop_guard.py`
- Modify: `src/med_autoscience/controllers/medical_publication_surface.py`

- [ ] **Step 1: 在 layout 中新增反向 runtime 路径 helper**

```python
def resolve_runtime_root_from_quest_root(quest_root: Path) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    return resolved_quest_root.parent.parent
```

- [ ] **Step 2: 在 transport 中新增 `stop_quest` 与 `inspect_quest_runtime`**

```python
def stop_quest(
    *,
    quest_id: str,
    source: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    return post_quest_control(
        quest_id=quest_id,
        action="stop",
        source=source,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
    )
```

```python
def inspect_quest_runtime(*, runtime_root: Path, quest_root: Path, quest_id: str) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    quest_exists = (resolved_quest_root / "quest.yaml").exists()
    quest_status_value = quest_state.quest_status(resolved_quest_root) if quest_exists else ""
    result = {
        "quest_exists": quest_exists,
        "quest_status": quest_status_value or None,
    }
    if quest_status_value in {"running", "active"}:
        result["bash_session_audit"] = inspect_quest_live_bash_sessions(
            runtime_root=runtime_root,
            quest_id=quest_id,
        )
    return result
```

- [ ] **Step 3: 用新 helper 收口 controller**

```python
runtime_root = layout.runtime_root
quest_runtime = med_deepscientist_transport.inspect_quest_runtime(
    runtime_root=runtime_root,
    quest_root=quest_root,
    quest_id=quest_id,
)
```

```python
stop_result = med_deepscientist_transport.stop_quest(
    quest_id=state.quest_id,
    source=source,
    daemon_url=daemon_url,
    runtime_root=resolve_runtime_root_from_quest_root(state.quest_root),
)
```

- [ ] **Step 4: 跑定向测试并确认转绿**

Run: `uv run pytest tests/test_runtime_protocol_layout.py tests/test_runtime_transport_med_deepscientist.py tests/test_figure_loop_guard.py tests/test_medical_publication_surface.py tests/test_study_runtime_router.py -q`

Expected: 全部 PASS。

### Task 3: 回归关键 runtime 面并确认没有退化

**Files:**
- Modify: `docs/superpowers/plans/2026-04-02-runtime-boundary-convergence.md`

- [ ] **Step 1: 跑主回归集合**

Run: `uv run pytest tests/test_profiles.py tests/test_overlay_installer.py tests/test_workspace_contracts.py tests/test_workspace_init.py tests/test_study_runtime_router.py tests/test_runtime_watch.py tests/test_medical_startup_contract_support.py tests/test_runtime_protocol_topology.py tests/test_cli.py tests/test_mcp_server.py tests/test_submission_targets.py tests/test_submission_targets_controller.py tests/test_runtime_transport_med_deepscientist.py tests/test_runtime_protocol_layout.py tests/test_figure_loop_guard.py tests/test_medical_publication_surface.py -q`

Expected: 全部 PASS。

- [ ] **Step 2: 精确扫描 runtime 散点是否减少**

Run: `rg -n "quest_root\\.parent\\.parent|post_quest_control\\(|action=\\\"stop\\\"|resolve_daemon_url\\(" src/med_autoscience/controllers src/med_autoscience/runtime_protocol src/med_autoscience/runtime_transport`

Expected: controller 不再自己拼 `quest_root.parent.parent`，`figure_loop_guard.py` 与 `medical_publication_surface.py` 不再直接调用 `post_quest_control(..., action=\"stop\", ...)`。

- [ ] **Step 3: 记录结果并提交**

```bash
git add docs/superpowers/plans/2026-04-02-runtime-boundary-convergence.md \
  src/med_autoscience/runtime_protocol/layout.py \
  src/med_autoscience/runtime_protocol/__init__.py \
  src/med_autoscience/runtime_transport/med_deepscientist.py \
  src/med_autoscience/runtime_transport/__init__.py \
  src/med_autoscience/controllers/study_runtime_router.py \
  src/med_autoscience/controllers/figure_loop_guard.py \
  src/med_autoscience/controllers/medical_publication_surface.py \
  tests/test_runtime_protocol_layout.py \
  tests/test_runtime_transport_med_deepscientist.py \
  tests/test_figure_loop_guard.py \
  tests/test_medical_publication_surface.py \
  tests/test_study_runtime_router.py
git commit -m "refactor: converge runtime boundary helpers"
```
