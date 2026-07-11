from __future__ import annotations

import pytest

from med_autoscience.controllers.paper_mission_owner_surface import opl_provider_attempts


@pytest.mark.parametrize("live_work_unit, current_work_unit", [(None, "wu-1"), ("wu-1", None), ("wu-1", "wu-2")])
def test_live_attempt_requires_exact_work_unit_identity(
    live_work_unit: str | None,
    current_work_unit: str | None,
) -> None:
    live_attempt = {"action_type": "run_review", "work_unit_id": live_work_unit}
    action = {"action_type": "run_review", "work_unit_id": current_work_unit}
    owner_route = {
        "allowed_actions": ["run_review"],
        "work_unit_id": current_work_unit,
    }

    assert not opl_provider_attempts.action_is_covered_by_live_attempt(
        live_attempt=live_attempt,
        action=action,
    )
    assert not opl_provider_attempts.owner_route_is_covered_by_live_attempt(
        live_attempt=live_attempt,
        owner_route=owner_route,
    )


def test_live_attempt_covers_only_the_same_action_and_work_unit() -> None:
    live_attempt = {"action_type": "run_review", "work_unit_id": "wu-1"}
    action = {"action_type": "run_review", "work_unit_id": "wu-1"}
    owner_route = {"allowed_actions": ["run_review"], "work_unit_id": "wu-1"}

    assert opl_provider_attempts.action_is_covered_by_live_attempt(
        live_attempt=live_attempt,
        action=action,
    )
    assert opl_provider_attempts.owner_route_is_covered_by_live_attempt(
        live_attempt=live_attempt,
        owner_route=owner_route,
    )
