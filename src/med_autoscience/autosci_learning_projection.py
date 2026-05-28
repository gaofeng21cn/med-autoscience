from __future__ import annotations

from typing import Any


SURFACE_KIND = "mas_autosci_learning_projection"
SOURCE_REPOSITORY = "https://github.com/skyllwt/AutoSci"
SOURCE_HEAD = "d89cc72a884a2d091b6fac5719f30b4c64d2c6bd"
SOURCE_PROJECT = "AutoSci/OmegaWiki"
CONTRACT_REF = "med_autoscience.autosci_learning_projection.build_autosci_learning_projection"
DOC_REF = "docs/references/mainline/autosci_learning_intake.md"


def build_autosci_learning_projection() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "version": "mas-autosci-learning-projection.v1",
        "status": "pattern_intake_projected",
        "source_snapshot": {
            "source_project": SOURCE_PROJECT,
            "repository": SOURCE_REPOSITORY,
            "observed_head": SOURCE_HEAD,
            "intake_doc_ref": DOC_REF,
            "dependency_introduced": False,
        },
        "absorbed_patterns": [
            {
                "pattern_id": "typed_research_knowledge_graph",
                "classification": "adopt_contract",
                "source_pattern": "runtime_schema_entities_edges_xref_conventions",
                "mas_mapping": "source_evidence_review_graph_refs",
                "owner_surface": "source_truth_and_knowledge_graph",
                "target_surfaces": [
                    "stage_knowledge_packet",
                    "evidence_ledger",
                    "review_ledger",
                    "source_readiness_refs",
                ],
                "source_refs": [
                    "runtime/schema/entities.yaml",
                    "runtime/schema/edges.yaml",
                    "runtime/schema/xref.yaml",
                    "runtime/schema/conventions.yaml",
                ],
                "authority": "projection_only",
            },
            {
                "pattern_id": "proposal_action_source_discovery_split",
                "classification": "adopt_contract",
                "source_pattern": "discover_and_daily_arxiv_recommendation_guard",
                "mas_mapping": "source_candidate_proposal_then_authorized_ingest",
                "owner_surface": "source_truth",
                "target_surfaces": [
                    "life_science_source_discovery_pack",
                    "source_adapter_output",
                    "source_readiness_typed_blocker",
                ],
                "source_refs": [
                    ".claude/skills/discover/SKILL.md",
                    ".claude/skills/daily-arxiv/SKILL.md",
                    ".claude/skills/daily-arxiv/references/recommendation-and-ingest-policy.md",
                ],
                "authority": "proposal_only_until_mas_owner_authorization",
            },
            {
                "pattern_id": "negative_research_memory",
                "classification": "adopt_contract",
                "source_pattern": "failed_ideas_failure_reason_anti_repetition_memory",
                "mas_mapping": "typed_negative_route_memory_refs",
                "owner_surface": "experiment_lifecycle_and_route_memory",
                "target_surfaces": [
                    "publication_route_memory_pack",
                    "stage_memory_closeout_packet",
                    "memory_write_router_receipt",
                ],
                "source_refs": [
                    ".claude/skills/ideate/SKILL.md",
                    "runtime/schema/entities.yaml#ideas",
                ],
                "authority": "memory_proposal_only_until_mas_router_receipt",
            },
            {
                "pattern_id": "experiment_deploy_collect_eval_lifecycle",
                "classification": "adopt_template",
                "source_pattern": "idea_pilot_formal_experiment_deploy_collect_eval",
                "mas_mapping": "analysis_campaign_attempt_receipts_and_eval_refs",
                "owner_surface": "experiment_lifecycle",
                "target_surfaces": [
                    "statistical_analysis_pack",
                    "controller_decisions/latest.json",
                    "stage_attempt_receipt",
                    "review_ledger",
                ],
                "source_refs": [
                    ".claude/skills/exp-design/SKILL.md",
                    ".claude/skills/exp-run/SKILL.md",
                    ".claude/skills/exp-eval/SKILL.md",
                ],
                "authority": "receipt_refs_only",
            },
            {
                "pattern_id": "independent_reviewer_verdict_mapping",
                "classification": "adopt_contract",
                "source_pattern": "review_outputs_verdict_weakness_action_mapping",
                "mas_mapping": "reviewer_os_verdict_to_source_artifact_refs",
                "owner_surface": "reviewer_os",
                "target_surfaces": [
                    "AI reviewer workflow",
                    "review_ledger",
                    "publication_eval/latest.json",
                ],
                "source_refs": [
                    ".claude/skills/review/SKILL.md",
                    ".claude/skills/shared-references/cross-model-review.md",
                ],
                "authority": "independent_reviewer_record_required",
            },
            {
                "pattern_id": "source_dag_render_qa_artifact_projection",
                "classification": "adopt_template",
                "source_pattern": "poster_source_dag_figure_manifest_render_qa",
                "mas_mapping": "paper_presentation_projection_render_qa_refs",
                "owner_surface": "publication_artifact",
                "target_surfaces": [
                    "paper_presentation_pack",
                    "stage_deliverable_index",
                    "artifact_freshness_pack",
                ],
                "source_refs": [
                    ".claude/skills/poster/SKILL.md",
                    "tools/wiki2dag.py",
                    "tools/poster.py",
                ],
                "authority": "artifact_projection_only",
            },
        ],
        "knowledge_graph_contract": {
            "surface_kind": "mas_research_knowledge_graph_contract",
            "absorbed_as": "typed_refs_and_edges_not_wiki_body_import",
            "entity_shape_policy": {
                "copy_autosci_taxonomy": False,
                "mas_entity_authority_surfaces": [
                    "study_charter",
                    "source_readiness_refs",
                    "evidence_ledger",
                    "review_ledger",
                    "publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "artifact_authority_refs",
                ],
            },
            "edge_policy": {
                "semantic_edges_separate_from_bibliographic_citations": True,
                "edge_requires_evidence_or_provenance_ref": True,
                "reverse_ref_or_terminal_exception_required": True,
                "confidence_without_source_ref_forbidden": True,
            },
            "write_policy": {
                "user_or_external_raw_inputs_read_only": True,
                "derived_graph_tool_or_owner_function_only": True,
                "runtime_log_append_only": True,
                "partial_authoritative_ingest_forbidden": True,
            },
        },
        "source_discovery_contract": {
            "surface_kind": "mas_source_discovery_proposal_action_split",
            "proposal_surface": "source_candidate_shortlist_ref",
            "action_surface": "mas_owner_authorized_ingest_or_source_repair_route",
            "candidate_may_write_mas_truth": False,
            "recommendation_may_authorize_source_readiness": False,
            "auto_ingest_requires_explicit_mode_and_high_confidence": True,
            "degraded_provider_signal_requires_caveat_or_typed_blocker": True,
        },
        "experiment_lifecycle_contract": {
            "surface_kind": "mas_experiment_lifecycle_contract",
            "idea_to_experiment_statuses": [
                "proposed",
                "pilot_designed",
                "pilot_running",
                "pilot_evaluated",
                "formal_experiment_designed",
                "formal_experiment_running",
                "evaluated",
                "failed_or_abandoned",
            ],
            "required_receipt_refs": [
                "design_ref",
                "deploy_receipt_ref",
                "monitor_refs",
                "collect_receipt_ref",
                "evaluation_verdict_ref",
            ],
            "failed_or_rejected_requires_reason": True,
            "negative_memory_writeback_requires_router_receipt": True,
        },
        "reviewer_os_contract": {
            "surface_kind": "mas_reviewer_os_verdict_mapping_contract",
            "separate_invocation_required": True,
            "self_review_closes_quality_gate": False,
            "required_output_fields": [
                "verdict",
                "score_or_confidence",
                "weaknesses",
                "action_items",
                "source_ref_mapping",
                "artifact_ref_mapping",
                "evidence_ref_mapping",
            ],
            "disagreement_policy": "conservative_route_back_or_typed_blocker",
        },
        "artifact_projection_contract": {
            "surface_kind": "mas_artifact_source_dag_render_qa_contract",
            "required_refs": [
                "source_dag_ref",
                "figure_asset_manifest_ref",
                "selected_asset_refs",
                "render_output_ref",
                "overflow_or_visual_qa_ref",
                "reviewer_critique_ref_or_not_applicable_reason",
            ],
            "projection_may_authorize_artifact_mutation": False,
            "render_success_is_publication_ready": False,
        },
        "watch_only_patterns": [
            {
                "pattern_id": "prompt_level_writer_policy",
                "reason": "upstream policy is descriptive and not a fail-closed runtime gate",
            },
            {
                "pattern_id": "paper_copilot_cs_venue_ranking",
                "reason": "citation and venue ranking signals require medical source-readiness adaptation",
            },
            {
                "pattern_id": "github_actions_daily_scheduler",
                "reason": "useful notification scaffold but not MAS generic hosted runtime owner",
            },
        ],
        "rejected_patterns": [
            "external_claude_slash_skills_as_runtime",
            "ssh_rsync_screen_remote_gpu_runner",
            "prompt_only_permission_as_authority",
            "partial_authoritative_ingest_success",
            "autosci_entity_taxonomy_as_mas_taxonomy",
            "self_review_as_independent_quality_gate",
        ],
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "quality_verdict_owner": "MedAutoScience",
            "source_readiness_owner": "MedAutoScience",
            "publication_artifact_authority_owner": "MedAutoScience",
            "generic_runtime_owner": "one-person-lab",
            "source_project_role": "external_pattern_source_only",
            "can_write_domain_truth": False,
            "can_write_evidence_ledger": False,
            "can_write_review_ledger": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_authorize_source_readiness": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_authorize_artifact_authority": False,
        },
    }


__all__ = [
    "CONTRACT_REF",
    "DOC_REF",
    "SOURCE_HEAD",
    "SOURCE_PROJECT",
    "SOURCE_REPOSITORY",
    "SURFACE_KIND",
    "build_autosci_learning_projection",
]
