from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import route_control_stoploss


SCHEMA_VERSION = 1
CONTROLLER_DECISION_PATH = Path("artifacts/controller_decisions/latest.json")
ROUTE_DECISION_REHEARSAL_MEMO_PATH = Path("artifacts/medical_paper/route_decision_rehearsal_memo.json")

NEXT_ACTION_BY_ROUTE_CONTROL = {
    "continue": "enter_baseline",
    "route_back": "run_literature_scout",
    "bounded_repair": "enter_bounded_analysis",
    "stop_loss": "stop_loss",
    "switch_line": "switch_line",
    "human_gate": "human_gate",
}

REHEARSAL_CLASSES = (
    "weak-result",
    "blocked-statistics",
    "missing-external-validation",
)


def build_route_decision_rehearsal(
    *,
    study_root: Path,
    current_route: str,
    alternative_routes: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    route = _text(current_route)
    alternatives = _text_list(list(alternative_routes))
    refs = _text_list(list(evidence_refs)) or [
        "artifacts/publication_eval/latest.json#route_pressure",
        "paper/evidence_ledger.json#route_decision",
    ]
    cases = [
        _build_route_rehearsal_case(current_route=route, spec=spec, evidence_refs=refs)
        for spec in _route_rehearsal_specs(alternative_routes=alternatives)
    ]
    coverage = _decision_coverage(cases)
    decision_memo = {
        "surface": "route_decision_rehearsal_memo",
        "schema_version": SCHEMA_VERSION,
        "authority": dict(route_control_stoploss.AUTHORITY),
        "controller_decision_role": "route_recommendation_only",
        "controller_decision_write_authorized": False,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "study_root": str(root),
        "current_route": route,
        "rehearsal_classes": list(REHEARSAL_CLASSES),
        "allowed_decisions": list(route_control_stoploss.DECISIONS),
        "decision_coverage": coverage,
        "durable_refs": {
            "decision_memo": str(ROUTE_DECISION_REHEARSAL_MEMO_PATH),
            **dict(route_control_stoploss.DURABLE_REFS),
        },
        "cases": cases,
    }
    return {
        "surface": "route_decision_rehearsal",
        "schema_version": SCHEMA_VERSION,
        "study_root": str(root),
        "status": "ready" if all(coverage.values()) else "blocked",
        "current_route": route,
        "rehearsal_classes": list(REHEARSAL_CLASSES),
        "allowed_decisions": list(route_control_stoploss.DECISIONS),
        "decision_coverage": coverage,
        "cases": cases,
        "decision_memo": decision_memo,
        "controller_decision_role": "route_recommendation_only",
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "durable_refs": dict(decision_memo["durable_refs"]),
        "materialized_paths": {},
    }


def materialize_route_decision_rehearsal(
    *,
    study_root: Path,
    current_route: str,
    alternative_routes: Sequence[str] = (),
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    projection = build_route_decision_rehearsal(
        study_root=study_root,
        current_route=current_route,
        alternative_routes=alternative_routes,
        evidence_refs=evidence_refs,
    )
    path = Path(projection["study_root"]) / ROUTE_DECISION_REHEARSAL_MEMO_PATH
    _write_json(path, _mapping(projection.get("decision_memo")))
    result = dict(projection)
    result["materialized_paths"] = {"decision_memo": str(path)}
    return result


def _route_rehearsal_specs(*, alternative_routes: Sequence[str]) -> list[dict[str, Any]]:
    alternatives = list(alternative_routes)
    return [
        {
            "case_id": "blocked-statistics-clear-control",
            "rehearsal_class": "blocked-statistics",
            "requested_decision": "continue",
            "evidence_state": "strong",
            "stop_pressure": "none",
            "attempted_paths": ["statistical_discipline_recheck"],
            "failure_reasons": ["statistical_blockers_cleared"],
            "continuation_cost": "normal_controller_review",
            "evidence_gain_ceiling": "adequate",
            "alternative_routes": alternatives,
        },
        {
            "case_id": "blocked-statistics-repair",
            "rehearsal_class": "blocked-statistics",
            "requested_decision": "bounded_repair",
            "evidence_state": "strong",
            "stop_pressure": "watch",
            "attempted_paths": ["primary_analysis"],
            "failure_reasons": [
                "statistical_blocker:missing_precision_statement",
                "statistical_blocker:external_validation_waiver_missing",
            ],
            "continuation_cost": {"bounded_repair_cycles": 1},
            "evidence_gain_ceiling": "moderate_if_repaired",
            "alternative_routes": alternatives,
        },
        {
            "case_id": "missing-external-validation-scout",
            "rehearsal_class": "missing-external-validation",
            "requested_decision": "route_back",
            "evidence_state": "blocked",
            "stop_pressure": "watch",
            "attempted_paths": ["external_validation_check"],
            "failure_reasons": ["external_validation_evidence_missing"],
            "continuation_cost": {"scout_refresh_cycles": 1},
            "evidence_gain_ceiling": "unknown_until_external_validation_refresh",
            "alternative_routes": alternatives,
        },
        {
            "case_id": "missing-external-validation-human-gate",
            "rehearsal_class": "missing-external-validation",
            "requested_decision": "human_gate",
            "evidence_state": "blocked",
            "stop_pressure": "watch",
            "attempted_paths": ["external_validation_check", "bounded_repair"],
            "failure_reasons": ["external_validation_required_for_claim_boundary"],
            "continuation_cost": {"review_cycles": 1},
            "evidence_gain_ceiling": "requires_human_acceptance_of_claim_boundary",
            "alternative_routes": alternatives,
            "human_gate_question": "Can the route proceed without external validation evidence?",
        },
        {
            "case_id": "weak-result-switch-line",
            "rehearsal_class": "weak-result",
            "requested_decision": "switch_line",
            "evidence_state": "weak",
            "stop_pressure": "high",
            "attempted_paths": ["baseline", "bounded_analysis"],
            "failure_reasons": ["weak_result_low_transportable_evidence_gain"],
            "continuation_cost": {"review_cycles": 2},
            "evidence_gain_ceiling": "low",
            "alternative_routes": alternatives,
        },
        {
            "case_id": "weak-result-stop-loss",
            "rehearsal_class": "weak-result",
            "requested_decision": "continue",
            "evidence_state": "weak",
            "stop_pressure": "high",
            "attempted_paths": ["baseline", "bounded_analysis"],
            "failure_reasons": ["weak_result_no_route_forward"],
            "continuation_cost": {"review_cycles": 2},
            "evidence_gain_ceiling": "low",
            "alternative_routes": alternatives,
        },
    ]


def _build_route_rehearsal_case(
    *,
    current_route: str,
    spec: Mapping[str, Any],
    evidence_refs: Sequence[str],
) -> dict[str, Any]:
    memo = route_control_stoploss.build_route_control_stoploss_memo(
        current_route=current_route,
        decision=_text(spec.get("requested_decision")),
        evidence_state=_text(spec.get("evidence_state")),
        stop_pressure=_text(spec.get("stop_pressure")),
        attempted_paths=_text_list(spec.get("attempted_paths")),
        failure_reasons=_text_list(spec.get("failure_reasons")),
        continuation_cost=spec.get("continuation_cost"),
        evidence_gain_ceiling=spec.get("evidence_gain_ceiling"),
        alternative_routes=_text_list(spec.get("alternative_routes")),
        human_gate_question=_text(spec.get("human_gate_question")) or None,
        evidence_refs=evidence_refs,
    )
    decision = _text(memo.get("decision"))
    rehearsal_class = _text(spec.get("rehearsal_class"))
    guard = _weak_route_analysis_guard(rehearsal_class)
    analysis_continuation_allowed = guard is None and decision in {"continue", "bounded_repair"}
    case = {
        "case_id": _text(spec.get("case_id")),
        "rehearsal_class": rehearsal_class,
        "requested_decision": _text(memo.get("requested_decision")),
        "decision": decision,
        "next_action": NEXT_ACTION_BY_ROUTE_CONTROL.get(decision, "human_gate"),
        "analysis_continuation_allowed": analysis_continuation_allowed,
        "route_recommendation": dict(_mapping(memo.get("route_recommendation"))),
        "controller_decision": _rehearsal_controller_recommendation(
            current_route=current_route,
            case_id=_text(spec.get("case_id")),
            memo=memo,
        ),
        "route_control_memo": dict(memo),
    }
    if guard is not None:
        case["weak_route_analysis_guard"] = guard
    return case


def _rehearsal_controller_recommendation(
    *,
    current_route: str,
    case_id: str,
    memo: Mapping[str, Any],
) -> dict[str, Any]:
    route_recommendation = _mapping(memo.get("route_recommendation"))
    return {
        "surface": "controller_decision_rehearsal_recommendation",
        "schema_version": SCHEMA_VERSION,
        "role": "route_recommendation_only",
        "case_id": case_id,
        "target_path": str(CONTROLLER_DECISION_PATH),
        "write_authorized": False,
        "decision_type": _text(memo.get("decision")),
        "requested_decision": _text(memo.get("requested_decision")),
        "current_route": current_route,
        "route_target": route_recommendation.get("recommended_route"),
        "decision_allowed": bool(memo.get("decision_allowed")),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "blockers": list(memo.get("blockers") or []),
    }


def _weak_route_analysis_guard(rehearsal_class: str) -> dict[str, Any] | None:
    if rehearsal_class != "weak-result":
        return None
    return {
        "continue_blocked": True,
        "bounded_repair_blocked": True,
        "reason": "weak_result_cannot_continue_or_expand_analysis",
    }


def _decision_coverage(cases: Sequence[Mapping[str, Any]]) -> dict[str, bool]:
    seen = {_text(case.get("decision")) for case in cases}
    return {decision: decision in seen for decision in route_control_stoploss.DECISIONS}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            result.append(text)
    return result
