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


def test_budget_exhausted_scientific_evidence_gap_routes_back_without_blocking_progress() -> None:
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

    assert decision["decision"] == "advance_with_carry_forward_risk"
    assert decision["severity"] == "carry_forward_advisory"
    assert decision["fatal"] is False
    assert decision["ordinary_progress_may_advance"] is True
    assert decision["carry_forward_risk_receipt"] is not None


def test_budget_exhausted_real_authority_boundary_remains_a_hard_stop() -> None:
    module = importlib.import_module("med_autoscience.progress_first_quality_loop")

    decision = module.budget_exhausted_decision(
        study_id="002-dm-china-us-mortality-attribution",
        action_type="submission_apply",
        work_unit_id="irreversible_submission",
        work_unit_fingerprint="fingerprint-authority",
        blocker_reason="irreversible_action_requires_authorization",
        failure_count=1,
        max_automatic_failures=1,
    )

    assert decision["decision"] == "block_for_fatal_risk"
    assert decision["fatal"] is True
    assert decision["ordinary_progress_may_advance"] is False


def test_nonconsumable_output_is_immediately_a_quality_debt_diagnostic() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_stage_attempt_receipt_consumption.progress_diagnostic"
    )

    receipt = module.consumption(
        diagnostic={
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
    )

    assert receipt["execution_status"] == "completed_with_quality_debt"
    assert receipt["next_stage_may_start"] is True
    assert receipt["progress_diagnostic"]["consumable_by_next_stage"] is True
    assert receipt["quality_debt"]["blocks_stage_transition"] is False
    assert "typed_blocker" not in receipt
    assert "blocked_reason" not in receipt
