from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "literature_intelligence_os"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/literature_intelligence_os.json")


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _has_text(value: object) -> bool:
    return bool(_text(value))


def _has_ref_items(value: object) -> bool:
    return any(_has_text(item) or bool(_mapping(item).get("ref")) for item in _list(value))


def _search_strategy_is_complete(payload: Mapping[str, Any]) -> bool:
    strategy = _mapping(payload.get("search_strategy"))
    return _has_text(strategy.get("query")) and _has_ref_items(strategy.get("mesh_terms"))


def _screening_decisions_are_complete(value: object) -> bool:
    decisions = [item for item in _list(value) if isinstance(item, Mapping)]
    if not decisions:
        return False
    for decision in decisions:
        if _text(decision.get("decision")) not in {"include", "exclude"}:
            return False
        if not _has_text(decision.get("reason")):
            return False
    return True


def _missing_reason(payload: Mapping[str, Any]) -> str:
    if not _has_text(payload.get("search_date")):
        return "missing_search_date"
    if not _search_strategy_is_complete(payload):
        return "missing_search_strategy"
    if not _has_ref_items(payload.get("searched_sources")):
        return "missing_searched_sources"
    if not _has_ref_items(payload.get("anchor_papers")):
        return "missing_anchor_paper_refs"
    if not _has_ref_items(payload.get("guidelines")):
        return "missing_guideline_refs"
    if not _has_ref_items(payload.get("systematic_reviews")):
        return "missing_systematic_review_refs"
    if not _has_ref_items(payload.get("journal_neighbor_refs")):
        return "missing_journal_neighbor_refs"
    if not _screening_decisions_are_complete(payload.get("screening_decisions")):
        return "missing_screening_decision_reason"
    if not _has_ref_items(payload.get("citation_ledger_refs")):
        return "missing_citation_ledger_refs"
    return ""


def stable_literature_intelligence_os_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalize_payload(*, study_root: Path, payload: Mapping[str, Any]) -> dict[str, Any]:
    missing_reason = _missing_reason(payload)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "status": "ready" if not missing_reason else "blocked",
        "missing_reason": missing_reason,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "search_date": _text(payload.get("search_date")),
        "searched_sources": _list(payload.get("searched_sources")),
        "anchor_papers": _list(payload.get("anchor_papers")),
        "guidelines": _list(payload.get("guidelines")),
        "systematic_reviews": _list(payload.get("systematic_reviews")),
        "journal_neighbor_refs": _list(payload.get("journal_neighbor_refs")),
        "screening_decisions": _list(payload.get("screening_decisions")),
        "citation_ledger_refs": _list(payload.get("citation_ledger_refs")),
    }


def materialize_literature_intelligence_os(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    path = stable_literature_intelligence_os_path(study_root=study_root)
    normalized = _normalize_payload(study_root=study_root, payload=payload)
    _write_json(path, normalized)
    return {
        "surface": SURFACE,
        "status": normalized["status"],
        "missing_reason": normalized["missing_reason"],
        "artifact_path": str(path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def read_literature_intelligence_os(*, study_root: Path) -> dict[str, Any]:
    return dict(_read_json(stable_literature_intelligence_os_path(study_root=study_root)))


def build_literature_intelligence_os_summary(*, study_root: Path) -> dict[str, Any]:
    path = stable_literature_intelligence_os_path(study_root=study_root)
    payload = _read_json(path)
    if not payload:
        return {
            "surface": SURFACE,
            "status": "blocked",
            "missing_reason": "missing_canonical_artifact",
            "artifact_path": str(path),
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
            "coverage": {
                "searched_source_count": 0,
                "anchor_paper_count": 0,
                "guideline_count": 0,
                "systematic_review_count": 0,
                "journal_neighbor_ref_count": 0,
                "screening_decision_count": 0,
                "citation_ledger_ref_count": 0,
            },
        }
    return {
        "surface": SURFACE,
        "status": _text(payload.get("status")) or "blocked",
        "missing_reason": _text(payload.get("missing_reason")),
        "artifact_path": str(path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "coverage": {
            "searched_source_count": len(_list(payload.get("searched_sources"))),
            "anchor_paper_count": len(_list(payload.get("anchor_papers"))),
            "guideline_count": len(_list(payload.get("guidelines"))),
            "systematic_review_count": len(_list(payload.get("systematic_reviews"))),
            "journal_neighbor_ref_count": len(_list(payload.get("journal_neighbor_refs"))),
            "screening_decision_count": len(_list(payload.get("screening_decisions"))),
            "citation_ledger_ref_count": len(_list(payload.get("citation_ledger_refs"))),
        },
    }
