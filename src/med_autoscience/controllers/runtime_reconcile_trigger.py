from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "runtime_reconcile_trigger_projection"
REQUEST_KIND = "runtime_supervisor_reconcile"
SAFE_CURRENT_ACTION = "safe_reconcile_ready"
STALE_RUNTIME_STATES = frozenset({"stale"})
STALE_WORKER_STATES = frozenset({"stale", "degraded"})
PARKED_REASONS = frozenset(
    {
        "publishability_stop_loss_recommended",
        "quest_parked_on_unchanged_finalize_state",
        "quest_waiting_for_explicit_wakeup_after_manual_hold",
        "quest_waiting_for_submission_metadata",
    }
)
AUTHORITY_FLAGS = {
    "quality_ready_authorized": False,
    "publication_ready_authorized": False,
    "submission_ready_authorized": False,
}


def build_runtime_reconcile_trigger_projection(
    *,
    status_payload: Mapping[str, Any],
    profile_ref: str | None,
    study_id: str,
    existing_fingerprints: Iterable[str] | None = None,
) -> dict[str, Any]:
    status = _mapping(status_payload)
    progress: dict[str, Any] = {}
    resolved_study_id = _text(study_id) or _text(status.get("study_id")) or "unknown-study"
    blocked_reasons = _blocked_reasons(
        status=status,
        progress=progress,
    )
    stale_signals = _stale_signals(status)
    if not stale_signals:
        blocked_reasons.append("runtime_session_not_stale")
    fingerprint = _dedupe_fingerprint(
        study_id=resolved_study_id,
        quest_id=_text(status.get("quest_id")),
        stale_signals=stale_signals,
    )
    duplicate = fingerprint in set(_string_items(existing_fingerprints))
    if duplicate:
        blocked_reasons.append("duplicate_reconcile_request")
    blocked_reasons = list(dict.fromkeys(blocked_reasons))
    safe_to_request = not blocked_reasons
    recommended_command = (
        _recommended_command(profile_ref=profile_ref, study_id=resolved_study_id)
        if safe_to_request
        else None
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "safe_to_request": safe_to_request,
        "request_kind": REQUEST_KIND,
        "recommended_command": recommended_command,
        "dedupe_fingerprint": fingerprint,
        "dedupe_state": "duplicate" if duplicate else "new",
        "blocked_reasons": blocked_reasons,
        "stale_signals": stale_signals,
        "authority": {
            "kind": "read_model_reconcile_request_projection",
            "writes_runtime": False,
            "writes_study_workspace": False,
            "writes_publication_truth": False,
            "writes_controller_decisions": False,
            "executes_reconcile": False,
        },
        "authority_flags": dict(AUTHORITY_FLAGS),
    }


def _blocked_reasons(*, status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    recovery_intent = _mapping(status.get("recovery_intent"))
    if _text(recovery_intent.get("current_action")) != SAFE_CURRENT_ACTION:
        reasons.append("recovery_intent_not_safe_reconcile_ready")
    if _human_gate_required(status):
        reasons.append("human_gate_required")
    if _completed_current_truth(status, progress):
        reasons.append("completed_truth")
    if _parked_current_truth(status, progress):
        reasons.append("parked_truth")
    if _retry_exhausted(status, progress):
        reasons.append("runtime_recovery_retry_budget_exhausted")
    return reasons


def _human_gate_required(status: Mapping[str, Any]) -> bool:
    if bool(status.get("needs_user_decision")) or bool(status.get("needs_physician_decision")):
        return True
    resume_contract = _mapping(_mapping(status.get("family_checkpoint_lineage")).get("resume_contract"))
    if resume_contract.get("human_gate_required") is True:
        return True
    interaction_arbitration = _mapping(status.get("interaction_arbitration"))
    if interaction_arbitration.get("requires_user_input") is True:
        return True
    pending = _mapping(status.get("pending_user_interaction"))
    if pending.get("blocking") is True and pending.get("expects_reply") is True:
        return True
    publication_supervisor_state = _mapping(status.get("publication_supervisor_state"))
    return _text(publication_supervisor_state.get("current_required_action")) == "human_confirmation_required"


def _completed_current_truth(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("decision")) == "completed":
        return True
    if _text(status.get("quest_status")) != "completed":
        return False
    contract = _mapping(status.get("study_completion_contract")) or _mapping(progress.get("study_completion_contract"))
    return contract.get("ready") is True and _text(contract.get("status")) == "resolved"


def _parked_current_truth(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _has_live_worker(status, progress):
        return False
    if _text(status.get("quest_status")) in {"waiting_for_user", "parked"}:
        return True
    macro_state = _mapping(status.get("study_macro_state")) or _mapping(progress.get("study_macro_state"))
    if _text(macro_state.get("writer_state")) == "parked" and _text(macro_state.get("reason")) in {
        "external_info",
        "stop_loss",
        "user_stop",
    }:
        return True
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("parked") is True:
        return True
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    if _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume":
        return True
    return _text(status.get("reason")) in PARKED_REASONS


def _has_live_worker(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("active_run_id")) or _text(progress.get("active_run_id")):
        return True
    supervision = _mapping(progress.get("supervision"))
    if _text(supervision.get("active_run_id")):
        return True
    liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(liveness.get("runtime_audit"))
    if _text(liveness.get("active_run_id")) or _text(runtime_audit.get("active_run_id")):
        return True
    return runtime_audit.get("worker_running") is True


def _retry_exhausted(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    reasons = set(_blocking_reasons(status, progress))
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    quest_status = _text(status.get("quest_status"))
    zero_budget_in_recovery_context = runtime_health.get("retry_budget_remaining") == 0 and (
        quest_status in {"active", "running"}
        or attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
        or canonical_runtime_action in {"recover_runtime", "probe_runtime", "relaunch_runtime", "external_supervisor_required"}
    )
    return (
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or attempt_state == "escalated"
        or zero_budget_in_recovery_context
    )


def _blocking_reasons(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    control_plane = _mapping(status.get("control_plane_snapshot"))
    progress_control = _mapping(progress.get("control_plane_snapshot"))
    return list(
        dict.fromkeys(
            [
                *_string_items(status.get("blocking_reasons")),
                *_string_items(runtime_health.get("blocking_reasons")),
                *_string_items(control_plane.get("blocking_reasons")),
                *_string_items(_mapping(control_plane.get("dispatch_gate")).get("blocking_reasons")),
                *_string_items(progress_control.get("blocking_reasons")),
                *_string_items(progress.get("current_blockers")),
            ]
        )
    )


def _stale_signals(status: Mapping[str, Any]) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    runtime_session = _mapping(status.get("runtime_session"))
    runtime_session_state = _text(runtime_session.get("freshness_state"))
    if runtime_session_state in STALE_RUNTIME_STATES:
        signals.append({"source": "runtime_session.freshness_state", "state": runtime_session_state})
    worker_state = _worker_state(status)
    if worker_state in STALE_WORKER_STATES:
        signals.append({"source": "worker_state", "state": worker_state})
    return signals


def _worker_state(status: Mapping[str, Any]) -> str | None:
    direct = _text(status.get("worker_state"))
    if direct is not None:
        return direct
    health = _mapping(status.get("runtime_health_snapshot"))
    liveness = _mapping(health.get("worker_liveness_state"))
    return _text(liveness.get("state"))


def _dedupe_fingerprint(
    *,
    study_id: str,
    quest_id: str | None,
    stale_signals: list[dict[str, str]],
) -> str:
    source = {
        "request_kind": REQUEST_KIND,
        "study_id": study_id,
        "quest_id": quest_id,
        "stale_signals": stale_signals,
    }
    encoded = json.dumps(source, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"{REQUEST_KIND}:{digest}"


def _recommended_command(*, profile_ref: str | None, study_id: str) -> str:
    profile_arg = _quote(profile_ref or "<profile>")
    study_arg = _quote(study_id)
    return (
        "uv run python -m med_autoscience.cli runtime-supervisor-reconcile "
        f"--profile {profile_arg} --studies {study_arg} --mode developer_apply_safe --dry-run"
    )


def _quote(value: str) -> str:
    if value and all(char.isalnum() or char in "/._:-" for char in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(item for raw in value if (item := _text(raw)) is not None))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_runtime_reconcile_trigger_projection",
]
