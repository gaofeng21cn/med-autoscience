from __future__ import annotations

import importlib


def test_publication_gate_recommends_stop_loss_for_circular_clinical_claim() -> None:
    module = importlib.import_module("med_autoscience.quality.publication_gate")

    closure = module.derive_quality_closure_truth(
        promotion_gate_payload={
            "current_required_action": "continue_write_stage",
            "stop_loss_pressure": "high",
        },
        route_repair_plan=None,
        quality_closure_basis={
            "clinical_significance": {
                "status": "blocked",
                "summary": "Knosp is already the clinical invasion frame; no clinical meaning remains.",
            },
            "evidence_strength": {
                "status": "blocked",
                "summary": "Endpoint/predictor circularity: Knosp already separates invasiveness perfectly.",
            },
            "novelty_positioning": {
                "status": "partial",
                "summary": "The negative boundary does not create meaningful novelty.",
            },
        },
    )

    assert closure == {
        "state": "stop_loss_recommended",
        "summary": "当前论文线的核心科学命题已被可发表性门控判定为不成立；继续工作会变成稿件包装，应主动止损停题。",
        "current_required_action": "stop_runtime",
        "route_target": "stop",
    }


def test_publication_gate_projects_stop_loss_execution_lane() -> None:
    module = importlib.import_module("med_autoscience.quality.publication_gate")

    lane = module.derive_quality_execution_lane(
        promotion_gate_payload={
            "current_required_action": "return_to_publishability_gate",
            "controller_stage_note": "Clinical value has collapsed; stop this paper line.",
        },
        route_repair_plan={
            "action_type": "stop_loss",
            "route_target": "stop",
            "route_key_question": "Is there any independent clinical claim left?",
            "route_rationale": "Knosp already answers the invasion question.",
        },
    )

    assert lane["lane_id"] == "stop_loss"
    assert lane["repair_mode"] == "stop_loss"
    assert lane["route_target"] == "stop"
    assert lane["route_key_question"] == "Is there any independent clinical claim left?"
    assert lane["why_now"] == "Knosp already answers the invasion question."
