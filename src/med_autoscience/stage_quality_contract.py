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
    "medical_claim_evidence_pack",
    "statistical_analysis_pack",
    "reporting_guideline_pack",
    "display_to_claim_pack",
    "route_memory_pack",
    "stop_loss_pack",
    "artifact_freshness_pack",
    "human_gate_pack",
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
    "medical_claim_evidence_pack": ("write", "review", "finalize", "decision"),
    "statistical_analysis_pack": ("baseline", "experiment", "analysis-campaign"),
    "reporting_guideline_pack": ("write", "review", "finalize", "journal-resolution"),
    "display_to_claim_pack": ("analysis-campaign", "write", "review"),
    "route_memory_pack": ("scout", "idea", "analysis-campaign", "review", "decision"),
    "stop_loss_pack": ("idea", "baseline", "experiment", "analysis-campaign", "review", "decision"),
    "artifact_freshness_pack": ("write", "finalize", "delivery_sync"),
    "human_gate_pack": ("all_boundary_changing_stages",),
}

_PACK_STUDY_ARCHETYPE_MAP: dict[str, tuple[str, ...]] = {
    "medical_claim_evidence_pack": ("all_clinical_manuscripts",),
    "statistical_analysis_pack": (
        "observational_or_cohort_or_registry",
        "diagnostic_or_prognostic_model",
        "randomized_or_intervention",
        "diagnostic_accuracy",
        "survey_trend_analysis",
    ),
    "reporting_guideline_pack": REPORTING_STUDY_ARCHETYPES,
    "display_to_claim_pack": (
        "clinical_classifier",
        "clinical_subtype_reconstruction",
        "external_validation_model_update",
        "diagnostic_accuracy",
        "ai_ml_medical_study",
    ),
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


_PACK_TITLES = {
    "medical_claim_evidence_pack": "Medical claim evidence pack",
    "statistical_analysis_pack": "Statistical analysis pack",
    "reporting_guideline_pack": "Reporting guideline pack",
    "display_to_claim_pack": "Display to claim pack",
    "route_memory_pack": "Route memory pack",
    "stop_loss_pack": "Stop-loss pack",
    "artifact_freshness_pack": "Artifact freshness pack",
    "human_gate_pack": "Human gate pack",
}

_PACK_OWNER_REFS = {
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
    "display_to_claim_pack": [
        _ref("surface_kind", "display_contract", "display_owner"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_map"),
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
    "display_to_claim_pack": [
        _ref("surface_kind", "display_contract", "required_rubric"),
        _ref("workspace_locator", "paper/evidence/evidence_ledger.json", "claim_evidence_map"),
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


__all__ = [
    "CLINICAL_BASE_GUIDELINES",
    "CONTRACT_REF",
    "PACK_ROLE",
    "PROJECTION_KIND",
    "QUALITY_PACK_CONTRACT_SURFACES",
    "REFRESH_POLICY",
    "REPO_PATH",
    "REQUIRED_STAGE_QUALITY_PACK_IDS",
    "SURFACE_KIND",
    "VERSION",
    "build_stage_quality_pack_contract",
    "build_stage_quality_pack_locator_projection",
    "build_stage_quality_pack_projection",
    "build_stage_quality_pack_ref_projection",
    "quality_pack_ids_for_stages",
]
