from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.medical_paper_v4_operations import (
    build_v4_operations_dashboard,
)


SCHEMA_VERSION = 1
SURFACE = "medical_paper_ops_health"
READ_MODEL = "medical_paper_ops_health_read_model"


def authority_contract() -> dict[str, Any]:
    return {
        "authority": "observability_projection_only",
        "read_model_only": True,
        "can_authorize_quality": False,
        "can_authorize_submission": False,
        "can_authorize_finalize": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def build_medical_paper_ops_health(
    readiness: Mapping[str, Any] | None,
    *,
    progress_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = readiness if isinstance(readiness, Mapping) else {}
    progress = progress_payload if isinstance(progress_payload, Mapping) else {}
    surfaces = _surfaces_by_key(source)
    health = {
        "provider_health": _provider_health(surfaces),
        "operator_replay_health": _operator_replay_health(source),
        "soak_drift_health": _soak_drift_health(surfaces, progress),
        "outcome_learning_health": _outcome_learning_health(surfaces, progress),
        "stat_guideline_health": _stat_guideline_health(surfaces, progress),
    }
    counts = {
        "ready": sum(1 for item in health.values() if item["status"] == "ready"),
        "partial": sum(1 for item in health.values() if item["status"] == "partial"),
        "blocked": sum(1 for item in health.values() if item["status"] == "blocked"),
    }
    status = "blocked" if counts["blocked"] else "partial" if counts["partial"] else "ready"
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "overall_status": status,
        "summary": _summary(status=status, counts=counts),
        "counts": counts,
        "last_green_at": _last_green_at(health),
        "health": health,
        "next_operator_action": _next_operator_action(health),
        "authority_contract": authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def workspace_medical_paper_ops_health(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    study_items = []
    for study in studies:
        if not isinstance(study, Mapping):
            continue
        readiness = study.get("medical_paper_readiness") if isinstance(study.get("medical_paper_readiness"), Mapping) else {}
        health = (
            study.get("medical_paper_ops_health")
            if isinstance(study.get("medical_paper_ops_health"), Mapping)
            else build_medical_paper_ops_health(readiness, progress_payload=study)
        )
        study_items.append(
            {
                "study_id": _text(study.get("study_id")) or "unknown-study",
                "overall_status": health["overall_status"],
                "summary": health["summary"],
                "last_green_at": health["last_green_at"],
                "next_operator_action": health["next_operator_action"],
                "health": health["health"],
            }
        )
    counts = {
        "study_count": len(study_items),
        "ready": sum(1 for item in study_items if item["overall_status"] == "ready"),
        "partial": sum(1 for item in study_items if item["overall_status"] == "partial"),
        "blocked": sum(1 for item in study_items if item["overall_status"] == "blocked"),
    }
    status = "not_available" if not study_items else "blocked" if counts["blocked"] else "partial" if counts["partial"] else "ready"
    return {
        "surface": "workspace_medical_paper_ops_health",
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "status": status,
        "summary": _workspace_summary(status=status, counts=counts),
        "counts": counts,
        "last_green_at": _workspace_last_green_at(study_items),
        "studies": study_items,
        "authority_contract": authority_contract(),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _provider_health(surfaces: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    surface = dict(surfaces.get("literature_provider_runtime") or {})
    provider_health = surface.get("provider_health") if isinstance(surface.get("provider_health"), Mapping) else {}
    status = _health_status(provider_health, surface, ready_statuses={"ready", "present"})
    diagnostics = _diagnostic_reasons(provider_health.get("diagnostics"))
    if not diagnostics and status != "ready":
        diagnostics = [_text(surface.get("missing_reason")) or "provider_health_not_ready"]
    return _health_item(
        component="provider_health",
        status=status,
        durable_refs=_durable_refs(surface),
        missing_reason=diagnostics[0] if diagnostics else "",
        next_action="repair_provider_health_freshness",
        details={
            "diagnostics": diagnostics,
            "checks": list(provider_health.get("checks") or []),
            "cache_freshness": dict(provider_health.get("cache_freshness") or {}),
            "citation_ledger": dict(provider_health.get("citation_ledger") or {}),
            "screening_reasons": dict(provider_health.get("screening_reasons") or {}),
        },
    )


def _operator_replay_health(readiness: Mapping[str, Any]) -> dict[str, Any]:
    v4 = build_v4_operations_dashboard(readiness)
    operator = dict((v4.get("health") or {}).get("operator_action_health") or {})
    action_truth = [item for item in v4.get("action_truth") or [] if isinstance(item, Mapping)]
    replay_refs = _unique(
        _text((item.get("action_result") or {}).get("replay_ref"))
        for item in action_truth
        if isinstance(item.get("action_result"), Mapping)
    )
    status = "ready" if not action_truth else "partial"
    if _text(operator.get("status")) == "blocked":
        status = "blocked"
    if action_truth and not replay_refs:
        status = "partial"
    return _health_item(
        component="operator_replay_health",
        status=status,
        durable_refs=replay_refs,
        missing_reason="" if status == "ready" else "operator_replay_actions_pending",
        next_action="replay_or_dispatch_guarded_operator_actions",
        details={
            "pending_action_count": int(operator.get("pending_action_count") or len(action_truth)),
            "action_ids": list(operator.get("action_ids") or []),
            "replay_refs": replay_refs,
        },
    )


def _soak_drift_health(
    surfaces: Mapping[str, Mapping[str, Any]],
    progress_payload: Mapping[str, Any],
) -> dict[str, Any]:
    surface = dict(surfaces.get("real_workspace_soak_monitor") or {})
    source = dict(progress_payload.get("real_workspace_soak_monitor") or {}) or surface
    status = _status_from_source(source, ready_values={"ready", "present"})
    drift_history = [dict(item) for item in source.get("drift_history") or [] if isinstance(item, Mapping)]
    last = drift_history[-1] if drift_history else {}
    last_green_at = _text(source.get("last_green_at")) or _text(last.get("scan_started_at") if _text(last.get("overall_status")) == "ready" else "")
    if not source:
        status = "blocked"
    return _health_item(
        component="soak_drift_health",
        status=status,
        durable_refs=_durable_refs(source),
        missing_reason=_text(source.get("missing_reason")) or _text(source.get("next_action")) or ("" if status == "ready" else "soak_drift_not_ready"),
        next_action="inspect_soak_drift_history" if status == "ready" else "run_read_only_real_workspace_soak_scheduler",
        details={
            "last_green_at": last_green_at,
            "last_green_scan_id": _text(source.get("last_green_scan_id")),
            "drift_history_count": len(drift_history),
            "latest_drift": _compact_drift(last),
        },
    )


def _outcome_learning_health(
    surfaces: Mapping[str, Mapping[str, Any]],
    progress_payload: Mapping[str, Any],
) -> dict[str, Any]:
    source = dict(progress_payload.get("ai_reviewer_outcome_learning_regression") or {})
    if not source:
        source = dict(surfaces.get("ai_reviewer_outcome_learning_regression") or {})
    if not source:
        source = dict(surfaces.get("ai_reviewer_calibration_learning_loop") or {})
    status = _status_from_source(source, ready_values={"ready", "present"})
    missing_modes = [str(item) for item in source.get("missing_required_failure_modes") or [] if str(item).strip()]
    if missing_modes:
        status = "blocked"
    return _health_item(
        component="outcome_learning_health",
        status=status,
        durable_refs=_durable_refs(source) + _unique(source.get("required_calibration_refs") or []),
        missing_reason=missing_modes[0] if missing_modes else _text(source.get("missing_reason")) or ("" if status == "ready" else "outcome_learning_regression_not_ready"),
        next_action="append_outcome_learning_calibration_intake" if status != "ready" else "continue_authoring_with_required_calibration_refs",
        details={
            "required_calibration_refs": list(source.get("required_calibration_refs") or []),
            "missing_required_failure_modes": missing_modes,
            "planning_mode": _text(source.get("planning_mode")),
        },
    )


def _stat_guideline_health(
    surfaces: Mapping[str, Mapping[str, Any]],
    progress_payload: Mapping[str, Any],
) -> dict[str, Any]:
    source = dict(progress_payload.get("statistical_discipline_operations") or {})
    if not source:
        source = dict(surfaces.get("statistical_discipline_operations") or {})
    status = _status_from_source(source, ready_values={"ready", "present"})
    blockers = [str(item) for item in source.get("blockers") or [] if str(item).strip()]
    if blockers:
        status = "blocked"
    guideline_pack = source.get("guideline_pack") if isinstance(source.get("guideline_pack"), Mapping) else {}
    evidence_contract = source.get("evidence_contract") if isinstance(source.get("evidence_contract"), Mapping) else {}
    return _health_item(
        component="stat_guideline_health",
        status=status,
        durable_refs=_durable_refs(source),
        missing_reason=blockers[0] if blockers else _text(source.get("missing_reason")) or ("" if status == "ready" else "stat_guideline_pack_not_ready"),
        next_action="resolve_statistical_guideline_blockers" if status != "ready" else "continue_statistical_review",
        details={
            "blockers": blockers,
            "guideline_families": list(guideline_pack.get("guideline_families") or []),
            "evidence_contract_fields": sorted(str(key) for key in evidence_contract),
            "primary_evidence_rule": _text(source.get("primary_evidence_rule")),
        },
    )


def _health_item(
    *,
    component: str,
    status: str,
    durable_refs: Sequence[str],
    missing_reason: str,
    next_action: str,
    details: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "component": component,
        "status": status,
        "durable_refs": list(durable_refs),
        "missing_reason": missing_reason,
        "next_action": next_action,
        "details": dict(details),
        "authority_contract": authority_contract(),
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


def _health_status(
    primary: Mapping[str, Any],
    secondary: Mapping[str, Any],
    *,
    ready_statuses: set[str],
) -> str:
    status = _text(primary.get("status")) or _text(secondary.get("status"))
    if status in ready_statuses:
        return "ready"
    if status in {"partial"}:
        return "partial"
    return "blocked"


def _status_from_source(source: Mapping[str, Any], *, ready_values: set[str]) -> str:
    status = _text(source.get("overall_status")) or _text(source.get("status"))
    if status in ready_values:
        return "ready"
    if status == "partial":
        return "partial"
    return "blocked"


def _diagnostic_reasons(value: object) -> list[str]:
    reasons: list[str] = []
    for item in value or []:
        if isinstance(item, Mapping):
            reason = _text(item.get("reason_code")) or _text(item.get("category"))
        else:
            reason = _text(item)
        if reason and reason not in reasons:
            reasons.append(reason)
    return reasons


def _durable_refs(surface: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("evidence_refs", "durable_refs", "required_calibration_refs"):
        refs.extend(_unique(surface.get(key) or []))
    for key in ("artifact_path", "durable_ref", "replay_ref"):
        value = _text(surface.get(key))
        if value and value not in refs:
            refs.append(value)
    return refs


def _compact_drift(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: item[key]
        for key in (
            "scan_id",
            "scan_started_at",
            "overall_status",
            "next_action",
            "blocked_reason_summary",
            "stop_loss_triggered",
            "revision_reopen_seen",
            "runtime_recovery_seen",
            "finalize_rebuild_seen",
        )
        if key in item
    }


def _last_green_at(health: Mapping[str, Mapping[str, Any]]) -> str | None:
    soak = health.get("soak_drift_health") or {}
    details = soak.get("details") if isinstance(soak.get("details"), Mapping) else {}
    return _text(details.get("last_green_at")) or None


def _workspace_last_green_at(studies: Sequence[Mapping[str, Any]]) -> str | None:
    values = sorted(_text(item.get("last_green_at")) for item in studies if _text(item.get("last_green_at")))
    return values[-1] if values else None


def _next_operator_action(health: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    for key in (
        "provider_health",
        "operator_replay_health",
        "soak_drift_health",
        "outcome_learning_health",
        "stat_guideline_health",
    ):
        item = health[key]
        if item["status"] in {"blocked", "partial"}:
            return {
                "health_key": key,
                "summary": item["next_action"],
                "missing_reason": item["missing_reason"],
            }
    return {
        "health_key": "none",
        "summary": "continue_managed_execution",
        "missing_reason": "",
    }


def _summary(*, status: str, counts: Mapping[str, int]) -> str:
    if status == "ready":
        return "medical paper ops health is ready; continue managed execution."
    return (
        "medical paper ops health is "
        f"{status}: ready {counts.get('ready', 0)}, partial {counts.get('partial', 0)}, "
        f"blocked {counts.get('blocked', 0)}."
    )


def _workspace_summary(*, status: str, counts: Mapping[str, int]) -> str:
    if status == "not_available":
        return "No study exposes medical paper ops health yet."
    return (
        f"{counts.get('study_count', 0)} study ops health projected; "
        f"ready {counts.get('ready', 0)}, partial {counts.get('partial', 0)}, blocked {counts.get('blocked', 0)}."
    )


def _unique(values: object) -> list[str]:
    result: list[str] = []
    for value in values or []:
        text = _text(value)
        if text and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "READ_MODEL",
    "SURFACE",
    "authority_contract",
    "build_medical_paper_ops_health",
    "workspace_medical_paper_ops_health",
]
