from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "study_line_decision_engine"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/study_line_decision.json")
CONTROLLER_DECISION_REF = "controller_decisions/latest.json"

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
