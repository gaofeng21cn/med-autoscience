from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from html import escape
import http.server
import json
from pathlib import Path
import socketserver
import threading
from typing import Any
import webbrowser

from med_autoscience.controllers.progress_portal_parts import (
    condition_badge,
    condition_section,
    dedupe_texts,
    display_source_refs,
    display_text,
    event_section,
    gate_text,
    list_html,
    list_section,
    live_console_projection,
    local_time_projection,
    portal_css,
    progress_section_explanations,
    refresh_meta,
    render_live_console_portal_link,
    render_section_explanations_section,
    render_workspace_alerts_section,
    render_workspace_studies_section,
    runtime_continuity_section,
    section,
    selected_workspace_study_id,
    source_refs as collect_source_refs,
    status_chip,
    unique_text,
    workspace_alert_projection,
    workspace_delivery_paragraphs,
    workspace_next_step_paragraphs,
    workspace_quality_paragraphs,
    workspace_status_paragraphs,
    workspace_studies,
)
from med_autoscience.controllers.runtime_continuity_projection import runtime_continuity_projection
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_progress_portal"
HOSTED_PACKAGE_SURFACE_KIND = "mas_progress_portal_hosted_package"
BRAND = "Med Auto Science"
PROGRESS_PORTAL_PAYLOAD_REF = "artifacts/runtime/progress_portal/latest.json"
PROGRESS_PORTAL_HTML_REF = "ops/mas/progress/index.html"
PROGRESS_PORTAL_HOSTED_PACKAGE_REF = "artifacts/runtime/progress_portal/hosted_package.json"


def build_progress_portal_payload(
    *,
    profile: WorkspaceProfile | None = None,
    profile_name: str | None = None,
    workspace_root: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    profile_ref: str | Path | None = None,
    progress_payload: Mapping[str, Any] | None = None,
    cockpit_payload: Mapping[str, Any] | None = None,
    runtime_payload: Mapping[str, Any] | None = None,
    package_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    local_timezone: str | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    auto_refresh_seconds: int | None = None,
    live_console_disabled_reason: str | None = None,
) -> dict[str, Any]:
    resolved_profile_name = profile_name or (profile.name if profile is not None else None) or "unknown"
    resolved_workspace_root = Path(
        workspace_root if workspace_root is not None else (profile.workspace_root if profile is not None else ".")
    )
    resolved_study_id = _non_empty_text(study_id)
    workspace_overview_mode = (
        resolved_study_id is None
        and study_root is None
        and progress_payload is None
    )

    progress = dict(progress_payload or {})
    if not progress and not workspace_overview_mode:
        if profile is None:
            raise ValueError("profile is required when progress_payload is not provided")
        from med_autoscience.controllers import study_progress

        progress = study_progress.read_study_progress(
            profile=profile,
            profile_ref=profile_ref,
            study_id=resolved_study_id,
            study_root=study_root,
            entry_mode=entry_mode,
            sync_runtime_summary=sync_runtime_summary,
        )
    cockpit = dict(cockpit_payload or {})
    if not cockpit and profile is not None and progress_payload is None:
        from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_payload import (
            read_workspace_cockpit,
        )

        cockpit = read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    resolved_study_id = (
        resolved_study_id
        or _non_empty_text(progress.get("study_id"))
        or selected_workspace_study_id(cockpit)
        or "workspace-overview"
    )

    runtime = dict(runtime_payload or {})
    package = dict(package_payload or {})
    user_visible = _valid_user_visible_projection(progress.get("user_visible_projection"))
    freshness = _freshness(progress.get("progress_freshness"))
    latest_events = _latest_events(user_visible, progress)
    quality = _quality_summary(progress.get("publication_eval"))
    delivery = _delivery_summary(progress, package, study_id=resolved_study_id)
    runtime_reconcile_trigger = _runtime_reconcile_trigger(progress.get("runtime_reconcile_trigger"))
    outer_supervision_slo = _outer_supervision_slo(progress.get("outer_supervision_slo"))
    workspace_study_rows = workspace_studies(cockpit, selected_study_id=resolved_study_id)
    workspace_alerts = workspace_alert_projection(
        cockpit.get("workspace_alerts"),
        workspace_studies=workspace_study_rows,
    )
    source_refs = collect_source_refs(progress, cockpit, runtime, package)
    source_payloads = {
        "progress": _source_payload_summary(progress),
        "cockpit": _source_payload_summary(cockpit),
        "runtime": _source_payload_summary(runtime),
        "package": _source_payload_summary(package),
    }
    runtime_continuity = _runtime_continuity(progress, runtime)
    live_console = live_console_projection(disabled_reason=live_console_disabled_reason)
    has_workspace_studies = bool(workspace_study_rows)
    has_workspace_alerts = bool(workspace_alerts["visible_items"])
    has_diagnostics = bool(workspace_alerts["suppressed_items"])
    has_latest_events = bool(latest_events)
    has_source_refs = bool(source_refs)
    conditions = _conditions(
        study_id=resolved_study_id,
        progress=progress,
        user_visible=user_visible,
        cockpit=cockpit,
        runtime=runtime,
        package=package,
        freshness=freshness,
        delivery=delivery,
        runtime_reconcile_trigger=runtime_reconcile_trigger,
        outer_supervision_slo=outer_supervision_slo,
        source_refs=source_refs,
    )
    resolved_generated_at = generated_at or _utc_now()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "brand": BRAND,
        "generated_at": resolved_generated_at,
        "generated_at_local": local_time_projection(resolved_generated_at, timezone_name=local_timezone),
        "authority": {
            "kind": "read_model_display_artifact",
            "writes_authority_surface": False,
            "authority_note": "Portal consumes MAS durable progress surfaces and does not own study, runtime, publication, or package truth.",
        },
        "workspace": {
            "profile_name": resolved_profile_name,
            "workspace_root": str(resolved_workspace_root),
            "workspace_status": _non_empty_text(cockpit.get("workspace_status")),
            "workspace_alerts": workspace_alerts["visible"],
            "workspace_alert_items": workspace_alerts["visible_items"],
            "studies": workspace_study_rows,
            "diagnostics": {
                "suppressed_alerts": workspace_alerts["suppressed"],
                "suppressed_alert_items": workspace_alerts["suppressed_items"],
                "suppressed_alert_policy": "legacy_runtime_or_inactive_study_noise",
            },
        },
        "study": {
            "study_id": resolved_study_id,
            "scope": "workspace" if workspace_overview_mode else "study",
            "state_label": _field(
                user_visible,
                "state_label",
                "工作区概览" if workspace_overview_mode else "状态投影缺失",
            ),
            "state_summary": _field(
                user_visible,
                "state_summary",
                "当前显示 workspace 级多论文状态；选择具体 study 后查看单篇进度。"
                if workspace_overview_mode
                else "当前缺少可展示的用户状态投影。",
            ),
            "current_stage": _field(user_visible, "current_stage"),
            "current_stage_summary": _field(user_visible, "current_stage_summary"),
            "paper_stage": _field(user_visible, "paper_stage"),
            "paper_stage_summary": _field(user_visible, "paper_stage_summary"),
            "current_blockers": _list_field(user_visible, "current_blockers"),
            "next_system_action": _field(user_visible, "next_system_action", "等待 MAS 重新生成 canonical progress projection。"),
            "needs_physician_decision": bool(
                user_visible.get("needs_physician_decision") or user_visible.get("needs_user_decision")
            ),
            "supervision": _supervision(progress, runtime),
            "runtime_reconcile_trigger": runtime_reconcile_trigger or None,
            "outer_supervision_slo": outer_supervision_slo or None,
            "runtime_continuity": runtime_continuity,
        },
        "freshness": freshness,
        "latest_events": latest_events,
        "quality": quality,
        "delivery": delivery,
        "live_console": live_console,
        "conditions": conditions,
        "section_explanations": progress_section_explanations(
            workspace_overview_mode=workspace_overview_mode,
            has_workspace_studies=has_workspace_studies,
            has_workspace_alerts=has_workspace_alerts,
            has_diagnostics=has_diagnostics,
            has_latest_events=has_latest_events,
            has_source_refs=has_source_refs,
            live_console_available=bool(live_console.get("available")),
        ),
        "source_refs": source_refs,
        "source_payloads": source_payloads,
        "opl_handoff": _opl_handoff_projection(
            study_id=resolved_study_id,
            profile_name=resolved_profile_name,
            freshness=freshness,
            source_refs=source_refs,
            source_payloads=source_payloads,
            delivery=delivery,
            conditions=conditions,
            runtime_continuity=runtime_continuity,
        ),
    }
    if auto_refresh_seconds is not None and auto_refresh_seconds > 0:
        payload["portal_view"] = {
            "auto_refresh_seconds": int(auto_refresh_seconds),
            "refresh_mode": "read_only_server_request_refresh",
        }
    return payload


def render_progress_portal_html(payload: Mapping[str, Any]) -> str:
    workspace = _mapping(payload.get("workspace"))
    study = _mapping(payload.get("study"))
    freshness = _mapping(payload.get("freshness"))
    quality = _mapping(payload.get("quality"))
    delivery = _mapping(payload.get("delivery"))
    live_console = _mapping(payload.get("live_console"))
    conditions = _mapping(payload.get("conditions"))
    workspace_diagnostics = _mapping(workspace.get("diagnostics"))
    runtime_continuity = _mapping(study.get("runtime_continuity"))
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
    brand = str(payload.get("brand") or BRAND)
    state_label = str(study.get("state_label") or "状态投影缺失")
    workspace_title = str(workspace.get("profile_name") or "unknown workspace")
    selected_study_id = str(study.get("study_id") or "unknown-study")
    condition_badge_label = condition_badge(conditions)
    blockers = _string_list(study.get("current_blockers"))
    workspace_alerts = _string_list(workspace.get("workspace_alerts"))
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
            '<dl class="meta">',
            f"<div><dt>本机时间</dt><dd>{escape(generated_at_local_label)}</dd></div>",
            f"<div><dt>UTC 时间</dt><dd>{escape(generated_at)}</dd></div>",
            f"<div><dt>进度新鲜度</dt><dd>{status_chip(freshness.get('status') or 'unknown')}</dd></div>",
            f"<div><dt>工作区</dt><dd>{escape(str(workspace.get('profile_name') or 'unknown'))}</dd></div>",
            f"<div><dt>当前论文线</dt><dd>{escape('工作区总览' if workspace_overview_mode else selected_study_id)}</dd></div>",
            f"<div><dt>状态缺口</dt><dd>{escape(condition_badge_label)}</dd></div>",
            "</dl>",
            render_live_console_portal_link(live_console),
            "</header>",
            render_workspace_studies_section(workspace_studies),
            '<section class="grid">',
            section(
                "当前状态",
                current_status_paragraphs,
            ),
            section(
                "下一步",
                next_step_paragraphs,
            ),
            runtime_continuity_section(runtime_continuity),
            section(
                "论文与质量",
                paper_paragraphs,
            ),
            section(
                "文件与交付",
                delivery_paragraphs,
            ),
            "</section>",
            list_section("当前阻塞", [display_text(item, fallback='未提供') for item in blockers], empty_text="当前没有投影出的阻塞项。"),
            render_workspace_alerts_section(
                "工作区告警",
                workspace_alert_items,
                empty_text="当前没有 workspace 级告警。",
            ),
            render_workspace_alerts_section(
                "诊断与修复建议",
                suppressed_alert_items,
                empty_text="当前没有被降级的旧/泛化诊断。",
            ),
            event_section(latest_events),
            condition_section(conditions),
            render_section_explanations_section(section_explanations),
            '<details class="refs">',
            f"<summary>数据来源 ({len(source_refs)}/{len(_string_list(payload.get('source_refs')))})</summary>",
            list_html(source_refs, empty_text="当前没有可展示的数据来源。"),
            "</details>",
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def materialize_progress_portal(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    profile_ref: str | Path | None = None,
    progress_payload: Mapping[str, Any] | None = None,
    cockpit_payload: Mapping[str, Any] | None = None,
    runtime_payload: Mapping[str, Any] | None = None,
    package_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    local_timezone: str | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    open_browser: bool = False,
    auto_refresh_seconds: int | None = None,
    live_console_disabled_reason: str | None = None,
) -> dict[str, Any]:
    payload = build_progress_portal_payload(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        profile_ref=profile_ref,
        progress_payload=progress_payload,
        cockpit_payload=cockpit_payload,
        runtime_payload=runtime_payload,
        package_payload=package_payload,
        generated_at=generated_at,
        local_timezone=local_timezone,
        entry_mode=entry_mode,
        sync_runtime_summary=sync_runtime_summary,
        auto_refresh_seconds=auto_refresh_seconds,
        live_console_disabled_reason=live_console_disabled_reason,
    )
    payload_path = profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    hosted_package_path = profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
    html_path = profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_progress_portal_html(payload), encoding="utf-8")
    hosted_package = build_progress_portal_hosted_package(
        profile=profile,
        profile_ref=profile_ref,
        payload=payload,
        payload_path=payload_path,
        html_path=html_path,
        hosted_package_path=hosted_package_path,
    )
    hosted_package_path.write_text(json.dumps(hosted_package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if open_browser:
        webbrowser.open(html_path.as_uri())
    opl_handoff = _materialized_opl_handoff(
        payload.get("opl_handoff"),
        payload_path=payload_path,
        html_path=html_path,
    )
    return {
        "status": "materialized",
        "surface_kind": SURFACE_KIND,
        "payload_path": str(payload_path),
        "html_path": str(html_path),
        "hosted_package_path": str(hosted_package_path),
        "generated_at": payload["generated_at"],
        "opl_handoff": opl_handoff,
        "hosted_package": hosted_package,
    }


def build_progress_portal_hosted_package(
    *,
    profile: WorkspaceProfile,
    payload: Mapping[str, Any],
    payload_path: Path,
    html_path: Path,
    hosted_package_path: Path,
    profile_ref: str | Path | None = None,
) -> dict[str, Any]:
    workspace_root = profile.workspace_root
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": HOSTED_PACKAGE_SURFACE_KIND,
        "owner": "MedAutoScience",
        "packaging_owner": "MedAutoScience",
        "package_role": "optional_hosted_runtime_workspace_truth_package",
        "generated_at": payload.get("generated_at"),
        "read_only": True,
        "default_operation_requires_external_mds": False,
        "default_diagnostic_requires_external_mds": False,
        "mds_webui_dependency_allowed": False,
        "default_webui": "mas_progress_portal",
        "authority": {
            "kind": "hosted_read_model_package",
            "writes_authority_surface": False,
            "forbidden_authority": [
                "study_truth",
                "publication_judgment",
                "quality_verdict",
                "runtime_authority",
                "artifact_authority",
                "controller_decision_authority",
            ],
        },
        "workspace": {
            "profile_name": profile.name,
            "workspace_root": str(workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        "package_refs": {
            "hosted_package": str(hosted_package_path),
            "hosted_package_ref": PROGRESS_PORTAL_HOSTED_PACKAGE_REF,
            "progress_payload": str(payload_path),
            "progress_payload_ref": PROGRESS_PORTAL_PAYLOAD_REF,
            "html": str(html_path),
            "html_ref": PROGRESS_PORTAL_HTML_REF,
            "workspace_relative": {
                "hosted_package": _workspace_relative(hosted_package_path, workspace_root),
                "progress_payload": _workspace_relative(payload_path, workspace_root),
                "html": _workspace_relative(html_path, workspace_root),
            },
        },
        "entrypoints": {
            "static_html": str(html_path),
            "static_html_ref": PROGRESS_PORTAL_HTML_REF,
            "workspace_helper": "ops/mas/bin/start-web",
            "refresh_command": "medautosci workspace progress-portal --profile <profile>",
            "optional_local_read_only_service": "medautosci workspace progress-portal --profile <profile> --serve",
            "live_console_static_html": "ops/mas/live-console/index.html",
            "live_console_read_model_ref": "artifacts/runtime/live_console/session_read_model/latest.json",
            "live_console_service": "medautosci runtime live-console --profile <profile> --serve",
        },
        "hosted_runtime_carrier_contract": {
            "allowed_carriers": [
                "local_read_only_http_server",
                "external_hosted_runtime_static_file_carrier",
                "OPL Runtime Manager family-level projection consumer",
            ],
            "must_consume": [
                PROGRESS_PORTAL_PAYLOAD_REF,
                PROGRESS_PORTAL_HTML_REF,
                "artifacts/runtime/live_console/session_read_model/latest.json",
                "ops/mas/live-console/index.html",
            ],
            "must_not_consume": [
                "MDS WebUI state",
                "external MedDeepScientist runtime root",
                "upstream DeepScientist UI state",
            ],
            "must_not_write": [
                "study_runtime_status",
                "runtime_watch",
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "study_macro_state/latest.json",
                "runtime_lifecycle.sqlite",
                "manuscript/current_package",
            ],
        },
        "source_refs": _string_list(payload.get("source_refs")),
        "source_payloads": _mapping(payload.get("source_payloads")),
        "conditions": _mapping(payload.get("conditions")),
        "opl_handoff": _mapping(payload.get("opl_handoff")),
    }


def serve_progress_portal(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    profile_ref: str | Path | None = None,
    progress_payload: Mapping[str, Any] | None = None,
    cockpit_payload: Mapping[str, Any] | None = None,
    runtime_payload: Mapping[str, Any] | None = None,
    package_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    local_timezone: str | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    host: str = "127.0.0.1",
    port: int = 0,
    interval_seconds: int = 30,
    open_browser: bool = False,
    once: bool = False,
) -> dict[str, Any]:
    refresh_seconds = max(1, int(interval_seconds))

    def refresh() -> dict[str, Any]:
        return materialize_progress_portal(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            profile_ref=profile_ref,
            progress_payload=progress_payload,
            cockpit_payload=cockpit_payload,
            runtime_payload=runtime_payload,
            package_payload=package_payload,
            generated_at=generated_at,
            local_timezone=local_timezone,
            entry_mode=entry_mode,
            sync_runtime_summary=sync_runtime_summary,
            auto_refresh_seconds=refresh_seconds,
        )

    materialized = refresh()
    html_path = Path(str(materialized["html_path"]))
    serve_root = html_path.parent

    class _ProgressPortalHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, directory=str(serve_root), **kwargs)

        def do_GET(self) -> None:  # noqa: N802
            refresh()
            super().do_GET()

        def log_message(self, format: str, *args: Any) -> None:
            return

    server = socketserver.TCPServer((host, int(port)), _ProgressPortalHandler)
    actual_host, actual_port = server.server_address
    url = f"http://{actual_host}:{actual_port}/"
    if open_browser:
        webbrowser.open(url)
    result = {
        "status": "serving",
        "surface_kind": SURFACE_KIND,
        "url": url,
        "host": actual_host,
        "port": actual_port,
        "interval_seconds": refresh_seconds,
        "read_only": True,
        "payload_path": materialized["payload_path"],
        "html_path": materialized["html_path"],
        "hosted_package_path": materialized["hosted_package_path"],
        "generated_at": materialized["generated_at"],
        "opl_handoff": materialized.get("opl_handoff"),
        "hosted_package": materialized.get("hosted_package"),
    }
    if once:
        server.server_close()
        return result
    thread = threading.Thread(target=server.serve_forever, name="mas-progress-portal", daemon=False)
    thread.start()
    return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _valid_user_visible_projection(value: object) -> dict[str, Any]:
    projection = _mapping(value)
    if projection.get("schema_version") != 2:
        return {}
    required = ("writer_state", "user_next", "reason")
    if any(_non_empty_text(projection.get(key)) is None for key in required):
        return {}
    return projection


def _field(payload: Mapping[str, Any], key: str, default: str | None = None) -> str | None:
    return _non_empty_text(payload.get(key)) or default


def _list_field(payload: Mapping[str, Any], key: str) -> list[str]:
    return _string_list(payload.get(key))


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _freshness(value: object) -> dict[str, Any]:
    freshness = _mapping(value)
    status = _non_empty_text(freshness.get("status")) or "missing"
    return {
        "status": status,
        "summary": _non_empty_text(freshness.get("summary")) or "进度新鲜度 surface 缺失。",
        "latest_event_at": _non_empty_text(freshness.get("latest_event_at")),
    }


def _latest_events(user_visible: Mapping[str, Any], progress: Mapping[str, Any]) -> list[dict[str, str]]:
    evidence = _mapping(user_visible.get("evidence"))
    candidates = evidence.get("latest_events")
    if not isinstance(candidates, list):
        candidates = progress.get("latest_events")
    events: list[dict[str, str]] = []
    if isinstance(candidates, list):
        for item in candidates:
            if not isinstance(item, Mapping):
                continue
            summary = _non_empty_text(item.get("summary")) or _non_empty_text(item.get("message"))
            timestamp = _non_empty_text(item.get("timestamp")) or _non_empty_text(item.get("recorded_at"))
            if summary:
                events.append({"timestamp": timestamp or "unknown", "summary": summary})
    return events


def _quality_summary(publication_eval: object) -> dict[str, Any]:
    payload = _mapping(publication_eval)
    verdict = _mapping(payload.get("verdict"))
    assessment = _mapping(payload.get("quality_assessment"))
    checks = []
    for name, item in assessment.items():
        if isinstance(item, Mapping):
            checks.append(
                {
                    "name": str(name),
                    "status": _non_empty_text(item.get("status")) or "unknown",
                    "summary": _non_empty_text(item.get("summary")),
                }
            )
    return {
        "status": _non_empty_text(verdict.get("overall_verdict")) or ("missing" if not payload else "unknown"),
        "summary": _non_empty_text(verdict.get("summary")) or "publication evaluation projection 缺失。",
        "checks": checks,
    }


def _delivery_summary(
    progress: Mapping[str, Any],
    package: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    package_study_id = _non_empty_text(package.get("study_id"))
    if package and (package_study_id is None or package_study_id == study_id):
        return {
            "status": _non_empty_text(package.get("status")) or "unknown",
            "summary": _non_empty_text(package.get("summary")) or "package projection 已存在。",
            "refs": _string_list(package.get("refs")),
        }
    delivery = _mapping(progress.get("delivery_inspection"))
    current_package = _mapping(delivery.get("current_package"))
    if current_package:
        return {
            "status": _non_empty_text(current_package.get("status")) or "unknown",
            "summary": _non_empty_text(current_package.get("summary")) or "current package projection 已存在。",
            "refs": _string_list(current_package.get("refs")),
        }
    return {
        "status": "missing",
        "summary": "current package projection 缺失。",
        "refs": [],
    }


def _supervision(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    supervision = _mapping(progress.get("supervision"))
    tick_audit = _mapping(runtime.get("supervisor_tick_audit"))
    return {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")) or _non_empty_text(runtime.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")) or _non_empty_text(runtime.get("health_status")),
        "supervisor_tick_status": (
            _non_empty_text(tick_audit.get("status"))
            or _non_empty_text(supervision.get("supervisor_tick_status"))
        ),
    }


def _runtime_reconcile_trigger(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    projection = dict(value)
    if projection.get("surface_kind") != "runtime_reconcile_trigger_projection":
        return {}
    projection.setdefault(
        "authority_flags",
        {
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        },
    )
    return projection


def _outer_supervision_slo(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    projection = dict(value)
    if projection.get("surface_kind") != "outer_supervision_slo":
        return {}
    return projection


def _runtime_continuity(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    return runtime_continuity_projection(progress, runtime)


def _conditions(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    user_visible: Mapping[str, Any],
    cockpit: Mapping[str, Any],
    runtime: Mapping[str, Any],
    package: Mapping[str, Any],
    freshness: Mapping[str, Any],
    delivery: Mapping[str, Any],
    runtime_reconcile_trigger: Mapping[str, Any],
    outer_supervision_slo: Mapping[str, Any],
    source_refs: list[str],
) -> dict[str, list[str]]:
    missing: list[str] = []
    stale: list[str] = []
    conflict: list[str] = []
    if not user_visible:
        missing.append("user_visible_projection_v2")
    if not source_refs:
        missing.append("source_refs")
    if freshness.get("status") == "missing":
        missing.append("progress_freshness")
    if freshness.get("status") == "stale":
        stale.append("progress_freshness")
    if runtime_reconcile_trigger.get("safe_to_request") is True:
        stale.append("runtime_reconcile_requestable")
    outer_state = _non_empty_text(outer_supervision_slo.get("state"))
    if outer_state == "missing":
        missing.append("outer_supervision_slo")
    elif outer_state in {"due", "stale"}:
        stale.append(f"outer_supervision_slo_{outer_state}")
    elif outer_state == "blocked":
        conflict.append("outer_supervision_slo_blocked")
    if delivery.get("status") == "missing":
        missing.append("current_package")
    tick_status = _non_empty_text(_mapping(runtime.get("supervisor_tick_audit")).get("status"))
    if tick_status in {"missing", "invalid"}:
        missing.append("runtime_supervisor_tick")
    elif tick_status == "stale":
        stale.append("runtime_supervisor_tick")
    progress_study_id = _non_empty_text(progress.get("study_id"))
    if progress_study_id and progress_study_id != study_id:
        conflict.append("progress_study_id_mismatch")
    cockpit_studies = cockpit.get("studies")
    if isinstance(cockpit_studies, list) and cockpit_studies:
        cockpit_ids = {
            item.get("study_id")
            for item in cockpit_studies
            if isinstance(item, Mapping) and _non_empty_text(item.get("study_id"))
        }
        if study_id not in cockpit_ids:
            conflict.append("cockpit_study_id_mismatch")
    package_study_id = _non_empty_text(package.get("study_id"))
    if package_study_id and package_study_id != study_id:
        conflict.append("package_study_id_mismatch")
    return {
        "missing": missing,
        "stale": stale,
        "conflict": conflict,
    }


def _source_payload_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not payload:
        return {"available": False}
    return {
        "available": True,
        "study_id": _non_empty_text(payload.get("study_id")),
        "generated_at": _non_empty_text(payload.get("generated_at")) or _non_empty_text(payload.get("emitted_at")),
        "status": _non_empty_text(payload.get("status")),
        "surface_kind": _non_empty_text(payload.get("surface_kind")),
    }


def _opl_handoff_projection(
    *,
    study_id: str,
    profile_name: str,
    freshness: Mapping[str, Any],
    source_refs: list[str],
    source_payloads: Mapping[str, Any],
    delivery: Mapping[str, Any],
    conditions: Mapping[str, Any],
    runtime_continuity: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "handoff_kind": "mas_progress_portal_opl_family_projection",
        "owner": "mas",
        "role": "family_level_projection",
        "authority": "display_artifact_only",
        "opl_role": "family_level_projection_consumer_only",
        "study_id": study_id,
        "profile_name": profile_name,
        "payload_refs": {
            "progress_portal": PROGRESS_PORTAL_PAYLOAD_REF,
            "source_payloads": dict(source_payloads),
        },
        "freshness": dict(freshness),
        "source_refs": list(source_refs),
        "artifact_locators": _string_list(delivery.get("refs")),
        "runtime_continuity": _mapping(runtime_continuity),
        "conditions": {
            "missing": _string_list(conditions.get("missing")),
            "stale": _string_list(conditions.get("stale")),
            "conflict": _string_list(conditions.get("conflict")),
        },
        "deep_link": PROGRESS_PORTAL_HTML_REF,
        "forbidden_authority": [
            "study_truth",
            "publication_judgment",
            "quality_verdict",
            "runtime_authority",
            "artifact_authority",
        ],
    }


def _materialized_opl_handoff(
    value: object,
    *,
    payload_path: Path,
    html_path: Path,
) -> dict[str, Any]:
    handoff = _mapping(value)
    handoff["payload_ref"] = str(payload_path)
    handoff["deep_link"] = str(html_path)
    payload_refs = _mapping(handoff.get("payload_refs"))
    payload_refs["progress_portal"] = str(payload_path)
    handoff["payload_refs"] = payload_refs
    return handoff


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError:
        return str(path)


__all__ = [
    "build_progress_portal_payload",
    "build_progress_portal_hosted_package",
    "render_progress_portal_html",
    "materialize_progress_portal",
    "serve_progress_portal",
]
