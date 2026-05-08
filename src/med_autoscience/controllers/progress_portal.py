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
    dedupe_texts,
    local_time_projection,
    render_workspace_studies_section,
    unique_text,
    workspace_alert_projection,
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
) -> dict[str, Any]:
    resolved_profile_name = profile_name or (profile.name if profile is not None else None) or "unknown"
    resolved_workspace_root = Path(
        workspace_root if workspace_root is not None else (profile.workspace_root if profile is not None else ".")
    )
    resolved_study_id = _non_empty_text(study_id)

    progress = dict(progress_payload or {})
    if not progress:
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
    resolved_study_id = resolved_study_id or _non_empty_text(progress.get("study_id")) or "unknown-study"

    cockpit = dict(cockpit_payload or {})
    if not cockpit and profile is not None and progress_payload is None:
        from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_payload import (
            read_workspace_cockpit,
        )

        cockpit = read_workspace_cockpit(profile=profile, profile_ref=profile_ref)

    runtime = dict(runtime_payload or {})
    package = dict(package_payload or {})
    user_visible = _valid_user_visible_projection(progress.get("user_visible_projection"))
    freshness = _freshness(progress.get("progress_freshness"))
    latest_events = _latest_events(user_visible, progress)
    quality = _quality_summary(progress.get("publication_eval"))
    delivery = _delivery_summary(progress, package, study_id=resolved_study_id)
    runtime_reconcile_trigger = _runtime_reconcile_trigger(progress.get("runtime_reconcile_trigger"))
    workspace_study_rows = workspace_studies(cockpit, selected_study_id=resolved_study_id)
    workspace_alerts = workspace_alert_projection(
        cockpit.get("workspace_alerts"),
        workspace_studies=workspace_study_rows,
    )
    source_refs = _source_refs(progress, cockpit, runtime, package)
    source_payloads = {
        "progress": _source_payload_summary(progress),
        "cockpit": _source_payload_summary(cockpit),
        "runtime": _source_payload_summary(runtime),
        "package": _source_payload_summary(package),
    }
    runtime_continuity = _runtime_continuity(progress, runtime)
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
            "studies": workspace_study_rows,
            "diagnostics": {
                "suppressed_alerts": workspace_alerts["suppressed"],
                "suppressed_alert_policy": "legacy_runtime_or_inactive_study_noise",
            },
        },
        "study": {
            "study_id": resolved_study_id,
            "state_label": _field(user_visible, "state_label", "状态投影缺失"),
            "state_summary": _field(user_visible, "state_summary", "当前缺少可展示的用户状态投影。"),
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
            "runtime_continuity": runtime_continuity,
        },
        "freshness": freshness,
        "latest_events": latest_events,
        "quality": quality,
        "delivery": delivery,
        "conditions": conditions,
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
    conditions = _mapping(payload.get("conditions"))
    runtime_continuity = _mapping(study.get("runtime_continuity"))
    latest_events = [dict(item) for item in payload.get("latest_events") or [] if isinstance(item, Mapping)]
    source_refs = _display_source_refs(payload.get("source_refs"))
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
    condition_badge = _condition_badge(conditions)
    blockers = _string_list(study.get("current_blockers"))
    workspace_alerts = _string_list(workspace.get("workspace_alerts"))
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
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            _refresh_meta(auto_refresh_seconds),
            f"<title>{escape(brand)} Progress Portal</title>",
            "<style>",
            _css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="portal">',
            '<header class="masthead">',
            f'<div class="brand">{escape(brand)}</div>',
            f"<h1>{escape(workspace_title)}</h1>",
            f'<p class="state">{escape(state_label)}</p>',
            '<dl class="meta">',
            f"<div><dt>generated_at local</dt><dd>{escape(generated_at_local_label)}</dd></div>",
            f"<div><dt>generated_at UTC</dt><dd>{escape(generated_at)}</dd></div>",
            f"<div><dt>freshness</dt><dd>{escape(str(freshness.get('status') or 'unknown'))}</dd></div>",
            f"<div><dt>workspace</dt><dd>{escape(str(workspace.get('profile_name') or 'unknown'))}</dd></div>",
            f"<div><dt>selected study</dt><dd>{escape(selected_study_id)}</dd></div>",
            f"<div><dt>conditions</dt><dd>{escape(condition_badge)}</dd></div>",
            "</dl>",
            "</header>",
            render_workspace_studies_section(workspace_studies),
            '<section class="grid">',
            _section(
                "当前状态",
                current_status_paragraphs,
            ),
            _section(
                "下一步",
                [
                    str(study.get("next_system_action") or "等待 MAS 重新生成下一步投影。"),
                    _gate_text(study),
                ],
            ),
            _runtime_continuity_section(runtime_continuity),
            _section(
                "论文与质量",
                paper_paragraphs,
            ),
            _section(
                "文件与交付",
                [
                    str(delivery.get("summary") or "交付投影缺失。"),
                    str(delivery.get("status") or "unknown"),
                ],
            ),
            "</section>",
            _list_section("当前阻塞", blockers, empty_text="当前没有投影出的阻塞项。"),
            _list_section("Workspace Alerts", workspace_alerts, empty_text="当前没有 workspace alert。"),
            _event_section(latest_events),
            _condition_section(conditions),
            '<details class="refs">',
            f"<summary>source refs ({len(source_refs)}/{len(_string_list(payload.get('source_refs')))})</summary>",
            _list_html(source_refs, empty_text="No source refs were available."),
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
        "summary": _non_empty_text(freshness.get("summary")) or "progress freshness surface is missing.",
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
        "summary": _non_empty_text(verdict.get("summary")) or "publication evaluation projection is missing.",
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
            "summary": _non_empty_text(package.get("summary")) or "package projection is available.",
            "refs": _string_list(package.get("refs")),
        }
    delivery = _mapping(progress.get("delivery_inspection"))
    current_package = _mapping(delivery.get("current_package"))
    if current_package:
        return {
            "status": _non_empty_text(current_package.get("status")) or "unknown",
            "summary": _non_empty_text(current_package.get("summary")) or "current package projection is available.",
            "refs": _string_list(current_package.get("refs")),
        }
    return {
        "status": "missing",
        "summary": "current package projection is missing.",
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


def _runtime_continuity(progress: Mapping[str, Any], runtime: Mapping[str, Any]) -> dict[str, Any]:
    return runtime_continuity_projection(progress, runtime)


def _source_refs(*payloads: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for payload in payloads:
        refs.extend(_refs_from(payload))
    return sorted(dict.fromkeys(refs))


def _refs_from(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        if _looks_like_ref(value):
            refs.append(value)
        return refs
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).endswith("refs") or str(key) in {"refs", "evidence_refs", "source_refs"}:
                refs.extend(_refs_from_ref_field(item))
            elif str(key).endswith("ref") or str(key).endswith("path"):
                refs.extend(_refs_from_ref_field(item))
            elif isinstance(item, (Mapping, list, tuple)):
                refs.extend(_refs_from(item))
        return refs
    if isinstance(value, list | tuple):
        for item in value:
            refs.extend(_refs_from(item))
    return refs


def _refs_from_ref_field(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_refs_from_ref_field(item))
        return result
    if isinstance(value, list | tuple):
        result: list[str] = []
        for item in value:
            result.extend(_refs_from_ref_field(item))
        return result
    return []


def _looks_like_ref(value: str) -> bool:
    return "/" in value or value.endswith(".json") or value.endswith(".yaml")


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


def _display_source_refs(value: object) -> list[str]:
    refs = _string_list(value)
    priority_tokens = (
        "/artifacts/runtime/health/",
        "/artifacts/runtime/runtime_supervision/",
        "/artifacts/controller_decisions/",
        "/artifacts/publication_eval/",
        "/artifacts/truth/",
        "/artifacts/runtime/progress_portal/",
        "/artifacts/supervision/hourly/",
        "/runtime/quests/",
    )
    blocked_tokens = (
        "/ops/med-deepscientist/",
        "med-deepscientist",
        ".ds/worktrees",
    )
    selected: list[str] = []
    for ref in refs:
        if any(token in ref for token in blocked_tokens):
            continue
        if any(token in ref for token in priority_tokens):
            selected.append(ref)
        if len(selected) >= 24:
            break
    return selected


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


def _condition_badge(conditions: Mapping[str, Any]) -> str:
    labels = []
    for key in ("missing", "stale", "conflict"):
        values = _string_list(conditions.get(key))
        if values:
            labels.append(f"{key}:{len(values)}")
    return ", ".join(labels) if labels else "clear"


def _gate_text(study: Mapping[str, Any]) -> str:
    if bool(study.get("needs_physician_decision")):
        return "需要医生/PI 确认后继续。"
    return "当前没有投影出的医生/PI gate。"


def _runtime_continuity_section(runtime_continuity: Mapping[str, Any]) -> str:
    session = _mapping(runtime_continuity.get("runtime_session"))
    intent = _mapping(runtime_continuity.get("recovery_intent"))
    items = []
    if session:
        items.append(f"worker: {session.get('worker_state') or 'unknown'}")
        if session.get("active_run_id"):
            items.append(f"active run: {session.get('active_run_id')}")
        elif session.get("last_known_run_id"):
            items.append(f"last known run: {session.get('last_known_run_id')}")
        if session.get("last_seen_at"):
            items.append(f"last seen: {session.get('last_seen_at')}")
        if session.get("freshness_state"):
            items.append(f"freshness: {session.get('freshness_state')}")
    if intent:
        items.append(f"recovery action: {intent.get('current_action') or 'unknown'}")
        if intent.get("next_owner"):
            items.append(f"next owner: {intent.get('next_owner')}")
        if intent.get("next_eligible_tick"):
            items.append(f"next eligible tick: {intent.get('next_eligible_tick')}")
    return _list_section("Runtime Continuity", items, empty_text="当前没有 runtime session / recovery intent 投影。")


def _section(title: str, paragraphs: list[str]) -> str:
    body = "".join(f"<p>{escape(text)}</p>" for text in dedupe_texts(paragraphs) if text)
    return f'<section class="panel"><h2>{escape(title)}</h2>{body}</section>'


def _list_section(title: str, items: list[str], *, empty_text: str) -> str:
    return f'<section class="panel wide"><h2>{escape(title)}</h2>{_list_html(items, empty_text=empty_text)}</section>'


def _event_section(events: list[dict[str, str]]) -> str:
    if not events:
        return _list_section("最近进展", [], empty_text="当前没有带时间戳的进展事件。")
    items = [f"{item.get('timestamp') or 'unknown'} - {item.get('summary') or ''}" for item in events]
    return _list_section("最近进展", items, empty_text="当前没有带时间戳的进展事件。")


def _condition_section(conditions: Mapping[str, Any]) -> str:
    items = []
    for key in ("missing", "stale", "conflict"):
        for value in _string_list(conditions.get(key)):
            items.append(f"{key}: {value}")
    return _list_section("stale / missing / conflict", items, empty_text="No stale, missing, or conflict conditions.")


def _list_html(items: list[str], *, empty_text: str) -> str:
    if not items:
        return f"<p>{escape(empty_text)}</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _css() -> str:
    return """
:root { color-scheme: light; --ink:#172026; --muted:#5d6972; --line:#d8dee4; --accent:#0f766e; --warn:#b45309; --bad:#b91c1c; --bg:#f7f9fb; --panel:#ffffff; }
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }
.portal { max-width: 1160px; margin: 0 auto; padding: 28px; }
.masthead { border-bottom: 1px solid var(--line); padding: 8px 0 22px; }
.brand { color: var(--accent); font-weight: 700; letter-spacing: 0; }
h1 { margin: 8px 0 4px; font-size: 32px; line-height: 1.15; }
h2 { margin: 0 0 10px; font-size: 17px; }
p { margin: 0 0 10px; line-height: 1.5; }
.state { color: var(--muted); font-size: 18px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 18px 0 0; }
.meta div { border: 1px solid var(--line); background: var(--panel); padding: 10px 12px; border-radius: 8px; }
dt { color: var(--muted); font-size: 12px; text-transform: uppercase; }
dd { margin: 3px 0 0; font-weight: 600; overflow-wrap: anywhere; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 18px 0 14px; }
.panel, .refs { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
.wide { margin-top: 14px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.study-row.selected td { background: #eef8f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; overflow-wrap: anywhere; }
summary { cursor: pointer; font-weight: 700; }
.refs { margin-top: 14px; }
@media (max-width: 760px) { .portal { padding: 18px; } .grid { grid-template-columns: 1fr; } h1 { font-size: 26px; } }
""".strip()


def _refresh_meta(value: object) -> str:
    if isinstance(value, int) and value > 0:
        return f'<meta http-equiv="refresh" content="{value}">'
    return ""


__all__ = [
    "build_progress_portal_payload",
    "build_progress_portal_hosted_package",
    "render_progress_portal_html",
    "materialize_progress_portal",
    "serve_progress_portal",
]
