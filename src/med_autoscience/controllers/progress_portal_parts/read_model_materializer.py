from __future__ import annotations

from collections.abc import Callable, Mapping
import json
from pathlib import Path
from typing import Any
import webbrowser

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile

from .hosted_package import (
    build_progress_portal_hosted_package as build_hosted_package,
    materialized_opl_handoff,
    workspace_relative,
)
from .payload_helpers import _mapping, _mapping_list, _non_empty_text, _string_list
from .workspace_overview import study_detail_href, workspace_portal_navigation


PROGRESS_PORTAL_PAYLOAD_REF = "runtime/artifacts/progress_portal/latest.json"
PROGRESS_PORTAL_HTML_REF = "ops/mas/progress/index.html"
PROGRESS_PORTAL_HOSTED_PACKAGE_REF = "runtime/artifacts/progress_portal/hosted_package.json"
PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE = "runtime/artifacts/progress_portal/studies/{study_id}/latest.json"
PROGRESS_PORTAL_STUDY_HTML_REF_TEMPLATE = "ops/mas/progress/studies/{study_id}/index.html"

PayloadBuilder = Callable[..., dict[str, Any]]
HtmlRenderer = Callable[[Mapping[str, Any]], str]


def build_progress_portal_hosted_package(
    *,
    profile: WorkspaceProfile,
    payload: Mapping[str, Any],
    payload_path: Path,
    html_path: Path,
    hosted_package_path: Path,
    hosted_package_surface_kind: str,
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
        surface_kind=hosted_package_surface_kind,
        profile_ref=profile_ref,
        study_pages=study_pages,
    )


def materialize_progress_portal(
    *,
    profile: WorkspaceProfile,
    build_payload: PayloadBuilder,
    render_html: HtmlRenderer,
    surface_kind: str,
    hosted_package_surface_kind: str,
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
        detail_payload = build_payload(
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

    payload = build_payload(
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
    layout = build_workspace_runtime_layout_for_profile(profile)
    payload_path = layout.runtime_artifacts_root / "progress_portal" / "latest.json"
    hosted_package_path = layout.runtime_artifacts_root / "progress_portal" / "hosted_package.json"
    html_path = profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    payload_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.parent.mkdir(parents=True, exist_ok=True)
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    html_path.write_text(render_html(payload), encoding="utf-8")
    study_pages = _materialize_study_pages(
        profile=profile,
        build_payload=build_payload,
        render_html=render_html,
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
        hosted_package_surface_kind=hosted_package_surface_kind,
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
        "surface_kind": surface_kind,
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


def _ensure_workspace_has_selected_study(workspace_payload: dict[str, Any], detail_payload: Mapping[str, Any]) -> None:
    detail_study = _mapping(detail_payload.get("study"))
    study_id = _non_empty_text(detail_study.get("study_id"))
    if study_id is None:
        return
    detail_workbench = _mapping(detail_payload.get("study_workbench"))
    detail_overview = _mapping(detail_workbench.get("overview"))
    owner_delta_summary = _mapping(detail_workbench.get("owner_delta_summary"))
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
            "operator_focus": owner_delta_summary.get("summary"),
            "current_owner_delta": detail_workbench.get("current_owner_delta"),
            "legacy_next_system_action_diagnostic": detail_overview.get("legacy_next_system_action_diagnostic"),
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
    build_payload: PayloadBuilder,
    render_html: HtmlRenderer,
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
            payload = build_payload(
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
            build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
            / "progress_portal"
            / "studies"
            / study_id
            / "latest.json"
        )
        html_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        html_path.write_text(render_html(payload), encoding="utf-8")
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
            "next_system_action_role": "diagnostic_projection_error_label",
            "authority": False,
            "can_generate_action": False,
            "can_execute": False,
            "needs_user_decision": False,
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
            "recommended_action_role": "diagnostic_projection_error_label",
            "diagnostic_only": True,
            "authority": False,
            "can_generate_action": False,
            "can_execute": False,
        },
        "projection_error": {
            "error_type": error.__class__.__name__,
            "message": message,
            "handled_as": "study_progress_projection_error",
            "study_root": str(study_root),
            "diagnostic_only": True,
            "authority": False,
            "can_generate_action": False,
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
    owner_delta_summary = _mapping(study.get("owner_delta_summary"))
    legacy_next_action = _mapping(study.get("legacy_next_system_action_diagnostic"))
    next_system_action = (
        _non_empty_text(owner_delta_summary.get("summary"))
        or "等待 OPL/current_owner_delta readback 生成只读下一步摘要。"
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
            "next_system_action_role": "read_only_owner_delta_summary",
            "legacy_next_system_action_diagnostic": legacy_next_action,
            "current_blockers": current_blockers,
            "needs_user_decision": False,
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


__all__ = [
    "PROGRESS_PORTAL_HTML_REF",
    "PROGRESS_PORTAL_HOSTED_PACKAGE_REF",
    "PROGRESS_PORTAL_PAYLOAD_REF",
    "PROGRESS_PORTAL_STUDY_HTML_REF_TEMPLATE",
    "PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE",
    "build_progress_portal_hosted_package",
    "materialize_progress_portal",
]
