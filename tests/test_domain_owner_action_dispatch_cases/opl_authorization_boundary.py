from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.controllers import domain_owner_action_dispatch
from med_autoscience.controllers.domain_owner_action_dispatch_parts import opl_execution_preflight
from tests.provider_admission_current_control_helpers import opl_transition_readback


pytestmark = pytest.mark.meta


def _projection(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "surface": "mas_domain_progress_transition_request_projection",
        "legacy_surface": "default_executor_dispatch_request",
        "projection_only": True,
        "owner_callable_carrier_projection_only": True,
        "dispatch_status": "transition_request_pending",
        "executor_kind": "codex_cli_default",
        "chat_completion_only_executor_forbidden": True,
        "action_type": "run_quality_repair_batch",
        "study_id": "study-a",
        "target_runtime_owner": "one-person-lab",
        "mas_dispatch_authority": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "work_unit_fingerprint": "fingerprint-a",
        "prompt_contract": {
            "prompt_budget": {},
            "compact_evidence_packet_ref": "packet://evidence",
            "do_not_repeat": True,
            "repeat_suppression_key": "repeat-key",
            "forbidden_surfaces": list(domain_owner_action_dispatch.FORBIDDEN_SURFACES),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
            "medical_claim_authoring_allowed": False,
        },
    }
    payload.update(overrides)
    return payload


def _trusted_authorization(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "owner": "one-person-lab",
        "executor_kind": "codex_cli_default",
        "provider_attempt_ref": "temporal://attempt/sat-current",
        "attempt_lease_ref": "temporal://lease/sat-current",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": "opl://execution-authorizations/sat-current",
        "stage_attempt_id": "sat-current",
    }
    payload.update(overrides)
    return payload


def _readback(*, work_unit_id: str = "write_delta", request_key: str = "request-a") -> dict[str, object]:
    return opl_transition_readback(
        "study-a",
        action_fingerprint="fingerprint-a",
        work_unit_id=work_unit_id,
        route_identity_key=request_key,
        attempt_idempotency_key=request_key,
        request_idempotency_key=request_key,
        stage_run_id=f"stage-run::study-a::{work_unit_id}",
    )


def test_owner_dispatch_fails_closed_without_opl_authorization_or_bound_readback() -> None:
    assert domain_owner_action_dispatch._contract_guard(_projection(), apply=False) == (
        False,
        "opl_execution_authorization_required",
    )
    blocked = opl_execution_preflight.block_if_missing_authorization(
        dispatch=_projection(),
        owner_route_basis=None,
        current_study={},
    )

    assert blocked is not None
    assert blocked["blocked_reason"] == "opl_execution_authorization_required"
    assert blocked["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert blocked["mas_dispatch_authority"] is False
    assert blocked["mas_creates_opl_outbox"] is False
    assert blocked["mas_creates_opl_event"] is False
    assert blocked["mas_creates_opl_stage_run"] is False
    assert blocked["provider_admission_pending"] is False


def test_owner_dispatch_accepts_trusted_opl_execution_authorization_only() -> None:
    payload = _projection(opl_execution_authorization=_trusted_authorization())

    assert domain_owner_action_dispatch._contract_guard(payload, apply=False) == (True, None)


def test_owner_dispatch_accepts_bound_domain_progress_transition_readback_only() -> None:
    payload = _projection(
        next_work_unit={"unit_id": "write_delta"},
        opl_domain_progress_transition_request={
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "idempotency_key": "request-a",
            "work_unit_id": "write_delta",
            "work_unit_fingerprint": "fingerprint-a",
        },
        opl_domain_progress_transition_result=_readback(),
    )

    assert domain_owner_action_dispatch._contract_guard(payload, apply=False) == (True, None)


def test_owner_dispatch_rejects_unbound_domain_progress_transition_readback() -> None:
    payload = _projection(
        next_work_unit={"unit_id": "write_delta"},
        opl_domain_progress_transition_request={
            "target_runtime_kind": "DomainProgressTransitionRuntime",
            "idempotency_key": "request-a",
            "work_unit_id": "write_delta",
            "work_unit_fingerprint": "fingerprint-a",
        },
        opl_domain_progress_transition_result=_readback(
            work_unit_id="stale_delta",
            request_key="stale-request",
        ),
    )

    assert domain_owner_action_dispatch._contract_guard(payload, apply=False) == (
        False,
        "opl_execution_authorization_required",
    )


def test_provider_hosted_exact_stage_attempt_authorizes_only_matching_stage_packet(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    dispatch = _projection(
        stage_packet_ref="stage-packet-a",
        action_type="run_quality_repair_batch",
        next_work_unit={"unit_id": "write_delta"},
    )
    monkeypatch.setenv("OPL_STAGE_ATTEMPT_ID", "sat-current")
    monkeypatch.setenv("OPL_STAGE_PACKET_REF", "stage-packet-a")
    monkeypatch.setenv("OPL_STAGE_ID", "domain_owner/default-executor-dispatch")
    monkeypatch.setenv("OPL_STUDY_ID", "study-a")
    monkeypatch.setenv("OPL_ACTION_TYPE", "run_quality_repair_batch")
    monkeypatch.setenv("OPL_WORK_UNIT_ID", "write_delta")
    monkeypatch.setenv("OPL_PROVIDER_ATTEMPT_REF", "temporal://attempt/sat-current")
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_REF", "temporal://lease/sat-current")
    monkeypatch.setenv("OPL_ATTEMPT_LEASE_STATUS", "active")
    monkeypatch.setenv(
        "OPL_EXECUTION_AUTHORIZATION_DECISION_REF",
        "opl://execution-authorizations/sat-current",
    )

    assert (
        opl_execution_preflight.provider_hosted_stage_attempt_authorizes_dispatch(dispatch)
        is True
    )

    mismatch = {**dispatch, "stage_packet_ref": "stage-packet-b"}
    assert (
        opl_execution_preflight.provider_hosted_stage_attempt_authorizes_dispatch(mismatch)
        is False
    )
