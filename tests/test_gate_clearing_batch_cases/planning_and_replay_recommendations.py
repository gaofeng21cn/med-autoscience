from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_build_gate_clearing_batch_recommended_action_promotes_blocked_bounded_analysis(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    mapping_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "analysis-analysis-c7574291-freeze-scientific-anchor-and-gate-map"
        / "experiments"
        / "analysis"
        / "analysis-c7574291"
        / "freeze-scientific-anchor-and-gate-map"
        / "outputs"
        / "scientific_anchor_mapping.json"
    )
    _write_json(
        mapping_path,
        {
            "proposed_scientific_followup_questions": ["Q1"],
            "proposed_explanation_targets": ["T1"],
            "clinician_facing_interpretation_target": "Clinician-facing interpretation target.",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "missing_medical_story_contract",
            "table_catalog_missing_or_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert action["gate_clearing_batch_mapping_path"] == str(mapping_path)
    assert "scientific-anchor fields can be frozen" in action["gate_clearing_batch_reason"]

def test_build_gate_clearing_batch_recommended_action_uses_managed_runtime_quest_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = make_profile(tmp_path)
    profile = profiles.WorkspaceProfile(
        **{
            **profile.__dict__,
            "runtime_root": profile.workspace_root / "runtime" / "quests",
            "med_deepscientist_runtime_root": profile.workspace_root / "legacy" / "mds-runtime",
        }
    )
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    mapping_path = (
        profile.managed_runtime_quests_root
        / "quest-001"
        / ".ds"
        / "worktrees"
        / "analysis-analysis-c7574291-freeze-scientific-anchor-and-gate-map"
        / "experiments"
        / "analysis"
        / "analysis-c7574291"
        / "freeze-scientific-anchor-and-gate-map"
        / "outputs"
        / "scientific_anchor_mapping.json"
    )
    _write_json(
        mapping_path,
        {
            "proposed_scientific_followup_questions": ["Q1"],
            "proposed_explanation_targets": ["T1"],
            "clinician_facing_interpretation_target": "Clinician-facing interpretation target.",
        },
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-001")
    gate_report = {
        "status": "blocked",
        "blockers": [
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "claim_evidence_map_missing_or_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-001",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["gate_clearing_batch_mapping_path"] == str(mapping_path)

def test_build_gate_clearing_batch_recommended_action_uses_surface_blocker_details(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc-primary-care-phenotype-treatment-gap",
        study_archetype="cross_sectional",
        endpoint_type="treatment_gap",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(
        study_root,
        quest_id="003-dpcc-primary-care-phenotype-treatment-gap",
    )
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_blockers": [
            "missing_medical_story_contract",
            "figure_semantics_manifest_missing_or_incomplete",
            "undefined_methodology_labels_present",
            "treatment_gap_reporting_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="003-dpcc-primary-care-phenotype-treatment-gap",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert "paper-facing display/reporting blockers" in action["gate_clearing_batch_reason"]

def test_build_gate_clearing_batch_recommended_action_promotes_bundle_stage_return_to_finalize(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    publication_eval_payload["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::return_to_controller::2026-04-21T12:42:39+00:00",
            "action_type": "return_to_controller",
            "priority": "now",
            "reason": "Let MAS re-evaluate the finalize-stage blockers before the same paper line resumes.",
            "evidence_refs": [str(study_root / "paper")],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)
    gate_report = {
        "status": "blocked",
        "blockers": [
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "controller_stage_note": "Only finalize or submission-bundle repairs remain on the current paper line.",
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_named_blockers": [],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-004",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "finalize"
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert "finalize/submission bundle blockers are deterministic same-line repair candidates" in action[
        "gate_clearing_batch_reason"
    ]

def test_build_gate_clearing_batch_recommended_action_widens_bounded_analysis_to_submission_refresh(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-invasive-architecture",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="observational_study",
    )
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-004")
    assert publication_eval_payload["recommended_actions"][0]["action_type"] == "bounded_analysis"
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "submission_surface_qc_failure_present",
        ],
        "current_required_action": "complete_bundle_stage",
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-004",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
    )

    assert action is not None
    assert action["action_type"] == "route_back_same_line"
    assert action["route_target"] == "finalize"
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert action["next_work_unit"] == {
        "unit_id": "submission_minimal_refresh",
        "lane": "finalize",
        "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
    }
