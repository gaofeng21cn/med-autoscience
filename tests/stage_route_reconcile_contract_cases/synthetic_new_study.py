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
    assert policy["canonical_next_action_fixture"] == {
        "surface_kind": "mas_next_action_envelope",
        "schema_version": 1,
        "study_id": "004-synthetic-route",
        "stage_id": "08-publication_package_handoff",
        "action_id": "next-action::dm004::story-repair",
        "action_family": "paper.write.prose_repair",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "dm004_never_mapped_next_action_story_repair",
        "work_unit_fingerprint": "stage-outcome::dm004::story-repair",
        "authority_boundary": {
            "action_family_authority": True,
            "exact_work_unit_id_authority": False,
            "can_write_runtime_queue_or_provider_attempt": False,
        },
    }
    assert policy["legacy_fallback_negative_fixture"] == {
        "fixture_role": "negative_no_resurrection_guard",
        "must_not_select_default_next_action": True,
        "must_not_authorize_provider_admission": True,
        "work_unit_id": "dm004_never_mapped_next_action_story_repair",
        "controller_action_type": "run_quality_repair_batch",
        "control_surface": "quality_repair_batch",
        "expected_blocking_reason": "controller_route_work_unit_unsupported",
    }
