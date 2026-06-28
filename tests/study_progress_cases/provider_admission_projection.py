from __future__ import annotations

import json

from tests.provider_admission_current_control_helpers import (
    opl_transition_readback,
)
from .shared import _write_json


def _opl_transition_result(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    stage_run_id: str = "stage-run-provider-admission",
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
        stage_run_id=stage_run_id,
    )


def _non_advancing_opl_transition_result(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    stage_run_id: str = "stage-run-provider-admission",
) -> dict[str, object]:
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
        stage_run_id=stage_run_id,
    )
    readback["identity"]["transition_kind"] = "NonAdvancingApply"
    readback["identity"]["outcome_kind"] = "non_advancing_apply_typed_blocker_ref"
    readback["exactly_one_outcome"]["transition_kind"] = "NonAdvancingApply"
    readback["exactly_one_outcome"]["outcome_kind"] = "non_advancing_apply_typed_blocker_ref"
    readback["exactly_one_outcome"]["non_advancing_apply"] = True
    readback["read_model_readback"]["identity"] = readback["identity"]
    readback["read_model_readback"]["exactly_one_outcome"] = readback["exactly_one_outcome"]
    return readback


def _write_ready_quality_repair_dispatch(study_root, *, study_id: str, fingerprint: str) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_quality_repair_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
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
            "runtime_id": "opl_domain_progress_transition_runtime",
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": command_id,
                "aggregate_identity": aggregate_identity,
                "source_generation": source_generation,
                "expected_version": source_generation,
                "stage_run_identity": stage_run_identity,
            },
        },
        {
            "entry_kind": "event",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "transition_kind": "StartProviderAttempt",
                "command_id": command_id,
                "event_id": event_id,
                "aggregate_identity": aggregate_identity,
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
            "runtime_id": "opl_domain_progress_transition_runtime",
            "transaction_id": transaction_id,
            "idempotency_key": idempotency_key,
            "aggregate_identity": aggregate_identity,
            "payload": {
                "outbox_item_id": outbox_item_id,
                "transition_event_id": event_id,
                "outbox_kind": "start_provider_attempt",
                "aggregate_identity": aggregate_identity,
                "stage_run_identity": stage_run_identity,
            },
        },
    ]
    log_path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n",
        encoding="utf-8",
    )


def _accepted_owner_gate_stage_packet_payload(
    *,
    study_id: str,
    work_unit_id: str,
    fingerprint: str,
    stage_packet_ref: str,
    include_owner_gate_condition: bool = True,
    include_stage_packet_ref: bool = True,
) -> dict[str, object]:
    evidence_refs = [
        "human_gate:owner-gate-decision:0863b0b9a2d94867284fa160",
        "owner-gate-decision:0863b0b9a2d94867284fa160",
    ]
    if include_stage_packet_ref:
        evidence_refs.append(stage_packet_ref)
    conditions = []
    if include_owner_gate_condition:
        conditions.append(
            {
                "condition": "accepted_owner_gate_decision",
                "decision": "admit_identity_bound_stage_packet",
            }
        )
    return {
        "study_id": study_id,
        "quest_id": study_id,
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "conditions": conditions,
            "evidence_refs": evidence_refs,
            "next_safe_action": {
                "kind": "admit_identity_bound_stage_packet",
                "owner": "one-person-lab",
                "provider_admission_allowed": True,
            },
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "typed_blocker",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
            },
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                    "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": {
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
        },
        "current_executable_owner_action": None,
    }


from .provider_admission_projection_cases.owner_gate_transition_request import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.current_action_admission import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.pending_identity_and_refresh import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.current_control_typed_blocker import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.gate_replay_admission_currentness import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.progress_first_admission_sync import *  # noqa: F403,F401,E402
from .provider_admission_projection_cases.transition_request_readback import *  # noqa: F403,F401,E402
