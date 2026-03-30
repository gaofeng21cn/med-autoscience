from __future__ import annotations

import importlib
from pathlib import Path


def make_profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    return profiles.WorkspaceProfile(
        name="nfpitnet",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "deepscientist" / "runtime",
        deepscientist_repo_root=tmp_path / "DeepScientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("scout", "idea", "decision", "write", "finalize"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=(
            "clinical_classifier",
            "clinical_subtype_reconstruction",
            "external_validation_model_update",
        ),
        default_submission_targets=(),
    )


def test_inspect_workspace_contracts_reports_missing_items(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)

    result = module.inspect_workspace_contracts(profile)

    assert result["runtime_contract"]["checks"]["runtime_root_exists"] is False
    assert result["runtime_contract"]["checks"]["deepscientist_runtime_root_exists"] is False
    assert result["runtime_contract"]["checks"]["runtime_root_matches_deepscientist_runtime"] is True
    assert result["runtime_contract"]["ready"] is False

    assert result["launcher_contract"]["checks"]["medautoscience_config_env_exists"] is False
    assert result["launcher_contract"]["checks"]["deepscientist_config_env_exists"] is False
    assert result["launcher_contract"]["checks"]["deepscientist_bin_dir_exists"] is False
    assert result["launcher_contract"]["checks"]["deepscientist_repo_root_configured"] is True
    assert result["launcher_contract"]["ready"] is False

    assert result["behavior_gate"]["checks"]["gate_file_exists"] is False
    assert result["behavior_gate"]["phase_25_ready"] is False
    assert result["behavior_gate"]["ready"] is False


def test_inspect_workspace_contracts_accepts_phase_25_ready_gate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    profile.runtime_root.mkdir(parents=True)
    profile.deepscientist_runtime_root.mkdir(parents=True, exist_ok=True)

    medautosci_config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    medautosci_config.parent.mkdir(parents=True, exist_ok=True)
    medautosci_config.write_text("MEDAUTOSCI_PROFILE=nfpitnet\n", encoding="utf-8")

    deepscientist_root = profile.workspace_root / "ops" / "deepscientist"
    deepscientist_root.mkdir(parents=True, exist_ok=True)
    (deepscientist_root / "config.env").write_text("DEEPSCIENTIST_PROFILE=nfpitnet\n", encoding="utf-8")
    (deepscientist_root / "bin").mkdir(parents=True, exist_ok=True)
    (deepscientist_root / "behavior_equivalence_gate.yaml").write_text(
        "\n".join(
            [
                "schema_version: v1",
                "phase_25_ready: true",
                "critical_overrides:",
                "  - id: no_degrade_runtime_watch",
                "    source_path: ops/deepscientist/policies/runtime_watch.md",
                "    status: approved",
                "    target_surface: runtime_watch",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.inspect_workspace_contracts(profile)

    assert result["runtime_contract"]["ready"] is True
    assert result["launcher_contract"]["ready"] is True
    assert result["behavior_gate"]["checks"]["schema_version_present"] is True
    assert result["behavior_gate"]["checks"]["phase_25_ready_is_bool"] is True
    assert result["behavior_gate"]["checks"]["critical_overrides_valid"] is True
    assert result["behavior_gate"]["phase_25_ready"] is True
    assert result["behavior_gate"]["ready"] is True
    assert result["behavior_gate"]["critical_overrides"] == [
        {
            "id": "no_degrade_runtime_watch",
            "source_path": "ops/deepscientist/policies/runtime_watch.md",
            "status": "approved",
            "target_surface": "runtime_watch",
        }
    ]


def test_inspect_workspace_contracts_rejects_invalid_override_shape(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    profile.runtime_root.mkdir(parents=True)
    profile.deepscientist_runtime_root.mkdir(parents=True, exist_ok=True)

    medautosci_config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    medautosci_config.parent.mkdir(parents=True, exist_ok=True)
    medautosci_config.write_text("MEDAUTOSCI_PROFILE=nfpitnet\n", encoding="utf-8")

    deepscientist_root = profile.workspace_root / "ops" / "deepscientist"
    deepscientist_root.mkdir(parents=True, exist_ok=True)
    (deepscientist_root / "config.env").write_text("DEEPSCIENTIST_PROFILE=nfpitnet\n", encoding="utf-8")
    (deepscientist_root / "bin").mkdir(parents=True, exist_ok=True)
    (deepscientist_root / "behavior_equivalence_gate.yaml").write_text(
        "\n".join(
            [
                "schema_version: v1",
                "phase_25_ready: true",
                "critical_overrides:",
                "  - id: malformed_override",
                "    source_path: ops/deepscientist/policies/runtime_watch.md",
                "    status: approved",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.inspect_workspace_contracts(profile)

    assert result["behavior_gate"]["checks"]["critical_overrides_valid"] is False
    assert result["behavior_gate"]["phase_25_ready"] is True
    assert result["behavior_gate"]["ready"] is False


def test_doctor_report_renders_auditable_contract_sections(tmp_path: Path) -> None:
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    rendered = doctor.render_doctor_report(doctor.build_doctor_report(profile))

    assert "runtime_contract: " in rendered
    assert "launcher_contract: " in rendered
    assert "behavior_gate: " in rendered
