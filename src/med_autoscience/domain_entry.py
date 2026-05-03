from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.control_plane_command_catalog import CONTROL_PLANE_OPERATION_COMMANDS_BY_COMMAND
from med_autoscience.controllers import (
    artifact_lifecycle_operations_report,
    control_plane_cleanup_apply,
    control_plane_migration_audit,
    product_entry,
    study_progress,
    study_runtime_router,
)
from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS
from med_autoscience.profiles import WorkspaceProfile, load_profile


class MedAutoScienceDomainEntry:
    """给 OPL / Gateway / CLI 复用的 service-safe structured entry。"""

    def __init__(
        self,
        *,
        profile_loader: Callable[[str | Path], WorkspaceProfile] | None = None,
    ) -> None:
        self._profile_loader = profile_loader or load_profile

    def dispatch(self, request: Mapping[str, Any]) -> dict[str, Any]:
        command = _require_command(request)
        spec = SERVICE_SAFE_DOMAIN_COMMANDS.get(command)
        if spec is None:
            raise ValueError(f"不支持的 domain entry command: {command}")

        _assert_required_fields(command=command, required_fields=spec.required_fields, request=request)

        if command in CONTROL_PLANE_OPERATION_COMMANDS_BY_COMMAND:
            payload = _dispatch_control_plane_operation(command, request)
            return _with_command(command, payload)

        profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
        profile = self._profile_loader(profile_ref)
        payload = _dispatch_profile_command(
            command=command,
            request=request,
            profile=profile,
            profile_ref=profile_ref,
        )

        return _with_command(command, payload)


def _assert_required_fields(
    *,
    command: str,
    required_fields: tuple[str, ...],
    request: Mapping[str, Any],
) -> None:
    missing_fields = [
        field_name for field_name in required_fields if not _has_structured_value(request.get(field_name))
    ]
    if missing_fields:
        raise ValueError(f"domain entry `{command}` 缺少必填字段: {', '.join(missing_fields)}")


def _with_command(command: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise TypeError(f"domain entry `{command}` 返回值必须是 mapping。")
        if "command" in payload:
            return payload
        return {"command": command, **payload}


def _dispatch_profile_command(
    *,
    command: str,
    request: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
) -> dict[str, Any]:
    handlers = {
        "workspace-cockpit": lambda: product_entry.read_workspace_cockpit(profile=profile, profile_ref=profile_ref),
        "product-frontdesk": lambda: product_entry.build_product_frontdesk(profile=profile, profile_ref=profile_ref),
        "product-preflight": lambda: product_entry.build_product_entry_preflight(profile=profile, profile_ref=profile_ref),
        "product-start": lambda: product_entry.build_product_entry_start(profile=profile, profile_ref=profile_ref),
        "product-entry-manifest": lambda: product_entry.build_product_entry_manifest(
            profile=profile,
            profile_ref=profile_ref,
        ),
        "skill-catalog": lambda: product_entry.build_skill_catalog(profile=profile, profile_ref=profile_ref),
        "study-progress": lambda: study_progress.read_study_progress(
            profile=profile,
            study_id=str(request["study_id"]),
            entry_mode=_optional_text(request.get("entry_mode")),
        ),
        "study-runtime-status": lambda: product_entry._serialize_runtime_status(
            study_runtime_router.study_runtime_status(
                profile=profile,
                study_id=str(request["study_id"]),
                entry_mode=_optional_text(request.get("entry_mode")),
            )
        ),
        "launch-study": lambda: product_entry.launch_study(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            entry_mode=_optional_text(request.get("entry_mode")),
            allow_stopped_relaunch=bool(request.get("allow_stopped_relaunch")),
            force=bool(request.get("force")),
        ),
        "submit-study-task": lambda: product_entry.submit_study_task(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            task_intent=str(request["task_intent"]),
            entry_mode=_optional_text(request.get("entry_mode")),
            journal_target=_optional_text(request.get("journal_target")),
            constraints=_sequence_value(request.get("constraints")),
            evidence_boundary=_sequence_value(request.get("evidence_boundary")),
            trusted_inputs=_sequence_value(request.get("trusted_inputs")),
            reference_papers=_sequence_value(request.get("reference_papers")),
            first_cycle_outputs=_sequence_value(request.get("first_cycle_outputs")),
        ),
        "build-product-entry": lambda: product_entry.build_product_entry(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            direct_entry_mode=_optional_text(request.get("direct_entry_mode")),
        ),
    }
    try:
        return handlers[command]()
    except KeyError as exc:
        raise ValueError(f"不支持的 profile domain entry command: {command}") from exc


def _require_command(request: Mapping[str, Any]) -> str:
    if not isinstance(request, Mapping):
        raise ValueError("domain entry request 必须是 mapping。")
    command = request.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ValueError("domain entry request 缺少 command。")
    return command.strip()


def _has_structured_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sequence_value(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return (value,)


def _workspace_roots_value(value: Any) -> tuple[Path, ...]:
    roots = _sequence_value(value)
    if not roots:
        raise ValueError("control-plane operation 缺少 workspace_roots。")
    paths: list[Path] = []
    for item in roots:
        text = str(item).strip()
        if not text:
            raise ValueError("control-plane operation workspace_roots 不能包含空值。")
        paths.append(Path(text).expanduser())
    return tuple(paths)


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _dispatch_control_plane_operation(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    workspace_roots = _workspace_roots_value(request.get("workspace_roots"))
    if command == "control-plane-migration-audit":
        return control_plane_migration_audit.run_migration_audit(
            workspace_roots=workspace_roots,
            dry_run=True,
        )
    if command == "control-plane-cleanup-apply":
        return control_plane_cleanup_apply.run_cleanup_apply(
            workspace_roots=workspace_roots,
            apply=_bool_value(request.get("apply")),
        )
    if command == "control-plane-lifecycle-report":
        return artifact_lifecycle_operations_report.run_lifecycle_operations_report(
            workspace_roots=workspace_roots,
        )
    raise ValueError(f"不支持的 control-plane operation command: {command}")
