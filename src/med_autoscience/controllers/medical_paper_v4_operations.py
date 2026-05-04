from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.medical_paper_v3_action_truth import action_truths_for_readiness


SCHEMA_VERSION = 1
SURFACE = "medical_paper_v4_operations_dashboard"


def authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_projection_only",
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def build_v4_operations_dashboard(readiness: Mapping[str, Any] | None) -> dict[str, Any]:
    source = readiness if isinstance(readiness, Mapping) else {}
    surfaces = _surfaces_by_key(source)
    action_truths = action_truths_for_readiness(source)
    health = {
        "provider_health": _surface_health(
            surfaces,
            "literature_provider_runtime",
            default_missing_reason="missing_literature_provider_runtime",
        ),
        "operator_action_health": _operator_action_health(action_truths),
        "soak_monitor_health": _surface_health(
            surfaces,
            "real_workspace_soak_monitor",
            default_missing_reason="missing_real_workspace_soak_monitor",
        ),
        "statistical_blocker_health": _surface_health(
            surfaces,
            "statistical_discipline_operations",
            default_missing_reason="missing_statistical_discipline_operations",
        ),
        "ai_reviewer_calibration_health": _ai_reviewer_calibration_health(surfaces),
    }
    blocked = [key for key, item in health.items() if item["status"] in {"missing", "blocked"}]
    partial = [key for key, item in health.items() if item["status"] == "partial"]
    overall_status = "ready"
    if blocked:
        overall_status = "blocked"
    elif partial:
        overall_status = "partial"
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": "medical_paper_v4_operations_read_model",
        "overall_status": overall_status,
        "summary": _summary(overall_status=overall_status, blocked=blocked, partial=partial),
        "health": health,
        "action_truth": action_truths,
        "next_action": _next_action(health),
        "authority_contract": authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def workspace_v4_operations_state(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dashboards = []
    for study in studies:
        readiness = study.get("medical_paper_readiness") if isinstance(study, Mapping) else None
        dashboard = build_v4_operations_dashboard(readiness if isinstance(readiness, Mapping) else {})
        dashboards.append(
            {
                "study_id": _text(study.get("study_id")) if isinstance(study, Mapping) else "unknown-study",
                "overall_status": dashboard["overall_status"],
                "summary": dashboard["summary"],
                "next_action": dashboard["next_action"],
                "health": dashboard["health"],
            }
        )
    counts = {
        "study_count": len(dashboards),
        "ready": sum(1 for item in dashboards if item["overall_status"] == "ready"),
        "partial": sum(1 for item in dashboards if item["overall_status"] == "partial"),
        "blocked": sum(1 for item in dashboards if item["overall_status"] == "blocked"),
    }
    status = "not_available" if not dashboards else ("blocked" if counts["blocked"] else "ready")
    if dashboards and counts["partial"] and not counts["blocked"]:
        status = "partial"
    return {
        "surface": "workspace_medical_paper_v4_operations_state",
        "schema_version": SCHEMA_VERSION,
        "read_model": "medical_paper_v4_operations_read_model",
        "status": status,
        "summary": _workspace_summary(status=status, counts=counts),
        "counts": counts,
        "studies": dashboards,
        "authority_contract": authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _surface_health(
    surfaces: Mapping[str, Mapping[str, Any]],
    surface_key: str,
    *,
    default_missing_reason: str,
) -> dict[str, Any]:
    surface = dict(surfaces.get(surface_key) or {})
    status = _text(surface.get("status")) or "missing"
    return {
        "surface_key": surface_key,
        "status": status,
        "missing_reason": _text(surface.get("missing_reason")) or ("" if status == "present" else default_missing_reason),
        "durable_refs": _durable_refs(surface),
        "next_action": _health_next_action(surface_key=surface_key, status=status),
    }


def _operator_action_health(action_truths: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    actions = [dict(item) for item in action_truths if isinstance(item, Mapping)]
    status = "ready" if not actions else "partial"
    if any(_text(item.get("status")) in {"blocked", "missing"} for item in actions):
        status = "blocked"
    return {
        "surface_key": "guarded_operator_actions",
        "status": status,
        "missing_reason": "" if status == "ready" else "guarded_operator_actions_pending",
        "pending_action_count": len(actions),
        "action_ids": [_text(item.get("action_id")) for item in actions if _text(item.get("action_id"))],
        "next_action": "replay_or_dispatch_guarded_operator_actions" if actions else "continue_managed_execution",
    }


def _ai_reviewer_calibration_health(surfaces: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    calibration = dict(surfaces.get("ai_reviewer_calibration_learning_loop") or {})
    if calibration:
        status = _text(calibration.get("status")) or "missing"
        return {
            "surface_key": "ai_reviewer_calibration_learning_loop",
            "status": status,
            "missing_reason": _text(calibration.get("missing_reason")),
            "durable_refs": _durable_refs(calibration),
            "next_action": _health_next_action(surface_key="ai_reviewer_calibration_learning_loop", status=status),
        }
    dependent = [
        surfaces.get("target_journal_writing_layer"),
        surfaces.get("revision_rebuttal_loop"),
        surfaces.get("authoring_runtime_authorization"),
    ]
    present = [item for item in dependent if isinstance(item, Mapping) and _text(item.get("status")) == "present"]
    status = "partial" if present else "blocked"
    return {
        "surface_key": "ai_reviewer_calibration_learning_loop",
        "status": status,
        "missing_reason": "missing_ai_reviewer_calibration_projection",
        "durable_refs": [],
        "next_action": "append_ai_reviewer_calibration_learning_entry",
    }


def _surfaces_by_key(readiness: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for item in readiness.get("capability_surfaces") or []:
        if not isinstance(item, Mapping):
            continue
        surface_key = _text(item.get("surface_key"))
        if surface_key:
            result[surface_key] = item
    return result


def _durable_refs(surface: Mapping[str, Any]) -> list[str]:
    refs = [str(item).strip() for item in surface.get("evidence_refs") or [] if str(item).strip()]
    artifact_path = _text(surface.get("artifact_path"))
    if artifact_path and artifact_path not in refs:
        refs.append(artifact_path)
    return refs


def _next_action(health: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    for key in (
        "provider_health",
        "operator_action_health",
        "statistical_blocker_health",
        "ai_reviewer_calibration_health",
        "soak_monitor_health",
    ):
        item = health[key]
        if item["status"] in {"missing", "blocked", "partial"}:
            return {
                "health_key": key,
                "surface_key": item["surface_key"],
                "summary": item["next_action"],
            }
    return {
        "health_key": "none",
        "surface_key": "medical_paper_v4_operations_dashboard",
        "summary": "continue_managed_execution",
    }


def _health_next_action(*, surface_key: str, status: str) -> str:
    if status in {"present", "ready"}:
        return "continue_managed_execution"
    return {
        "literature_provider_runtime": "repair_provider_operations_before_literature_ready",
        "real_workspace_soak_monitor": "run_read_only_real_workspace_soak_monitor",
        "statistical_discipline_operations": "resolve_statistical_reviewer_blockers",
        "ai_reviewer_calibration_learning_loop": "append_ai_reviewer_calibration_learning_entry",
    }.get(surface_key, "inspect_medical_paper_v4_operations_dashboard")


def _summary(*, overall_status: str, blocked: Sequence[str], partial: Sequence[str]) -> str:
    if overall_status == "ready":
        return "v4 production operations are ready; continue managed execution."
    if blocked:
        return "v4 production operations are blocked: " + ", ".join(blocked)
    return "v4 production operations are partial: " + ", ".join(partial)


def _workspace_summary(*, status: str, counts: Mapping[str, int]) -> str:
    if status == "not_available":
        return "No study exposes medical paper v4 operations state yet."
    return (
        f"{counts.get('study_count', 0)} study operations projected; "
        f"ready {counts.get('ready', 0)}, partial {counts.get('partial', 0)}, blocked {counts.get('blocked', 0)}."
    )


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "SURFACE",
    "authority_contract",
    "build_v4_operations_dashboard",
    "workspace_v4_operations_state",
]
