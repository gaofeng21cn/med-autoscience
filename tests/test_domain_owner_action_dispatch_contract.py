from __future__ import annotations

from med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract import (
    dispatch_contract_error,
)
from med_autoscience.controllers.domain_owner_action_dispatch_parts import (
    opl_execution_preflight,
)
from med_autoscience.controllers import domain_owner_action_dispatch
from tests.provider_admission_current_control_helpers import opl_transition_readback


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
    return opl_transition_readback(
        study_id,
        action_fingerprint=work_unit_fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=request_key,
        attempt_idempotency_key=request_key,
        request_idempotency_key=request_key,
        stage_run_id=f"stage-run::{study_id}::{work_unit_id}",
    )


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


def test_closeout_binding_does_not_authorize_owner_callable_execution() -> None:
    binding = {
        "surface_kind": "medical_paper_readiness_closeout_binding",
        "stage_run_id": "stage-run::study-a::write_delta",
        "stage_manifest_ref": "stages/write_delta/stage_manifest.json",
        "current_pointer_ref": "stages/write_delta/current.json",
        "closeout_refs": ["stages/write_delta/owner_receipt.json"],
        "source_fingerprint": "truth-source::study-a::write_delta",
        "work_unit_fingerprint": "fingerprint-a",
    }
    blocked = opl_execution_preflight.block_if_missing_authorization(
        dispatch=_dispatch(
            study_id="study-a",
            next_work_unit={"unit_id": "write_delta"},
            work_unit_fingerprint="fingerprint-a",
            closeout_binding=binding,
            prompt_contract={"closeout_binding": binding},
        ),
        owner_route_basis=None,
        current_study={},
    )

    assert blocked is not None
    assert blocked["blocked_reason"] == "opl_execution_authorization_required"
    assert blocked["mas_dispatch_authority"] is False
    assert blocked["mas_creates_opl_outbox"] is False
    assert blocked["mas_creates_opl_event"] is False
    assert blocked["mas_creates_opl_stage_run"] is False


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


def test_dispatch_study_discovery_ignores_owner_callable_adapter_list(tmp_path) -> None:
    profile = type(
        "Profile",
        (),
        {
            "studies_root": tmp_path / "studies",
        },
    )()
    (tmp_path / "studies").mkdir()
    consumer_payload = {
        "owner_callable_adapters": [
            {
                "study_id": "legacy-adapter-study",
                "dispatch_status": "ready",
            }
        ],
        "domain_progress_transition_requests": [
            {
                "study_id": "canonical-transition-study",
                "dispatch_status": "transition_request_pending",
            }
        ],
    }

    resolved = domain_owner_action_dispatch._resolve_study_ids(
        profile,
        (),
        consumer_payload=consumer_payload,
    )

    assert resolved == ("canonical-transition-study",)


def test_current_consumer_dispatches_ignore_owner_callable_adapter_list(tmp_path) -> None:
    from med_autoscience.controllers.domain_owner_action_dispatch_parts import persisted_dispatches

    study_id = "study-a"
    legacy_dispatch = _dispatch(
        study_id=study_id,
        refs={"dispatch_path": str(tmp_path / "legacy.json")},
    )
    canonical_dispatch = _projection(
        study_id=study_id,
        refs={"dispatch_path": str(tmp_path / "canonical.json")},
    )
    consumer_payload = {
        "owner_callable_adapters": [legacy_dispatch],
        "domain_progress_transition_requests": [canonical_dispatch],
    }

    dispatches = persisted_dispatches.current_consumer_dispatches(
        study_id=study_id,
        consumer_payload=consumer_payload,
        consumer_latest_path=tmp_path / "missing.json",
    )

    assert len(dispatches) == 1
    assert dispatches[0]["refs"]["dispatch_path"] == str(tmp_path / "canonical.json")
    assert dispatches[0]["surface"] == "mas_domain_progress_transition_request_projection"


def test_current_materialized_dispatches_ignore_owner_callable_adapter_list(tmp_path) -> None:
    from med_autoscience.controllers.domain_owner_action_dispatch_parts import (
        current_dispatch_materialization,
    )

    profile = type("Profile", (), {"studies_root": tmp_path / "studies"})()
    study_id = "study-a"
    legacy_dispatch = _dispatch(study_id=study_id)
    canonical_dispatch = _projection(study_id=study_id)

    def current_owner_callable_adapters(**_: object) -> dict[str, object]:
        return {
            "owner_callable_adapters": [legacy_dispatch],
            "domain_progress_transition_requests": [canonical_dispatch],
        }

    dispatches = current_dispatch_materialization.current_materialized_dispatches(
        profile=profile,
        study_id=study_id,
        action_types=("run_quality_repair_batch",),
        mode="preview",
        apply=False,
        current_owner_callable_adapters=current_owner_callable_adapters,
        text=lambda value: str(value).strip() if value else None,
    )

    assert len(dispatches) == 1
    assert dispatches[0]["surface"] == "mas_domain_progress_transition_request_projection"
