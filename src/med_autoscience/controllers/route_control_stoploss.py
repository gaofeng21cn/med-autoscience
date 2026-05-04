from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "route_control_stoploss"
STOP_LOSS_MEMO_PATH = Path("artifacts/medical_paper/stop_loss_memo.json")
CONTROLLER_DECISION_SUGGESTION_PATH = Path("artifacts/controller_decisions/latest.json")

DECISIONS: tuple[str, ...] = (
    "continue",
    "route_back",
    "bounded_repair",
    "stop_loss",
    "switch_line",
    "human_gate",
)
EVIDENCE_STATES = frozenset({"strong", "weak", "blocked"})
STOP_PRESSURES = frozenset({"none", "watch", "high"})
STOP_LOSS_MATERIALIZED_DECISIONS = frozenset({"stop_loss", "switch_line", "human_gate"})

AUTHORITY = {
    "owner": "MAS Route Control",
    "can_authorize_publication_quality": False,
    "quality_claim_authorized": False,
    "publication_authority_surface": "artifacts/publication_eval/latest.json",
    "controller_decision_role": "route_recommendation_only",
}

DURABLE_REFS = {
    "stop_loss_memo": str(STOP_LOSS_MEMO_PATH),
    "controller_decision_suggestion": str(CONTROLLER_DECISION_SUGGESTION_PATH),
    "publication_quality_authority": str(AUTHORITY["publication_authority_surface"]),
}

__all__ = [
    "AUTHORITY",
    "DECISIONS",
    "DURABLE_REFS",
    "STOP_LOSS_MEMO_PATH",
    "build_route_control_stoploss_memo",
    "materialize_route_control_stoploss_memo",
]


def build_route_control_stoploss_memo(
    *,
    current_route: str,
    decision: str,
    evidence_state: str,
    stop_pressure: str,
    attempted_paths: Sequence[str],
    failure_reasons: Sequence[str],
    continuation_cost: Any,
    evidence_gain_ceiling: Any,
    alternative_routes: Sequence[str],
    human_gate_question: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    normalized_route = _required_text(current_route, "current_route")
    normalized_decision = _required_choice(decision, "decision", DECISIONS)
    normalized_evidence_state = _required_choice(evidence_state, "evidence_state", EVIDENCE_STATES)
    normalized_stop_pressure = _required_choice(stop_pressure, "stop_pressure", STOP_PRESSURES)
    normalized_attempted_paths = _text_sequence(attempted_paths, "attempted_paths")
    normalized_failure_reasons = _text_sequence(failure_reasons, "failure_reasons")
    normalized_alternative_routes = _text_sequence(alternative_routes, "alternative_routes")
    normalized_evidence_refs = _text_sequence(evidence_refs, "evidence_refs")
    normalized_question = _optional_text(human_gate_question)

    blockers = _decision_blockers(
        decision=normalized_decision,
        evidence_state=normalized_evidence_state,
        stop_pressure=normalized_stop_pressure,
        alternative_routes=normalized_alternative_routes,
        human_gate_question=normalized_question,
    )
    decision_allowed = not blockers
    effective_decision = _effective_decision(
        requested_decision=normalized_decision,
        blockers=blockers,
    )

    memo = {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "authority": dict(AUTHORITY),
        "quality_claim_authorized": False,
        "current_route": normalized_route,
        "requested_decision": normalized_decision,
        "decision": effective_decision,
        "decision_allowed": decision_allowed,
        "blocked": not decision_allowed,
        "blockers": blockers,
        "durable_refs": dict(DURABLE_REFS),
        "route_control_inputs": {
            "evidence_state": normalized_evidence_state,
            "stop_pressure": normalized_stop_pressure,
            "attempted_paths": normalized_attempted_paths,
            "failure_reasons": normalized_failure_reasons,
            "continuation_cost": continuation_cost,
            "evidence_gain_ceiling": evidence_gain_ceiling,
            "alternative_routes": normalized_alternative_routes,
            "human_gate_question": normalized_question,
            "evidence_refs": normalized_evidence_refs,
        },
        "route_recommendation": _route_recommendation(
            current_route=normalized_route,
            decision=effective_decision,
            decision_allowed=decision_allowed,
            alternative_routes=normalized_alternative_routes,
        ),
        "controller_decision_suggestion": _controller_decision_suggestion(
            current_route=normalized_route,
            requested_decision=normalized_decision,
            decision=effective_decision,
            decision_allowed=decision_allowed,
            evidence_state=normalized_evidence_state,
            stop_pressure=normalized_stop_pressure,
            human_gate_question=normalized_question,
            alternative_routes=normalized_alternative_routes,
        ),
        "materialization": {
            "stop_loss_memo_required": effective_decision in STOP_LOSS_MATERIALIZED_DECISIONS,
            "stop_loss_memo_path": str(STOP_LOSS_MEMO_PATH),
            "controller_decision_suggestion_path": str(CONTROLLER_DECISION_SUGGESTION_PATH),
        },
    }
    if effective_decision in STOP_LOSS_MATERIALIZED_DECISIONS:
        memo["stop_loss_memo"] = _stop_loss_memo_payload(memo)
    return memo


def materialize_route_control_stoploss_memo(
    *,
    root: str | Path,
    current_route: str,
    decision: str,
    evidence_state: str,
    stop_pressure: str,
    attempted_paths: Sequence[str],
    failure_reasons: Sequence[str],
    continuation_cost: Any,
    evidence_gain_ceiling: Any,
    alternative_routes: Sequence[str],
    human_gate_question: str | None = None,
    evidence_refs: Sequence[str] = (),
) -> dict[str, Any]:
    memo = build_route_control_stoploss_memo(
        current_route=current_route,
        decision=decision,
        evidence_state=evidence_state,
        stop_pressure=stop_pressure,
        attempted_paths=attempted_paths,
        failure_reasons=failure_reasons,
        continuation_cost=continuation_cost,
        evidence_gain_ceiling=evidence_gain_ceiling,
        alternative_routes=alternative_routes,
        human_gate_question=human_gate_question,
        evidence_refs=evidence_refs,
    )
    materialized_paths: dict[str, str] = {}
    if memo["materialization"]["stop_loss_memo_required"]:
        path = Path(root) / STOP_LOSS_MEMO_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(memo["stop_loss_memo"], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        materialized_paths["stop_loss_memo"] = str(path)

    result = dict(memo)
    result["materialized_paths"] = materialized_paths
    return result


def _decision_blockers(
    *,
    decision: str,
    evidence_state: str,
    stop_pressure: str,
    alternative_routes: Sequence[str],
    human_gate_question: str | None,
) -> list[str]:
    blockers: list[str] = []
    if decision == "continue" and evidence_state in {"weak", "blocked"}:
        blockers.append(f"continue_blocked_by_{evidence_state}_evidence")
    if decision == "continue" and stop_pressure == "high":
        blockers.append("continue_blocked_by_high_stop_pressure")
    if decision == "switch_line" and not alternative_routes:
        blockers.append("switch_line_requires_alternative_route")
    if decision == "human_gate" and human_gate_question is None:
        blockers.append("human_gate_question_required")
    return blockers


def _effective_decision(*, requested_decision: str, blockers: Sequence[str]) -> str:
    if requested_decision == "continue" and blockers:
        return "stop_loss"
    return requested_decision


def _route_recommendation(
    *,
    current_route: str,
    decision: str,
    decision_allowed: bool,
    alternative_routes: Sequence[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "current_route": current_route,
        "decision": decision,
        "decision_allowed": decision_allowed,
        "quality_claim_authorized": False,
    }
    if decision == "switch_line":
        payload["alternative_routes"] = list(alternative_routes)
        payload["recommended_route"] = alternative_routes[0] if alternative_routes else None
    elif decision == "route_back":
        payload["recommended_route"] = current_route
    elif decision == "bounded_repair":
        payload["recommended_route"] = current_route
        payload["repair_scope"] = "bounded"
    elif decision == "stop_loss":
        payload["recommended_route"] = None
    elif decision == "human_gate":
        payload["recommended_route"] = None
    else:
        payload["recommended_route"] = current_route
    return payload


def _controller_decision_suggestion(
    *,
    current_route: str,
    requested_decision: str,
    decision: str,
    decision_allowed: bool,
    evidence_state: str,
    stop_pressure: str,
    human_gate_question: str | None,
    alternative_routes: Sequence[str],
) -> dict[str, Any]:
    suggestion = {
        "surface": "controller_decision_suggestion",
        "schema_version": SCHEMA_VERSION,
        "target_path": str(CONTROLLER_DECISION_SUGGESTION_PATH),
        "write_authorized": False,
        "suggested_payload": {
            "decision_type": decision,
            "requested_decision": requested_decision,
            "current_route": current_route,
            "decision_allowed": decision_allowed,
            "evidence_state": evidence_state,
            "stop_pressure": stop_pressure,
            "quality_claim_authorized": False,
        },
    }
    if decision == "switch_line":
        suggestion["suggested_payload"]["alternative_routes"] = list(alternative_routes)
        suggestion["suggested_payload"]["route_target"] = alternative_routes[0] if alternative_routes else None
    if decision == "human_gate":
        suggestion["suggested_payload"]["human_gate_question"] = human_gate_question
    return suggestion


def _stop_loss_memo_payload(memo: Mapping[str, Any]) -> dict[str, Any]:
    route_inputs = _mapping(memo.get("route_control_inputs"))
    return {
        "surface": "stop_loss_memo",
        "schema_version": SCHEMA_VERSION,
        "authority": dict(AUTHORITY),
        "quality_claim_authorized": False,
        "current_route": memo["current_route"],
        "decision": memo["decision"],
        "requested_decision": memo["requested_decision"],
        "decision_allowed": memo["decision_allowed"],
        "blockers": list(memo["blockers"]),
        "durable_refs": dict(memo["durable_refs"]),
        "evidence_state": route_inputs["evidence_state"],
        "stop_pressure": route_inputs["stop_pressure"],
        "attempted_paths": list(route_inputs["attempted_paths"]),
        "failure_reasons": list(route_inputs["failure_reasons"]),
        "continuation_cost": route_inputs["continuation_cost"],
        "evidence_gain_ceiling": route_inputs["evidence_gain_ceiling"],
        "alternative_routes": list(route_inputs["alternative_routes"]),
        "human_gate_question": route_inputs["human_gate_question"],
        "evidence_refs": list(route_inputs["evidence_refs"]),
        "controller_decision_suggestion": dict(memo["controller_decision_suggestion"]),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_choice(value: str, label: str, choices: Sequence[str] | frozenset[str]) -> str:
    text = _required_text(value, label)
    if text not in choices:
        allowed = ", ".join(sorted(choices))
        raise ValueError(f"{label} must be one of: {allowed}")
    return text


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be non-empty")
    return text


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_sequence(value: object, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} must be a list")
    normalized: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item or "").strip()
        if not text:
            raise ValueError(f"{label} entries must be non-empty strings")
        if text in seen:
            continue
        seen.add(text)
        normalized.append(text)
    return normalized
