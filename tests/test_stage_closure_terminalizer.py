from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.controllers.stage_closure_terminalizer import (
    ALLOWED_OUTCOME_KINDS,
    classify_stage_closure_blockers,
    stage_closure_decision_projection,
    terminalize_stage_closure,
)


pytestmark = [pytest.mark.contract]

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_contract_declares_four_terminal_outcomes_and_forbids_same_stage_loop() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts" / "mas-stage-closure-terminalizer.json").read_text(
            encoding="utf-8"
        )
    )

    assert set(contract["required_outcome_kinds"]) == ALLOWED_OUTCOME_KINDS
    assert contract["decision_requirements"]["must_emit_exactly_one_outcome"] is True
    assert (
        "continue_same_stage_without_semantic_delta"
        in contract["forbidden_terminal_interpretations"]
    )
    assert (
        contract["package_authority_split"]["current_package"]["requires_bundle_build_allowed"]
        is False
    )
    assert (
        contract["package_authority_split"]["submission_ready_package"][
            "requires_bundle_build_allowed"
        ]
        is True
    )


def test_current_package_mirror_stale_routes_to_mirror_sync_without_bundle_authority() -> None:
    decision = terminalize_stage_closure(
        study_id="003-dm-china-us-mortality-attribution",
        stage_id="publication_supervision",
        work_unit_id="submission_milestone_candidate::followthrough::followthrough-02",
        work_unit_fingerprint="dm003-followthrough",
        gate_replay={"gate_replay_status": "blocked"},
        delivery_readback={
            "freshness": "missing",
            "current_package_exists": False,
            "blocked_reason": "authority_snapshot_missing",
            "bundle_build_allowed": False,
        },
        repair_budget={"repair_budget_max": 3, "repair_attempt_count": 1},
    )

    outcome = decision["outcome"]
    assert outcome["kind"] == "next_stage_transition"
    assert outcome["transition_kind"] == "current_package_mirror_sync"
    assert outcome["package_kind"] == "current_package"
    assert outcome["can_submit"] is False
    assert outcome["requires_bundle_build_allowed"] is False
    assert "current_package_missing" in outcome["known_blockers"]
    assert "authority_snapshot_missing" in outcome["known_blockers"]
    assert (
        decision["authority_boundary"]["writes_current_package"] is False
    ), "terminalizer only decides; delivery sync owns the actual mirror write"


def test_quality_blockers_budget_exhausted_degrade_to_handoff_package() -> None:
    decision = terminalize_stage_closure(
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="publication_supervision",
        work_unit_id="analysis_claim_evidence_repair",
        work_unit_fingerprint="dm002-claim-evidence",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [
                "reviewer_first_concerns_unresolved",
                "claim_evidence_consistency_failed",
                "submission_hardening_incomplete",
            ],
        },
        delivery_readback={
            "freshness": "stale",
            "freshness_reason": "delivery_manifest_source_changed",
            "bundle_build_allowed": False,
        },
        repair_budget={
            "repair_budget_max": 3,
            "repair_attempt_count": 3,
        },
    )

    outcome = decision["outcome"]
    assert outcome["kind"] == "next_stage_transition"
    assert outcome["transition_kind"] == "degraded_handoff"
    assert outcome["package_kind"] == "degraded_handoff_package"
    assert outcome["can_submit"] is False
    assert outcome["requires_bundle_build_allowed"] is False
    assert decision["repair_budget"]["repair_budget_status"] == "exhausted"
    assert set(decision["blocker_taxonomy"]["quality_repairable"]) >= {
        "reviewer_first_concerns_unresolved",
        "claim_evidence_consistency_failed",
        "submission_hardening_incomplete",
    }


def test_same_signature_without_semantic_delta_terminalizes_to_typed_blocker() -> None:
    first = terminalize_stage_closure(
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="publication_supervision",
        work_unit_id="analysis_claim_evidence_repair",
        work_unit_fingerprint="same",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["claim_evidence_consistency_failed"],
        },
        repair_budget={"repair_budget_max": 3, "repair_attempt_count": 1},
    )
    second = terminalize_stage_closure(
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="publication_supervision",
        work_unit_id="analysis_claim_evidence_repair",
        work_unit_fingerprint="same",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["claim_evidence_consistency_failed"],
        },
        repair_budget={"repair_budget_max": 3, "repair_attempt_count": 1},
        previous_signature=first["decision_signature"],
    )

    assert second["repeated_without_semantic_delta"] is True
    assert second["outcome"]["kind"] == "typed_blocker"
    assert second["outcome"]["blocker_type"] == "same_signature_without_semantic_delta"


def test_route_back_checkpoint_blockers_do_not_become_unclassified() -> None:
    decision = terminalize_stage_closure(
        study_id="003-dm-china-us-mortality-attribution",
        stage_id="submission_milestone_candidate",
        work_unit_id="route-back-checkpoint",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [
                "accepted_submission_milestone_candidate",
                "paper_mission_stage_route_domain_gate_pending",
                "MAS mission executor consumed route-back/domain-gate evidence as a fresh paper-facing candidate and is continuing the PaperMission stage.",
            ],
        },
    )

    assert decision["blocker_taxonomy"]["unknown"] == []
    assert decision["blocker_taxonomy"]["route_back_checkpoint"] == [
        "accepted_submission_milestone_candidate",
        "paper_mission_stage_route_domain_gate_pending",
        "MAS mission executor consumed route-back/domain-gate evidence as a fresh paper-facing candidate and is continuing the PaperMission stage.",
    ]
    outcome = decision["outcome"]
    assert outcome["kind"] == "next_stage_transition"
    assert outcome["transition_kind"] == "route_back_candidate_checkpoint"
    assert outcome["next_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )


def test_repeated_route_back_checkpoint_stops_same_stage_redrive() -> None:
    first = terminalize_stage_closure(
        study_id="003-dm-china-us-mortality-attribution",
        stage_id="submission_milestone_candidate",
        work_unit_id="route-back-checkpoint",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [
                "accepted_submission_milestone_candidate",
                "paper_mission_stage_route_domain_gate_pending",
            ],
        },
    )
    second = terminalize_stage_closure(
        study_id="003-dm-china-us-mortality-attribution",
        stage_id="submission_milestone_candidate",
        work_unit_id="route-back-checkpoint",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": [
                "accepted_submission_milestone_candidate",
                "paper_mission_stage_route_domain_gate_pending",
            ],
        },
        previous_signature=first["decision_signature"],
    )

    assert second["repeated_without_semantic_delta"] is True
    outcome = second["outcome"]
    assert outcome["kind"] == "typed_blocker"
    assert outcome["blocker_type"] == "route_back_checkpoint_without_semantic_delta"
    assert outcome["next_action"] == "materialize_typed_blocker_or_route_redesign"


def test_route_back_checkpoint_budget_exhaustion_degrades_to_handoff() -> None:
    decision = terminalize_stage_closure(
        study_id="003-dm-china-us-mortality-attribution",
        stage_id="submission_milestone_candidate",
        work_unit_id="route-back-checkpoint",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["accepted_submission_milestone_candidate"],
        },
        repair_budget={"repair_budget_max": 2, "repair_attempt_count": 2},
    )

    outcome = decision["outcome"]
    assert outcome["kind"] == "next_stage_transition"
    assert outcome["transition_kind"] == "degraded_handoff"
    assert outcome["package_kind"] == "degraded_handoff_package"
    assert decision["repair_budget"]["repair_budget_status"] == "exhausted"


def test_closeout_observability_accepts_actual_stage_log_field_names() -> None:
    decision = terminalize_stage_closure(
        study_id="003-dm-china-us-mortality-attribution",
        stage_id="publication_supervision",
        work_unit_id="return_to_ai_reviewer_workflow",
        gate_replay={"gate_replay_status": "blocked"},
        opl_closeout={
            "status": "completed",
            "duration": {
                "started_at": "2026-06-28T23:30:00Z",
                "completed_at": "2026-06-28T23:40:00Z",
            },
            "token_usage": {"total_tokens": 1200},
            "cost": {
                "status": "missing",
                "reason": "provider attempt cost telemetry is not exposed",
            },
        },
    )

    assert "observability_gaps" not in decision


def test_closeout_observability_records_missing_reasons_without_unknown_gaps() -> None:
    decision = terminalize_stage_closure(
        study_id="002-dm-china-us-mortality-attribution",
        stage_id="submission_milestone_candidate",
        work_unit_id="followthrough-02",
        gate_replay={
            "gate_replay_status": "blocked",
            "gate_replay_blockers": ["accepted_submission_milestone_candidate"],
        },
        opl_closeout={"status": "waiting_for_opl_runtime_live_readback"},
    )

    assert "observability_gaps" not in decision
    closeout = decision["opl_closeout"]
    assert closeout["duration"]["missing_duration_reason"] == (
        "waiting_for_opl_runtime_live_readback::duration_not_recorded"
    )
    assert closeout["token_usage"]["missing_token_usage_reason"] == (
        "waiting_for_opl_runtime_live_readback::token_usage_not_recorded"
    )
    assert closeout["cost"]["missing_cost_reason"] == (
        "waiting_for_opl_runtime_live_readback::cost_not_recorded"
    )


def test_legacy_unclassified_checkpoint_decision_projects_as_route_back_checkpoint() -> None:
    projection = stage_closure_decision_projection(
        readback={
            "stage_closure_decision": {
                "surface_kind": "mas_stage_closure_decision",
                "outcome": {
                    "kind": "typed_blocker",
                    "blocker_type": "unclassified_stage_closure_blocker",
                    "next_action": "materialize_typed_blocker_or_route_redesign",
                },
                "known_blockers": [
                    "accepted_submission_milestone_candidate",
                    (
                        "MAS mission executor consumed route-back/domain-gate evidence "
                        "as a fresh paper-facing candidate and is continuing the "
                        "PaperMission stage."
                    ),
                    "paper_mission_stage_route_domain_gate_pending",
                ],
            }
        }
    )

    assert projection["outcome_kind"] == "next_stage_transition"
    assert projection["outcome"]["kind"] == "next_stage_transition"
    assert projection["outcome"]["transition_kind"] == "route_back_candidate_checkpoint"
    assert "blocker_type" not in projection["outcome"]


def test_blocker_taxonomy_keeps_submission_authority_separate_from_mirror_sync() -> None:
    classes = classify_stage_closure_blockers(
        [
            "authority_snapshot_missing",
            "delivery_manifest_source_changed",
            "reviewer_first_concerns_unresolved",
            "paper_mission_stage_route_domain_gate_pending",
        ]
    )

    assert classes["submission_authority"] == ["authority_snapshot_missing"]
    assert classes["mirror_sync"] == ["delivery_manifest_source_changed"]
    assert classes["quality_repairable"] == ["reviewer_first_concerns_unresolved"]
    assert classes["route_back_checkpoint"] == [
        "paper_mission_stage_route_domain_gate_pending"
    ]
