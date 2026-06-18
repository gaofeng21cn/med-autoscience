from __future__ import annotations

from pathlib import Path

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WORK_UNIT = "medical_prose_write_repair"
FINGERPRINT = "publication-blockers::0915410f804b3697"
CLOSEOUT_REF = (
    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
    "consumer/default_executor_execution/sat_08da46bea43329723d2fbbea.closeout.json"
)
RECEIPT_REF = (
    "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/"
    "003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/"
    "repair_execution_receipts/latest.json"
)


def test_paper_recovery_refresh_reconciles_consumed_closeout_with_current_execution_surfaces(
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

    result = refresh_module.normalize_paper_recovery_execution_projection(
        payload=_payload_with_stale_successor(),
        status={"study_id": STUDY_ID, "quest_id": STUDY_ID},
        handoff=_handoff_with_consumed_terminal_closeout(),
        runtime_health_snapshot={"runtime_health_epoch": "runtime-health-event-006980"},
        study_root=tmp_path / "studies" / STUDY_ID,
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

    assert result["paper_recovery_state"]["phase"] == "domain_blocked"
    assert result["paper_recovery_state"]["conditions"] == [
        {
            "condition": "accepted_closeout_typed_blocker",
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        }
    ]
    assert result["paper_recovery_state"]["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["owner"] == "one-person-lab"
    assert result["current_work_unit"]["action_type"] == "run_quality_repair_batch"
    assert result["current_work_unit"]["work_unit_id"] == WORK_UNIT
    state = result["current_work_unit"]["state"]
    assert state["state_kind"] == "typed_blocker"
    assert state["source"] == "terminal_closeout_typed_blocker"
    assert state["typed_blocker"]["typed_blocker_ref"] == CLOSEOUT_REF
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 0


def _payload_with_stale_successor() -> dict[str, object]:
    owner_receipt_work_unit = _owner_receipt_work_unit()
    return {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "queued",
        "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-event-006980"},
        "current_work_unit": owner_receipt_work_unit,
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "write",
        },
        "current_executable_owner_action": _stale_successor_action(),
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "schema_version": 1,
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "phase": "owner_action_ready",
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WORK_UNIT,
                    "work_unit_fingerprint": FINGERPRINT,
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
                    "work_unit_id": WORK_UNIT,
                    "work_unit_fingerprint": FINGERPRINT,
                    "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
                "identity_match": True,
            },
        },
        "paper_autonomy_supervisor_decision": {
            "decision": "materialize_recovery_action",
            "identity_match": True,
        },
        "gate_clearing_batch_followthrough": {
            "surface_kind": "gate_clearing_batch_followthrough",
            "status": "executed",
            "gate_replay_status": "blocked",
            "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            "work_unit_id": WORK_UNIT,
            "work_unit_fingerprint": FINGERPRINT,
            "work_unit_currentness": {
                "current_actionability_status": "actionable",
                "lacks_specific_blocker_object": False,
                "current_publication_work_unit_id": WORK_UNIT,
                "current_work_unit_fingerprint": FINGERPRINT,
            },
            "current_publication_work_unit": {"unit_id": WORK_UNIT, "lane": "write"},
        },
    }


def _handoff_with_consumed_terminal_closeout() -> dict[str, object]:
    return {
        "surface_kind": "opl_current_control_state_study_handoff",
        "running_provider_attempt": False,
        "next_owner": "one-person-lab",
        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WORK_UNIT,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "current_work_unit": _owner_receipt_work_unit(),
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "write",
            "typed_blocker": None,
        },
        "typed_blocker": _typed_blocker(),
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WORK_UNIT,
            "work_unit_fingerprint": FINGERPRINT,
            "action_fingerprint": FINGERPRINT,
            "typed_blocker_ref": CLOSEOUT_REF,
        },
        "latest_typed_default_executor_closeout": {
            "surface_kind": "mas_latest_default_executor_typed_closeout_projection",
            "read_model": "study_opl_current_control_state_handoff_projection",
            "authority": "observability_only",
            "source_path": CLOSEOUT_REF,
            "receipt_ref": CLOSEOUT_REF,
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "source_fingerprint": "mas_default_executor_provider_admission_source_95eb75e51e25e7fc938b8682",
            "idempotency_key": "idem_2f8ab5c3e2608435ee8ccde0",
            "action_type": "run_quality_repair_batch",
            "status": "typed_blocker",
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "work_unit_id": WORK_UNIT,
            "work_unit_fingerprint": FINGERPRINT,
            "action_fingerprint": FINGERPRINT,
            "typed_blocker": _typed_blocker(),
            "next_owner": "one-person-lab",
            "paper_stage_log": {
                "outcome": "typed_blocker",
                "progress_delta_classification": "typed_blocker",
                "remaining_blockers": [
                    "no_selected_dispatch_for_authorized_stage_packet"
                ],
            },
        },
        "latest_terminal_stage_log": {
            "surface_kind": "mas_latest_terminal_stage_log_projection",
            "status": "blocked",
            "route_outcome": "typed_blocker",
            "typed_blocker_ref": CLOSEOUT_REF,
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WORK_UNIT,
            "work_unit_fingerprint": FINGERPRINT,
            "action_fingerprint": FINGERPRINT,
            "paper_stage_log": {
                "outcome": "typed_blocker",
                "progress_delta_classification": "typed_blocker",
                "remaining_blockers": [
                    "no_selected_dispatch_for_authorized_stage_packet"
                ],
            },
        },
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "action_queue": [],
    }


def _owner_receipt_work_unit() -> dict[str, object]:
    return {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "owner_receipt_recorded",
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "stage_id": "publication_supervision",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WORK_UNIT,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "acceptance_refs": [RECEIPT_REF],
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": RECEIPT_REF,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": RECEIPT_REF,
            "next_safe_action_kind": "consume_owner_receipt",
            "provider_admission_pending": False,
        },
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "work_unit_id": WORK_UNIT,
            "work_unit_fingerprint": FINGERPRINT,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
        },
    }


def _stale_successor_action() -> dict[str, object]:
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": WORK_UNIT,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "owner_receipt_required": True,
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "paper_recovery_successor": {
            "phase": "owner_action_ready",
            "source_next_safe_action_kind": "materialize_successor_owner_action",
        },
    }


def _typed_blocker() -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_typed_blocker",
        "schema_version": 1,
        "reason": "no_selected_dispatch_for_authorized_stage_packet",
        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
        "owner": "one-person-lab",
        "next_owner": "one-person-lab",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WORK_UNIT,
        "work_unit_fingerprint": FINGERPRINT,
        "action_fingerprint": FINGERPRINT,
        "source_ref": CLOSEOUT_REF,
        "typed_blocker_ref": CLOSEOUT_REF,
        "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
        "closeout_refs": [CLOSEOUT_REF],
        "write_permitted": False,
    }
