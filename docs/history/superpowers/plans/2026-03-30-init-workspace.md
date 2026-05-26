# Init Workspace Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 MedAutoScience 增加一个 `init-workspace` 命令，供 Agent 直接初始化病种级 workspace。

**Architecture:** 在 CLI 下新增一个子命令，委托给独立的 `workspace_init` controller。controller 负责渲染最小目录骨架与示例文件，支持真实落盘和 `--dry-run` 计划输出，并保持幂等与显式配置原则。

**Tech Stack:** Python, argparse, pathlib, pytest

---

### Task 1: 建立 controller 与 dry-run 合约

**Files:**
- Create: `src/med_autoscience/controllers/workspace_init.py`
- Test: `tests/test_workspace_init.py`

- [ ] **Step 1: 写 dry-run 的失败测试**

- [ ] **Step 2: 实现目录骨架与返回 payload 的最小数据结构**

- [ ] **Step 3: 跑定向测试确认 dry-run 行为正确**

### Task 2: 接 CLI

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: 为 `init-workspace` 增加 parser 参数**

- [ ] **Step 2: 在 CLI 主分发中调用 controller**

- [ ] **Step 3: 跑 CLI 定向测试**

### Task 3: 生成最小示例文件

**Files:**
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Test: `tests/test_workspace_init.py`

- [ ] **Step 1: 生成 workspace 根 README、profile、本地 config example**

- [ ] **Step 2: 增加重复执行与 `--force` 行为**

- [ ] **Step 3: 跑 controller 定向测试**

### Task 4: 文档补入口

**Files:**
- Modify: `README.md`
- Modify: `bootstrap/README.md`

- [ ] **Step 1: 在 README 中补 `init-workspace` 用法**

- [ ] **Step 2: 在 bootstrap 中把新项目启动顺序切到该命令**

- [ ] **Step 3: 复读文档确保不和 quickstart 矛盾**

### Task 5: 回归验证

**Files:**
- Modify: `src/med_autoscience/controllers/workspace_init.py`
- Modify: `src/med_autoscience/cli.py`
- Modify: `tests/test_workspace_init.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`
- Modify: `bootstrap/README.md`

- [ ] **Step 1: 运行定向测试**

Run: `pytest -q tests/test_workspace_init.py tests/test_cli.py`
Expected: 全部通过。

- [ ] **Step 2: 手动做一次 dry-run 验证**

Run: `PYTHONPATH=src python3 -m med_autoscience.cli init-workspace --workspace-root /tmp/medautosci-demo --workspace-name demo --dry-run`
Expected: 输出 JSON，且 `/tmp/medautosci-demo` 不被创建。

- [ ] **Step 3: 手动做一次真实初始化验证**

Run: `PYTHONPATH=src python3 -m med_autoscience.cli init-workspace --workspace-root /tmp/medautosci-demo --workspace-name demo`
Expected: 目录与最小文件被创建。
