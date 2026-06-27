from __future__ import annotations

import pytest


def test_controller_human_gate_policy_allows_only_major_boundaries() -> None:
    from med_autoscience.human_gate_policy import controller_human_gate_policy

    stop_loss = controller_human_gate_policy(
        decision_type="stop_loss",
        controller_action_types=["stop_runtime"],
    )
    reroute = controller_human_gate_policy(
        decision_type="reroute_study",
        controller_action_types=["request_opl_stage_attempt"],
    )
    final_audit = controller_human_gate_policy(
        decision_type="promote_to_delivery",
        controller_action_types=["request_opl_stage_attempt"],
    )

    assert stop_loss.allowed is True
    assert stop_loss.category == "stop_loss"
    assert reroute.allowed is True
    assert reroute.category == "major_direction_pivot"
    assert final_audit.allowed is True
    assert final_audit.category == "final_submission_audit"
    assert stop_loss.transport_boundary["opl_role"] == (
        "question_required_receipt_and_resume_token_transport_only"
    )
    assert stop_loss.transport_boundary["question_ref_required"] is True
    assert stop_loss.transport_boundary["required_receipt_ref_required"] is True
    assert stop_loss.transport_boundary["resume_path_ref_required"] is True
    assert stop_loss.accepted_owner_answer_shapes == (
        "human_gate_ref",
        "route_back_evidence_ref",
        "typed_blocker_ref",
    )
    assert stop_loss.transport_boundary["accepted_owner_answer_shapes"] == [
        "human_gate_ref",
        "route_back_evidence_ref",
        "typed_blocker_ref",
    ]
    assert stop_loss.transport_boundary["opl_can_approve_human_gate"] is False
    assert stop_loss.transport_boundary["opl_can_block_without_mas_owner_boundary"] is False
    assert stop_loss.transport_boundary["can_write_human_gate"] is False
    assert stop_loss.transport_boundary["can_authorize_provider_admission"] is False
    assert stop_loss.to_dict()["accepted_owner_answer_shapes"] == [
        "human_gate_ref",
        "route_back_evidence_ref",
        "typed_blocker_ref",
    ]


def test_controller_human_gate_policy_keeps_ordinary_research_decisions_autonomous() -> None:
    from med_autoscience.human_gate_policy import controller_human_gate_policy

    continue_line = controller_human_gate_policy(
        decision_type="continue_same_line",
        controller_action_types=["request_opl_stage_attempt"],
    )
    bounded_analysis = controller_human_gate_policy(
        decision_type="bounded_analysis",
        controller_action_types=["request_opl_stage_attempt"],
    )
    relaunch = controller_human_gate_policy(
        decision_type="relaunch_branch",
        controller_action_types=["request_opl_stage_attempt_relaunch"],
    )

    assert continue_line.allowed is False
    assert continue_line.category == "mas_autonomous_scientific_decision"
    assert continue_line.accepted_owner_answer_shapes == ()
    assert bounded_analysis.allowed is False
    assert bounded_analysis.category == "mas_autonomous_scientific_decision"
    assert relaunch.allowed is False
    assert relaunch.category == "mas_autonomous_runtime_recovery"


def test_controller_human_gate_policy_keeps_route_back_same_line_autonomous() -> None:
    from med_autoscience.human_gate_policy import controller_human_gate_policy

    route_back = controller_human_gate_policy(
        decision_type="route_back_same_line",
        controller_action_types=["request_opl_stage_attempt"],
    )

    assert route_back.allowed is False
    assert route_back.category == "mas_autonomous_scientific_decision"
    assert route_back.reason_code == "mas_autonomous_decision_must_not_create_human_gate"
    assert route_back.transport_boundary["ordinary_annotation_blocks_auto_progress"] is False


def test_require_controller_human_gate_allowed_rejects_autonomous_decisions() -> None:
    from med_autoscience.human_gate_policy import require_controller_human_gate_allowed

    with pytest.raises(ValueError, match="major direction pivots"):
        require_controller_human_gate_allowed(
            decision_type="continue_same_line",
            controller_action_types=["request_opl_stage_attempt"],
        )
