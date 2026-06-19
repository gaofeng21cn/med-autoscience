from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SURFACE_KIND = "mas_paper_section_source_map_readback"
SCHEMA_VERSION = 1

REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "section_id",
    "section_role",
    "draft_block_refs",
    "claim_refs",
    "evidence_refs",
    "source_map_refs",
    "reviewer_repair_refs",
)
REF_FIELDS: tuple[str, ...] = (
    "draft_block_refs",
    "claim_refs",
    "evidence_refs",
    "source_map_refs",
    "reviewer_repair_refs",
)
READER_BLOCKER_FIELDS = frozenset({"source_map_refs"})


def build_paper_section_source_map_readback(section_map: Mapping[str, Any]) -> dict[str, Any]:
    """Build a body-free paper-section readback for mainline progress routing."""
    missing_fields = _missing_fields(section_map)
    authority_boundary = _authority_boundary()
    typed_blocker_candidate = (
        _typed_blocker_candidate(missing_fields, authority_boundary)
        if missing_fields
        else None
    )

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "typed_blocker_candidate" if missing_fields else "complete",
        "refs_only": True,
        "fail_open": True,
        "mainline_waits_for_readback": False,
        "can_block_current_owner_action": False,
        "section": {
            "section_id": _text(section_map.get("section_id")),
            "section_role": _text(section_map.get("section_role")),
        },
        "refs": {field: _refs(section_map.get(field)) for field in REF_FIELDS},
        "missing_fields": missing_fields,
        "typed_blocker_candidate": typed_blocker_candidate,
        "authority_boundary": authority_boundary,
        "external_provenance_refs": _external_provenance_refs(),
        "contract_refs": _contract_refs(),
    }


def _missing_fields(section_map: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        if field == "schema_version":
            if section_map.get(field) != SCHEMA_VERSION:
                missing.append(field)
        elif field in REF_FIELDS:
            if not _refs(section_map.get(field)):
                missing.append(field)
        elif _text(section_map.get(field)) is None:
            missing.append(field)
    return missing


def _typed_blocker_candidate(
    missing_fields: Sequence[str],
    authority_boundary: Mapping[str, bool],
) -> dict[str, Any]:
    blocker_type = _blocker_type(missing_fields)
    return {
        "blocker_type": blocker_type,
        "missing_fields": list(missing_fields),
        "refs_only": True,
        "fail_open": True,
        "can_block_current_owner_action": False,
        "recommended_owner_action": _recommended_owner_action(blocker_type),
        "authority_boundary": dict(authority_boundary),
    }


def _blocker_type(missing_fields: Sequence[str]) -> str:
    if any(field in READER_BLOCKER_FIELDS for field in missing_fields):
        return "reader_source_map_or_anchor_blocker"
    return "manuscript_argument_or_overclaim_blocker"


def _recommended_owner_action(blocker_type: str) -> str:
    if blocker_type == "reader_source_map_or_anchor_blocker":
        return "repair_section_source_map_refs"
    return "repair_section_argument_or_reviewer_refs"


def _authority_boundary() -> dict[str, bool]:
    return {
        "can_write_mas_truth": False,
        "can_mutate_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
    }


def _external_provenance_refs() -> list[dict[str, object]]:
    return [
        {
            "source_project": "nature-skills",
            "source_ref": "nature-skills@1cb9070:skills/nature-writing",
            "absorbed_as": "section_contract_to_draft_block_ref_pattern",
            "copied_upstream_text": False,
        },
        {
            "source_project": "nature-skills",
            "source_ref": "nature-skills@1cb9070:skills/nature-polishing",
            "absorbed_as": "section_aware_claim_boundary_and_overclaim_ref_pattern",
            "copied_upstream_text": False,
        },
        {
            "source_project": "nature-skills",
            "source_ref": "nature-skills@1cb9070:skills/nature-reader",
            "absorbed_as": "source_map_and_reader_anchor_ref_pattern",
            "copied_upstream_text": False,
        },
    ]


def _contract_refs() -> list[dict[str, str]]:
    return [
        {
            "pack_id": "manuscript_argument_pack",
            "extension_contract_id": "prose_polish_claim_boundary_contract",
            "typed_blocker_if_missing": "manuscript_argument_or_overclaim_blocker",
        },
        {
            "pack_id": "paper_reader_grounding_pack",
            "extension_contract_id": "full_paper_reader_source_map_contract",
            "typed_blocker_if_missing": "reader_source_map_or_anchor_blocker",
        },
    ]


def _refs(value: object) -> list[str]:
    if isinstance(value, str):
        ref = value.strip()
        return [ref] if ref else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [ref for item in value if isinstance(item, str) and (ref := item.strip())]
    return []


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_paper_section_source_map_readback",
]
