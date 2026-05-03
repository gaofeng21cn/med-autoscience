from __future__ import annotations

from typing import Any

from med_autoscience.controllers.medical_reporting_guidelines import (
    build_guideline_quality_gate_expectation,
    build_reporting_guideline_expectation,
)
from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
)
from med_autoscience.policies.medical_manuscript_draft_quality import (
    build_first_draft_manuscript_quality_contract,
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
        "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
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


def _automated_medical_paper_chain() -> dict[str, Any]:
    return {
        "claim": "medical_paper_as_governed_research_state_machine",
        "text_is_projection_not_authority": True,
        "gate_relaxation_allowed": False,
        "stable_components": [
            {
                "component_id": "mas_owner_truth",
                "why_it_matters": "the study line needs a durable objective and claim boundary before automation can continue",
                "authority_surface": "study_charter.paper_quality_contract",
            },
            {
                "component_id": "mds_controlled_backend",
                "why_it_matters": "long-running execution can be delegated without creating a second study owner",
                "authority_role": "controlled_backend_oracle_intake_buffer",
            },
            {
                "component_id": "durable_evidence_truth",
                "why_it_matters": "claims, evidence, review concerns, and next actions must survive chat/session loss",
                "authority_surfaces": [
                    "paper/evidence_ledger.json",
                    "paper/review_ledger.json",
                    "artifacts/publication_eval/latest.json",
                    "artifacts/controller_decisions/latest.json",
                ],
            },
            {
                "component_id": "ai_reviewer_quality_authority",
                "why_it_matters": "scientific and prose quality are judgment tasks, not mechanical completion states",
                "required_provenance": {
                    "assessment_owner": "ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
            },
            {
                "component_id": "canonical_source_first_artifact_authority",
                "why_it_matters": "submission-facing files must be reproducible projections, not manual patch roots",
                "derived_surfaces_not_authority": [
                    "manuscript/current_package/",
                    "submission_minimal/",
                    "artifacts/final/",
                ],
            },
        ],
        "upstream_judgment_gap": {
            "problem": "research_creativity_and_route_choice_are_less_stable_than_governance",
            "must_strengthen": [
                "literature_understanding",
                "study_line_selection",
                "analysis_design_discipline",
                "stop_loss_reasoning",
                "target_journal_writing_fit",
            ],
        },
    }


def _evidence_over_claims_gate() -> dict[str, Any]:
    return {
        "policy_id": "mas_evidence_over_claims_v1",
        "claim_only_ready_allowed": False,
        "ready_verbs_require_authority_refs": True,
        "required_refs": [
            "study_charter.paper_quality_contract",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
            "paper/medical_manuscript_blueprint.json",
            "artifacts/publication_eval/medical_prose_review.json",
            "artifacts/publication_eval/latest.json",
            "artifacts/controller_decisions/latest.json",
        ],
        "ai_reviewer_publication_eval": {
            "required_for": [
                "reviewer_first_ready",
                "finalize_ready",
                "submission_facing_quality_closure",
            ],
            "mechanical_projection_allowed_verdicts": ["review_required", "projection_only"],
            "mechanical_projection_can_authorize_quality": False,
            "reviewer_operating_system_contract": "medical_publication_ai_reviewer_os_v1",
        },
        "ai_first_subjective_quality": {
            "authority_owner": "ai_reviewer",
            "required_dimensions": [
                "medical_journal_prose_quality",
                "clinical_significance",
                "claim_restraint",
                "reader_flow",
            ],
            "mechanical_pattern_role": "evidence_snippets_only",
        },
        "forbidden_authority_sources": [
            "chat_summary",
            "terminal_prose",
            "memory_only",
            "generic_persona_approval",
            "non_medical_qa_label",
            "screenshot_style_qa",
        ],
    }


def _quality_preserving_fast_lane_policy() -> dict[str, Any]:
    return {
        "policy_id": "mas_quality_preserving_fast_lane_v1",
        "gate_relaxation_allowed": False,
        "allowed_parallelism": [
            "independent_read_projection",
            "bounded_analysis_unit",
            "replayable_repair_unit",
            "artifact_inventory_refresh",
        ],
        "forbidden_shortcuts": [
            "skip_publication_eval",
            "skip_evidence_ledger",
            "skip_review_ledger",
            "claim_only_ready",
            "mechanical_projection_as_ai_reviewer",
        ],
        "must_replay_after": [
            "publication_gate",
            "quality_closure_truth",
            "study_progress_projection",
        ],
    }


def _statistical_disciplines() -> list[dict[str, Any]]:
    return [
        {
            "discipline_id": "missingness",
            "why": "missingness changes the analyzed population and can reverse bias direction",
            "required_record": [
                "missingness_mechanism_assumption",
                "handling_method",
                "complete_case_or_imputation_rationale",
                "sensitivity_analysis",
            ],
            "prevents": ["biased_cohort_interpretation", "inflated_model_performance"],
        },
        {
            "discipline_id": "sample_size_precision",
            "why": "medical claims need support from event counts, precision, or feasibility rationale, not significance alone",
            "required_record": [
                "sample_size_or_event_count",
                "precision_or_confidence_interval",
                "model_degrees_of_freedom_or_parameter_budget",
                "power_precision_or_feasibility_rationale",
            ],
            "prevents": ["overclaiming_underpowered_results", "p_value_only_evidence"],
        },
        {
            "discipline_id": "external_validation",
            "why": "external validation separates local cohort findings from transportable medical conclusions",
            "required_record": [
                "validation_dataset_or_reason_unavailable",
                "population_shift_assessment",
                "performance_or_effect_transportability",
                "claim_downgrade_when_absent",
            ],
            "prevents": ["single_cohort_generalization", "unqualified_model_claims"],
        },
        {
            "discipline_id": "subgroup_analysis",
            "why": "subgroups improve clinical interpretation only when tied to clinical rationale and multiplicity guardrails",
            "required_record": [
                "predeclared_or_clinically_justified_subgroups",
                "interaction_or_heterogeneity_test",
                "multiplicity_guardrail",
                "exploratory_label_when_post_hoc",
            ],
            "prevents": ["post_hoc_subgroup_storytelling", "nominal_difference_as_core_claim"],
        },
        {
            "discipline_id": "multiplicity",
            "why": "automated analysis can create many nominal findings unless primary, secondary, and exploratory claims are separated",
            "required_record": [
                "primary_secondary_exploratory_labels",
                "family_of_tests",
                "adjustment_or_hierarchy_rationale",
                "hypothesis_generating_limitations",
            ],
            "prevents": ["multiple_testing_false_discovery", "exploratory_result_as_confirmatory"],
        },
        {
            "discipline_id": "clinical_utility",
            "why": "statistical separation is not enough unless the result can change a clinical decision, workflow, or interpretation",
            "required_record": [
                "decision_curve_or_threshold_net_benefit",
                "calibration_or_threshold_performance",
                "workflow_or_resource_use_implication",
                "clinical_interpretability_statement",
            ],
            "forbidden_shortcuts": ["AUC_or_p_value_alone_is_not_clinical_value"],
            "prevents": ["metric_only_publication_claim", "unclear_clinical_use_case"],
        },
        {
            "discipline_id": "endpoint_time_window",
            "why": "endpoint definition and prediction or exposure time window define the clinical question itself",
            "required_record": [
                "endpoint_definition",
                "index_time",
                "prediction_or_followup_horizon",
                "clinical_use_timing",
            ],
            "prevents": ["ambiguous_clinical_question", "time_leakage_or_misplaced_use_case"],
        },
        {
            "discipline_id": "sensitivity_robustness",
            "why": "main findings should survive plausible cohort, missingness, outlier, model, or competing-explanation pressure",
            "required_record": [
                "cohort_definition_sensitivity",
                "missingness_or_outlier_sensitivity",
                "model_specification_sensitivity",
                "competing_explanation_check",
            ],
            "prevents": ["fragile_primary_claim", "unexamined_alternative_explanation"],
        },
    ]


def _archetype_requirements() -> dict[str, list[str]]:
    return {
        "clinical_classifier": [
            "discrimination",
            "calibration",
            "decision_curve_or_net_benefit",
            "subgroup_performance",
            "interpretability",
            "external_validation_or_claim_downgrade",
        ],
        "clinical_subtype_reconstruction": [
            "subtype_stability",
            "between_subtype_clinical_difference",
            "prognosis_or_treatment_response_contrast",
            "subtype_identifier",
            "clinical_interpretability",
        ],
        "external_validation_model_update": [
            "original_model_reconstruction",
            "external_performance",
            "recalibration_or_model_update",
            "case_mix_shift",
            "transportability_limitations",
        ],
        "gray_zone_triage": [
            "rule_out_threshold",
            "rule_in_threshold",
            "gray_zone_accounting",
            "safety_tradeoff",
            "resource_use_implication",
        ],
        "llm_agent_clinical_task": [
            "task_definition",
            "baseline_comparison",
            "case_level_error_taxonomy",
            "subgroup_or_scenario_performance",
            "clinical_safety_boundary",
        ],
        "mechanistic_sidecar_extension": [
            "main_clinical_route_linkage",
            "pathway_or_functional_support",
            "public_data_support",
            "mechanism_claim_restraint",
        ],
    }


def _archetype_analysis_contract() -> dict[str, Any]:
    return {
        "surface": "archetype_specific_analysis_contract",
        "required_before": "analysis-campaign",
        "gate_relaxation_allowed": False,
        "analysis_is_not_work_volume": "each analysis must close a claim, reviewer concern, or publication gate blocker",
        "statistical_disciplines": _statistical_disciplines(),
        "archetype_requirements": _archetype_requirements(),
    }


def _bounded_analysis_decision_contract() -> dict[str, Any]:
    return {
        "surface": "bounded_analysis_decision_contract",
        "route_meanings": ["explore", "exploit", "fusion", "debug", "stop"],
        "candidate_board_required_fields": [
            "candidate_id",
            "route_meaning",
            "target_claim_or_concern",
            "expected_evidence_gain",
            "cost_and_risk",
            "clinical_interpretability",
            "decision",
            "decision_reason",
        ],
        "plateau_stop_triggers": [
            "new_analysis_repeats_existing_result",
            "evidence_gain_cannot_close_claim_or_reviewer_concern",
            "analysis_would_break_study_charter_or_data_permission",
            "claim_requires_post_hoc_storytelling",
        ],
        "stop_loss_memo": {
            "required_when": [
                "publication_eval_overall_verdict_weak_or_blocked",
                "stop_loss_pressure_high",
                "bounded_analysis_plateau",
            ],
            "required_fields": [
                "attempted_paths",
                "failure_reason",
                "evidence_gain_ceiling",
                "continuation_cost_and_risk",
                "alternative_routes",
                "human_gate_question",
            ],
        },
    }


def build_quality_os_runtime_materialization_contract() -> dict[str, Any]:
    return {
        "surface": "quality_os_runtime_materialization_contract",
        "schema_version": 1,
        "default_verdict_when_unclosed": "NEEDS_REVIEW",
        "runtime_surfaces": {
            "pre_draft_readiness": "paper/pre_draft_writing_readiness.json",
            "ai_review_ledger": "paper/review_ledger.json",
            "publication_eval": "artifacts/publication_eval/latest.json",
            "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
            "controller_decision": "artifacts/controller_decisions/latest.json",
        },
        "mechanical_gate_output_contract": {
            "allowed_output_kinds": ["completeness", "evidence", "blocker", "projection"],
            "forbidden_output_kinds": [
                "ready_authorization",
                "quality_closure",
                "submission_authorization",
            ],
            "mechanical_projection_can_authorize_ready": False,
        },
        "default_flow": {
            "write": {
                "required_before": "first_full_draft",
                "required_runtime_surface": "paper/pre_draft_writing_readiness.json",
                "required_status": "closed",
                "must_read": [
                    "study_charter.paper_quality_contract",
                    "paper/evidence_ledger.json",
                    "paper/review_ledger.json",
                    "paper/medical_manuscript_blueprint.json",
                    "artifacts/publication_eval/latest.json",
                ],
                "fail_closed_when_missing": "route_back_required",
                "ai_reviewer_provenance_required": True,
                "mechanical_gate_can_authorize_ready": False,
            },
            "revise": {
                "required_runtime_surface": "paper/review_ledger.json",
                "route_back_required": True,
                "route_back_trace_fields": [
                    "finding_refs",
                    "affected_claim_refs",
                    "fix_refs",
                    "acceptance_criteria",
                    "next_route",
                ],
                "fail_closed_when_route_back_missing": "review_ledger_route_back_required",
            },
            "finalize": {
                "requires_ai_reviewer_provenance": True,
                "required_provenance": {
                    "assessment_owner": "ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "required_runtime_surfaces": [
                    "artifacts/publication_eval/latest.json",
                    "artifacts/publication_eval/medical_prose_review.json",
                    "paper/review_ledger.json",
                ],
                "fail_closed_when_missing_provenance": "review_required",
                "mechanical_gate_can_authorize_ready": False,
            },
            "submission": {
                "requires_ai_reviewer_provenance": True,
                "required_provenance": {
                    "assessment_owner": "ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                },
                "required_runtime_surfaces": [
                    "artifacts/publication_eval/latest.json",
                    "artifacts/publication_eval/medical_prose_review.json",
                    "paper/review_ledger.json",
                ],
                "fail_closed_when_missing_provenance": "review_required",
                "mechanical_gate_can_authorize_ready": False,
            },
        },
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
    primary_guideline_family = str(selection["primary_guideline_family"])
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
            "automated_medical_paper_chain": _automated_medical_paper_chain(),
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
                "must_be_ai_reviewer_backed_for_quality_closure": True,
                "must_be_replayed_after_fast_lane": True,
                "required_reviewer_operating_system_contract": "medical_publication_ai_reviewer_os_v1",
            },
            "ai_reviewer_operating_system": build_ai_reviewer_operating_system_contract(
                DEFAULT_PUBLICATION_CRITIQUE_POLICY
            ),
            "evidence_over_claims_gate": _evidence_over_claims_gate(),
            "quality_preserving_fast_lane_policy": _quality_preserving_fast_lane_policy(),
            "first_draft_quality_floor": _first_draft_quality_floor(),
            "first_draft_manuscript_quality_contract": build_first_draft_manuscript_quality_contract(
                guideline_family=primary_guideline_family,
                manuscript_family=manuscript_family,
            ),
            "archetype_analysis_contract": _archetype_analysis_contract(),
            "bounded_analysis_decision_contract": _bounded_analysis_decision_contract(),
            "stronger_paper_shape_scan": _stronger_paper_shape_scan(),
            "completion_claim_policy": _completion_claim_policy(),
            "quality_runtime_materialization": build_quality_os_runtime_materialization_contract(),
        },
    }
