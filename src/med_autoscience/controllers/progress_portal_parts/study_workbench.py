from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from .rendering import list_html, status_chip
from .route_decision_trail import (
    build_route_decision_trail_payload,
    render_route_decision_trail_section,
)
from .source_refs import source_ref_allowed, source_refs
from .status_display import display_text


ARTIFACT_GROUPS = (
    "draft",
    "figures_tables",
    "current_package",
    "review_proof",
    "runtime_evidence",
)

_ARTIFACT_GROUP_LABELS = {
    "draft": "草稿",
    "figures_tables": "图表",
    "current_package": "当前交付包",
    "review_proof": "复审证据",
    "runtime_evidence": "运行证据",
}

_GROUP_ALIASES = {
    "draft": "draft",
    "manuscript_draft": "draft",
    "paper_draft": "draft",
    "figures_tables": "figures_tables",
    "figures": "figures_tables",
    "tables": "figures_tables",
    "figure_table": "figures_tables",
    "current_package": "current_package",
    "package": "current_package",
    "delivery_package": "current_package",
    "review_proof": "review_proof",
    "review": "review_proof",
    "publication_eval": "review_proof",
    "runtime_evidence": "runtime_evidence",
    "runtime": "runtime_evidence",
    "runtime_artifact": "runtime_evidence",
}


def build_study_workbench_payload(
    progress: Mapping[str, Any] | None,
    cockpit: Mapping[str, Any] | None,
    runtime: Mapping[str, Any] | None,
    package: Mapping[str, Any] | None,
    study_id: str,
    conversation_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_progress = _mapping(progress)
    resolved_cockpit = _mapping(cockpit)
    resolved_runtime = _mapping(runtime)
    resolved_package = _mapping(package)
    resolved_study_id = _non_empty_text(study_id) or _non_empty_text(resolved_progress.get("study_id")) or "unknown-study"
    user_visible = _valid_user_visible_projection(resolved_progress.get("user_visible_projection"))
    cockpit_study = _cockpit_study(resolved_cockpit, resolved_study_id)
    artifact_groups = _artifact_groups(resolved_progress, resolved_runtime, resolved_package)
    route_decision_trail = build_route_decision_trail_payload(
        resolved_progress,
        resolved_runtime,
        resolved_package,
        resolved_study_id,
    )
    conversation = _conversation_projection(conversation_payload, resolved_study_id)
    refs = source_refs(resolved_progress, resolved_cockpit, resolved_runtime, resolved_package)
    conditions = _conditions(
        study_id=resolved_study_id,
        progress=resolved_progress,
        cockpit=resolved_cockpit,
        runtime=resolved_runtime,
        package=resolved_package,
        user_visible=user_visible,
        artifact_groups=artifact_groups,
        route_decision_trail=route_decision_trail,
        source_refs=refs,
    )
    overview = {
        "study_id": resolved_study_id,
        "state_label": _first_text(
            user_visible.get("state_label"),
            cockpit_study.get("state_label"),
        ),
        "state_summary": _first_text(
            user_visible.get("state_summary"),
            cockpit_study.get("state_summary"),
        ),
        "next_system_action": _first_text(
            user_visible.get("next_system_action"),
            cockpit_study.get("next_system_action"),
        ),
        "current_blockers": _string_list(user_visible.get("current_blockers")),
    }
    path_stage = {
        "current_stage": _first_text(user_visible.get("current_stage"), cockpit_study.get("current_stage")),
        "current_stage_summary": _non_empty_text(user_visible.get("current_stage_summary")),
        "paper_stage": _first_text(user_visible.get("paper_stage"), cockpit_study.get("paper_stage")),
        "paper_stage_summary": _non_empty_text(user_visible.get("paper_stage_summary")),
        "progress_freshness": _mapping(resolved_progress.get("progress_freshness")),
    }
    runtime_projection = _runtime_projection(resolved_progress, resolved_runtime, cockpit_study)
    return {
        "schema_version": 1,
        "surface_kind": "mas_progress_portal_study_workbench",
        "authority": {
            "kind": "read_model_helper",
            "writes_authority_surface": False,
            "authority_note": "Consumes study progress, workspace cockpit, package/delivery refs, runtime projection, and source refs only.",
        },
        "study_id": resolved_study_id,
        "tabs": [
            {"id": "overview", "label": "概览", "status": _tab_status(overview)},
            {
                "id": "route_decision_trail",
                "label": "路线/决策",
                "status": _non_empty_text(route_decision_trail.get("status")) or "missing",
            },
            {"id": "path_stage", "label": "路径/阶段", "status": _tab_status(path_stage)},
            {"id": "runtime", "label": "运行", "status": _tab_status(runtime_projection)},
            {"id": "artifacts", "label": "产物", "status": _artifact_tab_status(artifact_groups)},
            {"id": "conversation", "label": "执行器对话", "status": conversation["status"]},
            {"id": "source_refs", "label": "来源", "status": "available" if refs else "missing"},
        ],
        "overview": overview,
        "route_decision_trail": route_decision_trail,
        "path_stage": path_stage,
        "runtime": runtime_projection,
        "artifact_groups": artifact_groups,
        "conversation": conversation,
        "source_refs": refs,
        "conditions": conditions,
    }


def render_study_workbench_sections(payload: Mapping[str, Any]) -> str:
    overview = _mapping(payload.get("overview"))
    route_decision_trail = _mapping(payload.get("route_decision_trail"))
    path_stage = _mapping(payload.get("path_stage"))
    runtime = _mapping(payload.get("runtime"))
    artifact_groups = _mapping(payload.get("artifact_groups"))
    conversation = _mapping(payload.get("conversation"))
    conditions = _mapping(payload.get("conditions"))
    refs = _string_list(payload.get("source_refs"))
    return "\n".join(
        [
            '<section class="panel wide">',
            "<h2>单篇论文工作台</h2>",
            "<p>"
            + escape(display_text(overview.get("state_label"), fallback="状态投影缺失", preserve_known_token=False))
            + "</p>",
            "</section>",
            render_route_decision_trail_section(route_decision_trail),
            _key_value_section(
                "路径与阶段",
                {
                    "当前阶段": display_text(path_stage.get("current_stage"), fallback="缺失", preserve_known_token=False),
                    "论文阶段": display_text(path_stage.get("paper_stage"), fallback="缺失", preserve_known_token=False),
                },
            ),
            _key_value_section(
                "运行",
                {
                    "active_run_id": display_text(runtime.get("active_run_id"), fallback="缺失", preserve_known_token=False),
                    "health_status": display_text(runtime.get("health_status"), fallback="缺失", preserve_known_token=False),
                    "supervisor_tick_status": display_text(
                        runtime.get("supervisor_tick_status"),
                        fallback="缺失",
                        preserve_known_token=False,
                    ),
                },
            ),
            _artifact_sections(artifact_groups),
            _conversation_section(conversation),
            '<section class="panel wide"><h2>数据来源</h2>'
            + list_html(refs, empty_text="缺少 source refs。")
            + "</section>",
            '<section class="panel wide"><h2>缺失 / 陈旧 / 冲突</h2>'
            + list_html(_condition_items(conditions), empty_text="当前没有 workbench 条件。")
            + "</section>",
        ]
    )


def _runtime_projection(
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    cockpit_study: Mapping[str, Any],
) -> dict[str, Any]:
    supervision = _mapping(progress.get("supervision"))
    tick_audit = _mapping(runtime.get("supervisor_tick_audit"))
    monitoring = _mapping(cockpit_study.get("monitoring"))
    runtime_health = _mapping(cockpit_study.get("runtime_health_snapshot"))
    worker_liveness = _mapping(runtime_health.get("worker_liveness_state"))
    supervisor_state = _mapping(runtime_health.get("supervisor_state"))
    return {
        "active_run_id": _first_text(
            supervision.get("active_run_id"),
            runtime.get("active_run_id"),
            monitoring.get("active_run_id"),
            worker_liveness.get("active_run_id"),
        ),
        "health_status": _first_text(
            supervision.get("health_status"),
            runtime.get("health_status"),
            monitoring.get("health_status"),
            runtime_health.get("attempt_state"),
        ),
        "supervisor_tick_status": _first_text(
            tick_audit.get("status"),
            supervision.get("supervisor_tick_status"),
            monitoring.get("supervisor_tick_status"),
            supervisor_state.get("status"),
        ),
        "worker_running": worker_liveness.get("worker_running") if "worker_running" in worker_liveness else None,
    }


def _artifact_groups(
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    package: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    groups = {
        group: {"group": group, "label": _ARTIFACT_GROUP_LABELS[group], "status": "missing", "items": []}
        for group in ARTIFACT_GROUPS
    }
    _add_explicit_artifacts(groups, progress.get("artifact_locators"), default_group=None, source="progress.artifact_locators")
    _add_explicit_artifacts(groups, progress.get("delivery_refs"), default_group=None, source="progress.delivery_refs")
    _add_delivery_inspection(groups, progress.get("delivery_inspection"))
    _add_explicit_artifacts(groups, runtime.get("artifact_locators"), default_group="runtime_evidence", source="runtime.artifact_locators")
    _add_explicit_artifacts(groups, runtime.get("runtime_evidence"), default_group="runtime_evidence", source="runtime.runtime_evidence")
    _add_package_refs(groups, package)
    for group in groups.values():
        group["items"] = _dedupe_items(group["items"])
        if group["items"]:
            statuses = {_non_empty_text(item.get("status")) for item in group["items"]}
            group["status"] = "available" if statuses <= {None, "available", "current", "fresh"} else "projected"
    return groups


def _add_delivery_inspection(groups: dict[str, dict[str, Any]], value: object) -> None:
    delivery = _mapping(value)
    for key, item in delivery.items():
        candidate = _mapping(item)
        if not candidate:
            continue
        group = _group_from_text(key) or _group_from_mapping(candidate)
        if group is None:
            continue
        refs = _refs_from_candidate(candidate)
        for ref in refs:
            _add_item(
                groups,
                group,
                ref=ref,
                label=_non_empty_text(candidate.get("label")) or str(key),
                status=_non_empty_text(candidate.get("status")),
                source=f"progress.delivery_inspection.{key}",
            )


def _add_package_refs(groups: dict[str, dict[str, Any]], package: Mapping[str, Any]) -> None:
    _add_explicit_artifacts(groups, package.get("artifact_locators"), default_group=None, source="package.artifact_locators")
    _add_explicit_artifacts(groups, package.get("delivery_refs"), default_group=None, source="package.delivery_refs")
    _add_explicit_artifacts(groups, package.get("package_refs"), default_group="current_package", source="package.package_refs")
    _add_explicit_artifacts(groups, package.get("refs"), default_group="current_package", source="package.refs")


def _add_explicit_artifacts(
    groups: dict[str, dict[str, Any]],
    value: object,
    *,
    default_group: str | None,
    source: str,
) -> None:
    if isinstance(value, str):
        if default_group is not None:
            _add_item(groups, default_group, ref=value, label=None, status=None, source=source)
        return
    if isinstance(value, Mapping):
        group = _group_from_mapping(value) or default_group
        refs = _refs_from_candidate(value)
        if group is not None:
            for ref in refs:
                _add_item(
                    groups,
                    group,
                    ref=ref,
                    label=_non_empty_text(value.get("label")) or _non_empty_text(value.get("name")),
                    status=_non_empty_text(value.get("status")),
                    source=source,
                )
        for key, item in value.items():
            key_group = _group_from_text(str(key))
            if key_group is None and group is not None:
                continue
            _add_explicit_artifacts(
                groups,
                item,
                default_group=key_group,
                source=f"{source}.{key}",
            )
        return
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            _add_explicit_artifacts(groups, item, default_group=default_group, source=source)


def _add_item(
    groups: dict[str, dict[str, Any]],
    group: str,
    *,
    ref: str,
    label: str | None,
    status: str | None,
    source: str,
) -> None:
    if group not in groups or not ref.strip() or not source_ref_allowed(ref):
        return
    groups[group]["items"].append(
        {
            "ref": ref.strip(),
            "label": label or ref.strip(),
            "status": status or "available",
            "source": source,
        }
    )


def _refs_from_candidate(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("ref", "path", "uri", "href"):
        text = _non_empty_text(value.get(key))
        if text is not None:
            refs.append(text)
    for key in ("refs", "paths", "artifact_refs", "package_refs", "delivery_refs"):
        refs.extend(_string_list(value.get(key)))
    return refs


def _conditions(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    cockpit: Mapping[str, Any],
    runtime: Mapping[str, Any],
    package: Mapping[str, Any],
    user_visible: Mapping[str, Any],
    artifact_groups: Mapping[str, Mapping[str, Any]],
    route_decision_trail: Mapping[str, Any],
    source_refs: list[str],
) -> dict[str, list[str]]:
    missing: list[str] = []
    stale: list[str] = []
    conflict: list[str] = []
    if not progress:
        missing.append("study_progress")
    if not user_visible:
        missing.append("user_visible_projection_v2")
    if not package:
        missing.append("package_projection")
    if not source_refs:
        missing.append("source_refs")
    if not _non_empty_text(runtime.get("active_run_id")) and not _mapping(progress.get("supervision")).get("active_run_id"):
        missing.append("runtime_active_run_id")
    for group_name, group in artifact_groups.items():
        if _non_empty_text(group.get("status")) == "missing":
            missing.append(f"artifact_group:{group_name}")
    for item in _string_list(_mapping(route_decision_trail.get("conditions")).get("missing")):
        missing.append(f"route_decision_trail:{item}")
    freshness_status = _non_empty_text(_mapping(progress.get("progress_freshness")).get("status"))
    if freshness_status == "missing":
        missing.append("progress_freshness")
    elif freshness_status == "stale":
        stale.append("progress_freshness")
    for label, payload in (("progress", progress), ("runtime", runtime), ("package", package)):
        payload_study_id = _non_empty_text(payload.get("study_id"))
        if payload_study_id and payload_study_id != study_id:
            conflict.append(f"{label}_study_id_mismatch")
    cockpit_ids = {
        item.get("study_id")
        for item in cockpit.get("studies") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id"))
    }
    if cockpit_ids and study_id not in cockpit_ids:
        conflict.append("cockpit_study_id_mismatch")
    return {"missing": missing, "stale": stale, "conflict": conflict}


def _cockpit_study(cockpit: Mapping[str, Any], study_id: str) -> dict[str, Any]:
    studies = cockpit.get("studies")
    if not isinstance(studies, list):
        return {}
    for item in studies:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            return dict(item)
    return {}


def _valid_user_visible_projection(value: object) -> dict[str, Any]:
    projection = _mapping(value)
    if projection.get("schema_version") != 2:
        return {}
    if not all(_non_empty_text(projection.get(key)) for key in ("writer_state", "user_next", "reason")):
        return {}
    return projection


def _tab_status(payload: Mapping[str, Any]) -> str:
    return "available" if any(value not in (None, "", [], {}) for value in payload.values()) else "missing"


def _artifact_tab_status(groups: Mapping[str, Mapping[str, Any]]) -> str:
    return "available" if any(group.get("items") for group in groups.values()) else "missing"


def _group_from_mapping(value: Mapping[str, Any]) -> str | None:
    for key in ("group", "artifact_group", "kind", "category", "type"):
        group = _group_from_text(_non_empty_text(value.get(key)) or "")
        if group is not None:
            return group
    return None


def _group_from_text(value: str) -> str | None:
    token = value.strip().lower().replace("-", "_")
    return _GROUP_ALIASES.get(token)


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _dedupe_items(items: object) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        if not isinstance(item, Mapping):
            continue
        ref = _non_empty_text(item.get("ref"))
        source = _non_empty_text(item.get("source"))
        if ref is None or source is None:
            continue
        key = (ref, source)
        if key in seen:
            continue
        seen.add(key)
        result.append(dict(item))
    return result


def _condition_items(conditions: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    for key in ("missing", "stale", "conflict"):
        for item in _string_list(conditions.get(key)):
            items.append(f"{key}: {item}")
    return items


def _artifact_sections(groups: Mapping[str, Any]) -> str:
    sections: list[str] = []
    for group_name in ARTIFACT_GROUPS:
        group = _mapping(groups.get(group_name))
        items = [
            f"{item.get('label') or item.get('ref')} - {item.get('ref')}"
            for item in group.get("items") or []
            if isinstance(item, Mapping)
        ]
        sections.append(
            '<section class="panel wide"><h2>'
            + escape(_ARTIFACT_GROUP_LABELS[group_name])
            + " "
            + status_chip(group.get("status") or "missing")
            + "</h2>"
            + list_html(items, empty_text="缺少显式产物引用。")
            + "</section>"
        )
    return "\n".join(sections)


def _conversation_projection(value: Mapping[str, Any] | None, study_id: str) -> dict[str, Any]:
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


def _conversation_section(conversation: Mapping[str, Any]) -> str:
    status = _non_empty_text(conversation.get("status")) or "missing"
    summary = _conversation_summary_text(_mapping(conversation.get("timeline_summary")))
    items = [
        _non_empty_text(item.get("summary")) or _non_empty_text(item.get("item_kind")) or "conversation item"
        for item in _mapping_list(conversation.get("timeline_items"))
    ]
    refs = _string_list(conversation.get("source_refs"))
    return (
        '<section class="panel wide"><h2>执行器对话 '
        + status_chip(status)
        + "</h2>"
        + (f"<p>{escape(summary)}</p>" if summary else "")
        + list_html(items, empty_text="缺少执行器 conversation timeline。")
        + "<h3>对话来源</h3>"
        + list_html(refs, empty_text="缺少 conversation source refs。")
        + "</section>"
    )


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


def _key_value_section(title: str, values: Mapping[str, str]) -> str:
    return (
        '<section class="panel wide"><h2>'
        + escape(title)
        + "</h2><dl>"
        + "".join(f"<div><dt>{escape(key)}</dt><dd>{escape(value)}</dd></div>" for key, value in values.items())
        + "</dl></section>"
    )


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


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "ARTIFACT_GROUPS",
    "build_study_workbench_payload",
    "render_study_workbench_sections",
]
