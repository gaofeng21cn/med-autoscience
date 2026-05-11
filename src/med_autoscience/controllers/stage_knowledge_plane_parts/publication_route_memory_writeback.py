from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.stage_knowledge_contract import (
    PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
    SCHEMA_VERSION,
    authority_boundary,
)


DEFAULT_WRITEBACK_STAGE_APPLICABILITY = ("scout", "idea", "decision", "analysis-campaign", "review")


def sync_accepted_publication_route_memory_cards(
    *,
    receipt: Mapping[str, Any],
    pack_path: Path,
    receipt_ref: str,
    apply: bool,
) -> None:
    if not apply:
        return
    accepted_cards = [
        _publication_route_memory_card_from_write(write, receipt_ref=receipt_ref)
        for write in _mapping_list(receipt.get("accepted_writes"))
        if _text(write.get("destination")) == "workspace_research_memory_proposal"
    ]
    if not accepted_cards:
        return
    existing_pack = _read_json(pack_path)
    existing_cards = _mapping_list(existing_pack.get("cards"))
    by_memory_id = {_text(card.get("memory_id")): dict(card) for card in existing_cards if _text(card.get("memory_id"))}
    for card in accepted_cards:
        by_memory_id[card["memory_id"]] = {**by_memory_id.get(card["memory_id"], {}), **card}
    pack = _publication_route_memory_pack_from_cards(
        cards=list(by_memory_id.values()),
        input_refs=_dedupe_text([*_text_list(existing_pack.get("input_refs")), receipt_ref]),
        idempotency_key=_text(existing_pack.get("idempotency_key")),
    )
    _write_json(pack_path, pack)


def _publication_route_memory_card_from_write(write: Mapping[str, Any], *, receipt_ref: str) -> dict[str, Any]:
    payload = _mapping(write.get("payload"))
    write_id = _required_text("write_id", write.get("write_id"))
    return {
        "memory_id": f"publication_route_memory_writeback__{_safe_key(write_id)}",
        "status": _text(payload.get("status")) or "active",
        "route_family": _text(payload.get("route_family")) or "stage_memory_writeback",
        "stage_applicability": _text_list(payload.get("stage_applicability"))
        or list(DEFAULT_WRITEBACK_STAGE_APPLICABILITY),
        "title": _text(payload.get("title")) or _text(payload.get("lesson"))[:80] or write_id,
        "prose_summary": _text(payload.get("prose_summary")) or _text(payload.get("lesson")),
        "failure_modes": _text_list(payload.get("failure_modes")),
        "source_refs": _text_list(write.get("source_refs")) or _text_list(payload.get("source_refs")),
        "source_receipt_ref": receipt_ref,
        "authority_boundary": "context_only_not_publication_authority",
    }


def _publication_route_memory_pack_from_cards(
    *,
    cards: Sequence[Mapping[str, Any]],
    input_refs: Sequence[str],
    idempotency_key: str,
) -> dict[str, Any]:
    normalized_cards = [
        {
            **dict(card),
            "authority_boundary": _text(card.get("authority_boundary"))
            or "context_only_not_publication_authority",
        }
        for card in cards
    ]
    source_fingerprint = _fingerprint(normalized_cards)
    return {
        "surface": PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": "workspace",
        "stage": "all",
        "memory_family": "publication_route_memory",
        "owner": "MedAutoScience",
        "state": "workspace_runtime_memory_pack",
        "input_refs": list(input_refs),
        "cards": normalized_cards,
        "card_count": len(normalized_cards),
        "source_apply_receipt_ref": _text(input_refs[0]) if input_refs else "",
        "idempotency_key": idempotency_key or f"publication_route_memory_pack:{source_fingerprint}",
        "source_fingerprint": source_fingerprint,
        "authority_boundary": authority_boundary(),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe_text(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys([item for item in items if item]))


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _safe_key(key: str) -> str:
    return "".join(char if char.isalnum() or char in {"-", "_", "."} else "_" for char in key)[:180]


def _fingerprint(payload: object) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = ["sync_accepted_publication_route_memory_cards"]
