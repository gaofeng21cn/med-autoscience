from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers import study_line_decision_engine
from med_autoscience.controllers import route_control_stoploss
from med_autoscience.controllers.route_decision_orchestrator_parts.executable_plan import (
    build_analysis_direction_decision,
)
from med_autoscience.controllers.route_decision_orchestrator_parts.rehearsal import (
    ROUTE_DECISION_REHEARSAL_MEMO_PATH,
    build_route_decision_rehearsal,
    materialize_route_decision_rehearsal,
)


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

CANDIDATE_PATH_DECISIONS = ("proceed", "refine", "pivot", "stop", "human_gate")
CANDIDATE_PATH_REQUIRED_FIELDS = ("question", "evidence_basis", "expected_artifact", "stop_rule")
ADVERSE_RESULT_ALIGNMENTS = frozenset({"weak", "contradictory", "blocked", "negative"})
NEXT_ACTION_BY_ROUTE_CONTROL = {
    "continue": "enter_baseline",
    "route_back": "run_literature_scout",
    "bounded_repair": "enter_bounded_analysis",
    "stop_loss": "stop_loss",
    "switch_line": "switch_line",
    "human_gate": "human_gate",
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


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
    route_control_decision: str,
    selected_line_id: str | None,
    blockers: Sequence[str],
    route_control_memo: Mapping[str, Any] | None = None,
    study_line_decision: Mapping[str, Any] | None = None,
    analysis_direction_decision: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stage_output_refs = _stage_output_refs_from_decisions(
        study_line_decision=study_line_decision,
        analysis_direction_decision=analysis_direction_decision,
    )
    stage_output_refs_present = bool(stage_output_refs)
    write_authorized = not blockers and route_decision != "human_gate" and stage_output_refs_present
    payload: dict[str, Any] = {
        "surface": "controller_decision",
        "schema_version": SCHEMA_VERSION,
        "decision_type": "study_line_route_decision",
        "mechanical_route_role": "route_router_and_materializer",
        "route_generation_owner": "stage_output",
        "can_generate_winning_path_without_stage_output": False,
        "requested_action": requested_action,
        "route_decision": route_decision,
        "route_control_decision": route_control_decision,
        "selected_line_id": selected_line_id,
        "route_target": selected_line_id,
        "write_authorized": write_authorized,
        "stage_output_refs": stage_output_refs,
        "stage_output_refs_present": stage_output_refs_present,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "study_root": str(study_root),
        "blockers": list(blockers),
    }
    line_decision = _mapping(study_line_decision)
    if line_decision:
        payload["study_line_decision"] = dict(line_decision)
    analysis_decision = _mapping(analysis_direction_decision)
    if analysis_decision:
        payload["analysis_direction_decision"] = dict(analysis_decision)
        payload["route_execution_plan"] = dict(analysis_decision)
    memo = _mapping(route_control_memo)
    if memo:
        payload["route_control_memo_ref"] = _text(
            _mapping(memo.get("materialized_paths")).get("stop_loss_memo")
        ) or str(route_control_stoploss.STOP_LOSS_MEMO_PATH)
        payload["route_control_summary"] = {
            "decision": _text(memo.get("decision")),
            "decision_allowed": bool(memo.get("decision_allowed")),
            "evidence_state": _text(_mapping(memo.get("route_control_inputs")).get("evidence_state")),
            "stop_pressure": _text(_mapping(memo.get("route_control_inputs")).get("stop_pressure")),
        }
        payload["route_control_durable_refs"] = dict(_mapping(memo.get("durable_refs")))
    return payload


def _candidate_by_id(candidates: list[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    indexed = {}
    for index, candidate in enumerate(candidates):
        candidate_id = _text(candidate.get("line_id")) or _text(candidate.get("id")) or f"candidate_{index + 1}"
        indexed[candidate_id] = candidate
    return indexed


def _evidence_basis(candidate: Mapping[str, Any]) -> list[str]:
    evidence_basis = [_text(item) for item in _list(candidate.get("evidence_basis")) if _text(item)]
    if evidence_basis:
        return evidence_basis
    return [_text(item) for item in _list(candidate.get("evidence_refs")) if _text(item)]


def _question(candidate: Mapping[str, Any]) -> str:
    explicit = _text(candidate.get("question"))
    if explicit:
        return explicit
    title = _text(candidate.get("title"))
    if title:
        return title
    line_id = _text(candidate.get("line_id")) or _text(candidate.get("id"))
    if line_id:
        return f"Can {line_id} answer the locked research question?"
    return ""


def _expected_artifact(candidate: Mapping[str, Any]) -> str:
    explicit = _text(candidate.get("expected_artifact"))
    if explicit:
        return explicit
    if _text(candidate.get("question")):
        return ""
    line_id = _text(candidate.get("line_id")) or _text(candidate.get("id"))
    if line_id:
        return f"artifacts/medical_paper/candidate_paths/{line_id}.json"
    return ""


def _stop_rule(candidate: Mapping[str, Any], ranked_candidate: Mapping[str, Any]) -> str:
    explicit = _text(candidate.get("stop_rule"))
    if explicit:
        return explicit
    dimensions = _mapping(candidate.get("dimensions"))
    return _text(dimensions.get("stop_threshold")) or _text(ranked_candidate.get("stop_rule"))


def _explicitly_blank(candidate: Mapping[str, Any], field: str) -> bool:
    return field in candidate and not _text(candidate.get(field))


def _candidate_path_required_blockers(
    *,
    candidates: list[Mapping[str, Any]],
    scorecard: Mapping[str, Any],
) -> list[str]:
    source_candidates = _candidate_by_id(candidates)
    blockers = []
    for ranked_candidate in scorecard.get("ranking") or []:
        if not isinstance(ranked_candidate, Mapping):
            continue
        candidate_id = _text(ranked_candidate.get("line_id"))
        source = source_candidates.get(candidate_id, {})
        resolved_fields = {
            "question": _question(source),
            "evidence_basis": _evidence_basis(source),
            "expected_artifact": _expected_artifact(source),
            "stop_rule": _stop_rule(source, ranked_candidate),
            "stage_output_refs": _stage_output_refs(source, ranked_candidate),
        }
        for field in CANDIDATE_PATH_REQUIRED_FIELDS:
            if _explicitly_blank(source, field) or not resolved_fields[field]:
                blockers.append(f"candidate_{candidate_id}_missing_{field}")
        if not resolved_fields["stage_output_refs"]:
            blockers.append(f"candidate_{candidate_id}_missing_stage_output_refs")
    return blockers


def _candidate_path_decision(
    *,
    route_decision: str,
    candidate_id: str,
    selected_line_id: str | None,
    candidate_status: str,
    blockers: Sequence[str],
    candidate: Mapping[str, Any],
) -> str:
    if route_decision == "human_gate" and candidate_id == selected_line_id:
        return "human_gate"
    if candidate_status == "blocked":
        return "stop"
    if route_decision == "switch_line" and candidate_id == selected_line_id:
        return "pivot"
    if route_decision == "proceed_to_baseline" and candidate_id == selected_line_id:
        return "proceed"
    if route_decision == "return_to_scout" and candidate_id == selected_line_id:
        return "refine"
    if _text(candidate.get("decision")) in CANDIDATE_PATH_DECISIONS:
        return _text(candidate.get("decision"))
    return "refine" if not blockers else "human_gate"


def _build_candidate_path_graph(
    *,
    scorecard: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
    route_decision: str,
    selected_line_id: str | None,
    controller_decision_ref: str,
    blockers: Sequence[str],
) -> dict[str, Any]:
    source_candidates = _candidate_by_id(candidates)
    graph_candidates = []
    for ranked_candidate in scorecard.get("ranking") or []:
        if not isinstance(ranked_candidate, Mapping):
            continue
        candidate_id = _text(ranked_candidate.get("line_id"))
        source = source_candidates.get(candidate_id, {})
        decision = _candidate_path_decision(
            route_decision=route_decision,
            candidate_id=candidate_id,
            selected_line_id=selected_line_id,
            candidate_status=_text(ranked_candidate.get("status")),
            blockers=blockers,
            candidate=source,
        )
        graph_candidates.append(
            {
                "candidate_id": candidate_id,
                "question": _question(source),
                "evidence_basis": _evidence_basis(source),
                "expected_artifact": _expected_artifact(source),
                "stop_rule": _stop_rule(source, ranked_candidate),
                "stage_output_refs": _stage_output_refs(source, ranked_candidate),
                "decision": decision,
                "controller_decision_ref": controller_decision_ref,
            }
        )

    graph_decision = "human_gate" if blockers else "stop"
    for candidate in graph_candidates:
        if candidate["candidate_id"] == selected_line_id:
            graph_decision = str(candidate["decision"])
            break

    return {
        "surface": "candidate_path_graph",
        "schema_version": SCHEMA_VERSION,
        "authority": "read_model_only",
        "replaces_controller_decision": False,
        "can_replace_controller_decision_latest": False,
        "can_replace_study_runtime_status": False,
        "replaces_study_truth": False,
        "can_replace_study_truth": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_publication_quality": False,
        "allowed_decisions": list(CANDIDATE_PATH_DECISIONS),
        "decision": graph_decision,
        "selected_candidate_id": selected_line_id,
        "controller_decision_ref": controller_decision_ref,
        "candidates": graph_candidates,
    }


def _claim_boundary_allows_pivot(candidates: list[Mapping[str, Any]], selected_line_id: str | None) -> bool:
    if not selected_line_id:
        return False
    candidate = _candidate_by_id(candidates).get(selected_line_id, {})
    change = _text(candidate.get("claim_boundary_change")) or _text(candidate.get("claim_boundary_delta"))
    return change in {"", "unchanged", "same", "within_boundary", "not_expanded"}


def _stage_output_refs(candidate: Mapping[str, Any], ranked_candidate: Mapping[str, Any] | None = None) -> list[str]:
    refs = _text_list(candidate.get("stage_output_refs"))
    if refs:
        return refs
    return _text_list(_mapping(ranked_candidate).get("stage_output_refs"))


def _stage_output_refs_from_decisions(
    *,
    study_line_decision: Mapping[str, Any] | None,
    analysis_direction_decision: Mapping[str, Any] | None,
) -> list[str]:
    refs: list[str] = []
    refs.extend(_text_list(_mapping(study_line_decision).get("stage_output_refs")))
    refs.extend(_text_list(_mapping(analysis_direction_decision).get("stage_output_refs")))
    return list(dict.fromkeys(refs))


def _route_control_decision(
    *,
    route_decision: str,
    route_signals: Mapping[str, Any],
) -> str:
    requested = _text(route_signals.get("requested_route_control_decision"))
    result_alignment = _result_alignment(route_signals)
    evidence_state = _effective_evidence_state(route_signals)
    stop_pressure = _text(route_signals.get("stop_pressure")) or "none"
    statistical_blockers = _text_list(route_signals.get("statistical_blockers"))
    alternative_routes = _text_list(route_signals.get("alternative_routes"))
    if requested and requested != "continue":
        return requested
    if requested == "continue" and result_alignment in ADVERSE_RESULT_ALIGNMENTS:
        if statistical_blockers and result_alignment in {"weak", "blocked"} and stop_pressure != "high":
            return "bounded_repair"
        return "switch_line" if alternative_routes else "stop_loss"
    if requested:
        return requested
    if statistical_blockers and result_alignment in {"weak", "blocked"} and stop_pressure != "high":
        return "bounded_repair"
    if result_alignment in {"negative", "contradictory"}:
        return "switch_line" if alternative_routes else "stop_loss"
    if evidence_state in {"weak", "blocked"} or stop_pressure == "high":
        return "switch_line" if alternative_routes else "stop_loss"
    if statistical_blockers:
        return "bounded_repair"
    if route_decision == "return_to_scout":
        return "route_back"
    if route_decision == "switch_line":
        return "switch_line"
    if route_decision == "human_gate":
        return "human_gate"
    return "continue"


def _route_decision_from_control(route_control_decision: str, route_decision: str) -> str:
    if route_control_decision == "route_back":
        return "return_to_scout"
    if route_control_decision == "stop_loss":
        return "return_to_scout"
    if route_control_decision == "switch_line":
        return "switch_line"
    if route_control_decision == "human_gate":
        return "human_gate"
    return route_decision


def _result_alignment(route_signals: Mapping[str, Any]) -> str:
    return _text(route_signals.get("result_alignment")).lower()


def _effective_evidence_state(route_signals: Mapping[str, Any]) -> str:
    result_alignment = _result_alignment(route_signals)
    if result_alignment in {"negative", "contradictory", "blocked"}:
        return "blocked"
    if result_alignment == "weak":
        return "weak"
    explicit = _text(route_signals.get("evidence_state")).lower()
    if explicit:
        return explicit
    return "strong"


def _route_control_memo(
    *,
    root: Path,
    current_route: str,
    route_control_decision: str,
    route_signals: Mapping[str, Any],
) -> dict[str, Any]:
    return route_control_stoploss.materialize_route_control_stoploss_memo(
        root=root,
        current_route=current_route,
        decision=route_control_decision,
        evidence_state=_effective_evidence_state(route_signals),
        stop_pressure=_text(route_signals.get("stop_pressure")) or "watch",
        attempted_paths=_text_list(route_signals.get("attempted_paths")) or ["route_decision_orchestrator"],
        failure_reasons=_route_failure_reasons(route_signals),
        continuation_cost=route_signals.get("continuation_cost") or "bounded_controller_review",
        evidence_gain_ceiling=route_signals.get("evidence_gain_ceiling") or "unknown",
        alternative_routes=_text_list(route_signals.get("alternative_routes")),
        human_gate_question=_text(route_signals.get("human_gate_question")) or None,
        evidence_refs=_text_list(route_signals.get("evidence_refs")),
        exploration_depth_review=_mapping(route_signals.get("exploration_depth_review")),
    )


def _route_failure_reasons(route_signals: Mapping[str, Any]) -> list[str]:
    reasons = _text_list(route_signals.get("failure_reasons"))
    reasons.extend(f"statistical_blocker:{item}" for item in _text_list(route_signals.get("statistical_blockers")))
    return reasons or ["route_control_signal_requires_decision"]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text:
            result.append(text)
    return result


def _initial_route_state(
    *,
    requested_action: str,
    readiness: Mapping[str, Any] | None,
) -> tuple[str, list[str], str]:
    route_decision = ACTION_TO_ROUTE_DECISION.get(requested_action, "human_gate")
    blockers: list[str] = []
    if route_decision == "human_gate":
        blockers.append("unsupported_requested_action")

    literature_blocker = _literature_blocker(_mapping(readiness))
    if literature_blocker:
        blockers.append(literature_blocker)
        route_decision = "return_to_scout"
    return route_decision, blockers, literature_blocker


def _scorecard_blockers(
    *,
    scorecard: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
) -> list[str]:
    blockers: list[str] = []
    for blocker in scorecard.get("blockers") or []:
        if isinstance(blocker, Mapping):
            code = _text(blocker.get("code"))
            if code:
                blockers.append(code)
    blockers.extend(_candidate_path_required_blockers(candidates=candidates, scorecard=scorecard))
    return blockers


def _selected_route_after_blockers(
    *,
    candidates: list[Mapping[str, Any]],
    scorecard: Mapping[str, Any],
    route_decision: str,
    alternative_line_id: str | None,
    literature_blocker: str,
    blockers: list[str],
) -> tuple[str, str | None]:
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
    elif route_decision == "switch_line" and not _claim_boundary_allows_pivot(candidates, selected_line_id):
        blockers.append("pivot_requires_unchanged_claim_boundary")
        route_decision = "human_gate"
    return route_decision, selected_line_id


def _route_control_projection(
    *,
    root: Path,
    route_decision: str,
    selected_line_id: str | None,
    route_signals: Mapping[str, Any] | None,
    blockers: list[str],
) -> dict[str, Any]:
    route_signals_payload = _mapping(route_signals)
    has_route_signals = bool(route_signals_payload)
    route_control_decision = _route_control_decision(
        route_decision=route_decision,
        route_signals=route_signals_payload,
    )
    projected_route_decision = _route_decision_from_control(route_control_decision, route_decision)
    projected_selected_line_id = selected_line_id
    if has_route_signals and route_control_decision == "switch_line":
        projected_selected_line_id = None

    route_control_memo = (
        _route_control_memo(
            root=root,
            current_route=projected_selected_line_id
            or _text(route_signals_payload.get("current_route"))
            or "unselected_route",
            route_control_decision=route_control_decision,
            route_signals=route_signals_payload,
        )
        if has_route_signals
        else {}
    )
    if route_control_memo and route_control_memo.get("decision_allowed") is False:
        blockers.extend(str(item) for item in route_control_memo.get("blockers") or [] if _text(item))
        route_control_decision = _text(route_control_memo.get("decision")) or route_control_decision
        projected_route_decision = _route_decision_from_control(route_control_decision, route_decision)
        if route_control_decision == "switch_line":
            projected_selected_line_id = None

    next_action = (
        NEXT_ACTION_BY_ROUTE_CONTROL.get(route_control_decision)
        if has_route_signals
        else None
    ) or NEXT_ACTION_BY_ROUTE.get(projected_route_decision, "human_gate")
    return {
        "route_decision": projected_route_decision,
        "route_control_decision": route_control_decision,
        "selected_line_id": projected_selected_line_id,
        "next_action": next_action,
        "route_control_memo": route_control_memo,
        "route_signals": route_signals_payload,
    }


def _analysis_direction_decision(
    *,
    route_signals: Mapping[str, Any],
    route_control_decision: str,
    controller_decision_ref: str,
) -> dict[str, Any]:
    return build_analysis_direction_decision(
        route_signals=route_signals,
        route_control_decision=route_control_decision,
        controller_decision_ref=controller_decision_ref,
        schema_version=SCHEMA_VERSION,
    )


def build_route_decision_orchestration(
    *,
    study_root: Path,
    candidates: list[Mapping[str, Any]],
    requested_action: str,
    readiness: Mapping[str, Any] | None = None,
    alternative_line_id: str | None = None,
    route_signals: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    action = _text(requested_action)
    route_decision, blockers, literature_blocker = _initial_route_state(
        requested_action=action,
        readiness=readiness,
    )
    scorecard = study_line_decision_engine.build_study_line_decision(
        study_root=root,
        candidates=candidates,
        route_decision=route_decision if route_decision != "human_gate" else None,
    )
    blockers.extend(_scorecard_blockers(scorecard=scorecard, candidates=candidates))
    if not _text_list(scorecard.get("stage_output_refs")):
        blockers.append("stage_output_refs_required_for_route_materialization")
    route_decision, selected_line_id = _selected_route_after_blockers(
        candidates=candidates,
        scorecard=scorecard,
        route_decision=route_decision,
        alternative_line_id=alternative_line_id,
        literature_blocker=literature_blocker,
        blockers=blockers,
    )
    route_control = _route_control_projection(
        root=root,
        route_decision=route_decision,
        selected_line_id=selected_line_id,
        route_signals=route_signals,
        blockers=blockers,
    )
    route_decision = str(route_control["route_decision"])
    route_control_decision = str(route_control["route_control_decision"])
    selected_line_id = route_control["selected_line_id"]
    next_action = str(route_control["next_action"])
    route_control_memo = _mapping(route_control["route_control_memo"])
    route_signals_payload = _mapping(route_control["route_signals"])

    controller_decision_ref = (root / CONTROLLER_DECISION_PATH).resolve()
    analysis_direction_decision = _analysis_direction_decision(
        route_signals=route_signals_payload,
        route_control_decision=route_control_decision,
        controller_decision_ref=str(controller_decision_ref),
    )
    study_line_decision = study_line_decision_engine.summarize_study_line_decision(
        scorecard=scorecard,
        route_decision=route_decision,
        selected_line_id=selected_line_id,
        controller_decision_ref=str(controller_decision_ref),
    )
    controller_decision = _controller_decision_payload(
        study_root=root,
        requested_action=action,
        route_decision=route_decision,
        route_control_decision=route_control_decision,
        selected_line_id=selected_line_id,
        blockers=blockers,
        route_control_memo=route_control_memo,
        study_line_decision=study_line_decision,
        analysis_direction_decision=analysis_direction_decision,
    )
    candidate_path_graph = _build_candidate_path_graph(
        scorecard=scorecard,
        candidates=candidates,
        route_decision=route_decision,
        selected_line_id=selected_line_id,
        controller_decision_ref=str(controller_decision_ref),
        blockers=blockers,
    )

    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(root),
        "mechanical_route_role": "route_router_and_materializer",
        "route_generation_owner": "stage_output",
        "can_generate_winning_path_without_stage_output": False,
        "status": "blocked" if blockers else "ready",
        "requested_action": action,
        "route_decision": route_decision,
        "route_control_decision": route_control_decision,
        "selected_line_id": selected_line_id,
        "next_action": next_action,
        "controller_decision_ref": str(controller_decision_ref),
        "controller_decision": controller_decision,
        "study_line_decision": study_line_decision,
        "analysis_direction_decision": analysis_direction_decision,
        "route_execution_plan": analysis_direction_decision,
        "candidate_path_graph": candidate_path_graph,
        "scorecard": dict(scorecard),
        "route_control_memo": route_control_memo,
        "route_signals": dict(route_signals_payload),
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
    route_signals: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    projection = build_route_decision_orchestration(
        study_root=study_root,
        candidates=candidates,
        requested_action=requested_action,
        readiness=readiness,
        alternative_line_id=alternative_line_id,
        route_signals=route_signals,
    )
    decision = _mapping(projection.get("controller_decision"))
    if decision.get("write_authorized") is True:
        _write_json(Path(projection["controller_decision_ref"]), decision)
    return projection
