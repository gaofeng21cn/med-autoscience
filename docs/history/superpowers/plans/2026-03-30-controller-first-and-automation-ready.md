# Controller-First And Automation-Ready Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 MedAutoScience 对新旧 workspace 默认执行两条稳定约束：优先复用成熟 controller/CLI/overlay skill，不允许 Agent 在已有平台能力覆盖的任务上自由发挥；同时在 study 边界已明确时，默认切入 DeepScientist managed runtime 的自动持续推进模式，而不是停留在碎片化人工交互。

**Architecture:** 新增独立 policy 层分别表达 `controller-first` 和 `automation-ready` 规则，并把这些规则注入 workspace 初始化模板、startup/runtime contract、startup boundary brief 和 relevant overlay templates。测试从 workspace init 输出、startup contract 文案、managed runtime status 和 overlay 渲染四个面收口，确保默认行为对新项目自动生效而不是靠 workspace 局部补丁。

**Tech Stack:** Python 3.12, existing MedAutoScience controllers/policies/overlay installer/templates, pytest, PyYAML

---

### Task 1: 定义 policy 层与基础渲染函数

**Files:**
- Create: `src/med_autoscience/policies/controller_first.py`
- Create: `src/med_autoscience/policies/automation_ready.py`
- Test: `tests/test_controller_first_policy.py`

- [ ] **Step 1: 写失败测试，约束 controller-first 任务域、首选 controller/CLI 和 fallback / write-back 规则**
- [ ] **Step 2: 写失败测试，约束 automation-ready 条件与渲染摘要**
- [ ] **Step 3: 运行局部测试，确认因模块不存在而失败**
- [ ] **Step 4: 最小实现两个 policy 模块与渲染函数**
- [ ] **Step 5: 运行局部测试，确认转绿**

### Task 2: 把 policy 接入 workspace init 默认输出

**Files:**
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Modify: `tests/test_workspace_init.py`

- [ ] **Step 1: 写失败测试，约束新 workspace 输出包含 controller-first / automation-ready 默认规则**
- [ ] **Step 2: 运行测试，确认失败原因正确**
- [ ] **Step 3: 最小实现 workspace README / profile / 规则输出注入**
- [ ] **Step 4: 运行局部测试，确认通过**

### Task 3: 把 policy 接入 startup contract 与 runtime brief

**Files:**
- Modify: `src/med_autoscience/controllers/startup_boundary_gate.py`
- Modify: `src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `tests/test_study_runtime_router.py`

- [ ] **Step 1: 写失败测试，约束 startup contract 暴露 controller-first 与 automation-ready 摘要**
- [ ] **Step 2: 写失败测试，约束 managed runtime 在自动推进就绪时明确偏向 autonomous continuation**
- [ ] **Step 3: 运行局部测试，确认失败**
- [ ] **Step 4: 最小实现 startup brief / runtime contract 注入与状态输出增强**
- [ ] **Step 5: 运行局部测试，确认通过**

### Task 4: 把 policy 接入 overlay 文本

**Files:**
- Modify: `src/med_autoscience/overlay/installer.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-decision.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-journal-resolution.SKILL.md`
- Modify: `tests/test_overlay_installer.py`

- [ ] **Step 1: 写失败测试，约束相关 overlay 能看到 controller-first / automation-ready 规则块**
- [ ] **Step 2: 运行局部测试，确认失败**
- [ ] **Step 3: 最小实现 overlay 动态 token 与模板注入**
- [ ] **Step 4: 运行局部测试，确认通过**

### Task 5: 回归验证与收口

**Files:**
- Modify: `tests/test_workspace_init.py`
- Modify: `tests/test_study_runtime_router.py`
- Modify: `tests/test_overlay_installer.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 运行新增测试集合**
- [ ] **Step 2: 运行与 workspace init / runtime routing / overlay 相关的回归测试**
- [ ] **Step 3: 检查 git diff，确认没有把 workspace 局部规则误当成框架实现**
- [ ] **Step 4: 提交实现**
