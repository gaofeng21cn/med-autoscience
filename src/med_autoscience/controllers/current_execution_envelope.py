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
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "quest_waiting_opl_runtime_owner_route",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS = frozenset(
    {
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "quest_marked_running_but_no_live_session",
        "quest_waiting_opl_runtime_owner_route",
        "runtime_recovery_not_authorized",
    }
)
MEDICAL_READINESS_BLOCKERS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
    }
)
PAPER_DELTA_READINESS_SUPERSEDING_ACTION_SOURCES = frozenset(
    {
        "domain_transition",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
    }
)
PROVIDER_ADMISSION_REPAIR_ACTIONS = frozenset(
    {
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }
)
PROVIDER_ADMISSION_AUTHORITIES = frozenset(
    {
        "mas_provider_admission_identity",
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
    stage_owner_answer_blocker = _stage_owner_answer_typed_blocker(progress_payload)
    running_attempt = _running_provider_attempt_state(
        live_provider_attempt=live_provider_attempt,
        runtime_health=runtime_health,
        owner=next_owner,
    )
    if running_attempt is not None and _running_attempt_invalidated_by_progress(progress_payload):
        running_attempt = None
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
    if stage_owner_answer_blocker is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        return _envelope(
            state_kind="typed_blocker",
            owner=_text(stage_owner_answer_blocker.get("owner")) or _text(next_owner) or "med-autoscience",
            next_work_unit=None,
            typed_blocker=stage_owner_answer_blocker,
            parked_state=None,
            source_refs=resolved_source_refs,
            conflict_suppression_refs=resolved_suppression_refs,
        )
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
        progress=progress_payload,
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
            return (
                classification.get("requires_human_gate") is True
                and _has_human_gate_authority_ref(status=status, progress=progress)
            )
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
    if _attempt_has_matching_terminal_closeout(attempt):
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


def _attempt_has_matching_terminal_closeout(attempt: Mapping[str, Any]) -> bool:
    terminal = _mapping(attempt.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _stage_attempt_id_from_handoff(attempt)
    terminal_attempt_id = _text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id is not None and active_attempt_id != terminal_attempt_id:
        return False
    status = _text(terminal.get("status"))
    if status in {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }:
        return True
    return _text(terminal.get("source_path")) is not None and _text(terminal.get("record_path")) is not None


def _stage_attempt_id_from_handoff(handoff: Mapping[str, Any]) -> str | None:
    if text := _text(handoff.get("active_stage_attempt_id")):
        return text
    active_run_id = _text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _running_attempt_invalidated_by_progress(progress: Mapping[str, Any]) -> bool:
    runtime_refs = _mapping(progress.get("opl_runtime_refs"))
    if runtime_refs.get("strict_live") is not False:
        return False
    if _text(runtime_refs.get("active_run_id")) is not None:
        return False
    auto_parked = _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("superseded_by_current_owner_action") is not True:
        return False
    return _text(runtime_refs.get("runtime_liveness_status")) in {
        "unknown",
        "none",
        "not_live",
        "stale",
        "parked",
    }


def _running_attempt_can_supersede_blocker(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    return _text(payload.get("blocker_type")) in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS


def _stage_owner_answer_typed_blocker(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = _stage_current_owner_delta(progress)
    if not _stage_delta_is_typed_blocker_owner_answer(progress=progress, delta=delta):
        return None
    reason = (
        _text(delta.get("reason"))
        or _text(delta.get("blocker_id"))
        or _text(delta.get("blocker_type"))
        or "typed_blocker"
    )
    source_ref = _text(delta.get("latest_owner_answer_ref")) or _text(delta.get("source_ref"))
    work_unit = _text(delta.get("action")) or _text(delta.get("action_type"))
    return {
        "blocker_type": reason,
        "blocker_id": reason,
        "owner": _text(delta.get("owner")) or "MedAutoScience",
        "work_unit_id": work_unit,
        "source_ref": source_ref,
        "latest_owner_answer_ref": source_ref,
        "latest_owner_answer_kind": "typed_blocker",
    }


def _stage_delta_is_typed_blocker_owner_answer(
    *,
    progress: Mapping[str, Any],
    delta: Mapping[str, Any],
) -> bool:
    hard_gate = _mapping(delta.get("hard_gate"))
    if _text(hard_gate.get("state")) == "domain_owner_answer_recorded":
        answer_kind = (
            _text(hard_gate.get("owner_answer_kind"))
            or _text(delta.get("latest_owner_answer_kind"))
            or _text(delta.get("source_kind"))
        )
        return answer_kind == "typed_blocker"
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return (
        _text(stage_run_kernel.get("status")) == "TypedBlocked"
        and _text(delta.get("source_kind")) == "typed_blocker"
        and _text(delta.get("source_ref")) is not None
    )


def _stage_current_owner_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    delta = _mapping(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return _mapping(stage_run_kernel.get("current_owner_delta"))


def _action_supersedes_stage_owner_answer(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    payload = _mapping(action)
    if not payload:
        return False
    if _provider_admission_repair_action_supersedes_readiness_blocker(payload):
        return True
    return _paper_delta_domain_transition_supersedes_readiness_blocker(
        action=payload,
        progress=progress,
    )


def _action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    blocker_type = _text(payload.get("blocker_type"))
    if blocker_type in CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS:
        return (
            _action_is_stage_current_owner_delta(action)
            or _provider_admission_repair_action_supersedes_readiness_blocker(action)
            or _paper_delta_domain_transition_supersedes_readiness_blocker(
                action=action,
                progress=_mapping(progress),
            )
        )
    if blocker_type not in MEDICAL_READINESS_BLOCKERS:
        return False
    if _text(action.get("action_type")) == "complete_medical_paper_readiness_surface":
        return True
    if "complete_medical_paper_readiness_surface" in _text_items(action.get("allowed_actions")):
        return True
    if _provider_admission_repair_action_supersedes_readiness_blocker(action):
        return True
    return _paper_delta_domain_transition_supersedes_readiness_blocker(
        action=action,
        progress=_mapping(progress),
    )


def _action_is_stage_current_owner_delta(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source_surface"))
        or _text(action.get("source"))
    ) == "stage_kernel_projection.current_owner_delta"


def _paper_delta_domain_transition_supersedes_readiness_blocker(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    progress_first = _mapping(progress.get("progress_first_sprint_state"))
    paper_delta = _mapping(progress.get("paper_progress_delta"))
    if progress_first.get("paper_progress_delta_counted") is not True and _delta_count(paper_delta) <= 0:
        return False
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if action_source not in PAPER_DELTA_READINESS_SUPERSEDING_ACTION_SOURCES:
        return False
    if _text(action.get("action_type")) not in {
        "request_opl_stage_attempt",
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }:
        return False
    return _text(action.get("work_unit_id")) != "complete_medical_paper_readiness_surface"


def _provider_admission_repair_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type"))
    action_types = {action_type, *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection(PROVIDER_ADMISSION_REPAIR_ACTIONS):
        return False
    if _text(action.get("work_unit_id")) == "complete_medical_paper_readiness_surface":
        return False
    if _text(action.get("next_work_unit")) == "complete_medical_paper_readiness_surface":
        return False
    authority = _text(action.get("authority"))
    if authority in PROVIDER_ADMISSION_AUTHORITIES:
        return True
    action_id = _text(action.get("action_id"))
    if action_id is not None and action_id.startswith("provider-admission::"):
        return True
    for key in ("action_fingerprint", "work_unit_fingerprint", "fingerprint"):
        text = _text(action.get(key))
        if text is not None and text.startswith("study-progress-current-owner-ticket::"):
            return True
    return False


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


def _has_human_gate_authority_ref(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    for surface in (
        status,
        progress,
        _mapping(status.get("auto_runtime_parked")),
        _mapping(progress.get("auto_runtime_parked")),
        _mapping(status.get("refs")),
        _mapping(progress.get("refs")),
    ):
        if _surface_has_human_gate_ref(surface):
            return True
    return False


def _surface_has_human_gate_ref(surface: Mapping[str, Any]) -> bool:
    for key in (
        "human_gate_ref",
        "human_gate_resume_ref",
        "human_gate_or_resume_ref",
        "human_gate_authority_ref",
        "decision_ref",
        "receipt_ref",
        "source_artifact_path",
    ):
        if _text(surface.get(key)) is not None:
            return True
    for key in (
        "human_gate_refs",
        "human_gate_resume_refs",
        "human_gate_or_resume_refs",
        "human_gate_authority_refs",
    ):
        if _text_items(surface.get(key)):
            return True
    for gate in surface.get("family_human_gates") or []:
        gate_payload = _mapping(gate)
        if _surface_has_human_gate_ref(gate_payload):
            return True
        for evidence in gate_payload.get("evidence_refs") or []:
            if _text(_mapping(evidence).get("ref")) is not None:
                return True
    return False


def _refs_from(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("controller_decision_path", "publication_eval_path", "runtime_status_summary_path"):
        if (ref := _text(value.get(key))) is not None:
            refs.append(ref)
    return refs


def _delta_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("count") or 0)
    except (TypeError, ValueError):
        return 0


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
