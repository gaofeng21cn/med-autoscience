from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from html import escape
from typing import Any

from med_autoscience.controllers.progress_portal_parts import local_time_projection
from med_autoscience.controllers.progress_portal_parts.rendering import local_time_label
from med_autoscience.controllers.progress_portal_parts.status_display import display_text, status_chip, status_label
from med_autoscience.runtime_protocol import live_console_contract


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_live_console_ui"
BRAND = "Med Auto Science"
LIVE_CONSOLE_HTML_REF = "ops/mas/live-console/index.html"
LIVE_CONSOLE_PAYLOAD_REF = "artifacts/runtime/live_console/ui_payload/latest.json"


def build_live_console_ui_payload(
    *,
    live_console_snapshot: Mapping[str, Any],
    generated_at: str | None = None,
    progress_portal_href: str = "../progress/index.html",
    stream_href: str | None = None,
) -> dict[str, Any]:
    workspace = _mapping(live_console_snapshot.get("workspace"))
    studies = _studies(live_console_snapshot.get("studies"))
    live_runs = _mapping_list(live_console_snapshot.get("runs"))
    selected_study_id = _text(live_console_snapshot.get("selected_study_id"))
    scope = "study" if selected_study_id else "profile"
    source_refs = _source_refs(studies)
    generated = generated_at or _utc_now()
    no_live_blockers = _no_live_blockers(studies)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "brand": BRAND,
        "generated_at": generated,
        "generated_at_local": local_time_projection(generated, timezone_name=None),
        "scope": scope,
        "selected_study_id": selected_study_id,
        "payload_ref": LIVE_CONSOLE_PAYLOAD_REF,
        "html_ref": LIVE_CONSOLE_HTML_REF,
        "authority": {
            "kind": "read_only_live_observation_shell",
            "read_only": True,
            "writes_authority_surface": False,
            "state_interpretation_owner": "runtime_session_read_model",
            "authority_note": (
                "Live Console renders MAS live observation payloads and does not own runtime, "
                "publication, controller, package, or study truth."
            ),
        },
        "portal_handoff": {
            "progress_portal_href": progress_portal_href,
            "relationship": "navigation_return_link",
            "portal_owns_live_console_state_interpretation": False,
        },
        "stream": {
            "href": stream_href,
            "mode": "read_only_observation",
            "writes_authority_surface": False,
        },
        "terminal_attach_gate": live_console_contract.terminal_attach_gate_status(
            study_id=selected_study_id,
        ),
        "workspace": {
            "profile_name": _text(workspace.get("profile_name")) or "unknown",
            "workspace_root": _text(workspace.get("workspace_root")) or "",
            "workspace_status": _text(workspace.get("workspace_status")) or "unknown",
        },
        "studies": studies,
        "empty_state": _empty_state(
            _mapping(live_console_snapshot.get("empty_state")),
            studies=studies,
            runs=live_runs,
            no_live_blockers=no_live_blockers,
        ),
        "controller_action_intents": _mapping_list(live_console_snapshot.get("controller_action_intents")),
        "source_refs": source_refs,
    }


def render_live_console_html(payload: Mapping[str, Any]) -> str:
    workspace = _mapping(payload.get("workspace"))
    studies = [dict(item) for item in payload.get("studies") or [] if isinstance(item, Mapping)]
    portal_handoff = _mapping(payload.get("portal_handoff"))
    stream = _mapping(payload.get("stream"))
    terminal_gate = _mapping(payload.get("terminal_attach_gate"))
    empty_state = _mapping(payload.get("empty_state"))
    action_intents = _mapping_list(payload.get("controller_action_intents"))
    generated_at = str(payload.get("generated_at") or "unknown")
    generated_at_local = _mapping(payload.get("generated_at_local"))
    generated_at_local_label = str(generated_at_local.get("label") or generated_at)
    brand = str(payload.get("brand") or BRAND)
    progress_href = str(portal_handoff.get("progress_portal_href") or "../progress/index.html")
    selected_study_id = _text(payload.get("selected_study_id"))
    scope = _text(payload.get("scope")) or ("study" if selected_study_id else "profile")
    scope_label = selected_study_id if scope == "study" and selected_study_id else "operator 总览"
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{escape(brand)} 运行控制台</title>",
            "<style>",
            _css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="console">',
            '<header class="masthead">',
            '<div class="topline">',
            f'<span class="brand">{escape(brand)}</span>',
            '<span class="badge">只读</span>',
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


def _studies(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    studies: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        study_id = _text(item.get("study_id"))
        if study_id is None:
            continue
        studies.append(
            {
                "study_id": study_id,
                "state_label": _text(item.get("state_label")),
                "current_stage": _text(item.get("current_stage")),
                "active_run_id": _text(item.get("active_run_id")),
                "runtime_health_status": _text(item.get("runtime_health_status")),
                "supervisor_tick_status": _text(item.get("supervisor_tick_status")),
                "worker_running": item.get("worker_running") if isinstance(item.get("worker_running"), bool) else None,
                "runtime_observation_status": _text(item.get("runtime_observation_status")),
                "blocking_reasons": _string_list(item.get("blocking_reasons")),
                "canonical_runtime_action": _text(item.get("canonical_runtime_action")),
                "allowed_controller_actions": _string_list(item.get("allowed_controller_actions")),
                "next_action_summary": _text(item.get("next_action_summary")),
                "runs": _runs(item.get("runs")),
                "timeline": _timeline(item.get("timeline")),
                "terminal_sources": _stream_sources(item.get("terminal_sources")),
                "log_sources": _stream_sources(item.get("log_sources")),
                "artifact_refs": _string_list(item.get("artifact_refs")),
                "event_refs": _string_list(item.get("event_refs")),
            }
        )
    return studies


def _runs(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    runs: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        run_id = _text(item.get("run_id"))
        if run_id is None:
            continue
        last_seen = _text(item.get("last_seen_at"))
        runs.append(
            {
                "run_id": run_id,
                "status": _text(item.get("status")),
                "started_at": _text(item.get("started_at")),
                "last_seen_at": last_seen,
                "last_seen_at_local": local_time_projection(last_seen, timezone_name=None) if last_seen else None,
            }
        )
    return runs


def _timeline(value: object) -> list[dict[str, str | None]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    events: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        summary = _text(item.get("summary")) or _text(item.get("status")) or _text(item.get("source_ref"))
        if summary is None:
            continue
        events.append(
            {
                "observed_at": _text(item.get("observed_at")),
                "observed_at_local": _mapping(item.get("local_time"))
                or (
                    local_time_projection(str(item.get("observed_at")), timezone_name=None)
                    if _text(item.get("observed_at"))
                    else {}
                ),
                "topic": _text(item.get("topic")),
                "summary": summary,
                "source_ref": _text(item.get("source_ref")),
            }
        )
    return events


def _stream_sources(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    sources: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        source_ref = _text(item.get("source_ref"))
        tail = _string_list(item.get("tail"))
        if source_ref is None and not tail:
            continue
        sources.append(
            {
                "label": _text(item.get("label")) or _stream_label_for_source(item),
                "source_ref": source_ref,
                "status": _text(item.get("status")) or "unknown",
                "tail": tail,
            }
        )
    return sources


def _source_refs(studies: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for study in studies:
        for event in study.get("timeline") or []:
            if isinstance(event, Mapping):
                refs.append(str(event.get("source_ref") or ""))
        for key in ("terminal_sources", "log_sources"):
            for source in study.get(key) or []:
                if isinstance(source, Mapping):
                    refs.append(str(source.get("source_ref") or ""))
        refs.extend(_string_list(study.get("artifact_refs")))
        refs.extend(_string_list(study.get("event_refs")))
    return _dedupe(refs)


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
        _dedupe(
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
        escape(display_text(study.get("study_id"), fallback="未知论文线", preserve_known_token=False)),
        escape(display_text(run.get("run_id") or study.get("active_run_id"), fallback="无 live run", preserve_known_token=False)),
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
                _dedupe(
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


def _display_text(value: object, fallback: str = "未提供") -> str:
    return display_text(value, fallback=fallback)


def _stream_section(title: str, studies: list[dict[str, Any]], *, key: str) -> str:
    blocks: list[str] = []
    for study in studies:
        study_id = str(study.get("study_id") or "unknown-study")
        for source in study.get(key) or []:
            if not isinstance(source, Mapping):
                continue
            tail = "\n".join(_string_list(source.get("tail")))
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
        refs.extend(_string_list(study.get(key)))
    return _list_panel(title, _dedupe(refs), empty_text="当前没有来源引用。")


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
    blockers = _mapping_list(empty_state.get("study_blockers"))
    blocker_table = ""
    if blockers:
        rows = []
        for item in blockers:
            rows.append(
                "<tr>"
                f'<td data-label="论文线">{escape(display_text(item.get("study_id"), fallback="未知论文线", preserve_known_token=False))}</td>'
                f'<td data-label="运行健康">{status_chip(item.get("runtime_health_status") or "unknown")}</td>'
                f'<td data-label="阻塞">{escape(_action_label(", ".join(_string_list(item.get("blocking_reasons"))) or "无"))}</td>'
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
    contract = _mapping(gate.get("required_owner_contract"))
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


def _worker_label(value: object) -> str:
    if value is True:
        return "运行中"
    if value is False:
        return "未运行"
    return "未知"


def _topic_label(value: object) -> str:
    text = _text(value)
    labels = {
        "workspace.status": "工作区状态",
        "study.status": "论文线状态",
        "runtime.health": "运行健康",
        "runtime.supervision": "监管心跳",
        "artifact.delta": "产物增量",
        "terminal.tail": "终端尾部",
        "log.tail": "日志尾部",
    }
    return labels.get(text or "", display_text(text, fallback="事件", preserve_known_token=False))


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
    text = _text(value)
    if text is None:
        return "未提供"
    return local_time_label(text)


def _stream_label_for_key(key: str) -> str:
    if key == "terminal_sources":
        return "终端摘要"
    if key == "log_sources":
        return "worker 日志"
    return "来源"


def _stream_label_for_source(item: Mapping[str, Any]) -> str:
    source_ref = _text(item.get("source_ref")) or _text(item.get("path")) or ""
    if "worker.log" in source_ref or "/logs/" in source_ref:
        return "worker 日志"
    if "bash_exec" in source_ref or "stdout" in source_ref or "terminal" in source_ref:
        return "终端摘要"
    return "来源"


def _intent_label(value: object) -> str:
    labels = {
        "inspect_progress": "查看进度",
        "open_study_runtime_status": "打开运行状态",
        "request_reconcile": "请求 reconcile",
    }
    text = _text(value) or ""
    return labels.get(text, display_text(text, fallback="未提供", preserve_known_token=False))


def _authority_label(value: object) -> str:
    labels = {
        "controller_required": "需要 MAS controller",
    }
    text = _text(value) or ""
    return labels.get(text, display_text(text, fallback="未提供", preserve_known_token=False))


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = " ".join(str(value).strip().split())
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _empty_state(
    explicit: Mapping[str, Any],
    *,
    studies: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    no_live_blockers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if explicit:
        return dict(explicit)
    if runs:
        return None
    if not studies:
        return {
            "reason": "no_studies",
            "summary": "当前 profile 没有发现可展示的 study。",
            "next_action": "确认 workspace profile 和 studies root。",
        }
    return {
        "reason": "no_live_run",
        "summary": "当前没有 live run；terminal/log 缺失是运行状态证据，而不是页面加载失败。",
        "study_count": len(studies),
        "study_blockers": no_live_blockers,
        "next_action": "回到 Progress Portal 查看 blocker，必要时通过 MAS controller 请求 reconcile。",
    }


def _no_live_blockers(studies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for study in studies:
        if study.get("active_run_id"):
            continue
        reasons = _string_list(study.get("blocking_reasons"))
        action = _text(study.get("canonical_runtime_action"))
        health = _text(study.get("runtime_health_status"))
        if (
            not reasons
            and action not in {"external_supervisor_required", "await_explicit_resume"}
            and health not in {"escalated", "parked", "missing", "none"}
        ):
            continue
        blockers.append(
            {
                "study_id": study.get("study_id"),
                "runtime_health_status": health,
                "blocking_reasons": reasons,
                "canonical_runtime_action": action,
                "next_action_summary": study.get("next_action_summary"),
            }
        )
    return blockers


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or stripped.lower() in {"none", "null", "unknown"}:
        return None
    return stripped


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f6f8fb;
  --ink: #142033;
  --muted: #56657a;
  --line: #d9e1ec;
  --panel: #ffffff;
  --accent: #0f766e;
  --warn: #8a4b00;
  --bad: #b91c1c;
  --ok: #047857;
  --code: #101827;
  --panel-alt: #fbfcfd;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 15px;
  line-height: 1.5;
}
.console {
  width: min(1280px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 24px 0 40px;
}
.masthead, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.masthead {
  padding: 22px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(20, 32, 51, .04);
}
.topline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}
.brand {
  color: var(--muted);
  font-weight: 700;
  letter-spacing: 0;
}
.badge {
  color: var(--warn);
  border: 1px solid rgba(138, 75, 0, .35);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 800;
}
.portal-link {
  color: var(--accent);
  font-weight: 700;
  text-decoration: none;
}
h1 {
  margin: 14px 0 12px;
  font-size: 30px;
  line-height: 1.2;
  letter-spacing: 0;
}
h2 {
  margin: 0 0 12px;
  font-size: 18px;
  line-height: 1.3;
  letter-spacing: 0;
}
h3 {
  margin: 0 0 6px;
  font-size: 14px;
  letter-spacing: 0;
}
.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin: 0;
}
.meta div {
  min-width: 0;
}
dt {
  color: var(--muted);
  font-size: 12px;
}
dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
}
.panel {
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(20, 32, 51, .03);
}
.wide {
  grid-column: 1 / -1;
}
.layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.stream {
  min-width: 0;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border-bottom: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
  overflow-wrap: anywhere;
}
th {
  color: var(--muted);
  font-size: 12px;
}
td code {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}
tbody tr:hover td { background: #f7fafc; }
.status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--line);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.35;
  white-space: nowrap;
}
.status-ok { color: var(--ok); background: #edf9f1; border-color: #b7e4c7; }
.status-warn { color: var(--warn); background: #fff7e6; border-color: #f0d18a; }
.status-bad { color: var(--bad); background: #fff1f1; border-color: #f0b9b9; }
.status-neutral { color: var(--muted); background: #f3f6f9; border-color: var(--line); }
ul {
  margin: 0;
  padding-left: 20px;
}
li {
  margin: 4px 0;
  overflow-wrap: anywhere;
}
.stream-block {
  border-top: 1px solid var(--line);
  padding-top: 12px;
  margin-top: 12px;
}
.stream-block:first-of-type {
  border-top: 0;
  padding-top: 0;
  margin-top: 0;
}
.source-ref {
  color: var(--muted);
  margin: 0 0 8px;
  overflow-wrap: anywhere;
}
pre {
  margin: 0;
  min-height: 88px;
  overflow: auto;
  border-radius: 6px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid var(--line);
  color: var(--ink);
  font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  white-space: pre-wrap;
}
.empty {
  color: var(--muted);
  margin: 0;
}
@media (max-width: 820px) {
  .console {
    width: min(100vw - 20px, 1280px);
    padding-top: 10px;
  }
  .layout {
    grid-template-columns: 1fr;
  }
  h1 {
    font-size: 24px;
  }
  .table-wrap {
    overflow-x: visible;
  }
  table.responsive-table,
  table.responsive-table thead,
  table.responsive-table tbody,
  table.responsive-table tr,
  table.responsive-table th,
  table.responsive-table td {
    display: block;
    width: 100%;
  }
  table.responsive-table thead {
    display: none;
  }
  table.responsive-table tr {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--panel-alt);
    margin: 0 0 10px;
    padding: 10px 12px;
  }
  table.responsive-table td {
    border-bottom: 0;
    padding: 6px 0;
    display: grid;
    grid-template-columns: minmax(96px, 38%) minmax(0, 1fr);
    gap: 10px;
  }
  table.responsive-table td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
  }
}
""".strip()


__all__ = [
    "LIVE_CONSOLE_HTML_REF",
    "LIVE_CONSOLE_PAYLOAD_REF",
    "build_live_console_ui_payload",
    "render_live_console_html",
]
