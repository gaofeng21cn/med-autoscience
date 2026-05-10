from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from .rendering import (
    condition_badge,
    condition_section,
    event_section,
    gate_text,
    list_html,
    list_section,
    portal_css,
    refresh_meta,
    runtime_continuity_section,
    section,
    status_chip,
)
from .live_console_shell import render_live_console_portal_link
from .section_explanations import render_section_explanations_section
from .source_refs import display_source_refs
from .status_display import display_text
from .study_workbench import render_study_workbench_sections
from .workspace_overview import (
    dedupe_texts,
    render_workspace_dashboard_section,
    render_workspace_alerts_section,
    render_workspace_studies_section,
    unique_text,
)
from .workspace_summary import (
    workspace_delivery_paragraphs,
    workspace_next_step_paragraphs,
    workspace_quality_paragraphs,
    workspace_status_paragraphs,
)


def render_progress_portal_html(payload: Mapping[str, Any], *, brand_fallback: str) -> str:
    workspace = _mapping(payload.get("workspace"))
    study = _mapping(payload.get("study"))
    freshness = _mapping(payload.get("freshness"))
    quality = _mapping(payload.get("quality"))
    delivery = _mapping(payload.get("delivery"))
    live_console = _mapping(payload.get("live_console"))
    conditions = _mapping(payload.get("conditions"))
    workspace_diagnostics = _mapping(workspace.get("diagnostics"))
    runtime_continuity = _mapping(study.get("runtime_continuity"))
    production_blocker_impact = _mapping(study.get("production_blocker_impact"))
    section_explanations = _mapping_list(payload.get("section_explanations"))
    latest_events = [dict(item) for item in payload.get("latest_events") or [] if isinstance(item, Mapping)]
    source_refs = display_source_refs(payload.get("source_refs"))
    workspace_studies = [
        dict(item)
        for item in workspace.get("studies") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id"))
    ]
    portal_view = _mapping(payload.get("portal_view"))
    auto_refresh_seconds = portal_view.get("auto_refresh_seconds")
    generated_at = str(payload.get("generated_at") or "unknown")
    generated_at_local = _mapping(payload.get("generated_at_local"))
    generated_at_local_label = _non_empty_text(generated_at_local.get("label")) or generated_at
    brand = str(payload.get("brand") or brand_fallback)
    state_label = str(study.get("state_label") or "状态投影缺失")
    workspace_title = str(workspace.get("profile_name") or "unknown workspace")
    selected_study_id = str(study.get("study_id") or "unknown-study")
    condition_badge_label = condition_badge(conditions)
    blockers = _string_list(study.get("current_blockers"))
    workspace_alert_items = _mapping_list(workspace.get("workspace_alert_items"))
    suppressed_alert_items = _mapping_list(workspace_diagnostics.get("suppressed_alert_items"))
    current_status_paragraphs = dedupe_texts(
        [
            str(study.get("state_summary") or "当前缺少状态摘要。"),
            str(study.get("current_stage_summary") or "当前阶段摘要缺失。"),
        ]
    )
    paper_paragraphs = dedupe_texts(
        [
            unique_text(
                str(study.get("paper_stage_summary") or "论文阶段摘要缺失。"),
                seen=current_status_paragraphs,
            ),
            str(quality.get("summary") or "质量投影缺失。"),
        ]
    )
    workspace_overview_mode = str(study.get("scope") or "") == "workspace"
    if workspace_overview_mode:
        current_status_paragraphs = workspace_status_paragraphs(workspace_studies)
        next_step_paragraphs = workspace_next_step_paragraphs(workspace_studies)
        paper_paragraphs = workspace_quality_paragraphs(workspace_studies)
        delivery_paragraphs = workspace_delivery_paragraphs(workspace_studies)
    else:
        next_step_paragraphs = [
            str(study.get("next_system_action") or "等待 MAS 重新生成下一步投影。"),
            gate_text(study),
        ]
        delivery_paragraphs = [
            str(delivery.get("summary") or "交付投影缺失。"),
            display_text(delivery.get("status"), fallback="交付状态未提供"),
        ]
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            refresh_meta(auto_refresh_seconds),
            f"<title>{escape(brand)} Progress Portal</title>",
            "<style>",
            portal_css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="portal">',
            '<header class="masthead">',
            f'<div class="brand">{escape(brand)}</div>',
            f"<h1>{escape(workspace_title)}</h1>",
            f'<p class="state">{escape(state_label)}</p>',
            '<details class="snapshot-meta">',
            "<summary>快照信息</summary>",
            '<dl class="meta">',
            f"<div><dt>本机时间</dt><dd>{escape(generated_at_local_label)}</dd></div>",
            f"<div><dt>UTC 时间</dt><dd>{escape(generated_at)}</dd></div>",
            f"<div><dt>进度新鲜度</dt><dd>{status_chip(freshness.get('status') or 'unknown')}</dd></div>",
            f"<div><dt>工作区</dt><dd>{escape(str(workspace.get('profile_name') or 'unknown'))}</dd></div>",
            f"<div><dt>当前论文线</dt><dd>{escape('工作区总览' if workspace_overview_mode else selected_study_id)}</dd></div>",
            f"<div><dt>状态缺口</dt><dd>{escape(condition_badge_label)}</dd></div>",
            "</dl>",
            "</details>",
            render_live_console_portal_link(live_console),
            "</header>",
            render_workspace_dashboard_section(
                workspace_studies,
                workspace_alert_items=workspace_alert_items,
                conditions=conditions,
                freshness=freshness,
            )
            if workspace_overview_mode
            else "",
            _navigation_section(payload) if not workspace_overview_mode else "",
            render_workspace_studies_section(workspace_studies),
            '<section class="grid">',
            section("当前状态", current_status_paragraphs),
            section("下一步", next_step_paragraphs),
            runtime_continuity_section(runtime_continuity),
            _production_blocker_impact_section(production_blocker_impact),
            section("论文与质量", paper_paragraphs),
            section("文件与交付", delivery_paragraphs),
            "</section>",
            list_section("当前阻塞", [display_text(item, fallback='未提供') for item in blockers], empty_text="当前没有投影出的阻塞项。"),
            render_workspace_alerts_section("工作区告警", workspace_alert_items, empty_text="当前没有 workspace 级告警。"),
            render_workspace_alerts_section("诊断与修复建议", suppressed_alert_items, empty_text="当前没有被降级的旧/泛化诊断。"),
            event_section(latest_events),
            condition_section(conditions),
            render_section_explanations_section(section_explanations),
            render_study_workbench_sections(_mapping(payload.get("study_workbench")))
            if not workspace_overview_mode
            else "",
            '<details class="refs">',
            f"<summary>数据来源 ({len(source_refs)}/{len(_string_list(payload.get('source_refs')))})</summary>",
            list_html(source_refs, empty_text="当前没有可展示的数据来源。"),
            "</details>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def _navigation_section(payload: Mapping[str, Any]) -> str:
    navigation = _mapping(payload.get("navigation"))
    studies = _mapping_list(navigation.get("studies"))
    scope = _non_empty_text(navigation.get("scope")) or "workspace"
    workspace_href = _non_empty_text(navigation.get("workspace_href")) or "index.html"
    if not studies and scope != "study":
        return ""
    links: list[str] = []
    if scope == "study":
        links.append(f'<a href="{escape(workspace_href, quote=True)}">工作区总览</a>')
    for item in studies:
        study_id = _non_empty_text(item.get("study_id"))
        href = _non_empty_text(item.get("href"))
        if study_id is None or href is None:
            continue
        label = f"{study_id}（当前）" if bool(item.get("selected")) else study_id
        links.append(f'<a href="{escape(href, quote=True)}">{escape(label)}</a>')
    if not links:
        return ""
    return (
        '<nav class="panel wide portal-nav" aria-label="论文线导航">'
        "<h2>论文线入口</h2>"
        '<div class="live-console-link">'
        + "".join(links)
        + "</div></nav>"
    )


def _production_blocker_impact_section(payload: Mapping[str, Any]) -> str:
    if not payload:
        return ""
    items = [
        f"是否影响产出：{'yes' if payload.get('affects_output') is True else 'no'}",
    ]
    for label, key in (
        ("next owner", "next_owner"),
        ("why not running", "why_not_running"),
        ("same fingerprint or handoff", "same_fingerprint_or_handoff"),
        ("will start LLM", "will_start_llm"),
        ("safe reconcile command", "safe_reconcile_command"),
    ):
        value = payload.get(key)
        if value is None:
            continue
        if isinstance(value, bool):
            value = "yes" if value else "no"
        items.append(f"{label}：{value}")
    route = _mapping(payload.get("route"))
    for key in ("source_fingerprint", "work_unit_fingerprint", "trace_id"):
        if route.get(key):
            items.append(f"route {key}：{route[key]}")
    return list_section("是否真影响产出", [str(item) for item in items], empty_text="当前没有 production blocker impact 投影。")


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


__all__ = ["render_progress_portal_html"]
