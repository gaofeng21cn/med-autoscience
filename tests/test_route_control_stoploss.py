from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _base_inputs(**overrides: Any) -> dict[str, Any]:
    payload = {
        "current_route": "dpcc-003.primary-care-risk",
        "decision": "stop_loss",
        "evidence_state": "blocked",
        "stop_pressure": "high",
        "attempted_paths": ["main_analysis", "bounded_repair"],
        "failure_reasons": ["endpoint_semantics_unresolvable", "no_transportable_evidence_gain"],
        "continuation_cost": {"runtime_hours": 12, "review_cycles": 2},
        "evidence_gain_ceiling": "low",
        "alternative_routes": ["dpcc-004.guideline-gap"],
        "human_gate_question": None,
        "evidence_refs": [
            "paper/evidence_ledger.json#endpoint_semantics",
            "artifacts/publication_eval/latest.json#publishability",
        ],
    }
    payload.update(overrides)
    return payload


def test_weak_result_cannot_continue() -> None:
    module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")

    memo = module.build_route_control_stoploss_memo(
        **_base_inputs(decision="continue", evidence_state="weak", stop_pressure="none")
    )

    assert memo["requested_decision"] == "continue"
    assert memo["decision"] == "stop_loss"
    assert memo["decision_allowed"] is False
    assert memo["blocked"] is True
    assert memo["blockers"] == ["continue_blocked_by_weak_evidence"]
    assert memo["quality_claim_authorized"] is False


def test_blocked_continue_suggests_stop_loss_route_with_durable_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")

    memo = module.build_route_control_stoploss_memo(
        **_base_inputs(decision="continue", evidence_state="blocked", stop_pressure="high")
    )

    assert memo["requested_decision"] == "continue"
    assert memo["decision"] == "stop_loss"
    assert memo["decision_allowed"] is False
    assert memo["route_recommendation"]["decision"] == "stop_loss"
    assert memo["route_recommendation"]["recommended_route"] is None
    assert memo["controller_decision_suggestion"]["suggested_payload"]["decision_type"] == "stop_loss"
    assert memo["durable_refs"] == {
        "stop_loss_memo": "artifacts/medical_paper/stop_loss_memo.json",
        "controller_decision_suggestion": "artifacts/controller_decisions/latest.json",
        "publication_quality_authority": "artifacts/publication_eval/latest.json",
    }
    assert memo["materialization"]["stop_loss_memo_required"] is True


def test_stop_loss_memo_fields_complete(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")

    memo = module.materialize_route_control_stoploss_memo(root=tmp_path, **_base_inputs())

    path = tmp_path / "artifacts" / "medical_paper" / "stop_loss_memo.json"
    assert memo["materialized_paths"] == {"stop_loss_memo": str(path)}
    written = json.loads(path.read_text(encoding="utf-8"))
    assert written == memo["stop_loss_memo"]
    assert written["surface"] == "stop_loss_memo"
    assert written["current_route"] == "dpcc-003.primary-care-risk"
    assert written["decision"] == "stop_loss"
    assert written["evidence_state"] == "blocked"
    assert written["stop_pressure"] == "high"
    assert written["attempted_paths"] == ["main_analysis", "bounded_repair"]
    assert written["failure_reasons"] == ["endpoint_semantics_unresolvable", "no_transportable_evidence_gain"]
    assert written["continuation_cost"] == {"runtime_hours": 12, "review_cycles": 2}
    assert written["evidence_gain_ceiling"] == "low"
    assert written["evidence_refs"] == [
        "paper/evidence_ledger.json#endpoint_semantics",
        "artifacts/publication_eval/latest.json#publishability",
    ]
    assert written["controller_decision_suggestion"]["target_path"] == "artifacts/controller_decisions/latest.json"


def test_switch_line_exposes_alternative_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")

    memo = module.materialize_route_control_stoploss_memo(
        root=tmp_path,
        **_base_inputs(decision="switch_line", evidence_state="weak", stop_pressure="watch"),
    )

    assert memo["decision_allowed"] is True
    assert memo["route_recommendation"]["alternative_routes"] == ["dpcc-004.guideline-gap"]
    assert memo["route_recommendation"]["recommended_route"] == "dpcc-004.guideline-gap"
    assert memo["stop_loss_memo"]["alternative_routes"] == ["dpcc-004.guideline-gap"]
    assert (
        memo["controller_decision_suggestion"]["suggested_payload"]["route_target"]
        == "dpcc-004.guideline-gap"
    )


def test_human_gate_requires_question() -> None:
    module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")

    memo = module.build_route_control_stoploss_memo(
        **_base_inputs(decision="human_gate", evidence_state="blocked", human_gate_question=None)
    )

    assert memo["decision_allowed"] is False
    assert memo["blocked"] is True
    assert memo["blockers"] == ["human_gate_question_required"]


def test_quality_claim_authorized_false() -> None:
    module = importlib.import_module("med_autoscience.controllers.route_control_stoploss")

    memo = module.build_route_control_stoploss_memo(
        **_base_inputs(decision="bounded_repair", evidence_state="strong", stop_pressure="watch")
    )

    assert memo["quality_claim_authorized"] is False
    assert memo["authority"]["quality_claim_authorized"] is False
    assert memo["authority"]["can_authorize_publication_quality"] is False
    assert memo["route_recommendation"]["quality_claim_authorized"] is False
    assert memo["controller_decision_suggestion"]["suggested_payload"]["quality_claim_authorized"] is False
