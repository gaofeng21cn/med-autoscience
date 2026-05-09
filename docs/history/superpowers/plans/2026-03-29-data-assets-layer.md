# Data Assets Layer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 MedAutoScience 增加正式的医学数据资产管理层，包括私有数据版本登记、公开数据 sidecar 登记、影响评估，以及 ToolUniverse 适配状态。

**Architecture:** 在 `src/med_autoscience/controllers` 下增加数据资产控制器，在 `src/med_autoscience/adapters` 下增加 ToolUniverse 适配器，在 `src/med_autoscience/cli.py` 暴露独立命令。私有数据注册以 workspace 的 `datasets/<family>/<version>` 为主扫描面；公开数据 sidecar 使用显式 JSON registry；影响评估读取 study 的 `data_input/dataset_manifest.yaml` 并对照 registry 输出状态。

**Tech Stack:** Python 3.12, argparse, json, pathlib, PyYAML, pytest

---

### Task 1: 数据资产契约与 CLI 入口

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Create: `src/med_autoscience/controllers/data_assets.py`
- Create: `tests/test_data_assets.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，约束 data asset CLI 行为**
- [ ] **Step 2: 运行测试，确认因命令不存在而失败**
- [ ] **Step 3: 最小实现 `init-data-assets` / `data-assets-status` / `assess-data-asset-impact` 命令**
- [ ] **Step 4: 运行局部测试，确认转绿**

### Task 2: 私有数据版本登记与公开数据 registry

**Files:**
- Modify: `src/med_autoscience/controllers/data_assets.py`
- Modify: `tests/test_data_assets.py`

- [ ] **Step 1: 写失败测试，约束私有数据扫描与公开数据 registry 初始化**
- [ ] **Step 2: 运行测试，确认失败原因正确**
- [ ] **Step 3: 最小实现私有数据扫描、registry 初始化与 impact 报告生成**
- [ ] **Step 4: 运行局部测试，确认通过**

### Task 3: ToolUniverse 适配器

**Files:**
- Create: `src/med_autoscience/adapters/tooluniverse.py`
- Modify: `src/med_autoscience/adapters/__init__.py`
- Modify: `src/med_autoscience/cli.py`
- Create: `tests/test_tooluniverse_adapter.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写失败测试，约束 ToolUniverse 状态探测与 CLI 输出**
- [ ] **Step 2: 运行测试，确认失败**
- [ ] **Step 3: 最小实现 ToolUniverse root / command / role status 适配器**
- [ ] **Step 4: 运行局部测试，确认通过**

### Task 4: README 与政策文档收口

**Files:**
- Modify: `README.md`
- Create: `policies/study-workflow/data_asset_management.md`
- Modify: `bootstrap/README.md`

- [ ] **Step 1: 清掉 README 英文残留，加入数据资产层说明**
- [ ] **Step 2: 写清 private/public/impact/ToolUniverse 的职责边界**
- [ ] **Step 3: 运行全文搜索，确认 README 不再有不必要英文残留**

### Task 5: 全量验证与 Git 收口

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_data_assets.py`
- Modify: `tests/test_tooluniverse_adapter.py`

- [ ] **Step 1: 运行新增测试与全量测试**
- [ ] **Step 2: 检查 git diff 与 README 表面质量**
- [ ] **Step 3: 提交并 push 到 GitHub**
