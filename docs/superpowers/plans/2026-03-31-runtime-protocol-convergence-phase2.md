# Runtime Protocol Convergence Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `MedAutoScience` 当前散落在 controller 和 adapter 里的 `DeepScientist` 布局/状态假设收口成显式 `runtime protocol` 层，为后续去掉 `deepscientist adapter` 做准备。

**Architecture:** Phase 2 不替换执行引擎，也不改变 `MedicalDeepScientist` 现有 daemon API / quest 布局。它只做一件事：把 `quest_root`、active worktree、paper root、main result、stdout、paper bundle、submission package 等路径与状态解析，集中到新的 `runtime_protocol` 帮助层中，然后让 `publication_gate`、`runtime_watch`、`study_delivery_sync`、`study_runtime_router` 这些调用点改为依赖协议层，而不是自己拼 `.ds/...` 路径。这样 adapter 会退化为 transport / engine shim，协议真相则上移到 `MedAutoScience`。

**Tech Stack:** Python 3.12, `dataclasses`, `pathlib`, `json`, pytest, existing controllers, existing `adapters/deepscientist/*`

---

## File Structure

- Create: `src/med_autoscience/runtime_protocol/__init__.py`
- Create: `src/med_autoscience/runtime_protocol/topology.py`
- Create: `src/med_autoscience/runtime_protocol/quest_state.py`
- Create: `tests/test_runtime_protocol_topology.py`
- Create: `tests/test_runtime_protocol_quest_state.py`
- Modify: `src/med_autoscience/adapters/deepscientist/runtime.py`
- Modify: `src/med_autoscience/controllers/publication_gate.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`
- Modify: `src/med_autoscience/controllers/study_delivery_sync.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `tests/test_publication_gate.py`
- Modify: `tests/test_runtime_watch.py`
- Modify: `tests/test_study_delivery_sync.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/workspace_architecture.md`

说明：

- 本计划不做 engine-neutral transport 抽象；transport 仍由 `adapters/deepscientist/*` 负责。
- 本计划不重命名 `deepscientist_repo_root`。
- 本计划不改变 `MedicalDeepScientist` 的 quest/worktree/paper/result 目录实际形状，只把这些形状提升为 `MedAutoScience` 明确管理的协议。

### Task 1: 提取 runtime topology 协议层

**Files:**
- Create: `src/med_autoscience/runtime_protocol/topology.py`
- Create: `tests/test_runtime_protocol_topology.py`
- Modify: `src/med_autoscience/controllers/study_delivery_sync.py`

- [ ] **Step 1: 写失败测试，覆盖 quest/worktree/paper/study 根路径解析**

```python
from __future__ import annotations

from pathlib import Path

from med_autoscience.runtime_protocol.topology import (
    resolve_paper_root_context,
    resolve_worktree_root_from_paper_root,
)


def test_resolve_worktree_root_from_paper_root_accepts_ds_layout(tmp_path: Path) -> None:
    paper_root = tmp_path / "runtime" / "quests" / "q001" / ".ds" / "worktrees" / "run-001" / "paper"
    paper_root.mkdir(parents=True)

    worktree_root = resolve_worktree_root_from_paper_root(paper_root)

    assert worktree_root == paper_root.parent


def test_resolve_paper_root_context_reads_study_id_from_worktree_quest_yaml(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspace"
    paper_root = workspace_root / "ops" / "deepscientist" / "runtime" / "quests" / "001-risk" / ".ds" / "worktrees" / "paper-main" / "paper"
    paper_root.mkdir(parents=True)
    (paper_root.parent / "quest.yaml").write_text("quest_id: 001-risk\n", encoding="utf-8")
    study_root = workspace_root / "studies" / "001-risk"
    (study_root / "study.yaml").parent.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")

    context = resolve_paper_root_context(paper_root)

    assert context.study_id == "001-risk"
    assert context.study_root == study_root
    assert context.worktree_root == paper_root.parent
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_runtime_protocol_topology.py`

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 写最小实现**

Create `src/med_autoscience/runtime_protocol/topology.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PaperRootContext:
    paper_root: Path
    worktree_root: Path
    quest_root: Path
    study_id: str
    study_root: Path


def resolve_worktree_root_from_paper_root(paper_root: Path) -> Path:
    resolved = Path(paper_root).expanduser().resolve()
    if resolved.name != "paper":
        raise ValueError(f"paper_root must end with /paper: {paper_root}")
    return resolved.parent
```

Implementation requirements:

- `resolve_quest_root_from_worktree_root()` 必须显式验证 `.ds/worktrees/<worktree>` 布局。
- `resolve_study_id_from_worktree_root()` 必须从 `worktree_root / "quest.yaml"` 读取顶层 `quest_id`。
- `resolve_study_root_from_paper_root()` 必须从 workspace 根推导 `studies/<study_id>`，找不到就报错，不允许静默猜测。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_runtime_protocol_topology.py`

Expected: `passed`

- [ ] **Step 5: 把 `study_delivery_sync` 改为只依赖 topology 协议层**

Implementation requirements:

- 删除 `study_delivery_sync.py` 内部重复的 `resolve_worktree_root()/resolve_quest_root()/resolve_study_root()` 逻辑。
- 改为调用 `runtime_protocol.topology.resolve_paper_root_context()`。
- `study_delivery_sync` 不得再直接假设 `worktree_root.parents[4]` 这类脆弱层级。

- [ ] **Step 6: 跑 `study_delivery_sync` 相关测试**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_study_delivery_sync.py`

Expected: `passed`

### Task 2: 提取 quest state 协议层

**Files:**
- Create: `src/med_autoscience/runtime_protocol/quest_state.py`
- Create: `tests/test_runtime_protocol_quest_state.py`
- Modify: `src/med_autoscience/adapters/deepscientist/runtime.py`
- Modify: `src/med_autoscience/controllers/publication_gate.py`
- Modify: `src/med_autoscience/controllers/runtime_watch.py`

- [ ] **Step 1: 写失败测试，覆盖 runtime_state/main result/stdout 协议读取**

```python
from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.runtime_protocol.quest_state import (
    find_latest_main_result_path,
    load_runtime_state,
    resolve_active_stdout_path,
)


def test_find_latest_main_result_path_prefers_latest_candidate(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    first = quest_root / ".ds" / "worktrees" / "run-a" / "experiments" / "main" / "001" / "RESULT.json"
    second = quest_root / "experiments" / "main" / "002" / "RESULT.json"
    first.parent.mkdir(parents=True, exist_ok=True)
    second.parent.mkdir(parents=True, exist_ok=True)
    first.write_text("{}", encoding="utf-8")
    second.write_text("{}", encoding="utf-8")
    second.touch()

    latest = find_latest_main_result_path(quest_root)

    assert latest == second


def test_resolve_active_stdout_path_reads_active_run_id(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    stdout_path = quest_root / ".ds" / "runs" / "run-123" / "stdout.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text("", encoding="utf-8")

    resolved = resolve_active_stdout_path(quest_root, {"active_run_id": "run-123"})

    assert resolved == stdout_path
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_runtime_protocol_quest_state.py`

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 写最小实现**

Implementation requirements:

- `load_runtime_state(quest_root)` 读取 `.ds/runtime_state.json`
- `find_latest_main_result_path(quest_root)` 统一封装：
  - `.ds/worktrees/*/experiments/main/*/RESULT.json`
  - `experiments/main/*/RESULT.json`
- `resolve_active_stdout_path(quest_root, runtime_state)` 统一封装 `.ds/runs/<active_run_id>/stdout.jsonl`
- `read_recent_stdout_lines(stdout_path)` 统一读取最近 `line`

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_runtime_protocol_quest_state.py`

Expected: `passed`

- [ ] **Step 5: 让 adapter/runtime.py 退化为协议层转发**

Implementation requirements:

- 保留 `src/med_autoscience/adapters/deepscientist/runtime.py` 作为兼容导出面。
- 其实现改为直接调用 `runtime_protocol.quest_state` 中的同名函数。
- 不允许再在 adapter 和 protocol 两边复制一套解析逻辑。

- [ ] **Step 6: 改造 `publication_gate` 与 `runtime_watch` 使用协议层**

Implementation requirements:

- `publication_gate.py` 不再直接从 adapter 猜路径，而改为使用 protocol 帮助层读 runtime state、main result、stdout。
- `runtime_watch.py` 如需读取 quest 状态，也应统一走协议层。

- [ ] **Step 7: 跑相关 controller 测试**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_publication_gate.py tests/test_runtime_watch.py tests/test_deepscientist_runtime_adapter.py`

Expected: `passed`

### Task 3: 让 startup/hydration 产物与 protocol 命名对齐

**Files:**
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] **Step 1: 写失败测试，覆盖 `create_payload` / `hydration_payload` 的协议可读性**

```python
def test_build_hydration_payload_is_protocol_explicit(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    create_payload = {
        "startup_contract": {
            "medical_analysis_contract_summary": {"study_archetype": "clinical_classifier"},
            "medical_reporting_contract_summary": {"reporting_guideline_family": "TRIPOD"},
            "entry_state_summary": "Study root: /tmp/workspace/studies/001-risk",
        }
    }

    payload = module._build_hydration_payload(create_payload=create_payload)

    assert payload["medical_analysis_contract"]["study_archetype"] == "clinical_classifier"
    assert payload["medical_reporting_contract"]["reporting_guideline_family"] == "TRIPOD"
    assert payload["entry_state_summary"].startswith("Study root:")
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_study_runtime_router.py -k hydration_payload`

Expected: 断言失败或字段名不匹配

- [ ] **Step 3: 写最小实现**

Implementation requirements:

- `study_runtime_router` 中与启动/恢复相关的 payload 键名必须保持稳定、直白、可测试。
- 若已有键名已满足要求，则把测试补到位并避免无意义重命名。
- `runtime protocol` 层只关心键名与产物位置，不吞并 controller 决策逻辑。

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_study_runtime_router.py -k hydration_payload`

Expected: `passed`

### Task 4: 文档化协议面并做回归验证

**Files:**
- Modify: `guides/agent_runtime_interface.md`
- Modify: `guides/workspace_architecture.md`
- Modify: `tests/test_publication_gate.py`
- Modify: `tests/test_runtime_watch.py`
- Modify: `tests/test_study_delivery_sync.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] **Step 1: 更新文档，明确哪些内容现在属于 `runtime protocol`**

必须写清楚：

- `quest_root` / active worktree / paper root / study root 的关系由 `runtime_protocol.topology` 管理
- runtime_state / main result / stdout 的解析由 `runtime_protocol.quest_state` 管理
- adapter 现在只承担 transport / engine shim，不再承担协议真相

- [ ] **Step 2: 跑回归测试**

Run:

```bash
cd /Users/gaofeng/workspace/med-autoscience
PYTHONPATH=src pytest -q \
  tests/test_runtime_protocol_topology.py \
  tests/test_runtime_protocol_quest_state.py \
  tests/test_deepscientist_runtime_adapter.py \
  tests/test_publication_gate.py \
  tests/test_runtime_watch.py \
  tests/test_study_delivery_sync.py \
  tests/test_study_runtime_router.py
```

Expected: `passed`

- [ ] **Step 3: 提交本轮协议收口**

```bash
git add \
  src/med_autoscience/runtime_protocol/__init__.py \
  src/med_autoscience/runtime_protocol/topology.py \
  src/med_autoscience/runtime_protocol/quest_state.py \
  src/med_autoscience/adapters/deepscientist/runtime.py \
  src/med_autoscience/controllers/publication_gate.py \
  src/med_autoscience/controllers/runtime_watch.py \
  src/med_autoscience/controllers/study_delivery_sync.py \
  src/med_autoscience/controllers/study_runtime_router.py \
  tests/test_runtime_protocol_topology.py \
  tests/test_runtime_protocol_quest_state.py \
  tests/test_publication_gate.py \
  tests/test_runtime_watch.py \
  tests/test_study_delivery_sync.py \
  tests/test_study_runtime_router.py \
  guides/agent_runtime_interface.md \
  guides/workspace_architecture.md
git commit -m "refactor: converge runtime protocol surfaces"
```

## Self-Review Checklist

- Spec coverage:
  - 显式 topology 协议层：Task 1
  - 显式 quest state 协议层：Task 2
  - startup/hydration 协议收口：Task 3
  - controller 迁移与文档：Task 4
- Placeholder scan:
  - 无 `TODO` / `TBD`
  - 所有新增文件与测试命令都已写明
- Scope check:
  - 本计划只覆盖 Phase 2 runtime protocol convergence
  - 不包含 adapter retirement
  - 不包含 daemon API shape 变更
