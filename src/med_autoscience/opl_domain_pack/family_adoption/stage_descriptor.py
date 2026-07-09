from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience import stage_quality_contract
from med_autoscience import stage_skill_surface_projection
from med_autoscience.stage_route_contract import (
    PROGRESS_FIRST_SPRINT_CONTRACT_FIELD,
    STAGE_ROUTE_CONTRACT_REF,
    load_stage_route_contract_payload,
)

from .. import hypothesis_portfolio_pack
from ..agent_pack_refs import (
    AGENT_QUALITY_GATE_REFS,
    AGENT_SKILL_REFS,
    AGENT_STAGE_NATIVE_SEMANTIC_PACK_REF,
    stage_knowledge_refs,
    stage_policy_ref,
    stage_prompt_ref,
)
from ..progress_first_policies import PROGRESS_DELTA_POLICY, TYPED_BLOCKER_LINEAGE_POLICY
from ..stage_completion_policy import STAGE_COMPLETION_POLICY
from ..stage_throughput_contracts import (
    human_gate_progress_evidence_contract,
    minimum_forward_delta_contract,
    route_obligation_lens,
)
from ..user_stage_log_contract import USER_STAGE_LOG_CONTRACT

STAGE_LED_AUTONOMY_INVENTORY_REF = "docs/references/integration/stage_led_autonomy_family_inventory.md"
STAGE_LED_AUTONOMY_POLICY_REF = "docs/policies/study-workflow/stage_led_research_autonomy.md"
STAGE_KNOWLEDGE_PLANE_CONTRACT_REF = (
    "med_autoscience.stage_knowledge_contract.stage_knowledge_plane_contract"
)
STAGE_QUALITY_PACK_CONTRACT_REF = stage_quality_contract.CONTRACT_REF
STANDARD_STAGE_PACK_CONFORMANCE_VERSION = "standard-stage-pack.v2"
ORDINARY_DEFAULT_STAGE_ID = "direction_and_route_selection"
DOMAIN_TOOL_AFFORDANCE_CATALOG_REF = "agent/tools/domain_affordances.md"
STANDARD_STAGE_PACK_L4_REQUIRED_GATES = [
    "repo_layout_declared",
    "stage_pack_v2_required",
    "stage_prompt_skill_knowledge_quality_gate_refs_resolve",
    "tool_affordance_boundary_declared",
    "receipt_schema_declared",
    "minimal_authority_functions_declared",
    "generated_surface_handoff_declared",
    "no_forbidden_write_contract_declared",
]
STANDARD_STAGE_PACK_L5_EVIDENCE_REQUIRED = [
    "real_user_path",
    "long_soak_recovery",
    "release_install_evidence",
    "owner_acceptance",
    "direct_and_opl_hosted_parity_at_scale",
]
STAGE_SUBPACKET_GATE_SOURCE_REF = (
    "src/med_autoscience/opl_domain_pack/family_adoption/stage_descriptor.py"
    "::_stage_typed_cognitive_subpacket_gate"
)
STAGE_SUBPACKET_GATE_CONFIGS: dict[str, dict[str, Any]] = {
    "manuscript_authoring": {
        "packet_id": "manuscript_packet",
        "packet_surface_kind": "mas_manuscript_authoring_packet",
        "packet_role": "canonical_manuscript_handoff_candidate",
        "admission_gate_id": "manuscript_packet_admission_gate",
        "consumed_ref_families": [
            "bounded_analysis_evidence_refs",
            "claim_evidence_map_refs",
            "source_grounding_refs",
            "citation_source_refs",
            "display_table_figure_refs",
            "controller_decision_refs",
        ],
        "produced_ref_families": [
            "canonical_manuscript_refs",
            "manuscript_claim_trace_refs",
            "citation_source_handoff_refs",
            "display_table_figure_handoff_refs",
            "route_back_or_owner_receipt_candidate_refs",
        ],
        "route_back_conditions": [
            "missing_or_stale_evidence_source_citation_display_or_claim_boundary_refs",
            "canonical_manuscript_source_not_current_against_claim_evidence_map",
            "specialist_candidate_requires_owner_acceptance_before_handoff",
        ],
        "typed_blocker_conditions": [
            "artifact_mutation_authority_missing",
            "source_readiness_or_citation_authenticity_unresolved",
            "canonical_manuscript_authority_path_missing",
        ],
        "human_gate_conditions": [
            "journal_strategy_or_claim_expansion_requires_PI_decision",
            "external_source_or_credential_authority_required",
        ],
    },
    "review_and_quality_gate": {
        "packet_id": "independent_review_packet",
        "packet_surface_kind": "mas_independent_review_packet",
        "packet_role": "independent_reviewer_auditor_gate_input",
        "admission_gate_id": "independent_review_packet_admission_gate",
        "consumed_ref_families": [
            "manuscript_packet_refs",
            "canonical_manuscript_refs",
            "evidence_ledger_refs",
            "claim_citation_support_refs",
            "research_integrity_gate_input_refs",
            "artifact_and_display_freshness_refs",
        ],
        "produced_ref_families": [
            "independent_reviewer_auditor_record_refs",
            "review_ledger_refs",
            "publication_eval_candidate_refs",
            "route_back_or_typed_blocker_refs",
            "memory_accept_reject_handoff_refs",
        ],
        "route_back_conditions": [
            "claim_source_citation_statistics_display_or_artifact_gap_remains",
            "same_invocation_attempts_to_self_review_executor_output",
            "research_integrity_gate_input_missing_or_unresolved",
        ],
        "typed_blocker_conditions": [
            "publication_quality_blocker",
            "ai_reviewer_quality_blocker",
            "source_citation_statistics_display_data_or_package_blocker",
        ],
        "human_gate_conditions": [
            "official_go_stop_reroute_or_publication_strategy_decision_required",
            "external_release_or_submission_authorization_requested",
        ],
    },
    "finalize_and_publication_handoff": {
        "packet_id": "publication_handoff_admission_packet",
        "packet_surface_kind": "mas_publication_handoff_admission_packet",
        "packet_role": "publication_handoff_candidate_before_external_delivery",
        "admission_gate_id": "publication_handoff_admission_gate",
        "consumed_ref_families": [
            "independent_review_packet_refs",
            "publication_eval_refs",
            "controller_decision_refs",
            "artifact_rebuild_and_freshness_refs",
            "journal_requirement_refs",
            "human_gate_state_refs",
        ],
        "produced_ref_families": [
            "publication_handoff_receipt_candidate_refs",
            "artifact_authority_refs",
            "package_freshness_proof_refs",
            "journal_submission_checklist_refs",
            "route_back_blocker_or_human_gate_refs",
        ],
        "route_back_conditions": [
            "quality_source_artifact_journal_fit_package_or_memory_gap_remains",
            "reviewer_or_artifact_freshness_stale_against_controller_decision",
            "handoff_packet_would_change_claim_or_package_authority",
        ],
        "typed_blocker_conditions": [
            "artifact_mutation_blocker",
            "publication_quality_blocker",
            "source_readiness_or_submission_package_blocker",
        ],
        "human_gate_conditions": [
            "external_submission_PI_journal_strategy_or_portal_action_required",
            "credential_or_irreversible_delivery_authorization_required",
        ],
    },
}


def plane_source_refs(descriptor: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_action_catalog",
            "role": "action_catalog",
        },
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_stage_control_plane_descriptor",
            "role": "deep_descriptor",
        },
        {
            "ref_kind": "repo_path",
            "ref": str(_mapping(descriptor.get("source_refs")).get("route_contract_source") or STAGE_ROUTE_CONTRACT_REF),
            "role": "route_contract_source",
        },
        {
            "ref_kind": "repo_path",
            "ref": str(
                _mapping(descriptor.get("source_refs")).get("stage_native_semantic_pack_source")
                or AGENT_STAGE_NATIVE_SEMANTIC_PACK_REF
            ),
            "role": "stage_native_semantic_pack",
        },
        {
            "ref_kind": "python_symbol",
            "ref": STAGE_KNOWLEDGE_PLANE_CONTRACT_REF,
            "role": "stage_knowledge_plane_contract",
        },
        {
            "ref_kind": "python_symbol",
            "ref": STAGE_QUALITY_PACK_CONTRACT_REF,
            "role": "quality_pack_contract",
        },
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
            "role": "stage_deliverable_index",
        },
        {
            "ref_kind": "repo_path",
            "ref": STAGE_LED_AUTONOMY_INVENTORY_REF,
            "role": "inventory_reference",
        },
        {
            "ref_kind": "repo_path",
            "ref": "agent/",
            "role": "canonical_semantic_pack_root",
        },
    ]


def build_stage_descriptor(stage: Mapping[str, Any], *, descriptor: Mapping[str, Any]) -> dict[str, Any]:
    runtime_event_refs = _required_runtime_event_refs(stage)
    cohort_loop_refs = _stage_cohort_loop_refs(stage)
    stage_id = str(stage["stage_id"])
    domain_stage_refs = list(stage["domain_stage_refs"])
    allowed_action_refs = list(stage["allowed_action_refs"])
    knowledge_refs = stage_knowledge_refs(stage)
    quality_pack_refs = stage_quality_contract.quality_pack_ids_for_stages(domain_stage_refs)
    skill_refs = [
        *[
            {"ref_kind": "repo_path", "ref": ref, "role": "domain_pack_skill_policy"}
            for ref in AGENT_SKILL_REFS
        ],
        {"ref_kind": "skill_id", "ref": "med-autoscience", "role": "domain_skill"},
        {"ref_kind": "skill_id", "ref": "mas", "role": "codex_app_skill"},
    ]
    prompt_ref = {
        "ref_kind": "repo_path",
        "ref": stage_prompt_ref(stage),
        "role": "stage_prompt",
    }
    evaluation_refs = [
        {
            "ref_kind": "json_pointer",
            "ref": "/family_stage_control_plane_descriptor/authority_boundary",
            "role": "authority_boundary",
        },
        {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "progress_projection"},
        {
            "ref_kind": "json_pointer",
            "ref": "/product_entry_manifest/owner_receipt_contract",
            "role": "owner_receipt_gate",
        },
        *[
            {"ref_kind": "repo_path", "ref": ref, "role": "agent_quality_gate"}
            for ref in AGENT_QUALITY_GATE_REFS
        ],
    ]
    independent_gate_receipt_required = bool(stage.get("independent_gate_receipt_required", False))
    mandatory_stage_hook_obligations = _mandatory_stage_hook_obligations(stage_id)
    mandatory_pre_gate_checks = _mandatory_stage_hook_pre_gate_checks(stage_id)
    typed_subpacket_gate = _stage_typed_cognitive_subpacket_gate(stage_id)
    source_refs = [
        *plane_source_refs(descriptor),
        {
            "ref_kind": "route_stage_refs",
            "ref": domain_stage_refs,
            "role": "mas_route_projection",
        },
    ]
    stage_contract = {
        "requires": list(stage.get("requires", [])),
        "ensures": list(stage.get("ensures", [])),
        "boundary_assumptions": [
            "MAS owns study truth, route decisions, evidence/review ledgers, publication eval, and package authority.",
            "OPL admission only checks descriptor composition; it cannot authorize publication quality or submission readiness.",
        ],
        "stage_completion_policy": {
            **STAGE_COMPLETION_POLICY,
            "policy_ref": f"stage-completion-policy:mas/{stage['stage_id']}",
            "stage_id": stage["stage_id"],
            "target_domain_id": "med-autoscience",
        },
        "user_stage_log_contract": USER_STAGE_LOG_CONTRACT,
        "progress_delta_policy": PROGRESS_DELTA_POLICY,
        "typed_blocker_lineage_policy": TYPED_BLOCKER_LINEAGE_POLICY,
        "minimum_forward_delta": minimum_forward_delta_contract(stage),
        "route_obligation_lens": route_obligation_lens(stage),
        "human_gate_progress_evidence": human_gate_progress_evidence_contract(),
        "hypothesis_portfolio_evidence_pack": (
            hypothesis_portfolio_pack.stage_hypothesis_portfolio_evidence_pack_contract()
        ),
        "expected_receipt_refs": _stage_expected_receipt_refs(stage_id),
        "receipt_schema_refs": _stage_receipt_schema_refs(),
        "authority_function_refs": _stage_authority_function_refs(),
        "l4_entry_gate": _stage_l4_entry_gate(),
        "l5_entry_gate": _stage_l5_entry_gate(),
    }
    progress_sprint_contract = _stage_progress_sprint_contract(stage, descriptor=descriptor)
    if progress_sprint_contract is not None:
        stage_contract["late_stage_progress_sprint_contract"] = progress_sprint_contract
    if mandatory_pre_gate_checks:
        stage_contract["mandatory_pre_gate_checks"] = mandatory_pre_gate_checks
    if typed_subpacket_gate:
        stage_contract["typed_cognitive_subpacket_gate"] = typed_subpacket_gate
    trust_boundary = {
        "lane": stage.get("trust_lane", "domain_agent"),
        "static_check_eligible": False,
        "effect_boundary": stage.get("trust_lane") == "ai_decision",
        "records_runtime_events": True,
        "owner_receipt_required": True,
        "human_gate_required": False,
        "runtime_guard_required": True,
    }
    if runtime_event_refs:
        stage_contract["runtime_event_refs"] = runtime_event_refs
        trust_boundary["runtime_event_refs"] = runtime_event_refs
    stage_contract.update(cohort_loop_refs)
    codex_cli_launch_packet = stage_skill_surface_projection.build_codex_cli_launch_packet(
        stage_id=stage_id,
        prompt_ref=prompt_ref,
        skill_refs=skill_refs,
        knowledge_refs=knowledge_refs,
        quality_gate_refs=evaluation_refs,
        quality_pack_refs=quality_pack_refs,
        allowed_action_refs=allowed_action_refs,
        expected_runtime_event_refs=runtime_event_refs,
        independent_gate_receipt_required=independent_gate_receipt_required,
    )
    if mandatory_pre_gate_checks:
        codex_cli_launch_packet["mandatory_pre_gate_checks"] = mandatory_pre_gate_checks
    if typed_subpacket_gate:
        codex_cli_launch_packet["typed_cognitive_subpacket_gate"] = typed_subpacket_gate
    stage_descriptor = {
        "stage_id": stage["stage_id"],
        "stage_kind": stage["stage_kind"],
        "title": stage["title"],
        "summary": f"{stage['title']} projected from MAS-owned Stage-Led Autonomy routes for OPL discovery.",
        "stage_pack_conformance_version": STANDARD_STAGE_PACK_CONFORMANCE_VERSION,
        "goal": _stage_goal(stage, descriptor=descriptor),
        "owner": "MedAutoScience",
        "domain_stage_refs": domain_stage_refs,
        "inputs": [
            {"ref_kind": "json_pointer", "ref": "/family_action_catalog", "role": "allowed_action_catalog"},
            {
                "ref_kind": "json_pointer",
                "ref": "/family_stage_control_plane_descriptor/stage_knowledge_plane",
                "role": "stage_knowledge_plane",
            },
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "progress_read_model"},
        ],
        "knowledge_refs": knowledge_refs,
        "quality_pack_refs": quality_pack_refs,
        "quality_pack_projection": stage_quality_contract.build_stage_quality_pack_ref_projection(
            domain_stage_refs
        ),
        "stage_skill_surface_projection": stage_skill_surface_projection.build_stage_skill_surface_projection(
            stage_id=stage_id
        ),
        "skills": skill_refs,
        "tool_refs": _stage_tool_refs(),
        "tool_affordance_boundary": _stage_tool_affordance_boundary(stage_id),
        "prompt_refs": [prompt_ref],
        "policy_refs": [
            {"ref_kind": "repo_path", "ref": STAGE_ROUTE_CONTRACT_REF, "role": "route_contract"},
            {"ref_kind": "repo_path", "ref": STAGE_LED_AUTONOMY_POLICY_REF, "role": "stage_led_policy"},
            {
                "ref_kind": "repo_path",
                "ref": stage_policy_ref(stage),
                "role": "stage_domain_policy",
            },
        ],
        "allowed_action_refs": allowed_action_refs,
        "deliverable_index_ref": _stage_deliverable_index_ref(),
        "outputs": [
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "stage_status"},
            _stage_deliverable_index_ref(),
            {
                "ref_kind": "json_pointer",
                "ref": "/opl_family_persistence_lifecycle_owner_route_adoption",
                "role": "owner_route_projection",
            },
        ],
        "evaluation": evaluation_refs,
        "codex_cli_launch_packet": codex_cli_launch_packet,
        "handoff": {
            "next_owner": "MedAutoScience",
            "next_stage_refs": list(stage.get("next_stage_refs", [])),
            "provides": list(stage.get("ensures", [])),
            "resume_surface_ref": "/domain_entry/study-progress",
            "owner_receipt_ref": "/opl_family_persistence_lifecycle_owner_route_adoption/payload/owner_route",
            "handler_target_ref": "/domain_entry",
        },
        "stage_contract": stage_contract,
        "trust_boundary": trust_boundary,
        "independent_gate_policy": _stage_independent_gate_policy(stage_id),
        "execution_review_separation_required": True,
        "source_refs": source_refs,
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "source_observed_at_ref": "/product_entry_manifest/family_stage_control_plane_descriptor/route_contract_snapshot",
            "refresh_policy": "rebuild_product_entry_manifest_before_opl_discovery",
            "stale_if_source_refs_missing": True,
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "route_contract_owner": "MedAutoScience",
            "stage_knowledge_plane_owner": "MedAutoScience",
            "publication_gate_owner": "MedAutoScience",
            "hypothesis_portfolio_owner": "MedAutoScience",
            "opl_role": "projection_consumer_only",
            "maps_existing_routes_only": True,
            "independent_gate_receipt_required": independent_gate_receipt_required,
            "can_write_domain_truth": False,
            "can_replace_route_contract": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            **hypothesis_portfolio_pack.HYPOTHESIS_PORTFOLIO_AUTHORITY_FLAGS,
        },
    }
    selected_executor = _selected_executor(stage_id)
    if selected_executor is not None:
        stage_descriptor["selected_executor"] = selected_executor
    if mandatory_stage_hook_obligations:
        stage_descriptor["mandatory_stage_hook_obligations"] = mandatory_stage_hook_obligations
    if typed_subpacket_gate:
        stage_descriptor["typed_cognitive_subpacket_gate"] = typed_subpacket_gate
    return stage_descriptor


def _mandatory_stage_hook_obligations(stage_id: str) -> list[dict[str, Any]]:
    from med_autoscience.research_integrity.stage_hooks import (
        TARGET_STAGE_IDS as RESEARCH_INTEGRITY_STAGE_HOOK_TARGET_STAGE_IDS,
        stage_obligation as research_integrity_stage_obligation,
    )

    if stage_id not in RESEARCH_INTEGRITY_STAGE_HOOK_TARGET_STAGE_IDS:
        return []
    return [research_integrity_stage_obligation()]


def _mandatory_stage_hook_pre_gate_checks(stage_id: str) -> list[dict[str, Any]]:
    from med_autoscience.research_integrity.stage_hooks import (
        TARGET_STAGE_IDS as RESEARCH_INTEGRITY_STAGE_HOOK_TARGET_STAGE_IDS,
        stage_launch_required_input as research_integrity_stage_launch_required_input,
    )

    if stage_id not in RESEARCH_INTEGRITY_STAGE_HOOK_TARGET_STAGE_IDS:
        return []
    return [research_integrity_stage_launch_required_input(stage_id=stage_id)]


def _stage_typed_cognitive_subpacket_gate(stage_id: str) -> dict[str, Any]:
    config = STAGE_SUBPACKET_GATE_CONFIGS.get(stage_id)
    if config is None:
        return {}
    return {
        "surface_kind": "mas_typed_cognitive_subpacket_gate",
        "version": "typed-cognitive-subpacket-gate.v1",
        "stage_id": stage_id,
        "contract_source_ref": STAGE_SUBPACKET_GATE_SOURCE_REF,
        "packet_id": config["packet_id"],
        "packet_surface_kind": config["packet_surface_kind"],
        "packet_role": config["packet_role"],
        "packet_required_before_stage_completion": True,
        "launch_surface": "codex_cli_launch_packet.typed_cognitive_subpacket_gate",
        "readback_surface": "stage_contract.typed_cognitive_subpacket_gate",
        "consumed_ref_families": list(config["consumed_ref_families"]),
        "produced_ref_families": list(config["produced_ref_families"]),
        "route_back_conditions": list(config["route_back_conditions"]),
        "typed_blocker_conditions": list(config["typed_blocker_conditions"]),
        "human_gate_conditions": list(config["human_gate_conditions"]),
        "admission_gate": {
            "gate_id": config["admission_gate_id"],
            "gate_owner": "MedAutoScience",
            "gate_decision_outputs": [
                "owner_receipt",
                "route_back",
                "typed_blocker",
                "human_gate",
            ],
            "fail_closed": True,
            "owner_receipt_or_typed_blocker_required": True,
            "candidate_packet_can_close_stage": False,
            "specialist_output_can_claim_ready": False,
            "test_pass_can_claim_ready": False,
            "package_freshness_can_claim_ready": False,
            "ready_claim_requires": [
                "MAS owner receipt accepting the packet",
                "independent gate or reviewer receipt when stage policy requires it",
                "fresh refs for the exact stage work unit",
                "route-back, typed blocker, or human gate when any required ref is missing",
            ],
        },
        "forbidden_ready_claims": [
            "specialist_output_as_ready",
            "test_pass_as_ready",
            "package_freshness_as_ready",
            "provider_completion_as_ready",
            "generated_surface_status_as_ready",
        ],
        "authority_boundary": {
            "packet_is_refs_only_candidate": True,
            "can_write_mas_study_truth": False,
            "can_write_publication_eval_latest": False,
            "can_write_controller_decisions": False,
            "can_mutate_current_package": False,
            "can_sign_owner_receipt": False,
            "can_materialize_typed_blocker": False,
            "can_materialize_human_gate": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
    }


def _stage_expected_receipt_refs(stage_id: str) -> list[dict[str, str]]:
    return [
        {
            "ref_kind": "stage_attempt_receipt_ref",
            "ref": f"stage-attempt-receipt-ref:mas/{stage_id}/{{stage_attempt_id}}",
            "role": "stage_attempt_receipt",
        },
        {
            "ref_kind": "executor_receipt_ref",
            "ref": f"executor-receipt-ref:mas/{stage_id}/codex-cli/{{stage_attempt_id}}",
            "role": "codex_executor_receipt",
        },
        {
            "ref_kind": "boundary_receipt_ref",
            "ref": f"boundary-receipt-ref:mas/{stage_id}/refs-only/{{stage_attempt_id}}",
            "role": "refs_only_boundary_receipt",
        },
        {
            "ref_kind": "owner_receipt_ref",
            "ref": f"owner-receipt-ref:mas/{stage_id}/{{stage_attempt_id}}",
            "role": "mas_owner_receipt",
        },
        {
            "ref_kind": "independent_gate_receipt_ref",
            "ref": f"independent-gate-receipt-ref:mas/{stage_id}/{{stage_attempt_id}}",
            "role": "independent_gate_receipt",
        },
        {
            "ref_kind": "typed_blocker_ref",
            "ref": f"typed-blocker-ref:mas/{stage_id}/{{stage_attempt_id}}",
            "role": "typed_blocker",
        },
    ]


def _stage_receipt_schema_refs() -> list[dict[str, str]]:
    return [
        {
            "ref_kind": "repo_path",
            "ref": "contracts/owner_receipt_contract.json",
            "role": "owner_receipt_or_typed_blocker_schema",
        }
    ]


def _stage_authority_function_refs() -> list[dict[str, str]]:
    return [
        {
            "ref_kind": "repo_path",
            "ref": "runtime/authority_functions/README.md#medical_research_owner_receipt_signer",
            "role": "medical_research_owner_receipt_signer",
        },
        {
            "ref_kind": "repo_path",
            "ref": "runtime/authority_functions/README.md#publication_quality_gate",
            "role": "publication_quality_gate",
        },
    ]


def _stage_l4_entry_gate() -> dict[str, Any]:
    return {
        "entry_level": "L4_structural_baseline",
        "required_gates": list(STANDARD_STAGE_PACK_L4_REQUIRED_GATES),
        "can_claim_l5": False,
        "can_claim_domain_ready": False,
    }


def _stage_l5_entry_gate() -> dict[str, Any]:
    return {
        "entry_level": "L5_production_operating_maturity",
        "evidence_required": list(STANDARD_STAGE_PACK_L5_EVIDENCE_REQUIRED),
        "conformance_pass_counts_as_l5": False,
        "contract_validation_counts_as_l5": False,
        "provider_completion_counts_as_l5": False,
        "app_projection_counts_as_l5": False,
    }


def _stage_tool_refs() -> list[dict[str, str]]:
    return [
        {
            "ref_kind": "repo_path",
            "ref": DOMAIN_TOOL_AFFORDANCE_CATALOG_REF,
            "role": "stage_tool_affordance_catalog",
            "catalog_role": "available_affordance_catalog_not_workflow_script",
        }
    ]


def _stage_tool_affordance_boundary(stage_id: str) -> dict[str, Any]:
    return {
        "surface_kind": "opl_tool_affordance_boundary",
        "version": "tool-affordance-boundary.v1",
        "catalog_role": "available_affordance_catalog_not_workflow_script",
        "policy": (
            "MAS tool refs declare available medical research affordances and safety "
            "boundaries only; they do not prescribe executor order, stage strategy, "
            "stage goal, or forbidden writes."
        ),
        "capability_refs": _policy_refs(
            "capability_boundary",
            [
                "medical_source_literature_and_dataset_context_reading",
                "medical_analysis_manuscript_figure_and_review_workspace_operation",
                "publication_quality_and_integrity_review_support",
                "refs_only_receipt_and_stage_artifact_materialization",
            ],
        ),
        "permission_scope_refs": _policy_refs(
            "permission_scope_boundary",
            [
                "repo_context_read",
                "declared_medical_research_workspace_read",
                "bounded_stage_output_write_when_owner_authorized",
                "receipt_or_typed_blocker_return",
            ],
        ),
        "credential_boundary_refs": _policy_refs(
            "credential_boundary_boundary",
            [
                "no_secret_material_in_stage_pack",
                "executor_must_request_human_gate_for_missing_credentials",
            ],
        ),
        "write_scope_refs": _policy_refs(
            "write_scope_boundary",
            [
                f"medical_research_stage_workspace_refs_only:{stage_id}",
                "publication_artifact_refs_only_until_mas_owner_receipt",
            ],
        ),
        "side_effect_risk_refs": _policy_refs(
            "side_effect_risk_boundary",
            [
                "external_database_or_llm_side_effect_requires_explicit_stage_permission",
                "artifact_or_submission_mutation_requires_mas_owner_receipt",
            ],
        ),
        "forbidden_authority_refs": _policy_refs(
            "forbidden_authority_boundary",
            [
                "publication_readiness_verdict_without_mas_owner_receipt",
                "medical_quality_verdict_without_mas_owner_receipt",
                "clinical_or_research_truth_write_by_opl",
                "artifact_body_mutation_by_opl",
                "memory_body_write_by_opl",
            ],
        ),
        "executor_autonomy": {
            "executor_can_choose_tools": True,
            "executor_can_choose_order_and_parallelism": True,
            "executor_can_skip_tools": True,
            "executor_can_substitute_tools_within_boundary": True,
            "executor_can_request_missing_context_or_human_gate": True,
            "tool_catalog_can_prescribe_tool_sequence": False,
            "tool_catalog_can_define_cognitive_strategy": False,
            "tool_catalog_can_override_stage_goal": False,
            "tool_catalog_can_authorize_forbidden_write": False,
        },
    }


def _stage_independent_gate_policy(stage_id: str) -> dict[str, Any]:
    return {
        "surface_kind": "mas_independent_quality_gate_policy",
        "version": "independent-quality-gate-policy.v1",
        "stage_id": stage_id,
        "gate_owner": "med-autoscience",
        "gate_ref": _stage_quality_gate_ref(stage_id),
        "execution_review_separation_required": True,
        "same_attempt_self_review_can_close_quality_gate": False,
        "mechanical_completion_can_close_stage": False,
        "provider_completion_can_claim_domain_ready": False,
        "generated_surface_readiness_can_claim_quality_or_export": False,
        "owner_receipt_or_typed_blocker_required": True,
        "human_gate_allowed": True,
        "route_back_allowed": True,
    }


def _stage_quality_gate_ref(stage_id: str) -> str:
    if stage_id in {"manuscript_authoring", "review_and_quality_gate"}:
        return "agent/quality_gates/ai_reviewer_auditor_gate.md"
    return "agent/quality_gates/artifact_source_authority_gate.md"


def _policy_refs(role: str, refs: list[str]) -> list[dict[str, str]]:
    return [{"ref_kind": "policy_ref", "ref": ref, "role": role} for ref in refs]


def _selected_executor(stage_id: str) -> dict[str, Any] | None:
    selected = {
        "executor_kind": "codex_cli",
        "owner_callable_adapter": True,
        "default_executor": True,
        "executor_binding_ref": "default_codex_cli",
        "binding_policy": "default_first_class_executor_for_ai_first_stage_execution",
        "required_capabilities": [
            "repo_context_reading",
            "domain_skill_invocation",
            "receipt_or_typed_blocker_return",
            "no_forbidden_write_guard",
        ],
    }
    if stage_id != ORDINARY_DEFAULT_STAGE_ID:
        selected["required_capabilities"].insert(2, "tool_affordance_boundary_compliance")
        selected["lane_kind"] = "variant"
    return selected


def _stage_progress_sprint_contract(
    stage: Mapping[str, Any],
    *,
    descriptor: Mapping[str, Any],
) -> dict[str, Any] | None:
    sprint_contract = _mapping(descriptor.get("late_stage_progress_sprint_contract"))
    covered_routes = set(sprint_contract.get("covered_routes") or [])
    domain_stage_refs = set(stage.get("domain_stage_refs") or [])
    if not (covered_routes & domain_stage_refs):
        return None
    return {
        "sprint_id": sprint_contract["sprint_id"],
        "contract_ref": f"{STAGE_ROUTE_CONTRACT_REF}#/{PROGRESS_FIRST_SPRINT_CONTRACT_FIELD}",
        "covered_work_units": list(sprint_contract["covered_work_units"]),
        "control_plane_outputs": list(sprint_contract["control_plane_outputs"]),
        "forbidden_control_plane_outputs": list(sprint_contract["forbidden_control_plane_outputs"]),
        "admission_order": list(sprint_contract["admission_order"]),
        "gate_before_delta_policy": sprint_contract["gate_before_delta_policy"],
        "authority_boundary": list(sprint_contract["authority_boundary"]),
    }


def _stage_cohort_loop_refs(stage: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    stage_id = str(stage["stage_id"])
    return {
        "source_scope_refs": [
            {
                "ref_kind": "route_stage_refs",
                "ref": list(stage["domain_stage_refs"]),
                "role": "mas_route_stage_source_scope",
            },
            {
                "ref_kind": "json_pointer",
                "ref": f"/product_entry_manifest/family_stage_control_plane/stages/{stage_id}/source_refs",
                "role": "stage_source_ref_projection",
            },
        ],
        "cohort_query_refs": [
            {
                "ref_kind": "json_pointer",
                "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/route_contract_snapshot",
                "role": "auditable_stage_cohort_query",
            },
        ],
        "trigger_refs": [
            {
                "ref_kind": "queue_ref",
                "ref": f"opl://family-stage-queue/med-autoscience/{stage_id}",
                "role": "opl_provider_stage_launch_trigger",
            },
            {
                "ref_kind": "action_ref",
                "ref": list(stage["allowed_action_refs"]),
                "role": "mas_guarded_action_trigger_candidates",
            },
        ],
        "monitor_refs": [
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "stage_progress_monitor"},
            {"ref_kind": "json_pointer", "ref": "/progress_projection", "role": "runtime_status_monitor"},
        ],
        "dashboard_metric_refs": [
            {
                "ref_kind": "json_pointer",
                "ref": f"/product_entry_manifest/family_stage_control_plane/stages/{stage_id}/freshness",
                "role": "operator_stage_freshness_metric",
            },
        ],
    }


def _required_runtime_event_refs(stage: Mapping[str, Any]) -> list[str]:
    stage_id = str(stage.get("stage_id") or "")
    refs = [str(ref) for ref in stage.get("runtime_event_refs") or [] if str(ref).strip()]
    if not refs:
        raise ValueError(f"runtime guard stage missing runtime_event_refs: {stage_id}")
    return refs


def stage_deliverable_index_projection(stage_surface: Mapping[str, Any]) -> dict[str, Any]:
    index = _mapping(stage_surface.get("stage_deliverable_index"))
    return {
        "surface_kind": index.get("surface_kind"),
        "version": index.get("version"),
        "role": index.get("role"),
        "stage_count": index.get("stage_count"),
        "locator_ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
        "stage_refs": list(index.get("stage_refs") or []),
        "human_review_page_refs": list(index.get("human_review_page_refs") or []),
        "source_refs": list(index.get("source_refs") or []),
        "human_review_policy": _mapping(index.get("human_review_policy")),
        "review_page_policy": _mapping(index.get("review_page_policy")),
        "authority_boundary": _mapping(index.get("authority_boundary")),
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "auto_advance_boundary": {
            "default_blocks_auto_advance": False,
            "blocking_only_when": "mas_human_gate_boundary_triggered",
            "opl_can_block_auto_advance": False,
            "opl_can_mark_publication_ready": False,
        },
    }


def _stage_deliverable_index_ref() -> dict[str, Any]:
    return {
        "ref_kind": "json_pointer",
        "ref": "/product_entry_manifest/family_stage_control_plane_descriptor/stage_deliverable_index",
        "role": "stage_deliverable_index",
        "opl_projection_boundary": "read_only_locator_no_truth_write",
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "human_review_blocks_auto_advance_by_default": False,
        "blocking_only_when": "mas_human_gate_boundary_triggered",
    }


def _stage_goal(stage: Mapping[str, Any], *, descriptor: Mapping[str, Any]) -> str:
    route_contracts = _mapping(load_stage_route_contract_payload().get("route_contracts"))
    route_goals = [
        str(_mapping(route_contracts.get(route_id)).get("goal") or "").strip()
        for route_id in stage["domain_stage_refs"]
    ]
    route_goals = [goal for goal in route_goals if goal]
    if route_goals:
        return " / ".join(route_goals[:2])
    route_count = _mapping(descriptor.get("route_contract_snapshot")).get("route_count")
    return f"Expose MAS route snapshot for {stage['title']} without changing the {route_count} MAS routes."


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
