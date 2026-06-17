from __future__ import annotations

import importlib
import json

from tests.study_runtime_test_helpers import make_profile, write_study

from .shared import _write_json


def _opl_transition_result(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    stage_run_id: str = "stage-run-provider-admission",
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": f"opl-domain-progress-event::{study_id}::{fingerprint}",
        "outbox_item_id": f"opl-domain-progress-outbox::{study_id}::{fingerprint}",
        "stage_run_identity": {
            "stage_run_id": stage_run_id,
            "stage_run_identity_ref": f"stage-run-identity::{study_id}::{fingerprint}",
            "observed_generation": fingerprint,
        },
        "identity": {
            "study_id": study_id,
            "quest_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
        },
        "causality": {
            "mas_transition_request_idempotency_key": route_key,
            "source_generation": fingerprint,
            "expected_version": fingerprint,
            "derived_from_request": True,
        },
        "authority_boundary": {
            "runtime_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
            "mas_can_authorize_provider_admission": False,
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
            "provider_completion_is_domain_completion": False,
        },
        "exactly_one_outcome": {
            "selected": "provider_admission_pending",
            "allowed": [
                "provider_admission_pending",
                "running_provider_attempt",
                "owner_receipt_ref",
                "typed_blocker_ref",
                "human_gate_ref",
                "route_back_evidence_ref",
            ],
        },
        "projection_metadata": {
            "authority": False,
            "projection_owner": "one-person-lab",
            "consumer": "med-autoscience",
            "observed_generation": fingerprint,
        },
    }


def _write_ready_quality_repair_dispatch(study_root, *, study_id: str, fingerprint: str) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "provider_attempt_or_lease_required": True,
            "opl_domain_progress_transition_result": _opl_transition_result(),
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "refs": {
                "dispatch_path": str(dispatch_path),
                "stage_packet_path": str(dispatch_path),
            },
            "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
            "owner_route": {
                "next_owner": "write",
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "stage_packet_ref": str(dispatch_path),
                    "stage_packet_refs": [str(dispatch_path)],
                    "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
                    "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
                    "owner_route_currentness_basis": {
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth::current",
                        "runtime_health_epoch": "runtime::current",
                    },
                },
            },
        },
    )


def _quality_repair_handoff(*, study_id: str, fingerprint: str) -> dict:
    return {
        "surface_kind": "opl_current_control_state_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "action_queue": [
            {
                "source_surface": "opl_current_control_state.action_queue",
                "status": "queued",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_executable_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "provider_attempt_or_lease_required": True,
                "opl_domain_progress_transition_result": _opl_transition_result(),
                "provider_completion_is_domain_completion": False,
                "owner_route": {
                    "next_owner": "write",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "source_refs": {
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "owner_route_currentness_basis": {
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth::current",
                            "runtime_health_epoch": "runtime::current",
                        },
                    },
                },
            }
        ],
    }


def _supervisor_decision(decision: str, *, study_id: str, fingerprint: str) -> dict:
    return {
        "surface_kind": "paper_autonomy_supervisor_decision",
        "decision": decision,
        "identity_match": True,
        "paper_autonomy_obligation": {
            "surface_kind": "paper_autonomy_obligation",
            "study_id": study_id,
            "quest_id": study_id,
            "stage_id": "publication_supervision",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
            "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        },
        "evidence_refs": [
            f"provider-admission::{study_id}::{fingerprint}",
            f"stage-run-identity::{study_id}::{fingerprint}",
        ],
        "missing_evidence_refs": [],
        "next_safe_action": {
            "kind": "admit_or_resume_stage_run"
            if decision == "execute_current_owner_delta"
            else "publish_stable_blocker_and_stop_same_identity_redrive",
        },
    }


def _quality_repair_current_work_unit(*, study_id: str, fingerprint: str, status: str) -> dict:
    return {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": status,
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "state": {
            "state_kind": status,
            "typed_blocker": {
                "blocker_type": "medical_publication_surface_blocked",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            }
            if status == "typed_blocker"
            else None,
        },
    }


def _write_transition_runtime_log(
    study_root,
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
    idempotency_key: str,
    source_generation: str = "truth::current",
) -> None:
    log_path = (
        study_root.parents[1]
        / "runtime"
        / "artifacts"
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{study_id}::{work_unit_id}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    stage_run_identity = {
        "stage_run_id": f"stage-run:{study_id}:{work_unit_id}",
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "provider_attempt_ref": f"opl://provider-admission/{study_id}/{idempotency_key}",
        "attempt_lease_ref": f"opl://attempt-leases/{idempotency_key}",
        "source_generation": source_generation,
    }
    transaction_id = "dptx_test_log_readback"
    command_id = "dptc_test_log_readback"
    event_id = "dpte_test_log_readback"
    outbox_item_id = "dpto_test_log_readback"
    entries = [
        {
            "entry_kind": "command",
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": command_id,
                "source_generation": source_generation,
                "expected_version": source_generation,
                "stage_run_identity": stage_run_identity,
            },
        },
        {
            "entry_kind": "event",
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": command_id,
                "event_id": event_id,
                "source_generation": source_generation,
                "expected_version": source_generation,
                "stage_run_identity": stage_run_identity,
                "outcome": {
                    "kind": "provider_admission_enqueued_or_blocked",
                    "stable_outcome": True,
                },
            },
        },
        {
            "entry_kind": "outbox_item",
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "outbox_item_id": outbox_item_id,
                "transition_event_id": event_id,
                "outbox_kind": "start_provider_attempt",
                "stage_run_identity": stage_run_identity,
            },
        },
    ]
    log_path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n",
        encoding="utf-8",
    )


def test_provider_admission_projection_clears_candidates_under_typed_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="typed_blocker",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "medical_publication_surface_blocked",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
    }


def test_provider_admission_projection_emits_candidate_for_current_executable_action(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert len(fields["provider_admission_candidates"]) == 1
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == "medical_prose_write_repair"
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["next_executable_owner"] == "write"
    expected_identity = f"provider-admission::{study_id}::{fingerprint}"
    expected_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == expected_stage_packet_ref
    assert candidate["stage_packet_refs"] == [candidate["stage_packet_ref"]]


def test_provider_admission_projection_blocks_queue_residue_under_supervisor_stop_decision(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision(
                    "stop_with_stable_typed_blocker",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["paper_autonomy_supervisor_decision"]["decision"] == "stop_with_stable_typed_blocker"
    assert fields["provider_admission_blocked_by_supervisor_decision"] == {
        "decision": "stop_with_stable_typed_blocker",
        "reason": "paper_autonomy_supervisor_decision_blocks_provider_admission",
    }


def test_provider_admission_projection_execute_decision_allows_current_candidate(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision(
                    "execute_current_owner_delta",
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            },
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields["provider_admission_candidates"][0]["work_unit_fingerprint"] == fingerprint


def test_provider_admission_projection_materialize_recovery_action_allows_log_readback(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_requires_opl_runtime_result": True,
                "successor_owner_action": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "supervisor_decision": _supervisor_decision(
                "materialize_recovery_action",
                study_id=study_id,
                fingerprint=fingerprint,
            ),
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "provider_admission_pending": False,
            },
            "currentness_basis": {
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "truth_epoch": "truth::current",
                "runtime_health_epoch": "runtime::current",
            },
        },
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "action_queue": [],
    }
    current_control = module._current_control_payload_for_provider_admission(
        payload=payload,
        handoff=handoff,
    )
    candidates = provider_admission.current_control_provider_admission_candidates(
        current_control,
        study_root=study_root,
        status_payload=payload,
        current_control_ref=handoff["source_path"],
    )
    assert len(candidates) == 1
    request = candidates[0]["opl_domain_progress_transition_request"]
    _write_transition_runtime_log(
        study_root,
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        idempotency_key=request["idempotency_key"],
    )

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert fields.get("provider_admission_blocked_by_supervisor_decision") is None
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["opl_transition_readback_source"] == "opl_domain_progress_transition_runtime_log"
    assert candidate["opl_domain_progress_transition_result"]["event_id"] == "dpte_test_log_readback"


def test_provider_admission_projection_materializes_gate_followthrough_owner_action_without_pending_flag(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "owner_route_currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
                "target_surface": {
                    "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                    "route_target": "write",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "next_work_unit": work_unit_id,
                    "owner_answer_missing": False,
                    "owner_answer_still_required": False,
                    "provider_admission_pending": False,
                },
                "currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "action_queue": [],
            "blocked_reason": "no_selected_dispatch_for_requested_action_types",
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 1
    candidate = fields["transition_request_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["currentness_basis"]["source_eval_id"] == source_eval_id
    assert candidate["status"] == "transition_request_pending"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["mas_owner_action_source"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )
    expected_identity = f"provider-admission::{study_id}::{fingerprint}"
    expected_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == expected_stage_packet_ref
    assert candidate["stage_packet_refs"] == [candidate["stage_packet_ref"]]


def test_provider_admission_projection_uses_current_work_unit_pending_identity(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(
        study_root,
        study_id=study_id,
        fingerprint=fingerprint,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "opl_domain_progress_transition_result": _opl_transition_result(),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    )

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "target_surface": {
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "studies": [
                {
                    "study_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "stale_handoff_study_entry",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::old",
                        "action_fingerprint": "publication-blockers::old",
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::old",
                        "action_fingerprint": "publication-blockers::old",
                        "state": {
                            "state_kind": "executable_owner_action",
                            "provider_admission_pending": True,
                        },
                    },
                },
            ],
            "action_queue": [
                {
                    "status": "queued",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "action_fingerprint": "publication-blockers::old",
                }
            ],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == "publication_gate_replay"
    assert candidate["work_unit_fingerprint"] == fingerprint


def test_existing_projection_refresh_promotes_progress_first_owner_action_admission(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "opl_domain_progress_transition_result": _opl_transition_result(),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    )
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "action_queue": [],
            },
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    admission = result["owner_action_admission"]
    assert admission == result["progress_first_monitoring_summary"]["owner_action_admission"]
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_running_proven"] is False
    assert admission["allowed_actions"] == ["run_gate_clearing_batch"]
    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["source"] == (
        "opl_current_control_state.study_current_executable_owner_action"
    )


def test_existing_projection_refresh_clears_stale_provider_admission_on_no_current_action(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"status": "stale"}],
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="typed_blocker",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "medical_publication_surface_blocked",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "opl_current_control_state_handoff": _quality_repair_handoff(
                study_id=study_id,
                fingerprint=fingerprint,
            ),
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []


def test_existing_projection_refresh_prefers_live_attempt_over_stale_handoff(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:446e24afa9bc729b3fc0f43184024d2c95ddbcf71db0d8db0183e4c42467ee30"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "runtime_liveness_audit": {
                "source": "opl_current_control_state_provider_attempt",
                "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
                "active_stage_attempt_id": "sat-live-gate-replay",
                "active_workflow_id": "wf-live-gate-replay",
                "running_provider_attempt": True,
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                    "provider_status": "running",
                },
                "stage_progress_log": {
                    "surface_kind": "temporal_workflow_stage_progress_log",
                    "attempt_refs": ["sat-live-gate-replay"],
                },
            },
            "progress_projection": {
                "study_id": study_id,
                "provider_admission_pending_count": 1,
                "provider_admission_candidates": [{"status": "stale"}],
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_type": "executed",
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "typed_blocker": {"blocker_type": "executed", "owner": "one-person-lab"},
                },
                "opl_current_control_state_handoff": {
                    "surface_kind": "opl_current_control_state_study_handoff",
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "blocked_reason": "provider_admission_current_control_state_required",
                    "next_owner": "one-person-lab",
                    "action_queue": [
                        {
                            "status": "queued",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "gate_clearing_batch",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                        }
                    ],
                },
            },
        },
        materialize_read_model_artifacts=False,
    )

    assert result["active_run_id"] == "opl-stage-attempt://sat-live-gate-replay"
    assert result["active_stage_attempt_id"] == "sat-live-gate-replay"
    assert result["active_workflow_id"] == "wf-live-gate-replay"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["current_work_unit"]["status"] == "running_provider_attempt"
    assert result["current_execution_envelope"]["state_kind"] == "running_provider_attempt"


def test_existing_projection_refresh_rejects_superseded_live_attempt_identity(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    current_fingerprint = "sha256:current-publication-gate-replay"
    stale_fingerprint = "sha256:stale-publication-gate-replay"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "runtime_liveness_audit": {
                "source": "opl_current_control_state_provider_attempt",
                "active_run_id": "opl-stage-attempt://sat-stale-gate-replay",
                "active_stage_attempt_id": "sat-stale-gate-replay",
                "active_workflow_id": "wf-stale-gate-replay",
                "running_provider_attempt": True,
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                    "provider_status": "running",
                },
            },
            "progress_projection": {
                "study_id": study_id,
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "action_fingerprint": current_fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "action_fingerprint": current_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_type": "executed",
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": current_fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "typed_blocker": {
                        "blocker_type": "executed",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                    },
                },
                "opl_current_control_state_handoff": {
                    "surface_kind": "opl_current_control_state_study_handoff",
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "next_owner": "one-person-lab",
                    "blocked_reason": "executed",
                    "action_queue": [],
                },
            },
        },
        materialize_read_model_artifacts=False,
    )

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["running_provider_attempt"] is True
    assert handoff["work_unit_fingerprint"] == stale_fingerprint
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat-stale-gate-replay"
    )
    assert result["active_run_id"] is None


from .provider_admission_projection_cases.current_control_typed_blocker import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.gate_replay_admission_currentness import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.progress_first_admission_sync import *  # noqa: F403,F401,E402
