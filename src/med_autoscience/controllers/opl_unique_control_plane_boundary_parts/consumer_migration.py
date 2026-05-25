from __future__ import annotations

from typing import Any

from .functional_followthrough_gaps import (
    FUNCTIONAL_FOLLOWTHROUGH_GAPS_OPEN_STATUS,
    OPL_REPLACEMENT_EXPECTATION_AUDIT,
    REMAINING_GAP_CLASSIFICATION,
    SOURCE_PURITY_WRAPPER_TAIL_MODULE_IDS,
    build_functional_followthrough_gap_summary,
)
from .generated_surface_handoff import build_generated_surface_handoff
from .generated_caller_retirement import (
    build_generated_default_caller_boundary,
)
from .consumer_migration_inventory import (
    FUNCTIONAL_MODULE_INVENTORY,
    FUNCTIONAL_SURFACE_CLASSIFICATION,
)

SCHEMA_VERSION = 1
SURFACE_KIND = "mas_runtime_control_retirement_consumer_projection"
ACTIVE_PATH_ROLE = "opl_replacement_default"
LOCAL_TOMBSTONE_PATH_ROLE = "history_tombstone_provenance_only"
OPTIONAL_ADAPTER_PATH_ROLE = "history_tombstone_provenance_only"
HERMES_TOMBSTONE_PATH_ROLE = "history_tombstone_provenance_only"
CURRENT_SCHEDULER_OWNER = "opl_provider_runtime_manager"
LEGACY_SCHEDULER_OWNER = "retired_provenance_only"
REPLACEMENT_OWNER = "one-person-lab"
REPLACEMENT_OWNER_SURFACE = "opl_provider_runtime_manager"
REPLACEMENT_STATE = "opl_replacement_contract_active"
RETIREMENT_STATE = "retired_runtime_tombstone_requires_standard_agent_purity_guard"
LOCAL_TOMBSTONE_RETIREMENT_STATE = "local_legacy_history_tombstone_provenance_only"

MAS_DOMAIN_AUTHORITY_AFTER_MIGRATION = (
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
    "standard_agent_purity_guard",
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
MAS_DOMAIN_AUTHORITY_THIN_PROGRAM_SURFACES = (
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
    "status": "ready_for_opl_pack_compiler_consumption_standard_agent_purity_guarded",
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
        "product_status",
        "product_session",
        "domain_handler",
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
GENERATED_DEFAULT_CALLER_BOUNDARY = build_generated_default_caller_boundary(
    schema_version=SCHEMA_VERSION,
    replacement_owner=REPLACEMENT_OWNER,
)
STANDARD_AGENT_PURITY = {
    "surface_kind": "mas_standard_opl_agent_purity",
    "schema_version": SCHEMA_VERSION,
    "status": "standard_agent_source_shape_landed",
    "agent_shape": "declarative_medical_pack_minimal_authority_functions_refs_only_projection",
    "default_runtime_owner": REPLACEMENT_OWNER,
    "generated_surface_owner": REPLACEMENT_OWNER,
    "domain_owner": "med-autoscience",
    "active_private_generic_residue_count": 0,
    "functional_structure_gap_count": 0,
    "default_caller_count": 0,
    "default_caller_readiness_status": "opl_generated_default_caller_ready",
    "source_purity_cutover_status": "standard_agent_source_shape_landed",
    "repo_local_wrapper_tail_count": 0,
    "repo_local_wrapper_tail_module_ids": [],
    "former_repo_local_wrapper_tail_module_ids": list(SOURCE_PURITY_WRAPPER_TAIL_MODULE_IDS),
    "domain_repo_physical_delete_authorized": False,
    "runtime_package_residue_count": 0,
    "retired_alias_residue_refs": [],
    "history_detail_in_default_read_model": False,
    "domain_projection_policy": "refs_receipts_blockers_only_no_body_verdict_or_blob",
    "retained_surface_classes": [
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    ],
    "forbidden_active_claims": [
        "mas_default_generic_scheduler",
        "mas_resident_generic_daemon",
        "mas_owned_generic_queue",
        "mas_owned_attempt_ledger",
        "mas_generic_transition_runner",
        "mas_generic_workbench_shell",
        "compatibility_alias_for_retired_runtime",
        "provider_completion_is_domain_completion",
    ],
}


STANDARD_AGENT_PURITY_GUARD = {
    "status": "standard_agent_purity_cutover_guard",
    "default_caller_count": 0,
    "default_manager": "opl",
    "default_caller_readiness_status": "opl_generated_default_caller_ready",
    "source_purity_cutover_status": "standard_agent_source_shape_landed",
    "repo_local_wrapper_tail_count": 0,
    "repo_local_wrapper_tail_module_ids": [],
    "former_repo_local_wrapper_tail_module_ids": list(SOURCE_PURITY_WRAPPER_TAIL_MODULE_IDS),
    "domain_repo_physical_delete_authorized": False,
    "runtime_package_residue_count": 0,
    "retired_alias_residue_refs": [],
    "proof_items": [
        "standard_agent_purity.active_private_generic_residue_count=0",
        "standard_agent_purity.default_caller_count=0",
        "standard_agent_purity.retired_alias_residue_refs=[]",
        "standard_agent_purity.default_caller_readiness_status=opl_generated_default_caller_ready",
        "standard_agent_purity.source_purity_cutover_status=standard_agent_source_shape_landed",
        "standard_agent_purity.domain_projection_policy=refs_receipts_blockers_only_no_body_verdict_or_blob",
    ],
}
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
                "owner-route handoff ref",
            ],
            "cannot_absorb_reason": "Only MAS can sign domain receipt, blocker, and owner-route handoff authority.",
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
    "all_other_program_surfaces": "opl_generated_or_domain_refs_projection_source",
    "forbidden_long_term_mas_shell_owners": [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_handler",
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
    domain_authority_refs_retirement_gates = [
        dict(item["retirement_gate"])
        for item in FUNCTIONAL_MODULE_INVENTORY
        if item["classification"] == "domain_authority_refs"
    ]
    functional_followthrough_gap_summary = build_functional_followthrough_gap_summary(
        classification_counts=classification_counts,
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_functional_consumer_boundary",
        "status": "opl_consumes_generic_surfaces_mas_supplies_domain_authority_pack",
        "consumer_role": "domain_authority_pack_thin_program_surface",
        "generic_surface_owner": REPLACEMENT_OWNER,
        "generic_surfaces_consumed_from_opl": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_does_not_own": list(OPL_CONSUMED_GENERIC_SURFACES),
        "mas_domain_authority_surfaces": list(MAS_DOMAIN_AUTHORITY_THIN_PROGRAM_SURFACES),
        "declarative_pack_compiler_input": dict(DECLARATIVE_PACK_COMPILER_INPUT),
        "generated_surface_handoff": {
            key: [dict(item) if isinstance(item, dict) else item for item in value]
            if isinstance(value, list)
            else value
            for key, value in GENERATED_SURFACE_HANDOFF.items()
        },
        "generated_default_caller_boundary": {
            key: [dict(item) if isinstance(item, dict) else item for item in value]
            if isinstance(value, list)
            else value
            for key, value in GENERATED_DEFAULT_CALLER_BOUNDARY.items()
        },
        "standard_agent_purity": dict(STANDARD_AGENT_PURITY),
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
            "classification_gap_count": 0,
            "functional_structure_gap_count": functional_followthrough_gap_summary[
                "functional_structure_gap_count"
            ],
            "active_private_generic_residue_count": 0,
            "repo_local_wrapper_tail_count": functional_followthrough_gap_summary[
                "repo_local_wrapper_tail_count"
            ],
            "repo_local_wrapper_tail_module_ids": list(
                functional_followthrough_gap_summary[
                    "repo_local_wrapper_tail_module_ids"
                ]
            ),
            "source_purity_cutover_status": functional_followthrough_gap_summary[
                "source_purity_cutover_status"
            ],
            "remaining_gap_classification": functional_followthrough_gap_summary[
                "remaining_gap_classification"
            ],
            "remaining_functional_followthrough_gate_ids": list(
                functional_followthrough_gap_summary[
                    "remaining_functional_followthrough_gate_ids"
                ]
            ),
            "closed_functional_structure_gate_ids": list(
                functional_followthrough_gap_summary[
                    "closed_functional_structure_gate_ids"
                ]
            ),
        },
        "functional_followthrough_gap_summary": functional_followthrough_gap_summary,
        "domain_authority_refs_retirement_gates": domain_authority_refs_retirement_gates,
        "domain_authority_refs_index_role": {
            "classification": "domain_authority_refs",
            "current_mas_role": "domain_authority_receipt_and_locator_ref_index",
            "authority": "refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine",
            "owner": REPLACEMENT_OWNER,
            "provenance_role": "domain_authority_ref_locator_index",
            "body_policy": "refs_receipts_blockers_only",
            "mas_may_index_domain_receipts": True,
            "mas_may_claim_generic_persistence_engine": False,
            "mas_consumes_opl_current_control_state_refs": True,
            "mas_may_write_domain_truth": False,
            "generic_owner_claim_allowed": False,
            "forbidden_mas_roles": [
                "generic_persistence_engine",
                "generic_lifecycle_engine",
                "generic_runtime_lifecycle_owner",
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
            "mas_domain_authority_pack": list(MAS_DOMAIN_AUTHORITY_THIN_PROGRAM_SURFACES),
            "refs_only_memory_writeback_chain": {
                "opl_consumes": [
                    "consumed_publication_route_memory_refs",
                    "typed_closeout_proposal_refs",
                    "memory_write_router_receipt_refs",
                    "workspace_writeback_receipt_refs",
                    "opl_aion_display_receipt_refs",
                ],
                "mas_domain_authority_refs": [
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
                "mas_domain_authority_refs": [
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
                "mas_domain_authority_refs": [
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
                "mas_domain_authority_refs": [
                    "human_gate_domain_receipt",
                    "repair_owner_receipt",
                    "stop_loss_receipt",
                    "typed_blocker",
                ],
                "state_chain_completion_is_publication_ready": False,
            },
        },
        "standard_agent_purity_guard": dict(STANDARD_AGENT_PURITY_GUARD),
        "standard_agent_purity_guard_scope": [
            "cli_default",
            "mcp_default",
            "product_entry_default",
            "domain_handler_default",
            "test_lane_default",
        ],
        "proof_surfaces": [
            "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
            "opl_current_control_state owner refs",
            "product_entry_manifest.functional_consumer_boundary",
            "domain_handler_export.functional_consumer_boundary",
            "functional_consumer_boundary.standard_agent_purity",
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
    legacy_runtime_surface = bool(manager_key or adapter_id) and not replacement_active
    active_path_role = (
        ACTIVE_PATH_ROLE
        if replacement_active
        else LOCAL_TOMBSTONE_PATH_ROLE
        if legacy_runtime_surface
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
        "allowed_operations": [],
        "forbidden_operations": [
            "status",
            "remove_legacy_jobs",
            "ensure",
            "create",
            "edit",
            "resume",
            "trigger_run",
            "write_tick_script",
        ],
        "retirement_state": LOCAL_TOMBSTONE_RETIREMENT_STATE if legacy_runtime_surface else RETIREMENT_STATE,
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
                else "history_tombstone_provenance_only"
                if legacy_runtime_surface
                else "required_before_retirement"
            ),
        },
        "functional_consumer_boundary": build_functional_consumer_boundary(),
        "mas_domain_authority_after_migration": list(MAS_DOMAIN_AUTHORITY_AFTER_MIGRATION),
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
    "GENERATED_DEFAULT_CALLER_BOUNDARY",
    "MAS_RETAINED_AFTER_MIGRATION",
    "MAS_RETAINED_THIN_PROGRAM_SURFACES",
    "MINIMAL_AUTHORITY_FUNCTION_IDS",
    "MINIMAL_AUTHORITY_FUNCTION_MANIFEST",
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
    "STANDARD_AGENT_PURITY_GUARD",
    "SURFACE_KIND",
    "LEGACY_SCHEDULER_OWNER",
    "LOCAL_TOMBSTONE_PATH_ROLE",
    "OPTIONAL_ADAPTER_PATH_ROLE",
    "attach_consumer_migration_contract",
    "build_functional_consumer_boundary",
    "build_consumer_migration_contract",
]
