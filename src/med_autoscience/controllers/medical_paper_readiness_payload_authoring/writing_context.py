from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.policies import publication_critique

from .shared import list_items, mapping_list, read_json, text


def payload_from_writing_context_sources(
    *,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    root = Path(study_root).expanduser().resolve()
    source_paths = {
        "style_corpus": root / "paper" / "medical_journal_style_corpus.json",
        "claim_evidence_map": root / "paper" / "claim_evidence_map.json",
        "display_registry": root / "paper" / "display_registry.json",
        "figure_semantics_manifest": root / "paper" / "figure_semantics_manifest.json",
        "table_catalog": root / "paper" / "tables" / "table_catalog.json",
        "results_narrative_map": root / "paper" / "results_narrative_map.json",
        "medical_manuscript_blueprint": root / "paper" / "medical_manuscript_blueprint.json",
        "medical_prose_review": root / "artifacts" / "publication_eval" / "medical_prose_review.json",
    }
    if any(not path.exists() for path in source_paths.values()):
        return {}
    style_corpus = read_json(source_paths["style_corpus"])
    claim_map = read_json(source_paths["claim_evidence_map"])
    display_registry = read_json(source_paths["display_registry"])
    table_catalog = read_json(source_paths["table_catalog"])
    prose_review = read_json(source_paths["medical_prose_review"])
    near_neighbors = _near_neighbor_style_corpus(style_corpus)
    claim_to_paragraph = _claim_to_paragraph_map(claim_map)
    display_to_claim = _display_to_claim_map(
        claim_map,
        display_registry=display_registry,
        table_catalog=table_catalog,
    )
    if not near_neighbors or not claim_to_paragraph or not display_to_claim:
        return {}
    payload = {
        "surface": "target_journal_writing_layer",
        "schema_version": publication_critique.SCHEMA_VERSION if hasattr(publication_critique, "SCHEMA_VERSION") else 1,
        "role": "ai_reviewer_quality_context",
        "target_journal_family": "general_internal_medicine",
        "near_neighbor_style_corpus": near_neighbors,
        "section_plan": _section_plan(),
        "claim_to_paragraph_map": claim_to_paragraph,
        "display_to_claim_map": display_to_claim,
        "restrained_language_strategy": _restrained_language_strategy(
            claim_map=claim_map,
            prose_review=prose_review,
        ),
        "payload_source": source,
        "source_basis": "structured_writing_context_sources",
        "source_refs": [str(path) for path in source_paths.values()],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    try:
        normalized = publication_critique._normalize_target_journal_writing_layer(dict(payload))
    except ValueError:
        return {}
    return {
        **normalized,
        "payload_source": source,
        "source_basis": "structured_writing_context_sources",
        "source_refs": [str(path) for path in source_paths.values()],
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _near_neighbor_style_corpus(style_corpus: Mapping[str, Any]) -> list[dict[str, str]]:
    source_refs = mapping_list(style_corpus.get("source_refs"))
    if not source_refs:
        return []
    jama_refs = [
        item
        for item in source_refs
        if "jama" in " ".join(text(item.get(key)) for key in ("source_id", "label", "journal")).lower()
    ]
    selected = jama_refs or source_refs[:3]
    neighbors: list[dict[str, str]] = []
    for item in selected[:4]:
        style_ref = text(item.get("source_id")) or text(item.get("url")) or text(item.get("label"))
        journal = _journal_label(item)
        if not style_ref or not journal:
            continue
        neighbors.append(
            {
                "journal": journal,
                "article_role": text(item.get("article_role")) or "near_neighbor_style_reference",
                "style_ref": style_ref,
            }
        )
    return neighbors


def _journal_label(item: Mapping[str, Any]) -> str:
    explicit = text(item.get("journal"))
    if explicit:
        return explicit
    rendered = " ".join(text(item.get(key)) for key in ("label", "source_id"))
    lowered = rendered.lower()
    if "jama network open" in lowered:
        return "JAMA Network Open"
    if "jama internal medicine" in lowered:
        return "JAMA Internal Medicine"
    if "jama" in lowered:
        return "JAMA"
    return text(item.get("label")) or text(item.get("source_id"))


def _claim_to_paragraph_map(claim_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for claim in mapping_list(claim_map.get("claims")):
        claim_id = text(claim.get("claim_id"))
        evidence_refs = _claim_evidence_refs(claim)
        if not claim_id or not evidence_refs:
            continue
        items.append(
            {
                "claim_id": claim_id,
                "section": _first_section(claim),
                "paragraph_role": text(claim.get("paper_role")) or "claim-grounded results paragraph",
                "evidence_refs": evidence_refs,
            }
        )
    return items


def _claim_evidence_refs(claim: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for evidence in mapping_list(claim.get("evidence_items")):
        refs.extend(text(item) for item in list_items(evidence.get("source_paths")) if text(item))
        item_id = text(evidence.get("item_id"))
        if item_id:
            refs.append(f"paper/claim_evidence_map.json#{item_id}")
    return list(dict.fromkeys(ref for ref in refs if ref))


def _first_section(claim: Mapping[str, Any]) -> str:
    for section in list_items(claim.get("sections")):
        section_text = text(section)
        if section_text:
            return section_text
    return "Results"


def _display_to_claim_map(
    claim_map: Mapping[str, Any],
    *,
    display_registry: Mapping[str, Any],
    table_catalog: Mapping[str, Any],
) -> list[dict[str, str]]:
    display_roles = _display_roles(display_registry=display_registry, table_catalog=table_catalog)
    items: list[dict[str, str]] = []
    for claim in mapping_list(claim_map.get("claims")):
        claim_id = text(claim.get("claim_id"))
        if not claim_id:
            continue
        for binding in list_items(claim.get("display_bindings")):
            display_id, display_role = _display_binding(binding)
            if not display_id:
                continue
            items.append(
                {
                    "display_id": display_id,
                    "claim_id": claim_id,
                    "display_role": display_role or display_roles.get(display_id) or "supports claim",
                }
            )
    deduped: dict[tuple[str, str], dict[str, str]] = {}
    for item in items:
        deduped[(item["display_id"], item["claim_id"])] = item
    return list(deduped.values())


def _display_roles(
    *,
    display_registry: Mapping[str, Any],
    table_catalog: Mapping[str, Any],
) -> dict[str, str]:
    roles: dict[str, str] = {}
    for display in mapping_list(display_registry.get("displays")):
        for key in ("display_id", "catalog_id"):
            display_id = text(display.get(key))
            if display_id:
                roles[display_id] = text(display.get("title")) or text(display.get("requirement_key"))
    for table in mapping_list(table_catalog.get("tables")):
        table_id = text(table.get("table_id"))
        if table_id:
            roles[table_id] = text(table.get("title")) or text(table.get("paper_role")) or "table evidence"
    return roles


def _display_binding(binding: object) -> tuple[str, str]:
    if isinstance(binding, Mapping):
        return (
            text(binding.get("display_id")) or text(binding.get("catalog_id")) or text(binding.get("table_id")),
            text(binding.get("display_role")) or text(binding.get("role")),
        )
    return text(binding), ""


def _section_plan() -> dict[str, str]:
    return {
        "Introduction": "clinical problem, evidence gap, and objective",
        "Methods": "cohort, endpoint, analysis, transportability, and bias controls",
        "Results": "primary finding with uncertainty before display interpretation",
        "Discussion": "principal finding, prior work, clinical interpretation, and limitations",
    }


def _restrained_language_strategy(
    *,
    claim_map: Mapping[str, Any],
    prose_review: Mapping[str, Any],
) -> dict[str, Any]:
    forbidden = [
        text(item)
        for claim in mapping_list(claim_map.get("claims"))
        for item in list_items(claim.get("prohibited_interpretations"))
        if text(item)
    ]
    principles = [
        text(item)
        for key in ("restraint_principles", "principles")
        for item in list_items(prose_review.get(key))
        if text(item)
    ]
    return {
        "forbidden_phrases": list(dict.fromkeys([*forbidden, "proves", "definitively establishes"])),
        "required_claim_qualifiers": ["was associated with", "was observed", "may support"],
        "style_principles": list(dict.fromkeys(principles)),
    }


__all__ = ["payload_from_writing_context_sources"]
