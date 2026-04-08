from __future__ import annotations

import importlib
import json
import os
from pathlib import Path


def test_init_workspace_dry_run_reports_plan_without_writing_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "diabetes-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="diabetes",
        dry_run=True,
        force=False,
    )

    assert result["dry_run"] is True
    assert result["workspace_root"] == str(workspace_root)
    assert result["workspace_name"] == "diabetes"
    assert result["created_directories"]
    assert result["created_files"]
    assert not workspace_root.exists()


def test_init_workspace_creates_minimal_workspace_and_entry_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "glioma-workspace"

    result = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="glioma",
        dry_run=False,
        force=False,
    )

    assert result["dry_run"] is False
    assert workspace_root.exists()
    assert (workspace_root / "datasets").is_dir()
    assert (workspace_root / "contracts").is_dir()
    assert (workspace_root / "studies").is_dir()
    assert (workspace_root / "portfolio" / "data_assets").is_dir()
    assert (workspace_root / "portfolio" / "research_memory").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "prompts").is_dir()
    assert (workspace_root / "portfolio" / "research_memory" / "external_reports").is_dir()
    assert (workspace_root / "ops" / "medautoscience" / "bin").is_dir()
    assert (workspace_root / "ops" / "med-deepscientist" / "bin").is_dir()

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "glioma.local.toml"
    assert profile_path.is_file()
    profile_text = profile_path.read_text(encoding="utf-8")
    assert 'name = "glioma"' in profile_text
    assert f'workspace_root = "{workspace_root}"' in profile_text
    assert 'default_startup_anchor_policy = "scout_first_for_continue_existing_state"' in profile_text
    assert 'legacy_code_execution_policy = "forbid_without_user_approval"' in profile_text
    assert 'public_data_discovery_policy = "required_for_scout_route_selection"' in profile_text
    assert 'startup_boundary_requirements = ["paper_framing", "journal_shortlist", "evidence_package"]' in profile_text
    assert '"analysis-campaign", "figure-polish", "write"' in profile_text
    assert "enable_autofigure_edit" not in profile_text
    assert "autofigure_edit_bootstrap_mode" not in profile_text
    assert "autofigure_edit_service_url" not in profile_text

    med_config = workspace_root / "ops" / "medautoscience" / "config.env"
    deep_config = workspace_root / "ops" / "med-deepscientist" / "config.env"
    med_shared = workspace_root / "ops" / "medautoscience" / "bin" / "_shared.sh"
    ds_shared = workspace_root / "ops" / "med-deepscientist" / "bin" / "_shared.sh"
    assert med_config.is_file()
    assert deep_config.is_file()
    assert med_shared.is_file()
    assert ds_shared.is_file()
    med_shared_text = med_shared.read_text(encoding="utf-8")
    ds_shared_text = ds_shared.read_text(encoding="utf-8")
    assert 'uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python -m med_autoscience.cli "$@"' in med_shared_text
    assert 'uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - "${PROFILE_PATH}"' in ds_shared_text
    assert 'CONTRACT_JSON="${payload_json}" uv run --directory "${MED_AUTOSCIENCE_REPO_RESOLVED}" python - <<' in ds_shared_text

    show_profile = workspace_root / "ops" / "medautoscience" / "bin" / "show-profile"
    enter_study = workspace_root / "ops" / "medautoscience" / "bin" / "enter-study"
    resolve_journal_shortlist = workspace_root / "ops" / "medautoscience" / "bin" / "resolve-journal-shortlist"
    init_portfolio_memory = workspace_root / "ops" / "medautoscience" / "bin" / "init-portfolio-memory"
    portfolio_memory_status = workspace_root / "ops" / "medautoscience" / "bin" / "portfolio-memory-status"
    prepare_external_research = workspace_root / "ops" / "medautoscience" / "bin" / "prepare-external-research"
    external_research_status = workspace_root / "ops" / "medautoscience" / "bin" / "external-research-status"
    ds_doctor = workspace_root / "ops" / "med-deepscientist" / "bin" / "doctor"
    assert show_profile.is_file()
    assert enter_study.is_file()
    assert resolve_journal_shortlist.is_file()
    assert init_portfolio_memory.is_file()
    assert portfolio_memory_status.is_file()
    assert prepare_external_research.is_file()
    assert external_research_status.is_file()
    assert ds_doctor.is_file()
    assert os.access(show_profile, os.X_OK)
    assert os.access(enter_study, os.X_OK)
    assert os.access(resolve_journal_shortlist, os.X_OK)
    assert os.access(init_portfolio_memory, os.X_OK)
    assert os.access(portfolio_memory_status, os.X_OK)
    assert os.access(prepare_external_research, os.X_OK)
    assert os.access(external_research_status, os.X_OK)
    assert os.access(ds_doctor, os.X_OK)

    portfolio_memory_readme = workspace_root / "portfolio" / "research_memory" / "README.md"
    portfolio_memory_registry = workspace_root / "portfolio" / "research_memory" / "registry.yaml"
    assert portfolio_memory_readme.is_file()
    assert portfolio_memory_registry.is_file()
    assert "Portfolio Research Memory" in portfolio_memory_readme.read_text(encoding="utf-8")

    root_readme = workspace_root / "README.md"
    assert root_readme.is_file()
    root_readme_text = root_readme.read_text(encoding="utf-8")
    assert "workspace" in root_readme_text.lower()
    assert "ops/medautoscience/bin/show-profile" in root_readme_text
    assert "不要直接通过 `med-deepscientist` UI、CLI 或 daemon HTTP API 发起研究 quest" in root_readme_text
    assert "portfolio/research_memory/" in root_readme_text

    deepscientist_readme = workspace_root / "ops" / "med-deepscientist" / "README.md"
    assert deepscientist_readme.is_file()
    deepscientist_readme_text = deepscientist_readme.read_text(encoding="utf-8")
    assert "runtime 运维面" in deepscientist_readme_text
    assert "不是研究入口" in deepscientist_readme_text
    assert "ops/medautoscience/bin/enter-study" in deepscientist_readme_text

    workspace_pyproject = workspace_root / "pyproject.toml"
    assert workspace_pyproject.is_file()
    workspace_pyproject_text = workspace_pyproject.read_text(encoding="utf-8")
    expected_repo_relpath = Path(os.path.relpath(Path(module.__file__).resolve().parents[3], workspace_root)).as_posix()
    assert 'name = "glioma-workspace"' in workspace_pyproject_text
    assert 'description = "Managed Python environment for the glioma workspace."' in workspace_pyproject_text
    assert '"med-autoscience"' in workspace_pyproject_text
    assert "[tool.uv.sources]" in workspace_pyproject_text
    assert f'med-autoscience = {{ path = "{expected_repo_relpath}", editable = true }}' in workspace_pyproject_text

    workspace_rules = workspace_root / "WORKSPACE_AUTOSCIENCE_RULES.md"
    assert workspace_rules.is_file()
    workspace_rules_text = workspace_rules.read_text(encoding="utf-8")
    assert "优先复用 MedAutoScience 已覆盖的成熟 controller / CLI / overlay skill" in workspace_rules_text
    assert "边界明确且 startup-ready 后，默认切入 `med-deepscientist` managed runtime 的自动持续推进" in workspace_rules_text
    assert "必须显式通知用户自动驾驶已启动或已被检测到，并提供监督入口" in workspace_rules_text
    assert "前台必须立即进入 supervisor-only 监管态" in workspace_rules_text
    assert "不得直接写入 runtime-owned 的 study / quest / paper surface" in workspace_rules_text
    assert "portfolio-memory-status" in workspace_rules_text
    assert "prepare-external-research" in workspace_rules_text


def test_init_workspace_is_idempotent_and_force_overwrites_files(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_init")
    workspace_root = tmp_path / "pituitary-workspace"

    first = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert first["created_files"]

    profile_path = workspace_root / "ops" / "medautoscience" / "profiles" / "pituitary.local.toml"
    profile_path.write_text("# local edit\n", encoding="utf-8")

    second = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=False,
    )
    assert str(profile_path) in second["skipped_files"]
    assert profile_path.read_text(encoding="utf-8") == "# local edit\n"

    third = module.init_workspace(
        workspace_root=workspace_root,
        workspace_name="pituitary",
        dry_run=False,
        force=True,
    )
    assert str(profile_path) in third["overwritten_files"]
    assert 'name = "pituitary"' in profile_path.read_text(encoding="utf-8")
