from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.stage_knowledge_contract import (
    PUBLICATION_ROUTE_MEMORY_STAGES,
    SCHEMA_VERSION,
    authority_boundary,
)


PUBLICATION_ROUTE_MEMORY_ROOT = Path("portfolio/research_memory/publication_route_memory")


def build_publication_route_memory_inventory(
    *,
    workspace_root: Path,
    stage: str | None = None,
    route_family_tags: Sequence[str] | None = None,
    statuses: Sequence[str] | None = None,
    include_card_body: bool = False,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    pack_root = resolved_workspace_root / PUBLICATION_ROUTE_MEMORY_ROOT
    pack_path = pack_root / "memory_pack.json"
    pack = _read_json(pack_path)
    cards = _mapping_list(pack.get("cards"))
    resolved_stage = _validate_publication_route_memory_stage(stage) if _text(stage) else ""
    route_tags = set(_text_list(list(route_family_tags or [])))
    status_filter = set(_text_list(list(statuses or [])))
    filtered_cards = [
        card
        for card in cards
        if _publication_route_card_matches(
            card=card,
            stage=resolved_stage,
            route_family_tags=route_tags,
            statuses=status_filter,
        )
    ]
    return {
        "surface": "publication_route_memory_inventory",
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if pack_path.exists() else "missing",
        "read_only": True,
        "body_included": bool(include_card_body),
        "workspace_root": str(resolved_workspace_root),
        "memory_pack_ref": str(pack_path),
        "card_count_total": len(cards),
        "card_count_filtered": len(filtered_cards),
        "filters": {
            "stage": resolved_stage or None,
            "route_family": sorted(route_tags),
            "status": sorted(status_filter),
        },
        "cards": [
            _publication_route_inventory_card(card, include_body=include_card_body)
            for card in filtered_cards
        ],
        "receipt_summary": _publication_route_memory_receipt_summary(pack_root=pack_root),
        "opl_aion_receipt_inventory": _opl_aion_receipt_inventory(pack_root=pack_root),
        "locator_refs": {
            "memory_pack": str(pack_path),
            "migration_receipts": str(pack_root / "migration_receipts"),
            "writeback_proposals": str(pack_root / "writeback_proposals" / "stage_memory_updates.jsonl"),
            "writeback_receipts": str(pack_root / "writeback_receipts"),
        },
        "authority_boundary": authority_boundary(),
    }


def _publication_route_card_matches(
    *,
    card: Mapping[str, Any],
    stage: str,
    route_family_tags: set[str],
    statuses: set[str],
) -> bool:
    stages = set(_text_list(card.get("stage_applicability")))
    if stage and stage not in stages:
        return False
    if route_family_tags and _text(card.get("route_family")) not in route_family_tags:
        return False
    if statuses and _text(card.get("status")) not in statuses:
        return False
    return True


def _publication_route_inventory_card(card: Mapping[str, Any], *, include_body: bool) -> dict[str, Any]:
    inventory_card = {
        "memory_id": _text(card.get("memory_id")),
        "status": _text(card.get("status")),
        "route_family": _text(card.get("route_family")),
        "stage_applicability": _text_list(card.get("stage_applicability")),
        "title": _text(card.get("title")),
        "source_receipt_ref": _text(card.get("source_receipt_ref")),
        "source_refs": _mapping_list(card.get("source_refs")),
        "authority_boundary": _text(card.get("authority_boundary")) or "context_only_not_publication_authority",
    }
    if include_body:
        inventory_card["prose_summary"] = _text(card.get("prose_summary"))
        inventory_card["best_fit"] = _text_list(card.get("best_fit"))
        inventory_card["poor_fit"] = _text_list(card.get("poor_fit"))
        inventory_card["minimum_evidence_package"] = _text_list(card.get("minimum_evidence_package"))
        inventory_card["analysis_pattern"] = _text_list(card.get("analysis_pattern"))
        inventory_card["table_figure_pattern"] = _text_list(card.get("table_figure_pattern"))
        inventory_card["claim_boundary"] = _text(card.get("claim_boundary"))
        inventory_card["reviewer_risks"] = _text_list(card.get("reviewer_risks"))
        inventory_card["pivot_or_stop_rules"] = _text_list(card.get("pivot_or_stop_rules"))
        inventory_card["codex_stage_guidance"] = _mapping(card.get("codex_stage_guidance"))
        inventory_card["example_signals"] = _text_list(card.get("example_signals"))
        inventory_card["failure_modes"] = _text_list(card.get("failure_modes"))
    return inventory_card


def _publication_route_memory_receipt_summary(*, pack_root: Path) -> dict[str, Any]:
    migration_receipts = sorted((pack_root / "migration_receipts").glob("*.json"))
    writeback_receipts = sorted((pack_root / "writeback_receipts").glob("*.json"))
    writeback_proposal = pack_root / "writeback_proposals" / "stage_memory_updates.jsonl"
    return {
        "migration_receipt_count": len(migration_receipts),
        "writeback_proposal_exists": writeback_proposal.exists(),
        "writeback_receipt_count": len(writeback_receipts),
        "migration_receipt_refs": [str(path) for path in migration_receipts],
        "writeback_proposal_ref": str(writeback_proposal),
        "writeback_receipt_refs": [str(path) for path in writeback_receipts],
    }


def _opl_aion_receipt_inventory(*, pack_root: Path) -> dict[str, Any]:
    receipt_paths = [
        *sorted((pack_root / "migration_receipts").glob("*.json")),
        *sorted((pack_root / "writeback_receipts").glob("*.json")),
    ]
    receipts = [_receipt_ref_projection(path) for path in receipt_paths]
    return {
        "body_included": False,
        "read_only": True,
        "receipt_count": len(receipts),
        "receipts": receipts,
    }


def _receipt_ref_projection(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    return {
        "ref": str(path),
        "receipt_status": _text(payload.get("status")),
        "receipt_kind": _text(payload.get("surface")) or _text(payload.get("surface_kind")),
        "accepted_refs": _accepted_receipt_refs(payload),
        "rejected_refs": _rejected_receipt_refs(payload),
        "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
        "body_included": False,
    }


def _accepted_receipt_refs(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    accepted_memory_ids = _text_list(payload.get("accepted_memory_ids"))
    if accepted_memory_ids:
        return [{"memory_id": memory_id, "reason": "", "status": "accepted"} for memory_id in accepted_memory_ids]
    refs = []
    for write in _mapping_list(payload.get("accepted_writes")):
        refs.append(
            {
                "write_id": _text(write.get("write_id")),
                "reason": _text(write.get("reason")),
                "status": "accepted",
            }
        )
    return refs


def _rejected_receipt_refs(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    rejected_cards = _mapping_list(payload.get("rejected_cards"))
    if rejected_cards:
        return [
            {
                "memory_id": _text(card.get("memory_id")),
                "reason": _text(card.get("reason")),
                "status": "rejected",
            }
            for card in rejected_cards
        ]
    refs = []
    for write in _mapping_list(payload.get("rejected_writes")):
        refs.append(
            {
                "write_id": _text(write.get("write_id")),
                "reason": _text(write.get("reason")),
                "status": "rejected",
            }
        )
    return refs


def _validate_publication_route_memory_stage(stage: str | None) -> str:
    resolved = _text(stage)
    if resolved not in PUBLICATION_ROUTE_MEMORY_STAGES:
        raise ValueError(f"unsupported publication route memory stage: {resolved}")
    return resolved


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


__all__ = ["build_publication_route_memory_inventory"]
