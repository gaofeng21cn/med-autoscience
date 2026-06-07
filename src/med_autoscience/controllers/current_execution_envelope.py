from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.runtime_control.owner_route_attempt_protocol import owner_reason_contract


ENVELOPE_KEYS = (
    "state_kind",
    "owner",
    "next_work_unit",
    "typed_blocker",
    "parked_state",
    "source_refs",
    "conflict_suppression_refs",
    "authority_boundary",
)
ALLOWED_STATE_KINDS = ("parked", "executable_owner_action", "running_provider_attempt", "typed_blocker")
EVIDENCE_ONLY_SURFACES = ("action_queue", "runtime_health", "no_op")
LIVE_ATTEMPT_SUPERSEDED_BLOCKERS = frozenset(
    {
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "quest_waiting_opl_runtime_owner_route",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
REASON_ONLY_TYPED_BLOCKERS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "medical_prose_review_request_rehydrate_required",
        "paper_progress_stall_current_missing",
        "paper_progress_stall_fingerprint_stale",
        "paper_progress_stall_terminal",
        "progress_first_owner_redrive_budget_exhausted",
        "typed_closeout_packet_required",
    }
)
AUTHORITY_BOUNDARY = {
    "surface_kind": "current_execution_envelope",
    "authority": "read_model_projection",
    "top_level_truth": "state_kind",
    "allowed_state_kinds": list(ALLOWED_STATE_KINDS),
    "evidence_only_surfaces": list(EVIDENCE_ONLY_SURFACES),
}


def build_current_execution_envelope(
    *,
    status: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    actions: Sequence[Mapping[str, Any]] | None = None,
    blocked_reason: str | None = None,
    next_owner: str | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    live_provider_attempt: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
    conflict_suppression_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    action_items = [dict(item) for item in actions or [] if isinstance(item, Mapping)]
    resolved_source_refs = _source_refs(status_payload, progress_payload, source_refs)
    resolved_suppression_refs = _conflict_suppression_refs(
        status=status_payload,
        progress=progress_payload,
        runtime_health=runtime_health,
        extra=conflict_suppression_refs,
    )
    resolved_typed_blocker = _typed_blocker(typed_blocker, blocked_reason=blocked_reason, owner=next_owner)
    running_attempt = _running_provider_attempt_state(
        live_provider_attempt=live_provider_attempt,
        runtime_health=runtime_health,
        owner=next_owner,
    )
    if running_attempt is not None:
        if _running_attempt_can_supersede_blocker(resolved_typed_blocker):
            return _envelope(
                state_kind="running_provider_attempt",
                owner=running_attempt["owner"],
                next_work_unit=running_attempt["next_work_unit"],
                typed_blocker=None,
                parked_state=None,
                source_refs=resolved_source_refs,
                conflict_suppression_refs=resolved_suppression_refs,
            )
        if resolved_typed_blocker is not None:
            return _envelope(
                state_kind="typed_blocker",
                owner=_text(resolved_typed_blocker.get("owner")) or _text(next_owner) or "med-autoscience",
                next_work_unit=None,
                typed_blocker=resolved_typed_blocker,
                parked_state=None,
                source_refs=resolved_source_refs,
                conflict_suppression_refs=resolved_suppression_refs,
            )
    action = _first_action(action_items)
    parked = _parked_state(status_payload, progress_payload)
    if parked is not None:
        if _parked_state_requires_human_resume(
            status=status_payload,
            progress=progress_payload,
            parked=parked,
        ):
            return _envelope(
                state_kind="parked",
                owner=parked["owner"],
                next_work_unit=None,
                typed_blocker=None,
                parked_state=parked["parked_state"],
                source_refs=resolved_source_refs,
                conflict_suppression_refs=resolved_suppression_refs,
            )
        if action is None:
            return _envelope(
                state_kind="parked",
                owner=parked["owner"],
                next_work_unit=None,
                typed_blocker=None,
                parked_state=parked["parked_state"],
                source_refs=resolved_source_refs,
                conflict_suppression_refs=resolved_suppression_refs,
            )
    if action is not None and _action_supersedes_typed_blocker(
        action=action,
        blocker=resolved_typed_blocker,
    ):
        return _envelope(
            state_kind="executable_owner_action",
            owner=_action_owner(action, next_owner=next_owner),
            next_work_unit=_next_work_unit(action),
            typed_blocker=None,
            parked_state=None,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    if resolved_typed_blocker is not None:
        return _envelope(
            state_kind="typed_blocker",
            owner=_text(resolved_typed_blocker.get("owner")) or _text(next_owner) or "med-autoscience",
            next_work_unit=None,
            typed_blocker=resolved_typed_blocker,
            parked_state=None,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    if action is not None:
        return _envelope(
            state_kind="executable_owner_action",
            owner=_action_owner(action, next_owner=next_owner),
            next_work_unit=_next_work_unit(action),
            typed_blocker=None,
            parked_state=None,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
    return _envelope(
        state_kind="typed_blocker",
        owner=_text(next_owner) or "med-autoscience",
        next_work_unit=None,
        typed_blocker=_minimal_blocker(blocked_reason or "current_execution_unresolved", owner=next_owner),
        parked_state=None,
        source_refs=resolved_source_refs,
        conflict_suppression_refs=resolved_suppression_refs,
    )


def build_current_execution_evidence(
    *,
    action_queue: Sequence[Mapping[str, Any]] | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    no_op: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = {
        "action_queue": [dict(item) for item in action_queue or [] if isinstance(item, Mapping)],
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, Mapping) else None,
        "no_op": _no_op_evidence(no_op),
    }
    for key, value in _mapping(extra).items():
        if key not in evidence:
            evidence[key] = value
    return evidence


def _envelope(
    *,
    state_kind: str,
    owner: str,
    next_work_unit: object,
    typed_blocker: dict[str, Any] | None,
    parked_state: str | None,
    source_refs: list[str],
    conflict_suppression_refs: list[str],
) -> dict[str, Any]:
    payload = {
        "state_kind": state_kind,
        "owner": owner,
        "next_work_unit": next_work_unit,
        "typed_blocker": typed_blocker,
        "parked_state": parked_state,
        "source_refs": source_refs,
        "conflict_suppression_refs": conflict_suppression_refs,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    return {key: payload[key] for key in ENVELOPE_KEYS}


def _parked_state(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, str] | None:
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("parked") is True:
        parked_state = _text(auto_parked.get("parked_state")) or _text(progress.get("parked_state"))
        if parked_state is not None:
            return {
                "parked_state": parked_state,
                "owner": _text(auto_parked.get("parked_owner")) or _text(progress.get("parked_owner")) or "user",
            }
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    if _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume":
        return {
            "parked_state": _text(progress.get("parked_state")) or "explicit_resume_pending",
            "owner": _text(progress.get("parked_owner")) or "user",
        }
    return None


def _parked_state_requires_human_resume(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    parked: Mapping[str, Any],
) -> bool:
    if _text(parked.get("parked_state")) == "explicit_resume_pending":
        return True
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("auto_execution_complete") is True:
        return True
    if auto_parked.get("awaiting_explicit_wakeup") is True:
        if _text(parked.get("parked_state")) == "waiting_user_decision":
            classification = _mapping(auto_parked.get("runtime_failure_classification"))
            return classification.get("requires_human_gate") is True
        return True
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    return _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume"


def _typed_blocker(
    typed_blocker: Mapping[str, Any] | None,
    *,
    blocked_reason: str | None,
    owner: str | None,
) -> dict[str, Any] | None:
    if isinstance(typed_blocker, Mapping) and typed_blocker:
        return dict(typed_blocker)
    text = _text(blocked_reason)
    if text is None:
        return None
    if not _reason_only_blocked_reason_is_typed_blocker(reason=text, owner=owner):
        return None
    return _minimal_blocker(text, owner=owner)


def _minimal_blocker(blocker_type: str, *, owner: str | None) -> dict[str, Any]:
    return {
        "blocker_type": blocker_type,
        "owner": _text(owner) or "med-autoscience",
    }


def _first_action(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    return actions[0] if actions else None


def _next_work_unit(action: Mapping[str, Any]) -> object:
    next_work_unit = action.get("next_work_unit")
    if isinstance(next_work_unit, Mapping):
        return dict(next_work_unit)
    text = _text(next_work_unit)
    if text is not None:
        return text
    for key in ("executable_work_unit", "controller_work_unit_id", "work_unit_id", "action_type"):
        if (value := _text(action.get(key))) is not None:
            return value
    return None


def _action_owner(action: Mapping[str, Any], *, next_owner: str | None) -> str:
    return (
        _text(action.get("owner"))
        or _text(action.get("recommended_owner"))
        or _text(action.get("next_owner"))
        or _text(next_owner)
        or "med-autoscience"
    )


def _running_provider_attempt_state(
    *,
    live_provider_attempt: Mapping[str, Any] | None,
    runtime_health: Mapping[str, Any] | None,
    owner: str | None,
) -> dict[str, Any] | None:
    attempt = _mapping(live_provider_attempt)
    if attempt.get("running_provider_attempt") is not True:
        return None
    health = _mapping(runtime_health)
    next_work_unit = (
        _text(attempt.get("work_unit_id"))
        or _text(attempt.get("next_work_unit"))
        or _text(health.get("work_unit_id"))
        or _text(attempt.get("action_type"))
        or _text(attempt.get("active_stage_attempt_id"))
        or _text(attempt.get("active_workflow_id"))
    )
    return {
        "owner": _text(owner) or "supervisor_only/live_provider_attempt",
        "next_work_unit": next_work_unit,
    }


def _running_attempt_can_supersede_blocker(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    return _text(payload.get("blocker_type")) in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS


def _action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    blocker_type = _text(payload.get("blocker_type"))
    if blocker_type != "medical_paper_readiness_not_ready":
        return False
    if _text(action.get("action_type")) == "complete_medical_paper_readiness_surface":
        return True
    return "complete_medical_paper_readiness_surface" in _text_items(action.get("allowed_actions"))


def _reason_only_blocked_reason_is_typed_blocker(*, reason: str, owner: str | None) -> bool:
    if reason in REASON_ONLY_TYPED_BLOCKERS:
        return True
    contract = owner_reason_contract(reason=reason, owner=owner)
    if contract.get("registered") is not True:
        return True
    return not any(_text(action) is not None for action in contract.get("allowed_actions") or [])


def _source_refs(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    source_refs: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in source_refs or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    refs.extend(_refs_from(_mapping(progress.get("refs"))))
    refs.extend(_refs_from(_mapping(status.get("refs"))))
    return sorted(dict.fromkeys(refs))


def _refs_from(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("controller_decision_path", "publication_eval_path", "runtime_status_summary_path"):
        if (ref := _text(value.get(key))) is not None:
            refs.append(ref)
    return refs


def _conflict_suppression_refs(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime_health: Mapping[str, Any] | None,
    extra: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in extra or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    health = _mapping(runtime_health) or _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    if (action := _text(health.get("canonical_runtime_action"))) is not None:
        refs.append(f"runtime_health:{action}")
    return sorted(dict.fromkeys(refs))


def _no_op_evidence(value: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [dict(value)]
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = [
    "ALLOWED_STATE_KINDS",
    "ENVELOPE_KEYS",
    "build_current_execution_envelope",
    "build_current_execution_evidence",
]
