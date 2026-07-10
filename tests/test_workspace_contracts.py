from __future__ import annotations

from dataclasses import replace
import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_inspect_workspace_contracts_reports_missing_items_and_skips_repo_manifest(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    repo_root = profile.med_deepscientist_repo_root
    repo_root.mkdir(parents=True)
    (repo_root / "MEDICAL_FORK_MANIFEST.json").write_text(
        json.dumps({"schema_version": 1, "engine_id": "med-deepscientist"}),
        encoding="utf-8",
    )

    result = module.inspect_workspace_contracts(profile)
    assert result["runtime_contract"]["ready"] is False
    assert result["runtime_contract"]["historical_fixture_ref"]["read_only"] is True
    assert result["launcher_contract"]["retained_entry"] == "backend_audit"
    assert result["launcher_contract"]["default_runner_allowed"] is False
    assert result["launcher_contract"]["default_webui_allowed"] is False
    assert result["launcher_contract"]["explicit_archive_import_ref"]["read_only"] is True
    assert result["launcher_contract"]["repo_manifest"] == {
        "inspection_skipped": True,
        "skip_reason": "explicit_backend_audit_only",
        "repo_root": str(repo_root),
    }
    assert result["behavior_gate"]["surface_kind"] == "retired_behavior_equivalence_gate"
    assert result["behavior_gate"]["current_readiness_gate"] is False
    assert result["behavior_gate"]["ready"] is True
    assert result["overall_ready"] is False


def test_inspect_workspace_contracts_accepts_clean_mas_first_workspace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    profile = replace(
        profile,
        med_deepscientist_runtime_root=profile.workspace_root / "runtime",
    )
    profile.runtime_root.mkdir(parents=True)
    config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    config.parent.mkdir(parents=True)
    config.write_text(f"MEDAUTOSCI_PROFILE={profile.name}\n", encoding="utf-8")
    result = module.inspect_workspace_contracts(profile)
    assert result["runtime_contract"]["ready"] is True
    assert result["launcher_contract"]["ready"] is True
    assert result["launcher_contract"]["checks"]["controlled_backend_config_env_exists"] is False
    assert result["behavior_gate"]["surface_kind"] == "retired_behavior_equivalence_gate"
    assert result["behavior_gate"]["current_readiness_gate"] is False
    assert result["overall_ready"] is True


def test_inspect_workspace_contracts_rejects_configured_backend_launcher(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    config = module.build_workspace_runtime_layout_for_profile(profile).config_env_path
    config.parent.mkdir(parents=True)
    executable = tmp_path / "launcher"
    executable.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    executable.chmod(0o755)
    for launcher in ("ABS/PATH/ds", str(executable)):
        config.write_text(f"MED_DEEPSCIENTIST_LAUNCHER={launcher}\n", encoding="utf-8")
        result = module.inspect_workspace_contracts(profile)
        assert result["launcher_contract"]["ready"] is False
        assert "launcher_contract.default_mds_runner_configured" in result["launcher_contract"]["issues"]
