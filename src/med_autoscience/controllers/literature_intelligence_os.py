from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "literature_intelligence_os"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/literature_intelligence_os.json")
EVIDENCE_NODE_PROVENANCE_KEYS = ("pmid", "doi", "guideline_ref", "source_ref")


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


def _dict_items(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in _list(value) if isinstance(item, Mapping)]


def _search_strategy_is_complete(payload: Mapping[str, Any]) -> bool:
    strategy = _mapping(payload.get("search_strategy"))
    return _has_text(strategy.get("query")) and _has_ref_items(strategy.get("mesh_terms"))


def _keyword_terms_are_complete(payload: Mapping[str, Any]) -> bool:
    strategy = _mapping(payload.get("search_strategy"))
    return _has_ref_items(strategy.get("keywords")) or _has_ref_items(payload.get("keywords"))


def _study_rationale(payload: Mapping[str, Any]) -> str:
    for key in ("why_worth_doing", "study_rationale", "research_rationale", "rationale"):
        value = _text(payload.get(key))
        if value:
            return value
    return ""


def _provider_provenance_is_complete(value: object) -> bool:
    providers = [item for item in _list(value) if isinstance(item, Mapping)]
    if not providers:
        return False
    for provider in providers:
        if not _has_text(provider.get("provider_name")):
            return False
        if not _has_text(provider.get("query")):
            return False
        if not _has_text(provider.get("retrieved_at")):
            return False
        if not _has_text(provider.get("response_status")):
            return False
        if not _has_ref_items(provider.get("source_refs")):
            return False
    return True


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


def _evidence_nodes(value: object) -> list[dict[str, Any]]:
    return _dict_items(value)


def _evidence_node_has_provenance(node: Mapping[str, Any]) -> bool:
    return any(_has_text(node.get(key)) for key in EVIDENCE_NODE_PROVENANCE_KEYS)


def _evidence_nodes_have_provenance(value: object) -> bool:
    nodes = _evidence_nodes(value)
    return all(_evidence_node_has_provenance(node) for node in nodes)


def _contradiction_flags(value: object) -> list[dict[str, Any]]:
    flags = _dict_items(value)
    for flag in flags:
        flag["review_signal_only"] = True
    return flags


def _authority() -> dict[str, Any]:
    return {
        "can_authorize_publication_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "contradiction_flags_authority": "evidence_review_signal_only",
    }


def _source_coverage(payload: Mapping[str, Any]) -> dict[str, int]:
    return {
        "searched_source_count": len(_list(payload.get("searched_sources"))),
        "provider_provenance_count": len(_list(payload.get("provider_provenance"))),
        "anchor_paper_count": len(_list(payload.get("anchor_papers"))),
        "guideline_count": len(_list(payload.get("guidelines"))),
        "systematic_review_count": len(_list(payload.get("systematic_reviews"))),
        "journal_neighbor_ref_count": len(_list(payload.get("journal_neighbor_refs"))),
        "high_score_neighbor_ref_count": len(_list(payload.get("high_score_neighbor_refs"))),
        "citation_ledger_ref_count": len(_list(payload.get("citation_ledger_refs"))),
        "evidence_node_count": len(_evidence_nodes(payload.get("evidence_nodes"))),
        "perspective_question_count": len(_dict_items(payload.get("perspective_questions"))),
        "contradiction_flag_count": len(_dict_items(payload.get("contradiction_flags"))),
    }


def _required_source_missing_reason(payload: Mapping[str, Any]) -> str:
    ordered_checks = (
        ("searched_sources", "missing_searched_sources"),
        ("anchor_papers", "missing_anchor_paper_refs"),
        ("guidelines", "missing_guideline_refs"),
        ("systematic_reviews", "missing_systematic_review_refs"),
        ("journal_neighbor_refs", "missing_journal_neighbor_refs"),
        ("high_score_neighbor_refs", "missing_high_score_neighbor_refs"),
        ("citation_ledger_refs", "missing_citation_ledger_refs"),
    )
    for key, reason in ordered_checks:
        if not _has_ref_items(payload.get(key)):
            return reason
    return ""


def _missing_reason(payload: Mapping[str, Any]) -> str:
    if not _has_text(payload.get("search_date")):
        return "missing_search_date"
    if not _search_strategy_is_complete(payload):
        return "missing_search_strategy"
    if not _keyword_terms_are_complete(payload):
        return "missing_keyword_terms"
    if not _provider_provenance_is_complete(payload.get("provider_provenance")):
        return "missing_provider_provenance"
    if not _study_rationale(payload):
        return "missing_study_rationale"
    missing_source_reason = _required_source_missing_reason(payload)
    if missing_source_reason:
        return missing_source_reason
    if not _screening_decisions_are_complete(payload.get("screening_decisions")):
        return "missing_screening_decision_reason"
    if _evidence_nodes(payload.get("evidence_nodes")) and not _evidence_nodes_have_provenance(
        payload.get("evidence_nodes")
    ):
        return "missing_evidence_node_provenance"
    return ""


def _diagnostic_category(reason: str) -> str:
    if reason == "missing_search_date" or reason == "missing_search_strategy" or reason == "missing_keyword_terms":
        return "search_readiness"
    if reason == "missing_searched_sources":
        return "source_readiness"
    if reason == "missing_provider_provenance":
        return "provider_provenance_readiness"
    if reason == "missing_study_rationale":
        return "study_rationale_readiness"
    if reason in {
        "missing_anchor_paper_refs",
        "missing_guideline_refs",
        "missing_systematic_review_refs",
        "missing_journal_neighbor_refs",
        "missing_high_score_neighbor_refs",
    }:
        return "literature_intelligence_readiness"
    if reason == "missing_screening_decision_reason":
        return "screening_readiness"
    if reason == "missing_citation_ledger_refs":
        return "citation_readiness"
    if reason == "missing_evidence_node_provenance":
        return "evidence_provenance_readiness"
    return "literature_intelligence_projection"


def _diagnostics(missing_reason: str) -> list[dict[str, Any]]:
    if not missing_reason:
        return []
    return [
        {
            "reason_code": missing_reason,
            "severity": "blocking",
            "category": _diagnostic_category(missing_reason),
        }
    ]


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
    normalized_graph = {
        "evidence_nodes": _evidence_nodes(payload.get("evidence_nodes")),
        "perspective_questions": _dict_items(payload.get("perspective_questions")),
        "contradiction_flags": _contradiction_flags(payload.get("contradiction_flags")),
        "metadata_quality": dict(_mapping(payload.get("metadata_quality"))),
        "citation_grounding": dict(_mapping(payload.get("citation_grounding"))),
    }
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "study_id": _text(payload.get("study_id")),
        "status": "ready" if not missing_reason else "blocked",
        "missing_reason": missing_reason,
        "diagnostics": _diagnostics(missing_reason),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "source_coverage": _source_coverage(payload),
        **normalized_graph,
        "authority": _authority(),
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "search_date": _text(payload.get("search_date")),
        "searched_sources": _list(payload.get("searched_sources")),
        "provider_provenance": _list(payload.get("provider_provenance")),
        "why_worth_doing": _study_rationale(payload),
        "anchor_papers": _list(payload.get("anchor_papers")),
        "guidelines": _list(payload.get("guidelines")),
        "systematic_reviews": _list(payload.get("systematic_reviews")),
        "journal_neighbor_refs": _list(payload.get("journal_neighbor_refs")),
        "high_score_neighbor_refs": _list(payload.get("high_score_neighbor_refs")),
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
        "diagnostics": normalized["diagnostics"],
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
            "diagnostics": _diagnostics("missing_canonical_artifact"),
            "artifact_path": str(path),
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
            "authority": _authority(),
            "coverage": {
                "searched_source_count": 0,
                "provider_provenance_count": 0,
                "anchor_paper_count": 0,
                "guideline_count": 0,
                "systematic_review_count": 0,
                "journal_neighbor_ref_count": 0,
                "high_score_neighbor_ref_count": 0,
                "screening_decision_count": 0,
                "citation_ledger_ref_count": 0,
                "evidence_node_count": 0,
                "perspective_question_count": 0,
                "contradiction_flag_count": 0,
            },
        }
    source_coverage = _source_coverage(payload)
    return {
        "surface": SURFACE,
        "status": _text(payload.get("status")) or "blocked",
        "missing_reason": _text(payload.get("missing_reason")),
        "diagnostics": _list(payload.get("diagnostics")) or _diagnostics(_text(payload.get("missing_reason"))),
        "artifact_path": str(path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "authority": _authority(),
        "coverage": {
            **source_coverage,
            "screening_decision_count": len(_list(payload.get("screening_decisions"))),
        },
    }
