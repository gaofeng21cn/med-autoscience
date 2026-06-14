from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from collections.abc import Mapping

from med_autoscience.controllers import current_execution_envelope
from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
from med_autoscience.controllers import runtime_dispatch_cost
from med_autoscience.controllers.domain_health_diagnostic_parts.reporting import _attach_family_companion_to_runtime_report
from med_autoscience.runtime_protocol import quest_state


def scan_active_quest_reports(
    *,
    runtime_root: Path,
    controller_runners: dict[str, Callable[..., dict[str, Any]]],
    apply: bool,
    persist_diagnostic_reports: bool,
    run_domain_health_diagnostic_for_quest_fn: Callable[..., dict[str, Any]],
    study_ids: tuple[str, ...] = (),
) -> tuple[list[str], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    requested_study_ids = {str(study_id).strip() for study_id in study_ids if str(study_id).strip()}
    scanned: list[str] = []
    reports: list[dict[str, Any]] = []
    for quest_root in quest_state.iter_active_quests(runtime_root):
        if requested_study_ids and quest_root.name not in requested_study_ids:
            continue
        scanned.append(quest_root.name)
        reports.append(
            run_domain_health_diagnostic_for_quest_fn(
                quest_root=quest_root,
                controller_runners=controller_runners,
                apply=apply,
                persist_diagnostic_reports=persist_diagnostic_reports,
            )
        )
    report_by_quest_root = {
        str(Path(str(report.get("quest_root") or "")).expanduser().resolve()): report
        for report in reports
        if str(report.get("quest_root") or "").strip()
    }
    return scanned, reports, report_by_quest_root


def build_runtime_report(
    *,
    runtime_root: Path,
    scanned: list[str],
    reports: list[dict[str, Any]],
    managed_study_actions: list[dict[str, Any]],
    managed_study_auto_recoveries: list[dict[str, Any]],
    managed_study_recovery_holds: list[dict[str, Any]],
    managed_study_outer_loop_dispatches: list[dict[str, Any]],
    managed_study_outer_loop_wakeup_audits: list[dict[str, Any]],
    managed_study_no_op_suppressions: list[dict[str, Any]],
    managed_study_opl_runtime_owner_handoffs: list[dict[str, Any]],
    managed_study_opl_provider_admission_candidates: list[dict[str, Any]],
    managed_study_progress_currentness: dict[str, dict[str, Any]],
    managed_study_autonomy_slo_statuses: list[dict[str, Any]],
    managed_study_autonomy_repair_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    managed_study_actions = _managed_study_actions_with_currentness(
        managed_study_actions=managed_study_actions,
        progress_currentness=managed_study_progress_currentness,
    )
    dispatch_counters = _dispatch_counters(
        dispatches=managed_study_outer_loop_dispatches,
        suppressions=managed_study_no_op_suppressions,
        provider_admission_candidates=managed_study_opl_provider_admission_candidates,
    )
    report_action_class = "codex_worker_dispatch" if dispatch_counters["codex_dispatch_count"] else (
        "controller_apply" if managed_study_outer_loop_dispatches else "observe_only"
    )
    report_will_start_llm = dispatch_counters["codex_dispatch_count"] > 0
    paper_recovery_states = _paper_recovery_states(
        progress_currentness=managed_study_progress_currentness,
        provider_admission_candidates=managed_study_opl_provider_admission_candidates,
        diagnostic_report={
            "action_class": report_action_class,
            "will_start_llm": report_will_start_llm,
            "codex_dispatch_count": dispatch_counters["codex_dispatch_count"],
            "provider_admission_pending_count": len(managed_study_opl_provider_admission_candidates),
        },
    )
    managed_study_actions = _managed_study_actions_with_paper_recovery_state(
        managed_study_actions=managed_study_actions,
        paper_recovery_states=paper_recovery_states,
    )
    managed_study_actions = _managed_study_actions_with_provider_admission_state(
        managed_study_actions=managed_study_actions,
        provider_admission_candidates=managed_study_opl_provider_admission_candidates,
        paper_recovery_states=paper_recovery_states,
    )
    managed_study_opl_runtime_owner_handoffs = _managed_handoffs_with_currentness(
        handoffs=managed_study_opl_runtime_owner_handoffs,
        progress_currentness=managed_study_progress_currentness,
    )
    current_execution_envelopes = _current_execution_envelopes(
        managed_study_actions=managed_study_actions,
        suppressions=managed_study_no_op_suppressions,
        progress_currentness=managed_study_progress_currentness,
    )
    runtime_report = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "runtime_root": str(runtime_root),
        "scanned_quests": scanned,
        "managed_study_actions": managed_study_actions,
        "managed_study_auto_recoveries": managed_study_auto_recoveries,
        "managed_study_recovery_holds": managed_study_recovery_holds,
        "managed_study_outer_loop_dispatches": managed_study_outer_loop_dispatches,
        "managed_study_outer_loop_wakeup_audits": managed_study_outer_loop_wakeup_audits,
        "managed_study_no_op_suppressions": managed_study_no_op_suppressions,
        "current_execution_envelopes": current_execution_envelopes,
        "current_execution_evidence": {
            "no_op": managed_study_no_op_suppressions,
            "managed_study_actions": managed_study_actions,
            "provider_admission_candidates": managed_study_opl_provider_admission_candidates,
            "progress_currentness": managed_study_progress_currentness,
        },
        "managed_study_opl_runtime_owner_handoffs": managed_study_opl_runtime_owner_handoffs,
        "managed_study_opl_provider_admission_candidates": managed_study_opl_provider_admission_candidates,
        "provider_admission_pending_count": len(managed_study_opl_provider_admission_candidates),
        "paper_recovery_states": paper_recovery_states,
        "paper_recovery_provider_admission_blocked_count": _paper_recovery_provider_admission_blocked_count(
            paper_recovery_states
        ),
        "managed_study_autonomy_slo_statuses": managed_study_autonomy_slo_statuses,
        "managed_study_autonomy_repair_actions": managed_study_autonomy_repair_actions,
        "action_class": report_action_class,
        "will_start_llm": report_will_start_llm,
        "codex_dispatch_count": dispatch_counters["codex_dispatch_count"],
        "suppressed_dispatch_count": dispatch_counters["suppressed_dispatch_count"],
        "dispatch_budget_window": dispatch_counters["dispatch_budget_window"],
        "action_fingerprints": dispatch_counters["action_fingerprints"],
        "reports": reports,
    }
    _attach_family_companion_to_runtime_report(runtime_report, runtime_root=Path(runtime_root).expanduser().resolve())
    return runtime_report


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _dispatch_counters(
    *,
    dispatches: list[dict[str, Any]],
    suppressions: list[dict[str, Any]],
    provider_admission_candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    codex_dispatch_count = sum(_dispatch_starts_worker(dispatch) for dispatch in dispatches)
    fingerprints = []
    for item in [*dispatches, *suppressions, *provider_admission_candidates]:
        for key in ("work_unit_fingerprint", "action_fingerprint", "work_unit_dispatch_key", "dedupe_scope"):
            value = str(item.get(key) or "").strip()
            if value:
                fingerprints.append(value)
                break
    return {
        "codex_dispatch_count": codex_dispatch_count,
        "suppressed_dispatch_count": len(suppressions),
        "dispatch_budget_window": runtime_dispatch_cost.dispatch_budget_window(),
        "action_fingerprints": list(dict.fromkeys(fingerprints)),
    }


def _paper_recovery_states(
    *,
    progress_currentness: dict[str, dict[str, Any]],
    provider_admission_candidates: list[dict[str, Any]],
    diagnostic_report: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    candidates_by_study = _provider_admission_candidates_by_study(provider_admission_candidates)
    states: dict[str, dict[str, Any]] = {}
    study_ids = set(progress_currentness) | set(candidates_by_study)
    for study_id in sorted(study_ids):
        progress = dict(_mapping(progress_currentness.get(study_id)))
        if not progress:
            progress = {"study_id": study_id}
        candidates = candidates_by_study.get(study_id, [])
        progress["provider_admission_pending_count"] = len(candidates)
        progress["provider_admission_candidates"] = candidates
        state = build_paper_recovery_state(
            progress,
            diagnostic_report={
                **dict(diagnostic_report),
                "provider_admission_pending_count": len(candidates),
            },
        )
        states[study_id] = state
    return states


def _paper_recovery_provider_admission_blocked_count(
    states: Mapping[str, Mapping[str, Any]],
) -> int:
    return sum(
        1
        for state in states.values()
        if _text(state.get("phase")) == "admission_blocked"
    )


def _dispatch_starts_worker(dispatch: dict[str, Any]) -> bool:
    if dispatch.get("started") is True or dispatch.get("worker_running") is True:
        return True
    action_type = str(dispatch.get("controller_action_type") or dispatch.get("action_type") or "").strip()
    return action_type in {"request_opl_stage_attempt", "request_opl_stage_attempt_relaunch"}


def _managed_study_actions_with_currentness(
    *,
    managed_study_actions: list[dict[str, Any]],
    progress_currentness: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for action in managed_study_actions:
        if not isinstance(action, Mapping):
            result.append(action)
            continue
        study_id = _text(action.get("study_id"))
        if study_id is None:
            result.append(dict(action))
            continue
        currentness = _mapping(progress_currentness.get(study_id))
        if not currentness:
            result.append(dict(action))
            continue
        result.append(_managed_study_action_with_currentness(action, currentness=currentness))
    return result


def _managed_study_action_with_currentness(
    action: Mapping[str, Any],
    *,
    currentness: Mapping[str, Any],
) -> dict[str, Any]:
    current_work_unit = _mapping(currentness.get("current_work_unit"))
    current_execution = _mapping(currentness.get("current_execution_envelope"))
    current_owner_action = _mapping(currentness.get("current_executable_owner_action"))
    state_kind = _text(current_work_unit.get("status")) or _text(current_execution.get("state_kind"))
    if state_kind not in {
        "running_provider_attempt",
        "typed_blocker",
        "blocked_current_work_unit",
        "executable_owner_action",
    }:
        return dict(action)

    result = dict(action)
    if current_work_unit:
        result["current_work_unit"] = current_work_unit
    if current_execution:
        result["current_execution_envelope"] = current_execution
    if current_owner_action:
        result["current_executable_owner_action"] = current_owner_action

    if state_kind == "running_provider_attempt":
        result["decision"] = "noop"
        result["reason"] = "running_provider_attempt_observed"
        result["running_provider_attempt"] = True
        proof = _mapping(_mapping(current_work_unit.get("state")).get("provider_attempt_proof"))
        if proof:
            result["provider_attempt_proof"] = proof
            if active_run_id := _text(proof.get("active_run_id")):
                result["active_run_id"] = active_run_id
            if active_stage_attempt_id := _text(proof.get("active_stage_attempt_id")):
                result["active_stage_attempt_id"] = active_stage_attempt_id
            if active_workflow_id := _text(proof.get("active_workflow_id")):
                result["active_workflow_id"] = active_workflow_id
        return result

    if state_kind in {"typed_blocker", "blocked_current_work_unit"}:
        result["decision"] = "blocked"
        result["reason"] = (
            _current_work_unit_blocker_reason(current_work_unit)
            or _current_execution_blocker_reason(current_execution)
            or state_kind
        )
        result["running_provider_attempt"] = False
    if state_kind == "executable_owner_action":
        result["running_provider_attempt"] = False
    return result


def _managed_study_actions_with_paper_recovery_state(
    *,
    managed_study_actions: list[dict[str, Any]],
    paper_recovery_states: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for action in managed_study_actions:
        if not isinstance(action, Mapping):
            result.append(action)
            continue
        study_id = _text(action.get("study_id"))
        recovery = _mapping(paper_recovery_states.get(study_id or ""))
        if not recovery:
            result.append(dict(action))
            continue
        result.append(_managed_study_action_with_paper_recovery_state(action, recovery=recovery))
    return result


def _managed_study_action_with_paper_recovery_state(
    action: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(action)
    result["paper_recovery_state"] = dict(recovery)
    phase = _text(recovery.get("phase"))
    if phase in {"domain_blocked", "human_gate"}:
        result["decision"] = phase
        result["reason"] = _paper_recovery_reason(recovery) or phase
        result["running_provider_attempt"] = False
    return result


def _managed_study_actions_with_provider_admission_state(
    *,
    managed_study_actions: list[dict[str, Any]],
    provider_admission_candidates: list[dict[str, Any]],
    paper_recovery_states: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates_by_study = _provider_admission_candidates_by_study(provider_admission_candidates)
    if not candidates_by_study:
        return [
            dict(action) if isinstance(action, Mapping) else action
            for action in managed_study_actions
        ]
    result: list[dict[str, Any]] = []
    for action in managed_study_actions:
        if not isinstance(action, Mapping):
            result.append(action)
            continue
        study_id = _text(action.get("study_id"))
        candidates = candidates_by_study.get(study_id or "")
        if not candidates:
            result.append(dict(action))
            continue
        recovery = _mapping(_mapping(paper_recovery_states).get(study_id or ""))
        result.append(
            _managed_study_action_with_provider_admission_state(
                action,
                candidates=candidates,
                paper_recovery_state=recovery,
            )
        )
    return result


def _managed_study_action_with_provider_admission_state(
    action: Mapping[str, Any],
    *,
    candidates: list[dict[str, Any]],
    paper_recovery_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = dict(action)
    result["provider_admission_candidates"] = [dict(candidate) for candidate in candidates]
    recovery = _mapping(paper_recovery_state)
    if recovery:
        result["paper_recovery_state"] = recovery
    gate = _mapping(result.get("execution_gate"))
    if gate.get("blocked") is True:
        result["running_provider_attempt"] = False
        result["provider_admission_state"] = {
            "status": "pending_but_execution_gate_blocked",
            "candidate_count": len(candidates),
            "running_provider_attempt": False,
            "execution_gate_reason": _text(gate.get("reason")),
        }
        return result
    if _text(recovery.get("phase")) == "admission_blocked":
        result["running_provider_attempt"] = False
        result["provider_admission_state"] = {
            "status": "blocked_by_paper_recovery_state",
            "candidate_count": len(candidates),
            "running_provider_attempt": False,
            "paper_recovery_phase": _text(recovery.get("phase")),
            "paper_recovery_reason": _paper_recovery_reason(recovery),
        }
        return result
    result.setdefault(
        "provider_admission_state",
        {
            "status": "pending",
            "candidate_count": len(candidates),
            "running_provider_attempt": result.get("running_provider_attempt") is True,
        },
    )
    return result


def _provider_admission_candidates_by_study(
    provider_admission_candidates: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    candidates_by_study: dict[str, list[dict[str, Any]]] = {}
    for candidate in provider_admission_candidates:
        if not isinstance(candidate, Mapping):
            continue
        study_id = _text(candidate.get("study_id"))
        if study_id is None:
            continue
        candidates_by_study.setdefault(study_id, []).append(dict(candidate))
    return candidates_by_study


def _paper_recovery_reason(recovery: Mapping[str, Any]) -> str | None:
    for condition in recovery.get("conditions") or []:
        if not isinstance(condition, Mapping):
            continue
        if text := _text(condition.get("condition")):
            return text
    return _text(recovery.get("phase"))


def _current_work_unit_blocker_reason(current_work_unit: Mapping[str, Any]) -> str | None:
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = _mapping(state.get("typed_blocker"))
    return (
        _text(typed_blocker.get("blocked_reason"))
        or _text(typed_blocker.get("blocker_type"))
        or _text(typed_blocker.get("blocker_id"))
        or _text(state.get("blocker_type"))
    )


def _current_execution_blocker_reason(current_execution: Mapping[str, Any]) -> str | None:
    typed_blocker = _mapping(current_execution.get("typed_blocker"))
    return (
        _text(typed_blocker.get("blocked_reason"))
        or _text(typed_blocker.get("blocker_type"))
        or _text(typed_blocker.get("blocker_id"))
    )


def _managed_handoffs_with_currentness(
    *,
    handoffs: list[dict[str, Any]],
    progress_currentness: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for handoff in handoffs:
        if not isinstance(handoff, Mapping):
            result.append(handoff)
            continue
        study_id = _text(handoff.get("study_id"))
        currentness = _mapping(progress_currentness.get(study_id)) if study_id is not None else {}
        result.append(_managed_handoff_with_currentness(handoff, currentness=currentness))
    return result


def _managed_handoff_with_currentness(
    handoff: Mapping[str, Any],
    *,
    currentness: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(handoff)
    current_work_unit = _mapping(currentness.get("current_work_unit"))
    current_execution = _mapping(currentness.get("current_execution_envelope"))
    state_kind = _text(current_work_unit.get("status")) or _text(current_execution.get("state_kind"))
    if state_kind not in {"running_provider_attempt", "typed_blocker", "blocked_current_work_unit"}:
        return result
    if _text(result.get("status")) != "handoff_required":
        return result
    result["status"] = "superseded_by_current_work_unit"
    result["previous_status"] = "handoff_required"
    result["reason"] = state_kind
    result["current_work_unit"] = current_work_unit or None
    result["current_execution_envelope"] = current_execution or None
    result["refs_only_handoff_superseded"] = True
    result["next_action_summary"] = (
        "Canonical current_work_unit supersedes this refs-only OPL handoff record."
    )
    return result


def _current_execution_envelopes(
    *,
    managed_study_actions: list[dict[str, Any]],
    suppressions: list[dict[str, Any]],
    progress_currentness: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    no_op_by_study = {
        study_id: item
        for item in suppressions
        if isinstance(item, Mapping) and (study_id := _text(item.get("study_id"))) is not None
    }
    envelopes: dict[str, dict[str, Any]] = {}
    for action in managed_study_actions:
        if not isinstance(action, Mapping):
            continue
        study_id = _text(action.get("study_id"))
        if study_id is None:
            continue
        action_with_currentness = {
            **action,
            **_mapping(progress_currentness.get(study_id)),
        }
        progress_envelope = _fresh_progress_current_execution_envelope(action_with_currentness)
        if progress_envelope is not None:
            envelopes[study_id] = progress_envelope
            continue
        status_envelope = _current_status_envelope(action_with_currentness)
        if status_envelope is not None and _text(status_envelope.get("state_kind")) in {
            "parked",
            "running_provider_attempt",
            "typed_blocker",
        }:
            envelopes[study_id] = status_envelope
            continue
        runtime_health = _mapping(action_with_currentness.get("runtime_health_snapshot"))
        envelopes[study_id] = current_execution_envelope.build_current_execution_envelope(
            status=action_with_currentness,
            progress=action_with_currentness,
            actions=_current_status_actions(action_with_currentness),
            blocked_reason=_text(action_with_currentness.get("reason")),
            next_owner=_text(action_with_currentness.get("runtime_owner"))
            or _text(action_with_currentness.get("domain_owner")),
            runtime_health=runtime_health,
            conflict_suppression_refs=[f"no_op:{_text(no_op_by_study[study_id].get('outcome'))}"]
            if study_id in no_op_by_study and _text(no_op_by_study[study_id].get("outcome")) is not None
            else None,
        )
    return envelopes


def _fresh_progress_current_execution_envelope(status: Mapping[str, Any]) -> dict[str, Any] | None:
    envelope = _current_status_envelope(status)
    if envelope is None:
        return None
    state_kind = _text(envelope.get("state_kind"))
    if state_kind != "executable_owner_action":
        return None
    work_unit = _mapping(status.get("current_work_unit"))
    if _text(work_unit.get("status")) != "executable_owner_action":
        return None
    owner = _text(work_unit.get("owner"))
    if owner in {None, "user", "human"}:
        return None
    next_work_unit = _text(work_unit.get("work_unit_id")) or _text(work_unit.get("action_type"))
    if next_work_unit is None:
        return None
    return envelope


def _current_status_envelope(status: Mapping[str, Any]) -> dict[str, Any] | None:
    envelope = _mapping(status.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind not in set(current_execution_envelope.ALLOWED_STATE_KINDS):
        return None
    return envelope


def _current_status_actions(status: Mapping[str, Any]) -> list[dict[str, Any]]:
    current = _mapping(status.get("current_executable_owner_action"))
    if not current:
        return []
    target_surface = _mapping(current.get("target_surface"))
    next_action = _mapping(current.get("next_action"))
    action_type = (
        _text(current.get("action_type"))
        or _text(current.get("work_unit_id"))
        or _text(next_action.get("action_id"))
    )
    if action_type is None:
        return []
    allowed_actions = _text_items(current.get("allowed_actions")) or [action_type]
    action = {
        "action_type": action_type,
        "owner": (
            _text(current.get("owner"))
            or _text(current.get("recommended_owner"))
            or _text(current.get("next_owner"))
            or _text(target_surface.get("owner"))
        ),
        "recommended_owner": _text(current.get("recommended_owner")) or _text(current.get("next_owner")),
        "next_owner": _text(current.get("next_owner")) or _text(current.get("owner")),
        "next_work_unit": (
            _text(current.get("next_work_unit"))
            or _text(current.get("work_unit_id"))
            or _text(next_action.get("action_id"))
        ),
        "work_unit_id": _text(current.get("work_unit_id")) or _text(next_action.get("action_id")),
        "allowed_actions": allowed_actions,
        "source_surface": _text(current.get("source")) or _text(current.get("source_surface")),
        "source_ref": _text(current.get("source_ref")) or _text(current.get("latest_owner_answer_ref")),
    }
    return [{key: value for key, value in action.items() if value is not None}]


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
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in items:
            items.append(text)
    return items


__all__ = ["build_runtime_report", "scan_active_quest_reports"]
