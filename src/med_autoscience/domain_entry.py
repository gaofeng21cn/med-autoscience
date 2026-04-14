from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.controllers import product_entry, study_progress, study_runtime_router
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

        missing_fields = [
            field_name for field_name in spec.required_fields if not _has_structured_value(request.get(field_name))
        ]
        if missing_fields:
            raise ValueError(f"domain entry `{command}` 缺少必填字段: {', '.join(missing_fields)}")

        profile_ref = Path(str(request["profile_ref"])).expanduser().resolve()
        profile = self._profile_loader(profile_ref)

        if command == "workspace-cockpit":
            payload = product_entry.read_workspace_cockpit(profile=profile, profile_ref=profile_ref)
        elif command == "product-frontdesk":
            payload = product_entry.build_product_frontdesk(profile=profile, profile_ref=profile_ref)
        elif command == "product-preflight":
            payload = product_entry.build_product_entry_preflight(profile=profile, profile_ref=profile_ref)
        elif command == "product-start":
            payload = product_entry.build_product_entry_start(profile=profile, profile_ref=profile_ref)
        elif command == "product-entry-manifest":
            payload = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
        elif command == "study-progress":
            payload = study_progress.read_study_progress(
                profile=profile,
                study_id=str(request["study_id"]),
                entry_mode=_optional_text(request.get("entry_mode")),
            )
        elif command == "study-runtime-status":
            payload = product_entry._serialize_runtime_status(
                study_runtime_router.study_runtime_status(
                    profile=profile,
                    study_id=str(request["study_id"]),
                    entry_mode=_optional_text(request.get("entry_mode")),
                )
            )
        elif command == "launch-study":
            payload = product_entry.launch_study(
                profile=profile,
                profile_ref=profile_ref,
                study_id=str(request["study_id"]),
                entry_mode=_optional_text(request.get("entry_mode")),
                allow_stopped_relaunch=bool(request.get("allow_stopped_relaunch")),
                force=bool(request.get("force")),
            )
        elif command == "submit-study-task":
            payload = product_entry.submit_study_task(
                profile=profile,
                study_id=str(request["study_id"]),
                task_intent=str(request["task_intent"]),
                entry_mode=_optional_text(request.get("entry_mode")),
                journal_target=_optional_text(request.get("journal_target")),
                constraints=_sequence_value(request.get("constraints")),
                evidence_boundary=_sequence_value(request.get("evidence_boundary")),
                trusted_inputs=_sequence_value(request.get("trusted_inputs")),
                reference_papers=_sequence_value(request.get("reference_papers")),
                first_cycle_outputs=_sequence_value(request.get("first_cycle_outputs")),
            )
        else:
            payload = product_entry.build_product_entry(
                profile=profile,
                profile_ref=profile_ref,
                study_id=str(request["study_id"]),
                direct_entry_mode=_optional_text(request.get("direct_entry_mode")),
            )

        if not isinstance(payload, dict):
            raise TypeError(f"domain entry `{command}` 返回值必须是 mapping。")
        if "command" in payload:
            return payload
        return {"command": command, **payload}


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
