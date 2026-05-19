from __future__ import annotations

from typing import Any

from .functional_followthrough_gaps import (
    FUNCTIONAL_FOLLOWTHROUGH_GAPS_OPEN_STATUS,
    OPL_REPLACEMENT_EXPECTATION_AUDIT,
    REMAINING_GAP_CLASSIFICATION,
    build_functional_followthrough_gap_summary,
)
from .generated_surface_handoff import build_generated_surface_handoff
from .consumer_migration_inventory import (
    FUNCTIONAL_MODULE_INVENTORY,
    FUNCTIONAL_SURFACE_CLASSIFICATION,
    RETIRED_LEGACY_RESIDUE_TOMBSTONES,
)

SCHEMA_VERSION = 1
SURFACE_KIND = "mas_legacy_domain_slo_diagnostic_consumer_migration"
ACTIVE_PATH_ROLE = "opl_replacement_default"
LOCAL_TOMBSTONE_PATH_ROLE = "physical_retired_tombstone_provenance_only"
OPTIONAL_ADAPTER_PATH_ROLE = "legacy_scheduler_diagnostic_cleanup_only"
CURRENT_SCHEDULER_OWNER = "opl_provider_runtime_manager"
LEGACY_SCHEDULER_OWNER = "mas_legacy_domain_slo_diagnostic"
REPLACEMENT_OWNER = "one-person-lab"
REPLACEMENT_OWNER_SURFACE = "opl_provider_runtime_manager"
REPLACEMENT_STATE = "opl_replacement_contract_active"
RETIREMENT_STATE = "local_legacy_retirement_pending_no_active_caller_proof"
LOCAL_TOMBSTONE_RETIREMENT_STATE = "local_legacy_physical_retired_tombstone"

MAS_RETAINED_AFTER_MIGRATION = (
    "paper_progress_slo_semantics",
    "mas_owner_receipt",
    "typed_blocker",
    "safe_action_refs",
    "quality_source_refs",
    "no_forbidden_write_evidence",
)
OPL_REPLACEMENT_EXPECTED_CAPABILITIES = (
    "scheduler_lifecycle",
    "cadence_slo",
    "job_registry_latest_run_projection",
    "provider_slo",
    "wakeup_transport",
    "attempt_queue_retry_dead_letter",
    "operator_projection",
)
RETIREMENT_PROOF_REQUIRED = (
    "opl_replacement_contract_available",
    "replacement_proof",
    "no_active_caller_proof",
    "no_forbidden_write",
    "focused_cli_status_tests",
    "git_diff_check",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "provider_completion_is_paper_closure",
    "scheduler_status_is_publication_ready",
    "scheduler_status_authorizes_artifact_mutation",
    "stable_blocker_is_paper_closure",
)
FORBIDDEN_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "paper/current_package",
    "manuscript/current_package",
    "paper/submission_minimal",
    "manuscript/submission_minimal",
    "runtime_lifecycle.sqlite",
)
OPL_CONSUMED_GENERIC_SURFACES = (
    "generic_scheduler",
    "generic_daemon",
    "generic_queue",
    "generic_attempt_ledger",
    "generic_runner",
    "generic_transition_runner",
    "generic_workbench",
    "generic_memory_locator",
    "generic_artifact_lifecycle",
    "generic_observability",
)
OPL_FUNCTIONAL_HARNESS_COVERAGE = (
    "refs_only_memory_writeback_chain",
    "queue_stage_attempt_typed_closeout",
    "generic_transition_runner",
    "restart_dead_letter_repair_human_gate_state_chain",
)
NO_ACTIVE_CALLER_PROOF = {
    "status": "legacy_local_scheduler_physical_retired",
    "default_caller_count": 0,
    "default_manager": "opl",
    "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
    "legacy_local_install_path_role": LOCAL_TOMBSTONE_PATH_ROLE,
    "cleanup_only_commands": [],
    "forbidden_default_callers": [
        "cli_default_local_scheduler_install",
        "workspace_bootstrap_local_scheduler_install",
        "product_entry_local_scheduler_install",
        "sidecar_local_scheduler_install",
        "mcp_local_scheduler_install",
    ],
    "forbidden_explicit_callers": [
        "runtime-supervision-status --profile <profile> --manager local",
        "runtime-ensure-supervision --profile <profile> --manager local",
        "runtime-remove-supervision --profile <profile> --manager local",
    ],
    "proof_items": [
        "cli_default_manager_is_opl",
        "cli_manager_choices_exclude_local",
        "workspace_bootstrap_manager_is_opl",
        "product_entry_consumes_opl_replacement_projection",
        "sidecar_exports_functional_boundary_no_generic_owner",
        "local_scheduler_status_remove_path_returns_tombstone_only",
        "local_scheduler_install_proof_generation_forbidden",
        "local_scheduler_launchagent_adapter_deleted",
    ],
}
LOCAL_SCHEDULER_PHYSICAL_RETIREMENT_PROOF = {
    "surface_kind": "mas_local_scheduler_physical_retirement_proof",
    "status": "physical_retired_tombstone_provenance_only",
    "install_allowed": False,
    "status_allowed": False,
    "remove_allowed": False,
    "trigger_allowed": False,
    "write_install_proof_allowed": False,
    "loaded_state_allowed": False,
    "default_cli_exposes_local_status": False,
    "default_cli_exposes_local_remove": False,
    "default_cli_exposes_local_install": False,
    "default_bootstrap_exposes_local_install": False,
    "cleanup_status": "tombstone_only",
    "remaining_physical_delete_blockers": [],
    "retained_refs": [
        "contracts/runtime/legacy-active-path-tombstones.json",
        "docs/history/runtime/legacy_active_path_tombstones.md",
    ],
}
MAS_RETAINED_THIN_PROGRAM_SURFACES = (
    "study_truth",
    "publication_quality_verdict",
    "artifact_authority",
    "publication_route_memory_body",
    "memory_writeback_decision",
    "domain_transition_table",
    "owner_receipt",
    "typed_blocker",
    "safe_action_refs",
)
MINIMAL_AUTHORITY_FUNCTION_IDS = (
    "publication_quality_verdict",
    "ai_reviewer_quality_decision",
    "artifact_mutation_authorization",
    "publication_route_memory_accept_reject",
    "source_readiness_verdict",
    "owner_receipt_signer",
    "medical_helper_implementation",
)
ALLOWED_PRIVATE_AUTHORITY_JUDGMENT_MODES = (
    "ai_first_stage_gate",
    "ai_first_record_validator",
    "mechanical_guard",
    "refs_only_adapter",
)
AI_FIRST_STAGE_GATE_FUNCTION_IDS = (
    "publication_quality_verdict",
    "ai_reviewer_quality_decision",
    "publication_route_memory_accept_reject",
    "source_readiness_verdict",
)
AI_FIRST_RECORD_VALIDATOR_FUNCTION_IDS = ("artifact_mutation_authorization",)
MECHANICAL_GUARD_FUNCTION_IDS = ("owner_receipt_signer", "medical_helper_implementation")
AI_FIRST_STAGE_QUALITY_GATE_BOUNDARY_IDS = (
    "publication_quality_stage_gate_boundary",
    "ai_reviewer_quality_stage_gate_boundary",
    "artifact_mutation_stage_gate_boundary",
    "publication_route_memory_accept_reject_stage_gate_boundary",
    "source_readiness_stage_gate_boundary",
)
FORBIDDEN_MECHANICAL_DECISION_SURFACES = (
    "script_exit_code_as_publication_quality_verdict",
    "function_return_value_as_ai_reviewer_quality_decision",
    "test_pass_as_artifact_mutation_authorization",
    "queue_completion_as_publication_route_memory_accept_reject",
    "file_presence_as_source_readiness_verdict",
)
INDEPENDENT_EXECUTOR_REVIEWER_AGENT_POLICY = {
    "surface_kind": "independent_executor_reviewer_agent_policy",
    "required": True,
    "executor_agent_role": "stage_work_executor",
    "reviewer_auditor_agent_role": "quality_gate_reviewer_or_auditor",
    "separate_invocation_required": True,
    "separate_context_record_required": True,
    "separate_task_record_required": True,
    "separate_receipt_required": True,
    "self_review_closes_quality_gate": False,
    "codex_cli_may_serve_both_roles_only_as_separate_invocations": True,
    "missing_independent_reviewer_record_policy": "fail_closed_or_route_back",
}
AI_FIRST_STAGE_QUALITY_GATE_BOUNDARIES = [
    {
        "boundary_id": "publication_quality_stage_gate_boundary",
        "legacy_readable_id": "publication_quality_verdict",
        "program_role": "validator",
        "function_id": "publication_quality_verdict",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "trace_refs": [
            "stage_quality_pack:publication_quality",
            "publication_eval/latest.json",
            "review_ledger",
            "evidence_ledger",
        ],
        "requires_ai_first_record": True,
        "required_record_refs": ["ai_reviewer_record", "quality_pack_evidence_refs"],
        "route_back_semantics": "route_back_to_review_or_revision_stage",
        "typed_blocker_semantics": "publication_quality_blocker",
    },
    {
        "boundary_id": "ai_reviewer_quality_stage_gate_boundary",
        "legacy_readable_id": "ai_reviewer_quality_decision",
        "program_role": "validator",
        "function_id": "ai_reviewer_quality_decision",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "trace_refs": [
            "AI reviewer workflow",
            "AI reviewer-backed publication eval",
            "stage_quality_pack:ai_reviewer_quality",
        ],
        "requires_ai_first_record": True,
        "required_record_refs": ["ai_reviewer_record", "reviewer_operating_system_trace"],
        "route_back_semantics": "route_back_to_ai_reviewer_repair_stage",
        "typed_blocker_semantics": "ai_reviewer_quality_blocker",
    },
    {
        "boundary_id": "artifact_mutation_stage_gate_boundary",
        "legacy_readable_id": "artifact_mutation_authorization",
        "program_role": "materializer",
        "function_id": "artifact_mutation_authorization",
        "judgment_mode": "ai_first_record_validator",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "trace_refs": [
            "stage_quality_pack:artifact_materialization",
            "canonical manuscript",
            "current_package",
            "artifact rebuild proof",
        ],
        "requires_ai_first_record": True,
        "required_record_refs": ["quality_pack_evidence_refs", "artifact_rebuild_proof"],
        "route_back_semantics": "route_back_to_artifact_rebuild_or_source_revision_stage",
        "typed_blocker_semantics": "artifact_mutation_blocker",
    },
    {
        "boundary_id": "publication_route_memory_accept_reject_stage_gate_boundary",
        "legacy_readable_id": "publication_route_memory_accept_reject",
        "program_role": "guard",
        "function_id": "publication_route_memory_accept_reject",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "trace_refs": [
            "publication-route memory body",
            "memory writeback proposal",
            "memory writeback router receipt",
            "stage_quality_pack:publication_route_memory",
        ],
        "requires_ai_first_record": True,
        "required_record_refs": ["publication_route_memory_body", "memory_writeback_receipt_refs"],
        "route_back_semantics": "route_back_to_memory_writeback_repair_stage",
        "typed_blocker_semantics": "publication_route_memory_writeback_blocker",
    },
    {
        "boundary_id": "source_readiness_stage_gate_boundary",
        "legacy_readable_id": "source_readiness_verdict",
        "program_role": "validator",
        "function_id": "source_readiness_verdict",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "trace_refs": [
            "study charter",
            "source readiness checks",
            "evidence ledger",
            "stage_quality_pack:source_readiness",
        ],
        "requires_ai_first_record": True,
        "required_record_refs": ["study_charter", "quality_pack_evidence_refs"],
        "route_back_semantics": "route_back_to_source_intake_or_study_design_stage",
        "typed_blocker_semantics": "source_readiness_blocker",
    },
]
DECLARATIVE_PACK_COMPILER_INPUT = {
    "surface_kind": "mas_declarative_pack_compiler_input",
    "schema_version": SCHEMA_VERSION,
    "owner": "med-autoscience",
    "compiler_owner": REPLACEMENT_OWNER,
    "status": "ready_for_opl_pack_compiler_consumption_generated_surface_migration",
    "pack_id": "mas-medical-research-pack",
    "pack_role": "domain_authority_pack_input_not_generated_shell_owner",
    "input_refs": [
        {
            "input_id": "domain_descriptor",
            "source_ref": "product_entry_manifest.standard_domain_agent_skeleton",
            "body_policy": "descriptor_only",
        },
        {
            "input_id": "stage_graph",
            "source_ref": "product_entry_manifest.family_stage_control_plane_descriptor",
            "body_policy": "descriptor_and_locator_refs",
        },
        {
            "input_id": "action_intents",
            "source_ref": "product_entry_manifest.family_action_catalog",
            "body_policy": "declarative_action_metadata",
        },
        {
            "input_id": "domain_transition_table",
            "source_ref": "study-state-matrix family_transition_spec_descriptor",
            "body_policy": "mas_owned_transition_spec_and_oracle_refs",
        },
        {
            "input_id": "publication_route_memory_policy",
            "source_ref": "product_entry_manifest.domain_memory_descriptor",
            "body_policy": "locator_receipt_refs_only_no_memory_body",
        },
        {
            "input_id": "artifact_authority_policy",
            "source_ref": "product_entry_manifest.lifecycle_guarded_apply_proof",
            "body_policy": "authority_policy_and_receipt_refs",
        },
        {
            "input_id": "source_readiness_policy",
            "source_ref": "workspace/source readiness verdict surfaces",
            "body_policy": "domain_verdict_function_only",
        },
        {
            "input_id": "receipt_schema",
            "source_ref": "product_entry_manifest.domain_owner_receipt_contract",
            "body_policy": "receipt_envelope_schema",
        },
        {
            "input_id": "no_forbidden_write_contract",
            "source_ref": "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
            "body_policy": "machine_guard",
        },
    ],
    "compiler_outputs_expected": [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ],
    "mas_long_term_code_owner": "minimal_authority_functions_only",
    "must_not_generate_or_claim_domain_authority": True,
}
GENERATED_SURFACE_HANDOFF = build_generated_surface_handoff(
    schema_version=SCHEMA_VERSION,
    replacement_owner=REPLACEMENT_OWNER,
)
MINIMAL_AUTHORITY_FUNCTION_MANIFEST = {
    "surface_kind": "mas_minimal_authority_function_manifest",
    "schema_version": SCHEMA_VERSION,
    "owner": "med-autoscience",
    "status": "minimal_authority_functions_only",
    "semantic_model": "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts",
    "gate_validator_ref": (
        "src/med_autoscience/controllers/ai_first_private_authority.py::"
        "validate_ai_first_private_authority_gate"
    ),
    "runtime_enforcement_status": "contract_validator_landed",
    "allowed_judgment_modes": list(ALLOWED_PRIVATE_AUTHORITY_JUDGMENT_MODES),
    "verdict_function_model_retired": True,
    "program_output_policy": (
        "programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only"
    ),
    "ai_first_stage_gate_function_ids": list(AI_FIRST_STAGE_GATE_FUNCTION_IDS),
    "ai_first_record_validator_function_ids": list(AI_FIRST_RECORD_VALIDATOR_FUNCTION_IDS),
    "mechanical_guard_function_ids": list(MECHANICAL_GUARD_FUNCTION_IDS),
    "standard_stage_gate_output_model": {
        "executor_output": "stage_work_artifact_source_evidence_refs_and_execution_receipt",
        "reviewer_output": "independent_ai_reviewer_or_auditor_gate_record",
        "program_output": "provenance_currentness_schema_receipt_or_typed_blocker",
        "self_review_closes_gate": False,
    },
    "boundary_ids": list(AI_FIRST_STAGE_QUALITY_GATE_BOUNDARY_IDS),
    "stage_quality_gate_boundaries": [
        dict(item) for item in AI_FIRST_STAGE_QUALITY_GATE_BOUNDARIES
    ],
    "forbidden_mechanical_decision_surfaces": list(FORBIDDEN_MECHANICAL_DECISION_SURFACES),
    "independent_executor_reviewer_agent_policy": dict(
        INDEPENDENT_EXECUTOR_REVIEWER_AGENT_POLICY
    ),
    "requires_ai_first_record": True,
    "function_ids": list(MINIMAL_AUTHORITY_FUNCTION_IDS),
    "function_count": len(MINIMAL_AUTHORITY_FUNCTION_IDS),
    "functions": [
        {
            "function_id": "publication_quality_verdict",
            "owner": "med-autoscience",
            "boundary_id": "publication_quality_stage_gate_boundary",
            "program_role": "validator",
            "judgment_mode": "ai_first_stage_gate",
            "decision_output_owner": "independent_reviewer_auditor_agent",
            "program_may_emit_pass_ready_verdict": False,
            "missing_ai_first_record_policy": "typed_blocker_or_route_back",
            "standard_stage_output": True,
            "required_record_refs": ["ai_reviewer_record", "quality_pack_evidence_refs"],
            "requires_ai_first_record": True,
            "trace_refs": [
                "stage_quality_pack:publication_quality",
                "publication_eval/latest.json",
                "review_ledger",
                "evidence_ledger",
            ],
            "route_back_semantics": "route_back_to_review_or_revision_stage",
            "typed_blocker_semantics": "publication_quality_blocker",
            "source_refs": [
                "publication_eval/latest.json",
                "publication gate",
                "review ledger",
            ],
            "cannot_absorb_reason": "Medical publication quality and readiness require MAS domain judgment.",
        },
        {
            "function_id": "ai_reviewer_quality_decision",
            "owner": "med-autoscience",
            "boundary_id": "ai_reviewer_quality_stage_gate_boundary",
            "program_role": "validator",
            "judgment_mode": "ai_first_stage_gate",
            "decision_output_owner": "independent_reviewer_auditor_agent",
            "program_may_emit_pass_ready_verdict": False,
            "missing_ai_first_record_policy": "typed_blocker_or_route_back",
            "standard_stage_output": True,
            "required_record_refs": ["ai_reviewer_record", "reviewer_operating_system_trace"],
            "requires_ai_first_record": True,
            "trace_refs": [
                "AI reviewer workflow",
                "AI reviewer-backed publication eval",
                "stage_quality_pack:ai_reviewer_quality",
            ],
            "route_back_semantics": "route_back_to_ai_reviewer_repair_stage",
            "typed_blocker_semantics": "ai_reviewer_quality_blocker",
            "source_refs": [
                "AI reviewer workflow",
                "reviewer operating system trace",
                "AI reviewer-backed publication eval",
            ],
            "cannot_absorb_reason": "OPL can transport reviewer work but cannot issue medical reviewer verdicts.",
        },
        {
            "function_id": "artifact_mutation_authorization",
            "owner": "med-autoscience",
            "boundary_id": "artifact_mutation_stage_gate_boundary",
            "program_role": "materializer",
            "judgment_mode": "ai_first_record_validator",
            "decision_output_owner": "independent_reviewer_auditor_agent",
            "program_may_emit_pass_ready_verdict": False,
            "missing_ai_first_record_policy": "typed_blocker_or_route_back",
            "standard_stage_output": True,
            "required_record_refs": ["quality_pack_evidence_refs", "artifact_rebuild_proof"],
            "requires_ai_first_record": True,
            "trace_refs": [
                "stage_quality_pack:artifact_materialization",
                "canonical manuscript",
                "current_package",
                "artifact rebuild proof",
            ],
            "route_back_semantics": "route_back_to_artifact_rebuild_or_source_revision_stage",
            "typed_blocker_semantics": "artifact_mutation_blocker",
            "source_refs": [
                "canonical manuscript",
                "current_package",
                "submission package",
                "artifact rebuild proof",
            ],
            "cannot_absorb_reason": "Artifact mutation changes submission-facing medical deliverables.",
        },
        {
            "function_id": "publication_route_memory_accept_reject",
            "owner": "med-autoscience",
            "boundary_id": "publication_route_memory_accept_reject_stage_gate_boundary",
            "program_role": "guard",
            "judgment_mode": "ai_first_stage_gate",
            "decision_output_owner": "independent_reviewer_auditor_agent",
            "program_may_emit_pass_ready_verdict": False,
            "missing_ai_first_record_policy": "typed_blocker_or_route_back",
            "standard_stage_output": True,
            "required_record_refs": ["publication_route_memory_body", "memory_writeback_receipt_refs"],
            "requires_ai_first_record": True,
            "trace_refs": [
                "publication-route memory body",
                "memory writeback proposal",
                "memory writeback router receipt",
                "stage_quality_pack:publication_route_memory",
            ],
            "route_back_semantics": "route_back_to_memory_writeback_repair_stage",
            "typed_blocker_semantics": "publication_route_memory_writeback_blocker",
            "source_refs": [
                "publication-route memory body",
                "memory writeback proposal",
                "memory writeback router receipt",
            ],
            "cannot_absorb_reason": "Memory body and accept/reject decisions remain domain-owned.",
        },
        {
            "function_id": "source_readiness_verdict",
            "owner": "med-autoscience",
            "boundary_id": "source_readiness_stage_gate_boundary",
            "program_role": "validator",
            "judgment_mode": "ai_first_stage_gate",
            "decision_output_owner": "independent_reviewer_auditor_agent",
            "program_may_emit_pass_ready_verdict": False,
            "missing_ai_first_record_policy": "typed_blocker_or_route_back",
            "standard_stage_output": True,
            "required_record_refs": ["study_charter", "quality_pack_evidence_refs"],
            "requires_ai_first_record": True,
            "trace_refs": [
                "study charter",
                "source readiness checks",
                "evidence ledger",
                "stage_quality_pack:source_readiness",
            ],
            "route_back_semantics": "route_back_to_source_intake_or_study_design_stage",
            "typed_blocker_semantics": "source_readiness_blocker",
            "source_refs": [
                "study charter",
                "source readiness checks",
                "evidence ledger",
            ],
            "cannot_absorb_reason": "Medical source sufficiency and study readiness are MAS domain verdicts.",
        },
        {
            "function_id": "owner_receipt_signer",
            "owner": "med-autoscience",
            "program_role": "receipt_signer",
            "judgment_mode": "mechanical_guard",
            "decision_output_owner": "med-autoscience_owner_receipt_signer",
            "program_may_emit_pass_ready_verdict": False,
            "medical_verdict_output_allowed": False,
            "requires_ai_first_record": False,
            "source_refs": [
                "MAS owner receipt",
                "typed blocker",
                "safe action receipt",
            ],
            "cannot_absorb_reason": "Only MAS can sign domain receipt, blocker, and safe action authority.",
        },
        {
            "function_id": "medical_helper_implementation",
            "owner": "med-autoscience",
            "program_role": "guard",
            "judgment_mode": "mechanical_guard",
            "decision_output_owner": "none",
            "program_may_emit_pass_ready_verdict": False,
            "medical_verdict_output_allowed": False,
            "ai_first_escalation_policy": (
                "helpers_that_would_emit_medical_ready_quality_route_or_source_verdicts_must_route_to_stage_gate"
            ),
            "requires_ai_first_record": False,
            "source_refs": [
                "medical analysis helpers",
                "reporting guideline helpers",
                "medical display/claim helper functions",
            ],
            "cannot_absorb_reason": "Domain helper code encodes medical research semantics rather than generic runtime shell.",
        },
    ],
    "all_other_program_surfaces": "opl_generated_or_migration_bridge",
    "forbidden_long_term_mas_shell_owners": [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ],
}
def build_functional_consumer_boundary() -> dict[str, Any]:
    classification_counts: dict[str, int] = {}
    for item in FUNCTIONAL_MODULE_INVENTORY:
        classification = str(item["classification"])
        classification_counts[classification] = classification_counts.get(classification, 0) + 1
    legacy_cleanup_items = [
        item["module_id"]
        for item in FUNCTIONAL_MODULE_INVENTORY
        if item["classification"] == "legacy_cleanup_no_active_caller_gate"
    ]
    legacy_physical_retired_items = [
        item["module_id"]
        for item in FUNCTIONAL_MODULE_INVENTORY
        if item.get("physical_retired") is True
    ]
    retired_legacy_residue_items = [
        str(item["residue_id"]) for item in RETIRED_LEGACY_RESIDUE_TOMBSTONES
    ]
    refs_only_adapter_retirement_gates = [
        dict(item["retirement_gate"])
        for item in FUNCTIONAL_MODULE_INVENTORY
        if item["classification"] == "refs_only_adapter"
    ]
    functional_followthrough_gap_summary = build_functional_followthrough_gap_summary(
        classification_counts=classification_counts,
        legacy_cleanup_items=legacy_cleanup_items,
        legacy_physical_retired_items=legacy_physical_retired_items,
        legacy_tombstone_items=retired_legacy_residue_items,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_functional_consumer_boundary",
        "status": "opl_consumes_generic_surfaces_mas_retains_domain_authority_pack",
        "consumer_role": "domain_authority_pack_thin_program_surface",
        "generic_surface_owner": REPLACEMENT_OWNER,
        "generic_surfaces_consumed_from_opl": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_does_not_own": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_retains": list(MAS_RETAINED_THIN_PROGRAM_SURFACES),
        "declarative_pack_compiler_input": dict(DECLARATIVE_PACK_COMPILER_INPUT),
        "generated_surface_handoff": {
            key: [dict(item) if isinstance(item, dict) else item for item in value]
            if isinstance(value, list)
            else value
            for key, value in GENERATED_SURFACE_HANDOFF.items()
        },
        "minimal_authority_function_manifest": {
            key: [dict(item) if isinstance(item, dict) else item for item in value]
            if isinstance(value, list)
            else value
            for key, value in MINIMAL_AUTHORITY_FUNCTION_MANIFEST.items()
        },
        "functional_surface_classification": {
            key: list(value) for key, value in FUNCTIONAL_SURFACE_CLASSIFICATION.items()
        },
        "functional_module_inventory": [
            {
                key: list(value) if isinstance(value, list) else value
                for key, value in item.items()
            }
            for item in FUNCTIONAL_MODULE_INVENTORY
        ],
        "functional_module_inventory_summary": {
            "total_count": len(FUNCTIONAL_MODULE_INVENTORY),
            "classification_counts": classification_counts,
            "long_term_opl_owned_replacement_count": 0,
            "retire_tombstone_classification_count": 0,
            "retired_legacy_residue_count": len(retired_legacy_residue_items),
            "classification_gap_count": 0,
            "functional_structure_gap_count": functional_followthrough_gap_summary[
                "functional_structure_gap_count"
            ],
            "active_private_generic_residue_count": 0,
            "remaining_gap_classification": REMAINING_GAP_CLASSIFICATION,
            "remaining_functional_followthrough_gate_ids": list(
                functional_followthrough_gap_summary[
                    "remaining_functional_followthrough_gate_ids"
                ]
            ),
            "legacy_cleanup_items_require_no_active_caller_gate": [],
            "legacy_cleanup_items_physical_retired": list(legacy_physical_retired_items),
            "legacy_cleanup_items_tombstoned": list(retired_legacy_residue_items),
            "legacy_cleanup_items_are_diagnostic_provenance_guards": False,
            "legacy_cleanup_item_role": "history_tombstone_provenance_only",
            "legacy_cleanup_items_are_remaining_active_gaps": False,
            "legacy_cleanup_items_have_default_entry": False,
            "legacy_cleanup_items_have_standard_template_refs": False,
            "closed_functional_structure_gate_ids": list(
                functional_followthrough_gap_summary[
                    "closed_functional_structure_gate_ids"
                ]
            ),
        },
        "functional_followthrough_gap_summary": functional_followthrough_gap_summary,
        "retired_legacy_residue_tombstones": [
            dict(item) for item in RETIRED_LEGACY_RESIDUE_TOMBSTONES
        ],
        "refs_only_adapter_retirement_gates": refs_only_adapter_retirement_gates,
        "runtime_lifecycle_sqlite_role": {
            "classification": "refs_only_adapter",
            "current_mas_role": "domain_sidecar_index_reference_adapter",
            "authority": "refs_only_index_not_generic_persistence_engine",
            "owner": REPLACEMENT_OWNER,
            "provenance_role": "runtime_lifecycle_sqlite_migration_provenance",
            "body_policy": "refs_receipts_blockers_only",
            "mas_may_index_domain_receipts": True,
            "mas_may_claim_generic_persistence_engine": False,
            "mas_consumes_opl_lifecycle_index_refs": True,
            "mas_may_write_domain_truth": False,
            "generic_owner_claim_allowed": False,
            "forbidden_mas_roles": [
                "generic_persistence_engine",
                "generic_lifecycle_engine",
                "generic_restore_retention_owner",
            ],
            "replacement_expectation": dict(OPL_REPLACEMENT_EXPECTATION_AUDIT),
        },
        "opl_functional_harness_consumer_coverage": {
            "surface_kind": "opl_functional_harness_consumer_coverage",
            "status": "landed_domain_authority_pack_consumer",
            "coverage_items": list(OPL_FUNCTIONAL_HARNESS_COVERAGE),
            "opl_harness_pass_is_paper_closure": False,
            "opl_harness_pass_is_publication_ready": False,
            "mas_owns_generic_runtime": False,
            "mas_retains_domain_authority_pack": list(MAS_RETAINED_THIN_PROGRAM_SURFACES),
            "refs_only_memory_writeback_chain": {
                "opl_consumes": [
                    "consumed_publication_route_memory_refs",
                    "typed_closeout_proposal_refs",
                    "memory_write_router_receipt_refs",
                    "workspace_writeback_receipt_refs",
                    "opl_aion_display_receipt_refs",
                ],
                "mas_retains": [
                    "publication_route_memory_body",
                    "memory_writeback_decision",
                    "accepted_rejected_blocked_writeback_verdict",
                ],
                "body_included": False,
                "opl_can_accept_or_reject_writeback": False,
            },
            "queue_stage_attempt_typed_closeout": {
                "opl_owns": [
                    "family_queue",
                    "stage_attempt_ledger",
                    "attempt_start_query_signal",
                    "framework_typed_closeout_transport",
                ],
                "mas_retains": [
                    "stage_closeout_domain_semantics",
                    "owner_receipt",
                    "typed_blocker",
                    "safe_action_refs",
                ],
                "queue_completion_is_paper_closure": False,
            },
            "generic_transition_runner": {
                "opl_owns": [
                    "generic_transition_runner",
                    "transition_matrix_runner",
                    "idempotent_tick",
                    "retry_dead_letter_transport",
                ],
                "mas_retains": [
                    "domain_transition_table",
                    "publication_quality_verdict",
                    "artifact_authority",
                    "owner_receipt",
                ],
                "runner_completion_can_authorize_publication": False,
            },
            "restart_dead_letter_repair_human_gate_state_chain": {
                "opl_owns": [
                    "restart_requery",
                    "dead_letter_state",
                    "repair_transport",
                    "human_gate_signal_transport",
                ],
                "mas_retains": [
                    "human_gate_domain_receipt",
                    "repair_owner_receipt",
                    "stop_loss_receipt",
                    "typed_blocker",
                ],
                "state_chain_completion_is_publication_ready": False,
            },
        },
        "no_active_caller_required": True,
        "no_active_caller_proof": dict(NO_ACTIVE_CALLER_PROOF),
        "legacy_local_scheduler_physical_retirement_proof": dict(
            LOCAL_SCHEDULER_PHYSICAL_RETIREMENT_PROOF
        ),
        "no_active_caller_scope": [
            "cli_default",
            "mcp_default",
            "product_entry_default",
            "sidecar_default",
            "test_lane_default",
        ],
        "proof_surfaces": [
            "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
            "runtime-supervision-status default manager=opl",
            "product_entry_manifest.functional_consumer_boundary",
            "sidecar_export.functional_consumer_boundary",
            "legacy_residue_audit.summary.default_caller_count",
        ],
        "forbidden_regressions": [
            "mas_default_generic_scheduler",
            "mas_resident_generic_daemon",
            "mas_owned_generic_queue",
            "mas_owned_attempt_ledger",
            "mas_generic_transition_runner",
            "mas_generic_workbench_shell",
        ],
    }


def build_consumer_migration_contract(
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    manager_key = str(manager or "").strip().lower()
    replacement_active = manager_key in {"opl", "opl_provider_runtime_manager"} or adapter_id == "opl_family_runtime_provider"
    local_tombstone = manager_key == "local" or adapter_id == "local_launchd_retired_tombstone"
    active_path_role = (
        ACTIVE_PATH_ROLE
        if replacement_active
        else LOCAL_TOMBSTONE_PATH_ROLE
        if local_tombstone
        else OPTIONAL_ADAPTER_PATH_ROLE
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "state": REPLACEMENT_STATE,
        "active_path_role": active_path_role,
        "current_scheduler_owner": CURRENT_SCHEDULER_OWNER if replacement_active else LEGACY_SCHEDULER_OWNER,
        "legacy_scheduler_owner": LEGACY_SCHEDULER_OWNER,
        "local_tombstone_path_role": LOCAL_TOMBSTONE_PATH_ROLE,
        "optional_adapter_path_role": OPTIONAL_ADAPTER_PATH_ROLE,
        "current_surface_allowed_until_replacement": False,
        "replacement_required_before_retirement": not replacement_active,
        "allowed_operations": (
            ["status", "remove_legacy_jobs"]
            if not replacement_active and not local_tombstone
            else []
        ),
        "forbidden_operations": (
            ["ensure", "create", "edit", "resume", "trigger_run", "write_tick_script"]
            if not replacement_active and not local_tombstone
            else []
        ),
        "retirement_state": LOCAL_TOMBSTONE_RETIREMENT_STATE if local_tombstone else RETIREMENT_STATE,
        "replacement_owner": REPLACEMENT_OWNER,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "replacement_contract_expected": {
            "owner": REPLACEMENT_OWNER,
            "surface": REPLACEMENT_OWNER_SURFACE,
            "required_capabilities": list(OPL_REPLACEMENT_EXPECTED_CAPABILITIES),
            "must_not_write_mas_domain_truth": True,
            "status": (
                "active"
                if replacement_active
                else "local_physical_retired"
                if local_tombstone
                else "required_before_retirement"
            ),
        },
        "functional_consumer_boundary": build_functional_consumer_boundary(),
        "mas_retained_after_migration": list(MAS_RETAINED_AFTER_MIGRATION),
        "retirement_proof_required": list(RETIREMENT_PROOF_REQUIRED),
        "forbidden_authority_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        "forbidden_writes": list(FORBIDDEN_WRITES),
        "adapter_id": adapter_id,
        "manager": manager,
    }


def attach_consumer_migration_contract(
    payload: dict[str, Any],
    *,
    adapter_id: str | None = None,
    manager: str | None = None,
) -> dict[str, Any]:
    result = dict(payload)
    contract = build_consumer_migration_contract(adapter_id=adapter_id, manager=manager)
    result["active_path_role"] = contract["active_path_role"]
    result["consumer_migration"] = contract
    result["replacement_owner"] = REPLACEMENT_OWNER
    result["retirement_state"] = contract["retirement_state"]
    return result


__all__ = [
    "ACTIVE_PATH_ROLE",
    "CURRENT_SCHEDULER_OWNER",
    "DECLARATIVE_PACK_COMPILER_INPUT",
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "FORBIDDEN_WRITES",
    "FUNCTIONAL_MODULE_INVENTORY",
    "FUNCTIONAL_SURFACE_CLASSIFICATION",
    "FUNCTIONAL_FOLLOWTHROUGH_GAPS_OPEN_STATUS",
    "GENERATED_SURFACE_HANDOFF",
    "MAS_RETAINED_AFTER_MIGRATION",
    "MAS_RETAINED_THIN_PROGRAM_SURFACES",
    "MINIMAL_AUTHORITY_FUNCTION_IDS",
    "MINIMAL_AUTHORITY_FUNCTION_MANIFEST",
    "NO_ACTIVE_CALLER_PROOF",
    "LOCAL_SCHEDULER_CLEANUP_ONLY_PROOF",
    "OPL_CONSUMED_GENERIC_SURFACES",
    "OPL_FUNCTIONAL_HARNESS_COVERAGE",
    "OPL_REPLACEMENT_EXPECTATION_AUDIT",
    "OPL_REPLACEMENT_EXPECTED_CAPABILITIES",
    "REPLACEMENT_OWNER",
    "REPLACEMENT_OWNER_SURFACE",
    "REPLACEMENT_STATE",
    "REMAINING_GAP_CLASSIFICATION",
    "RETIREMENT_PROOF_REQUIRED",
    "RETIREMENT_STATE",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "LEGACY_SCHEDULER_OWNER",
    "LOCAL_TOMBSTONE_PATH_ROLE",
    "OPTIONAL_ADAPTER_PATH_ROLE",
    "attach_consumer_migration_contract",
    "build_functional_consumer_boundary",
    "build_consumer_migration_contract",
]
