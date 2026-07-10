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
from med_autoscience.workspace_paths import PUBLICATION_ROUTE_MEMORY_RELPATH


PUBLICATION_ROUTE_MEMORY_ROOT = PUBLICATION_ROUTE_MEMORY_RELPATH
OPL_MEMORY_LIFECYCLE_OWNER_REF = (
    "one-person-lab:src/modules/workspace/workspace-artifact-lifecycle.ts"
)
OPL_MEMORY_EVIDENCE_LEDGER_OWNER_REF = (
    "one-person-lab:src/modules/ledger/memory-artifact-lifecycle-evidence-ledger.ts"
)
MEMORY_DESCRIPTOR_REF = "contracts/memory_descriptor.json#/workspace_apply_surface"


def build_publication_route_memory_inventory(
    *,
    workspace_root: Path,
    stage: str | None = None,
    route_family_tags: Sequence[str] | None = None,
    statuses: Sequence[str] | None = None,
    include_card_body: bool = False,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    pack_path = resolved_workspace_root / PUBLICATION_ROUTE_MEMORY_ROOT / "memory_pack.json"
    cards = _mapping_list(_read_json(pack_path).get("cards"))
    resolved_stage = _validate_publication_route_memory_stage(stage) if _text(stage) else ""
    route_tags = set(_text_list(route_family_tags or ()))
    status_filter = set(_text_list(statuses or ()))
    filtered_cards = [
        card
        for card in cards
        if _card_matches(
            card=card,
            stage=resolved_stage,
            route_family_tags=route_tags,
            statuses=status_filter,
        )
    ]
    return {
        "surface": "publication_route_memory_inventory",
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if pack_path.is_file() else "missing",
        "read_only": True,
        "body_included": bool(include_card_body),
        "memory_pack_ref": str(pack_path),
        "memory_descriptor_ref": MEMORY_DESCRIPTOR_REF,
        "card_count_total": len(cards),
        "card_count_filtered": len(filtered_cards),
        "filters": {
            "stage": resolved_stage or None,
            "route_family": sorted(route_tags),
            "status": sorted(status_filter),
        },
        "cards": [_inventory_card(card, include_body=include_card_body) for card in filtered_cards],
        "review_summary": _review_summary(filtered_cards),
        "opl_transport": {
            "memory_lifecycle_owner_ref": OPL_MEMORY_LIFECYCLE_OWNER_REF,
            "receipt_ledger_owner_ref": OPL_MEMORY_EVIDENCE_LEDGER_OWNER_REF,
            "mas_locates_or_groups_generic_receipts": False,
            "mas_materializes_operator_workbench": False,
        },
        "authority_boundary": {
            **authority_boundary(),
            "memory_body_owner": "MedAutoScience",
            "memory_accept_reject_owner": "MedAutoScience",
            "generic_locator_transport_owner": "one-person-lab",
        },
    }


def _card_matches(
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
    return not statuses or _text(card.get("status")) in statuses


def _inventory_card(card: Mapping[str, Any], *, include_body: bool) -> dict[str, Any]:
    inventory_card = {
        "memory_id": _text(card.get("memory_id")),
        "status": _text(card.get("status")),
        "review_state": _review_state(card),
        "route_family": _text(card.get("route_family")),
        "stage_applicability": _text_list(card.get("stage_applicability")),
        "title": _text(card.get("title")),
        "source_receipt_ref": _text(card.get("source_receipt_ref")),
        "source_refs": _mapping_list(card.get("source_refs")),
        "authority_boundary": _text(card.get("authority_boundary"))
        or "context_only_not_publication_authority",
    }
    if include_body:
        for field in (
            "prose_summary",
            "claim_boundary",
        ):
            inventory_card[field] = _text(card.get(field))
        for field in (
            "best_fit",
            "poor_fit",
            "minimum_evidence_package",
            "analysis_pattern",
            "table_figure_pattern",
            "reviewer_risks",
            "pivot_or_stop_rules",
            "example_signals",
            "failure_modes",
        ):
            inventory_card[field] = _text_list(card.get(field))
        inventory_card["codex_stage_guidance"] = _mapping(card.get("codex_stage_guidance"))
    return inventory_card


def _review_summary(cards: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    states = [_review_state(card) for card in cards]
    return {
        "surface": "publication_route_memory_review_summary",
        "card_count": len(cards),
        "active_count": states.count("active"),
        "stale_count": states.count("stale"),
        "deprecated_count": states.count("deprecated"),
        "needs_review_count": sum(state in {"stale", "deprecated"} for state in states),
        "stale_or_deprecated_refs": [
            _text(card.get("memory_id"))
            for card in cards
            if _review_state(card) in {"stale", "deprecated"}
        ],
        "authority_boundary": "domain_review_signal_not_publication_authority",
    }


def _review_state(card: Mapping[str, Any]) -> str:
    status = _text(card.get("status")).lower().replace("-", "_")
    if status in {"deprecated", "deprecated_seed", "retired", "retired_seed"}:
        return "deprecated"
    if status in {"stale", "stale_seed", "needs_review", "review_needed"}:
        return "stale"
    return "active"


def _validate_publication_route_memory_stage(stage: str | None) -> str:
    resolved = _text(stage)
    if resolved not in PUBLICATION_ROUTE_MEMORY_STAGES:
        raise ValueError(f"unsupported publication route memory stage: {resolved}")
    return resolved


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_text(item) for item in value if _text(item)]


__all__ = ["build_publication_route_memory_inventory"]
