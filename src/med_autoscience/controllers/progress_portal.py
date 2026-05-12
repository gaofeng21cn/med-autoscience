from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
import socketserver
import threading
from typing import Any
import webbrowser

from med_autoscience.controllers.progress_portal_parts import (
    build_study_workbench_payload,
    live_console_projection,
    local_time_projection,
    progress_section_explanations,
    build_runtime_workbench_projection,
    selected_workspace_study_id,
    source_refs as collect_source_refs,
    study_detail_href,
    workspace_portal_navigation,
    workspace_alert_projection,
    workspace_studies,
)
from med_autoscience.controllers.progress_portal_parts.hosted_package import (
    build_progress_portal_hosted_package as build_hosted_package,
    materialized_opl_handoff,
    workspace_relative,
)
from med_autoscience.controllers.progress_portal_parts.html import (
    render_progress_portal_html as render_progress_portal_html_part,
)
from med_autoscience.controllers.progress_portal_parts.serving import build_progress_portal_handler
from med_autoscience.controllers.production_blocker_impact_projection import (
    build_production_blocker_impact_projection,
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
PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE = "artifacts/runtime/progress_portal/studies/{study_id}/latest.json"
PROGRESS_PORTAL_STUDY_HTML_REF_TEMPLATE = "ops/mas/progress/studies/{study_id}/index.html"


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
    conversation_payload: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    local_timezone: str | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    auto_refresh_seconds: int | None = None,
    live_console_disabled_reason: str | None = None,
    page_scope: str | None = None,
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
    resolved_page_scope = page_scope or ("workspace" if workspace_overview_mode else "study")

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
    if not workspace_overview_mode:
        progress = _progress_with_study_root(
            progress,
            profile=profile,
            study_id=resolved_study_id,
            study_root=study_root,
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
    _attach_study_hrefs(workspace_study_rows, from_study_page=resolved_page_scope == "study")
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
    production_blocker_impact = _production_blocker_impact(
        progress,
        runtime,
        study_id=resolved_study_id,
    )
    study_workbench = (
        build_study_workbench_payload(
            progress,
            cockpit,
            runtime,
            package,
            resolved_study_id,
            conversation_payload=conversation_payload,
        )
        if resolved_page_scope == "study"
        else {}
    )
    live_console = live_console_projection(
        disabled_reason=live_console_disabled_reason,
        study_id=None if workspace_overview_mode else resolved_study_id,
        page_scope=resolved_page_scope,
    )
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
        "navigation": workspace_portal_navigation(
            workspace_study_rows,
            selected_study_id=None if workspace_overview_mode else resolved_study_id,
            page_scope=resolved_page_scope,
        ),
        "portal_paths": {
            "workspace_html_ref": PROGRESS_PORTAL_HTML_REF,
            "study_html_ref": (
                PROGRESS_PORTAL_STUDY_HTML_REF_TEMPLATE.format(study_id=resolved_study_id)
                if not workspace_overview_mode
                else None
            ),
            "workspace_payload_ref": PROGRESS_PORTAL_PAYLOAD_REF,
            "study_payload_ref": (
                PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE.format(study_id=resolved_study_id)
                if not workspace_overview_mode
                else None
            ),
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
            "production_blocker_impact": production_blocker_impact,
        },
        "freshness": freshness,
        "latest_events": latest_events,
        "quality": quality,
        "delivery": delivery,
        "study_workbench": study_workbench,
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
            production_blocker_impact=production_blocker_impact,
            page_scope=resolved_page_scope,
        ),
    }
    payload["mas_opl_runtime_workbench_projection"] = build_runtime_workbench_projection(
        workspace_root=resolved_workspace_root,
        profile_ref=profile_ref,
        profile_name=resolved_profile_name,
        generated_at=resolved_generated_at,
        study_id=resolved_study_id,
        workspace_overview_mode=workspace_overview_mode,
        page_scope=resolved_page_scope,
        workspace_study_rows=workspace_study_rows,
        user_visible=user_visible,
        progress=progress,
        runtime=runtime,
        freshness=freshness,
        source_refs=source_refs,
        conditions=conditions,
        study_workbench=study_workbench,
        live_console=live_console,
    )
    if auto_refresh_seconds is not None and auto_refresh_seconds > 0:
        payload["portal_view"] = {
            "auto_refresh_seconds": int(auto_refresh_seconds),
            "refresh_mode": "read_only_server_request_refresh",
        }
    return payload


def _attach_study_hrefs(studies: list[dict[str, Any]], *, from_study_page: bool) -> None:
    for item in studies:
        study_id = _non_empty_text(item.get("study_id"))
        if study_id is None:
            continue
        item["portal_href"] = study_detail_href(study_id, from_study_page=from_study_page)


def _ensure_workspace_has_selected_study(workspace_payload: dict[str, Any], detail_payload: Mapping[str, Any]) -> None:
    detail_study = _mapping(detail_payload.get("study"))
    study_id = _non_empty_text(detail_study.get("study_id"))
    if study_id is None:
        return
    workspace = _mapping(workspace_payload.get("workspace"))
    studies = _mapping_list(workspace.get("studies"))
    if any(_non_empty_text(item.get("study_id")) == study_id for item in studies):
        return
    studies.append(
        {
            "study_id": study_id,
            "selected": False,
            "state_label": detail_study.get("state_label"),
            "state_summary": detail_study.get("state_summary"),
            "current_stage": detail_study.get("current_stage"),
            "paper_stage": detail_study.get("paper_stage"),
            "active_run_id": _mapping(detail_study.get("supervision")).get("active_run_id"),
            "runtime_health_status": _mapping(detail_study.get("supervision")).get("health_status"),
            "supervisor_tick_status": _mapping(detail_study.get("supervision")).get("supervisor_tick_status"),
            "progress_freshness_status": _mapping(detail_payload.get("freshness")).get("status"),
            "operator_focus": detail_study.get("next_system_action"),
            "next_system_action": detail_study.get("next_system_action"),
            "portal_href": study_detail_href(study_id),
        }
    )
    workspace["studies"] = studies
    workspace_payload["workspace"] = workspace
    workspace_payload["navigation"] = workspace_portal_navigation(
        studies,
        selected_study_id=None,
        page_scope="workspace",
    )


def _materialize_study_pages(
    *,
    profile: WorkspaceProfile,
    workspace_payload: Mapping[str, Any],
    selected_payload: Mapping[str, Any] | None,
    profile_ref: str | Path | None,
    generated_at: str | None,
    local_timezone: str | None,
    auto_refresh_seconds: int | None,
    live_console_disabled_reason: str | None,
) -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    workspace = _mapping(workspace_payload.get("workspace"))
    cockpit_for_pages = _cockpit_from_workspace_payload(workspace_payload)
    for study in _mapping_list(workspace.get("studies")):
        study_id = _non_empty_text(study.get("study_id"))
        if study_id is None:
            continue
        if selected_payload is not None and _non_empty_text(_mapping(selected_payload.get("study")).get("study_id")) == study_id:
            payload = dict(selected_payload)
        else:
            progress = _study_progress_payload_for_materialized_page(
                profile=profile,
                study_id=study_id,
                profile_ref=profile_ref,
            )
            payload = build_progress_portal_payload(
                profile=profile,
                study_id=study_id,
                profile_ref=profile_ref,
                progress_payload=progress or _progress_from_workspace_study_row(study),
                cockpit_payload=cockpit_for_pages,
                conversation_payload=_conversation_read_model_payload(
                    profile=profile,
                    profile_ref=profile_ref,
                    study_id=study_id,
                    generated_at=generated_at,
                ),
                generated_at=generated_at,
                local_timezone=local_timezone,
                sync_runtime_summary=False,
                auto_refresh_seconds=auto_refresh_seconds,
                live_console_disabled_reason=live_console_disabled_reason,
                page_scope="study",
            )
        html_path = profile.workspace_root / "ops" / "mas" / "progress" / "studies" / study_id / "index.html"
        payload_path = (
            profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "studies" / study_id / "latest.json"
        )
        html_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        html_path.write_text(render_progress_portal_html(payload), encoding="utf-8")
        pages[study_id] = {
            "study_id": study_id,
            "payload_path": str(payload_path),
            "html_path": str(html_path),
            "payload_ref": workspace_relative(payload_path, profile.workspace_root),
            "html_ref": workspace_relative(html_path, profile.workspace_root),
            "opl_handoff": materialized_opl_handoff(
                payload.get("opl_handoff"),
                payload_path=payload_path,
                html_path=html_path,
            ),
        }
    return pages


def _study_progress_payload_for_materialized_page(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    profile_ref: str | Path | None,
) -> dict[str, Any]:
    study_root = (profile.studies_root / study_id).expanduser().resolve()
    if not (study_root / "study.yaml").is_file():
        return {}
    from med_autoscience.controllers import study_progress

    return study_progress.read_study_progress(
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        sync_runtime_summary=False,
    )


def _cockpit_from_workspace_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    workspace = _mapping(payload.get("workspace"))
    return {
        "workspace_status": workspace.get("workspace_status"),
        "workspace_alerts": _string_list(workspace.get("workspace_alerts")),
        "studies": _mapping_list(workspace.get("studies")),
    }


def _progress_from_workspace_study_row(study: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _non_empty_text(study.get("study_id")) or "unknown-study"
    state_label = _non_empty_text(study.get("state_label")) or "状态投影缺失"
    state_summary = _non_empty_text(study.get("state_summary")) or "该论文线缺少 canonical study-progress projection。"
    return {
        "study_id": study_id,
        "user_visible_projection": {
            "schema_version": 2,
            "state_label": state_label,
            "state_summary": state_summary,
            "current_stage": _non_empty_text(study.get("current_stage")),
            "paper_stage": _non_empty_text(study.get("paper_stage")),
            "next_system_action": _non_empty_text(study.get("next_system_action"))
            or _non_empty_text(study.get("operator_focus"))
            or "刷新 canonical study-progress projection。",
            "current_blockers": [],
            "needs_physician_decision": False,
        },
        "progress_freshness": {
            "status": _non_empty_text(study.get("progress_freshness_status")) or "missing",
            "summary": _non_empty_text(study.get("progress_freshness_summary")) or "progress freshness projection 缺失。",
        },
        "supervision": {
            "active_run_id": _non_empty_text(study.get("active_run_id")),
            "health_status": _non_empty_text(study.get("runtime_health_status")),
            "supervisor_tick_status": _non_empty_text(study.get("supervisor_tick_status")),
        },
        "refs": {},
    }


def _progress_with_study_root(
    progress: Mapping[str, Any],
    *,
    profile: WorkspaceProfile | None,
    study_id: str | None,
    study_root: Path | None,
) -> dict[str, Any]:
    resolved = dict(progress)
    if _non_empty_text(resolved.get("study_root")) is not None:
        return resolved
    root = study_root
    if root is None and profile is not None and _non_empty_text(study_id) is not None:
        root = profile.studies_root / str(study_id)
    if root is None:
        return resolved
    resolved["study_root"] = str(root.expanduser().resolve())
    refs = _mapping(resolved.get("refs"))
    refs.setdefault("study_root", resolved["study_root"])
    resolved["refs"] = refs
    return resolved


def render_progress_portal_html(payload: Mapping[str, Any]) -> str:
    return render_progress_portal_html_part(payload, brand_fallback=BRAND)

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
    selected_study_id = _non_empty_text(study_id) or (study_root.name if study_root is not None else None)
    detail_payload = None
    if selected_study_id is not None or progress_payload is not None or study_root is not None:
        detail_payload = build_progress_portal_payload(
            profile=profile,
            study_id=selected_study_id,
            study_root=study_root,
            profile_ref=profile_ref,
            progress_payload=progress_payload,
            cockpit_payload=cockpit_payload,
            runtime_payload=runtime_payload,
            package_payload=package_payload,
            conversation_payload=_conversation_read_model_payload(
                profile=profile,
                profile_ref=profile_ref,
                study_id=selected_study_id,
                study_root=study_root,
                generated_at=generated_at,
            ),
            generated_at=generated_at,
            local_timezone=local_timezone,
            entry_mode=entry_mode,
            sync_runtime_summary=sync_runtime_summary,
            auto_refresh_seconds=auto_refresh_seconds,
            live_console_disabled_reason=live_console_disabled_reason,
            page_scope="study",
        )
        selected_study_id = str(_mapping(detail_payload.get("study")).get("study_id") or selected_study_id)

    payload = build_progress_portal_payload(
        profile=profile,
        study_id=None,
        study_root=None,
        profile_ref=profile_ref,
        progress_payload=None,
        cockpit_payload=cockpit_payload,
        runtime_payload=None,
        package_payload=None,
        generated_at=generated_at,
        local_timezone=local_timezone,
        entry_mode=entry_mode,
        sync_runtime_summary=sync_runtime_summary,
        auto_refresh_seconds=auto_refresh_seconds,
        live_console_disabled_reason=live_console_disabled_reason,
        page_scope="workspace",
    )
    if detail_payload is not None:
        _ensure_workspace_has_selected_study(payload, detail_payload)
    payload_path = profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    hosted_package_path = profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
    html_path = profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_progress_portal_html(payload), encoding="utf-8")
    study_pages = _materialize_study_pages(
        profile=profile,
        workspace_payload=payload,
        selected_payload=detail_payload,
        profile_ref=profile_ref,
        generated_at=generated_at,
        local_timezone=local_timezone,
        auto_refresh_seconds=auto_refresh_seconds,
        live_console_disabled_reason=live_console_disabled_reason,
    )
    selected_page = study_pages.get(selected_study_id or "") if selected_study_id is not None else None
    hosted_package = build_progress_portal_hosted_package(
        profile=profile,
        profile_ref=profile_ref,
        payload=payload,
        payload_path=payload_path,
        html_path=html_path,
        hosted_package_path=hosted_package_path,
        study_pages=study_pages,
    )
    hosted_package_path.write_text(json.dumps(hosted_package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if open_browser:
        webbrowser.open(Path(selected_page["html_path"]).as_uri() if selected_page else html_path.as_uri())
    opl_handoff = materialized_opl_handoff(
        (selected_page or {}).get("opl_handoff") if selected_page else payload.get("opl_handoff"),
        payload_path=Path(str(selected_page["payload_path"])) if selected_page else payload_path,
        html_path=Path(str(selected_page["html_path"])) if selected_page else html_path,
    )
    return {
        "status": "materialized",
        "surface_kind": SURFACE_KIND,
        "payload_path": str(payload_path),
        "html_path": str(selected_page["html_path"]) if selected_page else str(html_path),
        "workspace_html_path": str(html_path),
        "hosted_package_path": str(hosted_package_path),
        "study_pages": study_pages,
        "selected_study_id": selected_study_id,
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
    study_pages: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    return build_hosted_package(
        profile=profile,
        payload=payload,
        payload_path=payload_path,
        html_path=html_path,
        hosted_package_path=hosted_package_path,
        refs={
            "progress_payload": PROGRESS_PORTAL_PAYLOAD_REF,
            "progress_html": PROGRESS_PORTAL_HTML_REF,
            "hosted_package": PROGRESS_PORTAL_HOSTED_PACKAGE_REF,
        },
        surface_kind=HOSTED_PACKAGE_SURFACE_KIND,
        profile_ref=profile_ref,
        study_pages=study_pages,
    )


def _conversation_read_model_payload(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_id: str | None,
    generated_at: str | None,
    study_root: Path | None = None,
) -> dict[str, Any]:
    from med_autoscience.controllers import runtime_live_console

    return runtime_live_console.build_conversation_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        generated_at=generated_at,
    )


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
    enable_actions: bool = False,
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

    handler = build_progress_portal_handler(
        serve_root=serve_root,
        refresh=refresh,
        profile=profile,
        study_id=study_id,
        enable_actions=enable_actions,
    )

    server = socketserver.TCPServer((host, int(port)), handler)
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
        "actions_enabled": bool(enable_actions),
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


def _production_blocker_impact(
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    return build_production_blocker_impact_projection(progress, runtime, study_id=study_id)


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
    production_blocker_impact: Mapping[str, Any],
    page_scope: str,
) -> dict[str, Any]:
    return {
        "handoff_kind": "mas_progress_portal_opl_family_projection",
        "owner": "mas",
        "role": "family_level_projection",
        "authority": "display_artifact_only",
        "opl_role": "family_level_projection_consumer_only",
        "study_id": study_id,
        "page_scope": page_scope,
        "profile_name": profile_name,
        "payload_refs": {
            "progress_portal": PROGRESS_PORTAL_PAYLOAD_REF,
            "source_payloads": dict(source_payloads),
        },
        "freshness": dict(freshness),
        "source_refs": list(source_refs),
        "artifact_locators": _string_list(delivery.get("refs")),
        "runtime_continuity": _mapping(runtime_continuity),
        "production_blocker_impact": _mapping(production_blocker_impact),
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


__all__ = [
    "build_progress_portal_payload",
    "build_progress_portal_hosted_package",
    "render_progress_portal_html",
    "materialize_progress_portal",
    "serve_progress_portal",
]
