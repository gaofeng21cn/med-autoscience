from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "literature_provider_runtime"
ARTIFACT_RELATIVE_PATH = Path("artifacts/medical_paper/literature_provider_runtime.json")
SUPPORTED_PROVIDERS = {"pubmed", "crossref", "semantic_scholar"}
UNAVAILABLE_STATUSES = {"provider_unavailable", "network_unavailable"}
LITERATURE_REF_CATEGORIES = {
    "anchor_papers",
    "guidelines",
    "systematic_reviews",
    "journal_neighbor_refs",
}


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


def _provider_name(provider: Mapping[str, Any]) -> str:
    return _text(provider.get("provider_name"))


def _provider_response_status(provider: Mapping[str, Any]) -> str:
    return _text(provider.get("response_status")) or "ok"


def _provider_refs(provider: Mapping[str, Any]) -> list[object]:
    return _list(provider.get("source_refs"))


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


def _providers(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [provider for provider in _list(payload.get("providers")) if isinstance(provider, Mapping)]


def _missing_reason(payload: Mapping[str, Any]) -> str:
    providers = _providers(payload)
    if not providers:
        return "missing_provider_sources"
    for provider in providers:
        name = _provider_name(provider)
        if not name:
            return "missing_provider_name"
        if name not in SUPPORTED_PROVIDERS:
            return f"unsupported_provider_{name}"
        status = _provider_response_status(provider)
        if status in UNAVAILABLE_STATUSES:
            return f"provider_unavailable_{name}"
        if not _has_text(provider.get("query")):
            return f"missing_provider_query_{name}"
        if not _has_text(provider.get("retrieved_at")):
            return f"missing_provider_retrieved_at_{name}"
        if not _has_ref_items(_provider_refs(provider)):
            return f"missing_provider_source_refs_{name}"
    if not _has_text(payload.get("search_date")):
        return "missing_search_date"
    if not _has_ref_items(payload.get("citation_ledger_refs")):
        return "missing_citation_ledger_refs"
    if not _screening_decisions_are_complete(payload.get("screening_decisions")):
        return "missing_screening_decision_reason"
    return ""


def _source_response_digest(providers: list[Mapping[str, Any]]) -> dict[str, Any]:
    statuses = sorted({_provider_response_status(provider) for provider in providers})
    return {
        "provider_count": len(providers),
        "source_ref_count": sum(len(_provider_refs(provider)) for provider in providers),
        "item_count": sum(len(_list(provider.get("items"))) for provider in providers),
        "response_statuses": statuses,
    }


def _provider_source_refs(providers: list[Mapping[str, Any]]) -> list[object]:
    refs: list[object] = []
    for provider in providers:
        refs.extend(_provider_refs(provider))
    return refs


def _categorized_refs(providers: list[Mapping[str, Any]]) -> dict[str, list[object]]:
    categorized = {category: [] for category in LITERATURE_REF_CATEGORIES}
    for provider in providers:
        for item in _list(provider.get("items")):
            source_item = _mapping(item)
            category = _text(source_item.get("category"))
            ref = source_item.get("ref")
            if category in categorized and _has_text(ref):
                categorized[category].append(ref)
    return categorized


def _literature_intelligence_payload(
    payload: Mapping[str, Any],
    providers: list[Mapping[str, Any]],
) -> dict[str, Any]:
    categorized = _categorized_refs(providers)
    return {
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "search_date": _text(payload.get("search_date")),
        "searched_sources": _provider_source_refs(providers),
        "anchor_papers": categorized["anchor_papers"],
        "guidelines": categorized["guidelines"],
        "systematic_reviews": categorized["systematic_reviews"],
        "journal_neighbor_refs": categorized["journal_neighbor_refs"],
        "screening_decisions": _list(payload.get("screening_decisions")),
        "citation_ledger_refs": _list(payload.get("citation_ledger_refs")),
    }


def build_literature_provider_runtime_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    providers = _providers(payload)
    missing_reason = _missing_reason(payload)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if not missing_reason else "blocked",
        "missing_reason": missing_reason,
        "providers": [_provider_name(provider) for provider in providers],
        "search_date": _text(payload.get("search_date")),
        "search_strategy": dict(_mapping(payload.get("search_strategy"))),
        "citation_ledger_refs": _list(payload.get("citation_ledger_refs")),
        "screening_decisions": _list(payload.get("screening_decisions")),
        "source_response_digest": _source_response_digest(providers),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "literature_intelligence_payload": _literature_intelligence_payload(payload, providers),
    }


def stable_literature_provider_runtime_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / ARTIFACT_RELATIVE_PATH).resolve()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def materialize_literature_provider_runtime(
    *,
    study_root: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    path = stable_literature_provider_runtime_path(study_root=study_root)
    projection = build_literature_provider_runtime_projection(payload)
    artifact = dict(projection)
    artifact["study_root"] = str(Path(study_root).expanduser().resolve())
    _write_json(path, artifact)
    return {
        "surface": SURFACE,
        "status": projection["status"],
        "missing_reason": projection["missing_reason"],
        "artifact_path": str(path),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "literature_intelligence_payload": projection["literature_intelligence_payload"],
    }
