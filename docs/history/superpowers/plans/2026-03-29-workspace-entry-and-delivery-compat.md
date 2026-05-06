# Workspace Entry And Delivery Compatibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `NF-PitNET workspace` 以本地薄脚本为入口接管 `MedAutoScience`，同时把不能降级的 `study_delivery_sync` 正式迁入 `MedAutoScience`，补齐 `export-submission-minimal -> shallow final delivery` 自动链路，保证 `002` 维护兼容和后续新论文默认走新入口。

**Architecture:** 平台能力继续收拢到 `MedAutoScience`，workspace 只保留课题配置与本地入口脚本。通过新增 `study_delivery_sync` controller、补齐 `export-submission-minimal -> sync-study-delivery(stage=\"submission_minimal\")` 自动链路、并建立 workspace-local profile 与 wrapper scripts，把用户入口统一到 `ops/medautoscience/bin/*`。`002` 的 legacy closeout 自动同步路径在维护期内视为冻结兼容 shim。

**Tech Stack:** Python 3.12, pytest, pathlib, argparse, json, shutil, POSIX shell

---

## File Structure

- Create: `src/med_autoscience/controllers/study_delivery_sync.py`
- Modify: `src/med_autoscience/controllers/submission_minimal.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `profiles/workspace.profile.template.toml`
- Modify: `controllers/README.md`
- Modify: `bootstrap/README.md`
- Create: `tests/test_study_delivery_sync.py`
- Modify: `tests/test_submission_minimal.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_profiles.py`
- Create: `docs/superpowers/specs/2026-03-29-workspace-entry-and-legacy-compat-design.md`
- Create: `ops/medautoscience/README.md`
- Create: `ops/medautoscience/compatibility_inventory.md`
- Create: `ops/medautoscience/config.env`
- Create: `ops/medautoscience/profiles/nfpitnet.workspace.toml`
- Create: `ops/medautoscience/bin/_shared.sh`
- Create: `ops/medautoscience/bin/bootstrap`
- Create: `ops/medautoscience/bin/show-profile`
- Create: `ops/medautoscience/bin/watch-runtime`
- Create: `ops/medautoscience/bin/publication-gate`
- Create: `ops/medautoscience/bin/medical-surface`
- Create: `ops/medautoscience/bin/export-submission`
- Create: `ops/medautoscience/bin/sync-delivery`

### Task 1: 先写 `study_delivery_sync` 的失败测试

**Files:**
- Create: `tests/test_study_delivery_sync.py`

- [ ] **Step 1: 写失败测试，覆盖 `submission_minimal` 与 `finalize` 两种同步阶段**
- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_study_delivery_sync.py`

Expected: `ModuleNotFoundError` 或断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 2: 把浅路径交付链接回 `submission_minimal`

**Files:**
- Modify: `tests/test_submission_minimal.py`
- Modify: `src/med_autoscience/controllers/submission_minimal.py`

- [ ] **Step 1: 写失败测试**

覆盖：
- 有 study 上下文时，`export-submission-minimal` 自动触发 `study_delivery_sync(stage="submission_minimal")`
- 无 study 上下文时，不触发自动同步

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_submission_minimal.py -k study_delivery`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 3: 把 controller 和交付同步接进 `MedAutoScience` CLI

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `controllers/README.md`
- Modify: `bootstrap/README.md`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 `publication-gate`、`medical-publication-surface`、`sync-study-delivery` 入口**
- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_cli.py -k 'publication_gate_command or medical_publication_surface_command or sync_study_delivery_command'`

Expected: parser 或断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 4: 显式化 workspace-local overlay scope 与平台定位 contract

**Files:**
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `profiles/workspace.profile.template.toml`
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试**

覆盖：
- `medical_overlay_scope` 解析与默认值
- `bootstrap` / `overlay-status` 在 `workspace` scope 下使用 `workspace_root/.codex/skills`

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_profiles.py tests/test_cli.py -k overlay_scope`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 5: 为 workspace 建立本地薄入口层

**Files:**
- Create: `ops/medautoscience/README.md`
- Create: `ops/medautoscience/compatibility_inventory.md`
- Create: `ops/medautoscience/config.env`
- Create: `ops/medautoscience/profiles/nfpitnet.workspace.toml`
- Create: `ops/medautoscience/bin/_shared.sh`
- Create: `ops/medautoscience/bin/bootstrap`
- Create: `ops/medautoscience/bin/show-profile`
- Create: `ops/medautoscience/bin/watch-runtime`
- Create: `ops/medautoscience/bin/publication-gate`
- Create: `ops/medautoscience/bin/medical-surface`
- Create: `ops/medautoscience/bin/export-submission`
- Create: `ops/medautoscience/bin/sync-delivery`

- [ ] **Step 1: 写文档，明确 workspace 与 `MedAutoScience` 的关系、兼容清单、经验回流规则**
- [ ] **Step 2: 写 workspace-local profile，并显式声明 `medical_overlay_scope`**
- [ ] **Step 3: 写 `_shared.sh`，通过显式配置文件定位 `MedAutoScience` repo 与 profile；缺失配置时 fail-fast**
- [ ] **Step 4: 写用户入口脚本，只做参数透传，不复制业务逻辑**
- [ ] **Step 5: 手工 smoke test 本地脚本的 repo/profile 定位与退出码**

### Task 6: 全量验证

**Files:**
- 无新增实现，仅验证

- [ ] **Step 1: 跑新增与相关测试**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_study_delivery_sync.py tests/test_submission_minimal.py tests/test_cli.py tests/test_profiles.py`

Expected: 全绿

- [ ] **Step 2: 跑全量 pytest**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q`

Expected: 全绿
