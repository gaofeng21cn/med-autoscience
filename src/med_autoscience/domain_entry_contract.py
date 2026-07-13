from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from opl_framework.family_entry_contracts import (
    build_domain_entry_command_catalog as build_opl_domain_entry_command_catalog,
    build_family_direct_opl_shared_handoff,
    build_family_domain_entry_contract,
    build_user_interaction_contract as build_opl_user_interaction_contract,
    validate_user_interaction_contract as validate_opl_user_interaction_contract,
)

SERVICE_SAFE_ENTRY_ADAPTER = "MedAutoScienceDomainEntry"
SERVICE_SAFE_ENTRY_TARGET = "med_autoscience.domain_entry:MedAutoScienceDomainEntry.dispatch"
SERVICE_SAFE_ENTRY_SURFACE_KIND = "med_autoscience_service_safe_domain_entry"
PRODUCT_ENTRY_BUILDER_COMMAND = "opl-generated-product-entry"
PRODUCT_ENTRY_MANIFEST_SCHEMA_REF = "contracts/schemas/v1/product-entry-manifest.schema.json"
PRODUCT_ENTRY_STATUS_SCHEMA_REF = "contracts/schemas/v1/product-entry-status.schema.json"
SUPPORTED_PRODUCT_ENTRY_MODES = ("direct", "opl-handoff")
DEFAULT_USER_INTERACTION_SHARED_HANDOFF_ENVELOPE = (
    "target_domain_id",
    "task_intent",
    "entry_mode",
    "workspace_locator",
    "domain_authority_handoff_contract",
    "return_surface_contract",
)


@dataclass(frozen=True)
class DomainEntryCommandSpec:
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()


def domain_entry_handler_target(command: str) -> str:
    return f"{SERVICE_SAFE_ENTRY_TARGET}#{command.replace('-', '_')}"


SERVICE_SAFE_OPERATOR_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    "set-study-lifecycle": DomainEntryCommandSpec(
        (
            "profile_ref",
            "study_id",
            "lifecycle_state",
            "reason_code",
            "reason_summary",
            "source_kind",
            "source_ref",
        ),
        ("evidence_refs", "recorded_at"),
    ),
    "study-progress": DomainEntryCommandSpec(("profile_ref", "study_id"), ("entry_mode",)),
    "paper-mission": DomainEntryCommandSpec(
        ("profile_ref", "study_id"),
        (
            "paper_mission_command",
            "objective",
            "mission_id",
            "candidate",
            "run_id",
            "output_root",
            "opl_runtime_payload",
            "dry_run",
        ),
    ),
    "launch-study": DomainEntryCommandSpec(
        ("profile_ref", "study_id"),
        ("entry_mode", "allow_stopped_relaunch", "explicit_user_wakeup", "force"),
    ),
    "submit-study-task": DomainEntryCommandSpec(
        ("profile_ref", "study_id", "task_intent"),
        (
            "task_intake_kind",
            "entry_mode",
            "journal_target",
            "constraints",
            "evidence_boundary",
            "trusted_inputs",
            "reference_papers",
            "first_cycle_outputs",
        ),
    ),
    "study-state-matrix": DomainEntryCommandSpec(
        ("profile_ref",),
        ("study_ids", "entry_mode"),
    ),
    "export-inspection-package": DomainEntryCommandSpec(
        ("profile_ref", "study_id"),
        ("publication_profile", "force_materialize"),
    ),
    "publication-aftercare-plan": DomainEntryCommandSpec(
        ("study_root",),
        ("quest_root",),
    ),
    "delivery-authority-backfill-apply": DomainEntryCommandSpec(
        ("workspace_roots",),
        ("apply", "authority_snapshot"),
    ),
    "external-learning-adoption-closure": DomainEntryCommandSpec(()),
    "scientific-capability-registry": DomainEntryCommandSpec(
        ("mode",),
        ("capability_id", "current_owner_delta", "study_root", "apply", "payload"),
    ),
    "mainline-status": DomainEntryCommandSpec(()),
    "mainline-phase": DomainEntryCommandSpec((), ("selector",)),
}
SERVICE_SAFE_DISPLAY_PACK_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    "display-pack-capability-discover": DomainEntryCommandSpec(
        (),
        ("repo_root", "paper_root", "include_templates", "opl_descriptor_output_dir"),
    ),
    "display-pack-orchestrate": DomainEntryCommandSpec(
        (),
        (
            "repo_root",
            "paper_root",
            "current_owner_delta",
            "claim_ref",
            "data_ref",
            "paper_target",
            "intent",
            "figure_request",
            "max_recommendations",
            "check_runtime_dependencies",
        ),
    ),
    "display-pack-figure-plan": DomainEntryCommandSpec(
        ("figure_request",),
        ("repo_root", "paper_root", "max_recommendations"),
    ),
    "display-pack-preflight": DomainEntryCommandSpec(
        (),
        (
            "repo_root",
            "paper_root",
            "template_id",
            "figure_request",
            "check_runtime_dependencies",
        ),
    ),
    "display-pack-render": DomainEntryCommandSpec(
        ("paper_root",),
        ("repo_root", "figure_request", "visual_audit_review"),
    ),
}
SERVICE_SAFE_RESEARCH_INTEGRITY_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    "research-integrity-gate-input": DomainEntryCommandSpec(
        (),
        (
            "payload",
            "reference_checks",
            "reference",
            "references",
            "claim_spans",
            "claim",
            "claims",
            "citation_refs",
            "evidence_refs",
            "reference_attestation_refs",
            "manuscript_sections",
            "manuscript",
            "numeric_facts",
            "display_facts",
            "provider_evidence",
            "reference_attestations",
            "display_to_claim_map",
            "reporting_guideline_expectations",
            "reporting_checklist_expectations",
        ),
    ),
    "research-integrity-reference-verification": DomainEntryCommandSpec(
        (),
        (
            "payload",
            "reference",
            "references",
            "provider_evidence",
            "provider_receipts",
            "source_refs",
            "reference_manager_ref",
            "manuscript_ref",
        ),
    ),
    "research-integrity-review-publication-gate-stage-hook": DomainEntryCommandSpec(
        (),
        (
            "payload",
            "stage_id",
            "stage_event",
            "stage_hook_ref",
            "reference",
            "references",
            "provider_evidence",
            "provider_receipts",
            "source_refs",
            "reference_manager_ref",
            "manuscript_ref",
            "claim_spans",
            "claim",
            "claims",
            "citation_refs",
            "evidence_refs",
            "reference_attestation_refs",
            "manuscript_sections",
            "manuscript",
            "numeric_facts",
            "display_facts",
            "reference_attestations",
            "display_to_claim_map",
            "reporting_guideline_expectations",
            "reporting_checklist_expectations",
        ),
    ),
}
SERVICE_SAFE_DOMAIN_HANDLER_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    "domain-handler-export": DomainEntryCommandSpec(
        ("profile_ref",),
        ("study_ids", "opl_production_proof_ref"),
    ),
    "domain-handler-dispatch": DomainEntryCommandSpec(("task_ref",)),
}
SERVICE_SAFE_DOMAIN_COMMANDS: dict[str, DomainEntryCommandSpec] = {
    **SERVICE_SAFE_OPERATOR_COMMANDS,
    **SERVICE_SAFE_DISPLAY_PACK_COMMANDS,
    **SERVICE_SAFE_RESEARCH_INTEGRITY_COMMANDS,
    **SERVICE_SAFE_DOMAIN_HANDLER_COMMANDS,
}


def build_domain_entry_command_contracts() -> list[dict[str, Any]]:
    return build_domain_entry_command_catalog()["command_contracts"]


def build_domain_entry_command_catalog() -> dict[str, Any]:
    return build_opl_domain_entry_command_catalog([
        {
            "command": command,
            "required_fields": list(spec.required_fields),
            "optional_fields": list(spec.optional_fields),
        }
        for command, spec in SERVICE_SAFE_DOMAIN_COMMANDS.items()
    ])


def build_domain_entry_contract() -> dict[str, Any]:
    catalog = build_domain_entry_command_catalog()
    return build_family_domain_entry_contract(
        entry_adapter=SERVICE_SAFE_ENTRY_ADAPTER,
        service_safe_surface_kind=SERVICE_SAFE_ENTRY_SURFACE_KIND,
        product_entry_builder_command=PRODUCT_ENTRY_BUILDER_COMMAND,
        supported_commands=catalog["supported_commands"],
        command_contracts=catalog["command_contracts"],
        supported_entry_modes=list(SUPPORTED_PRODUCT_ENTRY_MODES),
        domain_agent_entry_spec={
            "surface_kind": "domain_agent_entry_spec",
            "agent_id": "mas",
            "title": "MAS Domain Agent Entry (v1)",
            "description": (
                "MAS 通过 domain agent entry contract 暴露可审计的入口与进度语义，"
                "用于研究任务与投稿包的受控推进。"
            ),
            "default_engine": "codex",
            "workspace_requirement": "required",
            "locator_schema": {
                "required_fields": ["profile_ref"],
                "optional_fields": ["study_id", "entry_mode"],
            },
            "codex_entry_strategy": "domain_agent_entry",
            "artifact_conventions": "paper_and_submission_package",
            "progress_conventions": "study_runtime_narration",
            "entry_command": "study-progress",
            "manifest_command": "opl-generated-product-entry",
        },
        extra_payload={
            "surface_role": "domain_handler_target_for_opl_generated_interfaces",
            "generated_descriptor_owner": "one-person-lab",
            "domain_handler_target_owner": "MedAutoScience",
            "domain_repo_can_own_generated_surface": False,
            "authority_boundary": {
                "opl_owns_generated_cli_mcp_skill_product_status_workbench_descriptors": True,
                "mas_executes_domain_handlers_and_signs_owner_receipts": True,
                "opl_can_write_domain_truth": False,
                "opl_can_authorize_quality_or_export": False,
            },
        },
    )


def build_user_interaction_contract() -> dict[str, Any]:
    return build_opl_user_interaction_contract(
        entry_owner="opl_product_entry_or_domain_gui",
        user_interaction_mode="natural_language_entry",
        user_commands_required=False,
        command_surfaces_for_agent_consumption_only=True,
        shared_downstream_entry=SERVICE_SAFE_ENTRY_ADAPTER,
        shared_handoff_envelope=list(DEFAULT_USER_INTERACTION_SHARED_HANDOFF_ENVELOPE),
    )


def validate_user_interaction_contract(value: object, field: str) -> dict[str, Any]:
    return validate_opl_user_interaction_contract(value, field)


def build_shared_handoff(
    *,
    direct_entry_builder_command: str,
    opl_handoff_builder_command: str,
) -> dict[str, Any]:
    return build_family_direct_opl_shared_handoff(
        direct_entry_builder_command=direct_entry_builder_command,
        opl_handoff_builder_command=opl_handoff_builder_command,
    )
