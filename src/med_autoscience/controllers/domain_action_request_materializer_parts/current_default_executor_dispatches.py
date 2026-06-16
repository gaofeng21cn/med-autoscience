from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Callable

from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode
from med_autoscience.profiles import WorkspaceProfile


CurrentActions = Callable[..., tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]]
DefaultDispatch = Callable[..., dict[str, Any]]
ReadJsonObject = Callable[[object], dict[str, Any] | None]
ResolveStudyIds = Callable[[Mapping[str, Any], Iterable[str]], tuple[str, ...]]
ScanPath = Callable[[WorkspaceProfile], object]


def current_default_executor_dispatches(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    generated_at: str,
    supported_mode: str,
    dispatch_ready_for_execution: bool,
    read_json_object: ReadJsonObject,
    scan_latest_path: ScanPath,
    resolve_study_ids_from_scan: ResolveStudyIds,
    selected_actions: CurrentActions,
    default_executor_dispatch: DefaultDispatch,
    owner_from_action: Callable[[Mapping[str, Any], str], str],
    required_output_surface: Callable[[Mapping[str, Any], str], str],
    text: Callable[[object], str | None],
) -> dict[str, Any]:
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="external_queue_consumer",
    )
    developer_mode_payload = developer_mode.to_dict()
    scan_payload = read_json_object(scan_latest_path(profile)) or {}
    resolved_study_ids = resolve_study_ids_from_scan(scan_payload, study_ids)
    selected_request_actions, ignored_actions = selected_actions(
        profile=profile,
        scan_payload=scan_payload,
        study_ids=resolved_study_ids,
    )
    dispatches = [
        default_executor_dispatch(
            profile=profile,
            action=action,
            action_type=text(action.get("action_type")) or "unknown_action",
            next_executable_owner=owner_from_action(
                action,
                text(action.get("action_type")) or "unknown_action",
            ),
            required_output_surface=required_output_surface(
                action,
                text(action.get("action_type")) or "unknown_action",
            ),
            apply=apply,
            developer_mode_payload=(
                _developer_mode_payload_for_dry_run_execution(
                    developer_mode_payload,
                    supported_mode=supported_mode,
                )
                if dispatch_ready_for_execution and not apply
                else developer_mode_payload
            ),
            scan_payload=scan_payload,
            generated_at=generated_at,
        )
        for action in selected_request_actions
    ]
    return {
        "surface": "domain_action_request_materializer.current_owner_callable_adapters",
        "schema_version": 1,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_studies": list(resolved_study_ids),
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "apply_allowed": bool(apply and developer_mode.safe_actions_enabled),
        "adapter_kind": "opl_authorized_owner_callable_adapter",
        "target_runtime_owner": "one-person-lab",
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "mas_dispatch_authority": False,
        "selected_action_count": len(selected_request_actions),
        "ignored_actions": ignored_actions,
        "owner_callable_adapter_count": len(dispatches),
        "ready_owner_callable_adapter_count": _dispatch_status_count(dispatches, "ready", text=text),
        "blocked_owner_callable_adapter_count": _dispatch_status_count(dispatches, "blocked", text=text),
        "owner_callable_adapters": dispatches,
        "default_executor_dispatch_count": len(dispatches),
        "ready_default_executor_dispatch_count": _dispatch_status_count(dispatches, "ready", text=text),
        "blocked_default_executor_dispatch_count": _dispatch_status_count(dispatches, "blocked", text=text),
        "repeat_suppressed_count": sum(item.get("repeat_suppressed") is True for item in dispatches),
        "default_executor_dispatches": dispatches,
        "default_executor_dispatches_compat_role": "derived_read_model_for_existing_selectors",
    }


def _developer_mode_payload_for_dry_run_execution(
    developer_mode_payload: Mapping[str, Any],
    *,
    supported_mode: str,
) -> dict[str, Any]:
    return {
        **dict(developer_mode_payload),
        "mode": supported_mode,
        "safe_actions_enabled": True,
        "dry_run_executor_dispatch": True,
    }


def _dispatch_status_count(
    dispatches: list[dict[str, Any]],
    status: str,
    *,
    text: Callable[[object], str | None],
) -> int:
    return sum(text(dispatch.get("dispatch_status")) == status for dispatch in dispatches)


__all__ = ["current_default_executor_dispatches"]
