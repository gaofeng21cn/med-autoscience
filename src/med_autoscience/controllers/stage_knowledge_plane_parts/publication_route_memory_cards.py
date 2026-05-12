from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


RICH_CARD_FIELDS = (
    "prose_summary",
    "best_fit",
    "poor_fit",
    "minimum_evidence_package",
    "analysis_pattern",
    "table_figure_pattern",
    "claim_boundary",
    "reviewer_risks",
    "pivot_or_stop_rules",
    "codex_stage_guidance",
    "failure_modes",
    "source_refs",
)
RICH_LIST_FIELDS = (
    "best_fit",
    "poor_fit",
    "minimum_evidence_package",
    "analysis_pattern",
    "table_figure_pattern",
    "reviewer_risks",
    "pivot_or_stop_rules",
    "example_signals",
    "failure_modes",
)


def publication_seed_blockers(
    *,
    fixture: Mapping[str, Any],
    seed_cards: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    if fixture.get("surface_kind") != "publication_route_memory_seed_fixture":
        blockers.append({"blocker_id": "seed_fixture_surface_invalid", "owner_target": "domain_memory_owner"})
    if _text(fixture.get("memory_family")) != "publication_route_memory":
        blockers.append({"blocker_id": "seed_fixture_memory_family_invalid", "owner_target": "domain_memory_owner"})
    if not seed_cards:
        blockers.append({"blocker_id": "seed_fixture_cards_missing", "owner_target": "domain_memory_owner"})
    for index, card in enumerate(seed_cards):
        if not _text(card.get("memory_id")):
            blockers.append(
                {"blocker_id": f"seed_card:{index + 1}:memory_id_missing", "owner_target": "domain_memory_owner"}
            )
        if not _text_list(card.get("stage_applicability")):
            blockers.append(
                {
                    "blocker_id": f"seed_card:{index + 1}:stage_applicability_missing",
                    "owner_target": "domain_memory_owner",
                }
            )
        for field in RICH_CARD_FIELDS:
            if not _publication_route_card_field_present(card, field):
                blockers.append(
                    {
                        "blocker_id": f"seed_card:{index + 1}:{field}_missing",
                        "owner_target": "domain_memory_owner",
                    }
                )
    return blockers


def normalize_publication_route_card(card: Mapping[str, Any]) -> dict[str, Any]:
    normalized = {
        "memory_id": _required_text("memory_id", card.get("memory_id")),
        "status": _text(card.get("status")) or "active",
        "route_family": _text(card.get("route_family")),
        "stage_applicability": _text_list(card.get("stage_applicability")),
        "title": _text(card.get("title")),
        "prose_summary": _text(card.get("prose_summary")),
        "claim_boundary": _text(card.get("claim_boundary")),
        "codex_stage_guidance": _mapping(card.get("codex_stage_guidance")),
        "source_refs": _mapping_list(card.get("source_refs")),
    }
    for field in RICH_LIST_FIELDS:
        normalized[field] = _text_list(card.get(field))
    return normalized


def _publication_route_card_field_present(card: Mapping[str, Any], field: str) -> bool:
    value = card.get(field)
    if field == "source_refs":
        return bool(_mapping_list(value))
    if field == "codex_stage_guidance":
        return bool(_mapping(value))
    if field in RICH_LIST_FIELDS:
        return bool(_text_list(value))
    return bool(_text(value))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = ["normalize_publication_route_card", "publication_seed_blockers"]
