from __future__ import annotations


def provider_candidate(profile, study_id: str, *, action_fingerprint: str) -> dict[str, object]:
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
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
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": f"opl-domain-progress-event::{study_id}::{action_fingerprint}",
        "outbox_item_id": f"opl-domain-progress-outbox::{study_id}::{action_fingerprint}",
        "stage_run_identity": {
            "stage_run_id": stage_run_id,
            "stage_run_identity_ref": f"stage-run-identity::{study_id}::{action_fingerprint}",
            "observed_generation": action_fingerprint,
        },
        "identity": {
            "study_id": study_id,
            "quest_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "route_identity_key": route_identity_key,
            "attempt_idempotency_key": attempt_idempotency_key,
        },
        "causality": {
            "mas_transition_request_idempotency_key": request_idempotency_key,
            "source_generation": action_fingerprint,
            "expected_version": action_fingerprint,
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
            "observed_generation": action_fingerprint,
        },
    }


def provider_candidate_with_opl_readback(
    profile,
    study_id: str,
    *,
    action_fingerprint: str,
) -> dict[str, object]:
    candidate = provider_candidate(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )
    candidate["opl_domain_progress_transition_result"] = opl_transition_readback(
        study_id,
        action_fingerprint=action_fingerprint,
    )
    return candidate
