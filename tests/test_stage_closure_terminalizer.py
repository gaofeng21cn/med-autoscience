from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.controllers.stage_closure_terminalizer import (
    ALLOWED_OUTCOME_KINDS,
    classify_stage_closure_blockers,
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


def test_blocker_taxonomy_keeps_submission_authority_separate_from_mirror_sync() -> None:
    classes = classify_stage_closure_blockers(
        [
            "authority_snapshot_missing",
            "delivery_manifest_source_changed",
            "reviewer_first_concerns_unresolved",
        ]
    )

    assert classes["submission_authority"] == ["authority_snapshot_missing"]
    assert classes["mirror_sync"] == ["delivery_manifest_source_changed"]
    assert classes["quality_repairable"] == ["reviewer_first_concerns_unresolved"]
