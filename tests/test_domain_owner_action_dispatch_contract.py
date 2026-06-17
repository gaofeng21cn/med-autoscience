from __future__ import annotations

from med_autoscience.controllers.domain_owner_action_dispatch_parts.dispatch_contract import (
    dispatch_contract_error,
)


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
