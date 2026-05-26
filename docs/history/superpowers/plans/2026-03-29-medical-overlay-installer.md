# Medical Overlay Installer Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `MedAutoScience` 增加可重复安装、可检测漂移、可重新覆盖的医学写作 skill overlay，使其成为医学用户真正面对的独立入口。

**Architecture:** `MedAutoScience` 不修改 `DeepScientist core`，只对 `deepscientist-write` 与 `deepscientist-finalize` 两个标准 stage skill 做医学特化覆盖。overlay 通过 package 内模板 + 目标目录解析 + 本地 manifest/fingerprint 机制实现，并暴露为 CLI 子命令。

**Tech Stack:** Python 3.12, pytest, pathlib, dataclasses, hashlib, importlib.resources, argparse

---

## File Structure

- Create: `src/med_autoscience/overlay/__init__.py`
- Create: `src/med_autoscience/overlay/installer.py`
- Create: `src/med_autoscience/overlay/templates/__init__.py`
- Create: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-finalize.SKILL.md`
- Modify: `src/med_autoscience/cli.py`
- Modify: `pyproject.toml`
- Create: `tests/test_overlay_installer.py`
- Modify: `tests/test_cli.py`
- Modify: `README.md`

### Task 1: 锁定 overlay 目标解析与状态模型

**Files:**
- Create: `tests/test_overlay_installer.py`
- Create: `src/med_autoscience/overlay/installer.py`

- [ ] **Step 1: 写失败测试，覆盖 global / quest-local 目标目录解析**

```python
def test_overlay_status_reports_not_installed_for_global_targets(tmp_path: Path) -> None:
    ...


def test_overlay_status_uses_quest_local_skill_targets_when_quest_root_provided(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_overlay_installer.py`

Expected: `ModuleNotFoundError`

- [ ] **Step 3: 写最小实现，返回 scope / target_root / current status**

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_overlay_installer.py`

Expected: `passed`

### Task 2: 锁定 overlay 安装与覆盖漂移检测

**Files:**
- Modify: `tests/test_overlay_installer.py`
- Modify: `src/med_autoscience/overlay/installer.py`
- Create: `src/med_autoscience/overlay/templates/deepscientist-write.SKILL.md`
- Create: `src/med_autoscience/overlay/templates/deepscientist-finalize.SKILL.md`
- Modify: `pyproject.toml`

- [ ] **Step 1: 写失败测试，覆盖首次安装、重复安装、被上游覆盖后的状态检测**

```python
def test_install_medical_overlay_writes_skill_and_manifest(tmp_path: Path) -> None:
    ...


def test_overlay_status_detects_overwritten_by_upstream(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_overlay_installer.py`

Expected: 断言失败

- [ ] **Step 3: 写最小实现**

包括：
- overlay 模板加载
- SHA256 fingerprint
- target manifest 记录
- reapply 行为

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_overlay_installer.py`

Expected: `passed`

### Task 3: 暴露 CLI 入口

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `src/med_autoscience/cli.py`

- [ ] **Step 1: 写失败测试，覆盖 `overlay-status` / `install-medical-overlay` / `reapply-medical-overlay`**

```python
def test_overlay_status_command_dispatches_installer(monkeypatch, capsys) -> None:
    ...
```

- [ ] **Step 2: 运行测试确认 RED**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_cli.py`

Expected: parser 或 `AttributeError` 失败

- [ ] **Step 3: 写最小实现**

- [ ] **Step 4: 运行测试确认 GREEN**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q tests/test_cli.py`

Expected: `passed`

### Task 4: 文档与集成验证

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在 README 中补 overlay 入口与依赖关系说明**

- [ ] **Step 2: 跑全量 pytest**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src pytest -q`

Expected: 全绿

- [ ] **Step 3: 跑真实 dry-run**

Run: `cd /Users/gaofeng/workspace/med-autoscience && PYTHONPATH=src python3 -m med_autoscience.cli overlay-status`

Expected: 返回当前全局 skill overlay 状态
