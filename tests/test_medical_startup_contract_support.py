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
        "runtime_root": workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        "studies_root": workspace_root / "studies",
        "portfolio_root": workspace_root / "portfolio",
        "med_deepscientist_runtime_root": workspace_root / "ops" / "med-deepscientist" / "runtime",
        "med_deepscientist_repo_root": tmp_path / "med-deepscientist",
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


def test_resolve_study_archetype_prioritizes_study_payload_study_archetype(tmp_path: Path) -> None:
    support = importlib.import_module("med_autoscience.controllers._medical_contract_support")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))

    study_archetype, issue = support.resolve_study_archetype(
        study_payload={
            "study_archetype": "clinical_classifier",
            "preferred_study_archetype": "clinical_subtype_reconstruction",
        },
        profile=profile,
    )

    assert issue is None
    assert study_archetype == "clinical_classifier"


def test_analysis_contract_for_study_uses_study_level_metadata_priority_and_survival_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-survival-risk",
        {
            "study_id": "001-survival-risk",
            "study_archetype": "clinical_classifier",
            "preferred_study_archetype": "gray_zone_triage",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "clinical_classifier"
    assert result["endpoint_type"] == "time_to_event"
    assert result["manuscript_family"] == "prediction_model"
    assert result["recommended_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]
    assert result["declared_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]


def test_analysis_contract_rejects_ambiguous_profile_fallback_without_explicit_study_archetype(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_analysis_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-ambiguous-risk",
        {
            "study_id": "001-ambiguous-risk",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "unsupported"
    assert result["reason_code"] == "ambiguous_study_archetype"


def test_reporting_contract_summary_contains_recommended_explicit_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_contract")
    profile = make_profile(tmp_path, preferred_study_archetypes=("clinical_classifier", "gray_zone_triage"))
    study_root = write_study(
        profile.studies_root,
        "001-survival-reporting",
        {
            "study_id": "001-survival-reporting",
            "study_archetype": "clinical_classifier",
            "endpoint_type": "time_to_event",
            "manuscript_family": "prediction_model",
        },
    )

    result = module.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")),
        profile=profile,
    )

    assert result["status"] == "resolved"
    assert result["study_archetype"] == "clinical_classifier"
    assert result["endpoint_type"] == "time_to_event"
    assert result["manuscript_family"] == "prediction_model"
    assert result["recommended_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]
    assert result["declared_study_fields"] == [
        "study_archetype",
        "endpoint_type",
        "manuscript_family",
    ]
    assert result["display_registry_required"] is True
    assert result["required_illustration_shells"] == ["cohort_flow_figure"]
    assert result["required_table_shells"] == [
        "table1_baseline_characteristics",
        "table2_primary_performance_by_horizon",
    ]
    assert result["display_shell_plan"] == [
        {
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
        },
        {
            "display_id": "Figure2",
            "display_kind": "figure",
            "requirement_key": "discrimination_calibration_figure",
        },
        {
            "display_id": "Figure3",
            "display_kind": "figure",
            "requirement_key": "km_risk_stratification_figure",
        },
        {
            "display_id": "Figure4",
            "display_kind": "figure",
            "requirement_key": "decision_curve_figure",
        },
        {
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
        },
        {
            "display_id": "Table2",
            "display_kind": "table",
            "requirement_key": "table2_primary_performance_by_horizon",
        },
    ]
