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
LOW_LEVEL_FIELD_HINTS = ("raw_terminal_log", "full_prompt", "prompt", "secret", "token", "log_path")
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
    priority = {
        "ai_reviewer_trace_gap": 0,
        "predraft_gap": 1,
        "route_back_open": 2,
        "artifact_rebuild_pending": 3,
        "runtime_progress_stale": 4,
        "manual_judgment_pending": 5,
        "quality_toil_repeat": 6,
    }
    if not events:
        return None
    return sorted(events, key=lambda item: priority.get(str(item.get("category")), 99))[0]


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
        },
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
        "authority_contract": {
            "ledger_can_authorize_quality": False,
            "ledger_can_authorize_submission": False,
            "ledger_records_manuscript_content": False,
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
