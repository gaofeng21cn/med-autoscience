from __future__ import annotations

import importlib
from dataclasses import replace
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


def test_run_upgrade_check_reports_upgrade_available(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module,
        "inspect_deepscientist_repo",
        lambda *, repo_root, refresh=False: {
            "configured": True,
            "repo_root": str(repo_root),
            "repo_exists": True,
            "is_git_repo": True,
            "refresh_attempted": refresh,
            "refresh_succeeded": refresh,
            "current_branch": "main",
            "head_commit": "1111111",
            "origin_main_commit": "2222222",
            "ahead_count": 0,
            "behind_count": 2,
            "working_tree_clean": True,
            "upstream_update_available": True,
        },
    )
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
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {
            "all_targets_ready": True,
            "targets": [
                {"skill_id": "scout", "status": "overlay_applied"},
                {"skill_id": "write", "status": "overlay_applied"},
            ],
        },
    )

    result = module.run_upgrade_check(profile, refresh=True)

    assert result["decision"] == "upgrade_available"
    assert result["repo_check"]["behind_count"] == 2
    assert result["repo_check"]["upstream_update_available"] is True
    assert "pull_origin_main_then_reapply_medical_overlay" in result["recommended_actions"]


def test_run_upgrade_check_blocks_dirty_repo(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module,
        "inspect_deepscientist_repo",
        lambda *, repo_root, refresh=False: {
            "configured": True,
            "repo_root": str(repo_root),
            "repo_exists": True,
            "is_git_repo": True,
            "refresh_attempted": refresh,
            "refresh_succeeded": False,
            "current_branch": "main",
            "head_commit": "1111111",
            "origin_main_commit": "1111111",
            "ahead_count": 0,
            "behind_count": 0,
            "working_tree_clean": False,
            "upstream_update_available": False,
        },
    )
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
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {"all_targets_ready": True, "targets": [{"skill_id": "write", "status": "overlay_applied"}]},
    )

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["decision"] == "blocked_dirty_repo"
    assert "clean_or_commit_deepscientist_repo_before_upgrade" in result["recommended_actions"]


def test_run_upgrade_check_requests_branch_review_when_not_on_main(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module,
        "inspect_deepscientist_repo",
        lambda *, repo_root, refresh=False: {
            "configured": True,
            "repo_root": str(repo_root),
            "repo_exists": True,
            "is_git_repo": True,
            "refresh_attempted": refresh,
            "refresh_succeeded": False,
            "current_branch": "codex/pr2-external-controller-docs",
            "head_commit": "3333333",
            "origin_main_commit": "2222222",
            "ahead_count": 1,
            "behind_count": 0,
            "working_tree_clean": True,
            "upstream_update_available": False,
        },
    )
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
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {"all_targets_ready": True, "targets": [{"skill_id": "write", "status": "overlay_applied"}]},
    )

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["decision"] == "needs_branch_review"
    assert "review_local_branch_before_upgrade" in result["recommended_actions"]


def test_run_upgrade_check_blocks_when_repo_root_missing(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = replace(make_profile(tmp_path), deepscientist_repo_root=None)

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
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {"all_targets_ready": True, "targets": [{"skill_id": "write", "status": "overlay_applied"}]},
    )

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["decision"] == "blocked_repo_not_configured"
    assert "configure_deepscientist_repo_root_in_profile" in result["recommended_actions"]


def test_run_upgrade_check_blocks_when_behavior_gate_not_ready(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    def _repo_check_should_not_run(*, repo_root, refresh=False):
        raise AssertionError("inspect_deepscientist_repo should not run when behavior gate is not ready")

    monkeypatch.setattr(module, "inspect_deepscientist_repo", _repo_check_should_not_run)
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
            runtime_contract={"ready": True, "checks": {}},
            launcher_contract={"ready": True, "checks": {}},
            behavior_gate={
                "ready": False,
                "phase_25_ready": False,
                "schema_version": "v1",
                "critical_overrides": [],
                "checks": {},
            },
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {"all_targets_ready": True, "targets": [{"skill_id": "write", "status": "overlay_applied"}]},
    )

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["decision"] == "blocked_behavior_equivalence_gate"
    assert "complete_phase_25_behavior_equivalence_gate" in result["recommended_actions"]


def test_run_upgrade_check_exposes_repo_manifest(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.deepscientist_upgrade_check")
    doctor = importlib.import_module("med_autoscience.doctor")
    profile = make_profile(tmp_path)

    manifest_blob = {
        "engine_family": "MedicalDeepScientist",
        "freeze_base_commit": "abc123",
        "applied_commits": ["001"],
        "is_controlled_fork": True,
    }

    monkeypatch.setattr(
        module,
        "inspect_deepscientist_repo",
        lambda *, repo_root, refresh=False: {
            "configured": True,
            "repo_root": str(repo_root),
            "repo_exists": True,
            "is_git_repo": True,
            "refresh_attempted": refresh,
            "refresh_succeeded": True,
            "current_branch": "main",
            "head_commit": "1111111",
            "origin_main_commit": "1111111",
            "ahead_count": 0,
            "behind_count": 0,
            "working_tree_clean": True,
            "upstream_update_available": False,
            "repo_manifest": manifest_blob,
        },
    )
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
        ),
    )
    monkeypatch.setattr(
        module,
        "describe_medical_overlay",
        lambda **_: {"all_targets_ready": True, "targets": [{"skill_id": "write", "status": "overlay_applied"}]},
    )

    result = module.run_upgrade_check(profile, refresh=False)

    assert result["repo_check"]["repo_manifest"] is manifest_blob
