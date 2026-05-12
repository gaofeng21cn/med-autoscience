from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from html import escape
import json
from pathlib import Path
from typing import Any

from med_autoscience.stage_surface_contract import build_stage_surface_contract

from .rendering import list_html, status_chip
from .source_refs import source_ref_allowed
from .status_display import display_text


def build_stage_review_index(
    progress: Mapping[str, Any] | None,
    *,
    study_id: str,
    study_root: str | Path | None = None,
) -> dict[str, Any]:
    resolved_progress = _mapping(progress)
    locator_projection = _stage_review_locator_projection(
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
    review_page_ref = _review_page_ref(explicit)
    deliverable_index_ref = _non_empty_text(explicit.get("deliverable_index_ref"))
    source_refs = _dedupe_refs(
        [
            *_string_list(explicit.get("source_refs")),
            review_page_ref,
            deliverable_index_ref,
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
    claim_impact = _mapping(row.get("claim_impact"))
    human_review = _mapping(row.get("human_review_annotation"))
    next_owner = _mapping(row.get("next_owner"))
    return {
        "status": _non_empty_text(review_index.get("status")) or "missing",
        "current_stage": _non_empty_text(review_index.get("current_stage")),
        "latest_review_page_ref": _non_empty_text(latest.get("ref")),
        "deliverable_index_ref": _non_empty_text(review_index.get("deliverable_index_ref")),
        "freshness_state": _non_empty_text(freshness.get("state")),
        "paper_asset_delta_types": _string_list(paper_asset_delta.get("delta_types")),
        "claim_impact_state": _non_empty_text(claim_impact.get("impact_state")),
        "human_review_state": _non_empty_text(human_review.get("state")),
        "next_owner": _non_empty_text(next_owner.get("owner")),
        "blockers": _string_list(row.get("blockers")),
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_mark_publication_ready": False,
    }


def render_stage_review_section(payload: Mapping[str, Any]) -> str:
    rows = [_mapping(item) for item in payload.get("rows") or [] if isinstance(item, Mapping)]
    if not rows:
        return (
            '<section class="panel wide"><h2>Stage 交付审阅 '
            + status_chip(payload.get("status") or "missing")
            + "</h2>"
            "<p>缺少 Stage Review Page / Deliverable Index 显式引用。</p>"
            "<p>本页面不从文件名、产物路径或 stage 文案猜测审阅结论。</p>"
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
        "claim_impact": claim_impact,
        "freshness_signal": freshness_signal,
        "human_review_annotation": human_review,
        "next_owner": next_owner,
        "blockers": blockers,
        "continue_state": continue_state,
        "source_refs": source_refs,
        "latest_review_page_proof": _mapping(locator_projection.get("latest_review_page_proof")),
        "paper_line_index_proof": _mapping(locator_projection.get("paper_line_index_proof")),
        "authority": _authority_boundary(),
    }


def _stage_review_locator_projection(
    progress: Mapping[str, Any],
    *,
    study_id: str,
    study_root: str | Path | None,
) -> dict[str, Any]:
    explicit = _explicit_stage_review(progress)
    explicit_locator = _mapping(explicit.get("artifact_locator"))
    explicit_index_ref = _non_empty_text(explicit.get("deliverable_index_ref"))
    resolved_study_root = _study_root(progress, study_root)
    index_ref = (
        _non_empty_text(explicit_locator.get("stage_deliverable_index"))
        or _non_empty_text(explicit_locator.get("stage_deliverable_index_ref"))
        or explicit_index_ref
        or "artifacts/stage_reviews/index.json"
    )
    index_path = _resolve_locator_path(index_ref, study_root=resolved_study_root, study_id=study_id)
    if index_path is None or not index_path.is_file():
        return {}
    try:
        index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    if not isinstance(index_payload, Mapping):
        return {}
    index = dict(index_payload)
    index_study_id = _non_empty_text(index.get("study_id"))
    if index_study_id and index_study_id != study_id:
        return {
            "study_id": index_study_id,
            "deliverable_index_ref": _workspace_ref(index_path, study_root=resolved_study_root),
            "paper_line_index_proof": _paper_line_index_proof(
                index,
                index_path=index_path,
                study_root=resolved_study_root,
                status="conflict",
            ),
        }
    latest_review_page_ref = _review_page_ref(index) or _non_empty_text(
        _mapping(index.get("artifact_locator")).get("latest_review_page")
    )
    latest_review_page_path = _resolve_locator_path(
        latest_review_page_ref,
        study_root=resolved_study_root,
        study_id=study_id,
    )
    normalized: dict[str, Any] = {
        **index,
        "stage": _non_empty_text(index.get("stage")) or _non_empty_text(index.get("current_stage")),
        "review_page_ref": _workspace_ref(latest_review_page_path, study_root=resolved_study_root)
        if latest_review_page_path is not None
        else latest_review_page_ref,
        "deliverable_index_ref": _workspace_ref(index_path, study_root=resolved_study_root),
        "source_refs": _dedupe_refs(
            [
                *_string_list(index.get("source_refs")),
                _workspace_ref(index_path, study_root=resolved_study_root),
                _workspace_ref(latest_review_page_path, study_root=resolved_study_root)
                if latest_review_page_path is not None
                else latest_review_page_ref,
            ]
        ),
        "paper_line_index_proof": _paper_line_index_proof(
            index,
            index_path=index_path,
            study_root=resolved_study_root,
            status="available",
        ),
        "latest_review_page_proof": _latest_review_page_proof(
            latest_review_page_path,
            latest_review_page_ref=latest_review_page_ref,
            study_root=resolved_study_root,
        ),
        "artifact_locator": {
            "study_root": str(resolved_study_root) if resolved_study_root is not None else None,
            "stage_deliverable_index": _workspace_ref(index_path, study_root=resolved_study_root),
            "latest_review_page": _workspace_ref(latest_review_page_path, study_root=resolved_study_root)
            if latest_review_page_path is not None
            else latest_review_page_ref,
            "body_included": False,
            "read_only": True,
        },
    }
    return normalized


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


def _study_root(progress: Mapping[str, Any], study_root: str | Path | None) -> Path | None:
    if study_root is not None:
        return Path(study_root).expanduser().resolve()
    refs = _mapping(progress.get("refs"))
    for value in (
        progress.get("study_root"),
        refs.get("study_root"),
        refs.get("quest_root"),
    ):
        text = _non_empty_text(value)
        if text is not None:
            return Path(text).expanduser().resolve()
    return None


def _resolve_locator_path(
    ref: str | None,
    *,
    study_root: Path | None,
    study_id: str,
) -> Path | None:
    if ref is None:
        return None
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    if study_root is None:
        return None
    parts = path.parts
    if len(parts) >= 2 and parts[0] == "studies" and parts[1] == study_id:
        return (study_root.parent.parent / path).resolve()
    if parts and parts[0] == "artifacts":
        return (study_root / path).resolve()
    return (study_root / path).resolve()


def _workspace_ref(path: Path | None, *, study_root: Path | None) -> str | None:
    if path is None:
        return None
    if study_root is None:
        return str(path)
    try:
        return str(path.resolve().relative_to(study_root.parent.parent.resolve()))
    except ValueError:
        try:
            return str(path.resolve().relative_to(study_root.resolve()))
        except ValueError:
            return str(path)


def _paper_line_index_proof(
    index: Mapping[str, Any],
    *,
    index_path: Path,
    study_root: Path | None,
    status: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_stage_deliverable_index_locator_proof",
        "status": status,
        "index_ref": _workspace_ref(index_path, study_root=study_root),
        "index_surface_kind": _non_empty_text(index.get("surface_kind")),
        "stage": _non_empty_text(index.get("stage")) or _non_empty_text(index.get("current_stage")),
        "source_refs": _dedupe_refs(_string_list(index.get("source_refs"))),
        "body_included": False,
        "read_only": True,
        "writes_authority_surface": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
    }


def _latest_review_page_proof(
    latest_review_page_path: Path | None,
    *,
    latest_review_page_ref: str | None,
    study_root: Path | None,
) -> dict[str, Any]:
    ref = (
        _workspace_ref(latest_review_page_path, study_root=study_root)
        if latest_review_page_path is not None
        else latest_review_page_ref
    )
    return {
        "surface_kind": "mas_stage_deliverable_review_page_locator_proof",
        "status": "available" if latest_review_page_path is not None and latest_review_page_path.is_file() else "missing",
        "latest_review_page_ref": ref,
        "body_included": False,
        "read_only": True,
        "writes_authority_surface": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
    }


def _review_page_ref(value: Mapping[str, Any]) -> str | None:
    latest = _mapping(value.get("latest_review_page"))
    return (
        _non_empty_text(value.get("review_page_ref"))
        or _non_empty_text(value.get("latest_review_page_ref"))
        or _non_empty_text(latest.get("ref"))
    )


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


def _claim_impact(value: Mapping[str, Any]) -> dict[str, Any]:
    claim_trace = _mapping(value.get("claim_trace"))
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
    review = _mapping(value.get("human_review"))
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
    fallback = _mapping(deliverable_index.get("next_owner"))
    return {
        "owner": _non_empty_text(explicit.get("owner")) or _non_empty_text(fallback.get("owner")) or "MedAutoScience",
        "next_routes": _string_list(explicit.get("next_routes")) or _string_list(fallback.get("next_routes")),
        "source_ref": _non_empty_text(explicit.get("source_ref")) or _non_empty_text(fallback.get("source_ref")),
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


def _row_html(row: Mapping[str, Any]) -> str:
    paper_asset_delta = _mapping(row.get("paper_asset_delta"))
    claim_impact = _mapping(row.get("claim_impact"))
    freshness = _mapping(row.get("freshness_signal"))
    human_review = _mapping(row.get("human_review_annotation"))
    next_owner = _mapping(row.get("next_owner"))
    continue_state = _mapping(row.get("continue_state"))
    blockers = _string_list(row.get("blockers"))
    return (
        "<tr>"
        + _td("Stage", display_text(row.get("stage"), fallback="缺失", preserve_known_token=False))
        + _td("最新审阅页", _non_empty_text(row.get("latest_review_page_ref")) or "缺失")
        + _td("新鲜度", _non_empty_text(freshness.get("state")) or "缺失")
        + _td("论文资产变化", ", ".join(_string_list(paper_asset_delta.get("delta_types"))) or "缺失")
        + _td("Claim 影响", _non_empty_text(claim_impact.get("impact_state")) or "缺失")
        + _td("人工判断", _non_empty_text(human_review.get("state")) or "未记录")
        + _td("下一 owner", _non_empty_text(next_owner.get("owner")) or "缺失")
        + _td("阻塞/是否可继续", "; ".join([*blockers, _non_empty_text(continue_state.get("state")) or "缺失"]))
        + "</tr>"
    )


def _td(label: str, value: str) -> str:
    return f'<td data-label="{escape(label, quote=True)}">{escape(value)}</td>'


def _condition_list(payload: Mapping[str, Any]) -> str:
    conditions = _mapping(payload.get("conditions"))
    items: list[str] = []
    for key in ("missing", "stale", "conflict"):
        for item in _string_list(conditions.get(key)):
            items.append(f"{key}: {item}")
    return list_html(items, empty_text="当前没有 Stage 审阅条件。")


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


__all__ = [
    "build_stage_review_index",
    "render_stage_review_section",
    "runtime_stage_review_summary",
]
