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
MARKDOWN_LIST_SECTIONS = {
    "Best Fit": "best_fit",
    "Poor Fit": "poor_fit",
    "Minimum Evidence Package": "minimum_evidence_package",
    "Analysis Pattern": "analysis_pattern",
    "Table Figure Pattern": "table_figure_pattern",
    "Reviewer Risks": "reviewer_risks",
    "Pivot Or Stop Rules": "pivot_or_stop_rules",
    "Example Signals": "example_signals",
    "Failure Modes": "failure_modes",
}
MARKDOWN_TEXT_SECTIONS = {
    "Summary": "prose_summary",
    "Claim Boundary": "claim_boundary",
}


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


def publication_route_cards_from_markdown(markdown: str) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    current_card: dict[str, Any] | None = None
    current_section = ""
    section_lines: list[str] = []

    def flush_section() -> None:
        nonlocal section_lines
        if current_card is None or not current_section:
            section_lines = []
            return
        field = MARKDOWN_TEXT_SECTIONS.get(current_section)
        if field:
            current_card[field] = _paragraph(section_lines)
        elif current_section in MARKDOWN_LIST_SECTIONS:
            current_card[MARKDOWN_LIST_SECTIONS[current_section]] = _markdown_list(section_lines)
        elif current_section == "Codex Stage Guidance":
            current_card["codex_stage_guidance"] = _markdown_keyed_list(section_lines)
        elif current_section == "Source Refs":
            current_card["source_refs"] = _markdown_source_refs(section_lines)
        section_lines = []

    def flush_card() -> None:
        if current_card and _text(current_card.get("memory_id")).startswith("publication_route_memory_"):
            cards.append(dict(current_card))

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("## "):
            flush_section()
            flush_card()
            current_card = {"memory_id": line[3:].strip()}
            current_section = ""
            section_lines = []
            continue
        if current_card is None:
            continue
        if line.startswith("### "):
            flush_section()
            current_section = line[4:].strip()
            continue
        if current_section:
            section_lines.append(line)
            continue
        _parse_metadata_line(current_card, line)

    flush_section()
    flush_card()
    return cards


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


def _parse_metadata_line(card: dict[str, Any], line: str) -> None:
    if line.startswith("Status:"):
        card["status"] = line.removeprefix("Status:").strip()
    elif line.startswith("Route family:"):
        card["route_family"] = line.removeprefix("Route family:").strip()
    elif line.startswith("Stage applicability:"):
        stages = line.removeprefix("Stage applicability:").split(",")
        card["stage_applicability"] = [_text(stage) for stage in stages if _text(stage)]
    elif line.startswith("Title:"):
        card["title"] = line.removeprefix("Title:").strip()


def _paragraph(lines: Sequence[str]) -> str:
    return " ".join(line.strip() for line in lines if line.strip()).strip()


def _markdown_list(lines: Sequence[str]) -> list[str]:
    return [line.strip()[2:].strip() for line in lines if line.strip().startswith("- ") and line.strip()[2:].strip()]


def _markdown_keyed_list(lines: Sequence[str]) -> dict[str, str]:
    guidance: dict[str, str] = {}
    for item in _markdown_list(lines):
        key, separator, value = item.partition(":")
        if separator and _text(key) and _text(value):
            guidance[_text(key)] = _text(value)
    return guidance


def _markdown_source_refs(lines: Sequence[str]) -> list[dict[str, str]]:
    refs = []
    for item in _markdown_list(lines):
        parts = [_text(part) for part in item.split("|")]
        if len(parts) >= 2:
            refs.append(
                {
                    "ref_kind": parts[0],
                    "ref": parts[1],
                    "role": parts[2] if len(parts) >= 3 else "",
                }
            )
    return refs


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


__all__ = [
    "normalize_publication_route_card",
    "publication_route_cards_from_markdown",
    "publication_seed_blockers",
]
