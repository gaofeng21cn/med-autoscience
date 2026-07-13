from __future__ import annotations

from typing import Any


SURFACE_KIND = "mas_evo_scientist_progress_accelerator_projection"
SOURCE_REPOSITORY = "https://github.com/EvoScientist/EvoScientist"
SKILLS_REPOSITORY = "https://github.com/EvoScientist/EvoSkills"
SOURCE_RELEASE = "v0.1.4"
SOURCE_RELEASE_PUBLISHED_AT = "2026-06-06T23:57:20Z"
SKILLS_RELEASE = "v1.0.0"
CONTRACT_REF = "contracts/evo_scientist_progress_accelerator.json"
PROJECTION_BUILDER_REF = (
    "med_autoscience.evo_scientist_learning_projection."
    "build_evo_scientist_learning_projection"
)
DOC_REF = "docs/runtime/designs/evo_scientist_progress_first_intake.md"
RESOLVER_ABI_REF = (
    "one-person-lab:contracts/opl-framework/capability-registry-resolver.schema.json"
)

ABSORBED_PATTERN_IDS = (
    "auxiliary_background_model",
    "fire_and_forget_observation_memory",
    "conditional_tool_selection",
    "skill_routing_eval",
    "ive_failed_path_memory_taxonomy",
    "attempt_budget_stop_loss",
)
WATCH_ONLY_PATTERN_IDS = (
    "idea_tournament_as_default_gate",
    "full_research_lifecycle_pipeline_as_mas_default",
)
REJECTED_PATTERN_IDS = (
    "external_deepagents_runtime_as_mas_runtime",
    "foreign_langgraph_dev_worker_as_opl_substrate",
    "evo_memory_body_as_mas_truth",
    "tool_selector_as_hard_gate",
    "self_review_as_independent_quality_gate",
    "mandatory_full_literature_grounding_before_each_delta",
    "full_evoskills_pipeline_as_live_preflight",
)


def _false_authority() -> dict[str, bool]:
    return {
        "can_select_next_action": False,
        "can_generate_default_next_action": False,
        "can_generate_current_owner": False,
        "can_generate_owner_receipt": False,
        "can_generate_typed_blocker": False,
        "can_generate_paper_progress": False,
        "can_authorize_provider_attempt": False,
        "can_write_domain_truth": False,
        "can_write_memory_body": False,
        "can_write_artifact_body": False,
        "can_write_evidence_ledger": False,
        "can_write_review_ledger": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_authorize_current_owner_action": False,
        "can_authorize_source_readiness": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_quality_gate": False,
        "can_close_stage": False,
    }


def build_evo_scientist_learning_projection() -> dict[str, Any]:
    false_authority = _false_authority()
    return {
        "surface_kind": SURFACE_KIND,
        "version": "mas-evo-scientist-progress-accelerator.v2",
        "status": "declarative_external_pattern_projection",
        "contract_ref": CONTRACT_REF,
        "progress_accelerator_contract_ref": CONTRACT_REF,
        "projection_builder_ref": PROJECTION_BUILDER_REF,
        "source_snapshot": {
            "source_project": "EvoScientist/EvoScientist + EvoScientist/EvoSkills",
            "repository": SOURCE_REPOSITORY,
            "skills_repository": SKILLS_REPOSITORY,
            "observed_release": SOURCE_RELEASE,
            "observed_release_published_at": SOURCE_RELEASE_PUBLISHED_AT,
            "skills_release": SKILLS_RELEASE,
            "intake_doc_ref": DOC_REF,
            "dependency_introduced": False,
        },
        "absorbed_pattern_ids": list(ABSORBED_PATTERN_IDS),
        "watch_only_pattern_ids": list(WATCH_ONLY_PATTERN_IDS),
        "rejected_pattern_ids": list(REJECTED_PATTERN_IDS),
        "domain_delta": {
            "capability_id": "evo_scientist_progress_patterns",
            "capability_ref": "scientific-capability:evo_scientist_progress_patterns",
            "invocation_kind": "descriptor_only_current_owner_input_refs",
            "binding_kind": "optional",
            "source_family": "evo",
            "resolver_owner": "one-person-lab",
            "resolver_abi_ref": RESOLVER_ABI_REF,
            "mas_role": "declare_pattern_refs_and_accept_or_reject_memory_candidates",
            "memory_accept_reject_owner": "MedAutoScience",
            "runtime_writer": None,
            "local_persistence": "absent",
            "body_included": False,
        },
        "ordinary_progress_boundary": {
            "ordinary_progress_spine": [
                "current_owner_delta",
                "concrete_delta",
                "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
                "next_current_owner_delta",
            ],
            "descriptor_only": True,
            "refs_only": True,
            "critical_path_waits_for_pattern_ref": False,
            "missing_pattern_ref_blocks_dispatch": False,
            **false_authority,
        },
        "authority_boundary": {
            "source_project_role": "external_pattern_source_only",
            "generic_runtime_owner": "one-person-lab",
            "domain_truth_owner": "MedAutoScience",
            "quality_verdict_owner": "MedAutoScience",
            "source_readiness_owner": "MedAutoScience",
            "publication_artifact_authority_owner": "MedAutoScience",
            "memory_accept_reject_owner": "MedAutoScience",
            "refs_only": True,
            "body_included": False,
            **false_authority,
        },
    }


__all__ = [
    "ABSORBED_PATTERN_IDS",
    "CONTRACT_REF",
    "DOC_REF",
    "PROJECTION_BUILDER_REF",
    "REJECTED_PATTERN_IDS",
    "RESOLVER_ABI_REF",
    "SKILLS_RELEASE",
    "SKILLS_REPOSITORY",
    "SOURCE_RELEASE",
    "SOURCE_RELEASE_PUBLISHED_AT",
    "SOURCE_REPOSITORY",
    "SURFACE_KIND",
    "WATCH_ONLY_PATTERN_IDS",
    "build_evo_scientist_learning_projection",
]
