from __future__ import annotations

import importlib
from pathlib import Path

import yaml


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_profile(tmp_path: Path, **overrides):
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    payload = {
        "name": "diabetes",
        "workspace_root": workspace_root,
        "runtime_root": workspace_root / "ops" / "deepscientist" / "runtime" / "quests",
        "studies_root": workspace_root / "studies",
        "portfolio_root": workspace_root / "portfolio",
        "deepscientist_runtime_root": workspace_root / "ops" / "deepscientist" / "runtime",
        "deepscientist_repo_root": tmp_path / "DeepScientist",
        "default_publication_profile": "general_medical_journal",
        "default_citation_style": "AMA",
        "enable_medical_overlay": True,
        "medical_overlay_scope": "workspace",
        "medical_overlay_skills": ("intake-audit", "baseline", "write", "finalize"),
        "research_route_bias_policy": "high_plasticity_medical",
        "preferred_study_archetypes": ("clinical_classifier",),
        "default_submission_targets": (),
        "default_startup_anchor_policy": "scout_first_for_continue_existing_state",
        "legacy_code_execution_policy": "forbid_without_user_approval",
        "startup_boundary_requirements": ("paper_framing", "journal_shortlist", "evidence_package"),
    }
    payload.update(overrides)
    return profiles.WorkspaceProfile(**payload)


def write_study(studies_root: Path, study_id: str, payload: dict[str, object]) -> Path:
    study_root = studies_root / study_id
    write_text(study_root / "study.yaml", yaml.safe_dump(payload, allow_unicode=True, sort_keys=False))
    return study_root


def test_analysis_contract_for_study_marks_missing_endpoint_type_as_unsupported(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.studies_root,
        "001-risk",
        {
            "study_id": "001-risk",
            "preferred_study_archetype": "clinical_classifier",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "unsupported"
    assert result["reason_code"] == "missing_endpoint_type"


def test_analysis_contract_for_study_uses_primary_submission_target_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(
        tmp_path,
        default_submission_targets=(
            {
                "publication_profile": "frontiers_family_harvard",
                "primary": True,
                "package_required": True,
                "story_surface": "general_medical_journal",
            },
        ),
    )
    study_root = write_study(
        profile.studies_root,
        "001-risk",
        {
            "study_id": "001-risk",
            "preferred_study_archetype": "clinical_classifier",
            "endpoint_type": "binary",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["publication_profile"] == "frontiers_family_harvard"
    assert result["submission_target_family"] == "general_medical_journal"


def test_analysis_contract_for_study_rejects_unresolved_primary_publication_profile(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(
        tmp_path,
        default_submission_targets=(
            {
                "publication_profile": "unsupported_profile",
                "primary": True,
                "package_required": True,
                "story_surface": "general_medical_journal",
            },
        ),
    )
    study_root = write_study(
        profile.studies_root,
        "001-risk",
        {
            "study_id": "001-risk",
            "preferred_study_archetype": "clinical_classifier",
            "endpoint_type": "binary",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "unsupported"
    assert result["reason_code"] == "primary_submission_target_not_resolved_to_publication_profile"
    assert result["primary_target_resolution_status"] == "needs_journal_resolution"
