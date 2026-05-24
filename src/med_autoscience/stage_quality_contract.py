from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from med_autoscience.stage_quality_contract_parts.pack_data import (
    _JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS,
    _JOURNAL_EXTENSION_CONTRACTS,
    _JOURNAL_FAMILY_PATTERNS,
    _JOURNAL_REQUIRED_REVIEWER_OUTPUTS,
    _PACK_OWNER_REFS,
    _PACK_REQUIRED_REFS,
    _PACK_TITLES,
    _REVIEWER_PRECOMMITMENT_PACK_IDS,
)
from med_autoscience.stage_quality_contract_parts.journal_currentness import (
    JOURNAL_POLICY_CURRENTNESS_PACKS,
    LITERATURE_SEARCH_SOURCE_PACKS,
    build_citation_verification_pack,
    build_journal_policy_currentness_pack,
    build_literature_search_source_pack,
)
from med_autoscience.stage_quality_contract_parts.maturity import (
    PACK_MATURITY_STATUS,
    STRONG_PROMOTION_EVIDENCE_KINDS,
    build_promotion_evidence,
)


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
        "data_access_ground_truth_isolation": _data_access_ground_truth_isolation(),
        "authority_boundary": _contract_authority_boundary(),
        "opl_projection_boundary": {
            "role": "descriptor_ref_freshness_locator_only",
            "allowed_fields": [
                "contract_ref",
                "pack_ids",
                "freshness",
                "pack_locators",
                "data_access_ground_truth_isolation",
                "authority_boundary",
            ],
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
        "data_access_ground_truth_isolation_ref": (
            "/product_entry_manifest/stage_quality_pack_contract/data_access_ground_truth_isolation"
        ),
        "data_access_levels": _data_access_level_ids(),
        "runtime_permission_authority": False,
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
        "data_access_ground_truth_isolation_ref": (
            "/product_entry_manifest/stage_quality_pack_contract/data_access_ground_truth_isolation"
        ),
        "data_access_levels": _data_access_level_ids(),
        "runtime_permission_authority": False,
        "opl_projection_boundary": "descriptor_ref_freshness_locator_only",
    }


def _build_pack(pack_id: str) -> dict[str, Any]:
    pack = {
        "pack_id": pack_id,
        "title": _PACK_TITLES[pack_id],
        "role": PACK_ROLE,
        "maturity_status": PACK_MATURITY_STATUS[pack_id],
        "promotion_evidence": build_promotion_evidence(pack_id),
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
    if pack_id in _REVIEWER_PRECOMMITMENT_PACK_IDS:
        pack["reviewer_precommitment_contract"] = _reviewer_precommitment_contract(pack_id)
    if pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack["journal_family_patterns"] = list(_JOURNAL_FAMILY_PATTERNS[pack_id])
        pack["clean_room_absorption"] = _clean_room_absorption()
        pack["acceptance_evidence_fields"] = _journal_acceptance_evidence_fields(pack_id)
        pack["required_reviewer_output"] = _journal_required_reviewer_output(pack_id)
        pack["forbidden_authority"] = _journal_forbidden_authority()
        pack["quality_pack_consumption"] = _journal_quality_pack_consumption(pack_id)
        if pack_id in _JOURNAL_EXTENSION_CONTRACTS:
            pack["extension_contracts"] = list(_JOURNAL_EXTENSION_CONTRACTS[pack_id])
    if pack_id in LITERATURE_SEARCH_SOURCE_PACKS:
        pack["literature_search_source_pack"] = build_literature_search_source_pack()
    if pack_id in JOURNAL_POLICY_CURRENTNESS_PACKS:
        pack["journal_policy_currentness_pack"] = build_journal_policy_currentness_pack()
    if pack_id == "citation_integrity_pack":
        pack["citation_verification_pack"] = build_citation_verification_pack()
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


def _reviewer_precommitment_contract(pack_id: str) -> dict[str, object]:
    return {
        "contract_id": f"{pack_id}.reviewer_precommitment_contract.v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_reviewer_precommitment_contract",
        "paper_blind_phase": {
            "phase_id": "paper_content_blind_precommitment",
            "allowed_inputs": ["quality_pack_descriptor", "paper_metadata_only"],
            "forbidden_inputs": [
                "paper_body",
                "manuscript_package",
                "publication_eval_verdict",
                "controller_decision_verdict",
            ],
            "expected_output_ref": "reviewer_precommitment_record",
        },
        "paper_visible_phase": {
            "phase_id": "paper_visible_review",
            "required_inputs": [
                "quality_pack_descriptor",
                "reviewer_precommitment_record",
                "verified_evidence_refs",
                "paper_or_artifact_under_review",
            ],
            "precommitment_record_must_be_reinjected": True,
            "may_rewrite_precommitment_after_viewing_paper": False,
        },
        "required_precommitment_outputs": [
            "contract_paraphrase",
            "scoring_plan",
            "contract_acknowledged_receipt",
        ],
        "required_runtime_inputs": [
            "quality_pack_descriptor",
            "paper_metadata_only",
            "reviewer_precommitment_record",
            "verified_evidence_refs",
            "paper_or_artifact_under_review",
        ],
        "separate_invocation_required": True,
        "rubric_may_authorize_quality_verdict": False,
        "rubric_may_write_truth": False,
    }


def _data_access_ground_truth_isolation() -> dict[str, object]:
    return {
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_stage_quality_data_access_descriptor",
        "descriptor_only": True,
        "runtime_permission_authority": False,
        "levels": [
            {
                "level_id": "raw_source_intake",
                "ars_data_access_level": "raw",
                "mas_scope": "source_intake_or_unverified_workspace_material",
                "may_feed_candidate_generation": True,
                "may_authorize_reviewer_verdict": False,
            },
            {
                "level_id": "verified_evidence_only",
                "ars_data_access_level": "verified_only",
                "mas_scope": "evidence_or_review_refs_after_integrity_gate",
                "may_feed_candidate_generation": True,
                "may_authorize_reviewer_verdict": False,
            },
            {
                "level_id": "reviewer_verdict_only",
                "ars_data_access_level": "verified_only",
                "mas_scope": "reviewer_or_auditor_verdict_record",
                "may_feed_candidate_generation": False,
                "may_authorize_reviewer_verdict": False,
            },
        ],
        "ground_truth_boundary": {
            "rubric_or_verdict_must_not_seed_candidate_generation": True,
            "reviewer_must_run_as_separate_invocation": True,
            "rubric_may_authorize_quality_verdict": False,
            "rubric_may_write_truth": False,
            "descriptor_grants_runtime_access": False,
        },
    }


def _data_access_level_ids() -> list[str]:
    return [
        str(item["level_id"])
        for item in _data_access_ground_truth_isolation()["levels"]
    ]


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
