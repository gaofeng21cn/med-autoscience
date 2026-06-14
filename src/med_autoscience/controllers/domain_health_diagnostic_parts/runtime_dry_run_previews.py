from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

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
    preview = materialize_domain_action_requests(
        profile=profile,
        study_ids=study_ids,
        mode="developer_apply_safe",
        apply=False,
    )
    report["domain_action_request_materialization_preview"] = preview
    report["materialization_preview_request_task_count"] = _int_value(
        preview.get("request_task_count")
    )
    report["materialization_preview_default_executor_dispatch_count"] = _int_value(
        preview.get("default_executor_dispatch_count")
    )
    report["materialization_preview_ready_default_executor_dispatch_count"] = _int_value(
        preview.get("ready_default_executor_dispatch_count")
    )
    report["materialization_preview_blocked_default_executor_dispatch_count"] = _int_value(
        preview.get("blocked_default_executor_dispatch_count")
    )


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
        "materialize_provider_admission_or_owner_callable",
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(values: object) -> list[str]:
    if isinstance(values, str):
        return [values] if values.strip() else []
    if not isinstance(values, list | tuple | set):
        return []
    return [text for item in values if (text := _non_empty_text(item)) is not None]


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
