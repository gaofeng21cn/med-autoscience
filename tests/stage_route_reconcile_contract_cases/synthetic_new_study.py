from __future__ import annotations

from typing import Any


def assert_synthetic_new_study_route_policy(contract: dict[str, Any]) -> None:
    policy = contract["next_action_supersession"]["synthetic_new_study_route_policy"]

    assert policy["fixture"] == "dm004_synthetic_new_study"
    assert policy["canonical_route_authority"] == "NextActionEnvelope.action_family"
    assert policy["work_unit_id_role"] == "diagnostic_currentness_id_only"
    assert policy["exact_work_unit_id_authority"] is False
    assert policy["unknown_exact_work_unit_id_effect"] == (
        "accept_when_next_action_envelope_action_family_is_allowed"
    )
    assert policy["missing_next_action_envelope_effect"] == (
        "fail_closed_to_diagnostic_or_typed_blocker_candidate"
    )
    assert policy["forbidden_mapping_requirement"] == (
        "do_not_add_per_study_exact_work_unit_mapping_for_authority_route"
    )
    assert policy["required_authority_boundary"] == {
        "action_family_authority": True,
        "exact_work_unit_id_authority": False,
        "can_write_runtime_queue_or_provider_attempt": False,
    }
