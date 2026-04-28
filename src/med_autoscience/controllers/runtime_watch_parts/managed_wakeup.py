from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import (
    runtime_supervision,
    study_runtime_router,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_escalation_record import RuntimeEscalationRecordRef
from med_autoscience.study_decision_record import (
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
)


_HARD_AUTO_RECOVERY_QUEST_STATUSES = frozenset({"active", "running", "waiting_for_user", "stopped"})
_HARD_AUTO_RECOVERY_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "quest_waiting_on_invalid_blocking",
        "quest_completion_requested_before_publication_gate_clear",
        "quest_stopped_by_controller_guard",
    }
)
_RUNTIME_RECOVERY_DECISIONS = frozenset({"create_and_start", "resume", "relaunch_stopped"})


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _serialize_managed_study_action(
    action_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any]:
    action = (
        action_payload
        if isinstance(action_payload, StudyRuntimeStatus)
        else StudyRuntimeStatus.from_payload(action_payload)
    )
    return {
        "study_id": action.study_id,
        "decision": action.decision.value if action.decision is not None else None,
        "reason": action.reason.value if action.reason is not None else None,
    }


def _managed_study_status_payload(
    action_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any]:
    if isinstance(action_payload, StudyRuntimeStatus):
        return action_payload.to_dict()
    return dict(action_payload)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _candidate_path(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json_object(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mapping_value(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _payload_active_run_id(payload: Mapping[str, Any]) -> str | None:
    continuation_state = _mapping_value(payload, "continuation_state")
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    autonomous_runtime_notice = _mapping_value(payload, "autonomous_runtime_notice")
    execution_owner_guard = _mapping_value(payload, "execution_owner_guard")
    for candidate in (
        payload.get("active_run_id"),
        continuation_state.get("active_run_id"),
        runtime_liveness_audit.get("active_run_id"),
        runtime_audit.get("active_run_id"),
        autonomous_runtime_notice.get("active_run_id"),
        execution_owner_guard.get("active_run_id"),
    ):
        active_run_id = _non_empty_text(candidate)
        if active_run_id is not None:
            return active_run_id
    return None


def _payload_runtime_liveness_status(payload: Mapping[str, Any]) -> str | None:
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    return _non_empty_text(runtime_liveness_audit.get("status")) or _non_empty_text(runtime_audit.get("status"))


def _payload_strict_live(payload: Mapping[str, Any]) -> bool:
    if _payload_runtime_liveness_status(payload) != "live":
        return False
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    if runtime_audit.get("worker_running") is not True:
        return False
    return _payload_active_run_id(payload) is not None


def _should_refresh_managed_study_status_after_ensure(payload: Mapping[str, Any]) -> bool:
    if _non_empty_text(payload.get("decision")) not in _RUNTIME_RECOVERY_DECISIONS:
        return False
    return not _payload_strict_live(payload)


def _refresh_managed_study_status_after_ensure(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    if not _should_refresh_managed_study_status_after_ensure(status_payload):
        return status_payload
    refreshed = study_runtime_router.study_runtime_status(
        profile=profile,
        study_root=study_root,
    )
    return _managed_study_status_payload(refreshed)


def _runtime_watch_wakeup_latest_path(study_root: Path) -> Path:
    return study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"


def _artifact_fingerprint(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False}
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return {
            "path": str(resolved),
            "exists": False,
        }
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "exists": True,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
    }


def _runtime_supervision_artifact_fingerprint(path: Path) -> dict[str, Any]:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return {
            "path": str(resolved),
            "exists": False,
        }
    payload = _read_json_object(resolved) or {}
    stable_payload = {
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "health_status": _non_empty_text(payload.get("health_status")),
        "runtime_reason": _non_empty_text(payload.get("runtime_reason")),
        "next_action": _non_empty_text(payload.get("next_action")),
        "active_run_id": _non_empty_text(payload.get("active_run_id")),
        "needs_human_intervention": bool(payload.get("needs_human_intervention")),
        "supervisor_tick_status": _non_empty_text(payload.get("supervisor_tick_status")),
    }
    canonical = json.dumps(stable_payload, ensure_ascii=False, sort_keys=True)
    return {
        "path": str(resolved),
        "exists": True,
        "stable_payload_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        "stable_payload": stable_payload,
    }


def _managed_outer_loop_wakeup_fingerprint(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> tuple[str, dict[str, Any]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    quest_root = _candidate_path(status_payload.get("quest_root"))
    watched_payload = {
        "status": {
            "study_id": _non_empty_text(status_payload.get("study_id")),
            "quest_id": _non_empty_text(status_payload.get("quest_id")),
            "quest_root": str(quest_root) if quest_root is not None else None,
            "quest_status": _non_empty_text(status_payload.get("quest_status")),
            "decision": _non_empty_text(status_payload.get("decision")),
            "reason": _non_empty_text(status_payload.get("reason")),
            "active_run_id": _payload_active_run_id(status_payload),
            "runtime_liveness_status": _payload_runtime_liveness_status(status_payload),
            "runtime_event_ref": dict(status_payload.get("runtime_event_ref") or {})
            if isinstance(status_payload.get("runtime_event_ref"), Mapping)
            else None,
            "runtime_escalation_ref": dict(status_payload.get("runtime_escalation_ref") or {})
            if isinstance(status_payload.get("runtime_escalation_ref"), Mapping)
            else None,
            "publication_supervisor_state": dict(status_payload.get("publication_supervisor_state") or {})
            if isinstance(status_payload.get("publication_supervisor_state"), Mapping)
            else None,
        },
        "artifacts": {
            "publication_eval_latest": _artifact_fingerprint(
                resolved_study_root / "artifacts" / "publication_eval" / "latest.json"
            ),
            "evaluation_summary_latest": _artifact_fingerprint(
                resolved_study_root / "artifacts" / "evaluation_summary" / "latest.json"
            ),
            "controller_decision_latest": _artifact_fingerprint(
                resolved_study_root / "artifacts" / "controller_decisions" / "latest.json"
            ),
            "runtime_supervision_latest": _runtime_supervision_artifact_fingerprint(
                resolved_study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
            ),
            "publication_gate_latest": _artifact_fingerprint(
                (quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
                if quest_root is not None
                else None
            ),
        },
    }
    canonical = json.dumps(watched_payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest(), watched_payload


def _build_outer_loop_wakeup_audit(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any]:
    input_fingerprint, watched_payload = _managed_outer_loop_wakeup_fingerprint(
        study_root=study_root,
        status_payload=status_payload,
    )
    latest_path = _runtime_watch_wakeup_latest_path(Path(study_root).expanduser().resolve())
    previous = _read_json_object(latest_path) or {}
    previous_outcome = _non_empty_text(previous.get("outcome"))
    previous_fingerprint = _non_empty_text(previous.get("input_fingerprint"))
    return {
        "schema_version": 1,
        "recorded_at": utc_now(),
        "study_id": _non_empty_text(status_payload.get("study_id")) or Path(study_root).name,
        "quest_id": _non_empty_text(status_payload.get("quest_id")),
        "input_fingerprint": input_fingerprint,
        "previous_input_fingerprint": previous_fingerprint,
        "previous_outcome": previous_outcome,
        "dispatch_cause": "input_unchanged" if previous_fingerprint == input_fingerprint else "input_changed",
        "watched_inputs": watched_payload,
        "latest_path": str(latest_path),
    }


def _write_outer_loop_wakeup_audit(*, study_root: Path, audit: Mapping[str, Any]) -> None:
    _write_json_object(_runtime_watch_wakeup_latest_path(Path(study_root).expanduser().resolve()), audit)


def _should_hard_auto_recover_managed_study(action_payload: dict[str, Any] | StudyRuntimeStatus) -> bool:
    payload = _managed_study_status_payload(action_payload)
    decision = _non_empty_text(payload.get("decision"))
    if decision == "resume":
        if _non_empty_text(payload.get("quest_status")) not in _HARD_AUTO_RECOVERY_QUEST_STATUSES:
            return False
        if _non_empty_text(payload.get("reason")) not in _HARD_AUTO_RECOVERY_REASONS:
            return False
        if _payload_active_run_id(payload) is not None:
            return False
        return _payload_runtime_liveness_status(payload) != "live"
    return runtime_supervision.is_auto_continuation_recovery_pending(payload)


def _serialize_managed_study_auto_recovery(
    *,
    preflight_payload: dict[str, Any] | StudyRuntimeStatus,
    applied_payload: dict[str, Any] | StudyRuntimeStatus,
    source: str,
) -> dict[str, Any]:
    preflight = _serialize_managed_study_action(preflight_payload)
    applied = _serialize_managed_study_action(applied_payload)
    return {
        "study_id": applied.get("study_id") or preflight.get("study_id"),
        "preflight_decision": preflight.get("decision"),
        "preflight_reason": preflight.get("reason"),
        "applied_decision": applied.get("decision"),
        "applied_reason": applied.get("reason"),
        "source": source,
    }


def _controller_decision_latest_matches_outer_loop_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> bool:
    latest_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    payload = _read_json_object(latest_path)
    if payload is None:
        return False
    record = StudyDecisionRecord.from_payload(payload)
    desired_charter_ref = StudyDecisionCharterRef.from_payload(dict(tick_request.get("charter_ref") or {})).to_dict()
    desired_publication_eval_ref = StudyDecisionPublicationEvalRef.from_payload(
        dict(tick_request.get("publication_eval_ref") or {})
    ).to_dict()
    desired_controller_actions = tuple(
        StudyDecisionControllerAction.from_payload(action).to_dict()
        for action in (tick_request.get("controller_actions") or [])
        if isinstance(action, dict)
    )
    desired_runtime_escalation_payload = status_payload.get("runtime_escalation_ref")
    desired_runtime_escalation_ref = (
        RuntimeEscalationRecordRef.from_payload(dict(desired_runtime_escalation_payload)).to_dict()
        if isinstance(desired_runtime_escalation_payload, dict)
        else None
    )
    if record.decision_type.value != _non_empty_text(tick_request.get("decision_type")):
        return False
    if record.requires_human_confirmation is not bool(tick_request.get("requires_human_confirmation")):
        return False
    if record.reason != (_non_empty_text(tick_request.get("reason")) or ""):
        return False
    if record.charter_ref.to_dict() != desired_charter_ref:
        return False
    if record.publication_eval_ref.to_dict() != desired_publication_eval_ref:
        return False
    if tuple(action.to_dict() for action in record.controller_actions) != desired_controller_actions:
        return False
    if desired_runtime_escalation_ref is None:
        return True
    return record.runtime_escalation_ref.to_dict() == desired_runtime_escalation_ref


def _quest_report_requests_managed_study_reroute(report: Mapping[str, Any] | None) -> bool:
    if not isinstance(report, Mapping):
        return False
    controllers = report.get("controllers")
    if not isinstance(controllers, Mapping):
        return False
    figure_loop_guard_report = controllers.get("figure_loop_guard")
    if not isinstance(figure_loop_guard_report, Mapping):
        return False
    if _non_empty_text(figure_loop_guard_report.get("action")) != "applied":
        return False
    return bool(figure_loop_guard_report.get("quest_stop_applied"))

