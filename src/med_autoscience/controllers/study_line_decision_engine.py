from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "study_line_decision_engine"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/study_line_decision.json")
CONTROLLER_DECISION_REF = "controller_decisions/latest.json"
_UNSET = object()

REQUIRED_DIMENSIONS = (
    "novelty",
    "clinical_relevance",
    "data_fit",
    "external_validation",
    "analysis_feasibility",
    "journal_fit",
    "risk_cost",
    "stop_threshold",
)

BENEFIT_DIMENSIONS = (
    "novelty",
    "clinical_relevance",
    "data_fit",
    "external_validation",
    "analysis_feasibility",
    "journal_fit",
)

ROUTE_COMPARISON_AXES = (
    "novelty",
    "clinical_relevance",
    "data_fit",
    "external_validation",
    "journal_fit",
    "cost_risk",
    "stop_threshold",
)

ALLOWED_ROUTE_DECISIONS = {
    "proceed_to_baseline",
    "return_to_scout",
    "switch_line",
    "human_gate",
}


def stable_study_line_decision_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _durable_evidence_refs(value: object) -> list[str]:
    refs = []
    for item in _list(value):
        ref = _text(item)
        if not ref:
            continue
        refs.append(ref)
    return refs


def _dimension_score(candidate_id: str, dimension: str, value: object) -> tuple[float | None, str]:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None, f"candidate_{candidate_id}_{dimension}_score_not_numeric"
    score = float(value)
    if score < 0 or score > 5:
        return None, f"candidate_{candidate_id}_{dimension}_score_out_of_range"
    return score, ""


def _candidate_id(candidate: Mapping[str, Any], index: int) -> str:
    return _text(candidate.get("line_id")) or _text(candidate.get("id")) or f"candidate_{index + 1}"


def _validate_candidate(candidate: Mapping[str, Any], index: int) -> tuple[dict[str, Any], list[dict[str, str]]]:
    candidate_id = _candidate_id(candidate, index)
    dimensions = _mapping(candidate.get("dimensions"))
    blockers: list[dict[str, str]] = []

    if not _text(candidate.get("line_id")) and not _text(candidate.get("id")):
        blockers.append({"candidate_id": candidate_id, "code": "candidate_missing_line_id"})

    evidence_refs = _durable_evidence_refs(candidate.get("evidence_refs"))
    if not evidence_refs:
        blockers.append({"candidate_id": candidate_id, "code": "candidate_missing_evidence_refs"})

    dimension_scores: dict[str, float] = {}
    for dimension in REQUIRED_DIMENSIONS:
        if dimension not in dimensions:
            blockers.append({"candidate_id": candidate_id, "code": f"candidate_missing_{dimension}"})
            continue
        value = dimensions.get(dimension)
        if dimension == "stop_threshold":
            if not _text(value):
                blockers.append({"candidate_id": candidate_id, "code": "candidate_missing_stop_threshold"})
            continue
        score, reason = _dimension_score(candidate_id, dimension, value)
        if reason:
            blockers.append({"candidate_id": candidate_id, "code": reason})
            continue
        assert score is not None
        dimension_scores[dimension] = score

    total_score = sum(dimension_scores.get(key, 0.0) for key in BENEFIT_DIMENSIONS) - dimension_scores.get(
        "risk_cost", 0.0
    )
    normalized = {
        "line_id": candidate_id,
        "title": _text(candidate.get("title")),
        "dimensions": {key: dimensions.get(key) for key in REQUIRED_DIMENSIONS if key in dimensions},
        "dimension_scores": dimension_scores,
        "total_score": total_score,
        "evidence_refs": evidence_refs,
        "status": "blocked" if blockers else "eligible",
        "blockers": blockers,
    }
    return normalized, blockers


def _rank_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        candidates,
        key=lambda item: (
            item["status"] == "eligible",
            item["total_score"],
            item["dimension_scores"].get("clinical_relevance", 0.0),
            item["dimension_scores"].get("data_fit", 0.0),
            item["line_id"],
        ),
        reverse=True,
    )


def _route_candidate_summary(
    *,
    candidate: Mapping[str, Any],
    route_decision: str,
    controller_decision_ref: str,
) -> dict[str, Any]:
    dimensions = _mapping(candidate.get("dimensions"))
    dimension_scores = _mapping(candidate.get("dimension_scores"))
    return {
        "line_id": _text(candidate.get("line_id")),
        "title": _text(candidate.get("title")),
        "status": _text(candidate.get("status")),
        "route_decision": route_decision,
        "controller_decision_ref": controller_decision_ref,
        "total_score": candidate.get("total_score"),
        "comparison_axes": list(ROUTE_COMPARISON_AXES),
        "dimensions": {key: dimensions.get(key) for key in REQUIRED_DIMENSIONS if key in dimensions},
        "cost_risk": dimensions.get("risk_cost"),
        "dimension_scores": {key: dimension_scores.get(key) for key in BENEFIT_DIMENSIONS + ("risk_cost",)},
        "stop_threshold": _text(dimensions.get("stop_threshold")),
        "evidence_refs": list(_durable_evidence_refs(candidate.get("evidence_refs"))),
        "blockers": list(candidate.get("blockers") or []),
    }


def _route_action(
    *,
    route_decision: str,
    controller_decision_ref: str,
    selected_line_id: str | None = None,
    alternative_line_ids: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "route_decision": route_decision,
        "controller_decision_ref": controller_decision_ref,
        "requires_controller_decision_write": True,
    }
    if selected_line_id:
        payload["selected_line_id"] = selected_line_id
    if alternative_line_ids is not None:
        payload["alternative_line_ids"] = list(alternative_line_ids)
    if route_decision == "return_to_scout":
        payload["route_target"] = "literature_scout"
    if route_decision == "human_gate":
        payload["requires_human_decision"] = True
    return payload


def _route_projection(
    *,
    ranked_candidates: list[dict[str, Any]],
    selected_line_id: str | None,
    route_decision: str,
    controller_decision_ref: str,
) -> dict[str, Any]:
    current_candidate = next(
        (candidate for candidate in ranked_candidates if _text(candidate.get("line_id")) == _text(selected_line_id)),
        None,
    )
    current_route = (
        _route_candidate_summary(
            candidate=current_candidate,
            route_decision=route_decision,
            controller_decision_ref=controller_decision_ref,
        )
        if current_candidate
        else None
    )
    alternatives = [
        _route_candidate_summary(
            candidate=candidate,
            route_decision="switch_line",
            controller_decision_ref=controller_decision_ref,
        )
        for candidate in ranked_candidates
        if _text(candidate.get("status")) == "eligible" and _text(candidate.get("line_id")) != _text(selected_line_id)
    ]
    alternative_line_ids = [_text(candidate.get("line_id")) for candidate in alternatives if _text(candidate.get("line_id"))]
    return {
        "current_route": current_route,
        "alternative_routes": alternatives,
        "route_back": _route_action(
            route_decision="return_to_scout",
            controller_decision_ref=controller_decision_ref,
        ),
        "switch_line": _route_action(
            route_decision="switch_line",
            controller_decision_ref=controller_decision_ref,
            alternative_line_ids=alternative_line_ids,
        ),
        "human_gate": _route_action(
            route_decision="human_gate",
            controller_decision_ref=controller_decision_ref,
            selected_line_id=selected_line_id,
        ),
    }


def summarize_study_line_decision(
    *,
    scorecard: Mapping[str, Any],
    route_decision: str | None = None,
    selected_line_id: object = _UNSET,
    controller_decision_ref: str | None = None,
) -> dict[str, Any]:
    ranked_candidates = [dict(candidate) for candidate in scorecard.get("ranking") or [] if isinstance(candidate, Mapping)]
    resolved_route_decision = _text(route_decision) or _text(scorecard.get("route_decision")) or "human_gate"
    if selected_line_id is _UNSET:
        resolved_selected_line_id = _text(scorecard.get("selected_line_id"))
    else:
        resolved_selected_line_id = _text(selected_line_id)
    resolved_ref = _text(controller_decision_ref) or _text(scorecard.get("controller_decision_ref")) or CONTROLLER_DECISION_REF
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": _text(scorecard.get("status")),
        "selected_line_id": resolved_selected_line_id or None,
        "route_decision": resolved_route_decision,
        "controller_decision_ref": resolved_ref,
        **_route_projection(
            ranked_candidates=ranked_candidates,
            selected_line_id=resolved_selected_line_id or None,
            route_decision=resolved_route_decision,
            controller_decision_ref=resolved_ref,
        ),
    }


def build_study_line_decision(
    *,
    study_root: Path,
    candidates: list[Mapping[str, Any]],
    route_decision: str | None = None,
    controller_decision_ref: str = CONTROLLER_DECISION_REF,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    blockers: list[dict[str, str]] = []
    if not candidates:
        blockers.append({"candidate_id": "", "code": "missing_candidates"})

    normalized_candidates: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates):
        normalized, candidate_blockers = _validate_candidate(candidate, index)
        normalized_candidates.append(normalized)
        blockers.extend(candidate_blockers)

    ranked_candidates = _rank_candidates(normalized_candidates)
    eligible_candidates = [candidate for candidate in ranked_candidates if candidate["status"] == "eligible"]

    if route_decision is not None and route_decision not in ALLOWED_ROUTE_DECISIONS:
        blockers.append({"candidate_id": "", "code": "unsupported_route_decision"})

    selected = eligible_candidates[0] if eligible_candidates and not blockers else None
    selected_line_id = selected["line_id"] if selected else None
    resolved_route_decision = route_decision or "proceed_to_baseline"
    if blockers:
        resolved_route_decision = "human_gate"

    route_projection = _route_projection(
        ranked_candidates=ranked_candidates,
        selected_line_id=selected_line_id,
        route_decision=resolved_route_decision,
        controller_decision_ref=controller_decision_ref,
    )
    discarded_lines = [
        {
            "line_id": candidate["line_id"],
            "total_score": candidate["total_score"],
            "status": candidate["status"],
            "blockers": candidate["blockers"],
        }
        for candidate in ranked_candidates
        if candidate["line_id"] != selected_line_id
    ]

    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(root),
        "status": "blocked" if blockers else "selected",
        "selected_line_id": selected_line_id,
        "discarded_lines": discarded_lines,
        "route_decision": resolved_route_decision,
        "controller_decision_ref": controller_decision_ref,
        "controller_decision_ref_suggestion": controller_decision_ref,
        **route_projection,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "ranking": ranked_candidates,
        "blockers": blockers,
        "artifact_path": str(stable_study_line_decision_path(study_root=root)),
    }


def materialize_study_line_decision(
    *,
    study_root: Path,
    candidates: list[Mapping[str, Any]],
    route_decision: str | None = None,
    controller_decision_ref: str = CONTROLLER_DECISION_REF,
) -> dict[str, Any]:
    payload = build_study_line_decision(
        study_root=study_root,
        candidates=candidates,
        route_decision=route_decision,
        controller_decision_ref=controller_decision_ref,
    )
    _write_json(stable_study_line_decision_path(study_root=study_root), payload)
    return payload
