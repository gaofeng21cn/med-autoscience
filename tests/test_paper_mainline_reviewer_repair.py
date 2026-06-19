from __future__ import annotations

from med_autoscience.paper_mainline_reviewer_repair import (
    build_reviewer_repair_action_projection,
)


def test_builds_refs_only_reviewer_repair_action_projection() -> None:
    result = build_reviewer_repair_action_projection(
        [
            {
                "finding_id": "R1.1",
                "comment_ref": "review-ledger:R1.1",
                "comment_type": "unsupported_claim",
                "target_ref": "claim-map:primary-outcome",
                "severity": "major",
                "repair_action": "add_evidence",
                "required_refs": [
                    "evidence-ledger:primary-table",
                    {"ref": "citation-ledger:primary-source"},
                ],
            }
        ]
    )

    assert result["surface_kind"] == "mas_reviewer_repair_action_projection"
    assert result["schema_version"] == 1
    assert result["status"] == "complete"
    assert result["refs_only"] is True
    assert result["fail_open"] is True
    assert result["mainline_waits_for_repair_projection"] is False
    assert result["can_block_current_owner_action"] is False
    assert result["typed_blocker_candidates"] == []
    assert result["source_refs"] == {
        "external_skill_refs": [
            "nature-skills@1cb9070:skills/nature-response",
            "nature-skills@1cb9070:skills/nature-reader",
            "nature-skills@1cb9070:skills/nature-reviewer",
        ],
        "mas_contract_refs": [
            "journal_response_pack",
            "paper_reader_grounding_pack",
        ],
    }
    assert result["authority_boundary"] == {
        "can_write_mas_truth": False,
        "can_mutate_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_close_quality_gate": False,
    }

    assert result["repair_action_candidates"] == [
        {
            "candidate_ref": "reviewer-repair:R1.1:add_evidence",
            "finding_id": "R1.1",
            "comment_ref": "review-ledger:R1.1",
            "comment_type": "unsupported_claim",
            "target_ref": "claim-map:primary-outcome",
            "severity": "major",
            "repair_action": "add_evidence",
            "original_action": "add_evidence",
            "required_refs": [
                "evidence-ledger:primary-table",
                "citation-ledger:primary-source",
            ],
            "missing_author_input_state": None,
            "appeal_like_case_route": None,
            "status": "complete",
            "typed_blocker_candidate_refs": [],
            "refs_only": True,
            "can_mutate_paper_body": False,
            "can_close_quality_gate": False,
        }
    ]


def test_unknown_and_missing_actions_emit_fail_open_blocker_candidates() -> None:
    result = build_reviewer_repair_action_projection(
        [
            {
                "finding_id": "R2.1",
                "comment_ref": "review-ledger:R2.1",
                "comment_type": "overclaim",
                "target_ref": "claim-map:secondary",
                "severity": "major",
                "repair_action": "rewrite_everything",
            },
            {
                "finding_id": "R2.2",
                "comment_ref": "",
                "comment_type": "missing_control",
                "target_ref": "method:control",
                "severity": "severe",
                "missing_author_input_state": "needed",
                "appeal_like_case_route": "human_decision_required",
            },
        ]
    )

    assert result["status"] == "typed_blocker_candidate"
    assert result["refs_only"] is True
    assert result["fail_open"] is True
    assert result["mainline_waits_for_repair_projection"] is False
    assert result["can_block_current_owner_action"] is False
    assert all(value is False for value in result["authority_boundary"].values())

    actions = {
        item["finding_id"]: item for item in result["repair_action_candidates"]
    }
    assert actions["R2.1"]["repair_action"] == "route_to_human"
    assert actions["R2.1"]["original_action"] == "rewrite_everything"
    assert actions["R2.1"]["status"] == "typed_blocker_candidate"
    assert actions["R2.2"]["repair_action"] == "route_to_human"
    assert actions["R2.2"]["status"] == "typed_blocker_candidate"

    blocker_reasons = {
        (item["finding_id"], item["reason"])
        for item in result["typed_blocker_candidates"]
    }
    assert ("R2.1", "unknown_repair_action") in blocker_reasons
    assert ("R2.2", "missing_required_reviewer_ref") in blocker_reasons
    assert ("R2.2", "missing_repair_action") in blocker_reasons
    assert ("R2.2", "invalid_reviewer_severity") in blocker_reasons
    assert ("R2.2", "author_input_needed") in blocker_reasons
    assert ("R2.2", "appeal_like_case_requires_human_route") in blocker_reasons

    unknown = [
        item
        for item in result["typed_blocker_candidates"]
        if item["reason"] == "unknown_repair_action"
    ][0]
    assert unknown["blocker_type"] == "journal_response_traceability_blocker"
    assert unknown["recommended_owner_action"] == "route_to_human"
    assert unknown["can_block_current_owner_action"] is False
    assert unknown["authority_boundary"] == result["authority_boundary"]


def test_empty_findings_are_complete_empty_projection_not_progress_claim() -> None:
    result = build_reviewer_repair_action_projection([])

    assert result["status"] == "complete"
    assert result["repair_action_candidates"] == []
    assert result["typed_blocker_candidates"] == []
    assert result["refs_only"] is True
    assert result["fail_open"] is True
    assert result["authority_boundary"]["can_close_quality_gate"] is False
