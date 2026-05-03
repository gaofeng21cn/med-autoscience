from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers import study_line_decision_engine


SCHEMA_VERSION = 1
SURFACE = "route_decision_orchestrator"
CONTROLLER_DECISION_PATH = Path("artifacts/controller_decisions/latest.json")

ACTION_TO_ROUTE_DECISION = {
    "run_literature_scout": "return_to_scout",
    "score_study_lines": "return_to_scout",
    "select_line": "proceed_to_baseline",
    "route_back_to_scout": "return_to_scout",
    "switch_line": "switch_line",
    "enter_baseline": "proceed_to_baseline",
}

NEXT_ACTION_BY_ROUTE = {
    "proceed_to_baseline": "enter_baseline",
    "return_to_scout": "run_literature_scout",
    "switch_line": "enter_baseline",
    "human_gate": "human_gate",
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _literature_blocker(readiness: Mapping[str, Any]) -> str:
    status = _text(readiness.get("literature_status"))
    if status and status not in {"ready", "present"}:
        reason = _text(readiness.get("literature_missing_reason")) or status
        return f"literature_scout_blocked:{reason}"
    return ""


def _eligible_line_ids(scorecard: Mapping[str, Any]) -> set[str]:
    return {
        _text(item.get("line_id"))
        for item in scorecard.get("ranking") or []
        if isinstance(item, Mapping) and _text(item.get("status")) == "eligible" and _text(item.get("line_id"))
    }


def _selected_line_id(
    *,
    scorecard: Mapping[str, Any],
    route_decision: str,
    alternative_line_id: str | None,
    blockers: list[str],
) -> str | None:
    if route_decision == "switch_line":
        alternative = _text(alternative_line_id)
        if not alternative:
            blockers.append("switch_line_requires_alternative_route")
            return None
        if alternative not in _eligible_line_ids(scorecard):
            blockers.append("switch_line_alternative_not_eligible")
            return None
        return alternative
    selected = scorecard.get("selected_line_id")
    return _text(selected) or None


def _controller_decision_payload(
    *,
    study_root: Path,
    requested_action: str,
    route_decision: str,
    selected_line_id: str | None,
    blockers: Sequence[str],
) -> dict[str, Any]:
    write_authorized = not blockers and route_decision != "human_gate"
    payload: dict[str, Any] = {
        "surface": "controller_decision",
        "schema_version": SCHEMA_VERSION,
        "decision_type": "study_line_route_decision",
        "requested_action": requested_action,
        "route_decision": route_decision,
        "selected_line_id": selected_line_id,
        "route_target": selected_line_id,
        "write_authorized": write_authorized,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "study_root": str(study_root),
        "blockers": list(blockers),
    }
    return payload


def build_route_decision_orchestration(
    *,
    study_root: Path,
    candidates: list[Mapping[str, Any]],
    requested_action: str,
    readiness: Mapping[str, Any] | None = None,
    alternative_line_id: str | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    action = _text(requested_action)
    route_decision = ACTION_TO_ROUTE_DECISION.get(action, "human_gate")
    blockers: list[str] = []
    if route_decision == "human_gate":
        blockers.append("unsupported_requested_action")

    readiness_payload = _mapping(readiness)
    literature_blocker = _literature_blocker(readiness_payload)
    if literature_blocker:
        blockers.append(literature_blocker)
        route_decision = "return_to_scout"

    scorecard = study_line_decision_engine.build_study_line_decision(
        study_root=root,
        candidates=candidates,
        route_decision=route_decision if route_decision != "human_gate" else None,
    )
    for blocker in scorecard.get("blockers") or []:
        if isinstance(blocker, Mapping):
            code = _text(blocker.get("code"))
            if code:
                blockers.append(code)

    selected_line_id = _selected_line_id(
        scorecard=scorecard,
        route_decision=route_decision,
        alternative_line_id=alternative_line_id,
        blockers=blockers,
    )
    if blockers and route_decision == "switch_line":
        route_decision = "human_gate"
    elif blockers and not literature_blocker:
        route_decision = "human_gate"

    controller_decision_ref = (root / CONTROLLER_DECISION_PATH).resolve()
    controller_decision = _controller_decision_payload(
        study_root=root,
        requested_action=action,
        route_decision=route_decision,
        selected_line_id=selected_line_id,
        blockers=blockers,
    )

    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(root),
        "status": "blocked" if blockers else "ready",
        "requested_action": action,
        "route_decision": route_decision,
        "selected_line_id": selected_line_id,
        "next_action": NEXT_ACTION_BY_ROUTE.get(route_decision, "human_gate"),
        "controller_decision_ref": str(controller_decision_ref),
        "controller_decision": controller_decision,
        "scorecard": dict(scorecard),
        "blockers": blockers,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def materialize_route_decision_orchestration(
    *,
    study_root: Path,
    candidates: list[Mapping[str, Any]],
    requested_action: str,
    readiness: Mapping[str, Any] | None = None,
    alternative_line_id: str | None = None,
) -> dict[str, Any]:
    projection = build_route_decision_orchestration(
        study_root=study_root,
        candidates=candidates,
        requested_action=requested_action,
        readiness=readiness,
        alternative_line_id=alternative_line_id,
    )
    decision = _mapping(projection.get("controller_decision"))
    if decision.get("write_authorized") is True:
        _write_json(Path(projection["controller_decision_ref"]), decision)
    return projection
