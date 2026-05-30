from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from html import escape
from pathlib import Path
from typing import Any

from med_autoscience.stage_surface_contract import build_stage_surface_contract

from .rendering import list_html, status_chip
from .source_refs import source_ref_allowed
from .stage_review_parts import (
    build_stage_log_summary,
    materialize_stage_review_deliverable_index,
    paper_line_workspace_proof_available,
    paper_line_workspace_proof_refs,
    review_page_ref as stage_review_page_ref,
    runtime_stage_log_summary,
    stage_review_locator_projection,
)
from .status_display import display_text


def build_stage_review_index(
    progress: Mapping[str, Any] | None,
    *,
    study_id: str,
    study_root: str | Path | None = None,
) -> dict[str, Any]:
    resolved_progress = _mapping(progress)
    locator_projection = stage_review_locator_projection(
        resolved_progress,
        study_id=study_id,
        study_root=study_root,
    )
    explicit = locator_projection or _explicit_stage_review(resolved_progress)
    user_visible = _mapping(resolved_progress.get("user_visible_projection"))
    stage = (
        _non_empty_text(explicit.get("stage"))
        or _non_empty_text(user_visible.get("current_stage"))
        or _non_empty_text(resolved_progress.get("current_stage"))
    )
    review_page_ref = stage_review_page_ref(explicit)
    deliverable_index_ref = _non_empty_text(explicit.get("deliverable_index_ref"))
    source_refs = _dedupe_refs(
        [
            *_string_list(explicit.get("source_refs")),
            review_page_ref,
            deliverable_index_ref,
            *paper_line_workspace_proof_refs(_mapping(explicit.get("paper_line_workspace_proof"))),
        ]
    )
    stage_card = _stage_card(stage)
    missing = _missing_conditions(
        stage=stage,
        review_page_ref=review_page_ref,
        deliverable_index_ref=deliverable_index_ref,
        source_refs=source_refs,
        stage_card=stage_card,
    )
    paper_line_workspace_proof = _mapping(explicit.get("paper_line_workspace_proof"))
    if paper_line_workspace_proof and not paper_line_workspace_proof_available(paper_line_workspace_proof):
        missing.append("paper_line_workspace_proof_refs")
    stale = _stale_conditions(explicit)
    conflict = _conflict_conditions(explicit, study_id=study_id)
    status = "available" if not missing and not conflict else "missing"
    rows = (
        [
            _stage_review_row(
                explicit,
                study_id=study_id,
                stage=str(stage),
                review_page_ref=str(review_page_ref),
                deliverable_index_ref=str(deliverable_index_ref),
                source_refs=source_refs,
                stage_card=stage_card,
                progress=resolved_progress,
                locator_projection=locator_projection,
            )
        ]
        if status == "available"
        else []
    )
    stage_log_summary = build_stage_log_summary(
        explicit=explicit,
        progress=resolved_progress,
        row=rows[0] if rows else None,
        stage=stage,
        source_refs=source_refs,
    )
    return {
        "surface_kind": "mas_progress_portal_stage_review_index",
        "schema_version": 1,
        "status": status,
        "study_id": study_id,
        "current_stage": stage,
        "latest_review_page": {
            "ref": review_page_ref,
            "role": "one_page_paper_review",
            "body_included": False,
        },
        "deliverable_index_ref": deliverable_index_ref,
        "rows": rows,
        "source_refs": source_refs,
        "locator_projection": locator_projection,
        "paper_line_summary": _paper_line_summary(
            explicit=explicit,
            progress=resolved_progress,
            normalized_rows=rows,
        ),
        "stage_log_summary": stage_log_summary,
        "conditions": {
            "missing": missing,
            "stale": stale,
            "conflict": conflict,
        },
        "authority": _authority_boundary(),
    }


def runtime_stage_review_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    review_index = _mapping(value)
    row = _mapping((review_index.get("rows") or [{}])[0]) if isinstance(review_index.get("rows"), list) else {}
    latest = _mapping(review_index.get("latest_review_page"))
    freshness = _mapping(row.get("freshness_signal"))
    paper_asset_delta = _mapping(row.get("paper_asset_delta"))
    source_grounding = _mapping(row.get("source_grounding"))
    presentation_note = _mapping(row.get("paper_presentation_note"))
    claim_impact = _mapping(row.get("claim_impact"))
    human_review = _mapping(row.get("human_review_annotation"))
    next_owner = _mapping(row.get("next_owner"))
    continue_state = _mapping(row.get("continue_state"))
    stage_log = runtime_stage_log_summary(_mapping(review_index.get("stage_log_summary")))
    return {
        "status": _non_empty_text(review_index.get("status")) or "missing",
        "current_stage": _non_empty_text(review_index.get("current_stage")),
        "latest_review_page_ref": _non_empty_text(latest.get("ref")),
        "deliverable_index_ref": _non_empty_text(review_index.get("deliverable_index_ref")),
        "freshness_state": _non_empty_text(freshness.get("state")),
        "paper_asset_delta_types": _string_list(paper_asset_delta.get("delta_types")),
        "source_map_refs": _string_list(source_grounding.get("source_map_refs")),
        "page_block_anchor_refs": _string_list(source_grounding.get("page_block_anchor_refs")),
        "figure_near_claim_refs": _string_list(source_grounding.get("figure_near_claim_refs")),
        "paper_presentation_note_ref": _non_empty_text(presentation_note.get("ref")),
        "paper_presentation_evidence_spine_refs": _string_list(presentation_note.get("evidence_spine_refs")),
        "claim_impact_state": _non_empty_text(claim_impact.get("impact_state")),
        "human_review_state": _non_empty_text(human_review.get("state")),
        "next_owner": _non_empty_text(next_owner.get("owner")),
        "blockers": _string_list(row.get("blockers")),
        "continue_state": _non_empty_text(continue_state.get("state")),
        "stage_log_summary": stage_log,
        "research_pack_progress_summary": _mapping(stage_log.get("research_pack_progress_summary")),
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def render_stage_review_section(payload: Mapping[str, Any]) -> str:
    rows = [_mapping(item) for item in payload.get("rows") or [] if isinstance(item, Mapping)]
    stage_log = _mapping(payload.get("stage_log_summary"))
    if not rows:
        return (
            '<section class="panel wide"><h2>Stage 交付审阅 '
            + status_chip(payload.get("status") or "missing")
            + "</h2>"
            "<p>缺少 Stage Review Page / Deliverable Index 显式引用。</p>"
            "<p>本页面不从文件名、产物路径或 stage 文案猜测审阅结论。</p>"
            + _stage_log_html(stage_log)
            + _condition_list(payload)
            + "</section>"
        )
    return (
        '<section class="panel wide"><h2>Stage 交付审阅 '
        + status_chip(payload.get("status") or "available")
        + "</h2>"
        "<p>这一表只帮助人工审阅论文阶段交付物；不能授权质量 verdict、投稿 ready 或 publication ready。</p>"
        '<div class="table-wrap"><table class="responsive-table"><thead><tr>'
        "<th>Stage</th><th>最新审阅页</th><th>新鲜度</th><th>论文资产变化</th>"
        "<th>Claim 影响</th><th>人工判断</th><th>下一 owner</th><th>阻塞/是否可继续</th>"
        "</tr></thead><tbody>"
        + "".join(_row_html(row) for row in rows)
        + "</tbody></table></div>"
        + _stage_log_html(stage_log)
        + _condition_list(payload)
        + "</section>"
    )


def _stage_review_row(
    explicit: Mapping[str, Any],
    *,
    study_id: str,
    stage: str,
    review_page_ref: str,
    deliverable_index_ref: str,
    source_refs: list[str],
    stage_card: Mapping[str, Any],
    progress: Mapping[str, Any],
    locator_projection: Mapping[str, Any],
) -> dict[str, Any]:
    deliverable_index = deepcopy(_mapping(stage_card.get("deliverable_index")))
    paper_asset_delta = _paper_asset_delta(explicit)
    source_grounding = _source_grounding(explicit)
    presentation_note = _paper_presentation_note(explicit)
    claim_impact = _claim_impact(explicit)
    freshness_signal = _freshness_signal(explicit, progress)
    human_review = _human_review_annotation(explicit)
    next_owner = _next_owner(explicit, deliverable_index)
    blockers = _blockers(explicit, progress)
    continue_state = _continue_state(
        blockers=blockers,
        human_review=human_review,
        freshness_signal=freshness_signal,
    )
    return {
        "surface_kind": "mas_progress_portal_stage_review_row",
        "study_id": study_id,
        "stage": stage,
        "latest_review_page_ref": review_page_ref,
        "deliverable_index_ref": deliverable_index_ref,
        "deliverable_index": deliverable_index,
        "paper_asset_delta": paper_asset_delta,
        "source_grounding": source_grounding,
        "paper_presentation_note": presentation_note,
        "claim_impact": claim_impact,
        "freshness_signal": freshness_signal,
        "human_review_annotation": human_review,
        "next_owner": next_owner,
        "blockers": blockers,
        "continue_state": continue_state,
        "source_refs": source_refs,
        "latest_review_page_proof": _mapping(locator_projection.get("latest_review_page_proof")),
        "paper_line_index_proof": _mapping(locator_projection.get("paper_line_index_proof")),
        "paper_line_workspace_proof": _mapping(explicit.get("paper_line_workspace_proof")),
        "authority": _authority_boundary(),
    }


def _explicit_stage_review(progress: Mapping[str, Any]) -> dict[str, Any]:
    for key in (
        "stage_deliverable_review",
        "stage_review_index",
        "stage_review_page",
    ):
        value = _mapping(progress.get(key))
        if value:
            return value
    return {}


def _stage_card(stage: object) -> dict[str, Any]:
    stage_id = _non_empty_text(stage)
    if stage_id is None:
        return {}
    for card in build_stage_surface_contract()["stage_cards"]:
        if isinstance(card, Mapping) and card.get("route_id") == stage_id:
            return dict(card)
    return {}


def _missing_conditions(
    *,
    stage: str | None,
    review_page_ref: str | None,
    deliverable_index_ref: str | None,
    source_refs: list[str],
    stage_card: Mapping[str, Any],
) -> list[str]:
    missing: list[str] = []
    if stage is None:
        missing.append("current_stage")
    if review_page_ref is None:
        missing.append("stage_review_page")
    if deliverable_index_ref is None:
        missing.append("stage_deliverable_index_ref")
    if not source_refs:
        missing.append("stage_review_source_refs")
    if stage is not None and not stage_card:
        missing.append("stage_surface_contract_stage")
    return missing


def _stale_conditions(value: Mapping[str, Any]) -> list[str]:
    freshness = _mapping(value.get("freshness_signal"))
    state = _non_empty_text(freshness.get("state"))
    if state == "red_stale_or_inconsistent":
        return ["stage_review_freshness"]
    return []


def _conflict_conditions(value: Mapping[str, Any], *, study_id: str) -> list[str]:
    payload_study_id = _non_empty_text(value.get("study_id"))
    if payload_study_id and payload_study_id != study_id:
        return ["stage_review_study_id_mismatch"]
    return []


def _paper_asset_delta(value: Mapping[str, Any]) -> dict[str, Any]:
    delta = _mapping(value.get("paper_asset_delta"))
    return {
        "delta_types": _string_list(delta.get("delta_types")),
        "refs": _dedupe_refs(_string_list(delta.get("refs"))),
        "summary": _non_empty_text(delta.get("summary")),
        "body_included": False,
        "can_authorize_artifact_authority": False,
    }


def _source_grounding(value: Mapping[str, Any]) -> dict[str, Any]:
    grounding = _mapping(value.get("source_grounding"))
    return {
        "source_map_refs": _dedupe_refs(_string_list(grounding.get("source_map_refs"))),
        "page_block_anchor_refs": _dedupe_refs(_string_list(grounding.get("page_block_anchor_refs"))),
        "figure_near_claim_refs": _dedupe_refs(_string_list(grounding.get("figure_near_claim_refs"))),
        "body_included": False,
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
    }


def _paper_presentation_note(value: Mapping[str, Any]) -> dict[str, Any]:
    note = _mapping(value.get("paper_presentation_note"))
    return {
        "mode": "optional_deliverable_note",
        "projection_kind": "evidence_spine_presentation",
        "ref": _non_empty_text(note.get("ref")),
        "evidence_spine_refs": _dedupe_refs(_string_list(note.get("evidence_spine_refs"))),
        "summary": _non_empty_text(note.get("summary")),
        "body_included": False,
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
    }


def _claim_impact(value: Mapping[str, Any]) -> dict[str, Any]:
    claim_trace = _mapping(value.get("claim_trace")) or _mapping(value.get("claim_impact"))
    return {
        "impact_state": _non_empty_text(claim_trace.get("impact_state")) or "no_claim_change",
        "claim_refs": _string_list(claim_trace.get("claim_refs")),
        "summary": _non_empty_text(claim_trace.get("summary")),
        "can_authorize_quality_verdict": False,
    }


def _freshness_signal(value: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(value.get("freshness_signal"))
    state = _non_empty_text(explicit.get("state"))
    if state is None:
        state = _progress_freshness_signal(progress)
    return {
        "state": state,
        "summary": _non_empty_text(explicit.get("summary")),
        "source_refs": _dedupe_refs(_string_list(explicit.get("source_refs"))),
        "blocks_auto_advance_by_default": False,
        "can_authorize_submission_readiness": False,
    }


def _progress_freshness_signal(progress: Mapping[str, Any]) -> str:
    status = _non_empty_text(_mapping(progress.get("progress_freshness")).get("status"))
    if status == "fresh":
        return "green_current"
    if status == "stale":
        return "red_stale_or_inconsistent"
    return "yellow_refresh_recommended"


def _human_review_annotation(value: Mapping[str, Any]) -> dict[str, Any]:
    review = _mapping(value.get("human_review")) or _mapping(value.get("human_review_annotation"))
    state = _non_empty_text(review.get("state")) or "not_recorded"
    boundary_triggered = bool(review.get("human_gate_boundary_triggered"))
    blocks_auto_advance = state == "human_gate_required" and boundary_triggered
    return {
        "state": state,
        "reviewer_notes": _non_empty_text(review.get("reviewer_notes")),
        "blocks_auto_advance": blocks_auto_advance,
        "default_blocks_auto_advance": False,
        "blocking_only_when": "mas_human_gate_boundary_triggered",
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def _next_owner(value: Mapping[str, Any], deliverable_index: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(value.get("next_owner"))
    indexed_next_owner = _mapping(deliverable_index.get("next_owner"))
    return {
        "owner": _non_empty_text(explicit.get("owner")) or _non_empty_text(indexed_next_owner.get("owner")) or "MedAutoScience",
        "next_routes": _string_list(explicit.get("next_routes")) or _string_list(indexed_next_owner.get("next_routes")),
        "source_ref": _non_empty_text(explicit.get("source_ref")) or _non_empty_text(indexed_next_owner.get("source_ref")),
    }


def _blockers(value: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    explicit = _string_list(value.get("blockers"))
    if explicit:
        return explicit
    return _string_list(_mapping(progress.get("user_visible_projection")).get("current_blockers"))


def _continue_state(
    *,
    blockers: list[str],
    human_review: Mapping[str, Any],
    freshness_signal: Mapping[str, Any],
) -> dict[str, Any]:
    human_state = _non_empty_text(human_review.get("state"))
    freshness_state = _non_empty_text(freshness_signal.get("state"))
    if bool(human_review.get("blocks_auto_advance")):
        state = "human_gate_blocked"
    elif blockers or human_state in {"needs_revision", "route_back", "stop_or_pivot", "human_gate_required"}:
        state = "stage_review_attention_required"
    elif freshness_state == "red_stale_or_inconsistent":
        state = "refresh_recommended_before_human_review"
    else:
        state = "can_continue_by_mas_owner_surface"
    return {
        "state": state,
        "auto_advance_authority": False,
        "blocks_auto_advance": bool(human_review.get("blocks_auto_advance")),
        "owner": "MedAutoScience controller/runtime owner surfaces",
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


def _paper_line_summary(
    *,
    explicit: Mapping[str, Any],
    progress: Mapping[str, Any],
    normalized_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    raw_rows = _paper_line_stage_reviews(explicit, progress)
    rows: list[dict[str, Any]]
    if raw_rows:
        rows = [_summary_row(_mapping(item)) for item in raw_rows if isinstance(item, Mapping)]
    else:
        rows = [_summary_row_from_normalized(row) for row in normalized_rows]
    rows = [row for row in rows if row]
    freshness_states = [_non_empty_text(_mapping(row.get("freshness_signal")).get("state")) for row in rows]
    human_reviews = [_mapping(row.get("human_review_annotation")) for row in rows]
    return {
        "surface_kind": "mas_stage_review_paper_line_summary",
        "stage_count": len(rows),
        "claim_impact_by_state": _claim_impact_by_state(rows),
        "paper_asset_delta_types": _sorted_unique(
            delta_type
            for row in rows
            for delta_type in _string_list(_mapping(row.get("paper_asset_delta")).get("delta_types"))
        ),
        "freshness_rollup": {
            "state": _freshness_rollup_state(freshness_states),
            "stage_states": _stage_state_pairs(rows, "freshness_signal"),
            "blocks_auto_advance_by_default": False,
            "can_authorize_submission_readiness": False,
        },
        "human_review_rollup": {
            "states": _sorted_unique(
                _non_empty_text(review.get("state")) or "not_recorded" for review in human_reviews
            ),
            "blocks_auto_advance": any(bool(review.get("blocks_auto_advance")) for review in human_reviews),
            "default_blocks_auto_advance": False,
            "can_authorize_quality_verdict": False,
            "can_mark_publication_ready": False,
        },
        "blockers": _sorted_unique(blocker for row in rows for blocker in _string_list(row.get("blockers"))),
        "authority": _authority_boundary(),
    }


def _paper_line_stage_reviews(explicit: Mapping[str, Any], progress: Mapping[str, Any]) -> list[object]:
    explicit_rows = _list_items(explicit.get("paper_line_stage_reviews"))
    if explicit_rows:
        return explicit_rows
    for key in ("stage_review_index", "stage_deliverable_review", "stage_review_page"):
        rows = _list_items(_mapping(progress.get(key)).get("paper_line_stage_reviews"))
        if rows:
            return rows
    return []


def _summary_row(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage": _non_empty_text(value.get("stage")) or _non_empty_text(value.get("current_stage")),
        "paper_asset_delta": _paper_asset_delta(value),
        "claim_impact": _claim_impact(value),
        "freshness_signal": _freshness_signal(value, {}),
        "human_review_annotation": _human_review_annotation(value),
        "blockers": _string_list(value.get("blockers")),
    }


def _summary_row_from_normalized(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "stage": _non_empty_text(value.get("stage")),
        "paper_asset_delta": _mapping(value.get("paper_asset_delta")),
        "claim_impact": _mapping(value.get("claim_impact")),
        "freshness_signal": _mapping(value.get("freshness_signal")),
        "human_review_annotation": _mapping(value.get("human_review_annotation")),
        "blockers": _string_list(value.get("blockers")),
    }


def _claim_impact_by_state(rows: list[Mapping[str, Any]]) -> dict[str, list[str]]:
    by_state: dict[str, list[str]] = {}
    for row in rows:
        claim = _mapping(row.get("claim_impact"))
        state = _non_empty_text(claim.get("impact_state")) or "no_claim_change"
        refs = _string_list(claim.get("claim_refs")) or ["unreferenced_claim"]
        by_state.setdefault(state, [])
        for ref in refs:
            if ref not in by_state[state]:
                by_state[state].append(ref)
    return {key: sorted(values) for key, values in sorted(by_state.items())}


def _freshness_rollup_state(states: Iterable[str | None]) -> str:
    observed = [state for state in states if state is not None]
    if "red_stale_or_inconsistent" in observed:
        return "red_stale_or_inconsistent"
    if "yellow_refresh_recommended" in observed:
        return "yellow_refresh_recommended"
    if "green_current" in observed:
        return "green_current"
    return "missing"


def _stage_state_pairs(rows: list[Mapping[str, Any]], field: str) -> list[dict[str, str | None]]:
    result: list[dict[str, str | None]] = []
    for row in rows:
        result.append(
            {
                "stage": _non_empty_text(row.get("stage")),
                "state": _non_empty_text(_mapping(row.get(field)).get("state")),
            }
        )
    return result


def _sorted_unique(values: Iterable[object]) -> list[str]:
    result: set[str] = set()
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            result.add(text)
    return sorted(result)


def _row_html(row: Mapping[str, Any]) -> str:
    paper_asset_delta = _mapping(row.get("paper_asset_delta"))
    source_grounding = _mapping(row.get("source_grounding"))
    presentation_note = _mapping(row.get("paper_presentation_note"))
    claim_impact = _mapping(row.get("claim_impact"))
    freshness = _mapping(row.get("freshness_signal"))
    human_review = _mapping(row.get("human_review_annotation"))
    next_owner = _mapping(row.get("next_owner"))
    continue_state = _mapping(row.get("continue_state"))
    blockers = _string_list(row.get("blockers"))
    grounding_refs = [
        *_string_list(source_grounding.get("source_map_refs")),
        *_string_list(source_grounding.get("page_block_anchor_refs")),
        *_string_list(source_grounding.get("figure_near_claim_refs")),
    ]
    presentation_refs = [
        _non_empty_text(presentation_note.get("ref")),
        *_string_list(presentation_note.get("evidence_spine_refs")),
    ]
    paper_line_workspace_refs = paper_line_workspace_proof_refs(_mapping(row.get("paper_line_workspace_proof")))
    return (
        "<tr>"
        + _td("Stage", display_text(row.get("stage"), empty_text="缺失", preserve_known_token=False))
        + _td("最新审阅页", _non_empty_text(row.get("latest_review_page_ref")) or "缺失")
        + _td("新鲜度", _non_empty_text(freshness.get("state")) or "缺失")
        + _td(
            "论文资产变化",
            _join_parts(
                [
                    ", ".join(_string_list(paper_asset_delta.get("delta_types"))),
                    "source: " + "; ".join(grounding_refs) if grounding_refs else None,
                    "presentation: " + "; ".join(ref for ref in presentation_refs if ref) if any(presentation_refs) else None,
                    "paper-line workspace proof: " + "; ".join(paper_line_workspace_refs)
                    if paper_line_workspace_refs
                    else None,
                ]
            )
            or "缺失",
        )
        + _td("Claim 影响", _non_empty_text(claim_impact.get("impact_state")) or "缺失")
        + _td("人工判断", _non_empty_text(human_review.get("state")) or "未记录")
        + _td("下一 owner", _non_empty_text(next_owner.get("owner")) or "缺失")
        + _td("阻塞/是否可继续", "; ".join([*blockers, _non_empty_text(continue_state.get("state")) or "缺失"]))
        + "</tr>"
    )


def _td(label: str, value: str) -> str:
    return f'<td data-label="{escape(label, quote=True)}">{escape(value)}</td>'


def _join_parts(values: Iterable[str | None]) -> str:
    return "; ".join(value for value in values if value)


def _condition_list(payload: Mapping[str, Any]) -> str:
    conditions = _mapping(payload.get("conditions"))
    items: list[str] = []
    for key in ("missing", "stale", "conflict"):
        for item in _string_list(conditions.get(key)):
            items.append(f"{key}: {item}")
    return list_html(items, empty_text="当前没有 Stage 审阅条件。")


def _stage_log_html(stage_log: Mapping[str, Any]) -> str:
    if not stage_log:
        return ""
    items = [
        f"Stage: {_non_empty_text(stage_log.get('stage_name'))}"
        if _non_empty_text(stage_log.get("stage_name"))
        else None,
        f"Owner: {_non_empty_text(stage_log.get('current_owner'))}"
        if _non_empty_text(stage_log.get("current_owner"))
        else None,
        f"问题: {_non_empty_text(stage_log.get('problem_summary'))}"
        if _non_empty_text(stage_log.get("problem_summary"))
        else None,
        f"目标: {_non_empty_text(stage_log.get('stage_goal'))}"
        if _non_empty_text(stage_log.get("stage_goal"))
        else None,
        f"已做: {'; '.join(_string_list(stage_log.get('paper_work_done')))}"
        if _string_list(stage_log.get("paper_work_done"))
        else None,
        f"论文面: {'; '.join(_string_list(stage_log.get('changed_paper_surfaces')))}"
        if _string_list(stage_log.get("changed_paper_surfaces"))
        else None,
        f"结果: {_non_empty_text(stage_log.get('outcome'))}"
        if _non_empty_text(stage_log.get("outcome"))
        else None,
        f"进展分类: {_non_empty_text(stage_log.get('progress_delta_classification'))}"
        if _non_empty_text(stage_log.get("progress_delta_classification"))
        else None,
        _stage_log_delta_stats_text(stage_log),
        _research_pack_progress_text(stage_log),
        f"剩余阻塞: {'; '.join(_string_list(stage_log.get('remaining_blockers')))}"
        if _string_list(stage_log.get("remaining_blockers"))
        else None,
        f"证据: {'; '.join(_string_list(stage_log.get('evidence_refs')))}"
        if _string_list(stage_log.get("evidence_refs"))
        else None,
    ]
    filtered = [item for item in items if item]
    if not filtered:
        return ""
    return "<h3>Stage Log 摘要</h3>" + list_html(
        filtered,
        empty_text="当前没有可展示的 stage log 摘要。",
    )


def _stage_log_delta_stats_text(stage_log: Mapping[str, Any]) -> str | None:
    deliverable = _mapping(stage_log.get("deliverable_progress_delta") or stage_log.get("paper_progress_delta"))
    paper = _mapping(stage_log.get("paper_progress_delta"))
    platform = _mapping(stage_log.get("platform_repair_delta"))
    if not deliverable and not paper and not platform:
        return None
    deliverable_count = int(deliverable.get("count") or 0)
    deliverable_tokens = int(deliverable.get("token_usage_total") or 0)
    platform_count = int(platform.get("count") or 0)
    platform_tokens = int(platform.get("token_usage_total") or 0)
    return (
        "分账统计: "
        f"deliverable_progress_delta={deliverable_count} (tokens={deliverable_tokens}); "
        f"platform_repair_delta={platform_count} (tokens={platform_tokens})"
    )


def _research_pack_progress_text(stage_log: Mapping[str, Any]) -> str | None:
    summary = _mapping(stage_log.get("research_pack_progress_summary"))
    if not summary:
        return None
    deliverable = _mapping(summary.get("deliverable_progress_delta") or summary.get("paper_progress_delta"))
    platform = _mapping(summary.get("platform_repair_delta"))
    blocker = _mapping(summary.get("single_next_owner_blocker"))
    missing_reproducibility = _string_list(summary.get("missing_reproducibility_refs"))
    parts = [
        f"paper/deliverable_delta={int(deliverable.get('count') or 0)}",
        f"platform_repair_delta={int(platform.get('count') or 0)}",
        f"negative_results={int(summary.get('negative_result_count') or 0)}",
        f"route_switches={int(summary.get('route_switch_count') or 0)}",
        "missing_reproducibility_refs=" + ",".join(missing_reproducibility)
        if missing_reproducibility
        else "missing_reproducibility_refs=none",
    ]
    blocker_ref = _non_empty_text(blocker.get("ref"))
    if blocker_ref is not None:
        parts.append(f"single_next_owner_blocker={blocker_ref}")
    return "Research pack 摘要: " + "; ".join(parts)


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


def _list_items(value: object) -> list[object]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return list(value)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "build_stage_review_index",
    "materialize_stage_review_deliverable_index",
    "render_stage_review_section",
    "runtime_stage_review_summary",
]
