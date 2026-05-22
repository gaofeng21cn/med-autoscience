from __future__ import annotations

from typing import Any


def study_quality_target_profile(*, study_id: str) -> dict[str, Any]:
    if study_id == "002-dm-china-us-mortality-attribution":
        return _prediction_model_external_validation_profile()
    if study_id == "003-dpcc-primary-care-phenotype-treatment-gap":
        return _observational_phenotype_treatment_gap_profile()
    return _general_high_quality_medical_manuscript_profile()


def study_quality_contract_profile(*, study_id: str) -> dict[str, str]:
    family = study_quality_target_profile(study_id=study_id)["family"]
    if family == "prediction_model_external_validation":
        return {
            "quality_contract_ref": "quality_contract_ref:prediction_model_first_draft_quality",
            "scorer_ref": "scorer:mas/prediction-model-first-draft-quality",
            "regression_suite_ref": "regression-suite:mas/prediction-model-first-draft-quality",
            "required_patch_scope": "prediction_model_first_draft_quality_contract",
        }
    if family == "observational_phenotype_treatment_gap":
        return {
            "quality_contract_ref": "quality_contract_ref:phenotype_treatment_gap_first_draft_quality",
            "scorer_ref": "scorer:mas/phenotype-treatment-gap-first-draft-quality",
            "regression_suite_ref": "regression-suite:mas/phenotype-treatment-gap-first-draft-quality",
            "required_patch_scope": "phenotype_treatment_gap_first_draft_quality_contract",
        }
    return {
        "quality_contract_ref": "quality_contract_ref:general_medical_manuscript_first_draft_quality",
        "scorer_ref": "scorer:mas/general-medical-manuscript-first-draft-quality",
        "regression_suite_ref": "regression-suite:mas/general-medical-manuscript-first-draft-quality",
        "required_patch_scope": "general_medical_manuscript_first_draft_quality_contract",
    }


def _prediction_model_external_validation_profile() -> dict[str, Any]:
    return {
        "family": "prediction_model_external_validation",
        "blocker_ref_slugs": [
            "hdl-harmonization-and-sensitivity",
            "model-reproducibility-and-baseline-survival",
            "table1-table2-visible-baseline-performance",
            "methods-reproducibility-complete-case-external-validation",
            "numeric-abstract-results-with-uncertainty",
            "uncertainty-intervals-and-validation-metrics",
            "nhanes-survey-weighting-and-unweighted-framing",
            "calibration-risk-collapse-and-figure-quality",
            "grouped-calibration-with-observed-rate-intervals",
            "claim-evidence-display-alignment-without-runtime-language",
            "internal-quality-language-purge",
        ],
        "targets": [
            {
                "target_id": "hdl_harmonization_and_sensitivity",
                "requirement": "HDL harmonization and sensitivity or typed blocker",
                "route_target": "analysis_harmonization_owner",
            },
            {
                "target_id": "model_reproducibility_and_baseline_survival",
                "requirement": "model reproducibility and baseline survival provenance",
                "route_target": "source_provenance_owner",
            },
            {
                "target_id": "visible_baseline_and_performance_tables",
                "requirement": "Table 1 and Table 2 visible baseline/performance reporting",
                "route_target": "write",
            },
            {
                "target_id": "methods_reproducibility_complete_case_external_validation",
                "requirement": (
                    "Methods state data sources, inclusion criteria, sample sizes, event counts, "
                    "predictor definitions, HDL conversion, complete-case handling, fixed Cox model, "
                    "validation strategy, bootstrap uncertainty, grouped calibration, and software versions"
                ),
                "route_target": "write",
            },
            {
                "target_id": "numeric_abstract_results_with_uncertainty",
                "requirement": (
                    "abstract reports sample sizes, event counts, discrimination, observed and predicted "
                    "5-year risks, O:E ratio, Brier score, and calibration estimates with supported 95% CIs"
                ),
                "route_target": "write",
            },
            {
                "target_id": "uncertainty_intervals_and_validation_metrics",
                "requirement": "uncertainty intervals and validation metrics",
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "nhanes_weighting_or_unweighted_framing",
                "requirement": "NHANES weighting or unweighted framing",
                "route_target": "statistical_owner",
            },
            {
                "target_id": "calibration_risk_collapse_figure_quality",
                "requirement": "calibration and risk-collapse figure quality",
                "route_target": "figure-polish",
            },
            {
                "target_id": "grouped_calibration_with_observed_rate_intervals",
                "requirement": (
                    "risk groups report observed event counts, observed rates with intervals, and mean "
                    "predicted risks without using grouped calibration as a readiness verdict"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "claim_evidence_display_alignment_without_runtime_language",
                "requirement": (
                    "claims, main text, tables, figures, and evidence ledger align around external-validation "
                    "metrics while excluding MAS, AI reviewer, package, readiness, and other runtime language"
                ),
                "route_target": "write",
            },
            {
                "target_id": "internal_quality_language_purge",
                "requirement": "internal quality-language purge",
                "route_target": "write",
            },
            *_shared_manuscript_quality_targets(),
        ],
    }


def _observational_phenotype_treatment_gap_profile() -> dict[str, Any]:
    return {
        "family": "observational_phenotype_treatment_gap",
        "blocker_ref_slugs": [
            "phenotype-derivation-transparency",
            "recorded-treatment-gap-terminology",
            "bp-and-data-quality-assessment",
            "baseline-characteristics-table",
            "formal-figures-and-tables",
            "numeric-abstract-results-with-uncertainty",
            "restrained-discussion-and-prose",
            "reference-and-journal-style",
            "claim-evidence-alignment-without-runtime-language",
            "route-back-for-method-or-data-errors",
            "medical-prose-write-repair-story-surface-delta",
        ],
        "targets": [
            {
                "target_id": "phenotype_derivation_transparency",
                "requirement": (
                    "define whether phenotypes are rule-based or model-derived, the domains/features, "
                    "thresholds or algorithm, class-count rationale, reproducible assignment path, "
                    "and prespecification or analysis-plan status"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "recorded_treatment_gap_terminology",
                "requirement": (
                    "use recorded medication-coverage or potential treatment-review gap language, "
                    "with numerator, denominator, eligibility, time window, data source, and non-causal guardrails"
                ),
                "route_target": "write",
            },
            {
                "target_id": "bp_and_data_quality_assessment",
                "requirement": (
                    "materialize BP semantic checks, plausibility filters, missingness, medication-record "
                    "limitations, and claim downgrade or sensitivity routing"
                ),
                "route_target": "analysis_harmonization_owner",
            },
            {
                "target_id": "baseline_characteristics_table",
                "requirement": (
                    "provide a true baseline characteristics table with total and phenotype columns, "
                    "denominators, missingness, units, clinical variables, and comparison or balance statistics"
                ),
                "route_target": "write",
            },
            {
                "target_id": "formal_figures_and_tables",
                "requirement": (
                    "make main figures and tables journal-facing displays, not proof-of-concept, "
                    "internal QA, or unsupported summary panels"
                ),
                "route_target": "figure-polish",
            },
            {
                "target_id": "numeric_abstract_results_with_uncertainty",
                "requirement": "abstract reports hard sample sizes, estimates, and uncertainty where supported",
                "route_target": "write",
            },
            {
                "target_id": "restrained_discussion_and_prose",
                "requirement": (
                    "discussion is result-driven, clinically contextualized, and non-defensive; "
                    "limitations are centralized rather than repeated through every section"
                ),
                "route_target": "review",
            },
            {
                "target_id": "reference_and_journal_style",
                "requirement": (
                    "render references in journal style with author order, journal title case, "
                    "and citation hygiene suitable for medical submission"
                ),
                "route_target": "publication-gate",
            },
            {
                "target_id": "claim_evidence_alignment_without_runtime_language",
                "requirement": (
                    "align every claim with evidence and remove MAS, AI reviewer, verified outputs, "
                    "source gaps, submission readiness, and other runtime/internal QA language from the manuscript body"
                ),
                "route_target": "write",
            },
            {
                "target_id": "route_back_for_method_or_data_errors",
                "requirement": (
                    "route true data-processing, harmonization, statistical, or phenotype-construction "
                    "errors to the matching study owner before prose polish or package refresh"
                ),
                "route_target": "controller",
            },
            {
                "target_id": "medical_prose_write_repair_requires_story_surface_delta",
                "requirement": (
                    "medical_prose_write_repair and manuscript-story repairs must produce a canonical "
                    "paper/draft.md or paper/build/review_manuscript.md delta; ledger-only repair evidence "
                    "with manuscript_story_surface_delta_missing remains a typed blocker"
                ),
                "route_target": "write",
            },
            *_shared_manuscript_quality_targets(),
        ],
    }


def _general_high_quality_medical_manuscript_profile() -> dict[str, Any]:
    return {
        "family": "general_high_quality_medical_manuscript",
        "blocker_ref_slugs": [
            "methods-reproducibility",
            "numeric-results-with-uncertainty",
            "formal-tables-and-figures",
            "claim-evidence-alignment",
            "internal-quality-language-purge",
        ],
        "targets": [
            {
                "target_id": "methods_reproducibility",
                "requirement": "methods are reproducible from current evidence and analysis surfaces",
                "route_target": "write",
            },
            {
                "target_id": "numeric_results_with_uncertainty",
                "requirement": "results include support counts, estimates, and uncertainty where applicable",
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "formal_tables_and_figures",
                "requirement": "main displays are publication-facing and linked to claims",
                "route_target": "figure-polish",
            },
            {
                "target_id": "claim_evidence_alignment",
                "requirement": "claims align with evidence, review ledger, and limitations",
                "route_target": "review",
            },
            {
                "target_id": "internal_quality_language_purge",
                "requirement": "internal runtime and quality-control language stays outside the manuscript body",
                "route_target": "write",
            },
            *_shared_manuscript_quality_targets(),
        ],
    }


def _shared_manuscript_quality_targets() -> list[dict[str, str]]:
    return [
        {
            "target_id": "controller_read_model_consumes_owner_typed_blockers",
            "requirement": "controller read-model consumes owner typed blockers without requeue loops",
            "route_target": "controller",
        },
        {
            "target_id": "ai_native_expert_judgment_first",
            "requirement": "AI-native expert judgment remains primary; contracts and rubrics only block below-floor gaps",
            "route_target": "ai_reviewer",
        },
        {
            "target_id": "cross_stage_vulnerability_scan",
            "requirement": (
                "cross-stage vulnerability scan traces reviewer feedback through review, analysis, "
                "write, figure, and publication gate"
            ),
            "route_target": "agent_lab",
        },
        {
            "target_id": "internal_error_history_excluded_from_paper_story",
            "requirement": "internal error and debug history stay in diagnostics or incident learning, not the paper main story",
            "route_target": "write",
        },
    ]
