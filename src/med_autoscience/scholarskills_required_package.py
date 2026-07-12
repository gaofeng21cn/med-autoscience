from __future__ import annotations

import json
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


SCHOLARSKILLS_PACKAGE_ID = "mas-scholar-skills"
SCHOLARSKILLS_CAPABILITY_ABI = "mas-scholar-skills.v1"
SCHOLARSKILLS_VERSION_REQUIREMENT = ">=0.1.0 <0.2.0"
SCHOLARSKILLS_PROVIDER_MANIFEST_REF = (
    "external:mas-scholar-skills/contracts/opl_capability_package_manifest.json"
)
SCHOLARSKILLS_REQUIRED_PACKAGE_READBACK_REF = (
    "readback:opl_packages_status_mas#dependency_readiness/mas-scholar-skills"
)
SCHOLARSKILLS_REQUIRED_SKILL_IDS = (
    "mas-scholar-skills",
    "medical-manuscript-writing",
    "medical-manuscript-review",
    "medical-figure-design",
    "medical-figure-style",
    "medical-figure-composer",
    "medical-research-lit",
    "medical-statistical-review",
    "medical-table-design",
    "medical-submission-prep",
    "medical-data-governance",
)
SCHOLARSKILLS_REQUIRED_MODULE_IDS = (
    "mas-scholar-skills.display",
    "mas-scholar-skills.tables",
    "mas-scholar-skills.stats",
    "mas-scholar-skills.lit",
    "mas-scholar-skills.write",
    "mas-scholar-skills.review",
    "mas-scholar-skills.submit",
    "mas-scholar-skills.data",
)
SCHOLARSKILLS_REQUIRED_EXPORT_IDS = SCHOLARSKILLS_REQUIRED_SKILL_IDS
SCHOLARSKILLS_REQUIRED_INTERFACE_IDS = (
    *SCHOLARSKILLS_REQUIRED_EXPORT_IDS,
    *SCHOLARSKILLS_REQUIRED_MODULE_IDS,
)
MAS_PACKAGE_STATUS_COMMAND = (
    "opl",
    "packages",
    "status",
    "--package-id",
    "mas",
)
MAS_PACKAGE_REPAIR_COMMAND = (
    "opl",
    "packages",
    "repair",
    "--package-id",
    "mas",
)


def build_scholarskills_required_package_template() -> dict[str, Any]:
    return {
        "surface_kind": "mas_required_capability_package",
        "schema_version": 1,
        "package_id": SCHOLARSKILLS_PACKAGE_ID,
        "required": True,
        "dependency_kind": "hard_runtime_dependency",
        "version_requirement": SCHOLARSKILLS_VERSION_REQUIREMENT,
        "capability_abi": SCHOLARSKILLS_CAPABILITY_ABI,
        "required_skill_ids": list(SCHOLARSKILLS_REQUIRED_SKILL_IDS),
        "required_module_ids": list(SCHOLARSKILLS_REQUIRED_MODULE_IDS),
        "required_export_ids": list(SCHOLARSKILLS_REQUIRED_EXPORT_IDS),
        "required_interface_ids": list(SCHOLARSKILLS_REQUIRED_INTERFACE_IDS),
        "provider_manifest_ref": SCHOLARSKILLS_PROVIDER_MANIFEST_REF,
        "install_owner": "one-person-lab",
        "install_surface": "opl_packages",
        "user_install_action_count": 1,
        "missing_or_incompatible_policy": "fail_closed_to_doctor_and_repair",
        "status_command_templates": _scope_command_templates(
            MAS_PACKAGE_STATUS_COMMAND
        ),
        "repair_command_templates": _scope_command_templates(
            MAS_PACKAGE_REPAIR_COMMAND
        ),
        "optional_named_specialties_are_readiness_requirements": False,
        "activation_materialization": {
            "required": True,
            "owner": "one-person-lab",
            "trigger": "mas_workspace_or_quest_activation",
            "scopes": ["workspace", "quest"],
            "target_path_template": "<scope-root>/.codex/skills/<skill-id>",
            "required_skill_ids_source": "provider_manifest_exports_core_skill_ids",
            "receipt_required": True,
            "readiness_policy": "all_core_skills_current_for_active_scope",
        },
        "authority_boundary": {
            "provider_can_write_mas_domain_truth": False,
            "provider_can_sign_owner_receipt": False,
            "provider_can_create_typed_blocker": False,
            "provider_can_claim_mas_operational_readiness": False,
        },
    }


def build_scholarskills_required_package_readback(
    opl_package_status: Mapping[str, Any] | None,
    *,
    required_scope: str = "workspace",
    target_root: Path | str | None = None,
    query_error: str | None = None,
) -> dict[str, Any]:
    requirement = build_scholarskills_required_package_template()
    status_surface = _status_surface(opl_package_status)
    dependency = _dependency_status(status_surface)
    observed_export_ids = _text_set(dependency.get("export_ids"))
    observed_module_ids = _text_set(dependency.get("module_ids"))
    missing_export_ids = sorted(
        set(SCHOLARSKILLS_REQUIRED_EXPORT_IDS) - observed_export_ids
    )
    missing_module_ids = sorted(
        set(SCHOLARSKILLS_REQUIRED_MODULE_IDS) - observed_module_ids
    )
    observed_abi = _text(dependency.get("capability_abi"))
    observed_digest = _text(dependency.get("content_digest"))
    observed_version = _text(dependency.get("installed_version"))
    dependency_status = _text(dependency.get("status"))
    resolved_target_root = str(Path(target_root).expanduser().resolve()) if target_root else None
    status_command = _scoped_package_command(
        MAS_PACKAGE_STATUS_COMMAND,
        scope=required_scope,
        target_root=resolved_target_root or f"<{required_scope}-root>",
    )
    repair_command = _scoped_package_command(
        MAS_PACKAGE_REPAIR_COMMAND,
        scope=required_scope,
        target_root=resolved_target_root or f"<{required_scope}-root>",
    )
    materialization = _materialization_status(
        status_surface,
        required_scope=required_scope,
        target_root=resolved_target_root,
    )
    observed_materialized_skill_ids = _text_set(materialization.get("skill_ids"))
    missing_materialized_skill_ids = sorted(
        set(SCHOLARSKILLS_REQUIRED_SKILL_IDS) - observed_materialized_skill_ids
    )
    materialization_status = _text(materialization.get("status"))
    materialization_receipt_ref = _text(materialization.get("receipt_ref"))
    launch_allowed = status_surface.get("launch_allowed") is True
    launch_blocked_reason = _text(status_surface.get("launch_blocked_reason"))

    if not opl_package_status:
        status = "status_unavailable"
    elif not dependency:
        status = "missing"
    elif dependency_status == "missing":
        status = "missing"
    elif (
        dependency_status != "current"
        or observed_abi != SCHOLARSKILLS_CAPABILITY_ABI
        or not observed_version
        or not _is_sha256(observed_digest)
        or missing_export_ids
        or missing_module_ids
    ):
        status = "incompatible"
    else:
        status = "current"

    if status == "current" and (
        materialization_status != "current"
        or missing_materialized_skill_ids
        or not materialization_receipt_ref
        or _text(materialization.get("expected_digest"))
        != _text(materialization.get("actual_digest"))
    ):
        status = "scope_materialization_missing_or_stale"
    if status == "current" and not launch_allowed:
        status = "launch_blocked"

    operational_ready = status == "current"
    return {
        **requirement,
        "surface_kind": "mas_required_capability_package_readback",
        "status": status,
        "operational_ready": operational_ready,
        "observed_version": observed_version,
        "observed_capability_abi": observed_abi,
        "observed_content_digest": observed_digest,
        "observed_export_ids": sorted(observed_export_ids),
        "missing_export_ids": missing_export_ids,
        "observed_module_ids": sorted(observed_module_ids),
        "missing_module_ids": missing_module_ids,
        "required_scope": required_scope,
        "target_root": resolved_target_root,
        "package_dependency_status": dependency_status or "missing",
        "scope_materialization_status": materialization_status or "missing",
        "observed_materialized_skill_ids": sorted(observed_materialized_skill_ids),
        "missing_materialized_skill_ids": missing_materialized_skill_ids,
        "materialization_receipt_ref": materialization_receipt_ref,
        "launch_allowed": launch_allowed,
        "launch_blocked_reason": launch_blocked_reason,
        "allowed_when_blocked": _text_list(
            status_surface.get("allowed_when_blocked")
        ),
        "query_error": query_error,
        "repair_required": not operational_ready,
        "status_command": status_command,
        "repair_command": repair_command,
    }


def query_scholarskills_required_package_readback(
    *,
    workspace_root: Path | str,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    status_command = _scoped_package_command(
        MAS_PACKAGE_STATUS_COMMAND,
        scope="workspace",
        target_root=str(resolved_workspace_root),
    )
    try:
        result = runner(
            status_command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return build_scholarskills_required_package_readback(
            None,
            target_root=resolved_workspace_root,
            query_error=f"opl_packages_status_unavailable:{type(exc).__name__}",
        )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return build_scholarskills_required_package_readback(
            None,
            target_root=resolved_workspace_root,
            query_error=f"opl_packages_status_failed:{result.returncode}:{detail}",
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return build_scholarskills_required_package_readback(
            None,
            target_root=resolved_workspace_root,
            query_error=f"opl_packages_status_invalid_json:{exc.msg}",
        )
    if not isinstance(payload, Mapping):
        return build_scholarskills_required_package_readback(
            None,
            target_root=resolved_workspace_root,
            query_error="opl_packages_status_not_mapping",
        )
    return build_scholarskills_required_package_readback(
        payload,
        target_root=resolved_workspace_root,
    )


def _status_surface(opl_package_status: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(opl_package_status, Mapping):
        return {}
    surface = opl_package_status.get("opl_agent_package_status")
    return dict(surface) if isinstance(surface, Mapping) else {}


def _dependency_status(status_surface: Mapping[str, Any]) -> dict[str, Any]:
    readiness = status_surface.get("package_dependency_readiness")
    if not isinstance(readiness, Mapping):
        return {}
    dependencies = readiness.get("dependencies")
    if not isinstance(dependencies, Sequence) or isinstance(dependencies, str | bytes):
        return {}
    for dependency in dependencies:
        if (
            isinstance(dependency, Mapping)
            and _text(dependency.get("package_id")) == SCHOLARSKILLS_PACKAGE_ID
        ):
            normalized = dict(dependency)
            normalized["export_ids"] = dependency.get("required_export_ids")
            normalized["module_ids"] = dependency.get("required_module_ids")
            return normalized
    return {}


def _materialization_status(
    status_surface: Mapping[str, Any],
    *,
    required_scope: str,
    target_root: str | None,
) -> dict[str, Any]:
    materialization = status_surface.get("materialization_readiness")
    if not isinstance(materialization, Mapping):
        return {}
    if _text(materialization.get("scope")) != required_scope:
        return {}
    observed_root = _text(materialization.get("target_root"))
    if target_root and observed_root != target_root:
        return {}
    normalized = dict(materialization)
    normalized["skill_ids"] = materialization.get("materialized_skill_ids")
    normalized["receipt_ref"] = materialization.get("lifecycle_receipt_ref")
    return normalized


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_set(value: object) -> set[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return set()
    return {text for item in value if (text := _text(item))}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes):
        return []
    return [text for item in value if (text := _text(item))]


def _is_sha256(value: str | None) -> bool:
    if not value or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(character in "0123456789abcdef" for character in digest)


def _scope_command_templates(base: Sequence[str]) -> dict[str, list[str]]:
    return {
        "workspace": _scoped_package_command(
            base,
            scope="workspace",
            target_root="<workspace-root>",
        ),
        "quest": _scoped_package_command(
            base,
            scope="quest",
            target_root="<quest-root>",
        ),
    }


def _scoped_package_command(
    base: Sequence[str],
    *,
    scope: str,
    target_root: str,
) -> list[str]:
    if scope == "workspace":
        target_flag = "--target-workspace"
    elif scope == "quest":
        target_flag = "--target-quest"
    else:
        raise ValueError(f"unsupported MAS ScholarSkills materialization scope: {scope}")
    return [*base, "--scope", scope, target_flag, target_root, "--json"]


__all__ = [
    "MAS_PACKAGE_REPAIR_COMMAND",
    "MAS_PACKAGE_STATUS_COMMAND",
    "SCHOLARSKILLS_CAPABILITY_ABI",
    "SCHOLARSKILLS_PACKAGE_ID",
    "SCHOLARSKILLS_PROVIDER_MANIFEST_REF",
    "SCHOLARSKILLS_REQUIRED_EXPORT_IDS",
    "SCHOLARSKILLS_REQUIRED_INTERFACE_IDS",
    "SCHOLARSKILLS_REQUIRED_MODULE_IDS",
    "SCHOLARSKILLS_REQUIRED_PACKAGE_READBACK_REF",
    "SCHOLARSKILLS_REQUIRED_SKILL_IDS",
    "SCHOLARSKILLS_VERSION_REQUIREMENT",
    "build_scholarskills_required_package_readback",
    "build_scholarskills_required_package_template",
    "query_scholarskills_required_package_readback",
]
