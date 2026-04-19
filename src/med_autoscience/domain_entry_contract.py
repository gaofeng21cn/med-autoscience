from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opl_harness_shared.family_entry_contracts import (
    build_domain_entry_command_contract as _build_shared_domain_entry_command_contract,
    build_family_domain_entry_contract as _build_shared_family_domain_entry_contract,
    build_gateway_interaction_contract as _build_shared_gateway_interaction_contract,
    build_shared_handoff_builder as _build_shared_handoff_builder,
)


SERVICE_SAFE_ENTRY_ADAPTER = "MedAutoScienceDomainEntry"
SERVICE_SAFE_ENTRY_SURFACE_KIND = "med_autoscience_service_safe_domain_entry"
PRODUCT_ENTRY_BUILDER_COMMAND = "build-product-entry"
PRODUCT_ENTRY_MANIFEST_SCHEMA_REF = "contracts/schemas/v1/product-entry-manifest.schema.json"
PRODUCT_FRONTDESK_SCHEMA_REF = "contracts/schemas/v1/product-frontdesk.schema.json"
SUPPORTED_PRODUCT_ENTRY_MODES = ("direct", "opl-handoff")


@dataclass(frozen=True)
class DomainEntryCommandSpec:
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()


SERVICE_SAFE_DOMAIN_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    "workspace-cockpit": DomainEntryCommandSpec(("profile_ref",)),
    "product-frontdesk": DomainEntryCommandSpec(("profile_ref",)),
    "product-preflight": DomainEntryCommandSpec(("profile_ref",)),
    "product-start": DomainEntryCommandSpec(("profile_ref",)),
    "product-entry-manifest": DomainEntryCommandSpec(("profile_ref",)),
    "study-progress": DomainEntryCommandSpec(("profile_ref", "study_id"), ("entry_mode",)),
    "study-runtime-status": DomainEntryCommandSpec(("profile_ref", "study_id"), ("entry_mode",)),
    "launch-study": DomainEntryCommandSpec(
        ("profile_ref", "study_id"),
        ("entry_mode", "allow_stopped_relaunch", "force"),
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


def build_domain_entry_command_contracts() -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    for command, spec in SERVICE_SAFE_DOMAIN_COMMANDS.items():
        contracts.append(
            _build_shared_domain_entry_command_contract(
                command=command,
                required_fields=list(spec.required_fields),
                optional_fields=list(spec.optional_fields),
            )
        )
    return contracts


def build_domain_entry_contract() -> dict[str, Any]:
    return _build_shared_family_domain_entry_contract(
        entry_adapter=SERVICE_SAFE_ENTRY_ADAPTER,
        service_safe_surface_kind=SERVICE_SAFE_ENTRY_SURFACE_KIND,
        product_entry_builder_command=PRODUCT_ENTRY_BUILDER_COMMAND,
        supported_entry_modes=list(SUPPORTED_PRODUCT_ENTRY_MODES),
        supported_commands=list(SERVICE_SAFE_DOMAIN_COMMANDS),
        command_contracts=build_domain_entry_command_contracts(),
    )


def build_gateway_interaction_contract() -> dict[str, Any]:
    return _build_shared_gateway_interaction_contract(
        frontdoor_owner="opl_gateway_or_domain_gui",
        user_interaction_mode="natural_language_frontdoor",
        user_commands_required=False,
        command_surfaces_for_agent_consumption_only=True,
        shared_downstream_entry=SERVICE_SAFE_ENTRY_ADAPTER,
        shared_handoff_envelope=[
            "target_domain_id",
            "task_intent",
            "entry_mode",
            "workspace_locator",
            "runtime_session_contract",
            "return_surface_contract",
        ],
    )


def build_shared_handoff(
    *,
    direct_entry_builder_command: str,
    opl_handoff_builder_command: str,
) -> dict[str, Any]:
    return {
        "direct_entry_builder": _build_shared_handoff_builder(
            command=direct_entry_builder_command,
            entry_mode="direct",
        ),
        "opl_handoff_builder": _build_shared_handoff_builder(
            command=opl_handoff_builder_command,
            entry_mode="opl-handoff",
        ),
    }
