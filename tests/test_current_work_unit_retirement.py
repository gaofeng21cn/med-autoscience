from __future__ import annotations

import importlib


def test_current_work_unit_default_selector_is_retired_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    result = module.build_current_work_unit(
        actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "work_unit_id": "legacy-gate-replay",
                "work_unit_fingerprint": "sha256:legacy-gate-replay",
            }
        ],
        blocked_reason="legacy_owner_route_available",
        next_owner="gate_clearing_batch",
    )

    assert result == {}


def test_current_work_unit_does_not_promote_provider_or_envelope_residue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    result = module.build_current_work_unit(
        current_execution_envelope={
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "legacy-envelope-work-unit",
        },
        live_provider_attempt={
            "status": "running",
            "work_unit_id": "legacy-provider-attempt",
        },
        provider_admission={"status": "ready"},
        blocked_reason="legacy_running_provider_attempt",
        next_owner="write",
    )

    assert result == {}


def test_current_work_unit_typed_blocker_supersession_is_fail_closed() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    assert (
        module.action_supersedes_typed_blocker(
            action={"action_type": "run_gate_clearing_batch"},
            blocker={"blocker_id": "opl_execution_authorization_required"},
        )
        is False
    )
    assert (
        module.action_supersedes_typed_blocker(
            action={"action_type": "run_gate_clearing_batch"},
            blocker=None,
        )
        is True
    )


def test_current_work_unit_retirement_boundary_is_explicit() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")

    boundary = module.retired_authority_boundary()

    assert boundary["status"] == "retired"
    assert boundary["replacement_authority"] == "StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt"
    assert boundary["can_select_next_action"] is False
    assert boundary["can_authorize_dispatch"] is False
    assert boundary["can_start_provider_attempt"] is False
