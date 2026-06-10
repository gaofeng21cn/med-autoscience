from __future__ import annotations

from med_autoscience.progress_first_external_learning_contract import (
    CITATION_LIFECYCLE_QUEUE_FIELDS,
    COMPILED_VISUAL_REGION_QA_FIELDS,
    EXECUTOR_REAL_RUN_CLOSEOUT_FIELDS,
    FIGURE_DATA_LINEAGE_QA_FIELDS,
    HUMAN_DECISION_REQUEST_FIELDS,
    MICRO_STUDY_CANARY_STEPS,
    OPERATOR_MESSAGE_PREVIEW_FIELDS,
    SEMANTIC_NO_PROGRESS_EVIDENCE_FIELDS,
    build_ark_progress_first_learning_contract,
)


def test_ark_progress_first_learning_contract_preserves_mas_authority_boundary() -> None:
    contract = build_ark_progress_first_learning_contract()

    assert contract["surface_kind"] == "mas_ark_progress_first_learning_contract"
    assert contract["owner"] == "MedAutoScience"
    assert contract["clean_room_absorption"] == {
        "source_project": "kaust-ark/ARK",
        "source_commit": "01cab1048cc78fa4d33e8274e4f963a44d70dc48",
        "source_files": [
            "README.md",
            "TODO.md",
            "skills/builtin/human-intervention/SKILL.md",
            "skills/builtin/figure-integrity/SKILL.md",
            "tests/_preview_telegram.py",
        ],
        "absorbed_as": "mas_native_progress_first_contract_pattern",
        "runtime_dependency": False,
        "vendor_dependency": False,
        "foreign_authority": False,
    }

    boundary = contract["authority_boundary"]
    assert boundary["truth_owner"] == "MedAutoScience"
    assert boundary["publication_readiness_authority"] is False
    assert boundary["quality_verdict_authority"] is False
    assert boundary["source_readiness_authority"] is False
    assert boundary["artifact_mutation_authority"] is False
    assert boundary["runtime_control_authority"] is False
    assert boundary["human_approval_authority"] is False
    assert boundary["operator_message_transport_authority"] is False
    assert boundary["opl_can_write_mas_truth"] is False


def test_contract_is_progress_first_and_does_not_globalize_quality_gaps() -> None:
    contract = build_ark_progress_first_learning_contract()

    assert contract["progress_first_policy"] == {
        "may_block_unrelated_agent_progress": False,
        "non_hard_gate_gap_behavior": "typed_work_unit_or_route_back",
        "hard_gate_blockers": [
            "source_readiness_gate",
            "publication_gate",
            "artifact_mutation_authority_gate",
            "human_or_expert_gate",
            "forbidden_write_guard",
        ],
        "quality_gap_default": "continue_with_bounded_repair_work_unit",
        "operator_preview_gap_default": "projection_repair_work_unit",
    }
    assert "score_or_stagnation_threshold_as_publication_readiness" in contract["forbidden_adoptions"]
    assert "fallback_experiment_or_fabricated_result" in contract["forbidden_adoptions"]


def test_micro_study_canary_is_synthetic_and_routes_failures_to_platform_repair() -> None:
    contract = build_ark_progress_first_learning_contract()
    canary = contract["micro_study_canary_contract"]

    assert canary["required_steps"] == list(MICRO_STUDY_CANARY_STEPS)
    assert canary["target_runtime_budget_minutes"] == 5
    assert canary["study_authority_role"] == "synthetic_fixture_only"
    assert canary["failure_behavior"] == "platform_repair_work_unit"
    assert canary["may_block_real_studies"] is False
    assert canary["may_authorize_publication_readiness"] is False
    assert set(canary["failure_required_fields"]) >= {
        "failed_step",
        "reproducer_ref",
        "expected_contract_ref",
        "acceptance_test_ref",
    }


def test_human_decision_request_is_typed_and_reserved_for_hard_gates() -> None:
    contract = build_ark_progress_first_learning_contract()
    decision = contract["human_decision_request_contract"]

    assert decision["required_fields"] == list(HUMAN_DECISION_REQUEST_FIELDS)
    assert decision["hard_gate_only"] is True
    assert decision["ordinary_quality_gap_behavior"] == "owner_work_unit_not_human_block"
    assert decision["after_request_behavior"] == {
        "dependent_work": "stop_until_decision_receipt",
        "unrelated_work": "may_continue",
        "fallback_or_degraded_completion_allowed": False,
        "decision_receipt_required_before_retry": True,
    }
    assert decision["may_authorize_human_approval"] is False
    assert decision["may_authorize_publication_readiness"] is False


def test_operator_message_preview_is_read_only_projection_not_transport_authority() -> None:
    contract = build_ark_progress_first_learning_contract()
    preview = contract["operator_message_preview_contract"]

    assert preview["required_fields"] == list(OPERATOR_MESSAGE_PREVIEW_FIELDS)
    assert preview["preview_scope"] == "readability_redaction_and_action_ref_integrity"
    assert preview["network_side_effects_allowed"] is False
    assert preview["transport_dependency"] is False
    assert "operator_transport_delivery_receipt" in preview["forbidden_preview_outputs"]
    assert "study_truth_write" in preview["forbidden_preview_outputs"]
    assert preview["preview_gap_behavior"] == "projection_repair_work_unit"
    assert preview["may_block_agent_progress"] is False


def test_figure_lineage_qa_tracks_result_to_claim_without_artifact_authority() -> None:
    contract = build_ark_progress_first_learning_contract()
    lineage = contract["figure_data_lineage_qa_contract"]

    assert lineage["required_fields"] == list(FIGURE_DATA_LINEAGE_QA_FIELDS)
    assert lineage["lineage_chain"] == [
        "experiment_result_ref",
        "result_digest",
        "display_artifact_manifest_ref",
        "rendered_artifact_ref",
        "claim_refs",
    ]
    assert lineage["sampled_value_check_policy"] == {
        "minimum_sampled_values": 2,
        "sample_basis": "statistical_value_refs",
        "source_of_truth": "result_file_or_dataset_manifest",
    }
    assert lineage["page_adjustment_priority_ladder"] == [
        "lossless_layout_adjustment",
        "minimally_lossy_presentation_adjustment",
        "manifest_gated_lossy_adjustment",
    ]
    assert lineage["page_adjustment_policy"]["data_or_claim_changes_without_mas_authority"] == "typed_blocker"
    assert lineage["missing_or_mismatch_behavior"] == "artifact_qa_work_unit"
    assert lineage["may_block_unrelated_agent_progress"] is False
    assert lineage["may_authorize_artifact_mutation"] is False


def test_executor_real_run_closeout_requires_real_evidence_not_degraded_fallback() -> None:
    contract = build_ark_progress_first_learning_contract()
    closeout = contract["executor_real_run_closeout_contract"]

    assert closeout["required_fields"] == list(EXECUTOR_REAL_RUN_CLOSEOUT_FIELDS)
    assert closeout["blocked_not_degraded_policy"] == {
        "missing_resource_status": "blocked",
        "fallback_completion_status_allowed": False,
        "llm_substitute_for_real_experiment_allowed": False,
        "failed_command_evidence_required": True,
    }
    assert closeout["dependent_work_behavior"] == "stop_until_resource_or_decision_receipt"
    assert closeout["unrelated_work_behavior"] == "may_continue"
    assert closeout["missing_closeout_behavior"] == "owner_work_unit_or_typed_blocker_for_hard_gate"
    assert closeout["may_authorize_publication_readiness"] is False
    assert closeout["may_authorize_quality_verdict"] is False


def test_compiled_visual_region_qa_routes_layout_gaps_to_work_units() -> None:
    contract = build_ark_progress_first_learning_contract()
    visual = contract["compiled_visual_region_qa_contract"]

    assert visual["required_fields"] == list(COMPILED_VISUAL_REGION_QA_FIELDS)
    assert visual["qa_checks"] == [
        "page_region_bounds",
        "text_overlap",
        "figure_overflow",
        "table_overflow",
        "template_width_compliance",
        "effective_font_size_after_scaling",
        "physical_export_size_roundtrip",
        "multi_panel_non_redundancy",
    ]
    assert visual["advisory_source_patterns"] == {
        "Light0305/Light@d71033733bc4b357f3a2f0b6460ad7d8da070954": [
            "check_scaled_fonts_effective_font_size",
            "exported_figure_physical_size_validation",
            "panel_unique_scientific_question_review",
        ]
    }
    assert visual["missing_or_failed_check_behavior"] == "layout_work_unit"
    assert visual["hard_gate_only_when"] == [
        "publication_gate_requires_compiled_artifact",
        "compiled_region_hides_or_changes_scientific_claim",
        "artifact_mutation_authority_required",
    ]
    assert visual["may_block_unrelated_agent_progress"] is False
    assert visual["may_authorize_publication_readiness"] is False
    assert visual["may_authorize_artifact_mutation"] is False


def test_semantic_no_progress_signal_is_reviewer_evidence_not_a_stop_rule() -> None:
    contract = build_ark_progress_first_learning_contract()
    evidence = contract["semantic_no_progress_evidence_contract"]

    assert evidence["required_fields"] == list(SEMANTIC_NO_PROGRESS_EVIDENCE_FIELDS)
    assert evidence["no_progress_signal_role"] == "reviewer_issue_evidence_only"
    assert evidence["empty_or_trivial_delta_behavior"] == "next_bounded_work_unit_or_reviewer_route_back"
    assert evidence["score_or_stagnation_threshold_authority"] is False
    assert evidence["may_block_unrelated_agent_progress"] is False
    assert evidence["may_authorize_quality_verdict"] is False
    assert evidence["may_authorize_publication_readiness"] is False


def test_citation_lifecycle_queue_turns_stale_or_unused_refs_into_work_units() -> None:
    contract = build_ark_progress_first_learning_contract()
    queue = contract["citation_lifecycle_queue_contract"]

    assert queue["required_fields"] == list(CITATION_LIFECYCLE_QUEUE_FIELDS)
    assert queue["issue_kinds"] == [
        "unused_citation_cleanup",
        "stale_citation_refresh",
        "claim_citation_mismatch",
        "metadata_only_candidate_review",
        "preprint_published_version_refresh",
    ]
    assert queue["queue_behavior"] == {
        "unused_citation": "cleanup_work_unit",
        "stale_citation": "source_refresh_work_unit",
        "claim_citation_mismatch": "reviewer_route_back_or_source_refresh",
        "metadata_only_candidate": "manual_or_source_api_verification_required",
        "critical_claim_without_source": "typed_blocker",
    }
    assert queue["may_block_unrelated_agent_progress"] is False
    assert queue["may_authorize_source_readiness"] is False
    assert queue["may_authorize_publication_readiness"] is False
