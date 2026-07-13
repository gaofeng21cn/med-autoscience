from med_autoscience.controllers.opl_stage_attempt_readback import (
    has_opl_stage_attempt_readback,
    provider_attempt_stage_attempt_readback,
)


def test_stage_attempt_transport_readback_never_requires_semantic_transaction() -> None:
    payload = {
        "surface_kind": "opl_stage_attempt_readback",
        "status": "running",
        "stage_attempt_ref": "opl://attempt/1",
    }

    assert has_opl_stage_attempt_readback(payload) is True
    assert provider_attempt_stage_attempt_readback(payload) == payload


def test_transition_runtime_payload_is_not_a_supported_readback() -> None:
    payload = {
        "surface_kind": "opl_domain_progress_transition_runtime_live_readback",
        "runtime_readback_status": "complete_transaction",
        "transaction_complete": True,
    }

    assert has_opl_stage_attempt_readback(payload) is False
