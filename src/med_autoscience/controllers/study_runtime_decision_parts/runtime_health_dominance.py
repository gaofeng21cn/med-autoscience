from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from med_autoscience.controllers import runtime_health_kernel
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeDecision,
    StudyRuntimeReason,
    StudyRuntimeAuditStatus,
    ProgressProjectionStatus,
    _LIVE_QUEST_STATUSES,
)


_OPL_STAGE_ATTEMPT_PREFIX = "opl-stage-attempt://"
_OPL_RECOVERY_IDENTITY_KEYS = (
    "active_run_id",
    "active_stage_attempt_id",
    "stage_attempt_id",
    "opl_stage_attempt_id",
    "active_workflow_id",
    "provider_attempt_ref",
    "opl_stage_run_ref",
)
_TRUSTED_OPL_RUNTIME_READBACK_SURFACE_KINDS = frozenset(
    {
        "opl_current_control_state_handoff",
        "opl_current_control_state_study_handoff",
        "opl_current_control_state_provider_attempt_handoff",
        "opl_stage_run_readback",
        "opl_terminal_stage_log",
    }
)


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _latest_runtime_health_snapshot(study_root: Path) -> dict[str, object]:
    path = runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _runtime_health_requires_explicit_resume(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    try:
        if status.runtime_liveness_audit_record.status is StudyRuntimeAuditStatus.LIVE:
            return False
    except KeyError:
        pass
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    if continuation_state.active_run_id is not None:
        return False
    if continuation_state.continuation_policy != "wait_for_user_or_resume":
        return False
    snapshot = _latest_runtime_health_snapshot(study_root)
    if snapshot.get("study_id") != study_id or snapshot.get("quest_id") != quest_id:
        return False
    return (
        snapshot.get("canonical_runtime_action") == "await_explicit_resume"
        and snapshot.get("failure_reason") == "quest_stopped_requires_explicit_rerun"
    )


def _runtime_health_requires_live_recovery(
    *,
    status: ProgressProjectionStatus,
    runtime_health_snapshot: dict[str, object],
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    if runtime_health_snapshot.get("canonical_runtime_action") != "recover_runtime":
        return False
    worker_liveness_state = runtime_health_snapshot.get("worker_liveness_state")
    worker_state = (
        str(worker_liveness_state.get("state") or "").strip()
        if isinstance(worker_liveness_state, dict)
        else ""
    )
    return worker_state == "activity_timeout"


def _identity_tokens(value: object) -> set[str]:
    text = _text(value)
    if text is None:
        return set()
    return _identity_tokens_for_text(text, stage_attempt_alias=False)


def _stage_attempt_identity_tokens(value: object) -> set[str]:
    text = _text(value)
    if text is None:
        return set()
    return _identity_tokens_for_text(text, stage_attempt_alias=True)


def _identity_tokens_for_text(text: str, *, stage_attempt_alias: bool) -> set[str]:
    tokens = {text}
    if text.startswith(_OPL_STAGE_ATTEMPT_PREFIX):
        suffix = text[len(_OPL_STAGE_ATTEMPT_PREFIX) :].strip()
        if suffix:
            tokens.add(suffix)
    elif stage_attempt_alias and "://" not in text:
        tokens.add(f"{_OPL_STAGE_ATTEMPT_PREFIX}{text}")
    return tokens


def _identity_tokens_from_payload(payload: Mapping[str, object]) -> set[str]:
    tokens: set[str] = set()
    for key in _OPL_RECOVERY_IDENTITY_KEYS:
        identity = (
            _stage_attempt_identity_tokens(payload.get(key))
            if key in {"active_stage_attempt_id", "stage_attempt_id", "opl_stage_attempt_id"}
            else _identity_tokens(payload.get(key))
        )
        tokens.update(identity)
    runtime_liveness_audit = _mapping(payload.get("runtime_liveness_audit"))
    if runtime_liveness_audit:
        tokens.update(_identity_tokens_from_payload(runtime_liveness_audit))
    runtime_audit = _mapping(payload.get("runtime_audit"))
    if runtime_audit:
        tokens.update(_identity_tokens_from_payload(runtime_audit))
    worker_liveness = _mapping(payload.get("worker_liveness_state"))
    if worker_liveness:
        tokens.update(_identity_tokens_from_payload(worker_liveness))
    return tokens


def _runtime_health_recovery_identity_tokens(
    *,
    status_payload: Mapping[str, object],
    runtime_health_snapshot: Mapping[str, object],
) -> set[str]:
    tokens = set()
    tokens.update(_identity_tokens(runtime_health_snapshot.get("active_run_id")))
    tokens.update(_identity_tokens_from_payload(_mapping(runtime_health_snapshot.get("worker_liveness_state"))))
    if tokens:
        return tokens
    tokens.update(_identity_tokens(status_payload.get("active_run_id")))
    tokens.update(_identity_tokens_from_payload(_mapping(status_payload.get("runtime_liveness_audit"))))
    return tokens


def _trusted_opl_runtime_readback(payload: Mapping[str, object]) -> bool:
    if _text(payload.get("surface_kind")) in _TRUSTED_OPL_RUNTIME_READBACK_SURFACE_KINDS:
        return True
    return (
        _text(payload.get("source")) == "opl_current_control_state_provider_attempt"
        and payload.get("running_provider_attempt") is True
    )


def _collect_identity_bound_opl_readback_tokens(
    payload: Mapping[str, object],
    *,
    source: str,
) -> tuple[set[str], list[str]]:
    tokens: set[str] = set()
    sources: list[str] = []
    if _trusted_opl_runtime_readback(payload):
        payload_tokens = _identity_tokens_from_payload(payload)
        if payload_tokens:
            tokens.update(payload_tokens)
            sources.append(source)
    for nested_key in (
        "opl_lifecycle_readback",
        "opl_current_control_state",
        "current_control_state",
        "stage_run_readback",
        "latest_terminal_stage_log",
    ):
        nested = _mapping(payload.get(nested_key))
        if not nested:
            continue
        nested_tokens, nested_sources = _collect_identity_bound_opl_readback_tokens(
            nested,
            source=f"{source}.{nested_key}",
        )
        tokens.update(nested_tokens)
        sources.extend(nested_sources)
    return tokens, sources


def _runtime_health_recovery_authorization_details(
    *,
    status: ProgressProjectionStatus,
    runtime_health_snapshot: Mapping[str, object],
) -> dict[str, object]:
    if runtime_health_snapshot.get("authority") is True:
        return {
            "authorized": False,
            "suppressed_reason": "runtime_health_snapshot_authority_forbidden",
            "required_runtime_identity": [],
            "readback_runtime_identities": [],
            "matched_runtime_identity": [],
            "readback_sources": [],
        }
    status_payload = status.to_dict()
    required_tokens = _runtime_health_recovery_identity_tokens(
        status_payload=status_payload,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    readback_tokens: set[str] = set()
    readback_sources: list[str] = []
    for source, payload in (
        ("runtime_liveness_audit", _mapping(status_payload.get("runtime_liveness_audit"))),
        (
            "runtime_liveness_audit.runtime_audit",
            _mapping(_mapping(status_payload.get("runtime_liveness_audit")).get("runtime_audit")),
        ),
        ("opl_current_control_state", _mapping(status_payload.get("opl_current_control_state"))),
        ("current_control_state", _mapping(status_payload.get("current_control_state"))),
        ("opl_lifecycle_readback", _mapping(status_payload.get("opl_lifecycle_readback"))),
        ("stage_run_readback", _mapping(status_payload.get("stage_run_readback"))),
        ("latest_terminal_stage_log", _mapping(status_payload.get("latest_terminal_stage_log"))),
    ):
        if not payload:
            continue
        tokens, sources = _collect_identity_bound_opl_readback_tokens(payload, source=source)
        readback_tokens.update(tokens)
        readback_sources.extend(sources)
    matched_tokens = sorted(required_tokens & readback_tokens)
    return {
        "authorized": bool(required_tokens and matched_tokens),
        "suppressed_reason": (
            None
            if required_tokens and matched_tokens
            else "opl_runtime_readback_required_for_runtime_health_decision"
        ),
        "required_runtime_identity": sorted(required_tokens),
        "readback_runtime_identities": sorted(readback_tokens),
        "matched_runtime_identity": matched_tokens,
        "readback_sources": sorted(dict.fromkeys(readback_sources)),
    }


def _record_runtime_health_decision_gate(
    *,
    status: ProgressProjectionStatus,
    runtime_health_snapshot: Mapping[str, object],
    decision_authorized: bool,
    authorization_details: Mapping[str, object] | None = None,
) -> None:
    details = _mapping(authorization_details)
    suppressed_reason = _text(details.get("suppressed_reason"))
    status.extras["runtime_health_decision_gate"] = {
        "surface_kind": "runtime_health_diagnostic_consumer_gate",
        "runtime_owner": "one-person-lab",
        "mas_role": "read_only_diagnostic_consumer",
        "decision_authorized": decision_authorized,
        "decision_source": "opl_runtime_readback" if decision_authorized else None,
        "suppressed_reason": (
            None
            if decision_authorized
            else suppressed_reason or "opl_runtime_readback_required_for_runtime_health_decision"
        ),
        "identity_bound_opl_readback_required": True,
        "required_runtime_identity": list(details.get("required_runtime_identity") or []),
        "readback_runtime_identities": list(details.get("readback_runtime_identities") or []),
        "matched_runtime_identity": list(details.get("matched_runtime_identity") or []),
        "readback_sources": list(details.get("readback_sources") or []),
        "unbound_opl_ref_can_authorize_decision": False,
        "runtime_health_snapshot_authority": runtime_health_snapshot.get("authority") is True,
        "runtime_health_hint_only": runtime_health_snapshot.get("diagnostic_only") is True,
        "canonical_runtime_action_hint": runtime_health_snapshot.get("canonical_runtime_action"),
        "worker_liveness_state_hint": dict(_mapping(runtime_health_snapshot.get("worker_liveness_state"))),
        "can_generate_next_action_authority": False,
        "can_authorize_running_progress": False,
        "can_authorize_runtime_currentness": False,
    }


def _record_autonomy_slo_status_if_present(*, status: ProgressProjectionStatus, study_root: Path) -> None:
    from med_autoscience.controllers import autonomy_ai_doctor

    payload = autonomy_ai_doctor.read_latest_slo_status(study_root=study_root)
    if isinstance(payload, dict):
        status.extras["autonomy_slo"] = dict(payload)


def _derive_runtime_health_snapshot_for_status(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
    recorded_at: str,
) -> dict[str, object]:
    return runtime_health_kernel.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        status_payload=status.to_dict(),
        recorded_at=recorded_at,
    )


def _record_runtime_recovery_lifecycle_if_required(status: ProgressProjectionStatus) -> None:
    reason = status.reason.value if status.reason is not None else ""
    decision = status.decision.value if status.decision is not None else ""
    if reason not in {
        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION.value,
        StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE.value,
        StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED.value,
        StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED.value,
    }:
        return
    runtime_liveness_audit = (
        dict(status.extras.get("runtime_liveness_audit") or {})
        if isinstance(status.extras.get("runtime_liveness_audit"), dict)
        else {}
    )
    active_run_id = str(runtime_liveness_audit.get("active_run_id") or "").strip() or None
    if decision == StudyRuntimeDecision.RESUME.value:
        state = "recovering"
        recent_recovery_action = "resume"
        recovery_attempt_count = 1
        next_check_reason = "confirm_recovered_live_session"
    else:
        state = "parked_requires_resume"
        recent_recovery_action = (
            "enable_auto_resume"
            if reason == StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED.value
            else "inspect_runtime_liveness"
        )
        recovery_attempt_count = 0
        next_check_reason = "recover_runtime_audit_then_resume"
    next_check_after_seconds = 300
    status.extras["runtime_recovery_lifecycle"] = {
        "state": state,
        "reason": reason,
        "decision": decision,
        "runtime_liveness_status": str(runtime_liveness_audit.get("status") or "").strip() or None,
        "active_run_id": active_run_id,
        "recovery_attempt_count": recovery_attempt_count,
        "recent_recovery_action": recent_recovery_action,
        "next_check_reason": next_check_reason,
        "next_check_after_seconds": next_check_after_seconds,
        "next_check_at": (datetime.now(timezone.utc) + timedelta(seconds=next_check_after_seconds))
        .replace(microsecond=0)
        .isoformat(),
    }


def _record_runtime_health_dominance(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
    recorded_at: str,
) -> None:
    _record_autonomy_slo_status_if_present(status=status, study_root=study_root)
    runtime_health_snapshot = _derive_runtime_health_snapshot_for_status(
        status=status,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        recorded_at=recorded_at,
    )
    if _runtime_health_requires_live_recovery(status=status, runtime_health_snapshot=runtime_health_snapshot):
        authorization_details = _runtime_health_recovery_authorization_details(
            status=status,
            runtime_health_snapshot=runtime_health_snapshot,
        )
        decision_authorized = authorization_details["authorized"] is True
        _record_runtime_health_decision_gate(
            status=status,
            runtime_health_snapshot=runtime_health_snapshot,
            decision_authorized=decision_authorized,
            authorization_details=authorization_details,
        )
        try:
            runtime_liveness = status.runtime_liveness_audit_record
        except KeyError:
            runtime_liveness = None
        if (
            decision_authorized
            and (runtime_liveness is None or runtime_liveness.status is not StudyRuntimeAuditStatus.LIVE)
        ):
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE,
            )
            _record_runtime_recovery_lifecycle_if_required(status)
        runtime_health_snapshot = _derive_runtime_health_snapshot_for_status(
            status=status,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
            recorded_at=recorded_at,
    )
    status.extras["runtime_health_snapshot"] = runtime_health_snapshot
    status.extras["runtime_health_epoch"] = runtime_health_snapshot.get("runtime_health_epoch")


__all__ = [name for name in globals() if not name.startswith("__")]
