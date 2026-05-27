from __future__ import annotations


STRONG_PROMOTION_EVIDENCE_KINDS: tuple[str, ...] = (
    "synthetic_fixture",
    "focused_tests",
    "real_paper_line_owner_receipt",
    "anonymized_package_evidence",
)

PACK_MATURITY_STATUS: dict[str, str] = {
    "ai_native_expert_judgment_pack": "stable_contract",
    "medical_claim_evidence_pack": "stable_contract",
    "statistical_analysis_pack": "stable_contract",
    "reporting_guideline_pack": "stable_contract",
    "manuscript_argument_pack": "stable_contract",
    "statistical_reporting_pack": "stable_contract",
    "display_to_claim_pack": "stable_contract",
    "journal_response_pack": "stable_contract",
    "data_availability_fair_pack": "stable_contract",
    "citation_integrity_pack": "stable_contract",
    "figure_evidence_contract_pack": "stable_contract",
    "paper_reader_grounding_pack": "stable_contract",
    "paper_presentation_pack": "beta_contract",
    "life_science_source_discovery_pack": "beta_contract",
    "route_memory_pack": "stable_contract",
    "stop_loss_pack": "stable_contract",
    "artifact_freshness_pack": "stable_contract",
    "human_gate_pack": "stable_contract",
}

UPSTREAM_NATURE_STATUS_SIGNAL: dict[str, str] = {
    "journal_response_pack": "draft_beta_stable_skill_status_pattern_learned",
    "manuscript_argument_pack": "draft_beta_stable_skill_status_pattern_learned",
    "statistical_reporting_pack": "draft_beta_stable_skill_status_pattern_learned",
    "data_availability_fair_pack": "draft_beta_stable_skill_status_pattern_learned",
    "citation_integrity_pack": "draft_beta_stable_skill_status_pattern_learned",
    "figure_evidence_contract_pack": "draft_beta_stable_skill_status_pattern_learned",
    "paper_reader_grounding_pack": "draft_beta_stable_skill_status_pattern_learned",
    "paper_presentation_pack": "draft_beta_stable_skill_status_pattern_learned",
    "life_science_source_discovery_pack": "openai_plugin_skill_pack_pattern_learned",
}


def build_promotion_evidence(pack_id: str) -> dict[str, object]:
    maturity_status = PACK_MATURITY_STATUS[pack_id]
    stable_contract = maturity_status == "stable_contract"
    return {
        "maturity_model": "mas_contract_maturity_not_vendor_skill_status",
        "upstream_status_signal": UPSTREAM_NATURE_STATUS_SIGNAL.get(pack_id, "not_applicable"),
        "stable_requires_strong_evidence": True,
        "strong_evidence_kinds": list(STRONG_PROMOTION_EVIDENCE_KINDS),
        "evidence": list(PACK_PROMOTION_EVIDENCE[pack_id]),
        "stable_strong_evidence_satisfied": (
            _has_strong_promotion_evidence(pack_id) if stable_contract else False
        ),
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
    }


def _has_strong_promotion_evidence(pack_id: str) -> bool:
    return any(
        evidence["strength"] == "strong"
        and evidence["evidence_kind"] in STRONG_PROMOTION_EVIDENCE_KINDS
        for evidence in PACK_PROMOTION_EVIDENCE[pack_id]
    )


def _evidence(
    evidence_id: str,
    evidence_kind: str,
    ref_kind: str,
    ref: str,
    role: str,
    *,
    strength: str = "supporting",
) -> dict[str, str]:
    return {
        "evidence_id": evidence_id,
        "evidence_kind": evidence_kind,
        "ref_kind": ref_kind,
        "ref": ref,
        "role": role,
        "strength": strength,
    }


PACK_PROMOTION_EVIDENCE: dict[str, tuple[dict[str, str], ...]] = {
    "ai_native_expert_judgment_pack": (
        _evidence(
            "ai_reviewer_focused_contract_tests",
            "focused_tests",
            "test",
            "tests/test_ai_first_quality_boundary.py",
            "independent_reviewer_boundary_and_quality_pack_consumption",
            strength="strong",
        ),
    ),
    "medical_claim_evidence_pack": (
        _evidence(
            "claim_evidence_contract_tests",
            "focused_tests",
            "test",
            "tests/test_stage_quality_contract.py",
            "claim_evidence_refs_and_review_ledger_contract",
            strength="strong",
        ),
    ),
    "statistical_analysis_pack": (
        _evidence(
            "analysis_contract_focused_tests",
            "focused_tests",
            "test",
            "tests/test_stage_quality_contract.py",
            "analysis_contract_and_controller_decision_refs",
            strength="strong",
        ),
    ),
    "reporting_guideline_pack": (
        _evidence(
            "reporting_guideline_selection_tests",
            "focused_tests",
            "test",
            "tests/test_stage_quality_contract.py",
            "clinical_reporting_family_selection",
            strength="strong",
        ),
    ),
    "manuscript_argument_pack": (
        _evidence(
            "manuscript_argument_focused_tests",
            "focused_tests",
            "test",
            "tests/test_nature_skills_learning_contract.py",
            "argument_spine_section_job_map_and_claim_boundary_contract",
            strength="strong",
        ),
        _evidence(
            "manuscript_argument_owner_receipt_path",
            "real_paper_line_owner_receipt",
            "workspace_locator",
            "artifacts/publication_eval/latest.json",
            "ai_reviewer_argument_and_prose_review_required_before_publication_claim",
            strength="strong",
        ),
    ),
    "statistical_reporting_pack": (
        _evidence(
            "statistical_reporting_focused_tests",
            "focused_tests",
            "test",
            "tests/test_nature_skills_learning_contract.py",
            "statistical_reporting_refs_and_owner_receipt_contract",
            strength="strong",
        ),
        _evidence(
            "statistical_reporting_synthetic_fixture",
            "synthetic_fixture",
            "workspace_locator",
            "paper/evidence/evidence_ledger.json",
            "effect_estimate_denominator_missingness_and_validation_fixture",
            strength="strong",
        ),
    ),
    "display_to_claim_pack": (
        _evidence(
            "display_contract_focused_tests",
            "focused_tests",
            "test",
            "tests/test_publication_display_contract.py",
            "display_to_claim_trace_contract",
            strength="strong",
        ),
    ),
    "journal_response_pack": (
        _evidence(
            "journal_response_focused_tests",
            "focused_tests",
            "test",
            "tests/test_nature_skills_learning_contract.py",
            "reviewer_comment_response_tracker_and_independent_reviewer_output",
            strength="strong",
        ),
        _evidence(
            "journal_response_owner_receipt_path",
            "real_paper_line_owner_receipt",
            "workspace_locator",
            "paper/review/review_ledger.json",
            "real_revision_or_typed_blocker_receipt_required_before_publication_claim",
            strength="strong",
        ),
    ),
    "data_availability_fair_pack": (
        _evidence(
            "data_availability_focused_tests",
            "focused_tests",
            "test",
            "tests/test_data_assets.py",
            "data_asset_mapping_and_submission_statement_contract",
            strength="strong",
        ),
        _evidence(
            "data_availability_package_evidence",
            "anonymized_package_evidence",
            "workspace_locator",
            "paper/submission_minimal",
            "dataset_statement_or_restricted_access_package_trace",
            strength="strong",
        ),
    ),
    "citation_integrity_pack": (
        _evidence(
            "citation_integrity_focused_tests",
            "focused_tests",
            "test",
            "tests/test_citation_integrity_projection.py",
            "claim_segment_to_citation_support_projection",
            strength="strong",
        ),
        _evidence(
            "citation_integrity_synthetic_fixture",
            "synthetic_fixture",
            "workspace_locator",
            "paper/evidence/evidence_ledger.json",
            "claim_citation_support_or_blocker_fixture",
            strength="strong",
        ),
    ),
    "figure_evidence_contract_pack": (
        _evidence(
            "figure_contract_focused_tests",
            "focused_tests",
            "test",
            "tests/test_figure_renderer_contract.py",
            "figure_panel_source_data_export_contract",
            strength="strong",
        ),
        _evidence(
            "figure_package_evidence",
            "anonymized_package_evidence",
            "workspace_locator",
            "paper/evidence/evidence_ledger.json",
            "source_data_statistics_and_rendered_artifact_trace",
            strength="strong",
        ),
    ),
    "paper_reader_grounding_pack": (
        _evidence(
            "reader_grounding_focused_tests",
            "focused_tests",
            "test",
            "tests/progress_portal_cases/test_stage_review_surface.py",
            "stage_review_page_and_index_source_grounding_projection",
            strength="strong",
        ),
    ),
    "paper_presentation_pack": (
        _evidence(
            "presentation_contract_tests",
            "focused_tests",
            "test",
            "tests/test_nature_skills_learning_contract.py",
            "presentation_source_asset_and_context_refs",
            strength="strong",
        ),
    ),
    "life_science_source_discovery_pack": (
        _evidence(
            "life_science_source_discovery_contract_tests",
            "focused_tests",
            "test",
            "tests/test_life_science_source_discovery_pack.py",
            "openai_life_science_research_patterns_as_mas_source_refs",
            strength="strong",
        ),
    ),
    "route_memory_pack": (
        _evidence(
            "route_memory_focused_tests",
            "focused_tests",
            "test",
            "tests/test_stage_route_assets.py",
            "stage_knowledge_and_memory_route_refs",
            strength="strong",
        ),
    ),
    "stop_loss_pack": (
        _evidence(
            "stop_loss_controller_tests",
            "focused_tests",
            "test",
            "tests/test_stage_quality_contract.py",
            "controller_decision_and_escalation_context_refs",
            strength="strong",
        ),
    ),
    "artifact_freshness_pack": (
        _evidence(
            "artifact_freshness_package_evidence",
            "anonymized_package_evidence",
            "workspace_locator",
            "artifacts/delivery_manifest/latest.json",
            "delivery_manifest_and_current_package_freshness_trace",
            strength="strong",
        ),
    ),
    "human_gate_pack": (
        _evidence(
            "human_gate_controller_receipt",
            "real_paper_line_owner_receipt",
            "workspace_locator",
            "artifacts/controller_decisions/latest.json",
            "human_gate_or_typed_blocker_controller_receipt",
            strength="strong",
        ),
    ),
}


__all__ = [
    "PACK_MATURITY_STATUS",
    "STRONG_PROMOTION_EVIDENCE_KINDS",
    "build_promotion_evidence",
]
