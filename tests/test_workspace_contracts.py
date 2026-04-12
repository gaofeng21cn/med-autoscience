from __future__ import annotations

import importlib
import json
from pathlib import Path


def make_profile(tmp_path: Path):
    profiles = importlib.import_module("med_autoscience.profiles")
    return profiles.WorkspaceProfile(
        name="nfpitnet",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
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
    assert result["runtime_contract"]["checks"]["med_deepscientist_runtime_root_exists"] is False
    assert result["runtime_contract"]["checks"]["runtime_root_matches_med_deepscientist_runtime"] is True
    assert result["runtime_contract"]["ready"] is False

    assert result["launcher_contract"]["checks"]["medautoscience_config_env_exists"] is False
    assert result["launcher_contract"]["checks"]["med_deepscientist_config_env_exists"] is False
    assert result["launcher_contract"]["checks"]["med_deepscientist_bin_dir_exists"] is False
    assert result["launcher_contract"]["checks"]["med_deepscientist_repo_root_configured"] is True
    assert result["launcher_contract"]["ready"] is False

    assert result["behavior_gate"]["checks"]["gate_file_exists"] is False
    assert result["behavior_gate"]["phase_25_ready"] is False
    assert result["behavior_gate"]["ready"] is False


def test_inspect_workspace_contracts_accepts_phase_25_ready_gate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    profile.runtime_root.mkdir(parents=True)
    profile.med_deepscientist_runtime_root.mkdir(parents=True, exist_ok=True)

    medautosci_config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    medautosci_config.parent.mkdir(parents=True, exist_ok=True)
    medautosci_config.write_text("MEDAUTOSCI_PROFILE=nfpitnet\n", encoding="utf-8")

    deepscientist_root = profile.workspace_root / "ops" / "med-deepscientist"
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
                "    source_path: ops/med-deepscientist/policies/runtime_watch.md",
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
            "source_path": "ops/med-deepscientist/policies/runtime_watch.md",
            "status": "approved",
            "target_surface": "runtime_watch",
        }
    ]


def test_inspect_workspace_contracts_rejects_invalid_override_shape(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    profile.runtime_root.mkdir(parents=True)
    profile.med_deepscientist_runtime_root.mkdir(parents=True, exist_ok=True)

    medautosci_config = profile.workspace_root / "ops" / "medautoscience" / "config.env"
    medautosci_config.parent.mkdir(parents=True, exist_ok=True)
    medautosci_config.write_text("MEDAUTOSCI_PROFILE=nfpitnet\n", encoding="utf-8")

    deepscientist_root = profile.workspace_root / "ops" / "med-deepscientist"
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
                "    source_path: ops/med-deepscientist/policies/runtime_watch.md",
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
    assert "external_runtime_contract: " in rendered


def test_inspect_workspace_contracts_reports_repo_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.workspace_contracts")
    profile = make_profile(tmp_path)
    repo_root = profile.med_deepscientist_repo_root
    repo_root.mkdir(parents=True, exist_ok=True)
    manifest_path = repo_root / "MEDICAL_FORK_MANIFEST.json"
    manifest_payload = {
        "schema_version": 1,
        "engine_id": "med-deepscientist",
        "engine_family": "MedDeepScientist",
        "freeze_mode": "thin_fork",
        "upstream_source": {
            "repo_path": "/tmp/DeepScientist",
            "base_commit": "abc123",
        },
        "compatibility_contract": {
            "package_rename_applied": False,
            "daemon_api_shape_preserved": True,
            "quest_layout_preserved": True,
            "worktree_layout_preserved": True,
        },
        "applied_commits": [
            {"commit": "aaa", "kind": "runtime_bugfix", "summary": "first"},
            {"commit": "bbb", "kind": "runtime_bugfix", "summary": "second"},
        ],
        "lock_policy": {
            "mode": "regenerate_in_fork",
            "source_repo_was_dirty": True,
            "source_dirty_paths": ["uv.lock"],
        },
    }
    manifest_path.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    result = module.inspect_workspace_contracts(profile)
    manifest_checks = result["launcher_contract"]["manifest_checks"]
    assert manifest_checks["manifest_found"] is True
    assert manifest_checks["manifest_parsable"] is True

    repo_manifest = result["launcher_contract"]["repo_manifest"]
    assert repo_manifest["manifest_found"] is True
    assert repo_manifest["engine_family"] == manifest_payload["engine_family"]
    assert repo_manifest["freeze_base_commit"] == manifest_payload["upstream_source"]["base_commit"]
    assert repo_manifest["applied_commits"] == ("aaa", "bbb")
    assert repo_manifest["is_controlled_fork"] is True
