from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_cards import (
    normalize_publication_route_card,
    publication_route_cards_from_markdown,
    publication_seed_blockers,
)
from med_autoscience.stage_knowledge_contract import (
    PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE,
    PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
    SCHEMA_VERSION,
    authority_boundary,
)


PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF = Path(
    "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
)
PUBLICATION_ROUTE_MEMORY_LIBRARY_REF = Path("docs/policies/study-workflow/publication_route_memory_library.md")


def apply_publication_route_memory_seed_fixture(
    *,
    workspace_root: Path,
    seed_fixture_path: Path,
    pack_path: Path,
    receipt_path_for_idempotency_key,
    seed_library_path: Path | None = None,
    apply: bool = True,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_fixture_path = Path(seed_fixture_path).expanduser().resolve()
    fixture = _read_json(resolved_fixture_path)
    resolved_library_path = _resolve_publication_route_seed_library_path(
        fixture=fixture,
        fixture_path=resolved_fixture_path,
        seed_library_path=seed_library_path,
    )
    seed_cards = publication_route_cards_from_markdown(resolved_library_path.read_text(encoding="utf-8"))
    source_fingerprint = _fingerprint(
        {
            "fixture_path": str(resolved_fixture_path),
            "library_path": str(resolved_library_path),
            "seed_cards": seed_cards,
        }
    )
    idempotency_key = f"publication_route_memory_seed_apply:{source_fingerprint}"
    receipt_path = receipt_path_for_idempotency_key(
        workspace_root=resolved_workspace_root,
        idempotency_key=idempotency_key,
    )
    receipt_ref = str(receipt_path)
    if apply and receipt_path.exists():
        existing = _read_json(receipt_path)
        if existing:
            return {**existing, "idempotent_replay": True, "receipt_ref": str(receipt_path)}

    typed_blockers = publication_seed_blockers(fixture=fixture, seed_cards=seed_cards)
    accepted_cards = [] if typed_blockers else [normalize_publication_route_card(card) for card in seed_cards]
    receipt = {
        "surface": PUBLICATION_ROUTE_MEMORY_APPLY_RECEIPT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": "workspace",
        "stage": "all",
        "memory_family": "publication_route_memory",
        "status": "blocked" if typed_blockers else ("applied" if apply else "dry_run"),
        "apply": apply,
        "input_refs": [str(resolved_fixture_path)],
        "source_refs": [
            {
                "ref_kind": "repo_path",
                "ref": str(PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF),
                "resolved_path": str(resolved_fixture_path),
                "role": "repo_source_seed_index",
            },
            {
                "ref_kind": "repo_path",
                "ref": str(PUBLICATION_ROUTE_MEMORY_LIBRARY_REF),
                "resolved_path": str(resolved_library_path),
                "role": "canonical_markdown_memory_body",
            },
        ],
        "canonical_body_ref": str(resolved_library_path),
        "source_fingerprint": source_fingerprint,
        "idempotency_key": idempotency_key,
        "accepted_memory_ids": [card["memory_id"] for card in accepted_cards],
        "rejected_cards": [],
        "typed_blockers": typed_blockers,
        "memory_pack_ref": str(pack_path),
        "receipt_ref": receipt_ref,
        "authority_boundary": authority_boundary(),
    }
    if apply:
        if not typed_blockers:
            pack = _publication_route_memory_pack(cards=accepted_cards, receipt=receipt)
            receipt["memory_pack_fingerprint"] = pack["source_fingerprint"]
            _write_json(pack_path, pack)
        _write_json(receipt_path, receipt)
    return {**receipt, "receipt_ref": str(receipt_path)}


def default_seed_fixture_path() -> Path:
    return Path(__file__).resolve().parents[4] / PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF


def _resolve_publication_route_seed_library_path(
    *,
    fixture: Mapping[str, Any],
    fixture_path: Path,
    seed_library_path: Path | None,
) -> Path:
    if seed_library_path is not None:
        path = Path(seed_library_path).expanduser()
        return path.resolve()
    canonical_ref = _text(fixture.get("canonical_body_ref"))
    if not canonical_ref:
        raise ValueError("publication route seed fixture must point to a canonical Markdown body")
    candidate = Path(canonical_ref).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    from_fixture = (fixture_path.parent / candidate).resolve()
    if from_fixture.exists():
        return from_fixture
    repo_root = Path(__file__).resolve().parents[4]
    return (repo_root / candidate).resolve()


def _publication_route_memory_pack(
    *,
    cards: Sequence[Mapping[str, Any]],
    receipt: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_ref = _text(receipt.get("receipt_ref"))
    normalized_cards = [
        {
            **dict(card),
            "source_receipt_ref": receipt_ref,
            "authority_boundary": "context_only_not_publication_authority",
        }
        for card in cards
    ]
    return {
        "surface": PUBLICATION_ROUTE_MEMORY_PACK_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": "workspace",
        "stage": "all",
        "memory_family": "publication_route_memory",
        "owner": "MedAutoScience",
        "state": "workspace_runtime_memory_pack",
        "input_refs": [receipt_ref] if receipt_ref else [],
        "cards": normalized_cards,
        "card_count": len(normalized_cards),
        "source_apply_receipt_ref": receipt_ref,
        "idempotency_key": _text(receipt.get("idempotency_key"))
        or f"publication_route_memory_pack:{_fingerprint(normalized_cards)}",
        "source_fingerprint": _fingerprint(normalized_cards),
        "authority_boundary": authority_boundary(),
    }


def _text(value: object) -> str:
    return str(value or "").strip()


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


__all__ = [
    "PUBLICATION_ROUTE_MEMORY_LIBRARY_REF",
    "PUBLICATION_ROUTE_MEMORY_SEED_FIXTURE_REF",
    "apply_publication_route_memory_seed_fixture",
    "default_seed_fixture_path",
]
