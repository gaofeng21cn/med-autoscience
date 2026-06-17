from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import (
    domain_action_request_materializer,
    domain_owner_action_dispatch,
    owner_route_reconcile,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    handoff_dispatch_path,
    handoff_work_unit_id,
    materialized_record_only_provider_handoff,
    materialized_record_only_provider_handoffs,
    provider_probe_has_matching_attempt,
    provider_probe_has_non_running_actions,
    study_has_running_provider_attempt,
    transition_request_pending_dispatch_result,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.owner_callable_adapter_projection import (
    adapter_count,
    adapter_status_count,
    owner_callable_adapters,
)
from med_autoscience.profiles import WorkspaceProfile


PROGRESS_FIRST_SAME_TICK_MAX_PASSES = 3
PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS = 2.0
PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS = 1.0
PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT = 1


def _run_developer_supervisor_same_tick(
    *,
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...] = (),
    max_passes: int = PROGRESS_FIRST_SAME_TICK_MAX_PASSES,
    owner_route_reconcile_module: Any = owner_route_reconcile,
    domain_action_request_materializer_module: Any = domain_action_request_materializer,
    domain_owner_action_dispatch_module: Any = domain_owner_action_dispatch,
) -> dict[str, Any]:
    resolved_study_ids = (
        tuple(study_ids)
        or owner_route_reconcile_module.resolve_owner_route_reconcile_study_ids(profile)
    )
    retain_unscanned_studies = not bool(study_ids)
    iterations: list[dict[str, Any]] = []
    stop_reason = "max_passes_exhausted"
    carried_scan_result: dict[str, Any] | None = None
    carried_materialize_result: dict[str, Any] | None = None
    for pass_index in range(1, max(1, max_passes) + 1):
        if carried_scan_result is None:
            scan_result = owner_route_reconcile_module.scan_domain_routes(
                profile=profile,
                study_ids=resolved_study_ids,
                apply_safe_actions=True,
                developer_supervisor_mode="developer_apply_safe",
                live_attempt_timeout_seconds=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
                live_attempt_max_inspect_count=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
                provider_readiness_timeout_seconds=PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
                retain_unscanned_studies=retain_unscanned_studies,
            )
        else:
            scan_result = carried_scan_result
            carried_scan_result = None
        if carried_materialize_result is None:
            materialize_result = domain_action_request_materializer_module.materialize_domain_action_requests(
                profile=profile,
                study_ids=resolved_study_ids,
                mode="developer_apply_safe",
                apply=True,
            )
        else:
            materialize_result = carried_materialize_result
            carried_materialize_result = None
        if materialized_record_only_provider_handoff(materialize_result):
            dispatch_result = transition_request_pending_dispatch_result(
                materialize_result=materialize_result,
            )
        else:
            dispatch_result = domain_owner_action_dispatch_module.dispatch_domain_owner_actions(
                profile=profile,
                study_ids=resolved_study_ids,
                action_types=(),
                mode="developer_apply_safe",
                apply=True,
                consumer_payload=materialize_result,
            )
        iteration = {
            "pass_index": pass_index,
            "owner_route_reconcile": scan_result,
            "materialize": materialize_result,
            "dispatch": dispatch_result,
            "progress_first_delta": _same_tick_delta(
                scan_result=scan_result,
                materialize_result=materialize_result,
                dispatch_result=dispatch_result,
            ),
        }
        if _same_tick_handoff_written(iteration):
            iteration["provider_admission_probe"] = owner_route_reconcile_module.scan_domain_routes(
                profile=profile,
                study_ids=resolved_study_ids,
                apply_safe_actions=True,
                developer_supervisor_mode="developer_apply_safe",
                persist_surfaces=True,
                live_attempt_timeout_seconds=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
                live_attempt_max_inspect_count=PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
                provider_readiness_timeout_seconds=PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
                retain_unscanned_studies=retain_unscanned_studies,
            )
            provider_attempt_started = _provider_attempt_started_for_iteration(iteration)
            if (
                provider_attempt_started
                or materialized_record_only_provider_handoff(_mapping(iteration.get("materialize")))
            ):
                iteration["post_admission_materialize"] = domain_action_request_materializer_module.materialize_domain_action_requests(
                    profile=profile,
                    study_ids=resolved_study_ids,
                    mode="developer_apply_safe",
                    apply=True,
                )
                if provider_attempt_started and provider_probe_has_non_running_actions(
                    _mapping(iteration["provider_admission_probe"])
                ):
                    carried_scan_result = _mapping(iteration["provider_admission_probe"])
                    carried_materialize_result = _mapping(iteration["post_admission_materialize"])
        iterations.append(iteration)
        stop_reason = _same_tick_stop_reason(iteration)
        if stop_reason not in {
            "continue_same_tick_after_sync_owner_delta",
            "continue_same_tick_after_provider_admission_delta",
        }:
            break
    if stop_reason in {
        "continue_same_tick_after_sync_owner_delta",
        "continue_same_tick_after_provider_admission_delta",
    }:
        stop_reason = "max_passes_exhausted_owner_delta_required"
    terminal_diagnostic = _same_tick_terminal_diagnostic(
        stop_reason=stop_reason,
        iterations=iterations,
    )
    return {
        "surface": "developer_supervisor_same_tick",
        "schema_version": 1,
        "mode": "developer_apply_safe",
        "study_ids": list(resolved_study_ids),
        "max_passes": max(1, max_passes),
        "pass_count": len(iterations),
        "stop_reason": stop_reason,
        "actions": [
            "owner-route-reconcile",
            "domain-action-request-materialize",
            "domain-owner-action-dispatch",
        ],
        "provider_probe_budget": {
            "live_attempt_timeout_seconds": PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_TIMEOUT_SECONDS,
            "provider_readiness_timeout_seconds": PROGRESS_FIRST_SAME_TICK_PROVIDER_READINESS_TIMEOUT_SECONDS,
            "live_attempt_max_inspect_count": PROGRESS_FIRST_SAME_TICK_LIVE_ATTEMPT_MAX_INSPECT_COUNT,
            "scope": "focused_same_tick_owner_route_scan",
        },
        "iterations": iterations,
        "owner_route_reconcile": _mapping(iterations[-1].get("owner_route_reconcile")) if iterations else {},
        "materialize": _same_tick_terminal_materialize(iterations),
        "dispatch": _mapping(iterations[-1].get("dispatch")) if iterations else {},
        "progress_first_terminal_diagnostic": terminal_diagnostic,
        "owner_boundaries": {
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
        },
    }


def _same_tick_delta(
    *,
    scan_result: Mapping[str, Any],
    materialize_result: Mapping[str, Any],
    dispatch_result: Mapping[str, Any],
) -> dict[str, Any]:
    total_owner_callable_adapter_count = adapter_count(materialize_result)
    ready_owner_callable_adapter_count = adapter_status_count(materialize_result, "ready")
    blocked_owner_callable_adapter_count = adapter_status_count(materialize_result, "blocked")
    return {
        "scan_action_count": _count(scan_result, "action_queue"),
        "materialized_request_count": _int_value(materialize_result.get("request_task_count")),
        "owner_callable_adapter_count": ready_owner_callable_adapter_count,
        "owner_callable_adapter_total_count": total_owner_callable_adapter_count,
        "ready_owner_callable_adapter_count": ready_owner_callable_adapter_count,
        "blocked_owner_callable_adapter_count": blocked_owner_callable_adapter_count,
        "owner_callable_adapter_count": ready_owner_callable_adapter_count,
        "owner_callable_adapter_total_count": total_owner_callable_adapter_count,
        "ready_owner_callable_adapter_count": ready_owner_callable_adapter_count,
        "blocked_owner_callable_adapter_count": blocked_owner_callable_adapter_count,
        "dispatch_execution_count": _int_value(dispatch_result.get("execution_count")),
        "dispatch_executed_count": _int_value(dispatch_result.get("executed_count")),
        "dispatch_blocked_count": _int_value(dispatch_result.get("blocked_count")),
        "dispatch_repeat_suppressed_count": _int_value(dispatch_result.get("repeat_suppressed_count")),
        "codex_dispatch_count": _int_value(dispatch_result.get("codex_dispatch_count")),
        "handoff_ready_count": _execution_status_count(dispatch_result, "handoff_ready"),
    }


def _same_tick_stop_reason(iteration: Mapping[str, Any]) -> str:
    delta = _mapping(iteration.get("progress_first_delta"))
    if _same_tick_handoff_written(iteration):
        provider_admission_probe = _mapping(iteration.get("provider_admission_probe"))
        if _provider_attempt_started_for_iteration(iteration):
            if provider_probe_has_non_running_actions(provider_admission_probe):
                return "continue_same_tick_after_provider_admission_delta"
            return "provider_attempt_started"
        return "provider_handoff_written_transition_request_pending"
    if _int_value(delta.get("blocked_owner_callable_adapter_count")) > 0:
        return "typed_blocker_or_dispatch_blocker_observed"
    if _same_tick_provider_admission_blocker_written(iteration):
        return "provider_handoff_written_transition_request_pending"
    if _int_value(delta.get("dispatch_blocked_count")) > 0:
        return "typed_blocker_or_dispatch_blocker_observed"
    if _int_value(delta.get("dispatch_repeat_suppressed_count")) > 0:
        return "repeat_suppressed_owner_delta_required"
    if _int_value(delta.get("dispatch_executed_count")) > 0:
        return "continue_same_tick_after_sync_owner_delta"
    if _int_value(delta.get("owner_callable_adapter_count")) > 0:
        return "dispatch_materialized_but_not_selected"
    if _int_value(delta.get("scan_action_count")) > 0:
        return "owner_action_projected_but_not_materialized"
    return "no_owner_action_remaining"


def _same_tick_handoff_written(iteration: Mapping[str, Any]) -> bool:
    delta = _mapping(iteration.get("progress_first_delta"))
    return (
        _int_value(delta.get("codex_dispatch_count")) > 0
        or _int_value(delta.get("handoff_ready_count")) > 0
        or materialized_record_only_provider_handoff(_mapping(iteration.get("materialize")))
        or _same_tick_provider_admission_blocker_written(iteration)
    )


def _same_tick_provider_admission_blocker_written(iteration: Mapping[str, Any]) -> bool:
    return bool(_same_tick_provider_admission_blocker_executions(iteration))


def _same_tick_provider_admission_blocker_executions(iteration: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    dispatch = _mapping(iteration.get("dispatch"))
    current_identities = _same_tick_current_dispatch_identities(iteration)
    return [
        execution
        for execution in dispatch.get("executions") or []
        if isinstance(execution, Mapping)
        and _same_tick_provider_admission_blocker_execution(
            execution,
            current_identities=current_identities,
        )
    ]


def _same_tick_provider_admission_blocker_execution(
    execution: Mapping[str, Any],
    *,
    current_identities: list[Mapping[str, str]] | None = None,
) -> bool:
    if not (
        _non_empty_text(execution.get("execution_status")) == "blocked"
        and _non_empty_text(execution.get("blocked_reason")) == OPL_EXECUTION_AUTHORIZATION_BLOCKER
        and execution.get("provider_attempt_or_lease_required") is True
        and _non_empty_text(execution.get("dispatch_path")) is not None
        and _non_empty_text(execution.get("dispatch_authority")) is not None
    ):
        return False
    if current_identities is None:
        return True
    return any(
        _same_tick_identity_matches_execution(identity, execution=execution)
        for identity in current_identities
    )


def _same_tick_current_dispatch_identities(iteration: Mapping[str, Any]) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    identities.extend(
        _same_tick_action_identities(
            _mapping(iteration.get("owner_route_reconcile")).get("action_queue"),
        )
    )
    identities.extend(
        identity
        for identity in _same_tick_action_identities(
            owner_callable_adapters(_mapping(iteration.get("materialize"))),
        )
        if _same_tick_identity_has_currentness_anchor(identity)
    )
    return _dedupe_same_tick_identities(identities)


def _same_tick_action_identities(items: object) -> list[dict[str, str]]:
    identities: list[dict[str, str]] = []
    for item in items or []:
        if not isinstance(item, Mapping):
            continue
        identity = {
            key: value
            for key, value in {
                "study_id": _non_empty_text(item.get("study_id")),
                "action_type": _non_empty_text(item.get("action_type")),
                "work_unit_id": (
                    _non_empty_text(item.get("work_unit_id"))
                    or _non_empty_text(item.get("next_work_unit"))
                    or _non_empty_text(item.get("controller_work_unit_id"))
                    or _non_empty_text(_mapping(item.get("controller_next_work_unit")).get("unit_id"))
                    or handoff_work_unit_id(item)
                ),
                "action_fingerprint": _non_empty_text(item.get("action_fingerprint")),
                "work_unit_fingerprint": _non_empty_text(item.get("work_unit_fingerprint")),
                "dispatch_path": handoff_dispatch_path(item),
            }.items()
            if value is not None
        }
        if len(identity) > 1:
            identities.append(identity)
    return identities


def _same_tick_identity_matches_execution(
    identity: Mapping[str, str],
    *,
    execution: Mapping[str, Any],
) -> bool:
    for key in ("study_id", "action_type", "work_unit_id"):
        expected = _non_empty_text(identity.get(key))
        if expected is None:
            continue
        observed = _non_empty_text(execution.get(key))
        if observed is None:
            return False
        if observed != expected:
            return False
    expected_fingerprints = {
        value
        for key in ("action_fingerprint", "work_unit_fingerprint")
        if (value := _non_empty_text(identity.get(key))) is not None
    }
    if expected_fingerprints:
        observed_fingerprints = {
            value
            for key in ("action_fingerprint", "work_unit_fingerprint")
            if (value := _non_empty_text(execution.get(key))) is not None
        }
        if not observed_fingerprints or observed_fingerprints.isdisjoint(expected_fingerprints):
            return False
    expected_dispatch = _non_empty_text(identity.get("dispatch_path"))
    if expected_dispatch is None:
        return True
    observed_dispatch = _non_empty_text(execution.get("dispatch_path"))
    if observed_dispatch is None:
        return False
    return _same_tick_dispatch_ref_matches(expected_dispatch, observed_dispatch)


def _same_tick_identity_has_currentness_anchor(identity: Mapping[str, str]) -> bool:
    return any(
        _non_empty_text(identity.get(key)) is not None
        for key in ("work_unit_id", "action_fingerprint", "work_unit_fingerprint", "dispatch_path")
    )


def _same_tick_dispatch_ref_matches(expected: str, observed: str) -> bool:
    normalized_expected = expected.replace("\\", "/")
    normalized_observed = observed.replace("\\", "/")
    return (
        normalized_expected == normalized_observed
        or normalized_expected.endswith(f"/{normalized_observed}")
        or normalized_observed.endswith(f"/{normalized_expected}")
    )


def _dedupe_same_tick_identities(identities: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[tuple[str, str], ...]] = set()
    result: list[dict[str, str]] = []
    for identity in identities:
        key = tuple(sorted(identity.items()))
        if key in seen:
            continue
        seen.add(key)
        result.append(identity)
    return result


def _provider_attempt_started(scan_result: Mapping[str, Any]) -> bool:
    for study in scan_result.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        if study_has_running_provider_attempt(study):
            return True
    return False


def _provider_attempt_started_for_iteration(iteration: Mapping[str, Any]) -> bool:
    provider_admission_probe = _mapping(iteration.get("provider_admission_probe"))
    identities = _same_tick_handoff_identities(iteration)
    if not identities:
        return _provider_attempt_started(provider_admission_probe)
    return all(
        provider_probe_has_matching_attempt(provider_admission_probe, identity=identity)
        for identity in identities
    )


def _same_tick_handoff_identities(iteration: Mapping[str, Any]) -> list[dict[str, str]]:
    dispatch = _mapping(iteration.get("dispatch"))
    identities: list[dict[str, str]] = []
    for handoff in materialized_record_only_provider_handoffs(
        _mapping(iteration.get("materialize"))
    ):
        identity = {
            key: value
            for key, value in {
                "study_id": _non_empty_text(handoff.get("study_id")),
                "action_type": _non_empty_text(handoff.get("action_type")),
                "work_unit_id": handoff_work_unit_id(handoff),
                "dispatch_path": handoff_dispatch_path(handoff),
            }.items()
            if value is not None
        }
        if len(identity) > 1:
            identities.append(identity)
    for execution in dispatch.get("executions") or []:
        if not isinstance(execution, Mapping):
            continue
        if not (
            execution.get("will_start_llm") is True
            or _non_empty_text(execution.get("execution_status")) == "handoff_ready"
            or execution in _same_tick_provider_admission_blocker_executions(iteration)
        ):
            continue
        identity = {
            key: value
            for key in ("study_id", "action_type", "work_unit_id", "dispatch_path")
            if (value := _non_empty_text(execution.get(key))) is not None
        }
        if len(identity) > 1:
            identities.append(identity)
    return identities


def _same_tick_terminal_materialize(iterations: list[dict[str, Any]]) -> dict[str, Any]:
    if not iterations:
        return {}
    last_iteration = iterations[-1]
    post_admission_materialize = last_iteration.get("post_admission_materialize")
    if isinstance(post_admission_materialize, Mapping):
        return dict(post_admission_materialize)
    return _mapping(last_iteration.get("materialize"))


def _same_tick_terminal_diagnostic(
    *,
    stop_reason: str,
    iterations: list[dict[str, Any]],
) -> dict[str, Any]:
    last_iteration = iterations[-1] if iterations else {}
    last_delta = _mapping(last_iteration.get("progress_first_delta"))
    provider_admission_probe = _mapping(last_iteration.get("provider_admission_probe"))
    requires_next_owner_delta = stop_reason in {
        "repeat_suppressed_owner_delta_required",
        "max_passes_exhausted_owner_delta_required",
    }
    requires_opl_transition_readback = stop_reason == "provider_handoff_written_transition_request_pending"
    requires_dispatch_blocker_resolution = (
        stop_reason == "typed_blocker_or_dispatch_blocker_observed"
        and (
            _int_value(last_delta.get("blocked_owner_callable_adapter_count")) > 0
            or _int_value(last_delta.get("dispatch_blocked_count")) > 0
        )
    )
    return {
        "surface": "progress_first_developer_supervisor_terminal_diagnostic",
        "schema_version": 1,
        "stop_reason": stop_reason,
        "same_tick_terminal_projection": _same_tick_terminal_projection(
            stop_reason=stop_reason,
            last_iteration=last_iteration,
            last_delta=last_delta,
            provider_admission_probe=provider_admission_probe,
        ),
        "requires_next_owner_delta": requires_next_owner_delta,
        "requires_opl_transition_readback": requires_opl_transition_readback,
        "requires_dispatch_blocker_resolution": requires_dispatch_blocker_resolution,
        "dispatch_blocker_summary": (
            _dispatch_blocker_summary(last_iteration)
            if requires_dispatch_blocker_resolution
            else None
        ),
        "provider_admission_probe": (
            {
                "observed": False,
                "running_provider_attempt_count": 0,
                "study_ids": [
                    study.get("study_id")
                    for study in provider_admission_probe.get("studies") or []
                    if isinstance(study, Mapping) and _non_empty_text(study.get("study_id"))
                ],
            }
            if requires_opl_transition_readback
            else (
                {
                    "observed": True,
                    "running_provider_attempt_count": sum(
                        1
                        for study in provider_admission_probe.get("studies") or []
                        if isinstance(study, Mapping) and study.get("running_provider_attempt") is True
                    ),
                }
                if stop_reason == "provider_attempt_started"
                else None
            )
        ),
        "post_admission_materialize": (
            {
                "observed": isinstance(last_iteration.get("post_admission_materialize"), Mapping),
                "owner_callable_adapter_count": _int_value(
                    _mapping(last_iteration.get("post_admission_materialize")).get("owner_callable_adapter_count")
                ),
                "ready_owner_callable_adapter_count": _int_value(
                    _mapping(last_iteration.get("post_admission_materialize")).get(
                        "ready_owner_callable_adapter_count"
                    )
                ),
            }
            if isinstance(last_iteration.get("post_admission_materialize"), Mapping)
            else None
        ),
        "last_iteration_delta": dict(last_delta),
        "next_forced_delta": (
            {
                "required_delta_kind": (
                    "deliverable_progress_delta_or_domain_owner_receipt_or_typed_blocker"
                ),
                "reason": stop_reason,
                "target_surface": {
                    "surface_ref": "MAS owner receipt, domain typed blocker, or paper-facing deliverable delta",
                    "owner": "med-autoscience",
                },
                "acceptance_refs": [
                    "deliverable_progress_delta",
                    "domain_owner_receipt_ref",
                    "domain_typed_blocker_ref",
                    "human_gate_or_stop_loss_ref",
                ],
            }
            if requires_next_owner_delta
            else (
                {
                    "required_delta_kind": "opl_domain_progress_transition_readback",
                    "reason": stop_reason,
                    "target_surface": {
                        "surface_ref": "OPL DomainProgressTransitionRuntime event/outbox/StageRun readback",
                        "owner": "one-person-lab",
                    },
                    "acceptance_refs": [
                        "opl_domain_progress_transition_result.event_id",
                        "opl_domain_progress_transition_result.outbox_item_id",
                        "opl_domain_progress_transition_result.stage_run_id",
                        "opl_domain_progress_transition_result.stage_run_identity_ref",
                    ],
                    "recommended_owner_commands": [
                        "OPL DomainProgressTransitionRuntime intake",
                        "OPL StageRun lease or human gate readback",
                    ],
                }
                if requires_opl_transition_readback
                else (
                    {
                        "required_delta_kind": "dispatch_blocker_resolution_or_owner_route_currentness_delta",
                        "reason": stop_reason,
                        "target_surface": {
                            "surface_ref": "owner-route currentness basis, dispatch typed blocker, or domain owner receipt",
                            "owner": "med-autoscience",
                        },
                        "acceptance_refs": [
                            "currentness_contract.missing_required_fields == []",
                            "default_executor_dispatch.blocked_reason",
                            "domain_typed_blocker_ref",
                            "domain_owner_receipt_ref",
                        ],
                    }
                    if requires_dispatch_blocker_resolution
                    else None
                )
            )
        ),
        "forbidden_next_actions": (
            [
                "repeat_receipt_reconcile_without_owner_delta",
                "repeat_read_model_reconcile_without_owner_delta",
                "start_new_provider_attempt_for_same_source_without_owner_delta",
            ]
            if requires_next_owner_delta or requires_opl_transition_readback or requires_dispatch_blocker_resolution
            else []
        ),
    }


def _same_tick_terminal_projection(
    *,
    stop_reason: str,
    last_iteration: Mapping[str, Any],
    last_delta: Mapping[str, Any],
    provider_admission_probe: Mapping[str, Any],
) -> dict[str, Any]:
    provider_attempt_running = _provider_attempt_started_for_iteration(last_iteration)
    stable_typed_blocker_observed = stop_reason == "typed_blocker_or_dispatch_blocker_observed" and (
        _int_value(last_delta.get("blocked_owner_callable_adapter_count")) > 0
        or _int_value(last_delta.get("dispatch_blocked_count")) > 0
    )
    owner_delta_produced = stop_reason in {
        "repeat_suppressed_owner_delta_required",
        "max_passes_exhausted_owner_delta_required",
    }
    terminal_state = _same_tick_terminal_state(
        stop_reason=stop_reason,
        owner_delta_produced=owner_delta_produced,
        provider_attempt_running=provider_attempt_running,
        stable_typed_blocker_observed=stable_typed_blocker_observed,
    )
    return {
        "terminal_state": terminal_state,
        "owner_delta_produced": owner_delta_produced,
        "provider_attempt_running": provider_attempt_running,
        "stable_typed_blocker_observed": stable_typed_blocker_observed,
        "provider_handoff_written": _same_tick_handoff_written(last_iteration),
    }


def _same_tick_terminal_state(
    *,
    stop_reason: str,
    owner_delta_produced: bool,
    provider_attempt_running: bool,
    stable_typed_blocker_observed: bool,
) -> str:
    if provider_attempt_running:
        return "provider_attempt_running"
    if stable_typed_blocker_observed:
        return "stable_typed_blocker_observed"
    if owner_delta_produced:
        if stop_reason == "max_passes_exhausted_owner_delta_required":
            return "owner_delta_produced"
        return "owner_delta_required"
    return stop_reason


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _count(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, list):
        return len(value)
    return _int_value(value)


def _execution_status_count(payload: Mapping[str, Any], status: str) -> int:
    return sum(
        1
        for item in payload.get("executions") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("execution_status")) == status
    )


def _dispatch_blocker_summary(iteration: Mapping[str, Any]) -> dict[str, Any]:
    delta = _mapping(iteration.get("progress_first_delta"))
    materialize = _mapping(iteration.get("materialize"))
    dispatch = _mapping(iteration.get("dispatch"))
    blocked_reasons: list[str] = []
    blocked_actions: list[str] = []
    for item in owner_callable_adapters(materialize):
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("dispatch_status")) != "blocked":
            continue
        if (reason := _non_empty_text(item.get("blocked_reason"))) is not None and reason not in blocked_reasons:
            blocked_reasons.append(reason)
        if (action_type := _non_empty_text(item.get("action_type"))) is not None and action_type not in blocked_actions:
            blocked_actions.append(action_type)
    for item in dispatch.get("executions") or []:
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("execution_status")) != "blocked":
            continue
        if (reason := _non_empty_text(item.get("blocked_reason"))) is not None and reason not in blocked_reasons:
            blocked_reasons.append(reason)
        if (action_type := _non_empty_text(item.get("action_type"))) is not None and action_type not in blocked_actions:
            blocked_actions.append(action_type)
    return {
        "blocked_owner_callable_adapter_count": _int_value(delta.get("blocked_owner_callable_adapter_count")),
        "blocked_owner_callable_adapter_count": _int_value(delta.get("blocked_owner_callable_adapter_count")),
        "dispatch_blocked_count": _int_value(delta.get("dispatch_blocked_count")),
        "blocked_reasons": blocked_reasons,
        "blocked_actions": blocked_actions,
    }


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0
