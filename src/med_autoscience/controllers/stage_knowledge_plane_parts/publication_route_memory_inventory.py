from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers.body_free_evidence_packets import (
    build_body_free_evidence_packet,
)
from med_autoscience.stage_knowledge_contract import (
    PUBLICATION_ROUTE_MEMORY_STAGES,
    SCHEMA_VERSION,
    authority_boundary,
)
from med_autoscience.workspace_paths import PUBLICATION_ROUTE_MEMORY_RELPATH


PUBLICATION_ROUTE_MEMORY_ROOT = PUBLICATION_ROUTE_MEMORY_RELPATH


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


def build_publication_strategy_memory_workbench(
    *,
    workspace_root: Path,
    stage: str | None = None,
    route_family_tags: Sequence[str] | None = None,
    statuses: Sequence[str] | None = None,
    include_card_body: bool = False,
) -> dict[str, Any]:
    inventory = build_publication_route_memory_inventory(
        workspace_root=workspace_root,
        stage=stage,
        route_family_tags=route_family_tags,
        statuses=statuses,
        include_card_body=include_card_body,
    )
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    pack_root = resolved_workspace_root / PUBLICATION_ROUTE_MEMORY_ROOT
    pack_path = pack_root / "memory_pack.json"
    pack_cards = _mapping_list(_read_json(pack_path).get("cards"))
    filtered_cards = [
        card
        for card in pack_cards
        if _publication_route_card_matches(
            card=card,
            stage=_validate_publication_route_memory_stage(stage) if _text(stage) else "",
            route_family_tags=set(_text_list(list(route_family_tags or []))),
            statuses=set(_text_list(list(statuses or []))),
        )
    ]
    coverage = _publication_strategy_memory_workspace_coverage(
        workspace_root=resolved_workspace_root,
        pack_root=pack_root,
        pack_path=pack_path,
        pack_cards=pack_cards,
        filtered_count=len(filtered_cards),
        receipt_summary=inventory["receipt_summary"],
    )
    maintenance_actions = _publication_strategy_memory_maintenance_actions(
        inventory=inventory,
        coverage=coverage,
    )
    return {
        "surface_kind": "publication_strategy_memory_workbench",
        "surface": "publication_strategy_memory_workbench",
        "schema_version": SCHEMA_VERSION,
        "status": inventory["status"],
        "maintenance_status": "needs_review" if maintenance_actions else "clear",
        "read_only": True,
        "body_included": bool(include_card_body),
        "workspace_root": str(resolved_workspace_root),
        "memory_pack_ref": inventory["memory_pack_ref"],
        "card_count_total": inventory["card_count_total"],
        "card_count_filtered": inventory["card_count_filtered"],
        "filters": inventory["filters"],
        "cards": inventory["cards"],
        "operator_grouping": inventory["operator_grouping"],
        "review_summary": inventory["review_summary"],
        "receipt_summary": inventory["receipt_summary"],
        "opl_aion_receipt_inventory": inventory["opl_aion_receipt_inventory"],
        "locator_refs": inventory["locator_refs"],
        "workspace_coverage": coverage,
        "maintenance_actions": maintenance_actions,
        "maintainer_review_queue": {
            "surface": "publication_strategy_memory_maintainer_review_queue",
            "read_only": True,
            "item_count": len(maintenance_actions),
            "items": maintenance_actions,
            "authority_boundary": "review_queue_only_not_accept_reject_or_memory_body_authority",
        },
        "authority_boundary": _publication_strategy_memory_workbench_authority_boundary(),
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


def _publication_strategy_memory_workspace_coverage(
    *,
    workspace_root: Path,
    pack_root: Path,
    pack_path: Path,
    pack_cards: Sequence[Mapping[str, Any]],
    filtered_count: int,
    receipt_summary: Mapping[str, Any],
) -> dict[str, Any]:
    writeback_proposal = pack_root / "writeback_proposals" / "stage_memory_updates.jsonl"
    migration_receipt_count = int(receipt_summary.get("migration_receipt_count") or 0)
    writeback_receipt_count = int(receipt_summary.get("writeback_receipt_count") or 0)
    writeback_proposal_exists = bool(receipt_summary.get("writeback_proposal_exists"))
    return {
        "surface": "publication_strategy_memory_workspace_coverage",
        "read_only": True,
        "body_included": False,
        "workspace_root": str(workspace_root),
        "pack_present": pack_path.exists(),
        "pack_readable": bool(pack_cards) or not pack_path.exists(),
        "memory_pack_ref": str(pack_path),
        "seed_card_count": sum(1 for card in pack_cards if _is_seed_memory_card(card)),
        "card_count_total": len(pack_cards),
        "filtered_count": filtered_count,
        "migration_receipts": {
            "present": migration_receipt_count > 0,
            "count": migration_receipt_count,
            "refs": list(receipt_summary.get("migration_receipt_refs") or []),
        },
        "writeback_proposals": {
            "present": writeback_proposal_exists,
            "count": _jsonl_entry_count(writeback_proposal) if writeback_proposal_exists else 0,
            "ref": str(writeback_proposal),
        },
        "writeback_receipts": {
            "present": writeback_receipt_count > 0,
            "count": writeback_receipt_count,
            "refs": list(receipt_summary.get("writeback_receipt_refs") or []),
        },
        "receipt_presence": {
            "migration": migration_receipt_count > 0,
            "writeback": writeback_receipt_count > 0,
        },
        "authority_boundary": "coverage_counts_only_not_memory_body_or_publication_authority",
    }


def _publication_strategy_memory_maintenance_actions(
    *,
    inventory: Mapping[str, Any],
    coverage: Mapping[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    locator_refs = _mapping(inventory.get("locator_refs"))
    review_summary = _mapping(inventory.get("review_summary"))
    receipt_inventory = _mapping(inventory.get("opl_aion_receipt_inventory"))
    receipt_review_summary = _mapping(receipt_inventory.get("receipt_review_summary"))

    if not bool(coverage.get("pack_present")):
        actions.append(
            _maintenance_action(
                action_id="memory_pack_missing",
                reason="missing_publication_route_memory_pack",
                refs=[_text(locator_refs.get("memory_pack"))],
            )
        )

    if int(review_summary.get("needs_review_count") or 0) > 0:
        actions.append(
            _maintenance_action(
                action_id="stale_or_deprecated_cards",
                reason="stale_or_deprecated_publication_strategy_memory_refs",
                refs=_text_list(review_summary.get("stale_or_deprecated_refs")),
                counts={
                    "stale": int(review_summary.get("stale_count") or 0),
                    "deprecated": int(review_summary.get("deprecated_count") or 0),
                },
            )
        )

    migration_receipts = _mapping(coverage.get("migration_receipts"))
    if bool(coverage.get("pack_present")) and not bool(migration_receipts.get("present")):
        actions.append(
            _maintenance_action(
                action_id="migration_receipt_missing",
                reason="memory_pack_has_no_migration_receipt_ref",
                refs=[_text(locator_refs.get("migration_receipts"))],
            )
        )

    writeback_proposals = _mapping(coverage.get("writeback_proposals"))
    writeback_receipts = _mapping(coverage.get("writeback_receipts"))
    if bool(writeback_proposals.get("present")) and not bool(writeback_receipts.get("present")):
        actions.append(
            _maintenance_action(
                action_id="writeback_proposal_without_receipt",
                reason="writeback_proposals_need_maintainer_receipt_review",
                refs=[_text(writeback_proposals.get("ref"))],
                counts={"proposal_count": int(writeback_proposals.get("count") or 0)},
            )
        )

    rejected_count = int(receipt_review_summary.get("rejected_writeback_ref_count") or 0)
    blocked_count = int(receipt_review_summary.get("blocked_writeback_ref_count") or 0)
    if rejected_count or blocked_count:
        actions.append(
            _maintenance_action(
                action_id="rejected_or_blocked_writebacks",
                reason="writeback_receipt_refs_need_maintainer_review",
                refs=list(writeback_receipts.get("refs") or []),
                counts={"rejected": rejected_count, "blocked": blocked_count},
            )
        )

    if bool(coverage.get("pack_present")) and int(coverage.get("card_count_total") or 0) == 0:
        actions.append(
            _maintenance_action(
                action_id="memory_pack_empty",
                reason="publication_strategy_memory_pack_has_no_cards",
                refs=[_text(locator_refs.get("memory_pack"))],
            )
        )

    return actions


def _maintenance_action(
    *,
    action_id: str,
    reason: str,
    refs: Sequence[str],
    counts: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    payload = {
        "action_id": action_id,
        "kind": "maintainer_review_hint",
        "reason": reason,
        "refs": _text_list(list(refs)),
        "read_only": True,
        "can_apply": False,
        "can_accept_or_reject_writeback": False,
        "authority_boundary": "maintainer_hint_only_not_memory_or_publication_authority",
    }
    if counts:
        payload["counts"] = dict(counts)
    return _drop_empty(payload)


def _is_seed_memory_card(card: Mapping[str, Any]) -> bool:
    memory_id = _text(card.get("memory_id"))
    status = _text(card.get("status"))
    return memory_id.startswith("publication_route_memory_seed__") or status.endswith("_seed")


def _jsonl_entry_count(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _publication_strategy_memory_workbench_authority_boundary() -> dict[str, Any]:
    boundary = authority_boundary()
    boundary.update(
        {
            "role": "publication_strategy_memory_maintainer_workbench",
            "read_only": True,
            "can_read_memory_body_by_default": False,
            "can_write_memory_body": False,
            "can_accept_or_reject_writeback": False,
            "can_score_winning_route": False,
            "can_run_route_matching_engine": False,
            "can_enforce_evidence_gate": False,
            "can_control_programmatic_recipe": False,
        }
    )
    return boundary


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
        "by_receipt_status": _group_receipts_by_value(
            receipts,
            values_for_receipt=lambda receipt: [_text(receipt.get("receipt_status"))],
            group_key="receipt_status",
        ),
        "by_stage": _group_receipts_by_value(
            receipts,
            values_for_receipt=lambda receipt: [_text(receipt.get("stage"))],
            group_key="stage",
        ),
        "by_route_family": _group_receipts_by_value(
            receipts,
            values_for_receipt=lambda receipt: _text_list(receipt.get("route_family_tags")),
            group_key="route_family",
        ),
        "receipt_review_summary": _receipt_review_summary(receipts),
        "display_policy": {
            "projection_owner": "MedAutoScience",
            "display_role": "receipt_ref_only",
            "can_read_memory_body": False,
            "can_write_memory_body": False,
            "can_accept_or_reject_writeback": False,
            "can_score_winning_route": False,
            "can_authorize_publication_quality": False,
        },
    }


def _receipt_inventory_entry(*, path: Path, receipt_kind: str) -> dict[str, Any]:
    payload = _read_json(path)
    source_receipt_ref = _receipt_source_receipt_ref(payload=payload, path=path)
    writeback_receipt_ref = _receipt_writeback_receipt_ref(payload=payload, path=path)
    accepted_writeback_refs = _receipt_writeback_refs(
        payload=payload,
        status="accepted",
        source_receipt_ref=source_receipt_ref,
        writeback_receipt_ref=writeback_receipt_ref,
    )
    rejected_writeback_refs = _receipt_writeback_refs(
        payload=payload,
        status="rejected",
        source_receipt_ref=source_receipt_ref,
        writeback_receipt_ref=writeback_receipt_ref,
    )
    writeback_refs = [*accepted_writeback_refs, *rejected_writeback_refs]
    blocked_writeback_refs = _receipt_blocked_refs(
        payload=payload,
        source_receipt_ref=source_receipt_ref,
        writeback_receipt_ref=writeback_receipt_ref,
    )
    route_back_refs = [ref for ref in writeback_refs if _is_route_back_ref(ref)]
    route_family_tags = _receipt_route_family_tags(
        payload=payload,
        writeback_refs=writeback_refs,
        receipt_kind=receipt_kind,
    )
    return {
        "ref_kind": "publication_route_memory_receipt",
        "receipt_kind": receipt_kind,
        "ref": str(path),
        "idempotency_key": _text(payload.get("idempotency_key")),
        "study_id": _text(payload.get("study_id")),
        "stage": _text(payload.get("stage")),
        "route_family": route_family_tags[0] if route_family_tags else "",
        "route_family_tags": route_family_tags,
        "source_receipt_ref": source_receipt_ref,
        "writeback_receipt_ref": writeback_receipt_ref,
        "receipt_status": _text(payload.get("status")) or ("missing" if not path.exists() else "unknown"),
        "reason": _receipt_reason(payload),
        "freshness": _receipt_freshness(path),
        "accepted_refs": _receipt_accepted_refs(payload),
        "rejected_refs": _receipt_rejected_refs(payload),
        "accepted_writeback_refs": accepted_writeback_refs,
        "rejected_writeback_refs": rejected_writeback_refs,
        "blocked_writeback_refs": blocked_writeback_refs,
        "route_back_refs": route_back_refs,
        "writeback_refs": writeback_refs,
        "body_free_evidence_packets": _receipt_body_free_packets(
            path=path,
            accepted_refs=accepted_writeback_refs,
            rejected_refs=rejected_writeback_refs,
            blocked_refs=blocked_writeback_refs,
        ),
        "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
        "body_included": False,
        "authority_boundary": "read_only_display_not_mas_truth_authority",
    }


def _receipt_reason(payload: Mapping[str, Any]) -> str:
    typed_blockers = _mapping_list(payload.get("typed_blockers"))
    if typed_blockers:
        return _text(typed_blockers[0].get("reason")) or _text(typed_blockers[0].get("blocker_id"))
    rejected_writes = _mapping_list(payload.get("rejected_writes"))
    if rejected_writes:
        return _text(rejected_writes[0].get("reason"))
    rejected_cards = _mapping_list(payload.get("rejected_cards"))
    if rejected_cards:
        return _text(rejected_cards[0].get("reason"))
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


def _receipt_source_receipt_ref(*, payload: Mapping[str, Any], path: Path) -> str:
    receipt_refs = _text_list(payload.get("receipt_refs"))
    if receipt_refs:
        return receipt_refs[0]
    return _text(payload.get("receipt_ref")) or str(path)


def _receipt_writeback_receipt_ref(*, payload: Mapping[str, Any], path: Path) -> str:
    receipt_refs = _text_list(payload.get("receipt_refs"))
    if len(receipt_refs) >= 2:
        return receipt_refs[1]
    if _mapping_list(payload.get("accepted_writes")) or _mapping_list(payload.get("rejected_writes")):
        return str(path)
    return ""


def _receipt_writeback_refs(
    *,
    payload: Mapping[str, Any],
    status: str,
    source_receipt_ref: str,
    writeback_receipt_ref: str,
) -> list[dict[str, Any]]:
    writes = _mapping_list(payload.get("accepted_writes" if status == "accepted" else "rejected_writes"))
    receipt_status = _text(payload.get("status"))
    refs: list[dict[str, Any]] = []
    for write in writes:
        payload_body = _mapping(write.get("payload"))
        destination = _text(write.get("destination"))
        if destination != "workspace_research_memory_proposal":
            continue
        ref = _drop_empty(
            {
                "write_id": _text(write.get("write_id")),
                "memory_id": _memory_id_for_write(write) if status == "accepted" else "",
                "route_family": _text(payload_body.get("route_family")),
                "stage_applicability": _text_list(payload_body.get("stage_applicability")),
                "destination": destination,
                "owner_target": _text(write.get("owner_target")),
                "proposal_ref": _text(write.get("proposal_ref")),
                "receipt_ref": _text(write.get("receipt_ref")),
                "source_receipt_ref": source_receipt_ref,
                "writeback_receipt_ref": writeback_receipt_ref,
                "status": status,
                "receipt_status": receipt_status,
                "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
            }
        )
        ref["reason"] = _text(write.get("reason"))
        refs.append(ref)
    return refs


def _receipt_blocked_refs(
    *,
    payload: Mapping[str, Any],
    source_receipt_ref: str,
    writeback_receipt_ref: str,
) -> list[dict[str, Any]]:
    receipt_status = _text(payload.get("status"))
    if receipt_status != "blocked":
        return []
    refs: list[dict[str, Any]] = []
    for blocker in _mapping_list(payload.get("typed_blockers")):
        refs.append(
            _drop_empty(
                {
                    "blocker_id": _text(blocker.get("blocker_id")),
                    "reason": _text(blocker.get("reason")),
                    "source_receipt_ref": source_receipt_ref,
                    "writeback_receipt_ref": writeback_receipt_ref,
                    "status": "blocked",
                    "receipt_status": receipt_status,
                    "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
                }
            )
        )
    return refs


def _receipt_body_free_packets(
    *,
    path: Path,
    accepted_refs: Sequence[Mapping[str, Any]],
    rejected_refs: Sequence[Mapping[str, Any]],
    blocked_refs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    freshness = _receipt_freshness(path)
    packets: list[dict[str, Any]] = []
    for status, refs, role in (
        ("accepted", accepted_refs, "accepted_memory_receipt_ref"),
        ("rejected", rejected_refs, "rejected_memory_receipt_ref"),
        ("blocked", blocked_refs, "blocked_memory_receipt_ref"),
    ):
        for index, ref_payload in enumerate(refs):
            ref = _text(ref_payload.get("writeback_receipt_ref")) or _text(ref_payload.get("source_receipt_ref")) or str(path)
            ref_id = (
                _text(ref_payload.get("write_id"))
                or _text(ref_payload.get("memory_id"))
                or _text(ref_payload.get("blocker_id"))
                or str(index)
            )
            packets.append(
                build_body_free_evidence_packet(
                    ref=f"{ref}#{status}:{_safe_key(ref_id)}",
                    role=role,
                    owner="MedAutoScience",
                    receipt_id=f"publication-route-memory:{status}:{_safe_key(ref_id)}",
                    freshness=freshness,
                )
            )
    return packets


def _receipt_route_family_tags(
    *,
    payload: Mapping[str, Any],
    writeback_refs: Sequence[Mapping[str, Any]],
    receipt_kind: str,
) -> list[str]:
    route_families = [
        _text(ref.get("route_family"))
        for ref in writeback_refs
        if _text(ref.get("route_family"))
    ]
    for write in [*_mapping_list(payload.get("accepted_writes")), *_mapping_list(payload.get("rejected_writes"))]:
        payload_body = _mapping(write.get("payload"))
        if _text(payload_body.get("route_family")):
            route_families.append(_text(payload_body.get("route_family")))
    if not route_families and receipt_kind == "migration_receipt":
        route_families.append("seed_migration")
    return _dedupe_text(route_families)


def _is_route_back_ref(ref: Mapping[str, Any]) -> bool:
    route_family = _text(ref.get("route_family"))
    if route_family.startswith("route_back"):
        return True
    return "route_back" in route_family


def _memory_id_for_write(write: Mapping[str, Any]) -> str:
    payload = write.get("payload") if isinstance(write.get("payload"), Mapping) else {}
    if isinstance(payload, Mapping) and _text(payload.get("memory_id")):
        return _text(payload.get("memory_id"))
    write_id = _text(write.get("write_id"))
    return f"publication_route_memory_writeback__{_safe_key(write_id)}" if write_id else ""


def _group_receipts_by_value(
    receipts: Sequence[Mapping[str, Any]],
    *,
    values_for_receipt,
    group_key: str,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for receipt in receipts:
        values = [value for value in values_for_receipt(receipt) if value]
        for value in values or ["unclassified"]:
            grouped.setdefault(value, []).append(receipt)
    return [
        {
            group_key: value,
            "receipt_refs": _group_receipt_refs(grouped[value]),
            "receipt_count": len(grouped[value]),
        }
        for value in sorted(grouped)
    ]


def _group_receipt_refs(receipts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        _drop_empty(
            {
                "ref": _text(receipt.get("ref")),
                "receipt_kind": _text(receipt.get("receipt_kind")),
                "receipt_status": _text(receipt.get("receipt_status")),
                "reason": _text(receipt.get("reason")),
                "stage": _text(receipt.get("stage")),
                "route_family": _text(receipt.get("route_family")),
                "source_receipt_ref": _text(receipt.get("source_receipt_ref")),
                "writeback_receipt_ref": _text(receipt.get("writeback_receipt_ref")),
                "accepted_writeback_ref_count": len(_mapping_list(receipt.get("accepted_writeback_refs"))),
                "rejected_writeback_ref_count": len(_mapping_list(receipt.get("rejected_writeback_refs"))),
                "blocked_writeback_ref_count": len(_mapping_list(receipt.get("blocked_writeback_refs"))),
                "route_back_ref_count": len(_mapping_list(receipt.get("route_back_refs"))),
                "body_included": False,
                "authority_boundary": "ref_only_not_memory_body_or_writeback_authority",
            }
        )
        for receipt in receipts
    ]


def _receipt_review_summary(receipts: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    accepted_writeback_ref_count = sum(
        len(_mapping_list(receipt.get("accepted_writeback_refs")))
        for receipt in receipts
    )
    rejected_writeback_ref_count = sum(
        len(_mapping_list(receipt.get("rejected_writeback_refs")))
        for receipt in receipts
    )
    route_back_ref_count = sum(
        len(_mapping_list(receipt.get("route_back_refs")))
        for receipt in receipts
    )
    blocked_writeback_ref_count = sum(
        len(_mapping_list(receipt.get("blocked_writeback_refs")))
        for receipt in receipts
    )
    return {
        "surface": "publication_route_memory_receipt_review_summary",
        "receipt_count": len(receipts),
        "accepted_writeback_ref_count": accepted_writeback_ref_count,
        "rejected_writeback_ref_count": rejected_writeback_ref_count,
        "blocked_writeback_ref_count": blocked_writeback_ref_count,
        "route_back_ref_count": route_back_ref_count,
        "needs_maintainer_review_count": rejected_writeback_ref_count,
        "body_included": False,
        "authority_boundary": "review_signal_only_not_memory_body_or_writeback_authority",
    }


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


def _dedupe_text(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys([item for item in items if item]))


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


__all__ = [
    "build_publication_route_memory_inventory",
    "build_publication_strategy_memory_workbench",
]
