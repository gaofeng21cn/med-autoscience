from __future__ import annotations

import json

import pytest

from med_autoscience.controllers import stage_knowledge_plane
from med_autoscience.paper_mission_transaction import (
    REQUIRED_PAPER_AUDIT_PACK_FAMILIES,
    build_paper_mission_transaction,
)


PACK_ROLLBACK_TARGETS = [
    "01-study_intake",
    "02-protocol_and_analysis_plan",
    "03-data_asset_and_cohort_build",
    "04-analysis_execution",
    "05-evidence_synthesis",
    "06-manuscript_authoring",
    "07-independent_review_and_revision",
    "08-publication_package_handoff",
]


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


def test_rollback_target_policy_uses_8_stage_pack_advisory_mapping() -> None:
    board = stage_knowledge_plane.build_research_frontier_board(
        study_id="S1",
        stage="review",
        packet={
            "failed_paths": [
                {"write_id": "stop-line", "route_impact": "stop_loss", "stop_loss": True},
                {"write_id": "scout-reset", "route_impact": "return_to_scout"},
                {"write_id": "switch-line", "route_impact": "switch_line"},
                {"write_id": "stage-retry", "failure_scope": "stage_local"},
            ],
            "testing_candidates": [
                {
                    "candidate_id": "missing-evidence-line",
                    "missing_evidence_refs": ["evidence:missing-subgroup"],
                }
            ],
            "claim_boundary_decisions": [{"write_id": "downgrade-claim", "decision": "claim_downgrade"}],
            "literature_gaps": ["gap:external-validation"],
        },
    )

    policy = board["rollback_target_policy"]
    target_set = {row["target_stage"] for row in policy["pack_advisory_mapping"]}
    suggestions = {(row["candidate_id"], row["signal"]): row for row in policy["suggested_targets"]}

    assert policy["pack_stage_set"] == PACK_ROLLBACK_TARGETS
    assert target_set == set(PACK_ROLLBACK_TARGETS)
    assert policy["advisory_only"] is True
    assert policy["can_control_progress"] is False
    assert suggestions[("stop-line", "stop_loss")]["suggested_target_stage"] == (
        "07-independent_review_and_revision"
    )
    assert suggestions[("downgrade-claim", "claim_downgrade")]["suggested_target_stage"] == "05-evidence_synthesis"
    assert suggestions[("missing-evidence-line", "missing_evidence")]["suggested_target_stage"] == "04-analysis_execution"
    assert suggestions[("scout-reset", "route_impact:return_to_scout")]["suggested_target_stage"] == "01-study_intake"
    assert suggestions[("switch-line", "route_impact:switch_line")]["suggested_target_stage"] == (
        "02-protocol_and_analysis_plan"
    )
    assert suggestions[("stage-retry", "failure_scope:stage_local")]["suggested_target_stage"] == (
        "07-independent_review_and_revision"
    )
    assert all(row["suggested_target_stage"] in PACK_ROLLBACK_TARGETS for row in policy["suggested_targets"])


def test_failure_scope_maps_to_specific_8_stage_rollback_target() -> None:
    failure_scopes = [
        ("clinical_question", "01-study_intake"),
        ("endpoint", "02-protocol_and_analysis_plan"),
        ("data_asset", "03-data_asset_and_cohort_build"),
        ("analysis_execution", "04-analysis_execution"),
        ("claim_evidence", "05-evidence_synthesis"),
        ("manuscript_claim", "06-manuscript_authoring"),
        ("reviewer_quality", "07-independent_review_and_revision"),
        ("artifact_authority", "08-publication_package_handoff"),
    ]
    board = stage_knowledge_plane.build_research_frontier_board(
        study_id="S1",
        stage="review",
        packet={
            "failed_paths": [
                {"write_id": scope, "failure_scope": scope}
                for scope, _target in failure_scopes
            ],
        },
    )

    suggestions = {
        (row["candidate_id"], row["signal"]): row["suggested_target_stage"]
        for row in board["rollback_target_policy"]["suggested_targets"]
    }

    for scope, target in failure_scopes:
        assert suggestions[(scope, f"failure_scope:{scope}")] == target


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
    assert suggestions[("weak-endpoint-line", "stop_loss")] == (
        "07-independent_review_and_revision"
    )
    assert suggestions[("claim-downgrade", "claim_downgrade")] == "05-evidence_synthesis"
    assert packet["opl_research_frontier_projection"]["body_included"] is False
    assert packet["opl_research_frontier_projection"]["authority_boundary"]["can_replace_next_action"] is False


def test_closeout_materializes_independent_research_frontier_board_artifact(tmp_path) -> None:
    study_root = tmp_path / "study"
    workspace_root = tmp_path / "workspace"

    packet = stage_knowledge_plane.materialize_stage_memory_closeout_packet(
        study_id="S1",
        stage="decision",
        study_root=study_root,
        workspace_root=workspace_root,
        closeout_payload={
            "idempotency_key": "frontier-artifact",
            "source_refs": ["stage:decision:turn-1"],
            "failed_paths": [{"write_id": "weak-endpoint-line", "stop_loss": True}],
        },
    )

    board_path = study_root / "artifacts" / "stage_outputs" / "decision" / "research_frontier_board.json"
    board = json.loads(board_path.read_text(encoding="utf-8"))

    assert packet["artifact_path"].endswith("artifacts/stage_knowledge/decision/closeouts/frontier-artifact.json")
    assert packet["research_frontier_board_artifact_path"] == str(board_path)
    assert board["surface"] == "stage_research_frontier_board"
    assert board["study_id"] == "S1"
    assert board["stage"] == "decision"
    assert board["rollback_target_policy"]["advisory_only"] is True
    assert board["rollback_target_policy"]["pack_stage_set"] == PACK_ROLLBACK_TARGETS
    assert board["authority_boundary"]["can_replace_next_action"] is False
    assert board["authority_boundary"]["can_write_domain_truth"] is False


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


def test_stage_closeout_can_adopt_frontier_target_into_opl_route_command() -> None:
    board = stage_knowledge_plane.build_research_frontier_board(
        study_id="S1",
        stage="05-evidence_synthesis",
        packet={
            "failed_paths": [
                {
                    "write_id": "cohort-variable-gap",
                    "failure_scope": "data_asset",
                    "reason": "The evidence gap belongs to cohort variable construction.",
                }
            ],
        },
    )

    decision = stage_knowledge_plane.adopt_frontier_route_back_terminal_decision(
        board=board,
        selected_target_stage="03-data_asset_and_cohort_build",
        candidate_id="cohort-variable-gap",
        signal="failure_scope:data_asset",
        repair_scope="rebuild cohort variables and rerun downstream evidence synthesis",
    )
    transaction = build_paper_mission_transaction(
        mission_id="paper-mission::S1::frontier-route-back",
        study_id="S1",
        stage_id="05-evidence_synthesis",
        stage_run_ref="opl-stage-run://S1/05-evidence_synthesis",
        terminal_decision=decision,
        artifact_delta_refs=[
            {
                "ref_id": "frontier-route-back-decision",
                "ref_kind": "stage_terminal_decision",
                "uri": decision["frontier_advisory_ref"],
            }
        ],
        paper_audit_pack_refs=_audit_pack_refs("frontier-route-back"),
        idempotency_basis="frontier-route-back",
    )

    assert decision["decision_kind"] == "route_back"
    assert decision["target_stage_id"] == "03-data_asset_and_cohort_build"
    assert decision["frontier_advisory_authority"] is False
    assert decision["stage_closeout_authority_required"] is True
    assert transaction["opl_route_command"]["command_kind"] == "route_back"
    assert transaction["opl_route_command"]["target"] == "03-data_asset_and_cohort_build"
    assert (
        transaction["opl_route_command"]["source_terminal_decision_ref"]
        == f"{transaction['transaction_id']}#stage_terminal_decision"
    )


def test_frontier_route_back_adoption_requires_observed_suggestion() -> None:
    board = stage_knowledge_plane.build_research_frontier_board(
        study_id="S1",
        stage="05-evidence_synthesis",
        packet={
            "failed_paths": [
                {
                    "write_id": "analysis-gap",
                    "failure_scope": "analysis_execution",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="observed rollback target suggestion"):
        stage_knowledge_plane.adopt_frontier_route_back_terminal_decision(
            board=board,
            selected_target_stage="03-data_asset_and_cohort_build",
            repair_scope="try a target that the stage did not select from the board",
        )


def _audit_pack_refs(label: str) -> dict[str, list[dict[str, str]]]:
    return {
        family: [
            {
                "ref_id": f"{family}::{label}",
                "ref_kind": family,
                "uri": f"test://{label}/{family}",
            }
        ]
        for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    }
