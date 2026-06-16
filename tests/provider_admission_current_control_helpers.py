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
    stage_run_id: str | None = None,
) -> dict[str, object]:
    stage_run_id = stage_run_id or f"stage-run::{study_id}::{action_fingerprint}"
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "outcome_kind": "provider_admission_pending",
        "event_id": f"opl-domain-progress-event::{study_id}::{action_fingerprint}",
        "outbox_item_id": f"opl-domain-progress-outbox::{study_id}::{action_fingerprint}",
        "stage_run_id": stage_run_id,
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
