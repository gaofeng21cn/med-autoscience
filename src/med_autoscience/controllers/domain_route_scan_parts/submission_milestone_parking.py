from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_outer_loop
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_owner_route
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile


SUBMISSION_MILESTONE_PARK_SOURCE = "domain_route_scan_submission_milestone_park"


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


def _runtime_state_path(status: Mapping[str, Any]) -> Path | None:
    quest_root = _text(status.get("quest_root"))
    if quest_root is None:
        return None
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _submission_milestone_runtime_owner_handoff(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    quest_id: str,
    status: Mapping[str, Any],
    controller_decision: Mapping[str, Any],
) -> dict[str, Any]:
    runtime_state_path = _runtime_state_path(status)
    if runtime_state_path is None:
        return {
            "marked": False,
            "reason": "quest_root_missing",
        }
    return platform_repair_owner_route.mark_owner_route_handoff(
        study_root=profile.studies_root / study_id,
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        reason="submission_milestone_runtime_stop_required",
        repair_kind="submission_milestone_runtime_owner_stop",
        authorization=_mapping(controller_decision),
        extra={
            "requested_runtime_action": "stop",
            "source": SUBMISSION_MILESTONE_PARK_SOURCE,
            "runtime_root_ref": str(profile.runtime_root),
            "submission_milestone_parking": True,
        },
    )


def _write_submission_milestone_repair_lifecycle(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    controller_decision: Mapping[str, Any],
    stop_result: Mapping[str, Any] | None = None,
    owner_route_handoff: Mapping[str, Any] | None = None,
    state: str = "parked",
    dispatch_status: str = "applied",
    reason: str = "submission_milestone_parked",
) -> dict[str, Any]:
    payload = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "state": state,
        "authority": "observability_only" if dispatch_status == "owner_route_required" else "controller_stop",
        "blocked_reason": None if dispatch_status == "applied" else reason,
        "next_owner": None if dispatch_status == "applied" else "one-person-lab",
        "external_supervisor_required": False,
        "auto_apply_allowed": False,
        "applied_at": _utc_now() if dispatch_status == "applied" else None,
        "last_apply_attempt_at": _utc_now(),
        "quality_gate_relaxation_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "opl_runtime_owner_route_required": dispatch_status == "owner_route_required",
        "last_apply_attempt": {
            "state": "applied",
            "dispatch_status": dispatch_status,
            "reason": reason,
            "source": SUBMISSION_MILESTONE_PARK_SOURCE,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
        },
        "refs": {
            "controller_decision_ref": _mapping(controller_decision.get("study_decision_ref")),
        },
    }
    if stop_result is not None:
        payload["refs"]["stop_result"] = dict(stop_result)
    if owner_route_handoff is not None:
        payload["refs"]["runtime_owner_handoff"] = dict(owner_route_handoff)
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
    owner_route = _submission_milestone_runtime_owner_handoff(
        profile=profile,
        study_id=study_id,
        quest_id=quest_id,
        status=status,
        controller_decision=controller_decision,
    )
    if owner_route.get("marked") is not True:
        return {
            "dispatch_status": "blocked",
            "reason": _text(owner_route.get("reason")) or "submission_milestone_runtime_owner_handoff_failed",
            "controller_decision": dict(controller_decision),
            "runtime_owner_handoff": owner_route,
        }
    lifecycle = _write_submission_milestone_repair_lifecycle(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        controller_decision=controller_decision,
        owner_route_handoff=_mapping(owner_route.get("handoff")),
        state="owner_route_required",
        dispatch_status="owner_route_required",
        reason="submission_milestone_runtime_stop_required",
    )
    return {
        "dispatch_status": "owner_route_required",
        "reason": "submission_milestone_runtime_stop_required",
        "controller_decision": dict(controller_decision),
        "queue_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "recommended_task_kind": "domain_route/reconcile-apply",
        "runtime_owner_handoff": owner_route.get("handoff"),
        "repair_lifecycle": lifecycle,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
