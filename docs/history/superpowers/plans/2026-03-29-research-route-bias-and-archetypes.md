# Research Route Bias And Archetypes Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把“高可塑性医学选题规则”外置成独立 policy，并把成熟论文套路做成可配置的 study archetype registry，再经由 profile 和 overlay 渲染稳定注入 `DeepScientist` 的 `scout/idea/decision` 阶段。

**Architecture:** `MedAutoScience` 继续不修改 `DeepScientist core`。新增结构化 policy/archetype 模块作为单一事实来源，profile 负责声明启用策略与偏好 archetype，overlay installer 在安装时基于 profile 渲染 stage-specific skill 文本，从而把医学约束前移到研究路线形成阶段，而不是等到写作时再兜底纠偏。

**Tech Stack:** Python 3.12, pytest, dataclasses, pathlib, argparse, importlib.resources, tomllib

---

## File Structure

- Create: `src/med_autoscience/policies/research_route_bias.py`
- Create: `src/med_autoscience/policies/study_archetypes.py`
- Modify: `src/med_autoscience/policies/__init__.py`
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Modify: `src/med_autoscience/overlay/__init__.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-idea.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-decision.SKILL.md`
- Create: `policies/study-workflow/research_route_bias_policy.md`
- Create: `policies/study-workflow/study_archetypes.md`
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_overlay_installer.py`
- Create: `tests/test_research_route_bias.py`
- Create: `tests/test_study_archetypes.py`

### Task 1: 固化独立 route-bias policy

**Files:**
- Create: `tests/test_research_route_bias.py`
- Create: `src/med_autoscience/policies/research_route_bias.py`
- Create: `policies/study-workflow/research_route_bias_policy.md`
- Modify: `src/med_autoscience/policies/__init__.py`

- [ ] **Step 1: 写失败测试**

覆盖：
- 默认优先级顺序
- 评分维度
- 失败模式
- 能生成给 `scout/idea/decision` 使用的稳定文本摘要

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_research_route_bias.py`

Expected: `ModuleNotFoundError` 或断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 2: 固化 study archetype registry

**Files:**
- Create: `tests/test_study_archetypes.py`
- Create: `src/med_autoscience/policies/study_archetypes.py`
- Create: `policies/study-workflow/study_archetypes.md`
- Modify: `src/med_autoscience/policies/__init__.py`

- [ ] **Step 1: 写失败测试**

覆盖：
- 默认 archetype 集合至少包含 `clinical_classifier` 与 `llm_agent_clinical_task`
- archetype 可按 id 解析
- archetype 可生成稳定的 paper-facing bundle/analysis checklist 文本

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_study_archetypes.py`

Expected: `ModuleNotFoundError` 或断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 3: 扩展 profile 与 CLI，声明 policy/archetype 偏好

**Files:**
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`
- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/cli.py`

- [ ] **Step 1: 写失败测试**

覆盖：
- `WorkspaceProfile` 支持 `research_route_bias_policy`
- `WorkspaceProfile` 支持 `preferred_study_archetypes`
- `show-profile`/`bootstrap`/overlay 子命令能透传这些设置

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_profiles.py tests/test_cli.py`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 4: 把 policy/archetype 渲染进 overlay

**Files:**
- Modify: `tests/test_overlay_installer.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Modify: `src/med_autoscience/overlay/__init__.py`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-idea.SKILL.md`
- Modify: `src/med_autoscience/overlay/templates/deepscientist-decision.SKILL.md`

- [ ] **Step 1: 写失败测试**

覆盖：
- 模板不再把 route bias 写死在静态正文中
- installer 能按 policy/archetype 偏好渲染 skill 文本
- `describe/install/reapply` 对 profile 配置变化产生新的 overlay 指纹

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_overlay_installer.py`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 5: 全量验证

**Files:**
- 无新增代码，仅验证

- [ ] **Step 1: 运行目标测试集合**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_research_route_bias.py tests/test_study_archetypes.py tests/test_profiles.py tests/test_cli.py tests/test_overlay_installer.py tests/test_policy_integration.py`

Expected: 全绿

- [ ] **Step 2: 运行全量 pytest**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q`

Expected: 全绿
