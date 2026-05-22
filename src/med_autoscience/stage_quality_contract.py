from __future__ import annotations

from collections.abc import Iterable
from typing import Any


SURFACE_KIND = "mas_stage_quality_pack_contract"
VERSION = "mas-stage-quality-pack-contract.v1"
PROJECTION_KIND = "stage_quality_pack_projection"
CONTRACT_REF = "med_autoscience.stage_quality_contract.build_stage_quality_pack_contract"
REPO_PATH = "src/med_autoscience/stage_quality_contract.py"

PACK_ROLE = "quality_input_and_reviewer_rubric"
REFRESH_POLICY = "rebuild_product_entry_manifest_before_opl_discovery"

REQUIRED_STAGE_QUALITY_PACK_IDS: tuple[str, ...] = (
    "ai_native_expert_judgment_pack",
    "medical_claim_evidence_pack",
    "statistical_analysis_pack",
    "reporting_guideline_pack",
    "manuscript_argument_pack",
    "statistical_reporting_pack",
    "display_to_claim_pack",
    "journal_response_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
    "figure_evidence_contract_pack",
    "paper_reader_grounding_pack",
    "paper_presentation_pack",
    "route_memory_pack",
    "stop_loss_pack",
    "artifact_freshness_pack",
    "human_gate_pack",
)

JOURNAL_FAMILY_QUALITY_PACK_IDS: tuple[str, ...] = (
    "journal_response_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
    "figure_evidence_contract_pack",
    "manuscript_argument_pack",
    "paper_reader_grounding_pack",
    "paper_presentation_pack",
    "statistical_reporting_pack",
)

QUALITY_PACK_CONTRACT_SURFACES: tuple[str, ...] = (SURFACE_KIND, PROJECTION_KIND)
STRONG_PROMOTION_EVIDENCE_KINDS: tuple[str, ...] = (
    "synthetic_fixture",
    "focused_tests",
    "real_paper_line_owner_receipt",
    "anonymized_package_evidence",
)

CLINICAL_BASE_GUIDELINES: tuple[str, ...] = (
    "STROBE",
    "TRIPOD",
    "TRIPOD-AI",
    "CONSORT",
    "PRISMA",
    "STARD",
    "CARE",
)

DEFAULT_STUDY_ARCHETYPES: tuple[str, ...] = (
    "clinical_classifier",
    "clinical_subtype_reconstruction",
    "external_validation_model_update",
    "gray_zone_triage",
    "llm_agent_clinical_task",
    "mechanistic_sidecar_extension",
    "survey_trend_analysis",
)

REPORTING_STUDY_ARCHETYPES: tuple[str, ...] = (
    "observational_or_cohort_or_registry",
    "diagnostic_or_prognostic_model",
    "randomized_or_intervention",
    "systematic_review_or_meta_analysis",
    "diagnostic_accuracy",
    "case_report_or_case_series",
    "ai_ml_medical_study",
)

_PACK_STAGE_MAP: dict[str, tuple[str, ...]] = {
    "ai_native_expert_judgment_pack": (
        "scout",
        "idea",
        "baseline",
        "experiment",
        "analysis-campaign",
        "write",
        "review",
        "finalize",
        "decision",
        "journal-resolution",
    ),
    "medical_claim_evidence_pack": ("write", "review", "finalize", "decision"),
    "statistical_analysis_pack": ("baseline", "experiment", "analysis-campaign"),
    "reporting_guideline_pack": ("write", "review", "finalize", "journal-resolution"),
    "manuscript_argument_pack": ("write", "review", "finalize", "decision"),
    "statistical_reporting_pack": ("analysis-campaign", "write", "review", "finalize", "journal-resolution"),
    "display_to_claim_pack": ("analysis-campaign", "write", "review"),
    "journal_response_pack": ("review", "finalize", "journal-resolution"),
    "data_availability_fair_pack": ("write", "review", "finalize", "journal-resolution"),
    "citation_integrity_pack": ("write", "review", "finalize", "journal-resolution"),
    "figure_evidence_contract_pack": ("analysis-campaign", "write", "review", "finalize"),
    "paper_reader_grounding_pack": ("scout", "review", "finalize", "decision"),
    "paper_presentation_pack": ("finalize", "delivery_sync"),
    "route_memory_pack": ("scout", "idea", "analysis-campaign", "review", "decision"),
    "stop_loss_pack": ("idea", "baseline", "experiment", "analysis-campaign", "review", "decision"),
    "artifact_freshness_pack": ("write", "finalize", "delivery_sync"),
    "human_gate_pack": ("all_boundary_changing_stages",),
}

_PACK_STUDY_ARCHETYPE_MAP: dict[str, tuple[str, ...]] = {
    "ai_native_expert_judgment_pack": ("all_medical_research_stages",),
    "medical_claim_evidence_pack": ("all_clinical_manuscripts",),
    "statistical_analysis_pack": (
        "observational_or_cohort_or_registry",
        "diagnostic_or_prognostic_model",
        "randomized_or_intervention",
        "diagnostic_accuracy",
        "survey_trend_analysis",
    ),
    "reporting_guideline_pack": REPORTING_STUDY_ARCHETYPES,
    "manuscript_argument_pack": ("all_clinical_manuscripts",),
    "statistical_reporting_pack": (
        "observational_or_cohort_or_registry",
        "diagnostic_or_prognostic_model",
        "randomized_or_intervention",
        "systematic_review_or_meta_analysis",
        "diagnostic_accuracy",
        "ai_ml_medical_study",
        "survey_trend_analysis",
    ),
    "display_to_claim_pack": (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "diagnostic_accuracy",
        "ai_ml_medical_study",
    ),
    "journal_response_pack": ("all_revision_or_response_candidates",),
    "data_availability_fair_pack": ("all_submission_or_delivery_candidates",),
    "citation_integrity_pack": ("all_clinical_manuscripts",),
    "figure_evidence_contract_pack": ("all_figure_supported_manuscripts",),
    "paper_reader_grounding_pack": ("all_source_grounded_paper_lines",),
    "paper_presentation_pack": ("all_human_facing_paper_deliverables",),
    "route_memory_pack": DEFAULT_STUDY_ARCHETYPES,
    "stop_loss_pack": DEFAULT_STUDY_ARCHETYPES,
    "artifact_freshness_pack": ("all_submission_or_delivery_candidates",),
    "human_gate_pack": ("all_boundary_changing_studies",),
}


def build_stage_quality_pack_contract() -> dict[str, Any]:
    packs = [_build_pack(pack_id) for pack_id in REQUIRED_STAGE_QUALITY_PACK_IDS]
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "owner": "MedAutoScience",
        "contract_ref": CONTRACT_REF,
        "repo_source_ref": REPO_PATH,
        "pack_ids": list(REQUIRED_STAGE_QUALITY_PACK_IDS),
        "packs": packs,
        "pack_locators": {
            pack["pack_id"]: {
                "ref_kind": "json_pointer",
                "ref": f"/product_entry_manifest/stage_quality_pack_contract/packs/{pack['pack_id']}",
                "role": "quality_pack_descriptor",
            }
            for pack in packs
        },
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "refresh_policy": REFRESH_POLICY,
            "source_ref": REPO_PATH,
            "stale_if_contract_source_missing": True,
        },
        "authority_boundary": _contract_authority_boundary(),
        "opl_projection_boundary": {
            "role": "descriptor_ref_freshness_locator_only",
            "allowed_fields": ["contract_ref", "pack_ids", "freshness", "pack_locators", "authority_boundary"],
            "forbidden_outputs": [
                "quality_verdict",
                "publication_readiness",
                "submission_readiness",
                "mas_truth_write",
            ],
        },
    }


def build_stage_quality_pack_projection() -> dict[str, Any]:
    return {
        "surface_kind": PROJECTION_KIND,
        "contract_ref": CONTRACT_REF,
        "pack_ids": list(REQUIRED_STAGE_QUALITY_PACK_IDS),
        "pack_count": len(REQUIRED_STAGE_QUALITY_PACK_IDS),
        "pack_role": PACK_ROLE,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
    }


def build_stage_quality_pack_locator_projection() -> dict[str, Any]:
    return {
        "ref_kind": "json_pointer",
        "ref": "/product_entry_manifest/stage_quality_pack_contract",
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
        "opl_projection_boundary": "descriptor_ref_freshness_locator_only",
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
    }


def quality_pack_ids_for_stages(stage_ids: Iterable[str]) -> list[str]:
    stage_set = {str(stage_id) for stage_id in stage_ids}
    selected: list[str] = []
    for pack_id in REQUIRED_STAGE_QUALITY_PACK_IDS:
        pack_stages = set(_PACK_STAGE_MAP[pack_id])
        if "human_gate_pack" == pack_id or stage_set & pack_stages:
            selected.append(pack_id)
    return selected


def build_stage_quality_pack_ref_projection(stage_ids: Iterable[str]) -> dict[str, Any]:
    return {
        "role": PACK_ROLE,
        "pack_refs": quality_pack_ids_for_stages(stage_ids),
        "contract_ref": CONTRACT_REF,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
        "opl_projection_boundary": "descriptor_ref_freshness_locator_only",
    }


def _build_pack(pack_id: str) -> dict[str, Any]:
    pack = {
        "pack_id": pack_id,
        "title": _PACK_TITLES[pack_id],
        "role": PACK_ROLE,
        "maturity_status": _PACK_MATURITY_STATUS[pack_id],
        "promotion_evidence": _promotion_evidence(pack_id),
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "applies_to": {
            "stages": list(_PACK_STAGE_MAP[pack_id]),
            "study_archetypes": list(_PACK_STUDY_ARCHETYPE_MAP[pack_id]),
        },
        "authority_boundary": _pack_authority_boundary(),
        "owner_refs": list(_PACK_OWNER_REFS[pack_id]),
        "required_refs": list(_PACK_REQUIRED_REFS[pack_id]),
    }
    if pack_id == "reporting_guideline_pack":
        pack["guideline_selection"] = _reporting_guideline_selection()
    if pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack["journal_family_patterns"] = list(_JOURNAL_FAMILY_PATTERNS[pack_id])
        pack["clean_room_absorption"] = _clean_room_absorption()
        pack["acceptance_evidence_fields"] = _journal_acceptance_evidence_fields(pack_id)
        pack["required_reviewer_output"] = _journal_required_reviewer_output(pack_id)
        pack["forbidden_authority"] = _journal_forbidden_authority()
        pack["quality_pack_consumption"] = _journal_quality_pack_consumption(pack_id)
    return pack


def _contract_authority_boundary() -> dict[str, Any]:
    return {
        "pack_role": PACK_ROLE,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "truth_owner": "MedAutoScience",
        "opl_role": "descriptor_ref_freshness_locator_consumer",
        "opl_can_write_mas_truth": False,
        "opl_can_authorize_quality_verdict": False,
        "opl_can_authorize_publication_readiness": False,
    }


def _pack_authority_boundary() -> dict[str, Any]:
    return {
        "truth_owner": "MedAutoScience",
        "quality_owner": "MedAutoScience",
        "reviewer_rubric_owner": "MedAutoScience",
        "pack_role": PACK_ROLE,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_write_domain_truth": False,
    }


def _reporting_guideline_selection() -> list[dict[str, Any]]:
    return [
        _guideline_selection("observational_or_cohort_or_registry", ["STROBE"]),
        _guideline_selection("diagnostic_or_prognostic_model", ["TRIPOD", "TRIPOD-AI"]),
        _guideline_selection("randomized_or_intervention", ["CONSORT"]),
        _guideline_selection("systematic_review_or_meta_analysis", ["PRISMA"]),
        _guideline_selection("diagnostic_accuracy", ["STARD"]),
        _guideline_selection("case_report_or_case_series", ["CARE"]),
        _guideline_selection(
            "ai_ml_medical_study",
            ["AI/ML extension"],
            requires_clinical_base_guideline=True,
            clinical_base_guideline_options=CLINICAL_BASE_GUIDELINES,
        ),
    ]


def _guideline_selection(
    study_archetype: str,
    guideline_families: list[str],
    *,
    requires_clinical_base_guideline: bool = False,
    clinical_base_guideline_options: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "study_archetype": study_archetype,
        "guideline_families": list(guideline_families),
        "requires_clinical_base_guideline": requires_clinical_base_guideline,
        "clinical_base_guideline_options": list(clinical_base_guideline_options),
    }


def _ref(ref_kind: str, ref: str, role: str) -> dict[str, str]:
    return {"ref_kind": ref_kind, "ref": ref, "role": role}


def _clean_room_absorption() -> dict[str, object]:
    return {
        "source_project": "nature-skills",
        "absorbed_as": "mas_native_contract_pattern",
        "status_signal_consumed_as": "upstream_readme_status_only_not_mas_authority",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "publication_authority": False,
        "default_skill_source": False,
    }


def _promotion_evidence(pack_id: str) -> dict[str, object]:
    maturity_status = _PACK_MATURITY_STATUS[pack_id]
    stable_contract = maturity_status == "stable_contract"
    return {
        "maturity_model": "mas_contract_maturity_not_vendor_skill_status",
        "upstream_status_signal": _UPSTREAM_NATURE_STATUS_SIGNAL.get(pack_id, "not_applicable"),
        "stable_requires_strong_evidence": True,
        "strong_evidence_kinds": list(STRONG_PROMOTION_EVIDENCE_KINDS),
        "evidence": list(_PACK_PROMOTION_EVIDENCE[pack_id]),
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
        for evidence in _PACK_PROMOTION_EVIDENCE[pack_id]
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


def _journal_acceptance_evidence_fields(pack_id: str) -> list[dict[str, object]]:
    return [
        _field(field_id, role)
        for field_id, role in _JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS[pack_id]
    ]


def _journal_required_reviewer_output(pack_id: str) -> list[dict[str, object]]:
    return [
        {
            "output_id": output_id,
            "role": role,
            "required": True,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        }
        for output_id, role in _JOURNAL_REQUIRED_REVIEWER_OUTPUTS[pack_id]
    ]


def _journal_forbidden_authority() -> list[dict[str, object]]:
    return [
        {
            "authority_id": authority_id,
            "forbidden": True,
            "reason": reason,
        }
        for authority_id, reason in (
            ("vendor_skill_authority", "clean_room_pattern_only"),
            ("runtime_authority", "opl_descriptor_ref_locator_only"),
            ("default_skill_authority", "journal_pack_must_be_explicitly_consumed"),
            ("publication_readiness_authority", "mas_owner_receipt_or_reviewer_record_required"),
            ("quality_verdict_authority", "mas_quality_owner_closure_required"),
            ("mas_truth_write_authority", "pack_is_reviewer_rubric_not_truth_writer"),
        )
    ]


def _journal_quality_pack_consumption(pack_id: str) -> dict[str, object]:
    return {
        "consumer_roles": ["reviewer_agent", "auditor_agent"],
        "consumed_as": "explicit_quality_pack_descriptor",
        "required_contract_refs": [ref["ref"] for ref in _PACK_REQUIRED_REFS[pack_id]],
        "required_output_classes": [
            output_id for output_id, _role in _JOURNAL_REQUIRED_REVIEWER_OUTPUTS[pack_id]
        ],
        "opl_consumption_role": "descriptor_ref_freshness_locator_only",
        "opl_may_authorize_quality_verdict": False,
        "opl_may_authorize_publication_readiness": False,
        "opl_may_write_mas_truth": False,
    }


def _field(field_id: str, role: str) -> dict[str, object]:
    return {"field_id": field_id, "role": role, "required": True}


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
    "route_memory_pack": "Route memory pack",
    "stop_loss_pack": "Stop-loss pack",
    "artifact_freshness_pack": "Artifact freshness pack",
    "human_gate_pack": "Human gate pack",
}

_PACK_MATURITY_STATUS = {
    "ai_native_expert_judgment_pack": "stable_contract",
    "medical_claim_evidence_pack": "stable_contract",
    "statistical_analysis_pack": "stable_contract",
    "reporting_guideline_pack": "stable_contract",
    "display_to_claim_pack": "stable_contract",
    "journal_response_pack": "stable_contract",
    "data_availability_fair_pack": "stable_contract",
    "citation_integrity_pack": "stable_contract",
    "figure_evidence_contract_pack": "stable_contract",
    "paper_reader_grounding_pack": "stable_contract",
    "paper_presentation_pack": "beta_contract",
    "route_memory_pack": "stable_contract",
    "stop_loss_pack": "stable_contract",
    "artifact_freshness_pack": "stable_contract",
    "human_gate_pack": "stable_contract",
}

_UPSTREAM_NATURE_STATUS_SIGNAL = {
    "journal_response_pack": "draft_beta_stable_skill_status_pattern_learned",
    "data_availability_fair_pack": "draft_beta_stable_skill_status_pattern_learned",
    "citation_integrity_pack": "draft_beta_stable_skill_status_pattern_learned",
    "figure_evidence_contract_pack": "draft_beta_stable_skill_status_pattern_learned",
    "paper_reader_grounding_pack": "draft_beta_stable_skill_status_pattern_learned",
    "paper_presentation_pack": "draft_beta_stable_skill_status_pattern_learned",
}

_PACK_PROMOTION_EVIDENCE = {
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
        _ref("workspace_locator", "portfolio/data_assets", "data_asset_registry"),
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
    "route_memory_pack": [
        _ref("surface_kind", "stage_knowledge_packet", "route_memory_retrieval"),
        _ref("surface_kind", "memory_write_router_receipt", "route_memory_router"),
    ],
    "stop_loss_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "controller_decision"),
        _ref("surface_kind", "stop_loss_memo", "decision_owner"),
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
        _ref("workspace_locator", "portfolio/data_assets", "repository_identifier_source"),
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
    "route_memory_pack": [
        _ref("surface_kind", "stage_knowledge_packet", "required_memory_refs"),
        _ref("surface_kind", "stage_recall_index", "recall_projection"),
    ],
    "stop_loss_pack": [
        _ref("workspace_locator", "artifacts/controller_decisions/latest.json", "required_decision_refs"),
        _ref("surface_kind", "runtime_escalation_record", "escalation_context"),
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


__all__ = [
    "CLINICAL_BASE_GUIDELINES",
    "CONTRACT_REF",
    "JOURNAL_FAMILY_QUALITY_PACK_IDS",
    "PACK_ROLE",
    "PROJECTION_KIND",
    "QUALITY_PACK_CONTRACT_SURFACES",
    "REFRESH_POLICY",
    "REPO_PATH",
    "REQUIRED_STAGE_QUALITY_PACK_IDS",
    "STRONG_PROMOTION_EVIDENCE_KINDS",
    "SURFACE_KIND",
    "VERSION",
    "build_stage_quality_pack_contract",
    "build_stage_quality_pack_locator_projection",
    "build_stage_quality_pack_projection",
    "build_stage_quality_pack_ref_projection",
    "quality_pack_ids_for_stages",
]
