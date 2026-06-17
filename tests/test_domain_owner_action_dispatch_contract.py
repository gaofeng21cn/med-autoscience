from __future__ import annotations

from med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract import (
    dispatch_contract_error,
)
from med_autoscience.controllers import domain_owner_action_dispatch


SUPPORTED_ACTION_TYPES = frozenset({"run_quality_repair_batch"})


def _dispatch(**overrides: object) -> dict[str, object]:
    payload = {
        "surface": "default_executor_dispatch_request",
        "dispatch_status": "ready",
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "action_type": "run_quality_repair_batch",
        "target_runtime_owner": "one-person-lab",
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
    }
    payload.update(overrides)
    return payload


def test_dispatch_contract_rejects_mas_private_authority_claims() -> None:
    for key in (
        "mas_dispatch_authority",
        "mas_creates_opl_outbox",
        "mas_creates_opl_event",
        "mas_creates_opl_stage_run",
    ):
        assert (
            dispatch_contract_error(
                _dispatch(**{key: True}),
                apply=True,
                supported_action_types=SUPPORTED_ACTION_TYPES,
            )
            == f"{key}_forbidden"
        )


def test_dispatch_contract_rejects_non_opl_runtime_owner() -> None:
    assert (
        dispatch_contract_error(
            _dispatch(target_runtime_owner="med-autoscience"),
            apply=True,
            supported_action_types=SUPPORTED_ACTION_TYPES,
        )
        == "target_runtime_owner_mismatch"
    )


def _projection(**overrides: object) -> dict[str, object]:
    payload = _dispatch(
        surface="mas_domain_progress_transition_request_projection",
        legacy_surface="default_executor_dispatch_request",
        projection_only=True,
        owner_callable_carrier_projection_only=True,
    )
    payload["prompt_contract"] = {
        "prompt_budget": {},
        "compact_evidence_packet_ref": "packet://evidence",
        "do_not_repeat": True,
        "repeat_suppression_key": "repeat-key",
        "forbidden_surfaces": list(domain_owner_action_dispatch.FORBIDDEN_SURFACES),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    payload.update(overrides)
    return payload


def _opl_transition_readback(
    *,
    study_id: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    request_key: str,
) -> dict[str, object]:
    return {
        "surface_kind": "opl_domain_progress_transition_result",
        "runtime_owner": "one-person-lab",
        "runtime_kind": "DomainProgressTransitionRuntime",
        "transition_kind": "StartProviderAttempt",
        "outcome_kind": "provider_admission_pending",
        "event_id": f"event::{study_id}::{work_unit_id}",
        "outbox_item_id": f"outbox::{study_id}::{work_unit_id}",
        "stage_run_identity": {
            "stage_run_id": f"stage-run::{study_id}::{work_unit_id}",
            "observed_generation": work_unit_fingerprint,
        },
        "identity": {
            "study_id": study_id,
            "quest_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "route_identity_key": request_key,
            "attempt_idempotency_key": request_key,
        },
        "causality": {
            "mas_transition_request_idempotency_key": request_key,
            "source_generation": work_unit_fingerprint,
            "expected_version": work_unit_fingerprint,
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
            ],
            "rejected": [],
        },
        "projection_metadata": {
            "authority": False,
            "projection_owner": "one-person-lab",
            "consumer": "med-autoscience",
            "observed_generation": work_unit_fingerprint,
        },
    }


def _opl_authorization() -> dict[str, object]:
    return {
        "owner": "one-person-lab",
        "executor_kind": "codex_cli_default",
        "provider_attempt_ref": "temporal://attempt/sat-current",
        "attempt_lease_ref": "temporal://lease/sat-current",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": "opl://execution-authorizations/sat-current",
        "stage_attempt_id": "sat-current",
    }


def test_transition_request_projection_requires_opl_execution_authorization() -> None:
    assert domain_owner_action_dispatch._contract_guard(
        _projection(),
        apply=False,
    ) == (False, "opl_execution_authorization_required")


def test_transition_request_projection_with_opl_authorization_is_owner_callable_adapter() -> None:
    payload = _projection(opl_execution_authorization=_opl_authorization())

    assert domain_owner_action_dispatch._contract_guard(payload, apply=False) == (True, None)
    assert payload["surface"] == "mas_domain_progress_transition_request_projection"
    contract_payload = domain_owner_action_dispatch._dispatch_contract_payload(payload)
    assert contract_payload["surface"] == "default_executor_dispatch_request"
    assert contract_payload["legacy_surface"] == "default_executor_dispatch_request"


def test_transition_request_projection_accepts_matching_opl_transition_readback() -> None:
    payload = _projection(
        study_id="study-a",
        next_work_unit={"unit_id": "write_delta"},
        work_unit_fingerprint="fingerprint-a",
        opl_domain_progress_transition_request={
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "idempotency_key": "request-a",
            "work_unit_id": "write_delta",
            "work_unit_fingerprint": "fingerprint-a",
        },
        opl_domain_progress_transition_result=_opl_transition_readback(
            study_id="study-a",
            work_unit_id="write_delta",
            work_unit_fingerprint="fingerprint-a",
            request_key="request-a",
        ),
    )

    assert domain_owner_action_dispatch._contract_guard(payload, apply=False) == (True, None)


def test_transition_request_projection_rejects_unbound_opl_transition_readback() -> None:
    payload = _projection(
        study_id="study-a",
        next_work_unit={"unit_id": "write_delta"},
        work_unit_fingerprint="fingerprint-a",
        opl_domain_progress_transition_request={
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "idempotency_key": "request-a",
            "work_unit_id": "write_delta",
            "work_unit_fingerprint": "fingerprint-a",
        },
        opl_domain_progress_transition_result=_opl_transition_readback(
            study_id="study-a",
            work_unit_id="stale_delta",
            work_unit_fingerprint="stale-fingerprint",
            request_key="stale-request",
        ),
    )

    assert domain_owner_action_dispatch._contract_guard(
        payload,
        apply=False,
    ) == (False, "opl_execution_authorization_required")


def test_unknown_dispatch_surface_remains_unsupported() -> None:
    assert domain_owner_action_dispatch._contract_guard(
        _dispatch(surface="legacy_unknown_dispatch"),
        apply=False,
    ) == (False, "unsupported_dispatch_surface")
