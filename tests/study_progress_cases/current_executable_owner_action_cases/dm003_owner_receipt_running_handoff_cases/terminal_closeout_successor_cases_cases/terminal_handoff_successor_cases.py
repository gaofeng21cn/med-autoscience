from __future__ import annotations

from pathlib import Path

from tests.study_progress_cases import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WRITE_WORK_UNIT = "medical_prose_write_repair"
WRITE_FINGERPRINT = "publication-blockers::0915410f804b3697"


def test_paper_recovery_refresh_consumes_handoff_terminal_blocker_over_owner_receipt(
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
    closeout_ref = (
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat_08da46bea43329723d2fbbea.closeout.json"
    )
    typed_blocker = {
        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
        "owner": "one-person-lab",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WRITE_WORK_UNIT,
        "work_unit_fingerprint": WRITE_FINGERPRINT,
        "action_fingerprint": WRITE_FINGERPRINT,
        "typed_blocker_ref": closeout_ref,
        "source_ref": closeout_ref,
        "latest_owner_answer_kind": "typed_blocker",
        "latest_owner_answer_ref": closeout_ref,
        "terminal_closeout_outcome": "typed_blocker",
    }
    payload = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "publication_supervision",
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "owner_receipt_recorded",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "action_fingerprint": WRITE_FINGERPRINT,
            "acceptance_refs": ["artifacts/controller/repair_execution_receipts/latest.json"],
            "state": {
                "state_kind": "owner_receipt_recorded",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "next_safe_action_kind": "consume_owner_receipt",
                "provider_admission_pending": False,
            },
        },
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "write",
        },
        "current_executable_owner_action": None,
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
                    "work_unit_id": WRITE_WORK_UNIT,
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
        },
        "gate_clearing_batch_followthrough": {
            "surface_kind": "gate_clearing_batch_followthrough",
            "gate_replay_status": "blocked",
            "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "work_unit_currentness": {
                "current_actionability_status": "actionable",
                "lacks_specific_blocker_object": False,
                "current_publication_work_unit_id": WRITE_WORK_UNIT,
                "current_work_unit_fingerprint": WRITE_FINGERPRINT,
            },
            "current_publication_work_unit": {"unit_id": WRITE_WORK_UNIT, "lane": "write"},
        },
    }

    result = refresh_module.normalize_paper_recovery_execution_projection(
        payload=payload,
        status={},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "next_owner": "one-person-lab",
            "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
            "typed_blocker": typed_blocker,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "owner_receipt_recorded",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "acceptance_refs": ["artifacts/controller/repair_execution_receipts/latest.json"],
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                    "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                    "next_safe_action_kind": "consume_owner_receipt",
                    "provider_admission_pending": False,
                },
            },
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
                "typed_blocker": None,
            },
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
                "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "typed_blocker_ref": closeout_ref,
            },
            "latest_typed_owner_callable_closeout": {
                "surface_kind": "mas_latest_owner_callable_adapter_typed_closeout_projection",
                "read_model": "study_opl_current_control_state_handoff_projection",
                "authority": "observability_only",
                "source_path": closeout_ref,
                "receipt_ref": closeout_ref,
                "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                "source_fingerprint": "mas_owner_callable_adapter_provider_admission_source_95eb75e51e25e7fc938b8682",
                "idempotency_key": "idem_2f8ab5c3e2608435ee8ccde0",
                "action_type": "run_quality_repair_batch",
                "status": "typed_blocker",
                "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "typed_blocker": {
                    "surface_kind": "mas_domain_typed_blocker",
                    "schema_version": 1,
                    "reason": "no_selected_dispatch_for_authorized_stage_packet",
                    "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                    "source_ref": closeout_ref,
                    "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                    "next_owner": "one-person-lab",
                    "write_permitted": False,
                },
                "next_owner": "one-person-lab",
            },
            "latest_terminal_stage_log": {
                "surface_kind": "mas_latest_terminal_stage_log_projection",
                "status": "blocked",
                "route_outcome": "typed_blocker",
                "typed_blocker_ref": closeout_ref,
                "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
            },
        },
        runtime_health_snapshot={},
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

    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["owner"] == "one-person-lab"
    assert result["current_work_unit"]["state"]["source"] == "terminal_closeout_typed_blocker"
    assert result["current_work_unit"]["state"]["typed_blocker"]["typed_blocker_ref"] == closeout_ref
    assert result["paper_recovery_state"]["phase"] == "domain_blocked"
    assert result["paper_recovery_state"]["conditions"] == [
        {
            "condition": "accepted_closeout_typed_blocker",
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        }
    ]
    assert result["paper_recovery_state"]["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert result["paper_recovery_state"]["next_safe_action"]["provider_admission_allowed"] is False


def test_current_execution_refresh_keeps_handoff_owner_receipt_over_stale_closeout() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    stale_closeout_ref = (
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat_2d9f8f3b252de25a6103779f.closeout.json"
    )
    handoff_work_unit = {
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
        "input_refs": ["artifacts/controller/repair_execution_evidence/latest.json"],
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": receipt_ref,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "acceptance_refs": [receipt_ref],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": receipt_ref,
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
        "projection_metadata": {
            "authority": False,
            "projection_owner": "med-autoscience",
            "fixed_point_runtime_owner": "one-person-lab",
        },
        "authority_boundary": {
            "top_level_truth": "status",
            "mas_owner_authority_preserved": True,
            "stage_transition_authority": "OPL Stage Transition Authority",
            "stage_authority_role": "non_authoritative_observation_and_intent_producer",
            "can_write_stage_current_pointer": False,
            "can_write_current_owner_delta": False,
            "can_write_stage_terminal_state": False,
        },
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload={
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "current_stage": "publication_supervision",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "status": "progress_delta_observed",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "source_eval_id": "publication-eval::003::post-write-repair",
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": receipt_ref,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "changed_artifact_refs": [
                    {"path": "paper/draft.md"},
                    {"path": "paper/evidence_ledger.json"},
                ],
            },
            "current_executable_owner_action": None,
            "current_work_unit": handoff_work_unit,
        },
        status={"study_id": STUDY_ID},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "blocked_reason": "blocked:stage_outcome_authority_execution_count_zero",
            "next_owner": "write",
            "current_work_unit": handoff_work_unit,
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
                "typed_blocker": None,
            },
            "typed_blocker": {
                "blocker_type": "blocked:stage_outcome_authority_execution_count_zero",
                "blocked_reason": "blocked:stage_outcome_authority_execution_count_zero",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "typed_blocker_ref": stale_closeout_ref,
            },
            "latest_typed_owner_callable_closeout": {
                "status": "typed_blocker",
                "blocked_reason": "blocked:stage_outcome_authority_execution_count_zero",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "receipt_ref": stale_closeout_ref,
                "stage_attempt_id": "sat_2d9f8f3b252de25a6103779f",
            },
        },
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7"
        },
    )

    assert result["current_work_unit"]["status"] == "owner_receipt_recorded"
    assert result["current_work_unit"]["state"]["owner_receipt_ref"] == receipt_ref
    assert result["current_execution_envelope"]["state_kind"] == "owner_receipt_recorded"
    assert result["current_execution_envelope"].get("typed_blocker") is None


def test_current_execution_refresh_materializes_successor_over_owner_receipt_handoff() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    handoff_work_unit = {
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
        "input_refs": ["artifacts/controller/repair_execution_evidence/latest.json"],
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": receipt_ref,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "acceptance_refs": [receipt_ref],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "paper_recovery_state.owner_receipt_recorded",
            "owner_receipt_ref": receipt_ref,
            "next_safe_action_kind": "materialize_successor_owner_action",
            "provider_admission_pending": False,
        },
        "currentness_basis": {
            "source": "paper_recovery_state.owner_receipt_recorded",
            "source_eval_id": "publication-eval::003::post-write-repair",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
        },
    }
    payload = {
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
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WRITE_WORK_UNIT,
                    "work_unit_fingerprint": WRITE_FINGERPRINT,
                },
            },
            "conditions": [
                {
                    "condition": "same_work_unit_owner_receipt_recorded",
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
                    "source_surface": "paper_recovery_state.owner_action_ready",
                    "source_ref": receipt_ref,
                },
            },
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
                "identity_match": True,
            },
        },
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={"study_id": STUDY_ID},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "next_owner": "write",
            "current_work_unit": handoff_work_unit,
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
            },
        },
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7"
        },
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == WRITE_WORK_UNIT
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
def test_current_execution_refresh_materializes_consumed_routeback_successor_over_terminal_closeout() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    handoff_work_unit = {
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
        "input_refs": ["artifacts/controller/repair_execution_evidence/latest.json"],
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": receipt_ref,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "acceptance_refs": [receipt_ref],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": receipt_ref,
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
    payload = {
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
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
                "identity_match": True,
            },
        },
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={"study_id": STUDY_ID},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "stage_attempt_id": "sat_f22f2e9d25d336fa2a2a4306",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "owner_receipt_ref": receipt_ref,
            },
            "current_work_unit": handoff_work_unit,
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
            },
        },
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
