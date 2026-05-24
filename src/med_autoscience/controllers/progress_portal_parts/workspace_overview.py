from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from urllib.parse import quote
from typing import Any

from .status_display import display_text, status_chip, status_label


_LEGACY_OR_GENERIC_WORKSPACE_ALERTS = frozenset(
    {
        "OPL provider/runtime manager workspace supervision 尚未注册。",
        "Supervisor scheduler 尚未注册。",
        "MAS local scheduler 未加载或存在漂移；仅保留 tombstone/provenance refs。",
        "检测到 legacy MAS local scheduler LaunchAgent；请按 tombstone/provenance refs 审计旧生成物。",
        "检测到已退役的 MAS local scheduler 旧生成物；当前 CLI 不再暴露 local cleanup command。",
        "状态需要检查。",
    }
)
_WORKSPACE_SUPERVISION_ALERTS = frozenset(
    {
        "OPL provider/runtime manager workspace supervision 尚未注册。",
        "Supervisor scheduler 尚未注册。",
        "MAS local scheduler 已物理退役；仅保留 tombstone/provenance refs。",
        "检测到 legacy MAS local scheduler LaunchAgent；请按 tombstone/provenance refs 审计旧生成物。",
        "检测到已退役的 MAS local scheduler 旧生成物；当前 CLI 不再暴露 local cleanup command。",
    }
)
_PARKED_STUDY_WORKSPACE_ALERTS = frozenset(
    {
        "用户暂停或手动停驻，需显式恢复或新方案。",
        "当前阶段以人工判断或收尾为主，不要求系统继续产出新的自动推进信号。",
    }
)
_LOW_INFORMATION_GENERIC_ALERTS = frozenset({"状态需要检查。"})
_LOCAL_SCHEDULER_TOMBSTONE_ALERT = "MAS local scheduler 已物理退役；仅保留 tombstone/provenance refs。"


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


def workspace_alert_projection(value: object, *, workspace_studies: list[dict[str, Any]]) -> dict[str, list[Any]]:
    visible: list[dict[str, str | None]] = []
    suppressed: list[dict[str, str | None]] = []
    has_active_study = any(_workspace_study_is_active(item) for item in workspace_studies)
    for text in dedupe_texts(_string_list(value)):
        item = _alert_item(text)
        if text in _LEGACY_OR_GENERIC_WORKSPACE_ALERTS:
            suppressed.append(item)
            continue
        if has_active_study and _is_parked_study_alert(text):
            suppressed.append(item)
            continue
        if not any(_same_alert_family(item, existing) for existing in visible):
            visible.append(item)
    return {
        "visible": [str(item["current_output"]) for item in visible],
        "suppressed": [
            str(item["current_output"])
            for item in suppressed
            if item.get("diagnostic_visibility") != "hide_when_specific_study_rows_exist"
        ],
        "visible_items": visible,
        "suppressed_items": [
            item
            for item in suppressed
            if item.get("diagnostic_visibility") != "hide_when_specific_study_rows_exist"
        ],
    }


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
        opl_control = _mapping(item.get("opl_current_control_state")) or _mapping(item.get("current_control_state"))
        supervisor_state = _mapping(runtime_health.get("supervisor_state"))
        intervention_lane = _mapping(item.get("intervention_lane"))
        operator_status_card = _mapping(item.get("operator_status_card"))
        active_run_id = (
            _non_empty_text(monitoring.get("active_run_id"))
            or _non_empty_text(opl_control.get("active_run_id"))
        )
        health_status = (
            _non_empty_text(monitoring.get("health_status"))
            or _non_empty_text(opl_control.get("state"))
            or _non_empty_text(opl_control.get("status"))
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
                or _state_label_from_health(
                    health_status=health_status,
                    active_run_id=active_run_id,
                ),
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
            }
        )
    return result


def selected_workspace_study_id(cockpit: Mapping[str, Any]) -> str | None:
    return None


def render_workspace_studies_section(studies: list[dict[str, Any]]) -> str:
    if not studies:
        return ""
    rows = []
    headers = ("论文线", "OPL 控制面", "状态", "运行编号", "运行健康", "监管心跳", "进度新鲜度", "论文阶段", "焦点/下一步")
    for item in studies:
        selected_class = " selected" if bool(item.get("selected")) else ""
        study_id = display_text(item.get("study_id"), empty_text="未知论文线", preserve_known_token=False)
        study_href = _non_empty_text(item.get("portal_href"))
        study_cell = (
            f'<a href="{escape(study_href, quote=True)}">{escape(study_id)}</a>'
            if study_href
            else escape(study_id)
        )
        values = (
            study_cell,
            _study_control_plane_label(),
            escape(display_text(item.get("state_label"), empty_text="状态投影缺失", preserve_known_token=False)),
            escape(display_text(item.get("active_run_id"), empty_text="无运行编号", preserve_known_token=False)),
            status_chip(item.get("runtime_health_status") or "unknown"),
            status_chip(item.get("supervisor_tick_status") or "unknown"),
            status_chip(item.get("progress_freshness_status") or "unknown"),
            escape(display_text(item.get("paper_stage") or item.get("current_stage"), empty_text="未提供")),
            escape(display_text(item.get("operator_focus") or item.get("next_system_action"), empty_text="未提供", preserve_known_token=False)),
        )
        rows.append(
            "<tr"
            + f' class="study-row{selected_class}">'
            + "".join(f'<td data-label="{escape(label)}">{value}</td>' for label, value in zip(headers, values, strict=True))
            + "</tr>"
        )
    return (
        '<details class="panel wide study-overview field-details diagnostics-section">'
        "<summary>系统字段与来源</summary>"
        '<div class="field-details-body">'
        '<div class="table-wrap"><table class="responsive-table">'
        "<thead><tr>"
        "<th>论文线</th><th>OPL 控制面</th><th>状态</th><th>运行编号</th><th>运行健康</th>"
        "<th>监管心跳</th><th>进度新鲜度</th><th>论文阶段</th><th>焦点/下一步</th>"
        "</tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div></div></details>"
    )


def render_workspace_dashboard_section(
    studies: list[dict[str, Any]],
    *,
    workspace_alert_items: list[dict[str, str | None]],
    conditions: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> str:
    if not studies:
        return (
            '<section class="workspace-dashboard wide">'
            "<h2>工作区总览</h2>"
            '<p class="muted">当前 workspace 尚未发现论文线。</p>'
            "</section>"
        )
    study_items = "".join(_study_item(item) for item in studies)
    return (
        '<section class="workspace-dashboard wide" aria-label="工作区总览">'
        + _attention_band(
            studies,
            workspace_alert_items=workspace_alert_items,
            conditions=conditions,
            freshness=freshness,
        )
        + "<h2>论文线工作台</h2>"
        + '<div class="study-list">'
        + study_items
        + "</div></section>"
    )


def _attention_band(
    studies: list[dict[str, Any]],
    *,
    workspace_alert_items: list[dict[str, str | None]],
    conditions: Mapping[str, Any],
    freshness: Mapping[str, Any],
) -> str:
    live_count = sum(1 for item in studies if _non_empty_text(item.get("active_run_id")))
    attention_count = sum(1 for item in studies if _study_needs_attention(item))
    condition_count = sum(len(_string_list(conditions.get(key))) for key in ("missing", "stale", "conflict"))
    primary_alert = workspace_alert_items[0] if workspace_alert_items else {}
    alert_text = str(primary_alert.get("current_output") or "当前没有 workspace 级告警。")
    alert_command = _non_empty_text(primary_alert.get("recommended_command"))
    alert_detail = ""
    if primary_alert:
        alert_detail = (
            '<div class="attention-detail">'
            f'<span>来源：{escape(str(primary_alert.get("source") or "未提供"))}</span>'
            f'<span>用途：{escape(str(primary_alert.get("purpose") or "未提供"))}</span>'
            f'<span>期望：{escape(str(primary_alert.get("expected") or "未提供"))}</span>'
            "</div>"
        )
    command_html = (
        f'<code class="command-code">{escape(alert_command)}</code>'
        if alert_command
        else '<span class="muted">当前没有推荐命令。</span>'
    )
    alert_class = "attention-alert attention-alert--active" if primary_alert else "attention-alert"
    return (
        '<div class="attention-band">'
        '<div class="attention-summary">'
        '<span class="eyebrow">工作区关注</span>'
        "<h2>需要关注的事项</h2>"
        f"<p>{escape(alert_text)}</p>"
        + alert_detail
        + "</div>"
        '<div class="attention-metrics" aria-label="工作区关键指标">'
        + _metric_tile("活跃论文线", f"{live_count}/{len(studies)}", tone="info")
        + _metric_tile("需关注", str(attention_count), tone="warn" if attention_count else "ok")
        + _metric_tile("状态缺口", str(condition_count), tone="bad" if condition_count else "ok")
        + _metric_tile("进度新鲜度", status_label(freshness.get("status") or "unknown"), tone=_metric_tone(freshness.get("status")))
        + "</div>"
        f'<div class="{alert_class}">{command_html}</div>'
        "</div>"
    )


def _metric_tile(label: str, value: str, *, tone: str) -> str:
    return (
        f'<div class="metric-tile metric-tile--{escape(tone)}">'
        f'<span class="metric-label">{escape(label)}</span>'
        f'<strong>{escape(value)}</strong>'
        "</div>"
    )


def _study_item(item: Mapping[str, Any]) -> str:
    study_id = display_text(item.get("study_id"), empty_text="未知论文线", preserve_known_token=False)
    study_href = _non_empty_text(item.get("portal_href"))
    title = (
        f'<a href="{escape(study_href, quote=True)}">{escape(study_id)}</a>'
        if study_href
        else escape(study_id)
    )
    detail_link = (
        f'<a class="btn btn-outline" href="{escape(study_href, quote=True)}">打开详情</a>'
        if study_href
        else ""
    )
    action = display_text(
        item.get("operator_focus") or item.get("next_system_action"),
        empty_text="当前没有明确下一步投影。",
        preserve_known_token=False,
    )
    run_id = display_text(item.get("active_run_id"), empty_text="无运行编号", preserve_known_token=False)
    stage = display_text(item.get("paper_stage") or item.get("current_stage"), empty_text="未提供")
    selected_class = " study-item--selected" if bool(item.get("selected")) else ""
    tone_class = " study-item--attention" if _study_needs_attention(item) else ""
    return "".join(
        [
            f'<article class="study-item{selected_class}{tone_class}">',
            '<div class="study-info">',
            f"<h3>{title}</h3>",
            '<div class="study-meta">',
            f"<span>论文阶段：<strong>{escape(stage)}</strong></span>",
            f"<span>运行编号：<strong>{escape(run_id)}</strong></span>",
            "</div>",
            "</div>",
            '<div class="study-status">',
            status_chip(item.get("state_label") or "unknown"),
            status_chip(item.get("runtime_health_status") or "unknown"),
            status_chip(item.get("supervisor_tick_status") or "unknown"),
            status_chip(item.get("progress_freshness_status") or "unknown"),
            "</div>",
            '<div class="study-action">',
            '<span class="study-action-label">下一步重点</span>',
            f'<p class="study-action-desc">{escape(action)}</p>',
            "</div>",
            '<div class="study-actions">',
            detail_link,
            _study_control_plane_label(),
            "</div>",
            "</article>",
        ]
    )


def _study_needs_attention(item: Mapping[str, Any]) -> bool:
    if str(item.get("progress_freshness_status") or "") in {"stale", "missing"}:
        return True
    return str(item.get("runtime_health_status") or "") in {
        "blocked",
        "recovering",
        "escalated",
        "attention_required",
        "missing",
        "not_installed",
        "not_loaded",
        "parked",
        "awaiting_explicit_resume",
        "await_explicit_resume",
        "manual_hold",
    }


def _metric_tone(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"fresh", "loaded", "running", "active", "completed", "available"}:
        return "ok"
    if text in {"missing", "blocked", "escalated", "execution_failed", "invalid", "not_installed", "not_loaded"}:
        return "bad"
    return "warn" if text else "bad"


def _study_control_plane_label() -> str:
    return '<span class="muted">OPL current_control_state</span>'


def study_detail_href(study_id: str, *, from_study_page: bool = False) -> str:
    encoded = quote(study_id, safe="")
    prefix = "../" if from_study_page else "studies/"
    return f"{prefix}{encoded}/index.html"


def workspace_portal_navigation(
    studies: list[dict[str, Any]],
    *,
    selected_study_id: str | None,
    page_scope: str,
) -> dict[str, Any]:
    from_study_page = page_scope == "study"
    rows: list[dict[str, Any]] = []
    for item in studies:
        study_id = _non_empty_text(item.get("study_id"))
        if study_id is None:
            continue
        rows.append(
            {
                "study_id": study_id,
                "selected": study_id == selected_study_id,
                "href": study_detail_href(study_id, from_study_page=from_study_page),
                "control_plane_owner": "one-person-lab",
                "state_label": item.get("state_label"),
                "current_stage": item.get("current_stage"),
                "paper_stage": item.get("paper_stage"),
                "active_run_id": item.get("active_run_id"),
                "runtime_health_status": item.get("runtime_health_status"),
                "progress_freshness_status": item.get("progress_freshness_status"),
            }
        )
    return {
        "scope": page_scope,
        "selected_study_id": selected_study_id,
        "workspace_href": "../../index.html" if from_study_page else "index.html",
        "studies": rows,
    }


def render_workspace_alerts_section(title: str, items: list[dict[str, str | None]], *, empty_text: str) -> str:
    if not items:
        return (
            '<section class="panel wide">'
            f"<h2>{escape(title)}</h2>"
            f"<p>{escape(empty_text)}</p>"
            "</section>"
        )
    rows = []
    headers = ("当前输出", "来源", "用途", "期望输出", "修复/查看命令")
    for item in items:
        values = (
            escape(str(item.get("current_output") or "")),
            escape(str(item.get("source") or "")),
            escape(str(item.get("purpose") or "")),
            escape(str(item.get("expected") or "")),
            escape(str(item.get("recommended_command") or "")),
        )
        rows.append(
            "<tr>"
            + "".join(f'<td data-label="{escape(label)}">{value}</td>' for label, value in zip(headers, values, strict=True))
            + "</tr>"
        )
    return (
        '<section class="panel wide">'
        f"<h2>{escape(title)}</h2>"
        '<div class="table-wrap"><table class="responsive-table">'
        "<thead><tr><th>当前输出</th><th>来源</th><th>用途</th><th>期望输出</th><th>修复/查看命令</th></tr></thead>"
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
    opl_control = _mapping(item.get("opl_current_control_state")) or _mapping(item.get("current_control_state"))
    if _non_empty_text(opl_control.get("active_run_id")):
        return True
    current_stage = _non_empty_text(item.get("current_stage"))
    writer_state = _non_empty_text(item.get("writer_state"))
    user_visible = _mapping(item.get("user_visible_projection"))
    return current_stage == "live" or writer_state == "live" or _non_empty_text(user_visible.get("writer_state")) == "live"


def _is_parked_study_alert(text: str) -> bool:
    if text in _PARKED_STUDY_WORKSPACE_ALERTS:
        return True
    return any(text.startswith(prefix) for prefix in _PARKED_STUDY_WORKSPACE_ALERTS)


def _alert_item(text: str) -> dict[str, str | None]:
    source = "workspace_cockpit.workspace_alerts"
    purpose = "提示 workspace 级运行、进度或质量异常。"
    expected = "具体 study 行应给出 owner、运行健康、进度 freshness 和下一步。"
    recommended_command: str | None = None
    if text in _WORKSPACE_SUPERVISION_ALERTS:
        source = "workspace_supervision.service.summary"
        legacy_outputs = {
            _LOCAL_SCHEDULER_TOMBSTONE_ALERT,
            "检测到 legacy MAS local scheduler LaunchAgent；请按 tombstone/provenance refs 审计旧生成物。",
            "检测到已退役的 MAS local scheduler 旧生成物；当前 CLI 不再暴露 local cleanup command。",
        }
        if text not in legacy_outputs:
            text = "OPL provider/runtime manager workspace supervision 尚未注册。"
        purpose = "说明 workspace 级 MAS local scheduler 已退为 tombstone/provenance 语境。"
        expected = "默认 scheduler 由 OPL provider/runtime manager 持有；MAS local adapter 不再暴露 active status/remove/ensure command。"
    elif text == "状态需要检查。":
        source = "workspace_cockpit.generic_status"
        purpose = "旧版泛化告警；当前已有具体 study 行时不再作为主诊断展示。"
        expected = "由具体 study 行和 runtime health blocker 取代泛化状态。"
    elif "medical overlay" in text:
        source = "product_entry_preflight.medical_overlay_ready"
        purpose = "提示医学论文运行前置能力尚未全部 ready。"
        expected = "doctor/product-entry preflight 应通过或给出具体 medical overlay blocker。"
        recommended_command = "uv run python -m med_autoscience.cli doctor report --profile <profile>"
    elif "meaningful artifact delta" in text or "worker liveness" in text or "12 小时" in text:
        source = "workspace_cockpit.progress_freshness"
        purpose = "提示监管心跳不能单独证明论文实际推进。"
        text = "进度信号：有记录，但 worker 或 artifact delta 不满足继续推进证据。"
        expected = "worker liveness 或 meaningful artifact delta 应恢复为 fresh，或给出稳定 blocked_reason。"
        recommended_command = "uv run python -m med_autoscience.cli owner-route-reconcile --profile <profile>"
    elif _is_parked_study_alert(text):
        source = "workspace_cockpit.inactive_study_projection"
        purpose = "说明 parked/manual-hold study 不应被自动唤醒。"
        expected = "只有用户显式唤醒或新 task intake 才恢复运行。"
    return {
        "source": source,
        "purpose": purpose,
        "current_output": text,
        "expected": _localize_status_words(expected),
        "recommended_command": recommended_command,
        "diagnostic_visibility": "hide_when_specific_study_rows_exist"
        if text in _LOW_INFORMATION_GENERIC_ALERTS
        else "show",
    }


def _state_label_from_health(*, health_status: str | None, active_run_id: str | None) -> str:
    if health_status == "escalated":
        return "需要外层 supervisor"
    if health_status in {"parked", "awaiting_explicit_resume", "await_explicit_resume"}:
        return "等待显式恢复"
    if active_run_id:
        return "有 OPL 运行投影"
    return "无运行编号"


def _localize_status_words(value: str) -> str:
    result = value
    for token in ("fresh", "blocked_reason"):
        result = result.replace(token, status_label(token))
    return result


def _same_alert_family(left: Mapping[str, str | None], right: Mapping[str, str | None]) -> bool:
    return left.get("source") == right.get("source") and left.get("current_output") == right.get("current_output")


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
