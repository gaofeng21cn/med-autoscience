from __future__ import annotations

import importlib


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WRITE_WORK_UNIT = "medical_prose_write_repair"


def test_current_execution_refresh_prefers_selected_gate_successor_over_stale_handoff_action() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )

    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-20T05:46:03+00:00"
    )
    selected_work_unit = "analysis_claim_evidence_repair"
    selected_fingerprint = "publication-blockers::5d99b7c4019bd601"
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    closeout_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/owner_callable_adapter_receipt/sat_08da46bea43329723d2fbbea.closeout.json"
    )
    embedded_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "analysis-campaign",
        "work_unit_id": selected_work_unit,
        "work_unit_fingerprint": selected_fingerprint,
        "action_fingerprint": selected_fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": selected_work_unit,
            "selected_publication_work_unit_id": selected_work_unit,
            "explicit_publication_work_unit_id": selected_work_unit,
            "work_unit_fingerprint": selected_fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-4660f353450fc50d",
        },
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "analysis-campaign",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
        "acceptance_refs": [
            f"/workspace/studies/{STUDY_ID}/artifacts/controller/gate_clearing_batch/latest.json"
        ],
    }
    stale_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "next_owner": "write",
        "work_unit_id": WRITE_WORK_UNIT,
        "work_unit_fingerprint": stale_fingerprint,
        "action_fingerprint": stale_fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
    }
    typed_blocker = {
        "surface_kind": "mas_domain_typed_blocker",
        "schema_version": 1,
        "reason": "no_selected_dispatch_for_authorized_stage_packet",
        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        "source_ref": closeout_ref,
        "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
        "next_owner": "one-person-lab",
        "write_permitted": False,
        "owner": "one-person-lab",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WRITE_WORK_UNIT,
        "work_unit_fingerprint": stale_fingerprint,
        "action_fingerprint": stale_fingerprint,
        "typed_blocker_ref": closeout_ref,
        "currentness_basis": {
            "source": "study_intervention_event.owner_gate_decision",
            "source_eval_id": source_eval_id,
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": stale_fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-4660f353450fc50d",
        },
    }
    payload = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-event-006980-4660f353450fc50d",
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "state": {
                "state_kind": "typed_blocker",
                "source": "typed_blocker",
                "typed_blocker": typed_blocker,
            },
            "currentness_basis": dict(typed_blocker["currentness_basis"]),
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": typed_blocker,
        },
        "current_executable_owner_action": embedded_action,
        "gate_clearing_batch_followthrough": {
            "surface_kind": "gate_clearing_batch_followthrough",
            "status": "executed",
            "source_eval_id": source_eval_id,
            "work_unit_id": selected_work_unit,
            "work_unit_fingerprint": selected_fingerprint,
            "work_unit_currentness": {
                "explicit_publication_work_unit_id": selected_work_unit,
                "selected_publication_work_unit_id": selected_work_unit,
                "current_publication_work_unit_id": WRITE_WORK_UNIT,
                "selected_work_unit_fingerprint": selected_fingerprint,
                "explicit_work_unit_fingerprint": selected_fingerprint,
                "current_work_unit_fingerprint": stale_fingerprint,
                "explicit_work_unit_fingerprint_matches_current": False,
                "current_actionability_status": "actionable",
                "lacks_specific_blocker_object": False,
            },
            "current_publication_work_unit": {
                "unit_id": WRITE_WORK_UNIT,
                "lane": "write",
            },
            "selected_publication_work_unit": {
                "unit_id": selected_work_unit,
                "lane": "analysis-campaign",
            },
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [
                "stale_submission_minimal_authority",
                "medical_publication_surface_blocked",
                "reviewer_first_concerns_unresolved",
                "submission_hardening_incomplete",
            ],
            "latest_record_path": (
                f"/workspace/studies/{STUDY_ID}/artifacts/controller/gate_clearing_batch/latest.json"
            ),
        },
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "running_provider_attempt": False,
        "current_executable_owner_action": stale_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            },
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": stale_fingerprint,
        },
        "typed_blocker": typed_blocker,
        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
        "next_owner": "one-person-lab",
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "action_queue": [],
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={"study_id": STUDY_ID, "quest_id": STUDY_ID},
        handoff=handoff,
        runtime_health_snapshot=payload["runtime_health_snapshot"],
    )

    assert result["current_executable_owner_action"] is not None
    assert result["current_executable_owner_action"]["source"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )
    assert result["current_executable_owner_action"]["next_owner"] == "analysis-campaign"
    assert result["current_executable_owner_action"]["work_unit_id"] == selected_work_unit
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "analysis-campaign"
    assert result["current_work_unit"]["work_unit_id"] == selected_work_unit
