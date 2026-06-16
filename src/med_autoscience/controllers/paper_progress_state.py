from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection import (
    current_owner_handoff_action,
    current_owner_route_back_checklist,
)


PUBLIC_STATES = frozenset(
    {
        "progressing",
        "opl_stage_attempt_admission_required",
        "blocked_controller_route",
        "awaiting_callable_owner",
        "awaiting_human",
        "downstream_only",
        "terminal_delivered",
    }
)

PAPER_PROGRESS_STATE_SURFACE = "paper_progress_state"
PAPER_PROGRESS_STATE_READ_MODEL = "paper_progress_state_read_model"

_RUNTIME_RETRY_EXHAUSTED = "runtime_recovery_retry_budget_exhausted"
_DOWNSTREAM_ONLY = "publication_supervisor_state.bundle_tasks_downstream_only"


def build_paper_progress_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    macro_state = _study_macro_state(payload)
    details = _mapping(macro_state.get("details"))
    paper_facing_progress_slo = _paper_facing_progress_slo(payload)
    visible_paper_progress = bool(paper_facing_progress_slo["visible_as_progressing"])
    visible_progress = visible_paper_progress or _generic_artifact_delta_visible(payload)
    actual_write_active = _actual_write_active(
        payload,
        visible_progress=visible_progress,
    )
    package_delivered = _package_delivered(payload, details)
    meaningful_artifact_delta = _meaningful_artifact_delta(
        payload,
        visible_progress=visible_progress,
    )
    next_owner = _next_owner(payload, details)
    requires_user_input = _requires_user_input(payload)
    blocking_reasons = _blocking_reasons(payload)
    state = _paper_state(
        payload=payload,
        actual_write_active=actual_write_active,
        package_delivered=package_delivered,
        meaningful_artifact_delta=meaningful_artifact_delta,
        next_owner=next_owner,
        requires_user_input=requires_user_input,
        blocking_reasons=blocking_reasons,
    )
    why_not_progressing = _why_not_progressing(
        state=state,
        payload=payload,
        actual_write_active=actual_write_active,
        package_delivered=package_delivered,
        meaningful_artifact_delta=meaningful_artifact_delta,
        next_owner=next_owner,
        blocking_reasons=blocking_reasons,
    )
    handoff_action = current_owner_handoff_action(payload)
    stage_closeout_progress = _stage_closeout_progress(payload, handoff_action=handoff_action)
    return {
        "surface": PAPER_PROGRESS_STATE_SURFACE,
        "read_model": PAPER_PROGRESS_STATE_READ_MODEL,
        "schema_version": 1,
        "study_id": _text(payload.get("study_id")),
        "quest_id": _text(payload.get("quest_id")),
        "state": state,
        "actual_write_active": actual_write_active,
        "package_delivered": package_delivered,
        "meaningful_artifact_delta": meaningful_artifact_delta,
        "paper_facing_progress_slo": paper_facing_progress_slo,
        "next_owner": next_owner,
        "requires_user_input": requires_user_input,
        "why_not_progressing": why_not_progressing,
        "stage_closeout_progress": stage_closeout_progress,
        "route_back_checklist": current_owner_route_back_checklist(payload, handoff_action=handoff_action),
        "safe_reconcile_command": _safe_reconcile_command(payload),
    }


def _paper_state(
    *,
    payload: Mapping[str, Any],
    actual_write_active: bool,
    package_delivered: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
    requires_user_input: bool,
    blocking_reasons: list[str],
) -> str:
    if requires_user_input:
        return "awaiting_human"
    if _live_provider_attempt(payload) and actual_write_active and meaningful_artifact_delta:
        return "progressing"
    same_line_reactivation = _same_line_reactivation_active(payload)
    if _opl_stage_attempt_admission_owner(payload, next_owner) and not _route_authorization_blocked(payload):
        return "opl_stage_attempt_admission_required"
    if (
        _RUNTIME_RETRY_EXHAUSTED in blocking_reasons
        and _opl_stage_attempt_admission_owner(payload, next_owner)
        and not _route_authorization_blocked(payload)
    ):
        return "opl_stage_attempt_admission_required"
    if _controller_route_blocked(payload, blocking_reasons):
        return "blocked_controller_route"
    if _owner_callable_surface_missing(payload, next_owner):
        return "awaiting_callable_owner"
    if _is_downstream_only(payload, blocking_reasons):
        return "downstream_only"
    if package_delivered and not same_line_reactivation:
        return "terminal_delivered"
    if actual_write_active and meaningful_artifact_delta:
        return "progressing"
    if next_owner:
        return "awaiting_callable_owner"
    return "blocked_controller_route"


_PAPER_FACING_DELTA_CLASSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("canonical_manuscript", ("paper/draft.md", "paper/manuscript.md", "paper/build/review_manuscript.md")),
    ("figure_table", ("paper/figures/", "paper/tables/", "figures/", "tables/")),
    ("claim_evidence", ("paper/claim_evidence_map.json", "paper/evidence_ledger.json")),
    ("review_ledger", ("paper/review/", "review_ledger")),
    ("gate_replay", ("artifacts/controller/gate_replay_requests/", "gate_replay")),
    ("ai_reviewer_request", ("artifacts/supervision/requests/ai_reviewer/", "ai_reviewer/latest.json")),
    ("typed_blocker", ("typed-blocker:", "typed_blocker", "typed-blocker")),
)


def _paper_facing_progress_slo(payload: Mapping[str, Any]) -> dict[str, Any]:
    changed_refs = _paper_delta_changed_refs(payload)
    satisfied: list[str] = []
    for delta_class, markers in _PAPER_FACING_DELTA_CLASSES:
        if any(marker in ref for marker in markers for ref in changed_refs):
            satisfied.append(delta_class)
    missing = [delta_class for delta_class, _markers in _PAPER_FACING_DELTA_CLASSES if delta_class not in satisfied]
    return {
        "surface_kind": "paper_facing_progress_slo",
        "visible_as_progressing": bool(satisfied),
        "satisfied_delta_classes": satisfied,
        "missing_required_delta_classes": missing,
        "changed_refs": changed_refs,
    }


def _paper_delta_changed_refs(payload: Mapping[str, Any]) -> list[str]:
    progress_freshness = _mapping(payload.get("progress_freshness"))
    artifact_delta = _mapping(progress_freshness.get("meaningful_artifact_delta_freshness"))
    refs: list[str] = []
    repair_progress = _mapping(payload.get("repair_progress_projection"))
    for item in _mapping_items(repair_progress.get("changed_artifact_refs")):
        if text := _text(item.get("path")):
            refs.append(text)
    refs.extend(_string_items(_mapping(payload.get("paper_progress_delta")).get("refs")))
    if _text(artifact_delta.get("status")) == "fresh":
        refs.extend(_string_items(artifact_delta.get("changed_refs")))
        refs.extend(_string_items(artifact_delta.get("evidence_refs")))
    scan_delta = _mapping(payload.get("artifact_delta"))
    refs.extend(_string_items(scan_delta.get("changed_refs")))
    refs.extend(_string_items(scan_delta.get("evidence_refs")))
    stage_log = _mapping(_mapping(payload.get("latest_terminal_stage_log")).get("paper_stage_log"))
    refs.extend(_string_items(stage_log.get("changed_paper_surfaces")))
    refs.extend(_string_items(stage_log.get("changed_stage_surfaces")))
    return _dedupe(ref for ref in refs if _paper_delta_ref_is_current_truth(ref))


def _paper_delta_ref_is_current_truth(ref: str) -> bool:
    text = ref.strip()
    if not text:
        return False
    normalized = text.replace("\\", "/")
    if "/artifacts/stage_outputs/_body_authority/" in normalized or normalized.startswith(
        "artifacts/stage_outputs/_body_authority/"
    ):
        return False
    if "/runtime/quests/" in normalized:
        return False
    if "/archive/" in normalized or "/_archive/" in normalized:
        return False
    return True


def _stage_closeout_progress(
    payload: Mapping[str, Any],
    *,
    handoff_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action = _mapping(handoff_action)
    deliverable_delta = _mapping(action.get("deliverable_progress_delta"))
    paper_delta = _mapping(action.get("paper_progress_delta"))
    platform_delta = _mapping(action.get("platform_repair_delta"))
    classification = _text(action.get("progress_delta_classification"))
    changed_paper_surfaces = _string_items(action.get("changed_paper_surfaces"))
    changed_stage_surfaces = _string_items(action.get("changed_stage_surfaces"))
    paper_refs = _paper_delta_changed_refs(payload)
    return {
        "surface_kind": "paper_progress_stage_closeout_projection",
        "classification": classification,
        "paper_facing_delta_present": _delta_count(deliverable_delta) > 0
        or _delta_count(paper_delta) > 0
        or bool(changed_paper_surfaces)
        or bool(paper_refs),
        "runtime_closeout_only": classification == "platform_repair"
        or (_delta_count(platform_delta) > 0 and _delta_count(deliverable_delta) == 0 and not changed_paper_surfaces),
        "deliverable_progress_delta": deliverable_delta,
        "paper_progress_delta": paper_delta,
        "platform_repair_delta": platform_delta,
        "changed_paper_surfaces": changed_paper_surfaces,
        "changed_stage_surfaces": changed_stage_surfaces,
        "paper_delta_refs": paper_refs,
    }


def _delta_count(value: Mapping[str, Any]) -> int:
    count = value.get("count")
    if isinstance(count, bool):
        return 0
    if isinstance(count, int):
        return count
    return 0


def _actual_write_active(payload: Mapping[str, Any], *, visible_progress: bool) -> bool:
    macro_state = _study_macro_state(payload)
    writer_state = _text(macro_state.get("writer_state"))
    if _canonical_typed_blocker_blocks_liveness(payload):
        return False
    if writer_state != "live" and not _live_provider_attempt(payload):
        return False
    if not visible_progress:
        return False
    return bool(
        _text(_mapping(macro_state.get("details")).get("active_run_id"))
        or _text(payload.get("active_run_id"))
        or _text(_mapping(payload.get("supervision")).get("active_run_id"))
        or _provider_attempt_run_id(payload)
    )


def _live_provider_attempt(payload: Mapping[str, Any]) -> bool:
    if _canonical_typed_blocker_blocks_liveness(payload):
        return False
    runtime_liveness = _mapping(payload.get("runtime_liveness_audit"))
    if runtime_liveness.get("running_provider_attempt") is True:
        return True
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    if handoff.get("running_provider_attempt") is True:
        return True
    provider_status = _text(_mapping(handoff.get("runtime_health")).get("health_status"))
    if provider_status == "running" and _text(handoff.get("active_stage_attempt_id")) is not None:
        return True
    execution = _mapping(payload.get("current_execution_evidence"))
    execution_handoff = _mapping(execution.get("opl_current_control_state_handoff"))
    if execution_handoff.get("running_provider_attempt") is True:
        return True
    return False


def _canonical_typed_blocker_blocks_liveness(payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping(payload.get("current_work_unit"))
    if _text(current_work_unit.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return True
    execution = _mapping(payload.get("current_execution_envelope"))
    return _text(execution.get("state_kind")) == "typed_blocker" and bool(
        _mapping(execution.get("typed_blocker"))
    )


def _provider_attempt_run_id(payload: Mapping[str, Any]) -> str | None:
    runtime_liveness = _mapping(payload.get("runtime_liveness_audit"))
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    execution = _mapping(payload.get("current_execution_evidence"))
    execution_handoff = _mapping(execution.get("opl_current_control_state_handoff"))
    for surface in (runtime_liveness, handoff, execution_handoff):
        text = (
            _text(surface.get("active_run_id"))
            or _text(surface.get("active_stage_attempt_id"))
            or _text(surface.get("active_workflow_id"))
        )
        if text is not None:
            return text
    return None


def _package_delivered(payload: Mapping[str, Any], details: Mapping[str, Any]) -> bool:
    if details.get("package_delivered") is True:
        return True
    delivery = _mapping(payload.get("delivery_inspection"))
    if delivery.get("package_delivered") is True:
        return True
    if _delivery_current(delivery):
        return True
    submission_hygiene = _mapping(payload.get("submission_hygiene_truth"))
    if submission_hygiene.get("package_delivered") is True:
        return True
    package_state = _text(submission_hygiene.get("package_state"))
    return package_state in {"delivered", "current_package_delivered", "terminal_delivered"}


def _meaningful_artifact_delta(payload: Mapping[str, Any], *, visible_progress: bool) -> bool:
    if not visible_progress:
        return False
    if _mapping(payload.get("repair_progress_projection")).get("paper_delta_observed") is True:
        return True
    if _paper_facing_progress_slo(payload)["visible_as_progressing"]:
        return True
    if _fresh_artifact_delta_present(payload):
        return True
    if _scan_artifact_delta_present(payload):
        return True
    for key in ("paper_progress_stall", "opl_current_control_state_handoff", "runtime_health_snapshot"):
        value = _mapping(payload.get(key))
        if value.get("meaningful_artifact_delta") is True:
            return True
        artifact_delta = _mapping(value.get("artifact_delta"))
        if _text(artifact_delta.get("status")) == "fresh":
            return True
    return False


def _fresh_artifact_delta_present(payload: Mapping[str, Any]) -> bool:
    progress_freshness = _mapping(payload.get("progress_freshness"))
    artifact_delta = _mapping(progress_freshness.get("meaningful_artifact_delta_freshness"))
    return (
        _text(artifact_delta.get("status")) == "fresh"
        and (_text(artifact_delta.get("latest_progress_at")) is not None or bool(_paper_delta_changed_refs(payload)))
    ) or _scan_artifact_delta_present(payload)


def _generic_artifact_delta_visible(payload: Mapping[str, Any]) -> bool:
    progress_freshness = _mapping(payload.get("progress_freshness"))
    artifact_delta = _mapping(progress_freshness.get("meaningful_artifact_delta_freshness"))
    if not _fresh_artifact_delta_present(payload):
        return False
    if _text(artifact_delta.get("surface_kind")) == "runtime_log_delta":
        return False
    return not _string_items(artifact_delta.get("changed_refs"))


def _scan_artifact_delta_present(payload: Mapping[str, Any]) -> bool:
    if payload.get("meaningful_artifact_delta") is not True:
        return False
    artifact_delta = _mapping(payload.get("artifact_delta"))
    if _text(artifact_delta.get("status")) != "fresh":
        return False
    return _text(artifact_delta.get("latest_meaningful_delta_at")) is not None


def _next_owner(payload: Mapping[str, Any], details: Mapping[str, Any]) -> str | None:
    interaction = _mapping(payload.get("interaction_arbitration"))
    owner_route = _mapping(payload.get("owner_route"))
    production_impact = _mapping(payload.get("production_blocker_impact"))
    paper_progress_stall = _mapping(payload.get("paper_progress_stall"))
    domain_transition = _mapping(payload.get("domain_transition"))
    opl_handoff_action = current_owner_handoff_action(payload)
    ai_repair_lifecycle = _mapping(payload.get("ai_repair_lifecycle"))
    control_plane = _mapping(payload.get("authority_snapshot"))
    if _supervisor_only_live_quality_repair(payload):
        return "supervisor_only/live_quality_repair"
    owner = (
        _text(interaction.get("next_owner"))
        or _text(owner_route.get("next_owner"))
        or _text(production_impact.get("next_owner"))
        or _text(details.get("decision_owner"))
        or _text(details.get("route_owner"))
        or _text(domain_transition.get("owner"))
        or _text(paper_progress_stall.get("next_owner"))
        or _text((opl_handoff_action or {}).get("owner"))
        or _text(ai_repair_lifecycle.get("next_owner"))
        or _text(control_plane.get("next_owner"))
    )
    return _normalize_owner(owner)


def _requires_user_input(payload: Mapping[str, Any]) -> bool:
    interaction = _mapping(payload.get("interaction_arbitration"))
    if isinstance(interaction.get("requires_user_input"), bool):
        return bool(interaction.get("requires_user_input"))
    if payload.get("needs_user_decision") is True or payload.get("needs_physician_decision") is True:
        return True
    macro_state = _study_macro_state(payload)
    return _text(macro_state.get("user_next")) in {"submit_info", "revise"}


def _why_not_progressing(
    *,
    state: str,
    payload: Mapping[str, Any],
    actual_write_active: bool,
    package_delivered: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
    blocking_reasons: list[str],
) -> str | None:
    if state == "progressing" and actual_write_active and meaningful_artifact_delta:
        return None
    if package_delivered and state == "terminal_delivered":
        return "package_delivered"
    if state == "downstream_only":
        return _DOWNSTREAM_ONLY
    if state == "opl_stage_attempt_admission_required":
        return _RUNTIME_RETRY_EXHAUSTED
    if not meaningful_artifact_delta:
        stage_closeout = _stage_closeout_progress(payload, handoff_action=current_owner_handoff_action(payload))
        if stage_closeout["runtime_closeout_only"]:
            return "paper_facing_progress_delta_or_typed_blocker_missing"
    if not meaningful_artifact_delta and _paper_delta_changed_refs(payload):
        return "paper_facing_progress_delta_or_typed_blocker_missing"
    interaction = _mapping(payload.get("interaction_arbitration"))
    for value in (
        interaction.get("blocked_reason"),
        _mapping(payload.get("production_blocker_impact")).get("why_not_running"),
        _mapping(payload.get("paper_progress_stall")).get("why_not_running"),
        _mapping(payload.get("paper_progress_stall")).get("summary"),
        _mapping(_mapping(payload.get("progress_freshness")).get("activity_timeout")).get("summary"),
        _mapping(_mapping(payload.get("progress_freshness")).get("meaningful_artifact_delta_freshness")).get("summary"),
    ):
        text = _text(value)
        if text:
            return text
    if blocking_reasons:
        return blocking_reasons[0]
    if next_owner:
        return f"awaiting {next_owner}"
    if not meaningful_artifact_delta:
        return "meaningful_artifact_delta_missing"
    if not actual_write_active:
        return "actual_write_inactive"
    return "blocked_controller_route"


def _safe_reconcile_command(payload: Mapping[str, Any]) -> str | None:
    return None


def _controller_route_blocked(payload: Mapping[str, Any], blocking_reasons: list[str]) -> bool:
    control_plane = _mapping(payload.get("authority_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    if _route_authorization_blocked(payload):
        return True
    if _text(dispatch_gate.get("state")) == "blocked":
        return True
    if _text(control_plane.get("control_state")) in {"blocked_controller_decision", "blocked_ledger", "needs_reconcile"}:
        return True
    return any(reason.startswith("controller_") or reason.startswith("ledger.") for reason in blocking_reasons)


def _same_line_reactivation_active(payload: Mapping[str, Any]) -> bool:
    quality_truth = _mapping(payload.get("quality_closure_truth"))
    if _text(quality_truth.get("state")) == "quality_repair_required":
        return True
    study_truth = _mapping(payload.get("study_truth_snapshot"))
    if _text(study_truth.get("canonical_next_action")) == "resume_same_study_line":
        return True
    task_intake = _mapping(payload.get("task_intake"))
    revision_intake = _mapping(task_intake.get("revision_intake"))
    if _text(revision_intake.get("status")) == "active" and revision_intake.get("reactivation_required") is True:
        return True
    return False


def _is_downstream_only(payload: Mapping[str, Any], blocking_reasons: list[str]) -> bool:
    supervisor = _mapping(payload.get("publication_supervisor_state"))
    if supervisor.get("bundle_tasks_downstream_only") is True or _DOWNSTREAM_ONLY in blocking_reasons:
        return True
    if not _paper_facing_progress_slo(payload)["visible_as_progressing"]:
        return False
    next_owner = _text(payload.get("next_owner")) or _text(_mapping(payload.get("owner_route")).get("next_owner"))
    return next_owner == "supervisor_only/live_quality_repair"


def _owner_callable_surface_missing(payload: Mapping[str, Any], next_owner: str | None) -> bool:
    if next_owner == "supervisor_only/live_quality_repair":
        return False
    if next_owner == "MAS/controller":
        return False
    interaction = _mapping(payload.get("interaction_arbitration"))
    if _text(interaction.get("blocked_reason")) == "owner_callable_surface_missing":
        return True
    if next_owner and next_owner not in _registered_callable_owners():
        return True
    return "owner_callable_surface_missing" in _blocking_reasons(payload)


def _opl_stage_attempt_admission_owner(payload: Mapping[str, Any], next_owner: str | None) -> bool:
    owner_route = _mapping(payload.get("owner_route"))
    return (
        next_owner == "one-person-lab"
        and "request_opl_stage_attempt" in _string_items(owner_route.get("allowed_actions"))
    )


def _route_authorization_blocked(payload: Mapping[str, Any]) -> bool:
    control_plane = _mapping(payload.get("authority_snapshot"))
    route_authorization = _mapping(control_plane.get("route_authorization"))
    if not route_authorization:
        return False
    return route_authorization.get("authorized") is False


def _delivery_current(delivery: Mapping[str, Any]) -> bool:
    if _text(delivery.get("status")) == "current":
        return True
    if _text(delivery.get("delivery_status")) == "current":
        return True
    freshness = _mapping(delivery.get("freshness"))
    if _text(freshness.get("delivery_status")) == "current":
        return True
    handshake = _mapping(freshness.get("gate_freshness_handshake"))
    return _text(handshake.get("status")) == "current"


def _supervisor_only_live_quality_repair(payload: Mapping[str, Any]) -> bool:
    if not _supervisor_only(payload):
        return False
    if not _fresh_artifact_delta_present(payload):
        return False
    active_run_id = (
        _text(payload.get("active_run_id"))
        or _text(_mapping(payload.get("supervision")).get("active_run_id"))
        or _text(_mapping(_study_macro_state(payload).get("details")).get("active_run_id"))
        or _text(_mapping(payload.get("owner_route")).get("active_run_id"))
    )
    return active_run_id is not None


def _study_macro_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    macro_state = _mapping(payload.get("study_macro_state"))
    if macro_state:
        return macro_state
    owner_route = _mapping(payload.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    return _mapping(source_refs.get("study_macro_state"))


def _supervisor_only(payload: Mapping[str, Any]) -> bool:
    if _mapping(payload.get("execution_owner_guard")).get("supervisor_only") is True:
        return True
    if "execution_owner_guard.supervisor_only" in _blocking_reasons(payload):
        return True
    control_plane = _mapping(payload.get("authority_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    return "execution_owner_guard.supervisor_only" in _string_items(dispatch_gate.get("blocking_reasons"))


def _normalize_owner(owner: str | None) -> str | None:
    if owner is None:
        return None
    if owner == "mas_controller" or owner.startswith("MAS/controller"):
        return "MAS/controller"
    return owner


def _registered_callable_owners() -> set[str]:
    try:
        from med_autoscience.runtime_control.owner_callable_registry import callable_owner_names
    except ImportError:
        return set()
    return set(callable_owner_names())


def _blocking_reasons(payload: Mapping[str, Any]) -> list[str]:
    control_plane = _mapping(payload.get("authority_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    health = _mapping(payload.get("runtime_health_snapshot"))
    truth = _mapping(payload.get("study_truth_snapshot"))
    return _dedupe(
        [
            *_string_items(payload.get("current_blockers")),
            *_string_items(control_plane.get("blocking_reasons")),
            *_string_items(dispatch_gate.get("blocking_reasons")),
            *_string_items(health.get("blocking_reasons")),
            *_string_items(truth.get("blocking_reasons")),
        ]
    )


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _string_items(value: object) -> list[str]:
    if isinstance(value, Mapping) or isinstance(value, str | bytes):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, Iterable):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "PAPER_PROGRESS_STATE_READ_MODEL",
    "PAPER_PROGRESS_STATE_SURFACE",
    "PUBLIC_STATES",
    "build_paper_progress_state",
]
