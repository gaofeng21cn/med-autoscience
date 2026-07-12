from __future__ import annotations

import importlib


def test_budget_exhausted_decision_carries_forward_nonfatal_review_findings() -> None:
    module = importlib.import_module("med_autoscience.progress_first_quality_loop")

    decision = module.budget_exhausted_decision(
        study_id="002-dm-china-us-mortality-attribution",
        action_type="run_quality_repair_batch",
        work_unit_id="current_manuscript_prose_currentness_and_gate_replay_write_closeout",
        work_unit_fingerprint="fingerprint-002",
        blocker_reason="typed_closeout_packet_required",
        failure_count=3,
        max_automatic_failures=3,
    )

    assert decision["decision"] == "advance_with_carry_forward_risk"
    assert decision["severity"] == "carry_forward_advisory"
    assert decision["fatal"] is False
    assert decision["ordinary_progress_may_advance"] is True
    assert decision["readiness_claim_allowed"] is False
    assert "carry_forward_risk_receipt" in decision["next_allowed_outcomes"]
    receipt = decision["carry_forward_risk_receipt"]
    assert receipt["surface_kind"] == "mas_progress_first_carry_forward_risk_receipt"
    assert receipt["risk_owner"] == "MedAutoScience"
    assert receipt["authority_boundary"]["can_claim_submission_ready"] is False


def test_budget_exhausted_decision_blocks_fatal_evidence_or_authority_risk() -> None:
    module = importlib.import_module("med_autoscience.progress_first_quality_loop")

    decision = module.budget_exhausted_decision(
        study_id="002-dm-china-us-mortality-attribution",
        action_type="run_quality_repair_batch",
        work_unit_id="claim_evidence_repair",
        work_unit_fingerprint="fingerprint-fatal",
        blocker_reason="claim_loses_direct_evidence_support",
        failure_count=3,
        max_automatic_failures=3,
    )

    assert decision["decision"] == "block_for_fatal_risk"
    assert decision["severity"] == "fatal_blocker"
    assert decision["fatal"] is True
    assert decision["ordinary_progress_may_advance"] is False
    assert decision["carry_forward_risk_receipt"] is None
    assert decision["next_allowed_outcomes"] == [
        "single_typed_blocker",
        "human_or_operator_gate",
        "route_redesign",
    ]


def test_nonconsumable_redrive_budget_exhaustion_is_quality_debt_not_a_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_stage_attempt_receipt_consumption.nonconsumable_redrive_budget"
    )

    receipt = module.consumption(
        latest={
            "receipt_ref": "attempt.closeout.json",
            "execution_id": "attempt-1",
            "action_type": "run_quality_repair_batch",
            "reason": "manuscript_story_surface_delta_missing",
        },
        owner_route={
            "idempotency_key": "route-1",
            "route_epoch": "1",
            "source_fingerprint": "sha256:test",
        },
        repeat_count=3,
    )

    assert receipt["execution_status"] == "completed_with_quality_debt"
    assert receipt["next_stage_may_start"] is True
    assert receipt["quality_debt"]["blocks_stage_transition"] is False
    assert "typed_blocker" not in receipt
    assert "blocked_reason" not in receipt
