from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

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
from med_autoscience.controllers.progress_portal_parts.progress_first_operator import (
    build_progress_first_operator_projection,
)
from med_autoscience.controllers.progress_portal_parts.html import (
    render_progress_portal_html as render_progress_portal_html_part,
)
from med_autoscience.controllers.progress_portal_parts.owner_delta_summary import (
    legacy_next_action_diagnostic,
    owner_delta_read_only_summary,
)
from med_autoscience.controllers.progress_portal_parts.payload_helpers import (
    _conditions,
    _delivery_summary,
    _field,
    _freshness,
    _latest_events,
    _list_field,
    _mapping,
    _non_empty_text,
    _opl_handoff_projection,
    _outer_supervision_slo,
    _production_blocker_impact,
    _quality_summary,
    _runtime_continuity,
    _source_payload_summary,
    _supervision,
    _utc_now,
    _valid_user_visible_projection,
)
from med_autoscience.controllers.progress_portal_parts import read_model_materializer
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_progress_portal"
HOSTED_PACKAGE_SURFACE_KIND = "mas_progress_portal_hosted_package"
BRAND = "Med Auto Science"
PROGRESS_PORTAL_PAYLOAD_REF = read_model_materializer.PROGRESS_PORTAL_PAYLOAD_REF
PROGRESS_PORTAL_HTML_REF = read_model_materializer.PROGRESS_PORTAL_HTML_REF
PROGRESS_PORTAL_HOSTED_PACKAGE_REF = read_model_materializer.PROGRESS_PORTAL_HOSTED_PACKAGE_REF
PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE = (
    read_model_materializer.PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE
)
PROGRESS_PORTAL_STUDY_HTML_REF_TEMPLATE = (
    read_model_materializer.PROGRESS_PORTAL_STUDY_HTML_REF_TEMPLATE
)


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
    progress_first = build_progress_first_operator_projection(progress)
    mission_summary = _mission_summary(progress)
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
    if study_workbench:
        study_workbench = _study_workbench_with_mission_summary(study_workbench, mission_summary)
    owner_delta_summary = owner_delta_read_only_summary(_mapping(study_workbench.get("current_owner_delta")))
    legacy_next_action = legacy_next_action_diagnostic(
        user_visible.get("next_system_action"),
        user_visible.get("user_next"),
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
            "artifact_first_mission_summary": mission_summary,
            "mission_state": mission_summary.get("mission_state"),
            "current_objective": _mapping(mission_summary.get("current_objective")),
            "latest_artifact_delta": _mapping(mission_summary.get("latest_artifact_delta")),
            "next_owner_or_human_decision": _mapping(
                mission_summary.get("next_owner_or_human_decision")
            ),
            "platform_diagnostics": _mapping(mission_summary.get("platform_diagnostics")),
            "owner_delta_summary": owner_delta_summary,
            "next_system_action": _mission_next_step_summary(mission_summary)
            or owner_delta_summary["summary"]
            or "等待 artifact-first mission summary 生成论文产物下一步。",
            "next_system_action_role": "artifact_first_mission_summary",
            "legacy_next_system_action_diagnostic": legacy_next_action,
            "needs_user_decision": bool(user_visible.get("needs_user_decision")),
            "decision_trace": _body_free_trace(user_visible.get("decision_trace")),
            "decision_trace_refs": _list_field(user_visible, "decision_trace_refs"),
            "failed_path_ledger": _body_free_trace(user_visible.get("failed_path_ledger")),
            "failed_path_refs": _list_field(user_visible, "failed_path_refs"),
            "supervision": _supervision(progress, runtime),
            "outer_supervision_slo": outer_supervision_slo or None,
            "runtime_continuity": runtime_continuity,
            "production_blocker_impact": production_blocker_impact,
            "progress_first": progress_first,
            "evidence_gap_view": _mapping(study_workbench.get("evidence_gap_view")),
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


def _mission_summary(progress: Mapping[str, Any]) -> dict[str, Any]:
    existing = _mapping(progress.get("artifact_first_mission_summary"))
    if existing:
        return existing
    from med_autoscience.controllers.study_progress_parts.mission_summary import (
        build_artifact_first_mission_summary,
    )

    return build_artifact_first_mission_summary(progress)


def _mission_next_step_summary(summary: Mapping[str, Any]) -> str | None:
    objective = _mapping(summary.get("current_objective"))
    decision = _mapping(summary.get("next_owner_or_human_decision"))
    latest_delta = _mapping(summary.get("latest_artifact_delta"))
    parts: list[str] = []
    if text := _non_empty_text(summary.get("mission_state")):
        parts.append(f"mission_state={text}")
    if text := _non_empty_text(objective.get("objective")):
        parts.append(f"objective={text}")
    if text := _non_empty_text(decision.get("next_owner")):
        parts.append(f"next_owner={text}")
    elif decision.get("human_decision_required") is True:
        parts.append("human_decision_required=true")
    if count := latest_delta.get("count"):
        parts.append(f"artifact_delta_count={count}")
    return "; ".join(parts) if parts else None


def _study_workbench_with_mission_summary(
    study_workbench: Mapping[str, Any],
    mission_summary: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(study_workbench)
    updated["mission_summary"] = dict(mission_summary)
    tabs = [dict(item) for item in updated.get("tabs") or [] if isinstance(item, Mapping)]
    mission_tab = {
        "id": "mission_summary",
        "label": "Mission Summary",
        "status": _non_empty_text(mission_summary.get("mission_state")) or "missing",
    }
    updated["tabs"] = [mission_tab, *[item for item in tabs if item.get("id") != "mission_summary"]]
    overview = _mapping(updated.get("overview"))
    overview["mission_summary"] = dict(mission_summary)
    overview["next_system_action"] = _mission_next_step_summary(mission_summary) or overview.get(
        "next_system_action"
    )
    overview["next_system_action_role"] = "artifact_first_mission_summary"
    overview["next_system_action_boundary"] = _mission_overview_action_boundary(
        _mapping(overview.get("next_system_action_boundary"))
    )
    updated["overview"] = overview
    updated["overview_action_boundary"] = overview["next_system_action_boundary"]
    summary = _mapping(updated.get("summary"))
    summary["default_read_surface"] = "artifact_first_mission_summary"
    summary["mission_state"] = mission_summary.get("mission_state")
    summary["platform_repair_folded_to_diagnostics"] = True
    updated["summary"] = summary
    return updated


def _mission_overview_action_boundary(existing: Mapping[str, Any]) -> dict[str, Any]:
    boundary = dict(existing)
    boundary["next_system_action_role"] = "artifact_first_mission_summary"
    boundary["default_read_surface"] = "artifact_first_mission_summary"
    boundary["legacy_owner_delta_role"] = "diagnostic_input"
    boundary["projection_only"] = True
    boundary["can_generate_action"] = False
    boundary["can_execute"] = False
    boundary["can_authorize_provider_admission"] = False
    boundary["can_authorize_worker_attempt"] = False
    boundary["must_not_be_used_as_provider_admission"] = True
    boundary["must_not_be_used_as_next_action_authority"] = True
    boundary["must_not_be_used_as_publication_ready"] = True
    boundary["must_not_be_used_as_paper_progress"] = True
    return boundary


def _attach_study_hrefs(studies: list[dict[str, Any]], *, from_study_page: bool) -> None:
    for item in studies:
        study_id = _non_empty_text(item.get("study_id"))
        if study_id is None:
            continue
        item["portal_href"] = study_detail_href(study_id, from_study_page=from_study_page)


def _body_free_trace(value: object) -> dict[str, Any]:
    payload = _mapping(value)
    if not payload:
        return {}
    refs = [item for item in payload.get("refs") or [] if isinstance(item, str) and item.strip()]
    return {
        "summary": _non_empty_text(payload.get("summary")),
        "refs": refs,
        "body_included": False,
        "route_authority": False,
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
    return read_model_materializer.materialize_progress_portal(
        profile=profile,
        build_payload=build_progress_portal_payload,
        render_html=render_progress_portal_html,
        surface_kind=SURFACE_KIND,
        hosted_package_surface_kind=HOSTED_PACKAGE_SURFACE_KIND,
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
        open_browser=open_browser,
        auto_refresh_seconds=auto_refresh_seconds,
    )


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
    return read_model_materializer.build_progress_portal_hosted_package(
        profile=profile,
        payload=payload,
        payload_path=payload_path,
        html_path=html_path,
        hosted_package_path=hosted_package_path,
        hosted_package_surface_kind=HOSTED_PACKAGE_SURFACE_KIND,
        profile_ref=profile_ref,
        study_pages=study_pages,
    )


__all__ = [
    "build_progress_portal_payload",
    "build_progress_portal_hosted_package",
    "render_progress_portal_html",
    "materialize_progress_portal",
]
