from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers.research_memory.publication_route_memory_seed import (
    apply_publication_route_memory_seed_fixture as _apply_seed_fixture,
    default_seed_fixture_path as _default_seed_fixture_path,
)
from med_autoscience.controllers.research_memory.publication_route_memory_writeback import (
    sync_accepted_publication_route_memory_cards,
)
from med_autoscience.controllers.research_memory.research_frontier_board import (
    adopt_frontier_route_back_terminal_decision,
    build_research_frontier_board,
    frontier_board_packet_fields,
)
from med_autoscience.research_memory_contract import (
    EXPLORATORY_STAGES,
    PUBLICATION_ROUTE_MEMORY_STAGES,
    SCHEMA_VERSION,
    STAGE_OBLIGATIONS,
    TYPED_CLOSEOUT_CATEGORIES,
    authority_boundary,
    research_memory_contract,
)
from med_autoscience.workspace_paths import PUBLICATION_ROUTE_MEMORY_RELPATH, publication_route_memory_root


PUBLICATION_ROUTE_MEMORY_ROOT = PUBLICATION_ROUTE_MEMORY_RELPATH
PUBLICATION_ROUTE_MEMORY_SELECTION_LIMIT = 3
PUBLICATION_STRATEGY_MEMORY_KIND = "publication_strategy_memory"
PUBLICATION_STRATEGY_MEMORY_USE_POLICY = {
    "memory_kind": PUBLICATION_STRATEGY_MEMORY_KIND,
    "compatible_memory_family": "publication_route_memory",
    "canonical_body_mode": "markdown_first",
    "stage_packet_role": "reference_only_prompt_context",
    "retrieval_scope": "small_stage_relevant_ref_set",
    "body_transport": "body_free_refs_by_default",
    "forbidden_roles": {
        "recipe_engine": False,
        "route_scorer": False,
        "evidence_gate": False,
        "controller_decision_source": False,
        "publication_quality_authority": False,
        "submission_readiness_authority": False,
        "memory_body_owner_for_opl": False,
    },
}


def publication_route_memory_pack_root(*, workspace_root: Path) -> Path:
    return publication_route_memory_root(Path(workspace_root))


def publication_route_memory_pack_path(*, workspace_root: Path) -> Path:
    return publication_route_memory_pack_root(workspace_root=workspace_root) / "memory_pack.json"


def publication_route_memory_apply_receipt_path(*, workspace_root: Path, idempotency_key: str) -> Path:
    return (
        publication_route_memory_pack_root(workspace_root=workspace_root)
        / "writeback_receipts"
        / f"{_safe_key(idempotency_key)}.json"
    )


def apply_publication_route_memory_seed_fixture(
    *,
    workspace_root: Path,
    seed_fixture_path: Path,
    seed_library_path: Path | None = None,
    apply: bool = True,
) -> dict[str, Any]:
    return _apply_seed_fixture(
        workspace_root=Path(workspace_root).expanduser().resolve(),
        seed_fixture_path=seed_fixture_path,
        seed_library_path=seed_library_path,
        pack_path=publication_route_memory_pack_path(workspace_root=workspace_root),
        receipt_path_for_idempotency_key=publication_route_memory_apply_receipt_path,
        apply=apply,
    )


def apply_publication_route_memory_seed_library(
    *,
    workspace_root: Path,
    seed_library_path: Path,
    apply: bool = True,
) -> dict[str, Any]:
    return apply_publication_route_memory_seed_fixture(
        workspace_root=workspace_root,
        seed_fixture_path=_default_seed_fixture_path(),
        seed_library_path=seed_library_path,
        apply=apply,
    )


def default_publication_route_memory_seed_fixture_path() -> Path:
    return _default_seed_fixture_path()


def publication_strategy_memory_use_policy() -> dict[str, Any]:
    return json.loads(json.dumps(PUBLICATION_STRATEGY_MEMORY_USE_POLICY, ensure_ascii=False))


def select_publication_route_memory_refs(
    *,
    workspace_root: Path,
    stage: str,
    route_family_tags: Sequence[str] | None = None,
    limit: int = PUBLICATION_ROUTE_MEMORY_SELECTION_LIMIT,
) -> list[dict[str, Any]]:
    resolved_stage = _validate_publication_route_memory_stage(stage)
    pack_path = publication_route_memory_pack_path(workspace_root=workspace_root)
    cards = _mapping_list(_read_json(pack_path).get("cards"))
    route_tags = set(_text_list(route_family_tags or []))
    selected: list[dict[str, Any]] = []
    for card in cards:
        route_family = _text(card.get("route_family"))
        if resolved_stage not in set(_text_list(card.get("stage_applicability"))):
            continue
        if route_tags and route_family not in route_tags:
            continue
        selected.append(
            {
                "ref_kind": "workspace_memory_card_ref",
                "memory_kind": PUBLICATION_STRATEGY_MEMORY_KIND,
                "use_policy": "reference_only_for_ai_reasoning",
                "memory_id": _text(card.get("memory_id")),
                "route_family": route_family,
                "title": _text(card.get("title")),
                "route_memory_summary": _text(card.get("prose_summary")),
                "stage_applicability": _text_list(card.get("stage_applicability")),
                "memory_pack_ref": str(pack_path),
                "source_receipt_ref": _text(card.get("source_receipt_ref")),
                "authority_boundary": "context_only_not_publication_authority",
            }
        )
        if len(selected) >= limit:
            break
    return selected


def render_publication_strategy_memory_prompt_block(refs: Sequence[Mapping[str, Any]]) -> str:
    lines = [
        "## Publication Strategy Memory",
        "",
        "Use these memories as reference context only; current evidence and owner gates remain authoritative.",
    ]
    if not refs:
        return "\n".join([*lines, "", "No stage-relevant publication strategy memory refs were retrieved."])
    lines.extend(["", "Retrieved refs:"])
    for ref in refs:
        title = _text(ref.get("title")) or _text(ref.get("memory_id"))
        lines.append(f"- {title}")
        if summary := _text(ref.get("route_memory_summary")):
            lines.append(f"  Summary: {summary}")
        if body_ref := _text(ref.get("memory_pack_ref")):
            lines.append(f"  Memory pack locator: {body_ref}")
    return "\n".join(lines)


def normalize_publication_route_memory_closeout(
    *,
    study_id: str,
    stage: str,
    closeout_payload: Mapping[str, Any],
) -> dict[str, Any]:
    resolved_stage = _validate_publication_route_memory_stage(stage)
    normalized = {
        category: _mapping_list(closeout_payload.get(category))
        for category in TYPED_CLOSEOUT_CATEGORIES
    }
    typed_blockers = _mapping_list(closeout_payload.get("typed_blockers"))
    source_refs = list(dict.fromkeys([
        *_text_list(closeout_payload.get("source_refs")),
        *[
            ref
            for rows in normalized.values()
            for row in rows
            for ref in _text_list(row.get("source_refs"))
        ],
    ]))
    proposed_writes = [
        {
            **row,
            "source_category": category,
            "destination": _text(row.get("destination")),
            "write_id": _text(row.get("write_id")) or _fingerprint(row),
        }
        for category, rows in normalized.items()
        for row in rows
        if _text(row.get("destination"))
    ]
    source_fingerprint = _fingerprint({"stage": resolved_stage, "closeout": normalized, "source_refs": source_refs})
    return {
        "surface": "publication_route_memory_closeout",
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", study_id),
        "stage": resolved_stage,
        "source_refs": source_refs,
        "proposed_writes": proposed_writes,
        "typed_blockers": typed_blockers,
        "normalized_closeout": normalized,
        "source_fingerprint": source_fingerprint,
        "authority_boundary": authority_boundary(),
        "idempotency_key": _text(closeout_payload.get("idempotency_key"))
        or f"publication_route_memory_closeout:{study_id}:{resolved_stage}:{source_fingerprint}",
    }


def apply_publication_route_memory_closeout(
    *,
    closeout: Mapping[str, Any],
    workspace_root: Path,
    apply: bool = True,
) -> dict[str, Any]:
    idempotency_key = _required_text("idempotency_key", closeout.get("idempotency_key"))
    receipt_path = publication_route_memory_apply_receipt_path(
        workspace_root=workspace_root,
        idempotency_key=idempotency_key,
    )
    if apply and (existing := _read_json(receipt_path)):
        return {**existing, "idempotent_replay": True, "receipt_ref": str(receipt_path)}
    typed_blockers = _mapping_list(closeout.get("typed_blockers"))
    proposed = _mapping_list(closeout.get("proposed_writes"))
    accepted = [write for write in proposed if _text(write.get("destination")) == "publication_route_memory"]
    rejected = [
        {**write, "reason": "non_publication_memory_destination_requires_domain_owner"}
        for write in proposed
        if _text(write.get("destination")) != "publication_route_memory"
    ]
    receipt = {
        "surface": "publication_route_memory_acceptance_receipt",
        "schema_version": SCHEMA_VERSION,
        "study_id": _required_text("study_id", closeout.get("study_id")),
        "stage": _required_text("stage", closeout.get("stage")),
        "status": "blocked" if typed_blockers else "applied" if apply else "dry_run",
        "idempotency_key": idempotency_key,
        "source_fingerprint": _required_text("source_fingerprint", closeout.get("source_fingerprint")),
        "accepted_writes": [] if typed_blockers else accepted,
        "rejected_writes": rejected,
        "typed_blockers": typed_blockers,
        "authority_boundary": authority_boundary(),
    }
    if apply:
        if not typed_blockers:
            sync_accepted_publication_route_memory_cards(
                receipt=receipt,
                pack_path=publication_route_memory_pack_path(workspace_root=workspace_root),
                receipt_ref=str(receipt_path),
                apply=True,
            )
        _write_json(receipt_path, receipt)
    return {**receipt, "receipt_ref": str(receipt_path)}


def _validate_publication_route_memory_stage(stage: str) -> str:
    resolved = _required_text("stage", stage)
    if resolved not in PUBLICATION_ROUTE_MEMORY_STAGES:
        raise ValueError(f"unsupported publication-route memory stage: {resolved}")
    return resolved


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str:
    return str(value or "").strip()


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _safe_key(value: str) -> str:
    return "".join(character if character.isalnum() or character in "-_." else "_" for character in value)


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


__all__ = [
    "EXPLORATORY_STAGES",
    "PUBLICATION_ROUTE_MEMORY_ROOT",
    "PUBLICATION_ROUTE_MEMORY_STAGES",
    "PUBLICATION_STRATEGY_MEMORY_KIND",
    "PUBLICATION_STRATEGY_MEMORY_USE_POLICY",
    "STAGE_OBLIGATIONS",
    "adopt_frontier_route_back_terminal_decision",
    "apply_publication_route_memory_closeout",
    "apply_publication_route_memory_seed_fixture",
    "apply_publication_route_memory_seed_library",
    "build_research_frontier_board",
    "default_publication_route_memory_seed_fixture_path",
    "frontier_board_packet_fields",
    "normalize_publication_route_memory_closeout",
    "publication_route_memory_apply_receipt_path",
    "publication_route_memory_pack_path",
    "publication_route_memory_pack_root",
    "publication_strategy_memory_use_policy",
    "render_publication_strategy_memory_prompt_block",
    "research_memory_contract",
    "select_publication_route_memory_refs",
]
