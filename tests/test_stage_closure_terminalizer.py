from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.controllers.stage_closure_terminalizer import (
    classify_stage_closure_blockers,
    stage_closure_decision_missing,
    stage_closure_decision_projection,
    terminalize_stage_closure,
)


pytestmark = [pytest.mark.contract]
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_contract_declares_quality_projection_without_route_authority() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts" / "mas-stage-closure-terminalizer.json").read_text(
            encoding="utf-8"
        )
    )

    requirements = contract["decision_requirements"]
    assert contract["machine_boundary"]["role"] == "quality_debt_projection_only"
    assert requirements["must_emit_exactly_one_outcome"] is False
    assert requirements["must_fail_closed_when_no_semantic_delta_repeats"] is False
    assert requirements["route_selection_owner"] == "codex_cli"
    assert requirements["projection_can_select_stage_route"] is False
    assert requirements["quality_debt_blocks_stage_transition"] is False


@pytest.mark.parametrize(
    "blocker",
    [
        "reviewer_first_concerns_unresolved",
        "current_package_stale",
        "bundle_build_allowed_false",
        "accepted_submission_milestone_candidate",
        "unclassified_reviewer_shape_gap",
    ],
)
def test_non_authority_gaps_advance_with_quality_debt(blocker: str) -> None:
    decision = terminalize_stage_closure(
        study_id="progress-first-study",
        stage_id="review",
        work_unit_id="review-attempt",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [blocker],
        },
    )

    outcome = decision["outcome"]
    assert outcome["kind"] == "next_stage_transition"
    assert outcome["transition_kind"] == "completed_with_quality_debt"
    assert outcome["quality_debt"]["blocks_stage_transition"] is False
    assert outcome["next_owner"] == "codex_cli"
    assert decision["next_stage_may_start"] is True
    assert decision["authority_boundary"]["can_select_stage_route"] is False


def test_retry_budget_and_repeated_signature_never_block_progress() -> None:
    first = terminalize_stage_closure(
        study_id="progress-first-study",
        stage_id="analysis",
        work_unit_id="negative-result",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["claim_evidence_consistency_failed"],
        },
        repair_budget={"repair_budget_max": 2, "repair_attempt_count": 2},
    )
    repeated = terminalize_stage_closure(
        study_id="progress-first-study",
        stage_id="analysis",
        work_unit_id="negative-result",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["claim_evidence_consistency_failed"],
        },
        repair_budget={"repair_budget_max": 2, "repair_attempt_count": 2},
        previous_signature=first["decision_signature"],
    )

    assert repeated["repeated_without_semantic_delta"] is True
    assert repeated["outcome"]["kind"] == "next_stage_transition"
    assert repeated["outcome"]["transition_kind"] == "completed_with_quality_debt"
    assert repeated["next_stage_may_start"] is True


def test_negative_result_artifact_can_feed_any_declared_stage() -> None:
    decision = terminalize_stage_closure(
        study_id="hypothesis-study",
        stage_id="analysis",
        work_unit_id="negative-primary-result",
        semantic_delta={
            "paper_delta_refs": ["artifact:negative-result"],
            "failed_path_refs": ["artifact:failed-hypothesis-lineage"],
        },
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["reviewer_first_concerns_unresolved"],
        },
    )

    assert decision["outcome"]["next_action"] == (
        "select_any_declared_stage_with_quality_debt"
    )
    assert decision["outcome"]["next_owner"] == "codex_cli"


def test_only_real_hard_authority_boundary_can_stop_stage_transition() -> None:
    decision = terminalize_stage_closure(
        study_id="protected-study",
        stage_id="external-submission",
        work_unit_id="submit",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [
                "irreversible_external_submission_authorization_required"
            ],
        },
    )

    assert decision["outcome"]["kind"] == "typed_blocker"
    assert decision["outcome"]["blocker_type"] == "hard_authority_blocker"
    assert decision["next_stage_may_start"] is False


def test_zero_readable_output_is_the_only_non_authority_stop() -> None:
    decision = terminalize_stage_closure(
        study_id="empty-study",
        stage_id="analysis",
        work_unit_id="empty-attempt",
    )

    assert decision["outcome"]["kind"] == "typed_blocker"
    assert decision["outcome"]["blocker_type"] == "zero_readable_stage_output"


def test_clean_attempt_advances_without_claiming_readiness() -> None:
    decision = terminalize_stage_closure(
        study_id="clean-study",
        stage_id="analysis",
        work_unit_id="analysis-v1",
        semantic_delta={"paper_delta_refs": ["artifact:analysis-v1"]},
    )

    assert decision["outcome"]["transition_kind"] == "completed"
    assert decision["outcome"]["next_owner"] == "codex_cli"
    assert decision["outcome"]["can_submit"] is False


def test_missing_stage_closure_context_is_quality_debt_not_fail_closed() -> None:
    projection = stage_closure_decision_projection(
        readback={
            "consume_candidate_status": "route_back",
            "stage_terminal_decision": {
                "decision_kind": "route_back",
                "repair_budget": {"repair_attempt_count": 4},
            },
        }
    )

    assert projection["projection_status"] == (
        "quality_debt_stage_closure_context_missing"
    )
    assert projection["fail_closed"] is False
    assert projection["next_stage_may_start"] is True
    assert projection["route_selection_owner"] == "codex_cli"
    assert projection["outcome"]["kind"] == "next_stage_transition"
    assert stage_closure_decision_missing(projection) is False


def test_blocker_taxonomy_is_diagnostic_only() -> None:
    taxonomy = classify_stage_closure_blockers(
        [
            "claim_evidence_consistency_failed",
            "current_package_stale",
            "bundle_build_allowed_false",
            "credential_boundary",
            "unknown-shape",
        ]
    )

    assert taxonomy["quality_repairable"] == ["claim_evidence_consistency_failed"]
    assert taxonomy["mirror_sync"] == ["current_package_stale"]
    assert taxonomy["submission_authority"] == ["bundle_build_allowed_false"]
    assert taxonomy["hard_authority"] == ["credential_boundary"]
    assert taxonomy["unknown"] == ["unknown-shape"]
