# Submission Targets And Journal Resolution Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 MedAutoScience 支持 workspace 默认投稿目标、study/quest 显式投稿目标、写作/定稿阶段的目标期刊约束，以及面向未知期刊的受控 journal-resolution 入口。

**Architecture:** 增加一个独立的 submission-targets 解析层，统一读取 profile TOML、study.yaml、quest.yaml 并产出结构化目标清单。write/finalize overlay 不内嵌某篇论文的静态目标，而是学习并执行这个解析 contract；导出层新增按目标批量导出的控制器与 CLI。未知期刊不直接自由导出，而是先进入 journal-resolution skill，形成结构化 resolved target 后再交给 exporter。

**Tech Stack:** Python 3.12+, `tomllib`, `yaml.safe_load`, existing MedAutoScience CLI/controllers/overlay templates, pytest

---

### Task 1: 定义 submission targets 数据模型与解析层

**Files:**
- Create: `src/med_autoscience/submission_targets.py`
- Modify: `src/med_autoscience/profiles.py`
- Test: `tests/test_submission_targets.py`
- Test: `tests/test_profiles.py`

- [ ] **Step 1: 写失败测试，覆盖 profile 默认 targets、study/quest 覆盖与 primary target 解析**
- [ ] **Step 2: 跑测试确认失败**
- [ ] **Step 3: 实现 submission target dataclass、merge 规则与 profile/study/quest 解析**
- [ ] **Step 4: 跑局部测试确认通过**

### Task 2: 把 submission targets 接入 doctor 与 overlay

**Files:**
- Modify: `src/med_autoscience/doctor.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-finalize.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-journal-resolution.SKILL.md`
- Test: `tests/test_cli.py`
- Test: `tests/test_overlay_installer.py`

- [ ] **Step 1: 写失败测试，覆盖 overlay 能看见 submission target contract**
- [ ] **Step 2: 跑测试确认失败**
- [ ] **Step 3: 实现 overlay 动态 token 与 journal-resolution skill 安装**
- [ ] **Step 4: 跑局部测试确认通过**

### Task 3: 实现按 submission targets 批量导出投稿包

**Files:**
- Create: `src/med_autoscience/controllers/submission_targets.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/cli.py`
- Test: `tests/test_submission_targets_controller.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，覆盖 resolved targets 导出与 unresolved target 阻塞**
- [ ] **Step 2: 跑测试确认失败**
- [ ] **Step 3: 实现批量导出控制器与 CLI**
- [ ] **Step 4: 跑局部测试确认通过**

### Task 4: 回归验证与 002 工作流样例

**Files:**
- Modify: `tests/test_submission_minimal.py`
- Modify: `tests/test_study_delivery_sync.py`
- Modify: `docs/superpowers/plans/2026-03-29-submission-targets-and-journal-resolution.md`

- [ ] **Step 1: 跑全量测试确认新 contract 不破坏已有导出链路**
- [ ] **Step 2: 用 002 study.yaml 注入 Frontiers family 目标并实际导出验证**
- [ ] **Step 3: 记录实际工作流用法与边界**
