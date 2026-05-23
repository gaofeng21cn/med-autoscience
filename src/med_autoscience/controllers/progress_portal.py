from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
import socketserver
import threading
from typing import Any
import webbrowser

from med_autoscience.controllers.progress_portal_parts import (
    build_study_workbench_payload,
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
from med_autoscience.controllers.progress_portal_parts.payload_helpers import (
    _conditions,
    _delivery_summary,
    _field,
    _freshness,
    _latest_events,
    _list_field,
    _mapping,
    _mapping_list,
    _non_empty_text,
    _opl_handoff_projection,
    _outer_supervision_slo,
    _production_blocker_impact,
    _quality_summary,
    _runtime_continuity,
    _source_payload_summary,
    _string_list,
    _supervision,
    _utc_now,
    _valid_user_visible_projection,
)
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
    generated_at: str | None = None,
    local_timezone: str | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    auto_refresh_seconds: int | None = None,
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
    progress = _progress_with_study_root_for_portal(
        progress,
        workspace_overview_mode=workspace_overview_mode,
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
        )
        if resolved_page_scope == "study"
        else {}
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
            "outer_supervision_slo": outer_supervision_slo or None,
            "runtime_continuity": runtime_continuity,
            "production_blocker_impact": production_blocker_impact,
        },
        "freshness": freshness,
        "latest_events": latest_events,
        "quality": quality,
        "delivery": delivery,
        "study_workbench": study_workbench,
        "conditions": conditions,
        "section_explanations": progress_section_explanations(
            workspace_overview_mode=workspace_overview_mode,
            has_workspace_studies=has_workspace_studies,
            has_workspace_alerts=has_workspace_alerts,
            has_diagnostics=has_diagnostics,
            has_latest_events=has_latest_events,
            has_source_refs=has_source_refs,
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
                generated_at=generated_at,
                local_timezone=local_timezone,
                sync_runtime_summary=False,
                auto_refresh_seconds=auto_refresh_seconds,
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

    try:
        return study_progress.read_study_progress(
            profile=profile,
            profile_ref=profile_ref,
            study_id=study_id,
            study_root=study_root,
            sync_runtime_summary=False,
        )
    except Exception as exc:
        return _progress_projection_error_payload(
            study_id=study_id,
            study_root=study_root,
            error=exc,
        )


def _progress_projection_error_payload(
    *,
    study_id: str,
    study_root: Path,
    error: Exception,
) -> dict[str, Any]:
    message = str(error) or error.__class__.__name__
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "user_visible_projection": {
            "schema_version": 2,
            "writer_state": "blocked",
            "user_next": "wait",
            "reason": "study_progress_projection_error",
            "state_label": "进度投影异常",
            "state_summary": "该 study 的进度投影读取失败；Portal 仅显示阻塞状态，其他 study 页面继续生成。",
            "current_stage": "projection_blocked",
            "current_stage_summary": "Study progress projection failed during portal materialization.",
            "paper_stage": "projection_blocked",
            "paper_stage_summary": "论文线状态需要先修复 canonical progress projection。",
            "current_blockers": [f"{study_id} study progress projection failed: {message}"],
            "next_system_action": "Inspect and repair the study progress projection contract before routing this study.",
            "needs_physician_decision": False,
        },
        "progress_freshness": {
            "status": "invalid",
            "summary": f"study progress projection failed: {message}",
        },
        "supervision": {
            "active_run_id": None,
            "health_status": "blocked",
            "supervisor_tick_status": "unknown",
        },
        "intervention_lane": {
            "lane_id": "study_projection_error",
            "title": "Repair study progress projection",
            "severity": "critical",
            "summary": f"study progress projection failed: {message}",
            "recommended_action_id": "inspect_study_progress_projection",
        },
        "projection_error": {
            "error_type": error.__class__.__name__,
            "message": message,
            "handled_as": "study_progress_projection_error",
            "study_root": str(study_root),
        },
        "refs": {"study_root": str(study_root)},
    }


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
    current_stage = _non_empty_text(study.get("current_stage"))
    paper_stage = _non_empty_text(study.get("paper_stage"))
    next_system_action = (
        _non_empty_text(study.get("next_system_action"))
        or _non_empty_text(study.get("operator_focus"))
        or "刷新 canonical study-progress projection。"
    )
    current_blockers = _string_list(study.get("current_blockers"))
    return {
        "study_id": study_id,
        "user_visible_projection": {
            "schema_version": 2,
            "writer_state": "blocked" if current_stage == "projection_blocked" else "unknown",
            "user_next": "wait",
            "reason": "study_progress_projection_error" if current_stage == "projection_blocked" else "workspace_study_row_projection",
            "state_label": state_label,
            "state_summary": state_summary,
            "current_stage": current_stage,
            "paper_stage": paper_stage,
            "next_system_action": next_system_action,
            "current_blockers": current_blockers,
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
        "projection_error": _mapping(study.get("projection_error")),
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


def _progress_with_study_root_for_portal(
    progress: Mapping[str, Any],
    *,
    workspace_overview_mode: bool,
    profile: WorkspaceProfile | None,
    study_id: str | None,
    study_root: Path | None,
) -> dict[str, Any]:
    if workspace_overview_mode:
        return dict(progress)
    return _progress_with_study_root(
        progress,
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )


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
            generated_at=generated_at,
            local_timezone=local_timezone,
            entry_mode=entry_mode,
            sync_runtime_summary=sync_runtime_summary,
            auto_refresh_seconds=auto_refresh_seconds,
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


__all__ = [
    "build_progress_portal_payload",
    "build_progress_portal_hosted_package",
    "render_progress_portal_html",
    "materialize_progress_portal",
    "serve_progress_portal",
]
