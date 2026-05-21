from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from ..rendering import list_html, status_chip
from ..source_refs import source_ref_allowed


def build_conversation_projection(value: Mapping[str, Any] | None, study_id: str) -> dict[str, Any]:
    payload = _mapping(value)
    if not payload:
        return {
            "surface_kind": "mas_progress_portal_conversation_panel",
            "status": "missing",
            "study_id": study_id,
            "timeline_summary": {"item_count": 0, "counts_by_kind": {}, "missing_field_item_count": 0},
            "timeline_items": [],
            "source_refs": [],
            "conditions": {"missing": ["conversation_read_model"]},
            "authority": _conversation_authority(),
        }
    if _non_empty_text(payload.get("surface_kind")) != "mas_runtime_conversation_read_model":
        return {
            "surface_kind": "mas_progress_portal_conversation_panel",
            "status": "missing",
            "study_id": study_id,
            "timeline_summary": {"item_count": 0, "counts_by_kind": {}, "missing_field_item_count": 0},
            "timeline_items": [],
            "source_refs": [],
            "conditions": {"missing": ["mas_runtime_conversation_read_model"]},
            "authority": _conversation_authority(),
        }
    items = [
        _conversation_item(item)
        for item in _mapping_list(payload.get("timeline"))
        if _non_empty_text(item.get("study_id")) == study_id
    ]
    items = [item for item in items if item is not None]
    refs = _conversation_source_refs(payload, study_id)
    missing = [] if items else ["conversation_timeline"]
    return {
        "surface_kind": "mas_progress_portal_conversation_panel",
        "status": "available" if items else "missing",
        "study_id": study_id,
        "read_model_ref": "artifacts/runtime/conversation_read_model/latest.json",
        "timeline_summary": _conversation_timeline_summary(items),
        "timeline_items": _visible_conversation_items(items),
        "source_refs": refs,
        "conditions": {"missing": missing},
        "authority": _conversation_authority(),
    }


def render_conversation_section(conversation: Mapping[str, Any]) -> str:
    status = _non_empty_text(conversation.get("status")) or "missing"
    summary = _conversation_summary_text(_mapping(conversation.get("timeline_summary")))
    items = _mapping_list(conversation.get("timeline_items"))
    refs = _string_list(conversation.get("source_refs"))
    return (
        '<section class="panel wide"><h2>执行器对话 '
        + status_chip(status)
        + "</h2>"
        + (f"<p>{escape(summary)}</p>" if summary else "")
        + _conversation_timeline_html(items)
        + "<h3>对话来源</h3>"
        + list_html(refs, empty_text="缺少 conversation source refs。")
        + "</section>"
    )


def _conversation_authority() -> dict[str, Any]:
    return {
        "kind": "read_only_runtime_conversation_projection",
        "writes_authority_surface": False,
        "can_execute_controller_actions": False,
    }


def _conversation_item(item: Mapping[str, Any]) -> dict[str, Any] | None:
    kind = _non_empty_text(item.get("item_kind"))
    if kind is None:
        return None
    projected = {
        "sequence": item.get("sequence") if isinstance(item.get("sequence"), int) else None,
        "item_kind": kind,
        "occurred_at": _non_empty_text(item.get("occurred_at")),
        "message_id": _non_empty_text(item.get("message_id")),
        "message_status": _non_empty_text(item.get("message_status")),
        "run_id": _non_empty_text(item.get("run_id")),
        "turn_reason": _non_empty_text(item.get("turn_reason")),
        "turn_status": _non_empty_text(item.get("turn_status")),
        "event_name": _non_empty_text(item.get("event_name")),
        "runtime_status": _non_empty_text(item.get("runtime_status")),
        "source_ref": _non_empty_text(item.get("source_ref")),
        "blocker_refs": _conversation_refs(item.get("blocker_refs")),
        "action_refs": _conversation_refs(item.get("action_refs")),
        "tool_refs": _conversation_refs(item.get("tool_refs")),
    }
    projected["summary"] = _conversation_item_summary(projected)
    return projected


def _conversation_item_summary(item: Mapping[str, Any]) -> str:
    kind = _non_empty_text(item.get("item_kind")) or "conversation_item"
    parts = [_conversation_kind_label(kind)]
    if item.get("message_id"):
        parts.append(f"消息={item['message_id']}")
    if item.get("message_status"):
        parts.append(f"消息状态={item['message_status']}")
    if item.get("run_id"):
        parts.append(f"运行={item['run_id']}")
    if item.get("turn_reason"):
        parts.append(f"原因={item['turn_reason']}")
    if item.get("turn_status"):
        parts.append(f"状态={item['turn_status']}")
    if item.get("event_name"):
        parts.append(f"事件={item['event_name']}")
    for label in ("blocker_refs", "action_refs", "tool_refs"):
        refs = _string_list(item.get(label))
        if refs:
            parts.append(f"{_conversation_ref_label(label)}=" + "; ".join(refs[:3]))
    if item.get("source_ref"):
        parts.append(f"来源={item['source_ref']}")
    return " | ".join(parts)


def _visible_conversation_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = (
        "user_message",
        "turn_receipt",
        "latest_turn_receipt_ref",
        "runtime_control_ref",
        "controller_action_intent_ref",
        "action_or_blocker_ref",
        "live_console_run_ref",
        "live_console_event_ref",
        "runtime_lifecycle_event",
    )
    selected: list[dict[str, Any]] = []
    seen: set[int] = set()
    for kind in priority:
        per_kind = [item for item in items if item.get("item_kind") == kind]
        for item in per_kind[-3:]:
            identity = id(item)
            if identity in seen:
                continue
            selected.append(item)
            seen.add(identity)
    if len(selected) < 12:
        for item in items[-(12 - len(selected)):]:
            identity = id(item)
            if identity in seen:
                continue
            selected.append(item)
            seen.add(identity)
    return sorted(
        selected[:12],
        key=lambda item: (
            item.get("sequence") if isinstance(item.get("sequence"), int) else 10**9,
            _non_empty_text(item.get("item_kind")) or "",
        ),
    )


def _conversation_timeline_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in items:
        kind = _non_empty_text(item.get("item_kind")) or "unknown"
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "item_count": len(items),
        "counts_by_kind": counts,
        "missing_field_item_count": 0,
    }


def _conversation_kind_label(kind: str) -> str:
    return {
        "user_message": "用户消息",
        "turn_receipt": "执行回合",
        "latest_turn_receipt_ref": "最近回合",
        "runtime_control_ref": "运行控制",
        "controller_action_intent_ref": "控制意图",
        "action_or_blocker_ref": "动作/阻塞",
        "live_console_run_ref": "运行控制台",
        "live_console_event_ref": "控制台事件",
        "runtime_lifecycle_event": "运行事件",
    }.get(kind, kind)


def _conversation_ref_label(label: str) -> str:
    return {
        "blocker_refs": "阻塞",
        "action_refs": "动作",
        "tool_refs": "工具",
    }.get(label, label)


def _conversation_refs(value: object) -> list[str]:
    refs: list[str] = []
    for item in _mapping_list(value):
        kind = _non_empty_text(item.get("kind")) or _non_empty_text(item.get("surface_kind")) or "ref"
        text = _first_text(item.get("value"), item.get("source_ref"), item.get("message_id"), item.get("status"))
        if text is not None:
            refs.append(f"{kind}={text}")
    for item in _string_list(value):
        refs.append(item)
    return refs


def _conversation_source_refs(payload: Mapping[str, Any], study_id: str) -> list[str]:
    refs = ["artifacts/runtime/conversation_read_model/latest.json"]
    for item in _mapping_list(payload.get("source_refs")):
        ref_study_id = _non_empty_text(item.get("study_id"))
        if ref_study_id not in (None, study_id):
            continue
        ref = _non_empty_text(item.get("source_ref"))
        if ref is not None and source_ref_allowed(ref):
            refs.append(ref)
    return _dedupe_strings(refs)


def _conversation_timeline_html(items: list[dict[str, Any]]) -> str:
    if not items:
        return "<p>缺少执行器对话时间线。</p>"
    rendered: list[str] = []
    for item in items:
        kind = _non_empty_text(item.get("item_kind")) or "conversation_item"
        sequence = item.get("sequence") if isinstance(item.get("sequence"), int) else None
        anchor = f"conversation-seq-{sequence}" if sequence is not None else f"conversation-{kind}"
        meta: list[str] = []
        if sequence is not None:
            meta.append(f"#{sequence}")
        occurred_at = _non_empty_text(item.get("occurred_at"))
        if occurred_at:
            meta.append(occurred_at)
        run_id = _non_empty_text(item.get("run_id"))
        if run_id:
            meta.append(f"运行 {run_id}")
        source_ref = _non_empty_text(item.get("source_ref"))
        if source_ref:
            meta.append(f"来源 {source_ref}")
        summary = _non_empty_text(item.get("summary")) or kind
        rendered.append(
            '<li id="'
            + escape(anchor, quote=True)
            + '" class="conversation-item conversation-item--'
            + escape(kind, quote=True)
            + '" data-item-kind="'
            + escape(kind, quote=True)
            + '"'
            + (f' data-sequence="{sequence}"' if sequence is not None else "")
            + ">"
            + '<div class="conversation-item__marker" aria-hidden="true"></div>'
            + '<div class="conversation-item__body"><strong>'
            + escape(_conversation_kind_label(kind))
            + "</strong>"
            + ("<span>" + escape(" / ".join(meta)) + "</span>" if meta else "")
            + "<p>"
            + escape(summary)
            + "</p></div></li>"
        )
    return '<ol class="conversation-timeline">' + "".join(rendered) + "</ol>"


def _conversation_summary_text(summary: Mapping[str, Any]) -> str:
    count = summary.get("item_count")
    counts = _mapping(summary.get("counts_by_kind"))
    parts: list[str] = []
    if isinstance(count, int):
        parts.append(f"共 {count} 条")
    for key, label in (
        ("user_message", "用户消息"),
        ("turn_receipt", "执行回合"),
        ("latest_turn_receipt_ref", "最近回合"),
        ("runtime_control_ref", "运行控制"),
        ("action_or_blocker_ref", "动作/阻塞"),
    ):
        value = counts.get(key)
        if isinstance(value, int) and value:
            parts.append(f"{label} {value} 条")
    return "；".join(parts)


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _dedupe_strings(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "build_conversation_projection",
    "render_conversation_section",
]
