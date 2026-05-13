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
        "operator_grouping": _publication_route_memory_operator_grouping(
            workspace_root=resolved_workspace_root,
            cards=filtered_cards,
            include_body=include_card_body,
        ),
        "review_summary": _publication_route_memory_review_summary(filtered_cards),
        "receipt_summary": _publication_route_memory_receipt_summary(pack_root=pack_root),
        "opl_aion_receipt_inventory": _publication_route_memory_opl_aion_receipt_inventory(pack_root=pack_root),
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
        "review_state": _publication_route_memory_review_state(card),
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


def _publication_route_memory_operator_grouping(
    *,
    workspace_root: Path,
    cards: Sequence[Mapping[str, Any]],
    include_body: bool,
) -> dict[str, Any]:
    return {
        "surface": "publication_route_memory_operator_grouping",
        "read_only": True,
        "body_included": bool(include_body),
        "workspace": {
            "workspace_root": str(workspace_root),
            "memory_refs": _group_memory_refs(cards),
            "card_count": len(cards),
        },
        "by_stage": _group_cards_by_value(
            cards,
            values_for_card=lambda card: _text_list(card.get("stage_applicability")),
            group_key="stage",
        ),
        "by_route_family": _group_cards_by_value(
            cards,
            values_for_card=lambda card: [_text(card.get("route_family"))],
            group_key="route_family",
        ),
        "by_status": _group_cards_by_value(
            cards,
            values_for_card=lambda card: [_publication_route_memory_review_state(card)],
            group_key="status",
        ),
        "display_policy": {
            "consumer": "OPL/Aion",
            "display_role": "ref_only_grouping",
            "can_read_memory_body": bool(include_body),
            "can_write_memory_body": False,
            "can_accept_or_reject_writeback": False,
            "can_score_winning_route": False,
            "can_authorize_publication_quality": False,
        },
    }


def _publication_route_memory_review_summary(cards: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    states = [_publication_route_memory_review_state(card) for card in cards]
    return {
        "surface": "publication_route_memory_review_summary",
        "card_count": len(cards),
        "active_count": states.count("active"),
        "stale_count": states.count("stale"),
        "deprecated_count": states.count("deprecated"),
        "needs_review_count": sum(1 for state in states if state in {"stale", "deprecated"}),
        "stale_or_deprecated_refs": [
            _text(card.get("memory_id"))
            for card in cards
            if _publication_route_memory_review_state(card) in {"stale", "deprecated"}
        ],
        "authority_boundary": "review_signal_only_not_memory_body_or_quality_authority",
    }


def _publication_route_memory_review_state(card: Mapping[str, Any]) -> str:
    status = _text(card.get("status")).lower().replace("-", "_")
    if status in {"deprecated", "deprecated_seed", "retired", "retired_seed"}:
        return "deprecated"
    if status in {"stale", "stale_seed", "needs_review", "review_needed"}:
        return "stale"
    return "active"


def _group_cards_by_value(
    cards: Sequence[Mapping[str, Any]],
    *,
    values_for_card,
    group_key: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for card in cards:
        values = [value for value in values_for_card(card) if value]
        for value in values or ["unclassified"]:
            grouped.setdefault(value, []).append(card)
    return [
        {
            group_key: value,
            "memory_refs": _group_memory_refs(grouped[value]),
            "card_count": len(grouped[value]),
        }
        for value in sorted(grouped)
    ]


def _group_memory_refs(cards: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        _drop_empty(
            {
                "memory_id": _text(card.get("memory_id")),
                "status": _publication_route_memory_review_state(card),
                "route_family": _text(card.get("route_family")),
                "stage_applicability": _text_list(card.get("stage_applicability")),
                "source_receipt_ref": _text(card.get("source_receipt_ref")),
            }
        )
        for card in cards
        if _text(card.get("memory_id"))
    ]


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


def _publication_route_memory_opl_aion_receipt_inventory(*, pack_root: Path) -> dict[str, Any]:
    migration_receipts = [
        _receipt_inventory_entry(path=path, receipt_kind="migration_receipt")
        for path in sorted((pack_root / "migration_receipts").glob("*.json"))
    ]
    writeback_receipts = [
        _receipt_inventory_entry(path=path, receipt_kind="writeback_receipt")
        for path in sorted((pack_root / "writeback_receipts").glob("*.json"))
    ]
    receipts = [*migration_receipts, *writeback_receipts]
    return {
        "surface": "publication_route_memory_receipt_inventory",
        "read_only": True,
        "consumer": "OPL/Aion",
        "body_included": False,
        "receipt_count": len(receipts),
        "receipts": receipts,
        "display_policy": {
            "projection_owner": "MedAutoScience",
            "display_role": "receipt_ref_only",
            "can_read_memory_body": False,
            "can_write_memory_body": False,
            "can_score_winning_route": False,
            "can_authorize_publication_quality": False,
        },
    }


def _receipt_inventory_entry(*, path: Path, receipt_kind: str) -> dict[str, Any]:
    payload = _read_json(path)
    return {
        "ref_kind": "publication_route_memory_receipt",
        "receipt_kind": receipt_kind,
        "ref": str(path),
        "study_id": _text(payload.get("study_id")),
        "stage": _text(payload.get("stage")),
        "receipt_status": _text(payload.get("status")) or ("missing" if not path.exists() else "unknown"),
        "reason": _receipt_reason(payload),
        "freshness": _receipt_freshness(path),
        "accepted_refs": _receipt_accepted_refs(payload),
        "rejected_refs": _receipt_rejected_refs(payload),
        "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
        "body_included": False,
        "authority_boundary": "read_only_display_not_mas_truth_authority",
    }


def _receipt_reason(payload: Mapping[str, Any]) -> str:
    typed_blockers = _mapping_list(payload.get("typed_blockers"))
    if typed_blockers:
        return _text(typed_blockers[0].get("reason")) or _text(typed_blockers[0].get("blocker_id"))
    return _text(payload.get("reason"))


def _receipt_freshness(path: Path) -> dict[str, Any]:
    stat = path.stat() if path.exists() else None
    return {
        "exists": path.exists(),
        "mtime_epoch": stat.st_mtime if stat is not None else None,
        "size_bytes": stat.st_size if stat is not None else 0,
    }


def _receipt_accepted_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    accepted_writes = _mapping_list(payload.get("accepted_writes"))
    if accepted_writes:
        return [
            {
                "write_id": _text(item.get("write_id")),
                "memory_id": _memory_id_for_write(item),
                "destination": _text(item.get("destination")),
                "owner_target": _text(item.get("owner_target")),
                "reason": "",
                "status": "accepted",
            }
            for item in accepted_writes
            if _text(item.get("destination")) == "workspace_research_memory_proposal"
        ]
    return [
        {
            "memory_id": memory_id,
            "reason": "",
            "status": "accepted",
        }
        for memory_id in _text_list(payload.get("accepted_memory_ids"))
    ]


def _receipt_rejected_refs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    rejected_writes = _mapping_list(payload.get("rejected_writes"))
    rejected_cards = _mapping_list(payload.get("rejected_cards"))
    refs = [
        _drop_empty(
            {
                "write_id": _text(item.get("write_id")),
                "destination": _text(item.get("destination")),
                "owner_target": _text(item.get("owner_target")),
                "reason": _text(item.get("reason")),
                "status": "rejected",
            }
        )
        for item in rejected_writes
    ]
    refs.extend(
        _drop_empty(
            {
                "memory_id": _text(item.get("memory_id")),
                "reason": _text(item.get("reason")),
                "status": "rejected",
            }
        )
        for item in rejected_cards
    )
    return refs


def _memory_id_for_write(write: Mapping[str, Any]) -> str:
    payload = write.get("payload") if isinstance(write.get("payload"), Mapping) else {}
    if isinstance(payload, Mapping) and _text(payload.get("memory_id")):
        return _text(payload.get("memory_id"))
    write_id = _text(write.get("write_id"))
    return f"publication_route_memory_writeback__{_safe_key(write_id)}" if write_id else ""


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


def _drop_empty(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if value is not None and value != "" and value != []
    }


def _safe_key(key: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in key)[:180]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


__all__ = ["build_publication_route_memory_inventory"]
