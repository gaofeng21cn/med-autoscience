from __future__ import annotations

from med_autoscience.reviewer_issue_progress_contract import (
    REQUIRED_ISSUE_LEDGER_FIELDS,
    build_reviewer_issue_progress_contract,
)


def test_reviewer_issue_progress_contract_absorbs_ark_patterns_without_authority_leak() -> None:
    contract = build_reviewer_issue_progress_contract()

    assert contract["surface_kind"] == "mas_reviewer_issue_progress_contract"
    assert contract["owner"] == "MedAutoScience"
    assert contract["clean_room_absorption"] == {
        "source_project": "kaust-ark/ARK",
        "source_commit": "01cab1048cc78fa4d33e8274e4f963a44d70dc48",
        "absorbed_as": "mas_native_contract_pattern",
        "runtime_dependency": False,
        "vendor_dependency": False,
        "foreign_authority": False,
    }

    boundary = contract["authority_boundary"]
    assert boundary["truth_owner"] == "MedAutoScience"
    assert boundary["publication_readiness_authority"] is False
    assert boundary["quality_verdict_authority"] is False
    assert boundary["artifact_mutation_authority"] is False
    assert boundary["source_readiness_authority"] is False
    assert boundary["score_threshold_authority"] is False
    assert boundary["stagnation_authority"] == "advisory_route_signal_only"


def test_reviewer_issue_ledger_fields_and_goal_anchor_currentness_are_required() -> None:
    contract = build_reviewer_issue_progress_contract()

    assert contract["issue_ledger"]["required_fields"] == list(REQUIRED_ISSUE_LEDGER_FIELDS)
    assert set(REQUIRED_ISSUE_LEDGER_FIELDS) >= {
        "issue_id",
        "title",
        "severity",
        "issue_kind",
        "reviewer_record_ref",
        "canonical_artifact_digest",
        "refined_work_unit_ref",
        "status",
        "repeat_count",
        "attempted_fix_refs",
        "resolution_evidence_refs",
        "currentness",
    }
    assert contract["goal_anchor_currentness"] == {
        "required_fields": [
            "study_charter_ref",
            "goal_anchor_ref",
            "anchor_digest",
            "canonical_artifact_ref",
            "canonical_artifact_digest",
            "checked_at",
        ],
        "stale_if_digest_mismatch": True,
        "stale_behavior": "typed_anchor_refresh_work_unit_or_reviewer_route_back",
        "may_authorize_publication_readiness": False,
    }


def test_progress_first_policy_turns_repeat_issues_into_work_units_not_global_stall() -> None:
    contract = build_reviewer_issue_progress_contract()
    policy = contract["progress_first_policy"]

    assert policy["repeat_issue_behavior"] == "typed_repair_work_unit_or_reviewer_route_back"
    assert policy["score_delta_behavior"] == "advisory_progress_signal_only"
    assert policy["stagnation_behavior"] == "route_bias_not_publication_verdict"
    assert policy["may_block_all_agent_progress"] is False
    assert policy["hard_gate_blockers"] == [
        "source_readiness_gate",
        "publication_gate",
        "artifact_mutation_authority_gate",
        "human_or_expert_gate",
        "forbidden_write_guard",
    ]
