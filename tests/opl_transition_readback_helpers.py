from __future__ import annotations


def provider_candidate(profile, study_id: str, *, action_fingerprint: str) -> dict[str, object]:
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    )
    identity_key = f"provider-admission::{study_id}::{action_fingerprint}"
    return {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(dispatch_path),
        "stage_packet_ref": str(dispatch_path),
        "stage_packet_refs": [str(dispatch_path)],
        "route_identity_key": identity_key,
        "attempt_idempotency_key": identity_key,
        "idempotency_key": identity_key,
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }


def opl_transition_readback(
    study_id: str,
    *,
    action_fingerprint: str,
    work_unit_id: str = "produce_ai_reviewer_publication_eval_record_against_current_inputs",
    route_identity_key: str | None = None,
    attempt_idempotency_key: str | None = None,
    request_idempotency_key: str | None = None,
    stage_run_id: str | None = None,
) -> dict[str, object]:
    stage_run_id = stage_run_id or f"stage-run::{study_id}::{action_fingerprint}"
    route_identity_key = route_identity_key or f"provider-admission::{study_id}::{action_fingerprint}"
    attempt_idempotency_key = attempt_idempotency_key or route_identity_key
    request_idempotency_key = request_idempotency_key or route_identity_key
    event_id = f"opl-domain-progress-event::{study_id}::{action_fingerprint}"
    outbox_item_id = f"opl-domain-progress-outbox::{study_id}::{action_fingerprint}"
    transaction_id = f"opl-domain-progress-transaction::{study_id}::{action_fingerprint}"
    aggregate_identity = {
        "aggregate_kind": "study_work_unit",
        "aggregate_id": f"{study_id}::{work_unit_id}",
        "study_id": study_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
    }
    stage_run_identity = {
        "stage_run_id": stage_run_id,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
        "source_generation": action_fingerprint,
    }
    identity = {
        "surface_kind": "opl_domain_progress_transition_identity",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "aggregate_identity": aggregate_identity,
        "stage_run_identity": stage_run_identity,
        "idempotency_key": request_idempotency_key,
        "command_id": f"opl-domain-progress-command::{study_id}::{action_fingerprint}",
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "transaction_id": transaction_id,
        "latest_event_id": event_id,
        "latest_outbox_item_id": outbox_item_id,
        "latest_transaction_id": transaction_id,
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_enqueued_or_blocked",
    }
    causality = {
        "surface_kind": "opl_domain_progress_transition_causality",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "command_id": identity["command_id"],
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "transaction_id": transaction_id,
        "source_generation": action_fingerprint,
        "expected_version": action_fingerprint,
        "derived_from_event_id": event_id,
        "source_event_ids": [event_id],
        "source_outbox_item_ids": [outbox_item_id],
        "same_transaction_event_and_outbox": True,
        "runtime_readback_status": "complete_transaction",
        "transaction_complete": True,
    }
    authority_boundary = {
        "authority": False,
        "runtime_owner": "one-person-lab",
        "opl_can_write_domain_truth": False,
        "opl_can_write_mas_truth": False,
        "opl_can_create_domain_owner_receipt": False,
        "opl_can_create_domain_typed_blocker": False,
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "read_model_can_execute": False,
        "projection_can_authorize_provider_admission": False,
    }
    exactly_one_outcome = {
        "surface_kind": "opl_domain_progress_exactly_one_outcome",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "selected": True,
        "exactly_one_transition": True,
        "transition_count": 1,
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_enqueued_or_blocked",
        "stable_outcome": True,
        "non_advancing_apply": False,
        "fail_closed": False,
    }
    projection_metadata = {
        "surface_kind": "opl_domain_progress_projection_metadata",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "authority": False,
        "derived_from_event_id": event_id,
        "observed_generation": action_fingerprint,
        "derived_generation": action_fingerprint,
        "lag_status": "current",
        "read_model_rebuild_owner": "one-person-lab",
    }
    return {
        "surface_kind": "opl_domain_progress_transition_runtime_live_readback",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "evidence_source": {
            "source_kind": "fixture_or_replay_readback",
            "source_ref": "tests/opl_transition_readback_helpers.py::opl_transition_readback",
        },
        "storage_contract": "append_only_physical_jsonl",
        "runtime_readback_status": "complete_transaction",
        "transaction_complete": True,
        "append_only_log_entry_count": 3,
        "identity": identity,
        "causality": causality,
        "authority_boundary": authority_boundary,
        "exactly_one_outcome": exactly_one_outcome,
        "projection_metadata": projection_metadata,
        "read_model_readback": {
            "surface_kind": "opl_domain_progress_transition_read_model",
            "identity": identity,
            "causality": causality,
            "authority_boundary": authority_boundary,
            "exactly_one_outcome": exactly_one_outcome,
            "projection_metadata": projection_metadata,
        },
        "idempotency_readback": {
            "found": True,
            "idempotency_key": request_idempotency_key,
            "same_transaction_event_and_outbox": True,
        },
        "latest_transaction_readback": {
            "transaction_id": transaction_id,
            "command_present": True,
            "event_present": True,
            "outbox_item_present": True,
            "event_id": event_id,
            "outbox_item_id": outbox_item_id,
            "same_transaction_event_and_outbox": True,
            "transition_event_id": event_id,
            "outbox_transition_event_id": event_id,
        },
    }


def opl_transition_replay_audit_readback(
    study_id: str,
    *,
    action_fingerprint: str,
    work_unit_id: str = "produce_ai_reviewer_publication_eval_record_against_current_inputs",
    route_identity_key: str | None = None,
    attempt_idempotency_key: str | None = None,
    request_idempotency_key: str | None = None,
    stage_run_id: str | None = None,
) -> dict[str, object]:
    live = opl_transition_readback(
        study_id,
        action_fingerprint=action_fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_identity_key,
        attempt_idempotency_key=attempt_idempotency_key,
        request_idempotency_key=request_idempotency_key,
        stage_run_id=stage_run_id,
    )
    identity = live["identity"]
    causality = live["causality"]
    projection = live["projection_metadata"]
    return {
        "surface_kind": "opl_domain_progress_transition_replay_audit",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "authority": False,
        "replay_status": "replay_ready",
        "read_model_projection_consumable": True,
        "exactly_one_complete_transaction": True,
        "transaction_complete": True,
        "transition_count": 1,
        "aggregate_identity": dict(identity["aggregate_identity"]),
        "aggregate_version": 1,
        "transaction_id": identity["latest_transaction_id"],
        "event_id": identity["latest_event_id"],
        "outbox_item_id": identity["latest_outbox_item_id"],
        "idempotency_key": identity["idempotency_key"],
        "command_present": True,
        "event_present": True,
        "outbox_item_present": True,
        "same_outbox_identity": True,
        "same_transaction_event_and_outbox": True,
        "same_stage_run_identity": True,
        "stage_run_identity_readback": {
            "surface_kind": "opl_domain_progress_stage_run_identity_readback",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "same_stage_run_identity": True,
            "command_stage_run_identity_present": True,
            "event_stage_run_identity_present": True,
            "outbox_stage_run_identity_present": True,
            "command_stage_run_identity": dict(identity["stage_run_identity"]),
            "event_stage_run_identity": dict(identity["stage_run_identity"]),
            "outbox_stage_run_identity": dict(identity["stage_run_identity"]),
            **dict(identity["stage_run_identity"]),
            "fail_closed_reason": None,
        },
        "exactly_one_outcome": dict(live["exactly_one_outcome"]),
        "projection_metadata": {
            "surface_kind": "opl_domain_progress_transition_replay_projection_metadata",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "authority": False,
            "projection_role": "replay_ready_complete_transaction",
            "read_model_projection_consumable": True,
            "transaction_complete": True,
            "replay_status": "replay_ready",
            "exactly_one_complete_transaction": True,
            "derived_from_event_id": projection["derived_from_event_id"],
            "observed_generation": projection["observed_generation"],
            "read_model_rebuild_owner": "one-person-lab",
        },
        "source_generation": causality["source_generation"],
        "expected_version": causality["expected_version"],
    }


def provider_candidate_with_opl_readback(
    profile,
    study_id: str,
    *,
    action_fingerprint: str,
    work_unit_id: str = "produce_ai_reviewer_publication_eval_record_against_current_inputs",
    action_type: str = "return_to_ai_reviewer_workflow",
    next_executable_owner: str = "ai_reviewer",
    required_output_surface: str = "artifacts/publication_eval/latest.json",
) -> dict[str, object]:
    candidate = {
        **provider_candidate(
            profile,
            study_id,
            action_fingerprint=action_fingerprint,
        ),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": required_output_surface,
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }
    candidate["opl_domain_progress_transition_live_readback"] = opl_transition_readback(
        study_id,
        action_fingerprint=action_fingerprint,
        work_unit_id=work_unit_id,
    )
    return candidate
