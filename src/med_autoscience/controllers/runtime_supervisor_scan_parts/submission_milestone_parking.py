from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_outer_loop, study_runtime_router
from med_autoscience.controllers.study_runtime_resolution import _execution_payload, _load_yaml_dict
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


SUBMISSION_MILESTONE_PARK_SOURCE = "runtime_supervisor_scan_submission_milestone_park"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _stop_submission_milestone_runtime(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
) -> dict[str, Any]:
    study_payload = _load_yaml_dict(study_root / "study.yaml")
    execution = _execution_payload(study_payload, profile=profile)
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    backend = (
        study_runtime_router._managed_runtime_backend_for_execution(
            execution,
            profile=profile,
            runtime_root=runtime_context.runtime_root,
        )
        or study_runtime_router._default_managed_runtime_backend()
    )
    result = backend.stop_quest(
        runtime_root=runtime_context.runtime_root,
        quest_id=quest_id,
        source=SUBMISSION_MILESTONE_PARK_SOURCE,
    )
    return dict(result) if isinstance(result, Mapping) else {"result": result}


def _write_submission_milestone_repair_lifecycle(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    controller_decision: Mapping[str, Any],
    stop_result: Mapping[str, Any],
) -> dict[str, Any]:
    payload = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "state": "parked",
        "authority": "controller_stop",
        "blocked_reason": None,
        "next_owner": None,
        "external_supervisor_required": False,
        "auto_apply_allowed": False,
        "applied_at": _utc_now(),
        "last_apply_attempt_at": _utc_now(),
        "quality_gate_relaxation_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "last_apply_attempt": {
            "state": "applied",
            "dispatch_status": "applied",
            "reason": "submission_milestone_parked",
            "source": SUBMISSION_MILESTONE_PARK_SOURCE,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
        },
        "refs": {
            "controller_decision_ref": _mapping(controller_decision.get("study_decision_ref")),
            "stop_result": dict(stop_result),
        },
    }
    _write_json(study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json", payload)
    return payload


def _refresh_parked_controller_decision(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status: Mapping[str, Any],
) -> dict[str, Any] | None:
    return study_outer_loop.refresh_parked_submission_milestone_controller_decision(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload=dict(status),
        source=SUBMISSION_MILESTONE_PARK_SOURCE,
    )


def _quest_id_from_controller_or_status(
    *,
    controller_decision: Mapping[str, Any],
    status: Mapping[str, Any],
) -> str | None:
    return (
        _text(controller_decision.get("quest_id"))
        or _text(status.get("quest_id"))
        or _text(_mapping(status.get("continuation_state")).get("quest_id"))
    )


def reconcile_stopped_submission_milestone_parking(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    enabled: bool,
) -> dict[str, Any] | None:
    if not enabled:
        return None
    if not developer_mode.safe_actions_enabled:
        return {
            "dispatch_status": "blocked",
            "reason": "developer_supervisor_safe_actions_not_enabled",
        }
    if _text(status.get("quest_status")) != "stopped":
        return None
    try:
        controller_decision = _refresh_parked_controller_decision(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            status=status,
        )
    except Exception as exc:
        return {
            "dispatch_status": "blocked",
            "reason": "submission_milestone_controller_refresh_failed",
            "error": str(exc),
        }
    if controller_decision is None:
        return None
    quest_id = _quest_id_from_controller_or_status(
        controller_decision=controller_decision,
        status=status,
    )
    if quest_id is None:
        return {
            "dispatch_status": "blocked",
            "reason": "submission_milestone_stop_requires_quest_id",
            "controller_decision": dict(controller_decision),
        }
    stop_result = {
        "ok": True,
        "status": "already_stopped",
        "quest_id": quest_id,
        "source": SUBMISSION_MILESTONE_PARK_SOURCE,
    }
    lifecycle = _write_submission_milestone_repair_lifecycle(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        controller_decision=controller_decision,
        stop_result=stop_result,
    )
    return {
        "dispatch_status": "applied",
        "reason": "submission_milestone_already_parked",
        "controller_decision": dict(controller_decision),
        "stop_result": stop_result,
        "repair_lifecycle": lifecycle,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def refresh_submission_milestone_parking(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    enabled: bool,
) -> dict[str, Any] | None:
    if not enabled:
        return None
    if not developer_mode.safe_actions_enabled:
        return {
            "dispatch_status": "blocked",
            "reason": "developer_supervisor_safe_actions_not_enabled",
        }
    try:
        controller_decision = _refresh_parked_controller_decision(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            status=status,
        )
    except Exception as exc:
        return {
            "dispatch_status": "blocked",
            "reason": "submission_milestone_controller_refresh_failed",
            "error": str(exc),
        }
    if controller_decision is None:
        return None
    quest_id = _quest_id_from_controller_or_status(
        controller_decision=controller_decision,
        status=status,
    )
    if quest_id is None:
        return {
            "dispatch_status": "blocked",
            "reason": "submission_milestone_stop_requires_quest_id",
            "controller_decision": dict(controller_decision),
        }
    try:
        stop_result = _stop_submission_milestone_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
        )
    except Exception as exc:
        return {
            "dispatch_status": "blocked",
            "reason": "submission_milestone_stop_failed",
            "error": str(exc),
            "controller_decision": dict(controller_decision),
        }
    lifecycle = _write_submission_milestone_repair_lifecycle(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        controller_decision=controller_decision,
        stop_result=stop_result,
    )
    return {
        "dispatch_status": "applied",
        "reason": "submission_milestone_parked",
        "controller_decision": dict(controller_decision),
        "stop_result": stop_result,
        "repair_lifecycle": lifecycle,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
