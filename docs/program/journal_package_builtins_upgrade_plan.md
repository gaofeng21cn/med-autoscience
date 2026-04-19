# Journal Package Builtins Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 MAS 的选刊与期刊定制投稿包升级成 controller-owned 内置能力，打通 shortlist、official requirements、journal package materialization、delivery sync 和 publication gate。

**Architecture:** 保留 `submission_minimal` 作为 generic package authority，在其上新增 `journal_requirements` contract 与 `journal_package` materializer。期刊特异交付面统一落到 study 浅层 `submission_packages/<journal_slug>/`，并由 publication gate 感知 completeness。

**Tech Stack:** Python 3.12、现有 `med_autoscience` CLI / controllers / runtime contracts、`pytest`、`uv`

---

## 文件结构与职责

### 新增文件

- `src/med_autoscience/journal_requirements.py`
  - journal requirement dataclass、slug/manifest 解析与序列化。
- `src/med_autoscience/controllers/journal_requirements.py`
  - `resolve-journal-requirements` controller。
- `src/med_autoscience/controllers/journal_package.py`
  - `materialize-journal-package` controller。
- `tests/test_journal_requirements.py`
  - requirement contract 与 durable artifact 覆盖。
- `tests/test_journal_requirements_controller.py`
  - controller 输出与错误路径覆盖。
- `docs/runtime/journal_package_builtins_upgrade_design.md`
  - 设计基线，已提交。

### 修改文件

- `src/med_autoscience/cli.py`
  - 新增 publication 子命令。
- `src/med_autoscience/controllers/__init__.py`
  - 暴露新 controller 模块。
- `src/med_autoscience/controllers/submission_targets.py`
  - target 结果暴露 `journal_slug` 与 requirements ref。
- `src/med_autoscience/controllers/study_delivery_sync.py`
  - 新增 shallow `submission_packages/<journal_slug>/` 同步面。
- `src/med_autoscience/controllers/publication_gate.py`
  - journal package 完整性检测与 apply 路径接线。
- `src/med_autoscience/policies/controller_first.py`
  - controller-first 流程追加 new controller 顺序。
- `tests/test_submission_targets_controller.py`
  - target 结果新增字段覆盖。
- `tests/test_study_delivery_sync.py`
  - submission package shallow sync 覆盖。
- `tests/test_publication_gate.py`
  - journal package gate 覆盖。
- `tests/test_controller_first_policy.py`
  - policy 文本覆盖。
- `tests/test_cli.py`
  - CLI 子命令存在性覆盖。

## Task 1：先用失败测试固定 journal requirements contract

**Files:**

- Create: `tests/test_journal_requirements.py`
- Create: `tests/test_journal_requirements_controller.py`
- Create: `src/med_autoscience/journal_requirements.py`
- Create: `src/med_autoscience/controllers/journal_requirements.py`

- [ ] **Step 1: 写失败测试，锁定最小 contract**

关键测试：

```python
def test_load_journal_requirements_manifest_round_trip(tmp_path: Path) -> None:
    ...
    assert payload["journal_slug"] == "rheumatology-international"
    assert payload["abstract_word_cap"] == 250
    assert payload["title_page_required"] is True


def test_resolve_journal_requirements_controller_writes_durable_outputs(tmp_path: Path) -> None:
    ...
    assert result["status"] == "resolved"
    assert (study_root / "paper" / "journal_requirements" / "rheumatology-international" / "requirements.json").exists()
    assert (study_root / "paper" / "journal_requirements" / "rheumatology-international" / "requirements.md").exists()
```

- [ ] **Step 2: 运行测试确认 RED**

Run:

```bash
uv run pytest -q tests/test_journal_requirements.py tests/test_journal_requirements_controller.py
```

Expected:

```text
ModuleNotFoundError
```

- [ ] **Step 3: 实现最小 requirement model 与 controller**

实现点：

```python
@dataclass(frozen=True)
class JournalRequirements:
    journal_name: str
    journal_slug: str
    official_guidelines_url: str
    publication_profile: str | None
    abstract_word_cap: int | None
    title_page_required: bool
    ...
```

```python
def resolve_journal_requirements(...):
    # 规范 journal_slug
    # 写 requirements.json
    # 写 requirements.md
    # 返回 resolved payload
```

- [ ] **Step 4: 重跑新测试确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_journal_requirements.py tests/test_journal_requirements_controller.py
```

Expected:

```text
all passed
```

## Task 2：用失败测试固定 CLI 与 submission target 接口

**Files:**

- Modify: `src/med_autoscience/cli.py`
- Modify: `src/med_autoscience/controllers/__init__.py`
- Modify: `src/med_autoscience/controllers/submission_targets.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_submission_targets_controller.py`
- Modify: `tests/test_controller_first_policy.py`

- [ ] **Step 1: 写失败测试，锁定 CLI 和 target 新字段**

关键测试：

```python
def test_publication_cli_includes_resolve_journal_requirements() -> None:
    ...


def test_publication_cli_includes_materialize_journal_package() -> None:
    ...


def test_resolve_submission_targets_controller_exposes_journal_slug(tmp_path: Path) -> None:
    ...
    assert result["primary_target"]["journal_slug"] == "journal-of-clinical-endocrinology-metabolism"
```

- [ ] **Step 2: 运行相关测试确认 RED**

Run:

```bash
uv run pytest -q tests/test_cli.py tests/test_submission_targets_controller.py tests/test_controller_first_policy.py
```

- [ ] **Step 3: 接好 CLI/controller/policy**

实现点：

```python
resolve_journal_requirements_parser = subparsers.add_parser("resolve-journal-requirements")
materialize_journal_package_parser = subparsers.add_parser("materialize-journal-package")
```

```python
item["journal_slug"] = slugify_journal_name(...)
item["journal_requirements_ref"] = ...
```

- [ ] **Step 4: 重跑相关测试确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_cli.py tests/test_submission_targets_controller.py tests/test_controller_first_policy.py
```

## Task 3：用失败测试固定 journal package materialization 与 shallow sync

**Files:**

- Create: `src/med_autoscience/controllers/journal_package.py`
- Modify: `src/med_autoscience/controllers/study_delivery_sync.py`
- Modify: `tests/test_study_delivery_sync.py`

- [ ] **Step 1: 写失败测试，锁定 stable shallow output**

关键测试：

```python
def test_materialize_journal_package_writes_submission_package_root(tmp_path: Path) -> None:
    ...
    assert (study_root / "submission_packages" / "rheumatology-international" / "submission_manifest.json").exists()
    assert (study_root / "submission_packages" / "rheumatology-international" / "SUBMISSION_TODO.md").exists()


def test_study_delivery_sync_preserves_submission_packages_when_manuscript_sync_refreshes(tmp_path: Path) -> None:
    ...
```

- [ ] **Step 2: 运行相关测试确认 RED**

Run:

```bash
uv run pytest -q tests/test_study_delivery_sync.py -k "submission_package or shallow"
```

- [ ] **Step 3: 实现 materializer 与 delivery sync**

实现点：

```python
def materialize_journal_package(...):
    # 读取 requirements + active paper artifacts
    # 复制/生成 main_manuscript、title_page、figure_legends、supplementary、manifest、zip
```

```python
submission_package_root = study_root / "submission_packages" / journal_slug
```

- [ ] **Step 4: 重跑相关测试确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_study_delivery_sync.py -k "submission_package or shallow"
```

## Task 4：用失败测试固定 publication gate 对 journal package 的感知

**Files:**

- Modify: `src/med_autoscience/controllers/publication_gate.py`
- Modify: `tests/test_publication_gate.py`

- [ ] **Step 1: 写失败测试，锁定 gate 对 requirements 和 journal package 的检查**

关键测试：

```python
def test_build_gate_report_reports_missing_journal_requirements_for_primary_target(tmp_path: Path) -> None:
    ...
    assert "missing_journal_requirements" in report["blockers"]


def test_build_gate_report_reports_missing_journal_package_for_primary_target(tmp_path: Path) -> None:
    ...
    assert "missing_journal_package" in report["blockers"]


def test_apply_publication_gate_syncs_journal_package_when_requirements_are_ready(tmp_path: Path, monkeypatch) -> None:
    ...
    assert sync_calls == [("finalize", "general_medical_journal", "rheumatology-international")]
```

- [ ] **Step 2: 运行相关测试确认 RED**

Run:

```bash
uv run pytest -q tests/test_publication_gate.py -k "journal_requirements or journal_package"
```

- [ ] **Step 3: 实现 gate 新 blocker 与 apply 路径**

实现点：

```python
blockers.append("missing_journal_requirements")
blockers.append("missing_journal_package")
```

```python
if apply and journal_target_ready:
    journal_package.materialize_journal_package(...)
```

- [ ] **Step 4: 重跑相关测试确认 GREEN**

Run:

```bash
uv run pytest -q tests/test_publication_gate.py -k "journal_requirements or journal_package"
```

## Task 5：跑聚焦验证并收口

**Files:**

- Modify: 以上实际变更文件

- [ ] **Step 1: 跑聚焦测试集合**

Run:

```bash
uv run pytest -q tests/test_journal_requirements.py tests/test_journal_requirements_controller.py tests/test_submission_targets_controller.py tests/test_study_delivery_sync.py tests/test_publication_gate.py tests/test_cli.py tests/test_controller_first_policy.py
```

- [ ] **Step 2: 跑仓库最小验证入口**

Run:

```bash
scripts/verify.sh
make test-meta
```

- [ ] **Step 3: 按功能边界整理提交**

建议提交：

```bash
git commit -m "feat: add journal requirement resolution controller"
git commit -m "feat: materialize journal specific submission packages"
git commit -m "test: cover journal package publication gate integration"
```

- [ ] **Step 4: 吸收回 main 并 push**

Run:

```bash
git checkout main
git merge --ff-only codex/journal-package-builtins-20260419T101315
git push origin main
git worktree remove .worktrees/codex-journal-package-builtins-20260419T101315
git branch -d codex/journal-package-builtins-20260419T101315
```
