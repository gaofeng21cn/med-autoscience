# Sidecar Provider And Figure Sidecar Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 抽通 sidecar provider 骨架并接入 `AutoFigure-Edit` figure sidecar，同时保持现有 `ARIS` 入口兼容。

**Architecture:** 新增 provider registry 和通用 controller/adapter，把 `aris` 迁到统一骨架，再用同一机制接入 `autofigure_edit`。provider 共享 recommendation/provision/import 流程，但保留领域化 contract 与 handoff 校验。

**Tech Stack:** Python 3.12, pytest, argparse, JSON/YAML file contracts

---

### Task 1: 新增 provider registry 与通用路径层

**Files:**
- Create: `src/med_autoscience/sidecars/__init__.py`
- Create: `src/med_autoscience/sidecars/registry.py`
- Create: `src/med_autoscience/adapters/sidecar_provider.py`
- Test: `tests/test_sidecar_provider_registry.py`
- Test: `tests/test_sidecar_provider_adapter.py`

- [ ] **Step 1: 写失败测试**
- [ ] **Step 2: 运行测试确认按预期失败**
- [ ] **Step 3: 实现最小 registry 与路径函数**
- [ ] **Step 4: 运行测试确认通过**

### Task 2: 把 ARIS 迁到通用 provider 骨架

**Files:**
- Create: `src/med_autoscience/controllers/sidecar_provider.py`
- Modify: `src/med_autoscience/controllers/aris_sidecar.py`
- Modify: `src/med_autoscience/adapters/aris_sidecar.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/adapters/__init__.py`
- Test: `tests/test_aris_sidecar_controller.py`
- Test: `tests/test_aris_sidecar_adapter.py`

- [ ] **Step 1: 保持旧测试为红**
- [ ] **Step 2: 实现通用 controller 并让 ARIS wrapper 走新骨架**
- [ ] **Step 3: 跑 ARIS 定向测试**
- [ ] **Step 4: 确认旧接口兼容**

### Task 3: 新增 AutoFigure-Edit provider

**Files:**
- Create: `src/med_autoscience/controllers/autofigure_edit_sidecar.py`
- Create: `src/med_autoscience/adapters/autofigure_edit_sidecar.py`
- Test: `tests/test_autofigure_edit_sidecar_controller.py`

- [ ] **Step 1: 写 figure sidecar 失败测试**
- [ ] **Step 2: 实现 recommendation/provision/import/resolve**
- [ ] **Step 3: 跑 figure sidecar 定向测试**

### Task 4: 暴露通用 CLI

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: 写通用 sidecar CLI 失败测试**
- [ ] **Step 2: 实现 `recommend-sidecar` / `provision-sidecar` / `import-sidecar`**
- [ ] **Step 3: 跑 CLI 定向测试**

### Task 5: 回归验证

**Files:**
- No code changes required

- [ ] **Step 1: 运行新旧 sidecar 相关测试**
- [ ] **Step 2: 检查没有破坏现有 CLI 分发**
- [ ] **Step 3: 汇总验证结果**
