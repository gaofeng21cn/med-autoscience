from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = 1
SURFACE = "ai_first_feedback_state"
READ_MODEL = "ai_first_feedback_read_model"
LEDGER_SURFACE = "ai_first_feedback_ledger"
LEDGER_SCHEMA_VERSION = 1
QUALITY_LEARNING_QUEUE_SURFACE = "ai_first_quality_learning_queue"
QUALITY_LEARNING_QUEUE_READ_MODEL = "ai_first_quality_learning_queue_read_model"
QUALITY_LEARNING_OPERATIONS_REPORT_SURFACE = "ai_first_quality_learning_operations_report"
QUALITY_LEARNING_OPERATIONS_REPORT_READ_MODEL = "ai_first_quality_learning_operations_report_read_model"
LOW_LEVEL_FIELD_HINTS = ("raw_terminal_log", "full_prompt", "prompt", "secret", "token", "log_path")
EVENT_PRIORITY = {
    "ai_reviewer_trace_gap": 0,
    "predraft_gap": 1,
    "route_back_open": 2,
    "artifact_rebuild_pending": 3,
    "runtime_progress_stale": 4,
    "manual_judgment_pending": 5,
    "quality_toil_repeat": 6,
}
ACTION_RECOMMENDATIONS = {
    "predraft_gap": {
        "action_id": "return_to_predraft_readiness",
        "target_surface": "pre_draft_quality_runtime",
        "summary": "补齐写作前研究问题、证据边界、claim 风险和 reporting guideline readiness。",
    },
    "ai_reviewer_trace_gap": {
        "action_id": "return_to_ai_reviewer_workflow",
        "target_surface": "ai_reviewer_runtime_workflow",
        "summary": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
    },
    "route_back_open": {
        "action_id": "continue_route_back",
        "target_surface": "same_line_route_back",
        "summary": "继续同线 route-back、bounded analysis 或 revise flow，直到反馈闭合。",
    },
    "artifact_rebuild_pending": {
        "action_id": "rebuild_canonical_artifacts",
        "target_surface": "artifact_runtime_proof",
        "summary": "从 canonical source 重新建立 manuscript、figure、table 与 package rebuild proof。",
    },
    "manual_judgment_pending": {
        "action_id": "request_human_decision",
        "target_surface": "human_decision_gate",
        "summary": "请求人工或 physician decision gate，不把等待判断当作 runtime failure。",
    },
    "runtime_progress_stale": {
        "action_id": "refresh_runtime_progress",
        "target_surface": "runtime_progress_observer",
        "summary": "刷新 runtime progress、supervision 和 recovery surface，确认当前执行点。",
    },
    "quality_toil_repeat": {
        "action_id": "inspect_repeated_feedback_reason",
        "target_surface": "ai_first_feedback_ledger",
        "summary": "复盘重复反馈原因并决定是否需要 repo-level 系统修复。",
    },
}
QUALITY_LEARNING_FIX_LAYERS = {
    "quality_toil_repeat": {
        "impact_entry": "ai_first_feedback_ledger",
        "suggested_fix_layer": "feedback-ledger governance",
    },
    "route_back_open": {
        "impact_entry": "same_line_route_back",
        "suggested_fix_layer": "route-back controller contract",
    },
    "ai_reviewer_trace_gap": {
        "impact_entry": "ai_reviewer_runtime_workflow",
        "suggested_fix_layer": "AI reviewer trace contract",
    },
    "artifact_rebuild_pending": {
        "impact_entry": "artifact_runtime_proof",
        "suggested_fix_layer": "artifact rebuild proof layer",
    },
    "predraft_gap": {
        "impact_entry": "pre_draft_quality_runtime",
        "suggested_fix_layer": "pre-draft quality contract",
    },
    "runtime_progress_stale": {
        "impact_entry": "runtime_progress_observer",
        "suggested_fix_layer": "runtime progress observer",
    },
    "manual_judgment_pending": {
        "impact_entry": "human_decision_gate",
        "suggested_fix_layer": "human gate governance",
    },
}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object, default: str | None = None) -> str | None:
    text = str(value or "").strip()
    return text or default


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_key(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")[:96] or "feedback"


def stable_feedback_ledger_path(*, study_root: str | Path) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "runtime"
        / "ai_first_feedback_ledger"
        / "latest.json"
    )


def _evidence_refs(*paths: object) -> list[str]:
    refs: list[str] = []
    for value in paths:
        text = _text(value)
        if text and text not in refs:
            refs.append(text)
    return refs


def _event(
    *,
    category: str,
    severity: str,
    reason: str,
    next_action: str | None,
    source_surface: str,
    evidence_refs: list[str],
    human_review_required: bool = False,
) -> dict[str, Any]:
    return {
        "event_key": f"{category}:{_safe_key(reason)}",
        "category": category,
        "severity": severity,
        "reason": reason,
        "next_action": next_action,
        "action_recommendation": _action_recommendation(category=category, source_next_action=next_action),
        "source_surface": source_surface,
        "evidence_refs": evidence_refs,
        "human_review_required": human_review_required,
    }


def _action_recommendation(*, category: str, source_next_action: str | None = None) -> dict[str, Any]:
    template = dict(ACTION_RECOMMENDATIONS.get(category) or {})
    if not template:
        template = {
            "action_id": "inspect_feedback_signal",
            "target_surface": "ai_first_feedback_state",
            "summary": "检查当前 AI-first feedback signal 并选择对应运行入口。",
        }
    return {
        **template,
        "source_next_action": source_next_action,
        "authority": "observability_only",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "can_mutate_runtime": False,
    }


def _state_section(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    return _mapping(payload.get(key))


def _pre_draft_event(default_entry: Mapping[str, Any], refs: Mapping[str, Any]) -> dict[str, Any] | None:
    pre_draft = _state_section(default_entry, "pre_draft")
    if not default_entry:
        return None
    if pre_draft.get("draft_ready") is True and pre_draft.get("route_back_required") is not True:
        return None
    reason = (
        _text(pre_draft.get("route_back_reason"))
        or _text(pre_draft.get("summary"))
        or "pre_draft_readiness_not_closed"
    )
    return _event(
        category="predraft_gap",
        severity="warning",
        reason=reason,
        next_action=_text(default_entry.get("recommended_next_step")),
        source_surface=_text(pre_draft.get("surface"), "pre_draft_quality_runtime") or "pre_draft_quality_runtime",
        evidence_refs=_evidence_refs(refs.get("medical_manuscript_blueprint_path")),
    )


def _ai_reviewer_event(
    default_entry: Mapping[str, Any],
    operations_dashboard: Mapping[str, Any],
    refs: Mapping[str, Any],
) -> dict[str, Any] | None:
    workflow = _state_section(default_entry, "ai_reviewer_workflow")
    maintainer = _mapping(operations_dashboard.get("maintainer_view"))
    dashboard_trace = _mapping(maintainer.get("ai_reviewer_trace"))
    trace_complete = _bool(workflow.get("ai_reviewer_trace_complete"))
    if trace_complete is None:
        trace_complete = _bool(dashboard_trace.get("complete"))
    finalize_authorized = workflow.get("finalize_authorized") is True
    submission_authorized = workflow.get("submission_authorized") is True
    if trace_complete is True and finalize_authorized and submission_authorized:
        return None
    if not workflow and trace_complete is not False:
        return None
    reason = _text(workflow.get("summary")) or "ai_reviewer_trace_or_submission_authority_not_closed"
    return _event(
        category="ai_reviewer_trace_gap",
        severity="critical",
        reason=reason,
        next_action=_text(default_entry.get("recommended_next_step")),
        source_surface=_text(workflow.get("surface"), "ai_reviewer_runtime_workflow") or "ai_reviewer_runtime_workflow",
        evidence_refs=_evidence_refs(
            refs.get("publication_eval_path"),
            refs.get("medical_prose_review_path"),
        ),
        human_review_required=True,
    )


def _route_back_event(
    default_entry: Mapping[str, Any],
    operations_dashboard: Mapping[str, Any],
    refs: Mapping[str, Any],
) -> dict[str, Any] | None:
    route_back = _state_section(default_entry, "route_back")
    maintainer = _mapping(operations_dashboard.get("maintainer_view"))
    dashboard_route = _mapping(maintainer.get("route_back"))
    route_count = _int(dashboard_route.get("count"))
    required = bool(route_back.get("required")) or route_count > 0
    if not required:
        return None
    target = _text(route_back.get("ai_reviewer_target")) or _text(route_back.get("pre_draft_target")) or _text(
        dashboard_route.get("target")
    )
    reason = _text(route_back.get("reason")) or (f"route_back_target:{target}" if target else "route_back_open")
    return _event(
        category="route_back_open",
        severity="warning",
        reason=reason,
        next_action=_text(default_entry.get("recommended_next_step")),
        source_surface="ai_first_default_entry_state",
        evidence_refs=_evidence_refs(refs.get("publication_eval_path"), refs.get("controller_decision_path")),
    )


def _artifact_event(
    default_entry: Mapping[str, Any],
    operations_dashboard: Mapping[str, Any],
    refs: Mapping[str, Any],
) -> dict[str, Any] | None:
    artifact = _state_section(default_entry, "artifact_proof")
    maintainer = _mapping(operations_dashboard.get("maintainer_view"))
    artifact_stale = _mapping(maintainer.get("artifact_stale"))
    stale_count = _int(artifact_stale.get("stale_artifact_count"))
    pending = bool(artifact.get("rebuild_pending")) or stale_count > 0
    if not pending:
        return None
    reason = _text(artifact.get("summary")) or "canonical_artifact_rebuild_pending"
    return _event(
        category="artifact_rebuild_pending",
        severity="warning",
        reason=reason,
        next_action="rebuild_from_canonical_source",
        source_surface=_text(artifact.get("surface"), "artifact_runtime_proof") or "artifact_runtime_proof",
        evidence_refs=_evidence_refs(
            refs.get("ai_first_observability_delivery_manifest_path"),
            refs.get("delivery_manifest_path"),
        ),
    )


def _manual_judgment_event(progress_snapshot: Mapping[str, Any], default_entry: Mapping[str, Any]) -> dict[str, Any] | None:
    human_review_required = bool(progress_snapshot.get("needs_user_decision")) or bool(
        progress_snapshot.get("needs_physician_decision")
    ) or bool(default_entry.get("human_review_required"))
    if not human_review_required:
        return None
    reason = _text(progress_snapshot.get("user_decision_summary")) or _text(
        progress_snapshot.get("physician_decision_summary")
    ) or "manual_judgment_pending"
    return _event(
        category="manual_judgment_pending",
        severity="info",
        reason=reason,
        next_action=_text(progress_snapshot.get("next_system_action")),
        source_surface="study_progress",
        evidence_refs=[],
        human_review_required=True,
    )


def _runtime_stale_event(progress_snapshot: Mapping[str, Any]) -> dict[str, Any] | None:
    progress_freshness = _mapping(progress_snapshot.get("progress_freshness"))
    if _text(progress_freshness.get("status")) != "stale":
        return None
    reason = _text(progress_freshness.get("summary")) or "runtime_progress_stale"
    return _event(
        category="runtime_progress_stale",
        severity="warning",
        reason=reason,
        next_action=_text(progress_snapshot.get("next_system_action")),
        source_surface="study_progress.progress_freshness",
        evidence_refs=[],
    )


def _ledger_events(feedback_ledger: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    return [dict(item) for item in _list((feedback_ledger or {}).get("events")) if isinstance(item, Mapping)]


def _repeat_events(
    events: list[Mapping[str, Any]],
    *,
    active_event_keys: set[str],
) -> list[dict[str, Any]]:
    repeat_events: list[dict[str, Any]] = []
    for item in events:
        if str(item.get("event_key")) not in active_event_keys:
            continue
        if item.get("closed_at") is not None:
            continue
        repeat_count = _int(item.get("repeat_count"))
        if repeat_count <= 1:
            continue
        category = _text(item.get("category"), "unknown") or "unknown"
        reason = _text(item.get("reason"), category) or category
        repeat_events.append(
            _event(
                category="quality_toil_repeat",
                severity="warning",
                reason=f"{category}:{reason}",
                next_action="inspect_repeated_feedback_reason",
                source_surface=LEDGER_SURFACE,
                evidence_refs=[str(value) for value in _list(item.get("evidence_refs")) if str(value).strip()],
            )
        )
    return repeat_events


def _counts(events: list[Mapping[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, int] = {}
    for item in events:
        category = _text(item.get("category"), "unknown") or "unknown"
        by_category[category] = by_category.get(category, 0) + 1
    return {
        "open_feedback_count": len(events),
        "repeat_toil_count": by_category.get("quality_toil_repeat", 0),
        "open_route_back_count": by_category.get("route_back_open", 0),
        "artifact_rebuild_pending_count": by_category.get("artifact_rebuild_pending", 0),
        "ai_reviewer_trace_incomplete_count": by_category.get("ai_reviewer_trace_gap", 0),
        "manual_judgment_pending_count": by_category.get("manual_judgment_pending", 0),
        "by_category": by_category,
    }


def _primary_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not events:
        return None
    return sorted(events, key=lambda item: EVENT_PRIORITY.get(str(item.get("category")), 99))[0]


def _open_closed(item: Mapping[str, Any]) -> str:
    return "closed" if item.get("closed_at") is not None else "open"


def _counter_bucket() -> dict[str, int]:
    return {"open": 0, "closed": 0}


def _increment_bucket(target: dict[str, dict[str, int]], key: str, open_closed: str) -> None:
    bucket = target.setdefault(key, _counter_bucket())
    bucket[open_closed] = bucket.get(open_closed, 0) + 1


def _repeat_toil_rows(feedback_ledger: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _ledger_events(feedback_ledger):
        if _int(item.get("repeat_count")) <= 1:
            continue
        if _text(item.get("category")) == "quality_toil_repeat":
            continue
        category = _text(item.get("category"), "unknown") or "unknown"
        reason = _text(item.get("reason"), category) or category
        source_surface = _text(item.get("source_surface"), "unknown") or "unknown"
        rows.append(
            {
                "event_key": _text(item.get("event_key"), f"{category}:{_safe_key(reason)}"),
                "category": category,
                "reason": reason,
                "source_surface": source_surface,
                "open_closed": _open_closed(item),
                "repeat_count": _int(item.get("repeat_count")),
                "first_seen": _text(item.get("first_seen")),
                "last_seen": _text(item.get("last_seen")),
                "closed_at": _text(item.get("closed_at")),
                "action_recommendation": _action_recommendation(
                    category=category,
                    source_next_action=_text(item.get("next_action")),
                ),
            }
        )
    return rows


def _repeat_toil_priority(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    selected = sorted(
        rows,
        key=lambda item: (
            0 if item.get("open_closed") == "open" else 1,
            EVENT_PRIORITY.get(str(item.get("category")), 99),
            -_int(item.get("repeat_count")),
            str(item.get("reason") or ""),
        ),
    )[0]
    return dict(selected)


def _repeat_toil_summary(*, open_count: int, closed_count: int) -> str:
    if open_count:
        return f"{open_count} 个重复 AI-first 运行反馈信号仍处于打开状态。"
    if closed_count:
        return f"{closed_count} 个重复 AI-first 运行反馈信号已经关闭；当前没有打开的重复 toil。"
    return "当前没有重复 AI-first 运行反馈信号。"


def _repeat_toil_analytics(feedback_ledger: Mapping[str, Any] | None) -> dict[str, Any]:
    rows = _repeat_toil_rows(feedback_ledger)
    by_category: dict[str, dict[str, int]] = {}
    by_reason: dict[str, dict[str, int]] = {}
    by_source_surface: dict[str, dict[str, int]] = {}
    by_open_closed = _counter_bucket()
    for item in rows:
        open_closed = str(item["open_closed"])
        by_open_closed[open_closed] = by_open_closed.get(open_closed, 0) + 1
        _increment_bucket(by_category, str(item["category"]), open_closed)
        _increment_bucket(by_reason, str(item["reason"]), open_closed)
        _increment_bucket(by_source_surface, str(item["source_surface"]), open_closed)
    return {
        "surface": "ai_first_feedback_repeat_toil_analytics",
        "authority": "observability_only",
        "summary": _repeat_toil_summary(
            open_count=by_open_closed.get("open", 0),
            closed_count=by_open_closed.get("closed", 0),
        ),
        "priority": _repeat_toil_priority(rows),
        "by_category": by_category,
        "by_reason": by_reason,
        "by_source_surface": by_source_surface,
        "by_open_closed": by_open_closed,
        "authority_contract": {
            "analytics_can_authorize_quality": False,
            "analytics_can_authorize_submission": False,
            "analytics_records_manuscript_content": False,
        },
    }


def _queue_open_events(
    *,
    feedback_state: Mapping[str, Any],
    feedback_ledger: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    ledger_events = _ledger_events(feedback_ledger)
    if ledger_events:
        return [dict(item) for item in ledger_events if item.get("closed_at") is None]
    return [dict(item) for item in _list(feedback_state.get("events")) if isinstance(item, Mapping)]


def _paper_quality_queue_events(
    *,
    feedback_state: Mapping[str, Any],
    feedback_ledger: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in _queue_open_events(feedback_state=feedback_state, feedback_ledger=feedback_ledger)
        if _text(item.get("category")) != "quality_toil_repeat"
    ]


def _queue_frequency(item: Mapping[str, Any]) -> int:
    return max(_int(item.get("repeat_count")), 1)


def _queue_category_rank(category: str) -> int:
    if category == "quality_toil_repeat":
        return -1
    return EVENT_PRIORITY.get(category, 99)


def _quality_learning_queue_item(item: Mapping[str, Any]) -> dict[str, Any]:
    category = _text(item.get("category"), "unknown") or "unknown"
    reason = _text(item.get("reason"), category) or category
    action = _mapping(item.get("action_recommendation"))
    layer = dict(QUALITY_LEARNING_FIX_LAYERS.get(category) or {})
    impact_entry = (
        _text(layer.get("impact_entry"))
        or _text(action.get("target_surface"))
        or _text(item.get("source_surface"), "unknown")
        or "unknown"
    )
    suggested_fix_layer = _text(layer.get("suggested_fix_layer"), "inspect source read-model") or "inspect source read-model"
    return {
        "category": category,
        "reason": reason,
        "frequency": _queue_frequency(item),
        "impact_entry": impact_entry,
        "suggested_fix_layer": suggested_fix_layer,
        "source_surface": _text(item.get("source_surface"), impact_entry) or impact_entry,
    }


def _aggregate_quality_learning_queue_items(events: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for event in events:
        item = _quality_learning_queue_item(event)
        key = (
            str(item["category"]),
            str(item["reason"]),
            str(item["impact_entry"]),
            str(item["suggested_fix_layer"]),
        )
        prior = grouped.get(key)
        if prior is None:
            grouped[key] = item
            continue
        prior["frequency"] = _int(prior.get("frequency")) + _int(item.get("frequency"))
        source_surface = str(item.get("source_surface") or "")
        if source_surface and source_surface not in str(prior.get("source_surface") or "").split(", "):
            prior["source_surface"] = f"{prior.get('source_surface')}, {source_surface}"
    return sorted(
        grouped.values(),
        key=lambda item: (
            -_int(item.get("frequency")),
            _queue_category_rank(str(item.get("category") or "")),
            str(item.get("reason") or ""),
        ),
    )


def build_ai_first_quality_learning_queue(
    *,
    feedback_state: Mapping[str, Any],
    feedback_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a governance-only maintenance queue from sanitized feedback signals."""

    open_events = _paper_quality_queue_events(feedback_state=feedback_state, feedback_ledger=feedback_ledger)
    items = _aggregate_quality_learning_queue_items(open_events)
    return {
        "surface": QUALITY_LEARNING_QUEUE_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": QUALITY_LEARNING_QUEUE_READ_MODEL,
        "authority": "governance_only",
        "source_authority": "observability_only",
        "status": "attention_required" if items else "on_track",
        "summary": (
            f"{len(items)} 个 AI-first quality learning queue 维护项处于打开状态。"
            if items
            else "当前没有打开的 AI-first quality learning queue 维护项。"
        ),
        "items": items,
        "counts": {
            "open_queue_item_count": len(items),
            "open_signal_frequency": sum(_int(item.get("frequency")) for item in items),
            "by_reason": {str(item["reason"]): _int(item.get("frequency")) for item in items},
            "by_impact_entry": {
                str(entry): sum(_int(item.get("frequency")) for item in items if item.get("impact_entry") == entry)
                for entry in sorted({str(item.get("impact_entry")) for item in items if item.get("impact_entry")})
            },
            "by_suggested_fix_layer": {
                str(layer): sum(_int(item.get("frequency")) for item in items if item.get("suggested_fix_layer") == layer)
                for layer in sorted(
                    {str(item.get("suggested_fix_layer")) for item in items if item.get("suggested_fix_layer")}
                )
            },
        },
        "authority_contract": {
            "queue_can_authorize_quality": False,
            "queue_can_authorize_finalize": False,
            "queue_can_authorize_submission": False,
            "queue_can_mutate_runtime": False,
            "queue_records_manuscript_content": False,
            "queue_exposes_raw_logs_prompts_or_tokens": False,
            "repeat_toil_is_quality_gate": False,
        },
    }


def _operations_report_priority(item: Mapping[str, Any], *, rank: int, priority_type: str) -> dict[str, Any]:
    reason = _text(item.get("reason"), "unknown") or "unknown"
    frequency = _int(item.get("frequency")) or _queue_frequency(item)
    impact_entry = _text(item.get("impact_entry"), "unknown") or "unknown"
    suggested_fix_layer = _text(item.get("suggested_fix_layer"), "inspect source read-model") or "inspect source read-model"
    category = _text(item.get("category"), "unknown") or "unknown"
    return {
        "priority_rank": rank,
        "priority_type": priority_type,
        "category": category,
        "reason": reason,
        "frequency": frequency,
        "impact_entry": impact_entry,
        "suggested_fix_layer": suggested_fix_layer,
        "maintenance_priority": f"{reason} | frequency={frequency} | impact={impact_entry} | fix_layer={suggested_fix_layer}",
        "source_surface": _text(item.get("source_surface"), impact_entry) or impact_entry,
        "is_open_blocker": priority_type == "open_feedback",
        "is_quality_gate": False,
    }


def _repeat_toil_improvement_items(feedback_ledger: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    rows = [
        row
        for row in _repeat_toil_rows(feedback_ledger)
        if row.get("open_closed") == "open"
    ]
    return _aggregate_quality_learning_queue_items(rows)


def build_ai_first_quality_learning_operations_report(
    *,
    feedback_state: Mapping[str, Any],
    feedback_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a maintainer-facing operations report from sanitized quality-learning signals."""

    queue = build_ai_first_quality_learning_queue(
        feedback_state=feedback_state,
        feedback_ledger=feedback_ledger,
    )
    open_feedback_priorities = [
        _operations_report_priority(item, rank=index + 1, priority_type="open_feedback")
        for index, item in enumerate(queue["items"])
    ]
    repeat_toil_items = _repeat_toil_improvement_items(feedback_ledger)
    system_improvement_priorities = [
        _operations_report_priority(item, rank=index + 1, priority_type="system_improvement")
        for index, item in enumerate(repeat_toil_items)
    ]
    return {
        "surface": QUALITY_LEARNING_OPERATIONS_REPORT_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": QUALITY_LEARNING_OPERATIONS_REPORT_READ_MODEL,
        "authority": "maintainer_operations_only",
        "source_authority": "observability_only",
        "status": "attention_required" if open_feedback_priorities or system_improvement_priorities else "on_track",
        "summary": (
            f"{len(open_feedback_priorities)} 个 open feedback 维护优先项；"
            f"{len(system_improvement_priorities)} 个 repeat-toil 系统改进优先项。"
        ),
        "open_feedback_priorities": open_feedback_priorities,
        "system_improvement_priorities": system_improvement_priorities,
        "quality_learning_queue": queue,
        "counts": {
            "open_feedback_priority_count": len(open_feedback_priorities),
            "open_feedback_frequency": sum(_int(item.get("frequency")) for item in open_feedback_priorities),
            "system_improvement_priority_count": len(system_improvement_priorities),
            "system_improvement_frequency": sum(
                _int(item.get("frequency")) for item in system_improvement_priorities
            ),
        },
        "authority_contract": {
            "report_can_authorize_quality": False,
            "report_can_authorize_finalize": False,
            "report_can_authorize_submission": False,
            "report_can_mutate_runtime": False,
            "closed_feedback_counts_as_open_blocker": False,
            "repeat_toil_is_quality_gate": False,
            "report_records_manuscript_content": False,
            "report_exposes_raw_logs_prompts_or_tokens": False,
        },
    }


def _has_feedback_inputs(progress_snapshot: Mapping[str, Any]) -> bool:
    return bool(
        progress_snapshot.get("ai_first_default_entry_state")
        or progress_snapshot.get("ai_first_operations_dashboard")
        or progress_snapshot.get("ai_first_observability_snapshots")
    )


def build_ai_first_feedback_state(
    *,
    progress_snapshot: Mapping[str, Any],
    feedback_ledger: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    default_entry = _mapping(progress_snapshot.get("ai_first_default_entry_state"))
    operations_dashboard = _mapping(progress_snapshot.get("ai_first_operations_dashboard"))
    refs = _mapping(progress_snapshot.get("refs"))
    events = [
        item
        for item in (
            _pre_draft_event(default_entry, refs),
            _ai_reviewer_event(default_entry, operations_dashboard, refs),
            _route_back_event(default_entry, operations_dashboard, refs),
            _artifact_event(default_entry, operations_dashboard, refs),
            _manual_judgment_event(progress_snapshot, default_entry),
            _runtime_stale_event(progress_snapshot),
        )
        if item is not None
    ]
    active_event_keys = {str(item.get("event_key")) for item in events if item.get("event_key")}
    events.extend(_repeat_events(_ledger_events(feedback_ledger), active_event_keys=active_event_keys))
    primary = _primary_event(events)
    has_inputs = _has_feedback_inputs(progress_snapshot)
    if not has_inputs:
        status = "feedback_observer_incomplete"
        summary = "AI-first feedback observer 缺少 default-entry 或 operations 输入，不能判断运行反馈是否 on-track。"
    elif events:
        status = "attention_required"
        summary = f"{len(events)} 个 AI-first 运行反馈信号需要处理。"
    else:
        status = "on_track"
        summary = "当前没有新的 AI-first 运行反馈阻塞。"
    current_stage = _text(progress_snapshot.get("current_stage"), "unknown") or "unknown"
    next_step = _text(progress_snapshot.get("next_system_action")) or _text(default_entry.get("recommended_next_step"))
    primary_action = dict((primary or {}).get("action_recommendation") or {}) if primary else None
    quality_learning_queue = build_ai_first_quality_learning_queue(
        feedback_state={"events": events},
        feedback_ledger=feedback_ledger,
    )
    quality_learning_operations_report = build_ai_first_quality_learning_operations_report(
        feedback_state={"events": events},
        feedback_ledger=feedback_ledger,
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "authority": "observability_only",
        "status": status,
        "summary": summary,
        "current_stage": current_stage,
        "primary_feedback": primary,
        "primary_action": primary_action,
        "user_view": {
            "current_stage": current_stage,
            "primary_feedback_reason": _text((primary or {}).get("reason")) if primary else None,
            "next_step": _text((primary or {}).get("next_action")) or next_step,
            "next_action": _text((primary_action or {}).get("summary")) or _text((primary or {}).get("next_action")) or next_step,
            "human_review_required": any(bool(item.get("human_review_required")) for item in events),
        },
        "maintainer_view": {
            "events": events,
            "source_surfaces": sorted({str(item.get("source_surface")) for item in events if item.get("source_surface")}),
            "repeat_toil_analytics": _repeat_toil_analytics(feedback_ledger),
            "quality_learning_queue": quality_learning_queue,
            "quality_learning_operations_report": quality_learning_operations_report,
        },
        "quality_learning_queue": quality_learning_queue,
        "quality_learning_operations_report": quality_learning_operations_report,
        "events": events,
        "counts": _counts(events),
        "authority_contract": {
            "feedback_can_authorize_quality": False,
            "feedback_can_authorize_finalize": False,
            "feedback_can_authorize_submission": False,
            "feedback_can_mutate_runtime": False,
            "feedback_actions_can_authorize_quality": False,
            "feedback_actions_can_authorize_finalize": False,
            "feedback_actions_can_authorize_submission": False,
            "feedback_actions_can_mutate_runtime": False,
            "quality_learning_queue_can_authorize_quality": False,
            "quality_learning_queue_can_authorize_finalize": False,
            "quality_learning_queue_can_authorize_submission": False,
            "quality_learning_queue_records_manuscript_content": False,
            "quality_learning_operations_report_can_authorize_quality": False,
            "quality_learning_operations_report_can_authorize_finalize": False,
            "quality_learning_operations_report_can_authorize_submission": False,
            "quality_learning_operations_report_records_manuscript_content": False,
            "repeat_toil_is_quality_gate": False,
            "mechanical_feedback_is_projection_only": True,
        },
    }


def read_feedback_ledger(*, study_root: str | Path) -> dict[str, Any] | None:
    path = stable_feedback_ledger_path(study_root=study_root)
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _updated_ledger_events(
    *,
    existing_events: list[dict[str, Any]],
    active_events: list[Mapping[str, Any]],
    observed_at: str,
) -> list[dict[str, Any]]:
    by_key = {str(item.get("event_key")): dict(item) for item in existing_events if item.get("event_key")}
    active_keys = {str(item.get("event_key")) for item in active_events if item.get("event_key")}
    updated: list[dict[str, Any]] = []
    for active in active_events:
        key = str(active.get("event_key"))
        prior = by_key.get(key)
        event = dict(active)
        event["first_seen"] = prior.get("first_seen") if prior else observed_at
        event["last_seen"] = observed_at
        event["repeat_count"] = _int((prior or {}).get("repeat_count")) + 1 if prior else 1
        event["closed_at"] = None
        updated.append(event)
    for prior in existing_events:
        key = str(prior.get("event_key"))
        if key in active_keys:
            continue
        closed = dict(prior)
        if closed.get("closed_at") is None:
            closed["closed_at"] = observed_at
        updated.append(closed)
    return updated


def materialize_ai_first_feedback_ledger(
    *,
    study_root: str | Path,
    feedback_state: Mapping[str, Any],
    observed_at: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    path = stable_feedback_ledger_path(study_root=resolved_study_root)
    observed = observed_at or _utc_now()
    existing = read_feedback_ledger(study_root=resolved_study_root) or {}
    active_events = [dict(item) for item in _list(feedback_state.get("events")) if isinstance(item, Mapping)]
    events = _updated_ledger_events(
        existing_events=_ledger_events(existing),
        active_events=active_events,
        observed_at=observed,
    )
    payload = {
        "surface": LEDGER_SURFACE,
        "schema_version": LEDGER_SCHEMA_VERSION,
        "study_root": str(resolved_study_root),
        "updated_at": observed,
        "authority": "observability_only",
        "events": events,
        "open_event_count": sum(1 for item in events if item.get("closed_at") is None),
        "closed_event_count": sum(1 for item in events if item.get("closed_at") is not None),
        "repeat_toil_analytics": _repeat_toil_analytics({"events": events}),
        "quality_learning_queue": build_ai_first_quality_learning_queue(
            feedback_state={"events": active_events},
            feedback_ledger={"events": events},
        ),
        "quality_learning_operations_report": build_ai_first_quality_learning_operations_report(
            feedback_state={"events": active_events},
            feedback_ledger={"events": events},
        ),
        "authority_contract": {
            "ledger_can_authorize_quality": False,
            "ledger_can_authorize_submission": False,
            "ledger_records_manuscript_content": False,
            "ledger_quality_learning_queue_can_authorize_quality": False,
            "ledger_quality_learning_queue_can_authorize_finalize": False,
            "ledger_quality_learning_queue_can_authorize_submission": False,
            "ledger_quality_learning_operations_report_can_authorize_quality": False,
            "ledger_quality_learning_operations_report_can_authorize_submission": False,
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def materialize_ai_first_feedback_state(
    *,
    study_root: str | Path,
    progress_snapshot: Mapping[str, Any],
    observed_at: str | None = None,
) -> dict[str, Any]:
    initial_ledger = read_feedback_ledger(study_root=study_root)
    initial_state = build_ai_first_feedback_state(
        progress_snapshot=progress_snapshot,
        feedback_ledger=initial_ledger,
    )
    ledger = materialize_ai_first_feedback_ledger(
        study_root=study_root,
        feedback_state=initial_state,
        observed_at=observed_at,
    )
    state = build_ai_first_feedback_state(progress_snapshot=progress_snapshot, feedback_ledger=ledger)
    state["ledger"] = {
        "surface": LEDGER_SURFACE,
        "path": str(stable_feedback_ledger_path(study_root=study_root)),
        "open_event_count": ledger["open_event_count"],
        "closed_event_count": ledger["closed_event_count"],
    }
    return state
