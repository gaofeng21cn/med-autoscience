from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from med_autoscience.controllers.production_blocker_impact_projection import (
    build_production_blocker_impact_projection,
)
from med_autoscience.controllers.runtime_continuity_projection import runtime_continuity_projection


PROGRESS_PORTAL_PAYLOAD_REF = "artifacts/runtime/progress_portal/latest.json"
PROGRESS_PORTAL_HTML_REF = "ops/mas/progress/index.html"


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
    opl_control = _mapping(runtime.get("opl_current_control_state")) or _mapping(
        progress.get("opl_current_control_state")
    )
    return {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(opl_control.get("active_run_id")) or _non_empty_text(runtime.get("active_run_id")),
        "health_status": (
            _non_empty_text(opl_control.get("state"))
            or _non_empty_text(opl_control.get("status"))
            or _non_empty_text(runtime.get("health_status"))
            or _non_empty_text(supervision.get("health_status"))
        ),
        "supervisor_tick_status": (
            _non_empty_text(opl_control.get("supervisor_tick_status"))
            or _non_empty_text(tick_audit.get("status"))
        ),
    }

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
    outer_state = _non_empty_text(outer_supervision_slo.get("state"))
    if outer_state == "missing":
        missing.append("outer_supervision_slo")
    elif outer_state in {"due", "stale"}:
        stale.append(f"outer_supervision_slo_{outer_state}")
    elif outer_state == "blocked":
        conflict.append("outer_supervision_slo_blocked")
    if delivery.get("status") == "missing":
        missing.append("current_package")
    opl_control = _mapping(runtime.get("opl_current_control_state")) or _mapping(progress.get("opl_current_control_state"))
    tick_status = _non_empty_text(opl_control.get("supervisor_tick_status")) or _non_empty_text(
        _mapping(runtime.get("supervisor_tick_audit")).get("status")
    )
    if tick_status in {"missing", "invalid"}:
        missing.append("domain_route_tick")
    elif tick_status == "stale":
        stale.append("domain_route_tick")
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
    summary = {
        "available": True,
        "study_id": _non_empty_text(payload.get("study_id")),
        "generated_at": _non_empty_text(payload.get("generated_at")) or _non_empty_text(payload.get("emitted_at")),
        "status": _non_empty_text(payload.get("status")),
        "surface_kind": _non_empty_text(payload.get("surface_kind")),
    }
    projection_error = _mapping(payload.get("projection_error"))
    if projection_error:
        summary["projection_error"] = True
        summary["projection_error_type"] = _non_empty_text(projection_error.get("error_type"))
        summary["projection_error_handled_as"] = _non_empty_text(projection_error.get("handled_as"))
    return summary

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
