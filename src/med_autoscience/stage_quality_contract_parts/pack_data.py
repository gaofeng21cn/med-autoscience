from __future__ import annotations


def _ref(ref_kind: str, ref: str, role: str) -> dict[str, str]:
    return {"ref_kind": ref_kind, "ref": ref, "role": role}


_PACK_TITLES = {
    "ai_native_expert_judgment_pack": "AI-native expert judgment pack",
    "medical_claim_evidence_pack": "Medical claim evidence pack",
    "statistical_analysis_pack": "Statistical analysis pack",
    "reporting_guideline_pack": "Reporting guideline pack",
    "manuscript_argument_pack": "Manuscript argument pack",
    "statistical_reporting_pack": "Statistical reporting pack",
    "display_to_claim_pack": "Display to claim pack",
    "journal_response_pack": "Journal response pack",
    "data_availability_fair_pack": "Data availability and FAIR pack",
    "citation_integrity_pack": "Citation integrity pack",
    "figure_evidence_contract_pack": "Figure evidence contract pack",
    "paper_reader_grounding_pack": "Paper reader grounding pack",
    "paper_presentation_pack": "Paper presentation pack",
    "life_science_source_discovery_pack": "Life science source discovery pack",
    "route_memory_pack": "Route memory pack",
    "stop_loss_pack": "Stop-loss pack",
    "external_pattern_intake_pack": "External pattern intake pack",
    "artifact_freshness_pack": "Artifact freshness pack",
    "human_gate_pack": "Human gate pack",
}

_PACK_OWNER_REFS = {
    "ai_native_expert_judgment_pack": [
        _ref("surface_kind", "AI reviewer workflow", "expert_judgment_owner"),
        _ref("surface_kind", "stage_executor", "stage_native_reasoning_owner"),
    ],
    "medical_claim_evidence_pack": [
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "evidence_ledger"),
        _ref("workspace_locator", "paper/review/review_ledger.json", "review_ledger"),
        _ref("surface_kind", "AI reviewer workflow", "reviewer_owner"),
    ],
    "statistical_analysis_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "controller_decision"),
        _ref("surface_kind", "analysis_contract", "analysis_owner"),
    ],
    "reporting_guideline_pack": [
        _ref("human_doc", "docs/policies/quality/medical_manuscript_first_draft_quality.md", "quality_os_policy"),
        _ref("surface_kind", "publication_profile", "publication_profile_owner"),
    ],
    "manuscript_argument_pack": [
        _ref("surface_kind", "AI reviewer workflow", "manuscript_argument_owner"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_source"),
        _ref("workspace_locator", "artifacts/publication_eval/latest.json", "medical_prose_review_source"),
    ],
    "statistical_reporting_pack": [
        _ref("surface_kind", "analysis_contract", "analysis_owner"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "statistical_claim_trace"),
        _ref("surface_kind", "publication_profile", "journal_statistical_reporting_profile"),
    ],
    "display_to_claim_pack": [
        _ref("surface_kind", "display_contract", "display_owner"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_map"),
    ],
    "journal_response_pack": [
        _ref("workspace_locator", "paper/review/review_ledger.json", "review_ledger"),
        _ref("surface_kind", "revision_rebuttal_loop", "response_projection_owner"),
        _ref("workspace_locator", "artifacts/publication_eval/latest.json", "ai_reviewer_source"),
    ],
    "data_availability_fair_pack": [
        _ref("surface_kind", "data_assets_readiness", "data_asset_owner"),
        _ref("workspace_locator", "memory/portfolio/data_assets", "data_asset_registry"),
        _ref("workspace_locator", "paper/submission_minimal", "submission_statement_source"),
    ],
    "citation_integrity_pack": [
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_source"),
        _ref("surface_kind", "citation_integrity_projection", "citation_review_owner"),
    ],
    "figure_evidence_contract_pack": [
        _ref("surface_kind", "figure_renderer_contract", "renderer_contract_owner"),
        _ref("surface_kind", "publication_display_contract", "display_contract_owner"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "source_data_trace"),
    ],
    "paper_reader_grounding_pack": [
        _ref("surface_kind", "stage_deliverable_review_page", "source_grounded_reader_projection"),
        _ref("surface_kind", "stage_deliverable_index", "stage_review_index_owner"),
    ],
    "paper_presentation_pack": [
        _ref("surface_kind", "stage_deliverable_index", "presentation_source_index"),
        _ref("surface_kind", "paper_presentation_projection", "human_facing_projection_owner"),
    ],
    "life_science_source_discovery_pack": [
        _ref("surface_kind", "literature_intelligence_os", "literature_and_public_study_discovery"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "evidence_ref_owner"),
        _ref("surface_kind", "source_readiness_verdict", "source_readiness_stage_gate_owner"),
    ],
    "route_memory_pack": [
        _ref("surface_kind", "stage_knowledge_packet", "route_memory_retrieval"),
        _ref("surface_kind", "memory_write_router_receipt", "route_memory_router"),
    ],
    "stop_loss_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "controller_decision"),
        _ref("surface_kind", "stop_loss_memo", "decision_owner"),
    ],
    "external_pattern_intake_pack": [
        _ref("surface_kind", "stage_quality_pack_contract", "mas_native_contract_owner"),
        _ref("surface_kind", "AI reviewer workflow", "reviewer_refusal_rehearsal_owner"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "fresh_evidence_log_ref_owner"),
    ],
    "artifact_freshness_pack": [
        _ref("workspace_locator", "manuscript/current_package", "current_package"),
        _ref("workspace_locator", "artifacts/delivery_manifest/latest.json", "delivery_manifest"),
    ],
    "human_gate_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "controller_decision"),
        _ref("surface_kind", "OPL signal transport receipt", "signal_transport"),
    ],
}

_PACK_REQUIRED_REFS = {
    "ai_native_expert_judgment_pack": [
        _ref("surface_kind", "AI reviewer workflow", "open_expert_review_required"),
        _ref("surface_kind", "stage_quality_pack_contract", "quality_floor_not_ceiling"),
    ],
    "medical_claim_evidence_pack": [
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "required_evidence"),
        _ref("workspace_locator", "paper/review/review_ledger.json", "required_review"),
        _ref("workspace_locator", "artifacts/publication_eval/latest.json", "quality_closure_input"),
    ],
    "statistical_analysis_pack": [
        _ref("surface_kind", "analysis_contract", "required_rubric"),
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "decision_context"),
    ],
    "reporting_guideline_pack": [
        _ref("human_doc", "docs/policies/quality/medical_manuscript_first_draft_quality.md", "required_rubric"),
        _ref("surface_kind", "publication_profile", "guideline_profile"),
    ],
    "manuscript_argument_pack": [
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_boundary_refs"),
        _ref("surface_kind", "AI reviewer workflow", "argument_and_prose_review_required"),
        _ref("workspace_locator", "artifacts/publication_eval/latest.json", "medical_prose_quality_trace"),
    ],
    "statistical_reporting_pack": [
        _ref("surface_kind", "analysis_contract", "statistical_methods_and_assumptions"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "reported_estimate_and_denominator_refs"),
        _ref("surface_kind", "publication_profile", "journal_statistical_reporting_requirements"),
    ],
    "display_to_claim_pack": [
        _ref("surface_kind", "display_contract", "required_rubric"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_map"),
    ],
    "journal_response_pack": [
        _ref("surface_kind", "revision_rebuttal_loop", "response_read_model"),
        _ref("workspace_locator", "paper/review/review_ledger.json", "reviewer_comment_source"),
        _ref("workspace_locator", "artifacts/publication_eval/latest.json", "ai_reviewer_trace"),
    ],
    "data_availability_fair_pack": [
        _ref("surface_kind", "data_assets_readiness", "dataset_location_mapping"),
        _ref("workspace_locator", "memory/portfolio/data_assets", "repository_identifier_source"),
        _ref("workspace_locator", "paper/submission_minimal", "data_availability_statement"),
    ],
    "citation_integrity_pack": [
        _ref("surface_kind", "citation_integrity_projection", "claim_segment_review"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_refs"),
    ],
    "figure_evidence_contract_pack": [
        _ref("surface_kind", "figure_renderer_contract", "figure_contract_before_plotting"),
        _ref("surface_kind", "publication_display_contract", "display_to_claim_trace"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "source_data_refs"),
    ],
    "paper_reader_grounding_pack": [
        _ref("surface_kind", "stage_deliverable_review_page", "source_map_refs"),
        _ref("surface_kind", "stage_deliverable_index", "figure_near_claim_refs"),
    ],
    "paper_presentation_pack": [
        _ref("surface_kind", "paper_presentation_projection", "evidence_spine_projection"),
        _ref("surface_kind", "stage_deliverable_index", "presentation_source_refs"),
    ],
    "life_science_source_discovery_pack": [
        _ref("surface_kind", "stage_knowledge_packet", "entity_normalization_and_query_scope_refs"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "source_discovery_evidence_refs"),
        _ref("surface_kind", "typed_blocker", "missing_or_stale_source_discovery_blocker"),
    ],
    "route_memory_pack": [
        _ref("surface_kind", "stage_knowledge_packet", "required_memory_refs"),
        _ref("surface_kind", "stage_recall_index", "recall_projection"),
    ],
    "stop_loss_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "required_decision_refs"),
        _ref("surface_kind", "runtime_escalation_record", "escalation_context"),
    ],
    "external_pattern_intake_pack": [
        _ref("surface_kind", "stage_quality_pack_contract", "clean_room_pattern_descriptor"),
        _ref("surface_kind", "typed_blocker", "route_required_ref_blocker_only_for_current_delta"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "fresh_evidence_log_ref_when_current_delta_requires_it"),
    ],
    "artifact_freshness_pack": [
        _ref("workspace_locator", "artifacts/delivery_manifest/latest.json", "freshness_proof"),
        _ref("workspace_locator", "manuscript/current_package", "artifact_locator"),
    ],
    "human_gate_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "human_gate_decision"),
        _ref("json_pointer", "/product_entry_manifest/family_stage_control_plane/authority_boundary", "opl_boundary"),
    ],
}

_JOURNAL_FAMILY_PATTERNS: dict[str, tuple[str, ...]] = {
    "journal_response_pack": (
        "stable_comment_ids",
        "comment_response_tracker",
        "action_mapping",
        "missing_author_input_flags",
        "readiness_state",
    ),
    "data_availability_fair_pack": (
        "dataset_to_location_mapping",
        "restricted_data_access_route",
        "repository_identifier",
        "datacite_style_dataset_citation",
        "fair_metadata_checklist",
    ),
    "citation_integrity_pack": (
        "claim_segment_id",
        "candidate_citation_refs",
        "support_grade",
        "metadata_only_review_required",
        "reference_manager_export_note",
    ),
    "figure_evidence_contract_pack": (
        "core_claim",
        "evidence_chain",
        "panel_role",
        "source_data_refs",
        "statistics_refs",
        "export_contract",
        "qa_risks",
    ),
    "manuscript_argument_pack": (
        "paper_type_logic",
        "one_sentence_argument",
        "section_job_map",
        "claim_evidence_boundary_map",
        "paragraph_flow_review",
        "hedging_and_overclaim_check",
    ),
    "paper_reader_grounding_pack": (
        "source_map",
        "page_block_anchors",
        "figure_near_claim_refs",
        "source_grounded_followup",
    ),
    "paper_presentation_pack": (
        "evidence_spine",
        "selected_figure_assets",
        "speaker_notes_context",
        "optional_human_facing_deliverable",
    ),
    "statistical_reporting_pack": (
        "sample_size_and_denominator_trace",
        "effect_size_confidence_interval_p_value_trace",
        "missingness_and_exclusion_trace",
        "model_performance_calibration_external_validation_trace",
        "multiplicity_sensitivity_subgroup_assumption_trace",
        "software_version_and_reproducible_analysis_refs",
    ),
}

_JOURNAL_EXTENSION_CONTRACTS: dict[str, tuple[dict[str, object], ...]] = {
    "journal_response_pack": (
        {
            "contract_id": "reviewer_response_edge_case_contract",
            "learned_from": "nature-response",
            "absorbed_as": "revision_response_traceability_floor",
            "required_fields": [
                "decision_type",
                "editor_instruction_ids",
                "stable_reviewer_comment_ids",
                "comment_taxonomy",
                "action_label",
                "manuscript_location_or_placeholder_ref",
                "missing_author_input_state",
                "appeal_like_case_route",
                "difficult_case_risk_flag",
            ],
            "typed_blocker_if_missing": "journal_response_traceability_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "data_availability_fair_pack": (
        {
            "contract_id": "restricted_access_fair_metadata_contract",
            "learned_from": "nature-data",
            "absorbed_as": "dataset_availability_and_fair_trace_floor",
            "required_fields": [
                "result_supporting_dataset_inventory",
                "dataset_access_route",
                "generated_reused_third_party_class",
                "access_route",
                "restriction_reason",
                "data_controller_or_access_committee",
                "restricted_access_process_ref",
                "repository_identifier_or_blocker",
                "dataset_citation_metadata",
                "licence_or_reuse_condition",
                "code_material_protocol_split_ref",
                "available_upon_request_blocker_ref",
                "provenance_and_version_ref",
                "fair_metadata_check_ref",
            ],
            "typed_blocker_if_missing": "data_availability_or_fair_metadata_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "citation_integrity_pack": (
        {
            "contract_id": "strict_citation_scope_and_export_contract",
            "learned_from": "nature-citation",
            "absorbed_as": "claim_segment_citation_support_and_export_floor",
            "required_fields": [
                "claim_segment_id",
                "claim_type",
                "source_segment_ref",
                "claim_boundary",
                "english_search_claims",
                "query_claim_refs",
                "batch_strategy_ref",
                "accepted_journal_scope",
                "identifier_refs",
                "support_grade",
                "support_scale_refs",
                "contradictory_or_limiting_refs",
                "metadata_only_candidate_flag",
                "deduplication_basis",
                "deduplication_refs",
                "reference_export_format",
                "reference_export_ref",
            ],
            "allowed_export_formats": ["ENW", "RIS", "Zotero RDF", "BibTeX", "NBIB"],
            "typed_blocker_if_missing": "citation_support_or_export_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "figure_evidence_contract_pack": (
        {
            "contract_id": "figure_backend_export_qa_contract",
            "learned_from": "nature-figure",
            "absorbed_as": "figure_claim_evidence_export_qa_floor",
            "required_fields": [
                "core_conclusion",
                "evidence_chain",
                "panel_map",
                "selected_backend",
                "backend_exclusivity_proof",
                "export_formats",
                "editable_text_required",
                "source_data_refs",
                "statistics_refs",
                "image_integrity_notes",
                "visual_qa_ref",
            ],
            "forbidden_shortcuts": [
                "cross_backend_visual_fallback",
                "aesthetic_only_pass",
                "figure_without_source_data_or_statistics_trace",
            ],
            "typed_blocker_if_missing": "figure_export_or_source_data_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "manuscript_argument_pack": (
        {
            "contract_id": "prose_polish_claim_boundary_contract",
            "learned_from": "nature-polishing",
            "absorbed_as": "section_aware_prose_and_overclaim_floor",
            "required_fields": [
                "paper_type",
                "section_role",
                "reader_question",
                "reader_question_sequence",
                "writing_failure_mode",
                "section_architecture_id",
                "evidence_ladder_refs",
                "claim_strength",
                "hedging_calibration",
                "section_tense_check",
                "sentence_or_paragraph_risk_ref",
                "overclaim_detection_ref",
            ],
            "typed_blocker_if_missing": "manuscript_argument_or_overclaim_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "paper_reader_grounding_pack": (
        {
            "contract_id": "full_paper_reader_source_map_contract",
            "learned_from": "nature-reader",
            "absorbed_as": "source_grounded_reader_block_anchor_floor",
            "required_fields": [
                "source_map_ref",
                "stable_text_block_ids",
                "caption_block_ids",
                "figure_or_table_asset_ids",
                "page_and_block_anchors",
                "figure_near_first_substantive_mention_ref",
                "uncertainty_or_ocr_note_ref",
                "source_grounded_followup_refs",
            ],
            "typed_blocker_if_missing": "reader_source_map_or_anchor_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
    "paper_presentation_pack": (
        {
            "contract_id": "pptx_asset_manifest_and_package_qa_contract",
            "learned_from": "nature-paper2ppt",
            "absorbed_as": "presentation_evidence_spine_and_pptx_qa_floor",
            "required_fields": [
                "paper_type",
                "presentation_logic",
                "evidence_spine",
                "selected_figure_asset_refs",
                "asset_manifest_ref",
                "slide_count",
                "embedded_media_refs",
                "speaker_notes_context",
                "text_overflow_check_ref",
                "pptx_reopen_or_package_qa_ref",
            ],
            "typed_blocker_if_missing": "presentation_asset_or_package_qa_blocker",
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
    ),
}

_JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS: dict[str, tuple[tuple[str, str], ...]] = {
    "journal_response_pack": (
        ("reviewer_comment_refs", "stable_reviewer_comment_identity"),
        ("response_action_map_refs", "comment_to_revision_or_blocker_trace"),
        ("readiness_or_blocker_ref", "response_closeout_state"),
    ),
    "data_availability_fair_pack": (
        ("dataset_locator_refs", "dataset_to_repository_or_restricted_access_trace"),
        ("data_availability_statement_ref", "submission_statement_trace"),
        ("fair_metadata_review_refs", "repository_metadata_and_identifier_check"),
    ),
    "citation_integrity_pack": (
        ("claim_segment_refs", "claim_to_source_review_unit"),
        ("citation_candidate_refs", "candidate_reference_identity"),
        ("support_grade_refs", "support_or_blocker_trace"),
    ),
    "figure_evidence_contract_pack": (
        ("figure_panel_refs", "panel_to_claim_review_unit"),
        ("source_data_refs", "source_data_and_statistics_trace"),
        ("export_contract_refs", "rendered_artifact_trace"),
    ),
    "manuscript_argument_pack": (
        ("argument_spine_refs", "paper_type_and_one_sentence_argument_trace"),
        ("section_job_map_refs", "section_and_paragraph_role_review_trace"),
        ("claim_boundary_refs", "claim_evidence_boundary_and_overclaim_trace"),
    ),
    "paper_reader_grounding_pack": (
        ("source_map_refs", "paper_reader_source_anchor_trace"),
        ("page_block_anchor_refs", "reader_visible_block_identity"),
        ("followup_grounding_refs", "reader_question_to_source_trace"),
    ),
    "paper_presentation_pack": (
        ("evidence_spine_refs", "presentation_claim_sequence_trace"),
        ("selected_figure_asset_refs", "human_facing_visual_evidence_trace"),
        ("speaker_context_refs", "reader_or_presenter_context_trace"),
    ),
    "statistical_reporting_pack": (
        ("effect_estimate_refs", "effect_size_confidence_interval_p_value_trace"),
        ("denominator_missingness_refs", "sample_size_missingness_and_exclusion_trace"),
        ("model_validation_refs", "calibration_external_validation_and_sensitivity_trace"),
    ),
}

_JOURNAL_REQUIRED_REVIEWER_OUTPUTS: dict[str, tuple[tuple[str, str], ...]] = {
    "journal_response_pack": (
        ("refs", "reviewer_comment_and_response_refs"),
        ("blocker_or_readiness", "revision_response_ready_or_blocked"),
        ("reviewer_record", "independent_reviewer_response_record"),
    ),
    "data_availability_fair_pack": (
        ("refs", "dataset_statement_and_repository_refs"),
        ("blocker_or_readiness", "data_availability_ready_or_blocked"),
        ("owner_receipt_ref", "mas_data_asset_owner_receipt_or_typed_blocker"),
    ),
    "citation_integrity_pack": (
        ("refs", "claim_citation_and_evidence_refs"),
        ("blocker_or_readiness", "citation_support_ready_or_blocked"),
        ("reviewer_record", "independent_citation_review_record"),
    ),
    "figure_evidence_contract_pack": (
        ("refs", "figure_panel_source_data_and_export_refs"),
        ("blocker_or_readiness", "figure_evidence_ready_or_blocked"),
        ("owner_receipt_ref", "mas_display_or_artifact_owner_receipt_or_typed_blocker"),
    ),
    "manuscript_argument_pack": (
        ("refs", "argument_section_claim_boundary_and_prose_review_refs"),
        ("blocker_or_readiness", "manuscript_argument_ready_or_blocked"),
        ("reviewer_record", "independent_argument_and_prose_review_record"),
    ),
    "paper_reader_grounding_pack": (
        ("refs", "source_map_and_reader_anchor_refs"),
        ("blocker_or_readiness", "reader_grounding_ready_or_blocked"),
        ("reviewer_record", "independent_reader_grounding_review_record"),
    ),
    "paper_presentation_pack": (
        ("refs", "presentation_source_and_asset_refs"),
        ("blocker_or_readiness", "presentation_ready_or_blocked"),
        ("owner_receipt_ref", "mas_delivery_owner_receipt_or_typed_blocker"),
    ),
    "statistical_reporting_pack": (
        ("refs", "statistical_methods_estimates_denominators_and_validation_refs"),
        ("blocker_or_readiness", "statistical_reporting_ready_or_blocked"),
        ("owner_receipt_ref", "mas_analysis_owner_receipt_or_typed_blocker"),
    ),
}

_REVIEWER_PRECOMMITMENT_PACK_IDS: tuple[str, ...] = (
    "ai_native_expert_judgment_pack",
    "medical_claim_evidence_pack",
    "journal_response_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
    "figure_evidence_contract_pack",
    "manuscript_argument_pack",
    "paper_reader_grounding_pack",
    "paper_presentation_pack",
    "statistical_reporting_pack",
)
