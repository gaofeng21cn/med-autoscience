from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.action_catalog import TARGET_DOMAIN_ID, build_mas_action_catalog
from med_autoscience.controllers.domain_slo_scheduler_projection_parts.consumer_migration import (
    build_functional_consumer_boundary,
)
from med_autoscience.runtime_protocol.runtime_lifecycle_store_parts.agent_pack_refs import (
    AGENT_KNOWLEDGE_REFS,
    AGENT_PROMPT_REFS,
    AGENT_QUALITY_GATE_REFS,
    AGENT_SKILL_REFS,
    AGENT_STAGE_POLICY_REFS,
    REQUIRED_DOMAIN_PACK_PATHS,
)
from med_autoscience.runtime_protocol.runtime_lifecycle_store_parts.family_adoption import (
    build_domain_memory_descriptor,
    build_family_stage_control_plane,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_LABEL = "Med Auto Science"
DOMAIN_OWNER = "MedAutoScience"
GENERATED_SURFACE_OWNER = "one-person-lab"

FORBIDDEN_GENERIC_OWNER_ROLES = [
    "generic_scheduler_owner",
    "generic_daemon_owner",
    "generic_lifecycle_owner",
    "generic_queue_owner",
    "generic_attempt_ledger_owner",
    "generic_state_machine_runner_owner",
    "generic_cli_mcp_product_wrapper_owner",
    "generic_sidecar_owner",
    "generic_session_store_owner",
    "generic_status_workbench_owner",
    "generic_workspace_source_intake_owner",
    "generic_memory_transport_owner",
    "generic_artifact_gallery_owner",
    "generic_operator_workbench_owner",
    "generic_observability_slo_owner",
    "generic_persistence_engine_owner",
    "generic_sqlite_lifecycle_owner",
    "generic_native_helper_envelope_owner",
    "generic_review_repair_transport_owner",
    "generated_surface_owner_in_domain_repo",
]

GENERATED_SURFACES = [
    "cli",
    "mcp",
    "skill",
    "product_entry_manifest",
    "sidecar_export_dispatch",
    "status_read_model",
    "workbench_drilldown",
    "functional_harness_cases",
]

DECLARATIVE_DOMAIN_PACK = [
    "agent_canonical_semantic_pack",
    "stage_prompts",
    "stage_policies",
    "domain_skill_policies",
    "knowledge_refs",
    "stage_descriptors",
    "action_catalog",
    "domain_transition_table",
    "publication_route_memory_policy",
    "artifact_authority_policy",
    "source_readiness_policy",
    "owner_receipt_schema",
    "quality_gate_refs",
]

MINIMAL_AUTHORITY_FUNCTIONS = [
    "publication_quality_stage_gate_boundary",
    "ai_reviewer_quality_stage_gate_boundary",
    "artifact_mutation_stage_gate_boundary",
    "publication_route_memory_accept_reject_stage_gate_boundary",
    "source_readiness_stage_gate_boundary",
    "owner_receipt_signer",
    "medical_native_helper_implementation",
]
BACKWARD_READABLE_MINIMAL_AUTHORITY_IDS = [
    "publication_quality_verdict_authorizer",
    "ai_reviewer_quality_decision_authorizer",
    "artifact_mutation_authorizer",
    "publication_route_memory_accept_reject_decider",
    "source_readiness_verdict_authorizer",
]
FORBIDDEN_MECHANICAL_DECISION_SURFACES = [
    "script_exit_code_as_publication_quality_verdict",
    "function_return_value_as_ai_reviewer_quality_decision",
    "test_pass_as_artifact_mutation_authorization",
    "queue_completion_as_publication_route_memory_accept_reject",
    "file_presence_as_source_readiness_verdict",
]
ALLOWED_PRIVATE_AUTHORITY_JUDGMENT_MODES = [
    "ai_first_stage_gate",
    "ai_first_record_validator",
    "mechanical_guard",
    "refs_only_adapter",
]
AI_FIRST_STAGE_GATE_FUNCTION_IDS = [
    "publication_quality_verdict",
    "ai_reviewer_quality_decision",
    "publication_route_memory_accept_reject",
    "source_readiness_verdict",
]
AI_FIRST_RECORD_VALIDATOR_FUNCTION_IDS = ["artifact_mutation_authorization"]
MECHANICAL_GUARD_FUNCTION_IDS = ["owner_receipt_signer", "medical_helper_implementation"]
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
STAGE_QUALITY_GATE_BOUNDARIES = [
    {
        "boundary_id": "publication_quality_stage_gate_boundary",
        "legacy_readable_id": "publication_quality_verdict_authorizer",
        "program_role": "validator",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "requires_ai_first_record": True,
        "trace_refs": [
            "stage_quality_pack:publication_quality",
            "publication_eval/latest.json",
            "review_ledger",
            "evidence_ledger",
        ],
        "required_record_refs": ["ai_reviewer_record", "quality_pack_evidence_refs"],
        "route_back_semantics": "route_back_to_review_or_revision_stage",
        "typed_blocker_semantics": "publication_quality_blocker",
    },
    {
        "boundary_id": "ai_reviewer_quality_stage_gate_boundary",
        "legacy_readable_id": "ai_reviewer_quality_decision_authorizer",
        "program_role": "validator",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "requires_ai_first_record": True,
        "trace_refs": [
            "AI reviewer workflow",
            "AI reviewer-backed publication eval",
            "stage_quality_pack:ai_reviewer_quality",
        ],
        "required_record_refs": ["ai_reviewer_record", "reviewer_operating_system_trace"],
        "route_back_semantics": "route_back_to_ai_reviewer_repair_stage",
        "typed_blocker_semantics": "ai_reviewer_quality_blocker",
    },
    {
        "boundary_id": "artifact_mutation_stage_gate_boundary",
        "legacy_readable_id": "artifact_mutation_authorizer",
        "program_role": "materializer",
        "judgment_mode": "ai_first_record_validator",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "requires_ai_first_record": True,
        "trace_refs": [
            "stage_quality_pack:artifact_materialization",
            "canonical manuscript",
            "current_package",
            "artifact rebuild proof",
        ],
        "required_record_refs": ["quality_pack_evidence_refs", "artifact_rebuild_proof"],
        "route_back_semantics": "route_back_to_artifact_rebuild_or_source_revision_stage",
        "typed_blocker_semantics": "artifact_mutation_blocker",
    },
    {
        "boundary_id": "publication_route_memory_accept_reject_stage_gate_boundary",
        "legacy_readable_id": "publication_route_memory_accept_reject_decider",
        "program_role": "guard",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "requires_ai_first_record": True,
        "trace_refs": [
            "publication-route memory body",
            "memory writeback proposal",
            "memory writeback router receipt",
            "stage_quality_pack:publication_route_memory",
        ],
        "required_record_refs": ["publication_route_memory_body", "memory_writeback_receipt_refs"],
        "route_back_semantics": "route_back_to_memory_writeback_repair_stage",
        "typed_blocker_semantics": "publication_route_memory_writeback_blocker",
    },
    {
        "boundary_id": "source_readiness_stage_gate_boundary",
        "legacy_readable_id": "source_readiness_verdict_authorizer",
        "program_role": "validator",
        "judgment_mode": "ai_first_stage_gate",
        "decision_output_owner": "independent_reviewer_auditor_agent",
        "program_may_emit_pass_ready_verdict": False,
        "requires_ai_first_record": True,
        "trace_refs": [
            "study charter",
            "source readiness checks",
            "evidence ledger",
            "stage_quality_pack:source_readiness",
        ],
        "required_record_refs": ["study_charter", "quality_pack_evidence_refs"],
        "route_back_semantics": "route_back_to_source_intake_or_study_design_stage",
        "typed_blocker_semantics": "source_readiness_blocker",
    },
]


def _json_ready(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def build_standard_pack() -> dict[str, Any]:
    action_catalog = build_mas_action_catalog()
    stage_control_plane = build_family_stage_control_plane(
        family_action_catalog=action_catalog,
    )
    functional_boundary = build_functional_consumer_boundary()

    return {
        "domain_descriptor": _domain_descriptor(),
        "pack_compiler_input": _pack_compiler_input(),
        "generated_surface_handoff": _generated_surface_handoff(),
        "action_catalog": _with_forbidden_roles(action_catalog),
        "stage_control_plane": stage_control_plane,
        "memory_descriptor": _memory_descriptor(),
        "artifact_locator_contract": _artifact_locator_contract(),
        "owner_receipt_contract": _owner_receipt_contract(),
        "functional_privatization_audit": _functional_privatization_audit(functional_boundary),
        "private_functional_surface_policy": _private_functional_surface_policy(),
    }


def sync_standard_pack(*, repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    contracts = build_standard_pack()
    contract_dir = repo_root / "contracts"
    contract_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for name, payload in contracts.items():
        relative = Path("contracts") / f"{name}.json"
        path = repo_root / relative
        path.write_text(
            json.dumps(_json_ready(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        written.append(str(relative))
    return {
        "surface_kind": "mas_opl_standard_pack_sync",
        "target_domain_id": TARGET_DOMAIN_ID,
        "written": written,
    }


def _domain_descriptor() -> dict[str, Any]:
    return {
        "surface_kind": "domain_agent_descriptor",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "domain_label": DOMAIN_LABEL,
        "package_role": "opl_standard_domain_agent",
        "generated_surface_owner": GENERATED_SURFACE_OWNER,
        "domain_repo_can_own_generated_surface": False,
        "domain_repo_runtime_role": "domain_handler_target_and_authority_functions",
        "generated_descriptor_surfaces": list(GENERATED_SURFACES),
        "standard_contract_refs": {
            "action_catalog": "contracts/action_catalog.json",
            "stage_control_plane": "contracts/stage_control_plane.json",
            "pack_compiler_input": "contracts/pack_compiler_input.json",
            "generated_surface_handoff": "contracts/generated_surface_handoff.json",
            "functional_privatization_audit": "contracts/functional_privatization_audit.json",
        },
        "authority_boundary": {
            "opl_can_write_domain_truth": False,
            "opl_can_write_memory_body": False,
            "opl_can_authorize_quality_or_export": False,
            "domain_owns_truth_quality_artifact_memory_and_receipts": True,
            "domain_truth_owner": DOMAIN_OWNER,
        },
    }


def _pack_compiler_input() -> dict[str, Any]:
    return {
        "surface_kind": "opl_domain_pack_compiler_input",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "domain_pack_owner": TARGET_DOMAIN_ID,
        "canonical_semantic_pack_root": "agent/",
        "canonical_semantic_pack_role": (
            "declarative_medical_research_semantics_for_opl_pack_compiler"
        ),
        "src_role": "domain_handler_minimal_authority_functions_and_native_helpers_only",
        "src_must_not_be_canonical_semantic_pack": True,
        "required_domain_pack_paths": REQUIRED_DOMAIN_PACK_PATHS,
        "generated_surface_owner": GENERATED_SURFACE_OWNER,
        "declarative_domain_pack": DECLARATIVE_DOMAIN_PACK,
        "minimal_authority_functions": MINIMAL_AUTHORITY_FUNCTIONS,
        "minimal_authority_semantic_model": (
            "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
        ),
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
        "boundary_ids": MINIMAL_AUTHORITY_FUNCTIONS[:5],
        "stage_quality_gate_boundaries": STAGE_QUALITY_GATE_BOUNDARIES,
        "backward_readable_minimal_authority_ids": BACKWARD_READABLE_MINIMAL_AUTHORITY_IDS,
        "forbidden_mechanical_decision_surfaces": FORBIDDEN_MECHANICAL_DECISION_SURFACES,
        "independent_executor_reviewer_agent_policy": INDEPENDENT_EXECUTOR_REVIEWER_AGENT_POLICY,
        "requires_ai_first_record": True,
        "generated_surfaces_requested": GENERATED_SURFACES,
        "domain_repo_can_own_generated_surface": False,
        "domain_repo_runtime_role": "domain_handler_target_and_authority_functions",
        "source_refs": {
            "canonical_agent_pack_root": "agent/",
            "required_domain_pack_paths": REQUIRED_DOMAIN_PACK_PATHS,
            "action_catalog": "src/med_autoscience/action_catalog.py::build_mas_action_catalog",
            "stage_control_plane": (
                "src/med_autoscience/runtime_protocol/runtime_lifecycle_store_parts/"
                "family_adoption.py::build_family_stage_control_plane"
            ),
            "memory_descriptor": (
                "src/med_autoscience/runtime_protocol/runtime_lifecycle_store_parts/"
                "family_adoption.py::build_domain_memory_descriptor"
            ),
            "functional_audit": (
                "src/med_autoscience/controllers/domain_slo_scheduler_projection_parts/"
                "consumer_migration.py::build_functional_consumer_boundary"
            ),
        },
        "authority_boundary": {
            "opl_can_write_domain_truth": False,
            "opl_can_write_memory_body": False,
            "opl_can_authorize_quality_or_export": False,
            "domain_can_claim_generated_surface_owner": False,
            "agent_pack_owner": DOMAIN_OWNER,
            "src_role": "domain_handler_minimal_authority_native_helper",
        },
    }


def _generated_surface_handoff() -> dict[str, Any]:
    return {
        "surface_kind": "opl_generated_surface_handoff",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "generated_surface_owner": GENERATED_SURFACE_OWNER,
        "domain_repo_can_own_generated_surface": False,
        "source_contract_ref": "contracts/pack_compiler_input.json",
        "consumes_agent_pack_refs": True,
        "agent_pack_ref_source": "contracts/pack_compiler_input.json#/required_domain_pack_paths",
        "generated_surface_policy": {
            "may_compile": [
                "cli_descriptors",
                "mcp_tool_descriptors",
                "skill_descriptors",
                "product_entry_descriptors",
                "status_and_workbench_projection_descriptors",
            ],
            "must_read_semantics_from": "agent/",
            "must_dispatch_to": "MAS domain handler targets and minimal authority functions",
            "must_not_write": [
                "MAS study truth",
                "publication-route memory body",
                "AI reviewer verdict",
                "publication verdict",
                "artifact authority",
                "source body",
                "current_package",
            ],
        },
        "generated_surfaces": [
            {
                "surface_id": surface_id,
                "owner": GENERATED_SURFACE_OWNER,
                "domain_repo_can_own_generated_surface": False,
                "status": "descriptor_source_available",
            }
            for surface_id in GENERATED_SURFACES
        ],
        "required_domain_handoff": [
            "owner_receipt_schema",
            "typed_blocker_schema",
            "minimal_authority_function_refs",
            "no_forbidden_write_evidence",
        ],
    }


def _with_forbidden_roles(action_catalog: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(action_catalog)
    payload["forbidden_generic_owner_roles"] = FORBIDDEN_GENERIC_OWNER_ROLES
    payload["generated_surface_owner"] = GENERATED_SURFACE_OWNER
    payload["domain_repo_can_own_generated_surface"] = False
    payload["descriptor_projection_owner"] = GENERATED_SURFACE_OWNER
    payload["domain_repo_runtime_role"] = "domain_handler_target_and_authority_functions"
    payload["domain_handler_target_owner"] = DOMAIN_OWNER
    payload["catalog_role"] = (
        "domain_action_intent_and_handler_target_input_for_opl_generated_descriptors"
    )
    return payload


def _memory_descriptor() -> dict[str, Any]:
    descriptor = dict(build_domain_memory_descriptor())
    descriptor["root_contract_role"] = "opl_standard_domain_agent_memory_descriptor"
    descriptor["memory_body_owner"] = DOMAIN_OWNER
    descriptor["opl_projection_policy"] = "locator_and_receipt_refs_only"
    descriptor["authority_boundary"] = {
        "opl_can_write_memory_body": False,
        "opl_can_accept_or_reject_writeback": False,
        "domain_memory_accept_reject_owner": DOMAIN_OWNER,
    }
    return descriptor


def _artifact_locator_contract() -> dict[str, Any]:
    return {
        "surface_kind": "artifact_locator_contract",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "canonical_artifact_authority": DOMAIN_OWNER,
        "opl_projection_policy": "locator_lifecycle_and_receipt_refs_only",
        "authority_boundary": {
            "opl_can_mutate_artifacts": False,
            "opl_can_authorize_publication_quality": False,
            "domain_artifact_authority_owner": DOMAIN_OWNER,
        },
    }


def _owner_receipt_contract() -> dict[str, Any]:
    return {
        "surface_kind": "owner_receipt_contract",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "allowed_receipt_classes": [
            "owner_receipt",
            "typed_blocker",
            "no_regression_evidence",
            "memory_writeback_receipt",
            "artifact_lifecycle_receipt",
            "agent_capability_evolution_receipt",
        ],
        "forbidden_claims": [
            "opl_authorized_domain_ready",
            "opl_authorized_quality_or_export_verdict",
            "opl_wrote_domain_truth",
            "opl_wrote_memory_body",
            "opl_meta_agent_wrote_study_truth",
            "opl_meta_agent_authorized_publication_quality",
        ],
    }


def _functional_privatization_audit(functional_boundary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "functional_privatization_audit",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "target_domain_id": TARGET_DOMAIN_ID,
        "functional_consumer_boundary": dict(functional_boundary),
        "functional_followthrough_gap_summary": dict(functional_boundary["functional_followthrough_gap_summary"]),
        "authority_boundary": {
            "opl_can_write_domain_truth": False,
            "opl_can_write_memory_body": False,
            "opl_can_authorize_quality_or_export": False,
            "domain_can_claim_generic_runtime_owner": False,
            "domain_repo_can_own_generated_surface": False,
        },
    }


def _private_functional_surface_policy() -> dict[str, Any]:
    return {
        "surface_kind": "opl_domain_private_functional_surface_admission_policy",
        "schema_version": 1,
        "domain_id": TARGET_DOMAIN_ID,
        "default_posture": "forbidden_until_classified_and_receipted",
        "forbidden_private_surface_classes": [
            "generic_scheduler",
            "generic_queue_or_attempt_ledger",
            "generic_cli_mcp_product_wrapper",
            "generic_workbench_shell",
            "generic_observability_runtime",
        ],
        "allowed_private_surface_classes": [
            "ai_first_stage_quality_gate_boundary",
            "domain_native_helper_implementation",
            "owner_receipt_signer",
        ],
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
        "backward_readable_legacy_ids": BACKWARD_READABLE_MINIMAL_AUTHORITY_IDS,
        "forbidden_primary_allowed_private_surface_models": [
            "domain_truth_verdict_authorizer",
            "*_authorizer",
        ],
        "forbidden_mechanical_decision_surfaces": FORBIDDEN_MECHANICAL_DECISION_SURFACES,
        "independent_executor_reviewer_agent_policy": INDEPENDENT_EXECUTOR_REVIEWER_AGENT_POLICY,
        "requires_ai_first_record": True,
        "stage_quality_gate_boundaries": STAGE_QUALITY_GATE_BOUNDARIES,
        "forbidden_generic_owner_roles": FORBIDDEN_GENERIC_OWNER_ROLES,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync MAS OPL standard domain-agent pack contracts.")
    parser.add_argument("--check", action="store_true", help="Print the generated pack without writing.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if args.check:
        print(json.dumps(build_standard_pack(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    print(json.dumps(sync_standard_pack(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
