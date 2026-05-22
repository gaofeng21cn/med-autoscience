from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any

from med_autoscience.controllers.progress_portal_parts.rendering import local_time_label
from med_autoscience.controllers.progress_portal_parts.status_display import display_text, status_chip, status_label
from med_autoscience.controllers.runtime_live_console_ui_parts.constants import BRAND
from med_autoscience.controllers.runtime_live_console_ui_parts.rendering import live_console_css
from med_autoscience.controllers.runtime_live_console_ui_parts.shared import (
    dedupe,
    mapping,
    mapping_list,
    string_list,
    text,
)


def render_live_console_html(payload: Mapping[str, Any]) -> str:
    workspace = mapping(payload.get("workspace"))
    studies = [dict(item) for item in payload.get("studies") or [] if isinstance(item, Mapping)]
    portal_handoff = mapping(payload.get("portal_handoff"))
    stream = mapping(payload.get("stream"))
    terminal_gate = mapping(payload.get("terminal_attach_gate"))
    empty_state = mapping(payload.get("empty_state"))
    action_intents = mapping_list(payload.get("controller_action_intents"))
    generated_at = str(payload.get("generated_at") or "unknown")
    generated_at_local = mapping(payload.get("generated_at_local"))
    generated_at_local_label = str(generated_at_local.get("label") or generated_at)
    brand = str(payload.get("brand") or BRAND)
    progress_href = str(portal_handoff.get("progress_portal_href") or "../progress/index.html")
    selected_study_id = text(payload.get("selected_study_id"))
    scope = text(payload.get("scope")) or ("study" if selected_study_id else "profile")
    scope_label = selected_study_id if scope == "study" and selected_study_id else "operator 总览"
    attach_badge = "Attach Ready" if terminal_gate.get("status") == "available" else "只读"
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{escape(brand)} 运行控制台</title>",
            "<style>",
            live_console_css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="console">',
            '<header class="masthead">',
            '<div class="topline">',
            f'<span class="brand">{escape(brand)}</span>',
            f'<span class="badge">{escape(attach_badge)}</span>',
            f'<a class="portal-link" href="{escape(progress_href, quote=True)}">返回进度入口</a>',
            "</div>",
            f"<h1>{escape(str(workspace.get('profile_name') or 'unknown workspace'))}</h1>",
            '<dl class="meta">',
            f"<div><dt>控制台范围</dt><dd>{escape(scope_label)}</dd></div>",
            f"<div><dt>工作区路径</dt><dd>{escape(str(workspace.get('workspace_root') or ''))}</dd></div>",
            f"<div><dt>工作区状态</dt><dd>{status_chip(workspace.get('workspace_status') or 'unknown')}</dd></div>",
            f"<div><dt>本机时间</dt><dd>{escape(generated_at_local_label)}</dd></div>",
            f"<div><dt>UTC 时间</dt><dd>{escape(generated_at)}</dd></div>",
            f"<div><dt>流模式</dt><dd>{escape(str(stream.get('href') or '静态快照'))}</dd></div>",
            "</dl>",
            "</header>",
            _empty_state_section(empty_state),
            _study_run_section(studies),
            '<section class="layout">',
            _timeline_section(studies),
            _stream_section("终端输出", studies, key="terminal_sources"),
            _stream_section("日志输出", studies, key="log_sources"),
            "</section>",
            _terminal_attach_gate_section(terminal_gate),
            _action_intents_section(action_intents),
            _refs_section("产物来源", studies, key="artifact_refs"),
            _refs_section("事件来源", studies, key="event_refs"),
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def _study_run_section(studies: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for study in studies:
        runs = [dict(item) for item in study.get("runs") or [] if isinstance(item, Mapping)]
        if not runs:
            rows.append(_study_run_row(study, {}))
            continue
        for run in runs:
            rows.append(_study_run_row(study, run))
    return (
        '<section class="panel wide">'
        "<h2>论文运行表</h2>"
        '<div class="table-wrap"><table class="responsive-table">'
        "<thead><tr><th>论文线</th><th>运行编号</th><th>状态</th><th>阶段</th>"
        "<th>运行健康</th><th>监管心跳</th><th>worker</th><th>阻塞/动作</th><th>最后可见时间</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def _study_run_row(study: Mapping[str, Any], run: Mapping[str, Any]) -> str:
    worker = _worker_label(study.get("worker_running"))
    action = " | ".join(
        dedupe(
            [
                str(study.get("runtime_observation_status") or ""),
                str(study.get("canonical_runtime_action") or ""),
                *[str(item) for item in study.get("blocking_reasons") or []],
                str(study.get("next_action_summary") or ""),
            ]
        )
    )
    headers = ("论文线", "运行编号", "状态", "阶段", "运行健康", "监管心跳", "worker", "阻塞/动作", "最后可见时间")
    values = (
        escape(display_text(study.get("study_id"), empty_text="未知论文线", preserve_known_token=False)),
        escape(display_text(run.get("run_id") or study.get("active_run_id"), empty_text="无 live run", preserve_known_token=False)),
        escape(_display_text(study.get("state_label") or run.get("status"))),
        escape(_display_text(study.get("current_stage"))),
        status_chip(study.get("runtime_health_status") or "unknown"),
        status_chip(study.get("supervisor_tick_status") or "unknown"),
        escape(worker),
        escape(_action_label(action) or "无"),
        escape(_time_text(run.get("last_seen_at"))),
    )
    return (
        "<tr>"
        + "".join(f'<td data-label="{escape(label)}">{value}</td>' for label, value in zip(headers, values, strict=True))
        + "</tr>"
    )


def _timeline_section(studies: list[dict[str, Any]]) -> str:
    items: list[str] = []
    for study in studies:
        study_id = str(study.get("study_id") or "unknown-study")
        for event in study.get("timeline") or []:
            if not isinstance(event, Mapping):
                continue
            prefix = " | ".join(
                dedupe(
                    [
                        study_id,
                        _time_text(event.get("observed_at")),
                        _topic_label(event.get("topic")),
                    ]
                )
            )
            summary = event.get("summary") or event.get("status") or event.get("source_ref") or "observed"
            summary_label = _action_label(str(summary))
            label = f"{prefix}: {summary_label}" if prefix else summary_label
            items.append(label)
    return _list_panel("运行时间线", items, empty_text="当前没有运行事件。")


def _display_text(value: object, empty_text: str = "未提供") -> str:
    return display_text(value, empty_text=empty_text)


def _stream_section(title: str, studies: list[dict[str, Any]], *, key: str) -> str:
    blocks: list[str] = []
    for study in studies:
        study_id = str(study.get("study_id") or "unknown-study")
        for source in study.get(key) or []:
            if not isinstance(source, Mapping):
                continue
            tail = "\n".join(string_list(source.get("tail")))
            label = str(source.get("label") or _stream_label_for_key(key))
            source_ref = str(source.get("source_ref") or "")
            status = str(source.get("status") or "unknown")
            blocks.append(
                '<article class="stream-block">'
                f"<h3>{escape(study_id)} / {escape(label)}</h3>"
                f'<p class="source-ref">状态={escape(status_label(status))} · {escape(source_ref)}</p>'
                f"<pre>{escape(tail or '当前没有 tail 内容。')}</pre>"
                "</article>"
            )
    if not blocks:
        blocks.append('<p class="empty">当前没有可展示的 stream tail；如果 active_run_id 为空或 source status 为 missing，这本身就是运行证据。</p>')
    return f'<section class="panel stream"><h2>{escape(title)}</h2>{"".join(blocks)}</section>'


def _refs_section(title: str, studies: list[dict[str, Any]], *, key: str) -> str:
    refs: list[str] = []
    for study in studies:
        refs.extend(string_list(study.get(key)))
    return _list_panel(title, dedupe(refs), empty_text="当前没有来源引用。")


def _list_panel(title: str, items: list[str], *, empty_text: str) -> str:
    if not items:
        body = f'<p class="empty">{escape(empty_text)}</p>'
    else:
        body = "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"
    return f'<section class="panel"><h2>{escape(title)}</h2>{body}</section>'


def _empty_state_section(empty_state: Mapping[str, Any]) -> str:
    if not empty_state:
        return ""
    reason = str(empty_state.get("reason") or "")
    if reason != "no_live_run":
        return ""
    summary = str(empty_state.get("summary") or "当前没有 live run。")
    next_action = str(empty_state.get("next_action") or "回到 Progress Portal 查看下一步。")
    blockers = mapping_list(empty_state.get("study_blockers"))
    blocker_table = ""
    if blockers:
        rows = []
        for item in blockers:
            rows.append(
                "<tr>"
                f'<td data-label="论文线">{escape(display_text(item.get("study_id"), empty_text="未知论文线", preserve_known_token=False))}</td>'
                f'<td data-label="运行健康">{status_chip(item.get("runtime_health_status") or "unknown")}</td>'
                f'<td data-label="阻塞">{escape(_action_label(", ".join(string_list(item.get("blocking_reasons"))) or "无"))}</td>'
                f'<td data-label="动作">{escape(_action_label(str(item.get("canonical_runtime_action") or item.get("next_action_summary") or "未提供")))}</td>'
                "</tr>"
            )
        blocker_table = (
            '<div class="table-wrap"><table class="responsive-table">'
            "<thead><tr><th>论文线</th><th>运行健康</th><th>阻塞</th><th>动作</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table></div>"
        )
    return (
        '<section class="panel wide notice">'
        "<h2>当前没有 live run</h2>"
        f"<p>{escape(summary)}</p>"
        f"<p>{escape(next_action)}</p>"
        f"{blocker_table}"
        "</section>"
    )


def _action_intents_section(action_intents: list[dict[str, Any]]) -> str:
    rows = []
    headers = ("意图", "权限归属", "直接执行", "命令")
    for item in action_intents:
        values = (
            escape(_intent_label(item.get("intent"))),
            escape(_authority_label(item.get("authority"))),
            escape("是" if item.get("executes_directly") is True else "否"),
            f"<code>{escape(str(item.get('command') or ''))}</code>",
        )
        rows.append(
            "<tr>"
            + "".join(f'<td data-label="{escape(label)}">{value}</td>' for label, value in zip(headers, values, strict=True))
            + "</tr>"
        )
    if not rows:
        return _list_panel("控制器动作意图", [], empty_text="当前没有 controller action intent。")
    return (
        '<section class="panel wide">'
        "<h2>控制器动作意图</h2>"
        '<div class="table-wrap"><table class="responsive-table">'
        "<thead><tr><th>意图</th><th>权限归属</th><th>直接执行</th><th>命令</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def _terminal_attach_gate_section(gate: Mapping[str, Any]) -> str:
    if not gate:
        return ""
    if gate.get("status") == "available":
        return _terminal_attach_controls_section(gate)
    contract = mapping(gate.get("required_owner_contract"))
    rows = []
    headers = ("能力", "owner contract")
    for key in ("token", "lease", "idempotency", "audit", "input", "resize", "detach"):
        rows.append(
            "<tr>"
            f'<td data-label="{escape(headers[0])}">{escape(key)}</td>'
            f'<td data-label="{escape(headers[1])}">{escape(str(contract.get(key) or "missing"))}</td>'
            "</tr>"
        )
    return (
        '<section class="panel wide notice">'
        "<h2>Terminal Attach Gate</h2>"
        f"<p>status={escape(str(gate.get('status') or 'unknown'))} · "
        f"read_only_default={escape(str(bool(gate.get('read_only_default'))).lower())} · "
        f"forbidden_owner={escape(str(gate.get('forbidden_owner') or ''))}</p>"
        '<div class="table-wrap"><table class="responsive-table">'
        "<thead><tr><th>能力</th><th>owner contract</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table></div>"
        "</section>"
    )


def _terminal_attach_controls_section(gate: Mapping[str, Any]) -> str:
    endpoints = mapping(gate.get("endpoints"))
    capabilities = set(string_list(gate.get("capabilities")))
    buttons = []
    labels = {
        "attach": "Attach",
        "input": "Input",
        "resize": "Resize",
        "detach": "Detach",
    }
    for capability in ("attach", "input", "resize", "detach"):
        if capability not in capabilities:
            continue
        endpoint = str(endpoints.get(capability) or "")
        buttons.append(
            f'<button type="button" data-terminal-action="{escape(capability, quote=True)}" '
            f'data-endpoint="{escape(endpoint, quote=True)}">{escape(labels[capability])}</button>'
        )
    return (
        '<section class="panel wide terminal-attach">'
        "<h2>Terminal Attach</h2>"
        f"<p>status=available · owner={escape(str(gate.get('owner') or ''))} · "
        f"scope={escape(str(gate.get('study_id') or 'profile'))}</p>"
        '<div class="terminal-actions">'
        + "".join(buttons)
        + "</div>"
        '<label class="terminal-input-label" for="terminal-input">Input</label>'
        '<textarea id="terminal-input" rows="4" placeholder="MAS-owned terminal input"></textarea>'
        '<div class="terminal-resize">'
        '<label for="terminal-cols">Cols</label><input id="terminal-cols" type="number" min="20" value="120">'
        '<label for="terminal-rows">Rows</label><input id="terminal-rows" type="number" min="5" value="30">'
        "</div>"
        '<p class="source-ref">UI shows owner-provided attach/input/resize/detach endpoints; '
        'transport and audit remain owned by the MAS terminal attach owner.</p>'
        "</section>"
    )


def _worker_label(value: object) -> str:
    if value is True:
        return "运行中"
    if value is False:
        return "未运行"
    return "未知"


def _topic_label(value: object) -> str:
    topic_text = text(value)
    labels = {
        "workspace.status": "工作区状态",
        "study.status": "论文线状态",
        "runtime.health": "运行健康",
        "runtime.supervision": "监管心跳",
        "artifact.delta": "产物增量",
        "terminal.tail": "终端尾部",
        "log.tail": "日志尾部",
    }
    return labels.get(topic_text or "", display_text(topic_text, empty_text="事件", preserve_known_token=False))


def _action_label(value: str) -> str:
    result = value
    replacements = {
        "no_live_run": "无 live run",
        "external_supervisor_required": "需要外层 supervisor",
        "runtime_recovery_retry_budget_exhausted": "runtime 恢复重试预算耗尽",
        "quest_marked_running_but_no_live_session": "标记运行但没有 live session",
        "await_explicit_resume": "等待显式恢复",
        "awaiting_explicit_resume": "等待显式恢复",
        "run_id_without_worker": "有 run_id 但 worker 未确认",
        "recover_runtime": "恢复 runtime",
        "live_worker_meaningful_artifact_delta_timeout": "live worker 产物增量超时",
        "same_fingerprint_loop": "同 fingerprint 循环",
        "recovering": "恢复中",
        "fresh": "新鲜",
        "missing": "缺失",
        "none": "无",
        "escalated": "已升级",
        "parked": "停驻",
    }
    for source, target in replacements.items():
        result = result.replace(source, target)
    return result


def _time_text(value: object) -> str:
    time_value = text(value)
    if time_value is None:
        return "未提供"
    return local_time_label(time_value)


def _stream_label_for_key(key: str) -> str:
    if key == "terminal_sources":
        return "终端摘要"
    if key == "log_sources":
        return "worker 日志"
    return "来源"


def _intent_label(value: object) -> str:
    labels = {
        "inspect_progress": "查看进度",
        "open_progress_projection": "打开运行状态",
        "request_reconcile": "请求 reconcile",
    }
    intent_text = text(value) or ""
    return labels.get(intent_text, display_text(intent_text, empty_text="未提供", preserve_known_token=False))


def _authority_label(value: object) -> str:
    labels = {
        "controller_required": "需要 MAS controller",
    }
    authority_text = text(value) or ""
    return labels.get(authority_text, display_text(authority_text, empty_text="未提供", preserve_known_token=False))


__all__ = ["render_live_console_html"]
