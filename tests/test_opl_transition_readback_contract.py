from __future__ import annotations

import importlib


def _trusted_readback() -> dict[str, object]:
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": "opl-domain-progress-event:003-write",
        "outbox_item_id": "opl-domain-progress-outbox:003-write",
        "stage_run_identity": {
            "stage_run_id": "sat_003_write",
            "stage_run_identity_ref": "stage-run-identity:003-write",
            "observed_generation": "publication-blockers::0915410f804b3697",
        },
        "identity": {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "route_identity_key": (
                "provider-admission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "publication-blockers::0915410f804b3697"
            ),
            "attempt_idempotency_key": (
                "provider-admission::003-dpcc-primary-care-phenotype-treatment-gap::"
                "publication-blockers::0915410f804b3697"
            ),
        },
        "causality": {
            "mas_transition_request_idempotency_key": "paper-policy-request:003-write",
            "source_generation": "publication-blockers::0915410f804b3697",
            "expected_version": "publication-blockers::0915410f804b3697",
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
            "observed_generation": "publication-blockers::0915410f804b3697",
        },
    }


def test_trusted_opl_transition_readback_requires_full_runtime_shape() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback"
    )

    assert module.valid_opl_transition_readback(_trusted_readback()) is True

    weak_readback = {
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "outcome_kind": "provider_admission_pending",
        "event_id": "opl-domain-progress-event:003-write",
        "stage_run_id": "sat_003_write",
    }

    assert module.valid_opl_transition_readback(weak_readback) is False
    assert module.candidate_opl_transition_readback(
        {
            "opl_domain_progress_transition_result": weak_readback,
            "deprecated_opl_transition_projection": weak_readback,
        }
    ) == {}


def test_provider_admission_requires_structured_opl_readback_not_deprecated_projection() -> None:
    identity = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
        "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "mas_can_create_opl_outbox_record": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_stage_run": False,
        },
        "deprecated_opl_transition_projection": {
            "runtime_owner": "one-person-lab",
            "runtime_kind": "DomainProgressTransitionRuntime",
            "outcome_kind": "provider_admission_pending",
            "event_id": "legacy-event-only",
            "stage_run_id": "legacy-stage-run-only",
        },
    }

    pending = identity.provider_admission_current_control_action(candidate)
    assert pending["status"] == "transition_request_pending"
    assert pending["provider_admission_pending"] is False
    assert pending["provider_admission_requires_opl_runtime_result"] is True
    assert "opl_domain_progress_transition_result" not in pending

    admitted = identity.provider_admission_current_control_action(
        {**candidate, "opl_domain_progress_transition_result": _trusted_readback()}
    )
    assert admitted["status"] == "queued"
    assert admitted["provider_admission_pending"] is True
    assert admitted["provider_attempt_or_lease_required"] is True
    assert admitted["provider_completion_is_domain_completion"] is False
    assert admitted["opl_domain_progress_transition_result"]["identity"]["study_id"] == study_id
