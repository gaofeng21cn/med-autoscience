from __future__ import annotations

import json
from pathlib import Path


def test_independent_review_stage_has_bounded_repair_and_residual_user_review_contract() -> None:
    contract = json.loads(Path("contracts/mas-paper-study-stage-pack.json").read_text(encoding="utf-8"))
    stage = {
        item["stage_id"]: item
        for item in contract["stages"]
    }["07-independent_review_and_revision"]

    policy = stage["bounded_review_repair_policy"]
    assert policy["max_automated_repair_rounds"] == 3
    assert policy["independent_reviewer_context_required"] is True
    assert policy["auto_advance_when_no_clear_actionable_issue"] is True
    assert policy["after_round_budget_without_hard_blocker"] == "advance_to_next_stage_with_residual_user_review"
    assert policy["residual_user_review_language"] == "zh-CN"
    assert policy["residual_user_review_artifact_role"] == "residual_reviewer_issues_user_review"
    assert policy["authority_boundary"] == {
        "residual_user_review_can_authorize_quality": False,
        "residual_user_review_can_authorize_submission": False,
        "residual_user_review_can_block_auto_advance": False,
    }

    roles = {item["role"]: item["artifact_ref"] for item in stage["stable_artifact_roles"]}
    assert roles["residual_reviewer_issues_user_review"] == (
        "manuscript/inspection_package/residual_reviewer_issues.md"
    )
