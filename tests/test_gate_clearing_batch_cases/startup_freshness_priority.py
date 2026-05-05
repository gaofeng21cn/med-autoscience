from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_startup_freshness_work_unit_dominates_repairable_surface_without_eval_analysis_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution")
    publication_eval_payload = _write_bundle_stage_publication_eval(study_root, quest_id="quest-002")
    gate_report = {
        "status": "blocked",
        "current_required_action": "return_to_publishability_gate",
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "reviewer_first_concerns_unresolved",
            "claim_evidence_consistency_failed",
            "submission_hardening_incomplete",
            "submission_surface_qc_failure_present",
        ],
        "study_delivery_status": "stale_source_missing",
        "study_delivery_stale_reason": "delivery_manifest_sources_missing",
        "submission_minimal_authority_status": "stale_source_missing",
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": [
            "reviewer_first_concerns_unresolved",
            "claim_evidence_consistency_failed",
            "submission_hardening_incomplete",
        ],
    }

    action = module.build_gate_clearing_batch_recommended_action(
        profile=profile,
        study_root=study_root,
        quest_id="quest-002",
        publication_eval_payload=publication_eval_payload,
        gate_report=gate_report,
        prefer_startup_freshness_work_unit=True,
    )

    assert action is not None
    assert action["controller_action_type"] == "run_gate_clearing_batch"
    assert action["route_target"] == "finalize"
    assert action["next_work_unit"]["unit_id"] == "submission_minimal_refresh"
    assert [unit["unit_id"] for unit in action["blocking_work_units"]] == ["submission_minimal_refresh"]
