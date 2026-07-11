from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .human_gates import *  # noqa: F403

from med_autoscience.controllers.opl_runtime_refs import resolve_opl_runtime_refs


def _should_materialize_opl_runtime_owner_handoff_from_status(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
) -> bool:
    status_payload = status.to_dict()
    refs = resolve_opl_runtime_refs(status_payload)
    strict_live = refs.strict_live
    reason = str(status_payload.get("reason") or "").strip() or None
    study_id = str(status_payload.get("study_id") or "").strip() or None
    quest_id = str(status_payload.get("quest_id") or "").strip() or None
    quest_root = str(status_payload.get("quest_root") or "").strip() or None
    runtime_health_snapshot = status_payload.get("runtime_health_snapshot")
    if not isinstance(runtime_health_snapshot, dict):
        runtime_health_snapshot = {}
    runtime_health_action = str(runtime_health_snapshot.get("canonical_runtime_action") or "").strip() or None
    runtime_health_attempt_state = str(runtime_health_snapshot.get("attempt_state") or "").strip() or None
    retry_budget_remaining = runtime_health_snapshot.get("retry_budget_remaining")
    if runtime_health_action == "escalate_runtime" or (
        runtime_health_attempt_state == "escalated"
        and retry_budget_remaining == 0
    ):
        handoff_context = "escalated"
    elif runtime_health_action == "recover_runtime" or runtime_health_attempt_state == "recovering":
        handoff_context = "recovering"
    elif strict_live:
        handoff_context = "live"
    elif _opl_runtime_recovery_projection_needed(status_payload, refs=refs):
        handoff_context = "recovering"
    elif reason == "opl_stage_attempt_admission_required":
        handoff_context = "blocked"
    elif _opl_runtime_drop_detection_needed(status_payload, strict_live=strict_live):
        handoff_context = "degraded"
    else:
        return False
    latest_handoff_path = study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
    latest_handoff = _read_json_mapping(latest_handoff_path)
    if latest_handoff is None:
        return True
    latest_typed_blocker = latest_handoff.get("typed_blocker")
    if not isinstance(latest_typed_blocker, dict):
        latest_typed_blocker = {}
    latest_refs = latest_handoff.get("opl_current_control_state_ref")
    if not isinstance(latest_refs, dict):
        latest_refs = {}
    return any(
        (
            (str(latest_handoff.get("status") or "").strip() or None) != "handoff_required",
            latest_handoff.get("mas_materializes_runtime_supervision") is not False,
            latest_handoff.get("mas_runtime_read_model_retired") is not True,
            latest_handoff.get("provider_completion_is_domain_completion") is not False,
            latest_handoff.get("queue_succeeded_is_domain_completion") is not False,
            (str(latest_handoff.get("runtime_owner") or "").strip() or None) != "one-person-lab",
            (str(latest_handoff.get("domain_owner") or "").strip() or None) != "med-autoscience",
            (str(latest_handoff.get("study_id") or "").strip() or None) != study_id,
            (str(latest_handoff.get("quest_id") or "").strip() or None) != quest_id,
            (str(latest_handoff.get("quest_root") or "").strip() or None) != quest_root,
            (str(latest_handoff.get("reason") or "").strip() or None) != reason,
            latest_refs.get("required") is not True,
            (str(latest_refs.get("hydrate_from") or "").strip() or None) != "MAS DomainIntent / owner-route refs",
            (str(latest_typed_blocker.get("blocker_type") or "").strip() or None)
            != "opl_runtime_owner_handoff_required",
            (str(latest_typed_blocker.get("owner") or "").strip() or None) != "one-person-lab",
            (str(latest_typed_blocker.get("domain_owner") or "").strip() or None) != "med-autoscience",
            not handoff_context,
        )
    )


def _opl_runtime_recovery_projection_needed(
    status_payload: Mapping[str, Any],
    *,
    refs: Any,
) -> bool:
    if refs.strict_live:
        return False
    if _status_payload_human_gate_required_for_opl_runtime_ref(status_payload):
        return False
    quest_status = str(status_payload.get("quest_status") or "").strip()
    if quest_status not in {"running", "active"}:
        return False
    supervisor_tick_audit = status_payload.get("supervisor_tick_audit")
    supervisor_tick_status = (
        str(supervisor_tick_audit.get("status") or "").strip()
        if isinstance(supervisor_tick_audit, Mapping)
        else None
    )
    if supervisor_tick_status not in {"missing", "stale", "invalid"}:
        return False
    return refs.active_run_id is None


def _status_payload_human_gate_required_for_opl_runtime_ref(status_payload: Mapping[str, Any]) -> bool:
    interaction_arbitration = status_payload.get("interaction_arbitration")
    if isinstance(interaction_arbitration, Mapping) and bool(interaction_arbitration.get("requires_user_input")):
        return True
    publication_supervisor_state = status_payload.get("publication_supervisor_state")
    if isinstance(publication_supervisor_state, Mapping):
        current_required_action = str(publication_supervisor_state.get("current_required_action") or "").strip()
        return current_required_action == "human_confirmation_required"
    return False


def _opl_runtime_drop_detection_needed(status_payload: Mapping[str, Any], *, strict_live: bool) -> bool:
    if strict_live:
        return False
    decision = str(status_payload.get("decision") or "").strip()
    reason = str(status_payload.get("reason") or "").strip()
    quest_status = str(status_payload.get("quest_status") or "").strip()
    if reason in {
        "quest_marked_running_but_no_live_session",
        "running_quest_live_session_audit_failed",
        "resume_request_failed",
        "create_request_failed",
    }:
        return True
    if decision in {"create_and_start", "resume", "relaunch_stopped"}:
        return False
    return quest_status in {"running", "active"}


__all__ = [name for name in globals() if not name.startswith("__")]
