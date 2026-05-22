from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience import editable_shared_bootstrap as _editable_shared_bootstrap

_editable_shared_bootstrap.ensure_editable_dependency_paths()

from opl_harness_shared.family_entry_contracts import (
    build_domain_agent_entry_spec as _build_shared_domain_agent_entry_spec,
    build_domain_entry_command_catalog as _build_shared_domain_entry_command_catalog,
    build_family_direct_opl_shared_handoff as _build_shared_family_direct_opl_shared_handoff,
    build_family_domain_entry_contract as _build_shared_family_domain_entry_contract,
)

from med_autoscience.control_plane_command_catalog import (
    CONTROL_PLANE_OPERATIONS_COMMANDS,
    ControlPlaneOperationsCommand,
)


SERVICE_SAFE_ENTRY_ADAPTER = "MedAutoScienceDomainEntry"
SERVICE_SAFE_ENTRY_SURFACE_KIND = "med_autoscience_service_safe_domain_entry"
PRODUCT_ENTRY_BUILDER_COMMAND = "build-product-entry"
PRODUCT_ENTRY_MANIFEST_SCHEMA_REF = "contracts/schemas/v1/product-entry-manifest.schema.json"
PRODUCT_ENTRY_STATUS_SCHEMA_REF = "contracts/schemas/v1/product-entry-status.schema.json"
SUPPORTED_PRODUCT_ENTRY_MODES = ("direct", "opl-handoff")
DEFAULT_USER_INTERACTION_SHARED_HANDOFF_ENVELOPE = (
    "target_domain_id",
    "task_intent",
    "entry_mode",
    "workspace_locator",
    "runtime_session_contract",
    "return_surface_contract",
)


@dataclass(frozen=True)
class DomainEntryCommandSpec:
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()


SERVICE_SAFE_OPERATOR_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    "workspace-cockpit": DomainEntryCommandSpec(("profile_ref",)),
    "product-entry-status": DomainEntryCommandSpec(("profile_ref",)),
    "product-preflight": DomainEntryCommandSpec(("profile_ref",)),
    "product-start": DomainEntryCommandSpec(("profile_ref",)),
    "product-entry-manifest": DomainEntryCommandSpec(("profile_ref",)),
    "skill-catalog": DomainEntryCommandSpec(("profile_ref",)),
    "study-progress": DomainEntryCommandSpec(("profile_ref", "study_id"), ("entry_mode",)),
    "progress-projection": DomainEntryCommandSpec(("profile_ref", "study_id"), ("entry_mode",)),
    "launch-study": DomainEntryCommandSpec(
        ("profile_ref", "study_id"),
        ("entry_mode", "allow_stopped_relaunch", "explicit_user_wakeup", "force"),
    ),
    "submit-study-task": DomainEntryCommandSpec(
        ("profile_ref", "study_id", "task_intent"),
        (
            "entry_mode",
            "journal_target",
            "constraints",
            "evidence_boundary",
            "trusted_inputs",
            "reference_papers",
            "first_cycle_outputs",
        ),
    ),
    "build-product-entry": DomainEntryCommandSpec(
        ("profile_ref", "study_id"),
        ("direct_entry_mode",),
    ),
}
SERVICE_SAFE_DOMAIN_COMMANDS: dict[str, DomainEntryCommandSpec | ControlPlaneOperationsCommand] = {
    **SERVICE_SAFE_OPERATOR_COMMANDS,
    **{item.command: item for item in CONTROL_PLANE_OPERATIONS_COMMANDS},
}


def build_domain_entry_command_contracts() -> list[dict[str, Any]]:
    return build_domain_entry_command_catalog()["command_contracts"]


def build_domain_entry_command_catalog() -> dict[str, Any]:
    return _build_shared_domain_entry_command_catalog(
        [
            {
                "command": command,
                "required_fields": list(spec.required_fields),
                "optional_fields": list(spec.optional_fields),
            }
            for command, spec in SERVICE_SAFE_DOMAIN_COMMANDS.items()
        ]
    )


def build_domain_entry_contract() -> dict[str, Any]:
    contract = _build_shared_family_domain_entry_contract(
        entry_adapter=SERVICE_SAFE_ENTRY_ADAPTER,
        service_safe_surface_kind=SERVICE_SAFE_ENTRY_SURFACE_KIND,
        product_entry_builder_command=PRODUCT_ENTRY_BUILDER_COMMAND,
        supported_entry_modes=list(SUPPORTED_PRODUCT_ENTRY_MODES),
        domain_agent_entry_spec=_build_shared_domain_agent_entry_spec(
            agent_id="mas",
            title="MAS Domain Agent Entry (v1)",
            description=(
                "MAS 通过 domain agent entry contract 暴露可审计的入口与进度语义，"
                "用于研究任务与投稿包的受控推进。"
            ),
            default_engine="codex",
            workspace_requirement="required",
            locator_schema={
                "required_fields": ["profile_ref"],
                "optional_fields": ["study_id", "entry_mode"],
            },
            codex_entry_strategy="domain_agent_entry",
            artifact_conventions="paper_and_submission_package",
            progress_conventions="study_runtime_narration",
            entry_command="product-entry-status",
            manifest_command="product-entry-manifest",
        ),
        **build_domain_entry_command_catalog(),
    )
    contract["surface_role"] = "domain_handler_target_for_opl_generated_interfaces"
    contract["generated_descriptor_owner"] = "one-person-lab"
    contract["domain_handler_target_owner"] = "MedAutoScience"
    contract["domain_repo_can_own_generated_surface"] = False
    contract["authority_boundary"] = {
        "opl_owns_generated_cli_mcp_skill_product_status_workbench_descriptors": True,
        "mas_executes_domain_handlers_and_signs_owner_receipts": True,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
    }
    return contract


def build_user_interaction_contract() -> dict[str, Any]:
    return {
        "surface_kind": "user_interaction_contract",
        "entry_owner": "opl_product_entry_or_domain_gui",
        "user_interaction_mode": "natural_language_entry",
        "user_commands_required": False,
        "command_surfaces_for_agent_consumption_only": True,
        "shared_downstream_entry": SERVICE_SAFE_ENTRY_ADAPTER,
        "shared_handoff_envelope": list(DEFAULT_USER_INTERACTION_SHARED_HANDOFF_ENVELOPE),
    }


def validate_user_interaction_contract(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} 必须是 mapping。")
    payload = dict(value)
    required_string_fields = (
        "surface_kind",
        "entry_owner",
        "user_interaction_mode",
        "shared_downstream_entry",
    )
    for name in required_string_fields:
        if not str(payload.get(name) or "").strip():
            raise ValueError(f"{field}.{name} 必须是非空字符串。")
    for name in ("user_commands_required", "command_surfaces_for_agent_consumption_only"):
        if not isinstance(payload.get(name), bool):
            raise ValueError(f"{field}.{name} 必须是 boolean。")
    envelope = payload.get("shared_handoff_envelope")
    if not isinstance(envelope, list) or not all(isinstance(item, str) and item for item in envelope):
        raise ValueError(f"{field}.shared_handoff_envelope 必须是非空字符串列表。")
    return {
        **payload,
        "surface_kind": str(payload["surface_kind"]),
        "entry_owner": str(payload["entry_owner"]),
        "user_interaction_mode": str(payload["user_interaction_mode"]),
        "shared_downstream_entry": str(payload["shared_downstream_entry"]),
        "shared_handoff_envelope": list(envelope),
    }


def build_shared_handoff(
    *,
    direct_entry_builder_command: str,
    opl_handoff_builder_command: str,
) -> dict[str, Any]:
    return _build_shared_family_direct_opl_shared_handoff(
        direct_entry_builder_command=direct_entry_builder_command,
        opl_handoff_builder_command=opl_handoff_builder_command,
    )
