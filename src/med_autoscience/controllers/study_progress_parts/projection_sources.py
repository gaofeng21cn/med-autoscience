from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor, opl_runtime_refs
from med_autoscience.publication_eval_specificity_targets import specificity_target_status
from med_autoscience.profiles import WorkspaceProfile

from .shared import _mapping_copy, _non_empty_text, _read_json_object


def _supervision_active_run_id(
    *,
    status: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    autonomous_runtime_notice: dict[str, Any],
    continuation_state: dict[str, Any],
) -> str | None:
    return opl_runtime_refs.active_run_id(
        {
            **dict(status or {}),
            "execution_owner_guard": dict(execution_owner_guard or {}),
            "autonomous_runtime_notice": dict(autonomous_runtime_notice or {}),
            "continuation_state": dict(continuation_state or {}),
        }
    )


def _attach_existing_autonomy_slo_projection(
    payload: dict[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    autonomy_slo_status = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if autonomy_slo_status is None:
        return payload
    updated = dict(payload)
    updated["autonomy_slo"] = autonomy_slo_status
    updated["ai_doctor_state"] = (
        _mapping_copy(autonomy_slo_status.get("ai_doctor_request"))
        or {
            "state": autonomy_slo_status.get("ai_doctor_state") or "not_observed",
            "request_required": bool(autonomy_slo_status.get("ai_doctor_request_required")),
        }
    )
    repair_recommendation = _mapping_copy(autonomy_slo_status.get("repair_recommendation"))
    updated["repair_recommendation"] = repair_recommendation or None
    updated["last_meaningful_progress_at"] = _non_empty_text(
        autonomy_slo_status.get("last_meaningful_progress_at")
    )
    refs = _mapping_copy(updated.get("refs"))
    refs["autonomy_slo_status_path"] = str(
        autonomy_ai_doctor.stable_slo_status_path(study_root=study_root)
    )
    updated["refs"] = refs
    return updated


def _autonomy_slo_observer_status(
    *,
    study_root: Path,
    state: str,
    observer_status: str,
    error: object | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface": "autonomy_progress_slo_status",
        "schema_version": 1,
        "study_id": study_root.name,
        "state": state,
        "observer_status": observer_status,
        "breach_types": [],
        "ai_doctor_request_required": False,
        "ai_doctor_state": "not_required",
        "quality_gate_relaxation_allowed": False,
        "status_path": str(autonomy_ai_doctor.stable_slo_status_path(study_root=study_root)),
    }
    if error is not None:
        payload["observer_error"] = str(error)
    return payload


def _read_or_materialize_autonomy_slo_status(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
) -> dict[str, Any] | None:
    autonomy_slo_status = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if autonomy_slo_status is not None:
        return autonomy_slo_status
    try:
        from med_autoscience.controllers import study_cycle_profiler

        profile_payload = study_cycle_profiler.profile_study_cycle(
            profile=profile,
            study_id=None,
            study_root=study_root,
        )
    except (OSError, json.JSONDecodeError, TypeError, ValueError, RuntimeError) as exc:
        return _autonomy_slo_observer_status(
            study_root=study_root,
            state="observer_failed",
            observer_status="failed",
            error=exc,
        )
    profile_slo_status = _mapping_copy(profile_payload.get("autonomy_progress_slo_status"))
    if profile_slo_status:
        return profile_slo_status
    autonomy_slo_status = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if autonomy_slo_status is not None:
        return autonomy_slo_status
    return _autonomy_slo_observer_status(
        study_root=study_root,
        state="observer_not_materialized",
        observer_status="not_materialized",
    )


def _read_gate_specificity_request(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None = None,
) -> tuple[Path, dict[str, Any] | None]:
    request_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "requests"
        / "publication_gate_specificity"
        / "latest.json"
    )
    if _publication_eval_has_complete_specificity_targets(publication_eval_payload):
        return request_path, None
    payload = _read_json_object(request_path)
    if payload is None or payload.get("surface") != "domain_action_request":
        return request_path, None
    if _non_empty_text(payload.get("request_kind")) != "publication_gate_specificity_required":
        return request_path, None
    return request_path, {
        "surface": "study_progress_publication_gate_specificity_request_projection",
        "authority": _non_empty_text(payload.get("authority")) or "observability_only",
        "request_id": _non_empty_text(payload.get("request_id")),
        "request_owner": _non_empty_text(payload.get("request_owner")),
        "gate_owner": _non_empty_text(payload.get("gate_owner")),
        "missing_target_kinds": [
            item
            for item in (payload.get("missing_target_kinds") or [])
            if _non_empty_text(item) is not None
        ],
        "requested_target_types": [
            item
            for item in (payload.get("requested_target_types") or [])
            if _non_empty_text(item) is not None
        ],
        "owner_visible_checklist": [
            dict(item) for item in (payload.get("owner_visible_checklist") or []) if isinstance(item, dict)
        ],
        "next_controller_write": (
            dict(payload.get("next_controller_write"))
            if isinstance(payload.get("next_controller_write"), dict)
            else None
        ),
        "source_path": str(request_path),
        "quality_gate_relaxation_allowed": bool(payload.get("quality_gate_relaxation_allowed")),
        "paper_package_mutation_allowed": bool(payload.get("paper_package_mutation_allowed")),
        "medical_claim_authoring_allowed": bool(payload.get("medical_claim_authoring_allowed")),
    }


def _publication_eval_has_complete_specificity_targets(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    for action in payload.get("recommended_actions") or []:
        if not isinstance(action, dict):
            continue
        if specificity_target_status(action.get("specificity_targets")).get("complete") is True:
            return True
    return False
