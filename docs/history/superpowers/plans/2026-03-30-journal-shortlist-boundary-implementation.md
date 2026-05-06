# Journal Shortlist Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把“选刊证据解析”和“投稿格式解析”从平台层彻底拆开，并用 startup gate 防止误用 `submission target / journal-resolution` 流程。

**Architecture:** 新增一个独立的 `journal_shortlist` contract 与 controller，只解析 `study.yaml` 中的 shortlist evidence；startup boundary gate 改为依赖该 contract，而不再只看 shortlist 名单。与此同时，更新 controller-first policy、overlay 文案和 workspace init 入口，明确“先 shortlist，再 submission target，再 journal-resolution”的顺序。

**Tech Stack:** Python 3.12, dataclasses, YAML, argparse CLI, pytest

---

### Task 1: 新增 journal shortlist contract 与 controller

**Files:**
- Create: `src/med_autoscience/journal_shortlist.py`
- Create: `src/med_autoscience/controllers/journal_shortlist.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/cli.py`

- [ ] 定义 dataclass 与 YAML 解析逻辑
- [ ] 实现 `resolve_journal_shortlist_contract(...)`
- [ ] 实现 controller `resolve_journal_shortlist(...)`
- [ ] 新增 CLI 命令 `resolve-journal-shortlist`

### Task 2: 强化 startup boundary gate

**Files:**
- Modify: `src/med_autoscience/controllers/startup_boundary_gate.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`

- [ ] 让 `journal_shortlist_ready` 依赖 evidence-backed contract
- [ ] 更新 blocker 文案，明确缺的是 evidence 而不是单纯名单
- [ ] 在 startup contract / status payload 中输出新的 resolved shortlist summary

### Task 3: 修正误导性的 policy 与 overlay 文案

**Files:**
- Modify: `src/med_autoscience/policies/controller_first.py`
- Modify: `src/med_autoscience/submission_targets.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-journal-resolution.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`

- [ ] 把 controller-first 顺序改成 shortlist -> submission target -> journal-resolution
- [ ] 明确 submission target contract 不用于 venue discovery
- [ ] 明确 journal-resolution 不是选刊流程
- [ ] 在 scout 中把选刊入口固定为 `resolve-journal-shortlist`

### Task 4: 更新 workspace init 默认入口

**Files:**
- Modify: `src/med_autoscience/controllers/workspace_init.py`

- [ ] 新增 `ops/medautoscience/bin/resolve-journal-shortlist`
- [ ] 让自动生成的 workspace rules / summary 继承新的 controller-first 顺序

### Task 5: 补测试

**Files:**
- Create: `tests/test_journal_shortlist.py`
- Create: `tests/test_journal_shortlist_controller.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `tests/test_controller_first_policy.py`
- Modify: `tests/test_overlay_installer.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_workspace_init.py`

- [ ] 测试 contract 解析成功 / 失败路径
- [ ] 测试 gate 对无 evidence shortlist 的拒绝
- [ ] 测试 CLI / workspace init 新入口
- [ ] 测试 overlay 与 policy 文案已改

### Task 6: 运行验证

**Files:**
- Modify: 无

- [ ] 运行 `pytest tests/test_journal_shortlist.py tests/test_journal_shortlist_controller.py tests/test_study_runtime_router.py tests/test_controller_first_policy.py tests/test_overlay_installer.py tests/test_cli.py tests/test_workspace_init.py -q`
- [ ] 运行必要的 targeted grep / status 检查，确认旧误导文案已消失
