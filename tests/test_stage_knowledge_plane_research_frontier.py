from __future__ import annotations

import json

from med_autoscience.controllers import stage_knowledge_plane


def test_research_frontier_board_is_stage_local_advisory_without_control_authority() -> None:
    board = stage_knowledge_plane.build_research_frontier_board(
        study_id="S1",
        stage="idea",
        packet={
            "active_candidates": [
                {
                    "candidate_id": "clinical-subtype-line",
                    "summary": "Clinical subtype line remains plausible.",
                    "evidence_refs": ["evidence:subtype-feasibility"],
                }
            ],
            "testing_candidates": [
                {
                    "candidate_id": "external-validation-line",
                    "negative_result_refs": ["result:weak-external-signal"],
                    "missing_evidence_refs": ["evidence:external-validation"],
                }
            ],
            "next_hypothesis_suggestion": "test clinical subtype stability before claim expansion",
        },
    )

    assert board["surface"] == "stage_research_frontier_board"
    assert board["summary"]["counts_by_status"]["active"] == 1
    assert board["summary"]["counts_by_status"]["testing"] == 1
    assert board["summary"]["next_hypothesis_suggestion"] == (
        "test clinical subtype stability before claim expansion"
    )
    boundary = board["authority_boundary"]
    assert boundary["can_authorize_stage_completion"] is False
    assert boundary["can_replace_next_action"] is False
    assert boundary["can_write_domain_truth"] is False
    assert boundary["can_authorize_quality_verdict"] is False
    assert board["rollback_target_policy"]["advisory_only"] is True
    assert board["rollback_target_policy"]["can_control_progress"] is False


def test_failed_frontier_paths_project_stop_loss_and_route_back_target(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"

    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "frontier-stop-loss",
            "source_refs": ["stage:decision:turn-1"],
            "failed_paths": [
                {
                    "write_id": "weak-endpoint-line",
                    "reason": "Endpoint evidence stayed thin after bounded checks.",
                    "negative_result_refs": ["result:endpoint-thin"],
                    "route_back_refs": ["route-back:decision-stop-loss"],
                    "route_impact": "stop_loss",
                    "stop_loss": True,
                }
            ],
            "claim_boundary_decisions": [
                {
                    "write_id": "claim-downgrade",
                    "decision": "claim_downgrade",
                    "route_back_refs": ["route-back:claim-boundary"],
                }
            ],
        },
    )

    summary = packet["research_frontier_board_summary"]
    refs_by_id = {ref["candidate_id"]: ref for ref in packet["research_frontier_board_refs"]}
    suggestions = {
        (item["candidate_id"], item["signal"]): item["suggested_target_stage"]
        for item in summary["rollback_target_suggestions"]
    }

    assert summary["counts_by_status"]["stop_loss"] == 1
    assert refs_by_id["weak-endpoint-line"]["status"] == "stop_loss"
    assert refs_by_id["weak-endpoint-line"]["negative_result_refs"] == ["result:endpoint-thin"]
    assert refs_by_id["weak-endpoint-line"]["route_back_refs"] == ["route-back:decision-stop-loss"]
    assert suggestions[("weak-endpoint-line", "stop_loss")] == "decision"
    assert suggestions[("claim-downgrade", "claim_downgrade")] == "decision"
    assert packet["opl_research_frontier_projection"]["body_included"] is False
    assert packet["opl_research_frontier_projection"]["authority_boundary"]["can_replace_next_action"] is False


def test_frontier_board_preserves_memory_writeback_refs_and_opl_gets_refs_only(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"
    packet = stage_knowledge_plane.normalize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "frontier-writeback",
            "source_refs": ["stage:decision:turn-1"],
            "reusable_lessons": [
                {
                    "write_id": "route-memory-lesson",
                    "scope": "workspace_reusable",
                    "route_family": "negative_result_stoploss",
                    "stage_applicability": ["decision"],
                    "lesson": "Stop-loss was appropriate after route evidence stayed weak.",
                }
            ],
        },
    )

    projection = packet["opl_research_frontier_projection"]

    assert packet["research_frontier_board_summary"]["memory_writeback_ref_count"] == 1
    assert projection["surface"] == "stage_research_frontier_board_opl_refs_projection"
    assert projection["display_role"] == "refs_and_summary_only"
    assert projection["body_included"] is False
    assert projection["memory_writeback_refs"] == [
        {
            "write_id": "route-memory-lesson",
            "route_family": "negative_result_stoploss",
            "stage_applicability": ["decision"],
            "status": "proposed",
            "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
        }
    ]
    rendered_projection = json.dumps(projection, ensure_ascii=False)
    assert "Stop-loss was appropriate" not in rendered_projection
    assert projection["authority_boundary"]["can_write_domain_truth"] is False
