from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from med_autoscience.stage_surface_contract import build_stage_surface_contract

from ..source_refs import source_ref_allowed


def materialize_stage_review_deliverable_index(
    *,
    study_root: str | Path,
    study_id: str,
    stage: str,
    payload: Mapping[str, Any] | None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    stage_id = _safe_stage_id(stage)
    resolved_payload = _mapping(payload)
    review_page_ref = f"artifacts/stage_reviews/{stage_id}/latest.md"
    deliverable_index_ref = "artifacts/stage_reviews/index.json"
    review_page_path = resolved_study_root / review_page_ref
    index_path = resolved_study_root / deliverable_index_ref
    stage_card = _stage_card(stage_id)
    missing = _missing_conditions(resolved_payload, stage_card=stage_card)
    status = "available" if not missing else "missing"
    source_refs = _source_refs(
        resolved_payload,
        review_page_ref=review_page_ref,
        deliverable_index_ref=deliverable_index_ref,
    )
    index = _index_payload(
        study_id=study_id,
        stage=stage_id,
        status=status,
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
        review_page_ref=review_page_ref,
        deliverable_index_ref=deliverable_index_ref,
        payload=resolved_payload,
        source_refs=source_refs,
        stage_card=stage_card,
        missing=missing,
    )

    review_page_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.parent.mkdir(parents=True, exist_ok=True)
    review_page_path.write_text(_render_review_page(index), encoding="utf-8")
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "surface_kind": "mas_stage_review_materialization_receipt",
        "status": status,
        "study_id": study_id,
        "stage": stage_id,
        "review_page_path": str(review_page_path),
        "index_path": str(index_path),
        "review_page_ref": review_page_ref,
        "deliverable_index_ref": deliverable_index_ref,
        "conditions": {"missing": missing},
        "authority": _authority_boundary(),
    }


def _safe_stage_id(stage: str) -> str:
    stage_id = str(stage).strip()
    if not stage_id:
        raise ValueError("stage is required")
    path = Path(stage_id)
    if path.is_absolute() or "/" in stage_id or "\\" in stage_id or ".." in path.parts:
        raise ValueError(f"unsafe stage id: {stage_id}")
    return stage_id


def _missing_conditions(payload: Mapping[str, Any], *, stage_card: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in ("owner_receipt_refs", "ledger_refs", "quality_refs", "artifact_refs"):
        if not _dedupe_refs(_string_list(payload.get(key))):
            missing.append(key)
    if not stage_card:
        missing.append("stage_surface_contract_stage")
    return missing


def _source_refs(
    payload: Mapping[str, Any],
    *,
    review_page_ref: str,
    deliverable_index_ref: str,
) -> list[str]:
    freshness = _mapping(payload.get("freshness_signal"))
    next_owner = _mapping(payload.get("next_owner"))
    return _dedupe_refs(
        [
            review_page_ref,
            deliverable_index_ref,
            *_string_list(payload.get("owner_receipt_refs")),
            *_string_list(payload.get("ledger_refs")),
            *_string_list(payload.get("quality_refs")),
            *_string_list(payload.get("artifact_refs")),
            *_string_list(freshness.get("source_refs")),
            _non_empty_text(next_owner.get("source_ref")),
        ]
    )


def _index_payload(
    *,
    study_id: str,
    stage: str,
    status: str,
    generated_at: str,
    review_page_ref: str,
    deliverable_index_ref: str,
    payload: Mapping[str, Any],
    source_refs: list[str],
    stage_card: Mapping[str, Any],
    missing: list[str],
) -> dict[str, Any]:
    grounded = not missing
    deliverable_index = deepcopy(_mapping(stage_card.get("deliverable_index")))
    if deliverable_index:
        deliverable_index["source_refs"] = source_refs
        deliverable_index["review_page_ref"] = review_page_ref
        deliverable_index["deliverable_index_ref"] = deliverable_index_ref
    return {
        "surface_kind": "mas_stage_deliverable_index",
        "schema_version": 1,
        "status": status,
        "study_id": study_id,
        "stage": stage,
        "generated_at": generated_at,
        "review_page_ref": review_page_ref,
        "deliverable_index_ref": deliverable_index_ref,
        "source_refs": source_refs,
        "deliverable_index": deliverable_index,
        "paper_asset_delta": _paper_asset_delta(payload, grounded=grounded),
        "claim_trace": _claim_trace(payload, grounded=grounded),
        "freshness_signal": _freshness_signal(payload, grounded=grounded),
        "human_review": _human_review(payload, grounded=grounded),
        "next_owner": _next_owner(payload, deliverable_index=deliverable_index),
        "conditions": {
            "missing": missing,
            "stale": [] if grounded else ["stage_review_required_refs_missing"],
            "conflict": [],
        },
        "authority": _authority_boundary(),
    }


def _paper_asset_delta(payload: Mapping[str, Any], *, grounded: bool) -> dict[str, Any]:
    if not grounded:
        return _empty_paper_asset_delta()
    delta = _mapping(payload.get("paper_asset_delta"))
    return {
        "delta_types": _string_list(delta.get("delta_types")),
        "refs": _dedupe_refs(_string_list(delta.get("refs"))),
        "summary": _non_empty_text(delta.get("summary")),
        "body_included": False,
        "can_authorize_artifact_authority": False,
    }


def _claim_trace(payload: Mapping[str, Any], *, grounded: bool) -> dict[str, Any]:
    if not grounded:
        return _empty_claim_trace()
    trace = _mapping(payload.get("claim_trace"))
    return {
        "impact_state": _non_empty_text(trace.get("impact_state")) or "no_claim_change",
        "claim_refs": _string_list(trace.get("claim_refs")),
        "summary": _non_empty_text(trace.get("summary")),
        "can_authorize_quality_verdict": False,
    }


def _freshness_signal(payload: Mapping[str, Any], *, grounded: bool) -> dict[str, Any]:
    if not grounded:
        return {
            "state": "red_stale_or_inconsistent",
            "summary": "Required owner receipt, ledger, quality, or artifact refs are missing.",
            "source_refs": [],
            "blocks_auto_advance_by_default": False,
            "can_authorize_submission_readiness": False,
        }
    freshness = _mapping(payload.get("freshness_signal"))
    return {
        "state": _non_empty_text(freshness.get("state")) or "yellow_refresh_recommended",
        "summary": _non_empty_text(freshness.get("summary")),
        "source_refs": _dedupe_refs(_string_list(freshness.get("source_refs"))),
        "blocks_auto_advance_by_default": False,
        "can_authorize_submission_readiness": False,
    }


def _human_review(payload: Mapping[str, Any], *, grounded: bool) -> dict[str, Any]:
    if not grounded:
        return {
            "state": "not_recorded",
            "reviewer_notes": None,
            "blocks_auto_advance": False,
            "default_blocks_auto_advance": False,
            "blocking_only_when": "mas_human_gate_boundary_triggered",
            "can_authorize_quality_verdict": False,
            "can_authorize_submission_readiness": False,
            "can_mark_publication_ready": False,
        }
    review = _mapping(payload.get("human_review"))
    state = _non_empty_text(review.get("state")) or "not_recorded"
    boundary_triggered = bool(review.get("human_gate_boundary_triggered"))
    return {
        "state": state,
        "reviewer_notes": _non_empty_text(review.get("reviewer_notes")),
        "blocks_auto_advance": state == "human_gate_required" and boundary_triggered,
        "default_blocks_auto_advance": False,
        "blocking_only_when": "mas_human_gate_boundary_triggered",
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def _next_owner(payload: Mapping[str, Any], *, deliverable_index: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(payload.get("next_owner"))
    indexed_next_owner = _mapping(deliverable_index.get("next_owner"))
    return {
        "owner": _non_empty_text(explicit.get("owner")) or _non_empty_text(indexed_next_owner.get("owner")) or "MedAutoScience",
        "next_routes": _string_list(explicit.get("next_routes")) or _string_list(indexed_next_owner.get("next_routes")),
        "source_ref": _non_empty_text(explicit.get("source_ref")) or _non_empty_text(indexed_next_owner.get("source_ref")),
    }


def _render_review_page(index: Mapping[str, Any]) -> str:
    missing = _string_list(_mapping(index.get("conditions")).get("missing"))
    lines = [
        f"# Stage Review: {index['stage']}",
        "",
        f"- Study: `{index['study_id']}`",
        f"- Status: `{index['status']}`",
        f"- Review page ref: `{index['review_page_ref']}`",
        f"- Deliverable index ref: `{index['deliverable_index_ref']}`",
        "- Authority: read-only MAS stage review projection; this page cannot authorize quality verdicts, submission readiness, publication readiness, or artifact authority.",
        "",
    ]
    if missing:
        lines.extend(["## Missing conditions", "", *_bullet_lines(missing), ""])
    lines.extend(
        [
            "## Paper Asset Delta",
            "",
            *_mapping_bullets(_mapping(index.get("paper_asset_delta")), ("delta_types", "refs", "summary")),
            "",
            "## Claim Trace",
            "",
            *_mapping_bullets(_mapping(index.get("claim_trace")), ("impact_state", "claim_refs", "summary")),
            "",
            "## Freshness Signal",
            "",
            *_mapping_bullets(_mapping(index.get("freshness_signal")), ("state", "summary", "source_refs")),
            "",
            "## Human Review",
            "",
            *_mapping_bullets(_mapping(index.get("human_review")), ("state", "reviewer_notes")),
            "",
            "## Next Owner",
            "",
            *_mapping_bullets(_mapping(index.get("next_owner")), ("owner", "next_routes", "source_ref")),
            "",
            "## Source Refs",
            "",
            *_bullet_lines(_string_list(index.get("source_refs"))),
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def _empty_paper_asset_delta() -> dict[str, Any]:
    return {
        "delta_types": [],
        "refs": [],
        "summary": None,
        "body_included": False,
        "can_authorize_artifact_authority": False,
    }


def _empty_claim_trace() -> dict[str, Any]:
    return {
        "impact_state": "no_claim_change",
        "claim_refs": [],
        "summary": None,
        "can_authorize_quality_verdict": False,
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "kind": "read_only_stage_review_projection",
        "writes_authority_surface": False,
        "truth_owner": "MedAutoScience",
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
        "can_authorize_artifact_authority": False,
        "human_review_blocks_auto_advance_by_default": False,
    }


def _stage_card(stage: object) -> dict[str, Any]:
    stage_id = _non_empty_text(stage)
    if stage_id is None:
        return {}
    for card in build_stage_surface_contract()["stage_cards"]:
        if isinstance(card, Mapping) and card.get("route_id") == stage_id:
            return dict(card)
    return {}


def _mapping_bullets(value: Mapping[str, Any], keys: Iterable[str]) -> list[str]:
    lines: list[str] = []
    for key in keys:
        item = value.get(key)
        if isinstance(item, list):
            rendered = ", ".join(str(part) for part in item) if item else "none"
        elif item is None:
            rendered = "none"
        else:
            rendered = str(item)
        lines.append(f"- {key}: {rendered}")
    return lines


def _bullet_lines(values: Iterable[str]) -> list[str]:
    items = list(values)
    if not items:
        return ["- none"]
    return [f"- {value}" for value in items]


def _dedupe_refs(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _non_empty_text(value)
        if text is None or text in seen or not source_ref_allowed(text):
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None:
            result.append(text)
    return result


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = ["materialize_stage_review_deliverable_index"]
