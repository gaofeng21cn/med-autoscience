# Medical Overlay Frontload Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把医学 overlay 从 `write/finalize` 后段收口，前移到 `scout/idea/decision`，并通过 `profile/bootstrap` 让新 workspace 与新电脑进入 `MedAutoScience` 时默认就是医学发表导向模式。

**Architecture:** `MedAutoScience` 继续作为治理层，不改 `DeepScientist core`。通过 profile 声明所需 overlay skills，CLI 提供 `bootstrap` 与 `--profile` 驱动安装/检查，overlay installer 扩展为管理 `scout/idea/decision/write/finalize` 五个 stage skill。前段三类 skill 中显式加入“高可塑性、可扩展、可发表”的医学研究路线偏置。

**Tech Stack:** Python 3.12, pytest, pathlib, argparse, dataclasses, importlib.resources, tomllib

---

## File Structure

- Modify: `src/med_autoscience/profiles.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Create: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-idea.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-decision.SKILL.md`
- Modify: `profiles/workspace.profile.template.toml`
- Modify: `bootstrap/README.md`
- Modify: `README.md`
- Modify: `tests/test_profiles.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_overlay_installer.py`

### Task 1: 让 profile 能声明医学 overlay 需求

**Files:**
- Modify: `tests/test_profiles.py`
- Modify: `src/med_autoscience/profiles.py`
- Modify: `profiles/workspace.profile.template.toml`

- [ ] **Step 1: 写失败测试，覆盖 `enable_medical_overlay` 与 `medical_overlay_skills` 的解析与默认值**
- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_profiles.py`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 2: 扩展 overlay installer 到前段 stage

**Files:**
- Modify: `tests/test_overlay_installer.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Create: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-idea.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-decision.SKILL.md`

- [ ] **Step 1: 写失败测试，覆盖按 skill 子集安装与五个 stage skill 的状态检查**
- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_overlay_installer.py`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 3: 把 overlay 接进 profile/bootstrap 流程

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `bootstrap/README.md`
- Modify: `README.md`

- [ ] **Step 1: 写失败测试，覆盖 `overlay-status/install/reapply --profile` 与 `bootstrap --profile`**
- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_cli.py`

Expected: parser 或断言失败

- [ ] **Step 3: 写最小实现**
- [ ] **Step 4: 运行测试确认 GREEN**

### Task 4: 医学发表导向前移到 `scout/idea/decision`

**Files:**
- Create: `src/med_autoscience/overlay/templates/deepscientist-scout.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-idea.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-decision.SKILL.md`

- [ ] **Step 1: 在三个 stage skill 中加入医学研究路线偏置**

至少覆盖：
- 优先高可塑性路线
- 优先可形成分类器 / 风险分层 / clinical utility story 的路线
- 优先可接公开数据扩展与外部验证的路线
- 降权单一固定临床假设、阴性后没有转向空间的路线

- [ ] **Step 2: 做一次真实 overlay 安装并检查状态**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src python3 -m med_autoscience.cli install-medical-overlay`

Expected: 五个 skill 进入 managed 状态

### Task 5: 全量验证

**Files:**
- 无新增文件，仅验证

- [ ] **Step 1: 跑全量 pytest**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q`

Expected: 全绿

- [ ] **Step 2: 跑真实 bootstrap dry-run**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src python3 -m med_autoscience.cli bootstrap --profile <local-profile>`

Expected: 返回 doctor 结果、overlay 安装结果和 overlay 当前状态
