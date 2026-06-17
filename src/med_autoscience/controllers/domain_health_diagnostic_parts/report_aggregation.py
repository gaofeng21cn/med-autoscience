from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
from collections.abc import Mapping

from med_autoscience.controllers import current_execution_envelope
from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
from med_autoscience.controllers import runtime_dispatch_cost
from med_autoscience.controllers.domain_health_diagnostic_parts.reporting import _attach_family_companion_to_runtime_report
from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback,
)
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
    transition_request_candidates = _merge_provider_admission_candidates(
        _provider_admission_candidates_with_opl_runtime_readback(
            managed_study_opl_provider_admission_candidates,
            runtime_root=runtime_root,
        ),
        _progress_currentness_provider_admission_candidates(
            managed_study_progress_currentness,
            runtime_root=runtime_root,
        ),
    )
    provider_admission_candidates = _provider_admission_candidates_with_opl_readback(
        transition_request_candidates
    )
    transition_request_candidates = _transition_request_candidates_without_opl_readback(
        transition_request_candidates
    )
    dispatch_counters = _dispatch_counters(
        dispatches=managed_study_outer_loop_dispatches,
        suppressions=managed_study_no_op_suppressions,
        provider_admission_candidates=transition_request_candidates,
    )
    report_action_class = "codex_worker_dispatch" if dispatch_counters["codex_dispatch_count"] else (
        "controller_apply" if managed_study_outer_loop_dispatches else "observe_only"
    )
    report_will_start_llm = dispatch_counters["codex_dispatch_count"] > 0
    paper_recovery_states = _paper_recovery_states(
        progress_currentness=managed_study_progress_currentness,
        provider_admission_candidates=provider_admission_candidates,
        managed_study_actions=managed_study_actions,
        diagnostic_report={
            "action_class": report_action_class,
            "will_start_llm": report_will_start_llm,
            "codex_dispatch_count": dispatch_counters["codex_dispatch_count"],
            "provider_admission_pending_count": len(provider_admission_candidates),
            "transition_request_pending_count": len(transition_request_candidates),
        },
    )
    managed_study_actions = _managed_study_actions_with_paper_recovery_state(
        managed_study_actions=managed_study_actions,
        paper_recovery_states=paper_recovery_states,
    )
    managed_study_actions = _managed_study_actions_with_provider_admission_state(
        managed_study_actions=managed_study_actions,
        provider_admission_candidates=provider_admission_candidates,
        transition_request_candidates=transition_request_candidates,
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
            "provider_admission_candidates": provider_admission_candidates,
            "transition_request_candidates": transition_request_candidates,
            "progress_currentness": managed_study_progress_currentness,
        },
        "managed_study_opl_runtime_owner_handoffs": managed_study_opl_runtime_owner_handoffs,
        "managed_study_opl_provider_admission_candidates": provider_admission_candidates,
        "managed_study_opl_transition_request_candidates": transition_request_candidates,
        "provider_admission_pending_count": len(provider_admission_candidates),
        "transition_request_pending_count": len(transition_request_candidates),
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
    managed_study_actions: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    candidates_by_study = _provider_admission_candidates_by_study(provider_admission_candidates)
    action_context_by_study = _managed_study_action_context_by_study(managed_study_actions)
    states: dict[str, dict[str, Any]] = {}
    study_ids = set(progress_currentness) | set(candidates_by_study)
    for study_id in sorted(study_ids):
        progress = dict(_mapping(progress_currentness.get(study_id)))
        progress = _progress_with_managed_study_action_context(
            progress,
            action_context=action_context_by_study.get(study_id, {}),
        )
        if not progress:
            progress = {"study_id": study_id}
        candidates = candidates_by_study.get(study_id, [])
        progress["provider_admission_pending_count"] = len(candidates)
        progress["provider_admission_candidates"] = candidates
        if canonical_state := _mapping(progress.get("paper_recovery_state")):
            states[study_id] = dict(canonical_state)
            continue
        state = build_paper_recovery_state(
            progress,
            diagnostic_report={
                **dict(diagnostic_report),
                "provider_admission_pending_count": len(candidates),
            },
        )
        states[study_id] = state
    return states


def _provider_admission_candidates_with_opl_readback(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(candidate)
        for candidate in candidates
        if candidate_opl_transition_readback(candidate)
    ]


def _provider_admission_candidates_with_opl_runtime_readback(
    candidates: list[dict[str, Any]],
    *,
    runtime_root: Path,
) -> list[dict[str, Any]]:
    return [
        _candidate_with_opl_runtime_readback(
            candidate,
            runtime_root=runtime_root,
        )
        for candidate in candidates
    ]


def _transition_request_candidates_without_opl_readback(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(candidate)
        for candidate in candidates
        if not candidate_opl_transition_readback(candidate)
    ]


def _progress_currentness_provider_admission_candidates(
    progress_currentness: Mapping[str, Mapping[str, Any]],
    *,
    runtime_root: Path,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for payload in _mapping(progress_currentness).values():
        progress = _mapping(payload)
        for key in ("transition_request_candidates", "provider_admission_candidates"):
            candidates.extend(
                _candidate_with_opl_runtime_readback(
                    item,
                    runtime_root=runtime_root,
                )
                for item in progress.get(key) or []
                if isinstance(item, Mapping)
            )
    return candidates


def _candidate_with_opl_runtime_readback(
    candidate: Mapping[str, Any],
    *,
    runtime_root: Path,
) -> dict[str, Any]:
    payload = dict(candidate)
    inline_readback = candidate_opl_transition_readback(payload)
    if inline_readback:
        payload["opl_transition_readback_source"] = _opl_transition_readback_source(inline_readback)
        payload["status"] = "provider_admission_pending"
        payload["provider_admission_pending"] = True
        payload["provider_attempt_or_lease_required"] = True
        payload["provider_admission_requires_opl_runtime_result"] = False
    return payload


def _opl_transition_readback_source(readback: Mapping[str, Any]) -> str:
    return "opl_domain_progress_transition_runtime_live_readback"


def _merge_provider_admission_candidates(
    *candidate_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for group in candidate_groups:
        for candidate in group:
            key = (
                _text(candidate.get("study_id")),
                _text(candidate.get("action_type")),
                _text(candidate.get("work_unit_id")),
                _text(candidate.get("dispatch_path")),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(candidate))
    return merged


def _managed_study_action_context_by_study(
    managed_study_actions: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for action in managed_study_actions or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _text(action.get("study_id"))
        if study_id is None:
            continue
        context = {
            key: dict(value)
            for key in (
                "runtime_health_snapshot",
                "study_truth_snapshot",
                "authority_snapshot",
                "resume_postcondition",
            )
            if isinstance((value := action.get(key)), Mapping)
        }
        if context:
            contexts[study_id] = context
    return contexts


def _progress_with_managed_study_action_context(
    progress: Mapping[str, Any],
    *,
    action_context: Mapping[str, Any],
) -> dict[str, Any]:
    if not action_context:
        return dict(progress)
    merged = dict(progress)
    for key, value in action_context.items():
        if not isinstance(value, Mapping):
            continue
        existing = _mapping(merged.get(key))
        merged[key] = {**dict(value), **existing} if existing else dict(value)
    return merged


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
        "owner_receipt_recorded",
        "typed_blocker",
        "blocked_current_work_unit",
        "executable_owner_action",
    }:
        return dict(action)

    currentness_reason = (
        _current_work_unit_blocker_reason(current_work_unit)
        or _current_execution_blocker_reason(current_execution)
    )
    if (
        state_kind in {"typed_blocker", "blocked_current_work_unit"}
        and _is_unresolved_current_work_unit_fallback(currentness_reason, current_work_unit)
        and _text(action.get("reason")) is not None
    ):
        return dict(action)

    result = dict(action)
    if current_work_unit:
        result["current_work_unit"] = current_work_unit
    if current_execution:
        result["current_execution_envelope"] = current_execution
    if current_owner_action:
        result["current_executable_owner_action"] = current_owner_action
    if _is_opl_stage_attempt_admission_action(result):
        result["running_provider_attempt"] = False
        return result

    terminal_reason = _terminal_controller_work_unit_reason(result)
    if terminal_reason is not None and state_kind in {"typed_blocker", "blocked_current_work_unit"}:
        result["decision"] = _text(result.get("decision")) or "blocked"
        result["reason"] = _text(result.get("reason")) or terminal_reason
        result["running_provider_attempt"] = False
        return result

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

    if state_kind == "owner_receipt_recorded":
        result["decision"] = "owner_receipt_recorded"
        result["reason"] = "current_owner_receipt_recorded"
        result["running_provider_attempt"] = False
        return result

    if state_kind in {"typed_blocker", "blocked_current_work_unit"}:
        action_reason = _text(result.get("reason"))
        result["decision"] = "blocked"
        if _is_unresolved_current_work_unit_fallback(currentness_reason, current_work_unit) and action_reason:
            result["reason"] = action_reason
        else:
            result["reason"] = currentness_reason or action_reason or state_kind
        result["running_provider_attempt"] = False
    if state_kind == "executable_owner_action":
        result["running_provider_attempt"] = False
    return result


def _terminal_controller_work_unit_reason(action: Mapping[str, Any]) -> str | None:
    lifecycle = _mapping(action.get("controller_work_unit_lifecycle"))
    if lifecycle.get("terminal_consumed") is not True:
        return None
    return (
        _text(action.get("reason"))
        or _text(lifecycle.get("block_reason"))
        or _text(lifecycle.get("lifecycle_state"))
    )


def _is_unresolved_current_work_unit_fallback(
    reason: str | None,
    current_work_unit: Mapping[str, Any],
) -> bool:
    if reason != "current_work_unit_unresolved":
        return False
    return (
        _text(current_work_unit.get("work_unit_id")) is None
        and _text(current_work_unit.get("work_unit_fingerprint")) is None
    )


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
    if _paper_recovery_is_unresolved_current_work_unit_fallback(recovery):
        return dict(action)
    result = dict(action)
    result["paper_recovery_state"] = dict(recovery)
    supervisor_decision = _mapping(_mapping(recovery).get("supervisor_decision"))
    if supervisor_decision:
        result["supervisor_decision"] = dict(supervisor_decision)
    phase = _text(recovery.get("phase"))
    if _is_opl_stage_attempt_admission_action(result):
        return result
    if phase in {"domain_blocked", "human_gate"}:
        result["decision"] = phase
        result["reason"] = _paper_recovery_reason(recovery) or phase
        result["running_provider_attempt"] = False
    return result


def _is_opl_stage_attempt_admission_action(action: Mapping[str, Any]) -> bool:
    resume_postcondition = _mapping(action.get("resume_postcondition"))
    return (
        _text(action.get("decision")) == "blocked"
        and _text(action.get("reason")) == "quest_waiting_opl_runtime_owner_route"
        and resume_postcondition.get("status") == "opl_stage_attempt_admission_required"
    )


def _managed_study_actions_with_provider_admission_state(
    *,
    managed_study_actions: list[dict[str, Any]],
    provider_admission_candidates: list[dict[str, Any]],
    transition_request_candidates: list[dict[str, Any]] | None = None,
    paper_recovery_states: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates_by_study = _provider_admission_candidates_by_study(provider_admission_candidates)
    transition_requests_by_study = _provider_admission_candidates_by_study(
        transition_request_candidates or []
    )
    if not candidates_by_study and not transition_requests_by_study:
        return [_managed_study_action_without_provider_admission_state(action) for action in managed_study_actions]
    result: list[dict[str, Any]] = []
    for action in managed_study_actions:
        if not isinstance(action, Mapping):
            result.append(action)
            continue
        study_id = _text(action.get("study_id"))
        candidates = candidates_by_study.get(study_id or "")
        if not candidates:
            transition_requests = transition_requests_by_study.get(study_id or "")
            if transition_requests:
                result.append(_managed_study_action_with_no_provider_admission_state(action))
                continue
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


def _managed_study_action_with_no_provider_admission_state(
    action: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(action)
    result["provider_admission_candidates"] = []
    result["provider_admission_state"] = {
        "status": "none",
        "candidate_count": 0,
        "running_provider_attempt": False,
    }
    return result


def _managed_study_action_without_provider_admission_state(action: dict[str, Any] | Any) -> dict[str, Any] | Any:
    if not isinstance(action, Mapping):
        return action
    result = dict(action)
    if "provider_admission_candidates" in result or "provider_admission_state" in result:
        result["provider_admission_candidates"] = []
        result.pop("provider_admission_state", None)
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
        supervisor_decision = _mapping(recovery.get("supervisor_decision"))
        if supervisor_decision:
            result["supervisor_decision"] = dict(supervisor_decision)
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
    supervisor_decision = _mapping(result.get("supervisor_decision"))
    supervisor_gate = provider_admission_supervisor_gate(
        result,
        paper_recovery_state=recovery,
    )
    if supervisor_gate.get("blocked") is True:
        supervisor_decision = _mapping(supervisor_gate.get("supervisor_decision"))
        result["running_provider_attempt"] = False
        result["provider_admission_state"] = {
            "status": "blocked_by_paper_autonomy_supervisor_decision",
            "candidate_count": len(candidates),
            "running_provider_attempt": False,
            "supervisor_decision": dict(supervisor_decision),
            "paper_recovery_phase": _text(recovery.get("phase")),
            "paper_recovery_reason": _paper_recovery_reason(recovery),
            "next_safe_action": _mapping(recovery.get("next_safe_action")),
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
            "next_safe_action": _mapping(recovery.get("next_safe_action")),
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


def _paper_recovery_is_unresolved_current_work_unit_fallback(
    recovery: Mapping[str, Any],
) -> bool:
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    return any(
        isinstance(condition, Mapping)
        and _text(condition.get("condition")) == "current_work_unit_typed_blocker"
        and _text(condition.get("blocker_type")) == "current_work_unit_unresolved"
        for condition in recovery.get("conditions") or []
    ) and (
        _text(obligation.get("work_unit_id")) is None
        and _text(obligation.get("work_unit_fingerprint")) is None
    )


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
    if state_kind in {"typed_blocker", "blocked_current_work_unit"}:
        currentness_reason = (
            _current_work_unit_blocker_reason(current_work_unit)
            or _current_execution_blocker_reason(current_execution)
        )
        if _is_unresolved_current_work_unit_fallback(currentness_reason, current_work_unit):
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
