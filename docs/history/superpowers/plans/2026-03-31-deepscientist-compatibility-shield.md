# DeepScientist Compatibility Shield Implementation Plan

Owner: `MedAutoScience`
Purpose: `superpowers_history_record`
State: `history_provenance`
Machine boundary: 人读历史过程稿。当前 contract、runtime truth、policy truth、regression oracle 和 owner boundary 继续归核心 docs、contracts、source、tests、runtime/controller surfaces 和 owner receipts。

Read rule: 本文是 repo-tracked Superpowers 过程稿的历史快照。正文中的 REQUIRED SUB-SKILL、checkbox、File Structure、旧 CLI/MCP/runtime/workspace 路径、DeepScientist/MDS/Hermes 或 current/default wording 只按当时 design/plan provenance 读取；当前 MAS truth、执行顺序、runtime owner、quality/publication/artifact authority 和 regression oracle 以 active owner docs、核心五件套、contracts、source、tests 与 live read-model 为准。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `MedAutoScience` 变成 `DeepScientist` 的兼容护城河，强制安装并验证论文绘图依赖、禁止手拼 SVG 降级、让 quest runtime 的 overlay 成为权威来源，并把医学 SCI figure hard gate 前推到 figure route。

**Architecture:** 优先采用 `MedAutoScience-only` 实现，不先改 `DeepScientist` runner。运行时依赖通过新的 Python environment contract 统一检查；skill 权威性通过在 `ensure-study-runtime` 中把 quest `.codex/skills` 重覆写为 overlay，并把 `create_and_start` 拆成“先 create、覆写 overlay、再 resume”；figure 文字污染继续由 `medical_publication_surface` 扫描，但新增更明确的图内 prose / summary-card 拦截规则。

**Tech Stack:** Python 3.12, `uv`, `pytest`, `PyYAML`, `matplotlib`, `pandas`

---

## File Map

- Create: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/python_environment_contract.py`
  - 统一声明 `matplotlib` / `pandas` 是论文 figure 的强制依赖。
  - 暴露 `inspect_python_environment_contract()` 与 `ensure_python_environment_contract()`。
- Create: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/templates/deepscientist-figure-polish.SKILL.md`
  - 强制医学 SCI figure 约束，并显式禁止 stdlib-only SVG fallback。
- Modify: `/Users/gaofeng/workspace/med-autoscience/pyproject.toml`
  - 将 `matplotlib` / `pandas` 升级为受管 runtime 依赖。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/workspace_contracts.py`
  - 把 Python environment contract 纳入 runtime contract。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/doctor.py`
  - doctor report 展示 Python environment contract。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/cli.py`
  - `bootstrap` 执行依赖检查/安装并回报结果。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_runtime_router.py`
  - `ensure-study-runtime` 在 create/resume 前验证环境并把 quest overlay 变成权威源。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/constants.py`
  - 将 `figure-polish` 纳入默认 overlay skill 集。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/installer.py`
  - 支持 `figure-polish` 模板，复用 workspace `.codex/skills` 向 quest runtime 重覆写。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/policies/medical_publication_surface.py`
  - 增加图内 prose / summary-card 类污染的 forbidden patterns。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/medical_publication_surface.py`
  - 继续扫描 generated SVG/JSON，并把新污染类型归入 blocker。
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/deepscientist_upgrade_check.py`
  - 把 compatibility shield readiness 纳入升级放行条件。
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_python_environment_contract.py`
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py`
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_cli.py`
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py`
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py`
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_medical_publication_surface.py`
- Test: `/Users/gaofeng/workspace/med-autoscience/tests/test_deepscientist_upgrade_check.py`

### Task 1: Add Python Environment Contract

**Files:**
- Create: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/python_environment_contract.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/pyproject.toml`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_python_environment_contract.py`

- [ ] **Step 1: Write the failing tests**

```python
from __future__ import annotations

import importlib
from pathlib import Path
import tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_project_declares_matplotlib_and_pandas_as_runtime_dependencies() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    runtime_dependencies = pyproject["project"]["dependencies"]

    assert any(requirement.startswith("matplotlib") for requirement in runtime_dependencies)
    assert any(requirement.startswith("pandas") for requirement in runtime_dependencies)


def test_inspect_python_environment_contract_reports_missing_required_modules(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.python_environment_contract")
    real_import_module = module.importlib.import_module

    def fake_import_module(name: str):
        if name in {"matplotlib", "pandas"}:
            raise ModuleNotFoundError(name)
        return real_import_module(name)

    monkeypatch.setattr(module.importlib, "import_module", fake_import_module)

    report = module.inspect_python_environment_contract()

    assert report["ready"] is False
    assert report["checks"]["matplotlib_importable"] is False
    assert report["checks"]["pandas_importable"] is False
    assert "python_environment.matplotlib_importable" in report["issues"]
    assert "python_environment.pandas_importable" in report["issues"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/test_python_environment_contract.py -q
```

Expected:

- `test_project_declares_matplotlib_and_pandas_as_runtime_dependencies` fails because `pyproject.toml` 还没声明依赖。
- `test_inspect_python_environment_contract_reports_missing_required_modules` fails because新模块还不存在。

- [ ] **Step 3: Write minimal implementation**

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/python_environment_contract.py`

```python
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path
from typing import Any


REQUIRED_RUNTIME_MODULES = ("matplotlib", "pandas")
REPO_ROOT = Path(__file__).resolve().parents[1]


def _collect_check_issues(checks: dict[str, bool], *, prefix: str) -> list[str]:
    return [f"{prefix}.{name}" for name, ok in checks.items() if not ok]


def inspect_python_environment_contract() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    modules: dict[str, dict[str, str | None]] = {}
    for module_name in REQUIRED_RUNTIME_MODULES:
        check_key = f"{module_name}_importable"
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            checks[check_key] = False
            modules[module_name] = {"version": None}
            continue
        checks[check_key] = True
        modules[module_name] = {"version": str(getattr(module, "__version__", None) or "") or None}
    return {
        "ready": all(checks.values()),
        "checks": checks,
        "issues": _collect_check_issues(checks, prefix="python_environment"),
        "modules": modules,
        "interpreter": sys.executable,
    }


def ensure_python_environment_contract() -> dict[str, Any]:
    before = inspect_python_environment_contract()
    if before["ready"]:
        return {"action": "already_ready", "before": before, "after": before}

    completed = subprocess.run(
        ["uv", "sync"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    after = inspect_python_environment_contract()
    return {
        "action": "uv_sync",
        "before": before,
        "after": after,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
```

`/Users/gaofeng/workspace/med-autoscience/pyproject.toml`

```toml
[project]
dependencies = [
  "PyYAML>=6.0",
  "matplotlib>=3.9",
  "pandas>=2.2",
]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/test_python_environment_contract.py -q
```

Expected:

- 2 tests pass.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/med_autoscience/python_environment_contract.py tests/test_python_environment_contract.py
git commit -m "feat: add managed python environment contract"
```

### Task 2: Surface Environment Contract In Workspace Checks, Doctor, And Bootstrap

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/workspace_contracts.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/doctor.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/cli.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

`/Users/gaofeng/workspace/med-autoscience/tests/test_workspace_contracts.py`

```python
def test_inspect_workspace_contracts_includes_python_environment_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module,
        "inspect_python_environment_contract",
        lambda: {
            "ready": False,
            "checks": {"matplotlib_importable": False, "pandas_importable": True},
            "issues": ["python_environment.matplotlib_importable"],
        },
    )

    result = module.inspect_workspace_contracts(profile)

    assert result["runtime_contract"]["checks"]["python_environment_ready"] is False
    assert result["runtime_contract"]["python_environment"]["ready"] is False
```

`/Users/gaofeng/workspace/med-autoscience/tests/test_cli.py`

```python
def test_bootstrap_command_reports_python_environment_bootstrap(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        cli,
        "build_doctor_report",
        lambda profile: importlib.import_module("med_autoscience.doctor").DoctorReport(
            python_version="3.12.0",
            profile=profile,
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            deepscientist_runtime_exists=True,
            medical_overlay_enabled=True,
            medical_overlay_ready=True,
            runtime_contract={"ready": True, "checks": {}, "python_environment": {"ready": True}},
        ),
    )
    monkeypatch.setattr(
        cli,
        "ensure_python_environment_contract",
        lambda: {"action": "already_ready", "after": {"ready": True}},
    )

    exit_code = cli.main(["bootstrap", "--profile", str(profile_path)])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["python_environment_bootstrap"]["after"]["ready"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/test_workspace_contracts.py tests/test_cli.py -q
```

Expected:

- workspace contract 测试失败，因为 `runtime_contract` 里还没有 `python_environment`。
- bootstrap CLI 测试失败，因为 `bootstrap` 结果还没有 `python_environment_bootstrap` 字段。

- [ ] **Step 3: Write minimal implementation**

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/workspace_contracts.py`

```python
from med_autoscience.python_environment_contract import inspect_python_environment_contract


def inspect_workspace_contracts(profile: WorkspaceProfile) -> dict[str, Any]:
    python_environment = inspect_python_environment_contract()
    runtime_checks: dict[str, bool] = {
        "runtime_root_matches_deepscientist_runtime": profile.runtime_root == runtime_root_expected,
        "runtime_root_exists": profile.runtime_root.exists(),
        "deepscientist_runtime_root_exists": profile.deepscientist_runtime_root.exists(),
        "python_environment_ready": bool(python_environment.get("ready")),
    }
    runtime_contract = {
        "ready": all(runtime_checks.values()),
        "checks": runtime_checks,
        "issues": _collect_check_issues(runtime_checks, prefix="runtime_contract"),
        "python_environment": python_environment,
        ...
    }
```

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/doctor.py`

```python
class DoctorReport:
    ...
    runtime_contract: dict[str, object] = field(default_factory=dict)


def render_doctor_report(report: DoctorReport) -> str:
    lines = [
        ...
        f"runtime_contract: {json.dumps(report.runtime_contract, ensure_ascii=False, sort_keys=True)}",
    ]
```

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/cli.py`

```python
from med_autoscience.python_environment_contract import ensure_python_environment_contract

...
if args.command == "bootstrap":
    ...
    python_environment_bootstrap = ensure_python_environment_contract()
    result = {
        "profile": profile.name,
        "doctor": {...},
        "python_environment_bootstrap": python_environment_bootstrap,
        ...
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/test_workspace_contracts.py tests/test_cli.py -q
```

Expected:

- 新增环境 contract 测试通过。
- 既有 doctor/bootstrap 测试继续通过。

- [ ] **Step 5: Commit**

```bash
git add src/med_autoscience/workspace_contracts.py src/med_autoscience/doctor.py src/med_autoscience/cli.py tests/test_workspace_contracts.py tests/test_cli.py
git commit -m "feat: surface managed python environment contract"
```

### Task 3: Make Quest Overlay Authoritative And Cover Figure-Polish

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/constants.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/installer.py`
- Create: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/templates/deepscientist-figure-polish.SKILL.md`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_runtime_router.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py`

- [ ] **Step 1: Write the failing tests**

`/Users/gaofeng/workspace/med-autoscience/tests/test_overlay_installer.py`

```python
def test_install_medical_overlay_materializes_figure_polish_template(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.overlay.installer")
    home = tmp_path / "home"
    quest_root = tmp_path / "workspace"

    result = module.install_medical_overlay(
        quest_root=quest_root,
        home=home,
        skill_ids=("figure-polish",),
    )

    assert [item["skill_id"] for item in result["targets"]] == ["figure-polish"]
    skill_path = quest_root / ".codex" / "skills" / "deepscientist-figure-polish" / "SKILL.md"
    assert skill_path.exists()
    assert "Do not fall back to stdlib-only SVG composition" in skill_path.read_text(encoding="utf-8")
```

`/Users/gaofeng/workspace/med-autoscience/tests/test_study_runtime_router.py`

```python
def test_ensure_study_runtime_creates_then_reapplies_overlay_before_resume(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    created: dict[str, object] = {}
    overlay_calls: list[Path] = []
    resumed: list[str] = []

    monkeypatch.setattr(module, "inspect_workspace_contracts", lambda profile: {"overall_ready": True, "runtime_contract": {"ready": True}, "launcher_contract": {"ready": True}, "behavior_gate": {"ready": True, "phase_25_ready": True}})
    monkeypatch.setattr(module.startup_data_readiness_controller, "startup_data_readiness", lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"))
    monkeypatch.setattr(module.daemon_api, "create_quest", lambda *, runtime_root, payload: created.setdefault("payload", payload) or {"ok": True, "snapshot": {"quest_id": "001-risk", "quest_root": str(runtime_root / "001-risk"), "status": "created"}})
    monkeypatch.setattr(module.overlay_installer, "ensure_medical_overlay", lambda **kwargs: overlay_calls.append(Path(kwargs["quest_root"])) or {"post_status": {"all_targets_ready": True}})
    monkeypatch.setattr(module.daemon_api, "resume_quest", lambda *, runtime_root, quest_id, source: resumed.append(quest_id) or {"status": "running"})

    result = module.ensure_study_runtime(profile=profile, study_id="001-risk", source="medautosci-test")

    assert result["decision"] == "create_and_start"
    assert created["payload"]["auto_start"] is False
    assert overlay_calls == [profile.runtime_root / "001-risk"]
    assert resumed == ["001-risk"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/test_overlay_installer.py tests/test_study_runtime_router.py -q
```

Expected:

- overlay 测试失败，因为 `figure-polish` 还不在受支持 skill 集里。
- runtime router 测试失败，因为 `create_and_start` 还没有 `create -> reapply overlay -> resume` 顺序。

- [ ] **Step 3: Write minimal implementation**

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/constants.py`

```python
DEFAULT_MEDICAL_OVERLAY_SKILL_IDS = (
    "intake-audit",
    "scout",
    "baseline",
    "idea",
    "decision",
    "experiment",
    "analysis-campaign",
    "write",
    "review",
    "rebuttal",
    "figure-polish",
    "finalize",
)
```

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/installer.py`

```python
FULL_TEMPLATE_MAP = {
    "scout": "deepscientist-scout.SKILL.md",
    "idea": "deepscientist-idea.SKILL.md",
    "decision": "deepscientist-decision.SKILL.md",
    "write": "deepscientist-write.SKILL.md",
    "figure-polish": "deepscientist-figure-polish.SKILL.md",
    "finalize": "deepscientist-finalize.SKILL.md",
    "journal-resolution": "deepscientist-journal-resolution.SKILL.md",
}
```

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/overlay/templates/deepscientist-figure-polish.SKILL.md`

```md
---
name: figure-polish
description: Use when a quest needs a polished milestone chart, paper-facing figure, appendix figure, or a mandatory render-inspect-revise pass before treating a figure as final.
---

## Medical Figure Contract

- Paper-facing figures are evidence figures, not posters or infographics.
- Use `rtk uv run python ...` for any figure-rendering script that needs `matplotlib` or `pandas`.
- If `matplotlib` or `pandas` is unavailable, stop and repair the managed Python environment. Do not fall back to stdlib-only SVG composition.
- Visible figure text may include only panel labels, axes, legends, necessary statistical annotations, and minimal group/sample notes.
- Do not add summary cards, narrative paragraphs, vendor/tool mentions, or repository/service links inside the figure.
```

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/study_runtime_router.py`

```python
from med_autoscience.overlay import installer as overlay_installer


def _ensure_runtime_overlay(*, profile: WorkspaceProfile, quest_root: Path) -> dict[str, Any] | None:
    if not profile.enable_medical_overlay:
        return None
    return overlay_installer.ensure_medical_overlay(
        quest_root=quest_root,
        home=profile.workspace_root,
        skill_ids=profile.medical_overlay_skills,
        mode="reapply",
    )


if status["decision"] in {"create_and_start", "create_only"}:
    should_resume_after_create = status["decision"] == "create_and_start"
    create_payload = _build_create_payload(...)
    create_payload["auto_start"] = False
    daemon_result = daemon_api.create_quest(...)
    _ensure_runtime_overlay(profile=profile, quest_root=profile.runtime_root / status["quest_id"])
    if should_resume_after_create:
        daemon_result = daemon_api.resume_quest(
            runtime_root=profile.deepscientist_runtime_root,
            quest_id=str(status["quest_id"]),
            source=source,
        )
        status["quest_status"] = str(daemon_result.get("status") or "running")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/test_overlay_installer.py tests/test_study_runtime_router.py -q
```

Expected:

- `figure-polish` overlay 被正确安装。
- 新 quest 的首次运行路径改为 `create -> overlay -> resume`，不再让上游 quest skill 在首次自动启动时抢先生效。

- [ ] **Step 5: Commit**

```bash
git add src/med_autoscience/overlay/constants.py src/med_autoscience/overlay/installer.py src/med_autoscience/overlay/templates/deepscientist-figure-polish.SKILL.md src/med_autoscience/controllers/study_runtime_router.py tests/test_overlay_installer.py tests/test_study_runtime_router.py
git commit -m "feat: make quest overlay authoritative for managed figures"
```

### Task 4: Strengthen Medical Figure Hard Gate

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/policies/medical_publication_surface.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/medical_publication_surface.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_medical_publication_surface.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_surface_blocks_summary_card_text_inside_generated_svg(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(
        tmp_path,
        medicalized=True,
        ama_defaults=True,
        generated_figure_text_override="<svg><text>Key takeaway</text><text>Clinical message</text></svg>\n",
    )

    report = module.inspect_surface(quest_root=quest_root)

    assert report["clear"] is False
    assert "figure_surface_pollution_present" in report["blockers"]
    assert any(hit["pattern_id"] == "summary card label" for hit in report["findings"])
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/test_medical_publication_surface.py -q
```

Expected:

- 新测试失败，因为 `Key takeaway` / `Clinical message` 目前还不是 forbidden pattern。

- [ ] **Step 3: Write minimal implementation**

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/policies/medical_publication_surface.py`

```python
FORBIDDEN_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ...
    ("summary card label", "Key takeaway", r"\bKey takeaway\b", re.IGNORECASE),
    ("summary card label", "Take-home message", r"\bTake-home message\b", re.IGNORECASE),
    ("summary card label", "Clinical message", r"\bClinical message\b", re.IGNORECASE),
]
```

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/medical_publication_surface.py`

```python
def inspect_surface(quest_root: Path) -> dict[str, Any]:
    ...
    figure_text_hits = []
    for path in discover_figure_text_assets(state.paper_root, state.figure_catalog_path):
        figure_text_hits.extend(scan_text_file(path))
    findings.extend(figure_text_hits)
    if figure_text_hits:
        blockers.append("figure_surface_pollution_present")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/test_medical_publication_surface.py -q
```

Expected:

- 新的 SVG 污染样例被拦截。
- 既有 caption/tooling 污染测试继续通过。

- [ ] **Step 5: Commit**

```bash
git add src/med_autoscience/policies/medical_publication_surface.py src/med_autoscience/controllers/medical_publication_surface.py tests/test_medical_publication_surface.py
git commit -m "feat: hard-gate polluted medical figure text"
```

### Task 5: Gate Upstream Upgrades On Compatibility Shield Readiness

**Files:**
- Modify: `/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/deepscientist_upgrade_check.py`
- Modify: `/Users/gaofeng/workspace/med-autoscience/tests/test_deepscientist_upgrade_check.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_run_upgrade_check_blocks_when_compatibility_shield_not_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module,
        "build_doctor_report",
        lambda profile: doctor.DoctorReport(
            python_version="3.12.0",
            profile=profile,
            workspace_exists=True,
            runtime_exists=True,
            studies_exists=True,
            portfolio_exists=True,
            deepscientist_runtime_exists=True,
            medical_overlay_enabled=True,
            medical_overlay_ready=True,
            runtime_contract={
                "ready": False,
                "checks": {"python_environment_ready": False},
                "python_environment": {"ready": False},
            },
            launcher_contract={"ready": True, "checks": {}},
            behavior_gate={"ready": True, "phase_25_ready": True, "checks": {}},
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {
            "all_targets_ready": False,
            "targets": [{"skill_id": "figure-polish", "status": "not_installed"}],
        },
    )

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["decision"] == "blocked_compatibility_shield_not_ready"
    assert "repair_python_environment_and_overlay_before_upgrade" in result["recommended_actions"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
rtk uv run pytest tests/test_deepscientist_upgrade_check.py -q
```

Expected:

- 新测试失败，因为升级检查还不会识别 compatibility shield 未就绪。

- [ ] **Step 3: Write minimal implementation**

`/Users/gaofeng/workspace/med-autoscience/src/med_autoscience/controllers/deepscientist_upgrade_check.py`

```python
def _determine_decision(...):
    ...
    runtime_contract = workspace_check.get("runtime_contract")
    python_environment_ready = bool(
        (runtime_contract.get("python_environment") or {}).get("ready")
    ) if isinstance(runtime_contract, dict) else True
    if not python_environment_ready:
        actions.append("repair_python_environment_and_overlay_before_upgrade")
        return "blocked_compatibility_shield_not_ready", actions

    if overlay_check["enabled"] and not overlay_check["all_targets_ready"]:
        actions.append("repair_python_environment_and_overlay_before_upgrade")
        return "blocked_compatibility_shield_not_ready", actions
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
rtk uv run pytest tests/test_deepscientist_upgrade_check.py -q
```

Expected:

- 升级检查在兼容护城河未就绪时直接阻断。

- [ ] **Step 5: Commit**

```bash
git add src/med_autoscience/controllers/deepscientist_upgrade_check.py tests/test_deepscientist_upgrade_check.py
git commit -m "feat: gate upstream upgrades on compatibility shield"
```

### Task 6: End-To-End Verification

**Files:**
- Modify: none
- Test: existing targeted suites only

- [ ] **Step 1: Run the targeted regression suite**

Run:

```bash
rtk uv run pytest \
  tests/test_python_environment_contract.py \
  tests/test_workspace_contracts.py \
  tests/test_cli.py \
  tests/test_study_runtime_router.py \
  tests/test_overlay_installer.py \
  tests/test_medical_publication_surface.py \
  tests/test_deepscientist_upgrade_check.py \
  -q
```

Expected:

- All targeted tests pass.

- [ ] **Step 2: Re-run the doctor/bootstrap smoke paths**

Run:

```bash
rtk uv run python -m med_autoscience.cli doctor --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.workspace.toml
rtk uv run python -m med_autoscience.cli bootstrap --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.workspace.toml
```

Expected:

- doctor 输出里能看到 `runtime_contract` 中的 `python_environment`。
- bootstrap 输出里有 `python_environment_bootstrap`，并且 `after.ready` 为 `true`。

- [ ] **Step 3: Re-run a managed study-runtime dry verification**

Run:

```bash
rtk uv run python -m med_autoscience.cli study-runtime-status \
  --profile /Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/ops/medautoscience/profiles/dm-cvd-mortality-risk.workspace.toml \
  --study-id 001-dm-cvd-mortality-risk
```

Expected:

- 如果 Python environment contract 未就绪，返回明确阻断。
- 如果 contract 就绪，runtime 只会通过 quest overlay 权威源进入后续 managed run。

- [ ] **Step 4: Commit verification notes if needed**

```bash
git status --short
```

Expected:

- 没有意外未跟踪改动；若有调试残留，先清理，再继续。

## Self-Review

- Spec coverage:
  - `matplotlib/pandas` 强依赖 contract：Task 1 + Task 2
  - 禁止 stdlib SVG fallback：Task 3 template + Task 4 hard gate
  - MedAutoScience 作为 quest overlay 权威源：Task 3
  - 医学 SCI figure hard gate：Task 4
  - validated upstream version：Task 5
- Placeholder scan:
  - 没有 `TODO`、`TBD`、`implement later`。
- Type consistency:
  - 统一使用 `python_environment`、`python_environment_ready`、`blocked_compatibility_shield_not_ready` 这些字段名，后续实现不得改名漂移。

## Execution Handoff

Plan complete and saved to `/Users/gaofeng/workspace/med-autoscience/docs/superpowers/plans/2026-03-31-deepscientist-compatibility-shield.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 我按任务拆分，用 fresh subagent 逐个实现并在每步间复核

**2. Inline Execution** - 我在当前会话里直接按这个计划执行，分批做 TDD 和验证

Which approach?
