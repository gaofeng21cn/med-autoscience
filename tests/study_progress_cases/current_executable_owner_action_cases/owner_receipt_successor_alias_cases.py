from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WRITE_WORK_UNIT = "medical_prose_write_repair"
WRITE_FINGERPRINT = "publication-blockers::0915410f804b3697"
RECEIPT_REF = "artifacts/controller/repair_execution_receipts/latest.json"


def test_consumed_owner_receipt_successor_does_not_require_legacy_identity_alias() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    payload = _payload(
        supervisor_decision={
            "decision": "opl_supervisor_decision_readback_required",
            "decision_authority": False,
            "requires_opl_supervisor_decision_engine_readback": True,
        }
    )

    result = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={"study_id": STUDY_ID},
        handoff=_handoff(),
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7"
        },
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == WRITE_WORK_UNIT
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"


def test_consumed_owner_receipt_successor_rejects_explicit_identity_mismatch() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    payload = _payload(
        supervisor_decision={
            "decision": "opl_supervisor_decision_readback_required",
            "identity_match": False,
        }
    )

    result = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={"study_id": STUDY_ID},
        handoff=_handoff(),
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7"
        },
    )

    assert result["current_executable_owner_action"] is None


def _payload(*, supervisor_decision: dict[str, object]) -> dict[str, object]:
    handoff_work_unit = _handoff_work_unit()
    return {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "queued",
        "current_executable_owner_action": None,
        "current_work_unit": handoff_work_unit,
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "schema_version": 1,
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "phase": "owner_action_ready",
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
            "supervisor_decision": supervisor_decision,
        },
    }


def _handoff() -> dict[str, object]:
    return {
        "surface_kind": "opl_current_control_state_study_handoff",
        "running_provider_attempt": False,
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "action_fingerprint": WRITE_FINGERPRINT,
            "owner_receipt_ref": RECEIPT_REF,
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_08da46bea43329723d2fbbea.closeout.json"
            ),
        },
        "typed_blocker": {
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "action_fingerprint": WRITE_FINGERPRINT,
        },
        "current_work_unit": _handoff_work_unit(),
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "write",
        },
    }


def _handoff_work_unit() -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "owner_receipt_recorded",
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "stage_id": "publication_supervision",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WRITE_WORK_UNIT,
        "work_unit_fingerprint": WRITE_FINGERPRINT,
        "action_fingerprint": WRITE_FINGERPRINT,
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": RECEIPT_REF,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "acceptance_refs": [RECEIPT_REF],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": RECEIPT_REF,
            "next_safe_action_kind": "consume_owner_receipt",
            "provider_admission_pending": False,
        },
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
        },
    }
