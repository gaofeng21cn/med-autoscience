from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any


_LEGACY_OR_GENERIC_WORKSPACE_ALERTS = frozenset(
    {
        "Hermes-hosted runtime supervision 尚未注册。",
        "状态需要检查。",
    }
)
_PARKED_STUDY_WORKSPACE_ALERTS = frozenset(
    {
        "用户暂停或手动停驻，需显式恢复或新方案。",
        "当前阶段以人工判断或收尾为主，不要求系统继续产出新的自动推进信号。",
    }
)


def dedupe_texts(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        text = " ".join(value.strip().split())
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def unique_text(value: str, *, seen: Iterable[str]) -> str:
    text = " ".join(value.strip().split())
    if not text:
        return ""
    return "" if text in set(seen) else text


def workspace_alert_projection(value: object, *, workspace_studies: list[dict[str, Any]]) -> dict[str, list[str]]:
    visible: list[str] = []
    suppressed: list[str] = []
    has_active_study = any(_workspace_study_is_active(item) for item in workspace_studies)
    for text in dedupe_texts(_string_list(value)):
        if text in _LEGACY_OR_GENERIC_WORKSPACE_ALERTS:
            suppressed.append(text)
            continue
        if has_active_study and _is_parked_study_alert(text):
            suppressed.append(text)
            continue
        visible.append(text)
    return {"visible": visible, "suppressed": suppressed}


def workspace_studies(cockpit: Mapping[str, Any], *, selected_study_id: str) -> list[dict[str, Any]]:
    studies = cockpit.get("studies")
    if not isinstance(studies, list):
        return []
    result: list[dict[str, Any]] = []
    for item in studies:
        if not isinstance(item, Mapping):
            continue
        study_id = _non_empty_text(item.get("study_id"))
        if study_id is None:
            continue
        user_visible = _mapping(item.get("user_visible_projection"))
        monitoring = _mapping(item.get("monitoring"))
        progress_freshness = _mapping(item.get("progress_freshness"))
        runtime_health = _mapping(item.get("runtime_health_snapshot"))
        worker_liveness = _mapping(runtime_health.get("worker_liveness_state"))
        supervisor_state = _mapping(runtime_health.get("supervisor_state"))
        intervention_lane = _mapping(item.get("intervention_lane"))
        operator_status_card = _mapping(item.get("operator_status_card"))
        active_run_id = (
            _non_empty_text(monitoring.get("active_run_id"))
            or _non_empty_text(worker_liveness.get("active_run_id"))
        )
        health_status = (
            _non_empty_text(monitoring.get("health_status"))
            or _non_empty_text(runtime_health.get("attempt_state"))
        )
        supervisor_tick_status = (
            _non_empty_text(monitoring.get("supervisor_tick_status"))
            or _non_empty_text(supervisor_state.get("status"))
        )
        operator_focus = (
            _non_empty_text(intervention_lane.get("title"))
            or _non_empty_text(operator_status_card.get("user_visible_verdict"))
            or _non_empty_text(item.get("next_system_action"))
            or _non_empty_text(user_visible.get("next_system_action"))
        )
        result.append(
            {
                "study_id": study_id,
                "selected": study_id == selected_study_id,
                "state_label": _non_empty_text(item.get("state_label"))
                or _non_empty_text(user_visible.get("state_label"))
                or "状态投影缺失",
                "state_summary": _non_empty_text(item.get("state_summary"))
                or _non_empty_text(user_visible.get("state_summary")),
                "current_stage": _non_empty_text(item.get("current_stage"))
                or _non_empty_text(user_visible.get("current_stage")),
                "paper_stage": _non_empty_text(item.get("paper_stage"))
                or _non_empty_text(user_visible.get("paper_stage")),
                "active_run_id": active_run_id,
                "runtime_health_status": health_status,
                "supervisor_tick_status": supervisor_tick_status,
                "progress_freshness_status": _non_empty_text(progress_freshness.get("status")),
                "progress_freshness_summary": _non_empty_text(progress_freshness.get("summary")),
                "operator_focus": operator_focus,
                "next_system_action": _non_empty_text(item.get("next_system_action"))
                or _non_empty_text(user_visible.get("next_system_action")),
                "worker_running": worker_liveness.get("worker_running") if "worker_running" in worker_liveness else None,
            }
        )
    return result


def selected_workspace_study_id(cockpit: Mapping[str, Any]) -> str | None:
    studies = cockpit.get("studies")
    if not isinstance(studies, list):
        return None
    for item in studies:
        if not isinstance(item, Mapping):
            continue
        if _workspace_study_has_active_signal(item):
            study_id = _non_empty_text(item.get("study_id"))
            if study_id is not None:
                return study_id
    for item in studies:
        if isinstance(item, Mapping):
            study_id = _non_empty_text(item.get("study_id"))
            if study_id is not None:
                return study_id
    return None


def render_workspace_studies_section(studies: list[dict[str, Any]]) -> str:
    if not studies:
        return ""
    rows = []
    for item in studies:
        selected_class = " selected" if bool(item.get("selected")) else ""
        rows.append(
            "<tr"
            f' class="study-row{selected_class}">'
            f"<td>{escape(str(item.get('study_id') or 'unknown-study'))}</td>"
            f"<td>{escape(str(item.get('state_label') or '状态投影缺失'))}</td>"
            f"<td>{escape(str(item.get('active_run_id') or 'none'))}</td>"
            f"<td>{escape(str(item.get('runtime_health_status') or 'unknown'))}</td>"
            f"<td>{escape(str(item.get('supervisor_tick_status') or 'unknown'))}</td>"
            f"<td>{escape(str(item.get('progress_freshness_status') or 'unknown'))}</td>"
            f"<td>{escape(str(item.get('paper_stage') or item.get('current_stage') or 'unknown'))}</td>"
            f"<td>{escape(str(item.get('operator_focus') or item.get('next_system_action') or 'none'))}</td>"
            "</tr>"
        )
    return (
        '<section class="panel wide study-overview">'
        "<h2>论文线概览</h2>"
        '<div class="table-wrap"><table>'
        "<thead><tr>"
        "<th>study_id</th><th>状态</th><th>active_run_id</th><th>runtime health</th>"
        "<th>supervisor</th><th>freshness</th><th>paper/current stage</th><th>焦点/下一步</th>"
        "</tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def _workspace_study_is_active(item: Mapping[str, Any]) -> bool:
    if _non_empty_text(item.get("active_run_id")):
        return True
    return _non_empty_text(item.get("current_stage")) == "live" or _non_empty_text(item.get("writer_state")) == "live"


def _workspace_study_has_active_signal(item: Mapping[str, Any]) -> bool:
    if _non_empty_text(item.get("active_run_id")):
        return True
    monitoring = _mapping(item.get("monitoring"))
    if _non_empty_text(monitoring.get("active_run_id")):
        return True
    runtime_health = _mapping(item.get("runtime_health_snapshot"))
    worker_liveness = _mapping(runtime_health.get("worker_liveness_state"))
    if bool(worker_liveness.get("worker_running")):
        return True
    current_stage = _non_empty_text(item.get("current_stage"))
    writer_state = _non_empty_text(item.get("writer_state"))
    user_visible = _mapping(item.get("user_visible_projection"))
    return current_stage == "live" or writer_state == "live" or _non_empty_text(user_visible.get("writer_state")) == "live"


def _is_parked_study_alert(text: str) -> bool:
    if text in _PARKED_STUDY_WORKSPACE_ALERTS:
        return True
    return any(text.startswith(prefix) for prefix in _PARKED_STUDY_WORKSPACE_ALERTS)


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
