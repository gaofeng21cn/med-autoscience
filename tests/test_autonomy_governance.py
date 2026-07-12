from __future__ import annotations

import importlib
import pytest


def test_direction_locked_bounded_analysis_is_autonomous_with_stable_scope() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="bounded_analysis",
        controller_action_types=["request_opl_stage_attempt_relaunch"],
        route_target="analysis-campaign",
        requires_human_confirmation=False,
        direction_locked=True,
    )

    assert contract == {
        "contract_kind": "study_autonomy_governance_contract",
        "lane_id": "bounded_analysis",
        "continuation_scope": "bounded_supplementary_analysis",
        "next_stage": "analysis-campaign",
        "human_gate_class": "none",
        "requires_human_confirmation": False,
        "controller_action_types": ["request_opl_stage_attempt_relaunch"],
        "decision_type": "bounded_analysis",
        "reason_code": "direction_locked_bounded_analysis_stays_autonomous",
    }


def test_runtime_recovery_after_direction_lock_stays_autonomous() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="relaunch_branch",
        controller_action_types=["request_opl_stage_attempt_relaunch"],
        requires_human_confirmation=False,
        direction_locked=True,
    )

    assert contract["lane_id"] == "runtime_recovery"
    assert contract["continuation_scope"] == "same_study_runtime_recovery"
    assert contract["next_stage"] == "runtime_recovery"
    assert contract["human_gate_class"] == "none"
    assert contract["reason_code"] == "direction_locked_runtime_recovery_stays_autonomous"


def test_final_audit_is_a_narrow_human_gate_class() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="promote_to_delivery",
        controller_action_types=["request_opl_stage_attempt"],
        route_target="submission",
        requires_human_confirmation=True,
        direction_locked=True,
    )

    assert contract["lane_id"] == "final_submission_audit"
    assert contract["continuation_scope"] == "pre_submission_final_audit"
    assert contract["next_stage"] == "submission"
    assert contract["human_gate_class"] == "final_submission_audit"
    assert contract["reason_code"] == "final_submission_audit_requires_human_gate"


def test_explicit_human_override_can_gate_an_otherwise_autonomous_decision() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="continue_same_line",
        controller_action_types=["request_opl_stage_attempt"],
        requires_human_confirmation=True,
        direction_locked=True,
        explicit_human_override=True,
    )

    assert contract["lane_id"] == "human_override"
    assert contract["continuation_scope"] == "explicit_human_override"
    assert contract["human_gate_class"] == "explicit_human_override"
    assert contract["reason_code"] == "explicit_human_override_requires_human_gate"


def test_autonomous_scientific_decisions_cannot_claim_human_gate() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    with pytest.raises(ValueError, match="autonomous MAS decision cannot require human confirmation"):
        module.build_autonomy_governance_contract(
            decision_type="continue_same_line",
            controller_action_types=["request_opl_stage_attempt"],
            route_target="write",
            requires_human_confirmation=True,
            direction_locked=True,
        )


def test_controller_owned_stop_contract_does_not_create_human_gate() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="stop_loss",
        controller_action_types=["stop_runtime"],
        requires_human_confirmation=False,
        direction_locked=True,
    )

    assert contract["lane_id"] == "controller_stop"
    assert contract["continuation_scope"] == "runtime_stop_contract"
    assert contract["next_stage"] == "stopped"
    assert contract["human_gate_class"] == "none"
    assert contract["reason_code"] == "controller_stop_contract_does_not_create_human_gate"


def test_direction_unlocked_decision_requires_human_gate_class() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="continue_same_line",
        controller_action_types=["request_opl_stage_attempt"],
        route_target="write",
        requires_human_confirmation=True,
        direction_locked=False,
    )

    assert contract["lane_id"] == "direction_lock_required"
    assert contract["continuation_scope"] == "direction_lock"
    assert contract["human_gate_class"] == "direction_not_locked"
    assert contract["next_stage"] == "direction_lock"
