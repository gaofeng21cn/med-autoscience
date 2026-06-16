from __future__ import annotations

import json
from pathlib import Path

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WRITE_WORK_UNIT = "medical_prose_write_repair"
WRITE_FINGERPRINT = "publication-blockers::0915410f804b3697"
AI_REVIEWER_WORK_UNIT = "ai_reviewer_medical_prose_quality_review"
AI_REVIEWER_FINGERPRINT = (
    "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
)


def _dm003_post_write_repair_payload() -> dict:
    return {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "publication_supervision",
        "paper_stage": "analysis-campaign",
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "owner_receipt_recorded",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "action_fingerprint": WRITE_FINGERPRINT,
            "state": {
                "state_kind": "owner_receipt_recorded",
                "source": "paper_recovery_state.owner_receipt_recorded",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "next_safe_action_kind": "consume_owner_receipt",
            },
        },
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "write",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_receipt_recorded",
            "current_authority": {
                "obligation": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WRITE_WORK_UNIT,
                    "work_unit_fingerprint": WRITE_FINGERPRINT,
                },
            },
            "next_safe_action": {
                "kind": "consume_owner_receipt",
                "owner": "write",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            },
        },
        "repair_progress_projection": {
            "surface_kind": "repair_progress_projection",
            "source": "mas_owner_repair_execution_evidence",
            "paper_delta_observed": True,
            "accepted_owner_receipt": True,
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "action_fingerprint": WRITE_FINGERPRINT,
            "source_fingerprint": "sha256:4cb87568158cbc2e3a45bbf48a3348123947c5f70ce7b5efa261f1af4da4698e",
            "source_eval_id": "publication-eval::003::post-write-repair",
            "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            "gate_replay_done": True,
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
        },
        "gate_clearing_batch_followthrough": {
            "surface_kind": "gate_clearing_batch_followthrough",
            "status": "executed",
            "gate_replay_status": "blocked",
            "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            "source_eval_id": "publication-eval::003::pre-repair",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "work_unit_currentness": {
                "explicit_publication_work_unit_id": WRITE_WORK_UNIT,
                "selected_publication_work_unit_id": WRITE_WORK_UNIT,
                "current_publication_work_unit_id": WRITE_WORK_UNIT,
                "explicit_work_unit_fingerprint": WRITE_FINGERPRINT,
                "current_work_unit_fingerprint": WRITE_FINGERPRINT,
                "explicit_work_unit_fingerprint_matches_current": True,
                "current_actionability_status": "actionable",
                "lacks_specific_blocker_object": False,
            },
            "current_publication_work_unit": {
                "unit_id": WRITE_WORK_UNIT,
                "lane": "write",
            },
        },
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "ai_reviewer",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": AI_REVIEWER_WORK_UNIT,
                "lane": "review",
            },
            "guard_boundary": {
                "required_owner_surface": "artifacts/publication_eval/latest.json",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "eval_id": "publication-eval::003::post-write-repair",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
            },
        },
        "next_forced_delta": {
            "required_delta_kind": "review_current_paper_delta",
            "reason": "paper_progress_delta_observed",
            "work_unit_id": AI_REVIEWER_WORK_UNIT,
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "ai_reviewer",
                "surface_ref": "artifacts/publication_eval/latest.json",
            },
            "owner_action": {
                "next_owner": "ai_reviewer",
                "work_unit_id": AI_REVIEWER_WORK_UNIT,
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "owner_receipt_required": True,
            },
        },
    }


def test_current_owner_action_prefers_ai_reviewer_transition_over_consumed_write_receipt() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(_dm003_post_write_repair_payload())

    assert action is not None
    assert action["source"] == "domain_transition"
    assert action["next_owner"] == "ai_reviewer"
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["work_unit_id"] == AI_REVIEWER_WORK_UNIT
    assert action["work_unit_fingerprint"] == AI_REVIEWER_FINGERPRINT


def test_current_owner_action_accepts_ai_reviewer_transition_consumed_route_work_unit() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    payload = _dm003_post_write_repair_payload()
    payload["repair_progress_projection"]["source_fingerprint"] = (
        "sha256:b3aec4ff1e4a13eb0c0a2f228a6b70aa0c07a86d3485c2887359b764013af8bd"
    )
    payload["domain_transition"]["completion_receipt_consumption"] = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "eval_id": "publication-eval::003::post-write-repair",
        "work_unit_id": AI_REVIEWER_WORK_UNIT,
        "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
    }

    action = module.build_current_executable_owner_action(payload)

    assert action is not None
    assert action["source"] == "domain_transition"
    assert action["next_owner"] == "ai_reviewer"
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["work_unit_id"] == AI_REVIEWER_WORK_UNIT
    assert action["work_unit_fingerprint"] == AI_REVIEWER_FINGERPRINT


def test_paper_recovery_refresh_reaches_ai_reviewer_after_gate_and_write_receipts(
    tmp_path: Path,
) -> None:
    refresh_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "paper_recovery_execution_refresh"
    )
    action_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    provider_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    payload_sync = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.payload_sync"
    )
    recovery_state = importlib.import_module("med_autoscience.controllers.paper_recovery_state")

    study_root = tmp_path / "studies" / STUDY_ID
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
    dispatch_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_request",
                "study_id": STUDY_ID,
                "quest_id": STUDY_ID,
                "action_type": "return_to_ai_reviewer_workflow",
                "dispatch_status": "ready",
                "dispatch_authority": "ai_reviewer_record_production_handoff",
                "next_executable_owner": "ai_reviewer",
                "required_output_surface": "artifacts/publication_eval/latest.json",
                "refs": {"dispatch_path": str(dispatch_path)},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = _dm003_post_write_repair_payload()
    payload["current_stage"] = "queued"
    payload["truth_epoch"] = "truth-event-000035"
    payload["runtime_health_snapshot"] = {"runtime_health_epoch": "runtime-health-event-006956"}
    payload["current_work_unit"] = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "owner_receipt_recorded",
        "owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": WRITE_FINGERPRINT,
        "action_fingerprint": WRITE_FINGERPRINT,
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "paper_recovery_state.owner_receipt_recorded",
            "owner_receipt_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "next_safe_action_kind": "consume_owner_receipt",
        },
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": "artifacts/controller/gate_clearing_batch/latest.json",
        },
        "currentness_basis": {
            "source_eval_id": "publication-eval::003::post-write-repair",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "truth_epoch": "truth-event-000035",
            "runtime_health_epoch": "runtime-health-event-006956",
        },
    }
    payload["current_execution_envelope"] = {
        "state_kind": "owner_receipt_recorded",
        "owner": "gate_clearing_batch",
    }
    payload["current_executable_owner_action"] = None
    payload["paper_recovery_state"] = {
        "surface_kind": "paper_recovery_state",
        "schema_version": 1,
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "phase": "owner_action_ready",
        "current_authority": {
            "owner": "write",
            "authority": "med-autoscience",
            "obligation": {
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": WRITE_FINGERPRINT,
            },
        },
        "conditions": [
            {
                "condition": "consumed_owner_receipt_routeback_successor",
                "source_condition": "current_work_unit_owner_receipt_recorded",
            }
        ],
        "next_safe_action": {
            "kind": "materialize_successor_owner_action",
            "owner": "write",
            "provider_admission_allowed": True,
            "successor_owner_action": {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
        "supervisor_decision": {
            "decision": "materialize_recovery_action",
            "identity_match": True,
        },
    }
    payload["paper_autonomy_supervisor_decision"] = {
        "decision": "stop_with_owner_receipt",
        "identity_match": True,
    }
    payload["provider_admission_blocked_by_supervisor_decision"] = {
        "decision": "stop_with_owner_receipt",
        "reason": "paper_autonomy_supervisor_decision_blocks_provider_admission",
    }
    payload["repair_progress_projection"]["source_fingerprint"] = (
        "sha256:b3aec4ff1e4a13eb0c0a2f228a6b70aa0c07a86d3485c2887359b764013af8bd"
    )
    payload["domain_transition"]["completion_receipt_consumption"] = {
        "status": "consumed",
        "receipt_kind": "ai_reviewer_publication_eval",
        "eval_id": "publication-eval::003::post-write-repair",
        "work_unit_id": AI_REVIEWER_WORK_UNIT,
        "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
    }

    result = refresh_module.refresh_after_paper_recovery_state(
        payload=payload,
        status={},
        handoff={},
        runtime_health_snapshot=payload["runtime_health_snapshot"],
        study_root=study_root,
        build_current_executable_owner_action=(
            action_module.build_current_executable_owner_action
        ),
        refresh_current_execution_surfaces=surfaces.refresh_current_execution_surfaces,
        provider_admission_projection_fields=(
            provider_projection.provider_admission_projection_fields
        ),
        sync_progress_first_owner_action_admission=(
            payload_sync.sync_progress_first_owner_action_admission
        ),
        build_paper_recovery_state=recovery_state.build_paper_recovery_state,
    )

    assert result["current_executable_owner_action"]["source"] == "domain_transition"
    assert result["current_executable_owner_action"]["next_owner"] == "ai_reviewer"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "ai_reviewer"
    assert result["current_work_unit"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["current_work_unit"]["work_unit_id"] == AI_REVIEWER_WORK_UNIT
    assert result["provider_admission_pending_count"] == 1
    assert "provider_admission_blocked_by_supervisor_decision" not in result


def test_progress_first_projects_running_ai_reviewer_handoff_over_consumed_write_receipt() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    payload = _dm003_post_write_repair_payload()
    payload["current_executable_owner_action"] = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "domain_transition",
        "next_owner": "ai_reviewer",
        "work_unit_id": AI_REVIEWER_WORK_UNIT,
        "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
        "action_fingerprint": AI_REVIEWER_FINGERPRINT,
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "owner_receipt_required": True,
        "owner_route_currentness_basis": {
            "source": "domain_transition",
            "work_unit_id": AI_REVIEWER_WORK_UNIT,
            "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
            "truth_epoch": "truth-current",
            "runtime_health_epoch": "runtime-current",
        },
    }
    payload["opl_current_control_state_handoff"] = {
        "running_provider_attempt": True,
        "active_run_id": "opl-stage-attempt://sat_current_ai_reviewer",
        "active_stage_attempt_id": "sat_current_ai_reviewer",
        "active_workflow_id": "wf_current_ai_reviewer",
        "next_owner": "ai_reviewer",
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": AI_REVIEWER_WORK_UNIT,
        "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
        "action_fingerprint": AI_REVIEWER_FINGERPRINT,
        "owner_route_currentness_basis": {
            "work_unit_id": AI_REVIEWER_WORK_UNIT,
            "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
            "truth_epoch": "truth-current",
            "runtime_health_epoch": "runtime-current",
        },
        "runtime_health": {
            "runtime_liveness_status": "attempt_running",
            "health_status": "live",
        },
        "action_queue": [],
    }

    monitoring = module.build_progress_first_monitoring_summary(payload)

    assert monitoring["running_provider_attempt"] is True
    assert monitoring["execution_state_kind"] == "running_provider_attempt"
    assert monitoring["active_stage_attempt_id"] == "sat_current_ai_reviewer"
    assert monitoring["current_executable_owner_action"]["source"] == "domain_transition"
    admission = monitoring["owner_action_admission"]
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_proof"]["active_stage_attempt_id"] == (
        "sat_current_ai_reviewer"
    )
