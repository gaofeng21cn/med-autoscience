from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.authority_operation_command_catalog import AUTHORITY_OPERATION_COMMANDS_BY_COMMAND
from med_autoscience.controllers import (
    artifact_lifecycle_operations_report,
    continuous_soak_summary,
    delivery_authority_backfill_apply,
    product_entry,
    study_progress,
    workspace_authority_migration_audit,
)
from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS
from med_autoscience.profiles import WorkspaceProfile, load_profile


DISPLAY_PACK_DOMAIN_COMMANDS = frozenset(
    {
        "display-pack-capability-discover",
        "display-pack-orchestrate",
        "display-pack-figure-plan",
        "display-pack-preflight",
        "display-pack-render",
    }
)


class MedAutoScienceDomainEntry:
    """给 OPL framework、direct MAS skill 和 CLI 复用的 service-safe structured entry。"""

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

        if command in AUTHORITY_OPERATION_COMMANDS_BY_COMMAND:
            payload = _dispatch_authority_operation(command, request)
            return _with_command(command, payload)

        if command in DISPLAY_PACK_DOMAIN_COMMANDS:
            payload = _dispatch_display_pack_command(command, request)
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
        "study-progress": lambda: study_progress.read_study_progress(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            entry_mode=_optional_text(request.get("entry_mode")),
        ),
        "launch-study": lambda: product_entry.launch_study(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            entry_mode=_optional_text(request.get("entry_mode")),
            allow_stopped_relaunch=bool(request.get("allow_stopped_relaunch")),
            explicit_user_wakeup=bool(request.get("explicit_user_wakeup")),
            force=bool(request.get("force")),
        ),
        "submit-study-task": lambda: product_entry.submit_study_task(
            profile=profile,
            profile_ref=profile_ref,
            study_id=str(request["study_id"]),
            task_intent=str(request["task_intent"]),
            task_intake_kind=_optional_text(request.get("task_intake_kind")),
            entry_mode=_optional_text(request.get("entry_mode")),
            journal_target=_optional_text(request.get("journal_target")),
            constraints=_sequence_value(request.get("constraints")),
            evidence_boundary=_sequence_value(request.get("evidence_boundary")),
            trusted_inputs=_sequence_value(request.get("trusted_inputs")),
            reference_papers=_sequence_value(request.get("reference_papers")),
            first_cycle_outputs=_sequence_value(request.get("first_cycle_outputs")),
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
        raise ValueError("authority operation 缺少 workspace_roots。")
    paths: list[Path] = []
    for item in roots:
        text = str(item).strip()
        if not text:
            raise ValueError("authority operation workspace_roots 不能包含空值。")
        paths.append(Path(text).expanduser())
    return tuple(paths)


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _optional_int_value(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float_value(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_mapping_value(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _mapping_value(value: Any, *, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"display pack domain entry `{field_name}` 必须是 mapping。")
    return value


def _dispatch_display_pack_command(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    from med_autoscience import display_pack_agent

    repo_root = request.get("repo_root")
    paper_root = request.get("paper_root")
    if command == "display-pack-capability-discover":
        return display_pack_agent.display_pack_capability_discover(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            include_templates=_bool_value(request.get("include_templates")),
        )
    if command == "display-pack-orchestrate":
        figure_request = request.get("figure_request")
        current_owner_delta = request.get("current_owner_delta")
        return display_pack_agent.display_pack_orchestrate(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            current_owner_delta=(
                _mapping_value(current_owner_delta, field_name="current_owner_delta")
                if current_owner_delta is not None
                else None
            ),
            claim_ref=str(request.get("claim_ref") or ""),
            data_ref=str(request.get("data_ref") or ""),
            paper_target=str(request.get("paper_target") or ""),
            intent=str(request.get("intent") or ""),
            figure_request=(
                _mapping_value(figure_request, field_name="figure_request")
                if figure_request is not None
                else None
            ),
            max_recommendations=_optional_int_value(request.get("max_recommendations")) or 5,
            check_runtime_dependencies=_bool_value(request.get("check_runtime_dependencies"), default=True),
        )
    if command == "display-pack-figure-plan":
        return display_pack_agent.display_pack_figure_plan(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            figure_request=_mapping_value(request.get("figure_request"), field_name="figure_request"),
            max_recommendations=_optional_int_value(request.get("max_recommendations")) or 5,
        )
    if command == "display-pack-preflight":
        figure_request = request.get("figure_request")
        return display_pack_agent.display_pack_preflight(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=paper_root if paper_root is not None else None,
            template_id=_optional_text(request.get("template_id")),
            figure_request=(
                _mapping_value(figure_request, field_name="figure_request")
                if figure_request is not None
                else None
            ),
            check_runtime_dependencies=_bool_value(request.get("check_runtime_dependencies"), default=True),
        )
    if command == "display-pack-render":
        figure_request = request.get("figure_request")
        visual_audit_review = request.get("visual_audit_review")
        return display_pack_agent.display_pack_render(
            repo_root=repo_root if repo_root is not None else None,
            paper_root=Path(str(paper_root)).expanduser(),
            figure_request=(
                _mapping_value(figure_request, field_name="figure_request")
                if figure_request is not None
                else None
            ),
            visual_audit_review=(
                _mapping_value(visual_audit_review, field_name="visual_audit_review")
                if visual_audit_review is not None
                else None
            ),
        )
    raise ValueError(f"不支持的 display pack domain entry command: {command}")


def _dispatch_authority_operation(command: str, request: Mapping[str, Any]) -> dict[str, Any]:
    workspace_roots = _workspace_roots_value(request.get("workspace_roots"))
    if command == "workspace-authority-migration-audit":
        return workspace_authority_migration_audit.run_migration_audit(
            workspace_roots=workspace_roots,
            dry_run=True,
        )
    if command == "delivery-authority-backfill-apply":
        return delivery_authority_backfill_apply.run_backfill_apply(
            workspace_roots=workspace_roots,
            apply=_bool_value(request.get("apply")),
            authority_snapshot=_optional_mapping_value(request.get("authority_snapshot")),
        )
    if command == "artifact-lifecycle-report":
        return artifact_lifecycle_operations_report.run_lifecycle_operations_report(
            workspace_roots=workspace_roots,
            deep=_bool_value(request.get("deep")),
            max_files=_optional_int_value(request.get("max_files")),
            max_seconds=_optional_float_value(request.get("max_seconds")),
        )
    if command == "storage-governance-report":
        result = artifact_lifecycle_operations_report.run_lifecycle_operations_report(
            workspace_roots=workspace_roots,
            deep=_bool_value(request.get("deep")),
            max_files=_optional_int_value(request.get("max_files")),
            max_seconds=_optional_float_value(request.get("max_seconds")),
        )
        return {
            **result,
            "surface": "storage_governance_report",
            "source_surface": result.get("surface"),
        }
    if command == "artifact-lifecycle-continuous-soak-summary":
        return continuous_soak_summary.build_continuous_soak_summary(
            workspace_roots=workspace_roots,
            deep=_bool_value(request.get("deep")),
            max_files=_optional_int_value(request.get("max_files")),
            max_seconds=_optional_float_value(request.get("max_seconds")),
        )
    raise ValueError(f"不支持的 authority operation command: {command}")
