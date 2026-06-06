from __future__ import annotations

from med_autoscience.controllers.opl_execution_boundary import (
    trusted_opl_execution_authorization,
)


def _authorization(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "owner": "one-person-lab",
        "executor_kind": "codex_cli",
        "provider_attempt_ref": "opl://stage-attempts/sat-live",
        "stage_attempt_id": "sat-live",
        "attempt_lease_ref": "opl://stage-attempts/sat-live/leases/task-live/active",
        "attempt_lease_status": "active",
        "execution_authorization_decision_ref": (
            "opl://stage-attempts/sat-live/execution-authorizations/task-live/wf-live"
        ),
    }
    payload.update(overrides)
    return payload


def test_trusted_opl_execution_authorization_requires_explicit_provider_attempt_ref() -> None:
    payload = _authorization(provider_attempt_ref=None)

    assert trusted_opl_execution_authorization(payload) is None


def test_trusted_opl_execution_authorization_requires_active_lease_and_decision_ref() -> None:
    assert trusted_opl_execution_authorization(_authorization()) is not None
    assert trusted_opl_execution_authorization(_authorization(attempt_lease_status="expired")) is None
    assert trusted_opl_execution_authorization(
        _authorization(execution_authorization_decision_ref=None)
    ) is None
