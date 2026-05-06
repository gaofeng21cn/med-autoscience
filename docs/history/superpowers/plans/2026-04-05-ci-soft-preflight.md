# CI Soft Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为仓库落地非阻断式的本地变更感知预检，并把 GitHub CI 收紧为主线告警面。

**Architecture:** 通过一个 checked-in 的 preflight contract 将“文件改动面”显式映射到“验证命令集合”，再由独立执行器负责采集改动、分类、执行命令和结构化输出。CLI 只做参数解析和结果渲染；远端 CI 仅保留 `push` 主线触发，不承担 PR / worktree 中间态噪音吸收职责。

**Tech Stack:** Python 3.12, argparse, subprocess, pytest, GitHub Actions YAML

---

### Task 1: 写 contract 层失败测试

**Files:**
- Create: `tests/test_dev_preflight_contract.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/docs/superpowers/specs/2026-04-05-ci-soft-preflight-design.md`

- [ ] **Step 1: 写 contract 分类的失败测试**

```python
from med_autoscience import dev_preflight_contract as module


def test_classify_changes_matches_runtime_surface_exactly() -> None:
    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/study_runtime_router.py",
            "src/med_autoscience/runtime_transport/med_deepscientist.py",
        ]
    )

    assert result.matched_categories == ("runtime_contract_surface",)
    assert result.unclassified_changes == ()


def test_classify_changes_flags_unclassified_paths() -> None:
    result = module.classify_changed_files(
        [
            "src/med_autoscience/controllers/workspace_init.py",
        ]
    )

    assert result.matched_categories == ()
    assert result.unclassified_changes == ("src/med_autoscience/controllers/workspace_init.py",)


def test_plan_commands_deduplicates_multi_surface_commands() -> None:
    commands = module.plan_commands_for_categories(
        ("workflow_surface", "workflow_surface", "codex_plugin_docs_surface")
    )

    assert commands.count("uv run pytest tests/test_release_workflow.py -q") == 1
    assert "uv run pytest tests/test_codex_plugin.py -q" in commands
```

- [ ] **Step 2: 运行 contract 测试确认失败**

Run: `uv run pytest tests/test_dev_preflight_contract.py -q`
Expected: FAIL，提示 `med_autoscience.dev_preflight_contract` 不存在或缺少 `classify_changed_files`

- [ ] **Step 3: 写最小 contract 实现**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationResult:
    matched_categories: tuple[str, ...]
    unclassified_changes: tuple[str, ...]


def classify_changed_files(changed_files: list[str]) -> ClassificationResult:
    ...


def plan_commands_for_categories(categories: tuple[str, ...]) -> list[str]:
    ...
```

- [ ] **Step 4: 重新运行 contract 测试**

Run: `uv run pytest tests/test_dev_preflight_contract.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add tests/test_dev_preflight_contract.py src/med_autoscience/dev_preflight_contract.py
git commit -m "feat: add preflight contract classification"
```

### Task 2: 写执行器失败测试

**Files:**
- Create: `tests/test_dev_preflight.py`
- Create: `src/med_autoscience/dev_preflight.py`
- Modify: `src/med_autoscience/dev_preflight_contract.py`

- [ ] **Step 1: 写执行器失败测试**

```python
from pathlib import Path

from med_autoscience import dev_preflight as module


def test_run_preflight_reports_unclassified_changes_without_running_commands() -> None:
    result = module.run_preflight(
        changed_files=["src/med_autoscience/controllers/workspace_init.py"],
        repo_root=Path.cwd(),
    )

    assert result.ok is False
    assert result.unclassified_changes == ("src/med_autoscience/controllers/workspace_init.py",)
    assert result.results == ()


def test_run_preflight_executes_planned_commands(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(command, cwd, shell, check, text, capture_output):
        calls.append(command)
        class Result:
            returncode = 0
            stdout = "ok"
            stderr = ""
        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_preflight(
        changed_files=["README.md"],
        repo_root=Path.cwd(),
    )

    assert result.ok is True
    assert result.matched_categories == ("codex_plugin_docs_surface",)
    assert calls
```

- [ ] **Step 2: 运行执行器测试确认失败**

Run: `uv run pytest tests/test_dev_preflight.py -q`
Expected: FAIL，提示 `med_autoscience.dev_preflight` 不存在或缺少 `run_preflight`

- [ ] **Step 3: 写最小执行器实现**

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class PreflightResult:
    input_mode: str
    changed_files: tuple[str, ...]
    matched_categories: tuple[str, ...]
    unclassified_changes: tuple[str, ...]
    planned_commands: tuple[str, ...]
    results: tuple[CommandResult, ...]
    ok: bool


def run_preflight(*, changed_files: list[str], repo_root: Path, input_mode: str = "files") -> PreflightResult:
    ...
```

- [ ] **Step 4: 运行执行器与 contract 测试**

Run: `uv run pytest tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/med_autoscience/dev_preflight.py src/med_autoscience/dev_preflight_contract.py tests/test_dev_preflight.py
git commit -m "feat: add preflight execution engine"
```

### Task 3: 接入 CLI 并验证 red-green

**Files:**
- Modify: `src/med_autoscience/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `src/med_autoscience/dev_preflight.py`

- [ ] **Step 1: 写 CLI 子命令失败测试**

```python
def test_preflight_changes_command_outputs_json(monkeypatch, capsys, tmp_path) -> None:
    from med_autoscience import cli as module

    monkeypatch.setattr(
        module.dev_preflight,
        "run_preflight",
        lambda **kwargs: module.dev_preflight.PreflightResult(
            input_mode="files",
            changed_files=("README.md",),
            matched_categories=("codex_plugin_docs_surface",),
            unclassified_changes=(),
            planned_commands=("uv run pytest tests/test_codex_plugin.py -q",),
            results=(),
            ok=True,
        ),
    )

    exit_code = module.entrypoint(
        [
            "preflight-changes",
            "--files",
            "README.md",
            "--format",
            "json",
        ]
    )

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "\"ok\": true" in out
```

- [ ] **Step 2: 运行 CLI 测试确认失败**

Run: `uv run pytest tests/test_cli.py -q -k preflight_changes`
Expected: FAIL，提示未知子命令 `preflight-changes` 或 `dev_preflight` 未导入

- [ ] **Step 3: 写最小 CLI 接入**

```python
from med_autoscience import dev_preflight

preflight_parser = subparsers.add_parser("preflight-changes")
preflight_parser.add_argument("--files", nargs="+")
preflight_parser.add_argument("--staged", action="store_true")
preflight_parser.add_argument("--base-ref")
preflight_parser.add_argument("--format", choices=("text", "json"), default="text")
```

- [ ] **Step 4: 运行 CLI 相关测试**

Run: `uv run pytest tests/test_cli.py -q -k preflight_changes`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/med_autoscience/cli.py tests/test_cli.py
git commit -m "feat: add preflight changes cli command"
```

### Task 4: 补 git 改动采集与维护指南

**Files:**
- Modify: `src/med_autoscience/dev_preflight.py`
- Create: `guides/repository_ci_preflight.md`
- Modify: `tests/test_dev_preflight.py`

- [ ] **Step 1: 写 staged / base-ref 采集失败测试**

```python
def test_collect_changed_files_from_staged(monkeypatch) -> None:
    from med_autoscience import dev_preflight as module

    monkeypatch.setattr(module, "_git_diff_name_only", lambda **kwargs: ["README.md"])

    files = module.collect_changed_files(repo_root=Path.cwd(), staged=True)

    assert files == ["README.md"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run pytest tests/test_dev_preflight.py -q -k collect_changed_files`
Expected: FAIL，提示 `collect_changed_files` 未定义

- [ ] **Step 3: 写最小 git 改动采集与指南**

```python
def collect_changed_files(*, repo_root: Path, staged: bool = False, base_ref: str | None = None, files: list[str] | None = None) -> list[str]:
    ...
```

指南内容至少包含：

- 当前远端 CI 只在 `push main/development` 上作为告警运行
- `medautosci preflight-changes --files ...`
- `medautosci preflight-changes --staged`
- `medautosci preflight-changes --base-ref origin/main`
- 遇到 `unclassified_changes` 时要补 contract，而不是跳过

- [ ] **Step 4: 运行执行器测试**

Run: `uv run pytest tests/test_dev_preflight.py -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/med_autoscience/dev_preflight.py tests/test_dev_preflight.py guides/repository_ci_preflight.md
git commit -m "docs: add repository ci preflight guide"
```

### Task 5: 收紧远端 CI 触发面并回归验证

**Files:**
- Modify: `.github/workflows/ci.yml`
- Modify: `tests/test_release_workflow.py`

- [ ] **Step 1: 写 workflow 触发面失败测试**

```python
def test_ci_workflow_only_triggers_on_push_main_and_development() -> None:
    workflow = yaml.safe_load(Path(".github/workflows/ci.yml").read_text(encoding="utf-8"))
    assert "pull_request" not in workflow["on"]
    assert workflow["on"]["push"]["branches"] == ["main", "development"]
```

- [ ] **Step 2: 运行 workflow 测试确认失败**

Run: `uv run pytest tests/test_release_workflow.py -q -k ci_workflow_only_triggers`
Expected: FAIL，当前 `pull_request` 仍存在

- [ ] **Step 3: 修改 `ci.yml` 与对应测试**

```yaml
on:
  push:
    branches:
      - main
      - development
```

- [ ] **Step 4: 运行目标测试与构建验证**

Run: `uv run pytest tests/test_dev_preflight_contract.py tests/test_dev_preflight.py tests/test_cli.py tests/test_release_workflow.py tests/test_codex_plugin.py tests/test_codex_plugin_installer.py tests/test_codex_plugin_installer_script.py tests/test_display_schema_contract.py tests/test_display_surface_materialization.py tests/test_display_layout_qc.py tests/test_publication_gate.py tests/test_medical_publication_surface.py tests/test_study_runtime_router.py tests/test_runtime_transport_med_deepscientist.py tests/test_runtime_protocol_study_runtime.py tests/test_runtime_protocol_runtime_watch.py -q`
Expected: PASS

Run: `uv run python -m build --sdist --wheel`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add .github/workflows/ci.yml tests/test_release_workflow.py
git commit -m "ci: narrow workflow triggers and add local preflight"
```

## Spec Coverage Check

- CI 仅保留主线 push 告警：Task 5
- 本地显式 `preflight-changes` 入口：Task 3
- checked-in contract：Task 1
- 执行器结构化输出：Task 2
- `--files` / `--staged` / `--base-ref`：Task 3 + Task 4
- 维护指南：Task 4
- 未分类改动显式失败：Task 1 + Task 2

## Placeholder Scan

- 无 `TODO` / `TBD`
- 每个任务都列出文件、测试和命令
- 所有新增类型、函数、命令名称在任务中都有定义

## Type Consistency Check

- `ClassificationResult` 由 contract 层返回
- `PreflightResult` / `CommandResult` 由执行器层返回
- CLI 始终调用 `dev_preflight.run_preflight(...)`
- 改动采集统一通过 `collect_changed_files(...)`
