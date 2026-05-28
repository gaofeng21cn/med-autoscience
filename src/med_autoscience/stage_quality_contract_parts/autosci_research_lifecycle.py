from __future__ import annotations


AUTOSCI_OBSERVED_HEAD = "d89cc72a884a2d091b6fac5719f30b4c64d2c6bd"
AUTOSCI_RESEARCH_LIFECYCLE_PACKS = frozenset(
    {
        "ai_native_expert_judgment_pack",
        "life_science_source_discovery_pack",
        "route_memory_pack",
        "statistical_analysis_pack",
        "paper_presentation_pack",
    }
)


def build_autosci_clean_room_absorption() -> dict[str, object]:
    return {
        "source_project": "AutoSci/OmegaWiki",
        "source_repository": "https://github.com/skyllwt/AutoSci",
        "observed_head": AUTOSCI_OBSERVED_HEAD,
        "absorbed_as": "mas_native_contract_pattern",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "default_skill_source": False,
        "copy_external_runtime_or_slash_commands": False,
        "publication_authority": False,
        "artifact_authority": False,
    }


def build_autosci_pack_contracts(pack_id: str) -> list[dict[str, object]]:
    return list(_AUTOSCI_PACK_CONTRACTS.get(pack_id, ()))


_AUTOSCI_PACK_CONTRACTS: dict[str, tuple[dict[str, object], ...]] = {
    "ai_native_expert_judgment_pack": (
        {
            "contract_id": "independent_reviewer_verdict_mapping_contract",
            "learned_from": "autosci-review",
            "absorbed_as": "reviewer_verdict_to_source_artifact_refs_floor",
            "required_fields": [
                "reviewer_record_ref",
                "separate_invocation_receipt_ref",
                "verdict",
                "score_or_confidence",
                "weaknesses",
                "action_items",
                "source_ref_mapping",
                "artifact_ref_mapping",
                "evidence_ref_mapping",
                "disagreement_or_conservative_route_ref",
            ],
            "typed_blocker_if_missing": "independent_reviewer_verdict_mapping_blocker",
            "self_review_closes_quality_gate": False,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "life_science_source_discovery_pack": (
        {
            "contract_id": "proposal_action_source_discovery_contract",
            "learned_from": "autosci-discover-daily-arxiv",
            "absorbed_as": "source_candidate_proposal_then_owner_action_floor",
            "required_fields": [
                "candidate_record_ref",
                "seed_mode_or_query_ref",
                "dedup_basis_ref",
                "recommendation_rationale_ref",
                "source_provider_preflight_ref",
                "decision_artifact_ref",
                "explicit_ingest_authorization_ref_or_not_applicable_reason",
                "source_adapter_rejection_log_ref",
                "degraded_signal_caveat_or_typed_blocker_ref",
            ],
            "typed_blocker_if_missing": "source_discovery_proposal_action_blocker",
            "recommendation_may_write_mas_truth": False,
            "may_authorize_source_readiness": False,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
        {
            "contract_id": "typed_knowledge_graph_edge_contract",
            "learned_from": "autosci-runtime-schema",
            "absorbed_as": "semantic_edge_citation_provenance_separation_floor",
            "required_fields": [
                "entity_ref",
                "entity_kind",
                "semantic_edge_ref",
                "edge_workflow",
                "edge_evidence_ref",
                "confidence_or_support_basis",
                "citation_ref_if_bibliographic",
                "reverse_ref_or_terminal_exception",
                "provenance_ref",
            ],
            "typed_blocker_if_missing": "research_graph_ref_consistency_blocker",
            "semantic_edges_separate_from_citations": True,
            "partial_authoritative_ingest_forbidden": True,
            "may_authorize_source_readiness": False,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "route_memory_pack": (
        {
            "contract_id": "negative_research_memory_contract",
            "learned_from": "autosci-ideate",
            "absorbed_as": "failed_hypothesis_route_anti_repetition_floor",
            "required_fields": [
                "failed_or_rejected_item_ref",
                "failure_reason",
                "source_or_review_refs",
                "active_duplicate_check_ref",
                "do_not_repeat_scope",
                "memory_writeback_proposal_ref",
                "memory_write_router_receipt_ref",
            ],
            "typed_blocker_if_missing": "negative_memory_or_duplicate_route_blocker",
            "failed_or_rejected_requires_reason": True,
            "memory_body_write_requires_mas_router_receipt": True,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "statistical_analysis_pack": (
        {
            "contract_id": "experiment_lifecycle_receipt_contract",
            "learned_from": "autosci-exp-design-run-eval",
            "absorbed_as": "idea_pilot_deploy_collect_eval_receipt_floor",
            "required_fields": [
                "idea_or_hypothesis_ref",
                "pilot_design_ref_or_not_applicable_reason",
                "formal_design_ref",
                "deploy_receipt_ref",
                "monitor_refs",
                "collect_receipt_ref",
                "evaluation_verdict_ref",
                "failed_or_inconclusive_reason_ref",
                "controller_next_route_ref",
            ],
            "typed_blocker_if_missing": "experiment_lifecycle_receipt_blocker",
            "deploy_success_is_not_analysis_success": True,
            "review_verdict_required_before_status_promotion": True,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "paper_presentation_pack": (
        {
            "contract_id": "source_dag_render_qa_artifact_contract",
            "learned_from": "autosci-poster",
            "absorbed_as": "source_dag_figure_manifest_render_qa_floor",
            "required_fields": [
                "source_dag_ref",
                "figure_asset_manifest_ref",
                "selected_asset_refs",
                "render_output_ref",
                "overflow_or_visual_qa_ref",
                "reviewer_critique_ref_or_not_applicable_reason",
                "artifact_authority_receipt_ref_or_typed_blocker",
            ],
            "typed_blocker_if_missing": "presentation_render_qa_or_artifact_authority_blocker",
            "render_success_is_publication_ready": False,
            "projection_may_authorize_artifact_mutation": False,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
}


__all__ = [
    "AUTOSCI_OBSERVED_HEAD",
    "AUTOSCI_RESEARCH_LIFECYCLE_PACKS",
    "build_autosci_clean_room_absorption",
    "build_autosci_pack_contracts",
]
