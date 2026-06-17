from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.owner_callable_adapter_projection import (
    adapter_count,
    adapter_status_count,
    domain_progress_transition_requests,
    transition_request_count,
    transition_request_status_count,
    with_owner_callable_adapter_projection,
)
from med_autoscience.profiles import WorkspaceProfile


MaterializeDomainActionRequests = Callable[..., dict[str, Any]]
ExportFamilyDomainHandler = Callable[..., dict[str, Any]]


def attach_domain_action_request_materialization_preview(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    materialize_domain_action_requests: MaterializeDomainActionRequests,
) -> None:
    if not _report_requests_recovery_materialization(report):
        return
    preview = with_owner_callable_adapter_projection(
        materialize_domain_action_requests(
            profile=profile,
            study_ids=study_ids,
            mode="developer_apply_safe",
            apply=False,
            dispatch_ready_for_execution=True,
        )
    )
    report["domain_action_request_materialization_preview"] = preview
    report["materialization_preview_request_task_count"] = _int_value(
        preview.get("request_task_count")
    )
    report["materialization_preview_transition_request_count"] = transition_request_count(preview)
    report["materialization_preview_transition_request_pending_count"] = (
        transition_request_status_count(preview, "transition_request_pending")
    )
    report["materialization_preview_owner_callable_adapter_count"] = transition_request_count(preview)
    report["materialization_preview_ready_owner_callable_adapter_count"] = transition_request_status_count(
        preview,
        "ready",
    )
    report["materialization_preview_blocked_owner_callable_adapter_count"] = transition_request_status_count(
        preview,
        "blocked",
    )
    report["materialization_preview_transition_request_pending_owner_callable_adapter_count"] = (
        transition_request_status_count(preview, "transition_request_pending")
    )
    report["materialization_preview_legacy_owner_callable_adapter_count"] = adapter_count(preview)
    report["materialization_preview_legacy_ready_owner_callable_adapter_count"] = adapter_status_count(
        preview,
        "ready",
    )
    report["materialization_preview_legacy_blocked_owner_callable_adapter_count"] = adapter_status_count(
        preview,
        "blocked",
    )
    _attach_materialization_preview_to_managed_actions(report=report, preview=preview)
    _sync_transition_request_preview_to_report(report=report, preview=preview)


def attach_domain_handler_owner_resolution_preview(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    export_family_domain_handler: ExportFamilyDomainHandler,
) -> None:
    if not _report_requests_owner_resolution(report):
        return
    profile_ref = profile.profile_ref
    if profile_ref is None:
        report["domain_handler_owner_resolution_preview_status"] = "profile_ref_missing"
        return
    exported = export_family_domain_handler(profile=profile, profile_ref=profile_ref)
    requested = set(_text_items(study_ids))
    tasks = [
        dict(task)
        for task in exported.get("pending_family_tasks") or []
        if isinstance(task, Mapping)
        and _non_empty_text(task.get("task_kind")) == "domain_route/reconcile-apply"
        and (
            not requested
            or _non_empty_text(_mapping(task.get("payload")).get("study_id")) in requested
            or _non_empty_text(task.get("study_id")) in requested
        )
    ]
    report["domain_handler_owner_resolution_preview"] = {
        "surface": "domain_handler_owner_resolution_preview",
        "schema_version": 1,
        "dry_run": True,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    report["domain_handler_owner_resolution_preview_task_count"] = len(tasks)
    _attach_owner_resolution_preview_to_managed_actions(report=report, tasks=tasks)


def _attach_materialization_preview_to_managed_actions(
    *,
    report: dict[str, Any],
    preview: Mapping[str, Any],
) -> None:
    actions = report.get("managed_study_actions")
    if not isinstance(actions, list):
        return
    request_tasks_by_study = _items_by_study(preview.get("request_tasks"))
    legacy_adapters_by_study = _items_by_study(preview.get("owner_callable_adapters"))
    transition_requests_by_study = _items_by_study(domain_progress_transition_requests(preview))
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None:
            continue
        request_tasks = request_tasks_by_study.get(study_id, [])
        legacy_adapters = legacy_adapters_by_study.get(study_id, [])
        transition_requests = transition_requests_by_study.get(study_id, [])
        if not request_tasks and not transition_requests:
            continue
        updated = dict(action)
        updated["domain_action_request_materialization_preview"] = {
            "surface": "domain_action_request_materialization_preview",
            "schema_version": 1,
            "dry_run": bool(preview.get("dry_run", True)),
            "study_id": study_id,
            "request_task_count": len(request_tasks),
            "transition_request_count": len(transition_requests),
            "transition_request_pending_count": sum(
                _non_empty_text(item.get("dispatch_status")) == "transition_request_pending"
                for item in transition_requests
            ),
            "owner_callable_adapter_count": len(transition_requests),
            "ready_owner_callable_adapter_count": sum(
                _non_empty_text(item.get("dispatch_status")) == "ready"
                for item in transition_requests
            ),
            "blocked_owner_callable_adapter_count": sum(
                _non_empty_text(item.get("dispatch_status")) == "blocked"
                for item in transition_requests
            ),
            "transition_request_pending_owner_callable_adapter_count": sum(
                _non_empty_text(item.get("dispatch_status")) == "transition_request_pending"
                for item in transition_requests
            ),
            "legacy_owner_callable_adapter_count": len(legacy_adapters),
            "request_tasks": request_tasks,
            "domain_progress_transition_requests": transition_requests,
        }
        actions[index] = updated


def _sync_transition_request_preview_to_report(
    *,
    report: dict[str, Any],
    preview: Mapping[str, Any],
) -> None:
    transition_requests = [
        _transition_request_projection(request)
        for request in domain_progress_transition_requests(preview)
    ]
    transition_requests = [item for item in transition_requests if item]
    if not transition_requests:
        return
    existing = [
        dict(item)
        for item in report.get("managed_study_opl_transition_request_candidates") or []
        if isinstance(item, Mapping)
    ]
    merged = _merge_transition_request_candidates(existing, transition_requests)
    report["managed_study_opl_transition_request_candidates"] = merged
    report["transition_request_pending_count"] = len(merged)
    report.setdefault("provider_admission_pending_count", 0)
    current_execution_evidence = _mapping(report.get("current_execution_evidence"))
    current_execution_evidence["transition_request_candidates"] = merged
    current_execution_evidence.setdefault(
        "provider_admission_candidates",
        [
            dict(item)
            for item in report.get("managed_study_opl_provider_admission_candidates") or []
            if isinstance(item, Mapping)
        ],
    )
    report["current_execution_evidence"] = current_execution_evidence
    report["action_fingerprints"] = _merged_action_fingerprints(
        report.get("action_fingerprints"),
        merged,
    )


def _transition_request_projection(adapter: Mapping[str, Any]) -> dict[str, Any]:
    projection = dict(adapter)
    transition_request = _mapping(projection.get("opl_domain_progress_transition_request"))
    request_basis = _mapping(transition_request.get("currentness_basis"))
    if request_basis and not _mapping(projection.get("currentness_basis")):
        projection["currentness_basis"] = dict(request_basis)
    projection.setdefault("status", "transition_request_pending")
    projection.setdefault("provider_admission_pending", False)
    projection.setdefault("provider_attempt_or_lease_required", False)
    projection.setdefault("provider_admission_requires_opl_runtime_result", True)
    projection.setdefault("opl_transition_runtime_required", True)
    projection.setdefault(
        "source",
        _non_empty_text(adapter.get("source")) or "domain_action_request_materialization_preview",
    )
    projection.setdefault("same_tick_materialization_source", "dry_run_preview")
    return projection


def _merge_transition_request_candidates(
    existing: list[dict[str, Any]],
    incoming: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for item in [*existing, *incoming]:
        key = (
            _non_empty_text(item.get("study_id")),
            _non_empty_text(item.get("action_type")),
            _non_empty_text(item.get("work_unit_id")),
            _non_empty_text(item.get("work_unit_fingerprint"))
            or _non_empty_text(item.get("action_fingerprint")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(dict(item))
    return merged


def _merged_action_fingerprints(
    existing: object,
    transition_requests: list[dict[str, Any]],
) -> list[str]:
    values = _text_items(existing)
    for item in transition_requests:
        fingerprint = _non_empty_text(item.get("work_unit_fingerprint")) or _non_empty_text(
            item.get("action_fingerprint")
        )
        if fingerprint is not None:
            values.append(fingerprint)
    return list(dict.fromkeys(values))


def _attach_owner_resolution_preview_to_managed_actions(
    *,
    report: dict[str, Any],
    tasks: list[dict[str, Any]],
) -> None:
    actions = report.get("managed_study_actions")
    if not isinstance(actions, list):
        return
    tasks_by_study = _items_by_study(tasks)
    for index, action in enumerate(actions):
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None:
            continue
        study_tasks = tasks_by_study.get(study_id, [])
        if not study_tasks:
            continue
        updated = dict(action)
        updated["domain_handler_owner_resolution_preview"] = {
            "surface": "domain_handler_owner_resolution_preview",
            "schema_version": 1,
            "dry_run": True,
            "study_id": study_id,
            "task_count": len(study_tasks),
            "tasks": study_tasks,
        }
        actions[index] = updated


def _report_requests_owner_resolution(report: Mapping[str, Any]) -> bool:
    for recovery in _mapping(report.get("paper_recovery_states")).values():
        if _recovery_requests_owner_resolution(_mapping(recovery)):
            return True
    for action in report.get("managed_study_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if _recovery_requests_owner_resolution(_mapping(action.get("paper_recovery_state"))):
            return True
    return False


def _recovery_requests_owner_resolution(recovery: Mapping[str, Any]) -> bool:
    if not recovery:
        return False
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) == "materialize_successor_owner_gate":
        return True
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    return _non_empty_text(supervisor_decision.get("decision")) == "stop_with_stable_typed_blocker"


def _report_requests_recovery_materialization(report: Mapping[str, Any]) -> bool:
    for recovery in _mapping(report.get("paper_recovery_states")).values():
        if _recovery_requests_materialization(_mapping(recovery)):
            return True
    for action in report.get("managed_study_actions") or []:
        if not isinstance(action, Mapping):
            continue
        if _recovery_requests_materialization(_mapping(action.get("paper_recovery_state"))):
            return True
    return False


def _recovery_requests_materialization(recovery: Mapping[str, Any]) -> bool:
    if not recovery:
        return False
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    if _non_empty_text(supervisor_decision.get("decision")) == "materialize_recovery_action":
        return True
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    return _non_empty_text(next_safe_action.get("kind")) in {
        "run_mas_owner_callable",
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
        "materialize_mas_transition_request_or_owner_callable",
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(values: object) -> list[str]:
    if isinstance(values, str):
        return [values] if values.strip() else []
    if not isinstance(values, list | tuple | set):
        return []
    return [text for item in values if (text := _non_empty_text(item)) is not None]


def _items_by_study(items: object) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    if not isinstance(items, list):
        return grouped
    for item in items:
        if not isinstance(item, Mapping):
            continue
        study_id = (
            _non_empty_text(item.get("study_id"))
            or _non_empty_text(_mapping(item.get("payload")).get("study_id"))
        )
        if study_id is None:
            continue
        grouped.setdefault(study_id, []).append(dict(item))
    return grouped


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "attach_domain_action_request_materialization_preview",
    "attach_domain_handler_owner_resolution_preview",
]
