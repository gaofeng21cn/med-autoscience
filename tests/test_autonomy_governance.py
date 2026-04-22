from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def test_direction_locked_bounded_analysis_is_autonomous_with_stable_scope() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="bounded_analysis",
        controller_action_types=["ensure_study_runtime_relaunch_stopped"],
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
        "controller_action_types": ["ensure_study_runtime_relaunch_stopped"],
        "decision_type": "bounded_analysis",
        "reason_code": "direction_locked_bounded_analysis_stays_autonomous",
    }


def test_runtime_recovery_after_direction_lock_stays_autonomous() -> None:
    module = importlib.import_module("med_autoscience.runtime.autonomy_governance")

    contract = module.build_autonomy_governance_contract(
        decision_type="relaunch_branch",
        controller_action_types=["ensure_study_runtime_relaunch_stopped"],
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
        controller_action_types=["ensure_study_runtime"],
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
        controller_action_types=["ensure_study_runtime"],
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
            controller_action_types=["ensure_study_runtime"],
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
        controller_action_types=["ensure_study_runtime"],
        route_target="write",
        requires_human_confirmation=True,
        direction_locked=False,
    )

    assert contract["lane_id"] == "direction_lock_required"
    assert contract["continuation_scope"] == "direction_lock"
    assert contract["human_gate_class"] == "direction_not_locked"
    assert contract["next_stage"] == "direction_lock"


def test_study_outer_loop_decision_artifact_carries_autonomy_governance_contract(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    outer_loop = importlib.import_module("med_autoscience.controllers.study_outer_loop")
    outer_loop_tests = importlib.import_module("tests.test_study_outer_loop")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_escalation_ref = outer_loop_tests._write_runtime_escalation_record(outer_loop, quest_root, study_root)
    charter_ref = outer_loop_tests._write_charter(study_root)
    publication_eval_ref = outer_loop_tests._write_publication_eval(study_root, quest_root)

    monkeypatch.setattr(
        outer_loop.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_escalation_ref": runtime_escalation_ref,
        },
    )
    monkeypatch.setattr(
        outer_loop.study_runtime_router,
        "ensure_study_runtime",
        lambda **_: {"decision": "relaunch_stopped", "reason": "quest_stopped_requires_explicit_rerun"},
    )

    result = outer_loop.study_outer_loop_tick(
        profile=profile,
        study_id="001-risk",
        charter_ref=charter_ref,
        publication_eval_ref=publication_eval_ref,
        decision_type="bounded_analysis",
        route_target="analysis-campaign",
        route_key_question="What narrow robustness check is still needed?",
        route_rationale="The study direction is locked and only one bounded check remains.",
        requires_human_confirmation=False,
        controller_actions=[
            {
                "action_type": "ensure_study_runtime_relaunch_stopped",
                "payload_ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
            }
        ],
        reason="Run the bounded supplementary analysis before the next gate pass.",
        source="test-source",
        recorded_at="2026-04-05T06:00:00+00:00",
    )

    payload = json.loads(Path(result["study_decision_ref"]["artifact_path"]).read_text(encoding="utf-8"))
    assert payload["autonomy_governance_contract"] == {
        "contract_kind": "study_autonomy_governance_contract",
        "lane_id": "bounded_analysis",
        "continuation_scope": "bounded_supplementary_analysis",
        "next_stage": "analysis-campaign",
        "human_gate_class": "none",
        "requires_human_confirmation": False,
        "controller_action_types": ["ensure_study_runtime_relaunch_stopped"],
        "decision_type": "bounded_analysis",
        "reason_code": "direction_locked_bounded_analysis_stays_autonomous",
    }
    assert payload["family_human_gates"] == []
