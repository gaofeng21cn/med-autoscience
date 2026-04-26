from __future__ import annotations

from typing import Any

from med_autoscience.controllers.medical_reporting_guidelines import (
    build_guideline_quality_gate_expectation,
    build_reporting_guideline_expectation,
)


_OBSERVATIONAL_FAMILIES = frozenset(
    {
        "clinical_observation",
        "observational",
        "observational_study",
        "cohort_study",
        "case_control",
        "cross_sectional",
    }
)
_PREDICTION_FAMILIES = frozenset(
    {
        "prediction",
        "prediction_model",
        "validation",
        "model_validation",
        "prediction_validation",
        "ai_prediction_model",
        "ai_validation_model",
        "machine_learning_prediction_model",
    }
)
_AI_PREDICTION_FAMILIES = frozenset(
    {
        "ai_prediction_model",
        "ai_validation_model",
        "machine_learning_prediction_model",
    }
)
_TRIAL_FAMILIES = frozenset(
    {
        "trial",
        "clinical_trial",
        "randomized_trial",
        "randomised_trial",
        "ai_trial",
        "ai_randomized_trial",
    }
)
_AI_TRIAL_FAMILIES = frozenset({"ai_trial", "ai_randomized_trial"})
_SYSTEMATIC_REVIEW_FAMILIES = frozenset(
    {
        "systematic_review",
        "systematic_review_or_meta_analysis",
        "meta_analysis",
    }
)
_REAL_WORLD_DATA_FAMILIES = frozenset(
    {
        "real_world_data",
        "real_world_evidence",
        "rwd",
        "rwe",
        "registry_study",
        "ehr_cohort",
        "claims_database_study",
        "routinely_collected_health_data",
    }
)


def _token(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _uses_ai_guideline(
    *,
    study_archetype: str,
    manuscript_family: str,
    uses_ai: bool | None,
    ai_tokens: frozenset[str],
) -> bool:
    if uses_ai is not None:
        return bool(uses_ai)
    return study_archetype in ai_tokens or manuscript_family in ai_tokens


def _is_real_world_data(
    *,
    study_archetype: str,
    manuscript_family: str,
    real_world_data: bool | None,
) -> bool:
    if real_world_data is not None:
        return bool(real_world_data)
    return study_archetype in _REAL_WORLD_DATA_FAMILIES or manuscript_family in _REAL_WORLD_DATA_FAMILIES


def select_reporting_guideline_families(
    *,
    study_archetype: str | None,
    manuscript_family: str | None,
    uses_ai: bool | None = None,
    real_world_data: bool | None = None,
) -> dict[str, list[str] | str]:
    archetype = _token(study_archetype)
    family = _token(manuscript_family)

    if archetype in _SYSTEMATIC_REVIEW_FAMILIES or family in _SYSTEMATIC_REVIEW_FAMILIES:
        primary = "PRISMA"
    elif archetype in _TRIAL_FAMILIES or family in _TRIAL_FAMILIES:
        primary = (
            "CONSORT-AI"
            if _uses_ai_guideline(
                study_archetype=archetype,
                manuscript_family=family,
                uses_ai=uses_ai,
                ai_tokens=_AI_TRIAL_FAMILIES,
            )
            else "CONSORT"
        )
    elif archetype in _PREDICTION_FAMILIES or family in _PREDICTION_FAMILIES:
        primary = (
            "TRIPOD+AI"
            if _uses_ai_guideline(
                study_archetype=archetype,
                manuscript_family=family,
                uses_ai=uses_ai,
                ai_tokens=_AI_PREDICTION_FAMILIES,
            )
            else "TRIPOD"
        )
    elif archetype in _OBSERVATIONAL_FAMILIES or family in _OBSERVATIONAL_FAMILIES:
        primary = "STROBE"
    else:
        primary = "STROBE"

    overlays: list[str] = []
    if _is_real_world_data(
        study_archetype=archetype,
        manuscript_family=family,
        real_world_data=real_world_data,
    ):
        overlays.append("RECORD")
    return {
        "primary_guideline_family": primary,
        "overlay_guideline_families": overlays,
    }


def _authority_surfaces() -> dict[str, str]:
    return {
        "study_charter_owner": "study_charter.paper_quality_contract",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review_ledger.json",
        "publication_eval": "artifacts/publication_eval/latest.json",
        "reporting_guideline_checklist": "reporting_guideline_checklist.json",
    }


def _first_draft_quality_floor() -> dict[str, Any]:
    return {
        "required_before": "first_full_draft",
        "required_status": "closed",
        "gate_relaxation_allowed": False,
        "required_evidence": [
            "reporting_guideline_checklist_closed",
            "methods_and_population_accounting_closed",
            "table_figure_claim_map_closed",
            "evidence_ledger_claim_traceability_closed",
            "review_ledger_scientific_followup_closed",
        ],
    }


def _stronger_paper_shape_scan() -> dict[str, Any]:
    return {
        "status": "required_before_first_full_draft",
        "gate_relaxation_allowed": False,
        "required_axes": [
            "timepoint_or_temporal_depth",
            "stakeholder_or_role_contrast",
            "center_geography_or_site_coverage",
            "guideline_correspondence",
            "clinically_legible_subgroup_or_association_plan",
            "real_world_adoption_constraints",
        ],
        "route_back_when_stronger_shape_is_supported": "analysis-campaign",
        "claim_boundary": "no_new_primary_claims_without_human_gate",
    }


def _completion_claim_policy() -> dict[str, Any]:
    return {
        "mechanical_repair_complete_equals_scientific_quality_complete": False,
        "mechanical_repair_completion_claim": "mechanical_work_units_complete",
        "scientific_quality_completion_claim": "scientific_quality_complete_after_quality_gates_replayed_and_closed",
        "requires_closed_surfaces": list(_authority_surfaces().values()),
        "requires_successful_publication_gate_replay": True,
        "allows_completion_claim_without_review_ledger": False,
    }


def build_medical_quality_operating_system_contract(
    *,
    study_archetype: str | None,
    manuscript_family: str | None,
    uses_ai: bool | None = None,
    real_world_data: bool | None = None,
) -> dict[str, Any]:
    selection = select_reporting_guideline_families(
        study_archetype=study_archetype,
        manuscript_family=manuscript_family,
        uses_ai=uses_ai,
        real_world_data=real_world_data,
    )
    guideline_families = [
        str(selection["primary_guideline_family"]),
        *[str(item) for item in selection["overlay_guideline_families"]],
    ]
    return {
        "surface": "medical_quality_operating_system_contract",
        "schema_version": 1,
        "study_archetype": study_archetype,
        "manuscript_family": manuscript_family,
        "guideline_selection": {
            **selection,
            "guideline_families": guideline_families,
            "guideline_expectations": {
                family: build_reporting_guideline_expectation(family) for family in guideline_families
            },
            "quality_gate_expectations": {
                family: build_guideline_quality_gate_expectation(family) for family in guideline_families
            },
        },
        "quality_contract": {
            "owner": "study_charter",
            "owner_surface": "study_charter.paper_quality_contract",
            "gate_relaxation_allowed": False,
            "authority_surfaces": _authority_surfaces(),
            "evidence_ledger": {
                "surface": "paper/evidence_ledger.json",
                "required_status": "closed",
                "blocks_fast_lane_completion_when_open": True,
            },
            "review_ledger": {
                "surface": "paper/review_ledger.json",
                "required_status": "closed",
                "blocks_fast_lane_completion_when_open": True,
            },
            "publication_eval": {
                "surface": "artifacts/publication_eval/latest.json",
                "required_verdict": "not_blocked",
                "must_be_replayed_after_fast_lane": True,
            },
            "first_draft_quality_floor": _first_draft_quality_floor(),
            "stronger_paper_shape_scan": _stronger_paper_shape_scan(),
            "completion_claim_policy": _completion_claim_policy(),
        },
    }
