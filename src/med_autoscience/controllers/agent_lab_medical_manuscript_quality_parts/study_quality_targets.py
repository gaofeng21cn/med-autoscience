from __future__ import annotations

from typing import Any


def study_quality_target_profile(*, study_id: str) -> dict[str, Any]:
    if study_id == "002-dm-china-us-mortality-attribution":
        return _prediction_model_external_validation_profile()
    if study_id == "003-dpcc-primary-care-phenotype-treatment-gap":
        return _observational_phenotype_treatment_gap_profile()
    if "obesity" in study_id:
        return _obesity_registry_descriptive_profile()
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
    if family == "obesity_registry_descriptive_phenotype_atlas":
        return {
            "quality_contract_ref": "quality_contract_ref:obesity_registry_descriptive_first_draft_quality",
            "scorer_ref": "scorer:mas/obesity-registry-descriptive-first-draft-quality",
            "regression_suite_ref": "regression-suite:mas/obesity-registry-descriptive-first-draft-quality",
            "required_patch_scope": "obesity_registry_descriptive_first_draft_quality_contract",
        }
    return {
        "quality_contract_ref": "quality_contract_ref:general_medical_manuscript_first_draft_quality",
        "scorer_ref": "scorer:mas/general-medical-manuscript-first-draft-quality",
        "regression_suite_ref": "regression-suite:mas/general-medical-manuscript-first-draft-quality",
        "required_patch_scope": "general_medical_manuscript_first_draft_quality_contract",
    }


def _obesity_registry_descriptive_profile() -> dict[str, Any]:
    return {
        "family": "obesity_registry_descriptive_phenotype_atlas",
        "blocker_ref_slugs": [
            "obesity-registry-descriptive-question-boundary",
            "reference-integrity-25-to-40-citations",
            "main-text-3500-word-floor",
            "clinical-value-result-figure-gap",
            "figure-polish-skill-consistency",
            "tables-and-figures-volume-floor",
            "internal-report-style-language-purge",
            "administrative-declaration-sections-required",
            "registry-data-lock-enrollment-boundary",
            "diagnostic-provenance-caveat-required",
            "figure-caption-content-consistency",
            "pdf-nonblank-figure-export-qc",
            "journal-figure-numbering-normalization",
            "wide-table-supplement-or-landscape-routing",
            "descriptive-atlas-discussion-theme-compression",
            "supplementary-missingness-atlas-required",
            "adult-bmi-sensitivity-table-required",
            "methods-registry-cohort-completeness",
            "results-phenotype-clinical-interpretability",
            "discussion-claim-guardrails",
        ],
        "targets": [
            {
                "target_id": "obesity_registry_descriptive_question_boundary",
                "requirement": (
                    "frame the paper as a descriptive obesity registry phenotype atlas, not a mechanism, "
                    "prediction, causal, or treatment-effect study"
                ),
                "route_target": "review",
            },
            {
                "target_id": "reference_integrity_25_to_40_citations",
                "requirement": (
                    "main manuscript contains a journal-rendered reference list with 25-40 relevant "
                    "medical citations and no uncited reference placeholders"
                ),
                "route_target": "publication-gate",
            },
            {
                "target_id": "main_text_3500_word_floor",
                "requirement": (
                    "main text reaches at least 3500 words of manuscript-facing scientific prose "
                    "without padding or internal process narration"
                ),
                "route_target": "write",
            },
            {
                "target_id": "clinical_value_result_figure_gap",
                "requirement": (
                    "Results include one or two additional clinically interpretable displays that connect "
                    "obesity phenotypes to comorbidity burden, severity gradient, treatment opportunity, "
                    "or care-delivery value within the evidence boundary"
                ),
                "route_target": "figure-polish",
            },
            {
                "target_id": "figure_polish_skill_consistency",
                "requirement": (
                    "all paper-facing figures are regenerated through the current figure-polish skill or "
                    "equivalent ScholarSkills display pack, with consistent style, legends, units, and refs"
                ),
                "route_target": "figure-polish",
            },
            {
                "target_id": "tables_and_figures_volume_floor",
                "requirement": (
                    "submission draft has a credible descriptive registry volume: at least two main tables, "
                    "three to five main figures or equivalent figure panels, and concise supplementary displays "
                    "when needed"
                ),
                "route_target": "write",
            },
            {
                "target_id": "internal_report_style_language_purge",
                "requirement": (
                    "remove internal-report language, process justification, MAS/AI reviewer/package wording, "
                    "repeated disclaimer lists, analytic/data-surface jargon, and defensive stage narration "
                    "from the manuscript body"
                ),
                "route_target": "write",
            },
            {
                "target_id": "administrative_declaration_sections_required",
                "requirement": (
                    "manuscript or submission package includes ethics approval and consent or waiver, "
                    "data availability, funding, and conflict-of-interest sections; unknown facts remain "
                    "owner-confirmation gates rather than invented text"
                ),
                "route_target": "publication-gate",
            },
            {
                "target_id": "registry_data_lock_enrollment_boundary",
                "requirement": (
                    "Methods distinguish observed visit-date coverage, formal registry enrollment period, "
                    "analytic release version, and analytic data-lock date without inferring missing owner metadata; "
                    "unconfirmed formal data-lock or enrollment facts must route to submission TODO or human gate "
                    "instead of remaining as placeholder manuscript-body prose"
                ),
                "route_target": "write",
            },
            {
                "target_id": "diagnostic_provenance_caveat_required",
                "requirement": (
                    "recorded diagnostic fields state available denominators and provenance limits, including "
                    "whether fields are diagnosis labels, laboratory thresholds, medications, imaging, PSG, "
                    "questionnaires, or history when that information is known"
                ),
                "route_target": "write",
            },
            {
                "target_id": "figure_caption_content_consistency",
                "requirement": (
                    "figure captions and visible display labels must match the rendered content; captions must "
                    "not mention domains such as sleep or psychobehavioral measures unless the figure actually displays them"
                ),
                "route_target": "figure-polish",
            },
            {
                "target_id": "pdf_nonblank_figure_export_qc",
                "requirement": (
                    "submission PDFs must pass page-level visual QC for every main figure panel, including a "
                    "nonblank rendered image region for late figures such as Figure 5 and Figure 6; compile success "
                    "or file existence alone is not enough"
                ),
                "route_target": "figure-polish",
            },
            {
                "target_id": "journal_figure_numbering_normalization",
                "requirement": (
                    "paper-facing figure headings and captions use journal numbering such as 'Figure 1. Title' "
                    "and must not retain double labels like 'F1 / Figure 1: F1'"
                ),
                "route_target": "write",
            },
            {
                "target_id": "wide_table_supplement_or_landscape_routing",
                "requirement": (
                    "wide variable-definition or ascertainment tables must be routed to supplementary material, "
                    "split, or landscape output when main-text PDF layout would force severe wrapping or overlap"
                ),
                "route_target": "publication-gate",
            },
            {
                "target_id": "descriptive_atlas_discussion_theme_compression",
                "requirement": (
                    "descriptive registry-atlas Discussion should synthesize findings into a small set of clinical "
                    "themes, typically registry structure, adult metabolic phenotype, and psychobehavioral subcohort, "
                    "rather than enumerating a long internal checklist of findings"
                ),
                "route_target": "review",
            },
            {
                "target_id": "supplementary_missingness_atlas_required",
                "requirement": (
                    "registry descriptive manuscripts include a materialized supplementary missingness atlas "
                    "or an explicit typed blocker explaining why variable-level availability cannot be reported"
                ),
                "route_target": "write",
            },
            {
                "target_id": "adult_bmi_sensitivity_table_required",
                "requirement": (
                    "obesity registry manuscripts with pediatric or age-missing records include an adult-known-age "
                    "BMI-category and diagnostic-denominator sensitivity table or a typed blocker explaining why "
                    "adult interpretation cannot be separated"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "methods_registry_cohort_completeness",
                "requirement": (
                    "Methods define registry source, study period, sites or centers, inclusion/exclusion, "
                    "obesity phenotype definitions, covariates, missingness, statistical summaries, and software"
                ),
                "route_target": "write",
            },
            {
                "target_id": "results_phenotype_clinical_interpretability",
                "requirement": (
                    "Results report denominators, obesity phenotype distributions, clinically meaningful "
                    "comparisons, comorbidity or care-pattern signals, and uncertainty or dispersion where supported"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "discussion_claim_guardrails",
                "requirement": (
                    "Discussion emphasizes descriptive registry insights, clinical context, and limitations "
                    "without inferring mechanisms, prediction utility, treatment efficacy, or causality"
                ),
                "route_target": "review",
            },
            *_shared_manuscript_quality_targets(),
        ],
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
            "structured-evidence-text-table-consistency",
            "claim-evidence-display-alignment-without-runtime-language",
            "ai-reviewer-record-current-manuscript-binding",
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
                "target_id": "structured_evidence_text_table_consistency",
                "requirement": (
                    "prediction-model manuscript text and main performance tables must be materialized from the same "
                    "structured validation evidence; if C-index, O:E, Brier, calibration intercept, calibration slope, "
                    "or their 95% CIs exist in the current evidence, Table 2 and Results must not report them as "
                    "unavailable or omit them"
                ),
                "route_target": "write",
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
                "target_id": "ai_reviewer_record_current_manuscript_binding",
                "requirement": (
                    "AI reviewer publication-eval records must be current against the manuscript they cite; "
                    "records predating current paper/draft.md or review_manuscript.md fail closed to record "
                    "production before publication_eval/latest.json can be refreshed"
                ),
                "route_target": "ai_reviewer",
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
            "structured-phenotype-pattern-service-priority-contrast",
            "medication-record-sensitivity-interpretation",
            "unsupported-temporal-visit-site-variance-gap",
            "figure-table-terminology-supplementary-retention",
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
                "target_id": "structured_phenotype_pattern_service_priority_contrast",
                "requirement": (
                    "promote descriptive phenotype counts into a structured phenotype pattern with rate-count "
                    "separation and service-priority contrast; otherwise route back before drafting a light atlas"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "medication_record_sensitivity_interpretation",
                "requirement": (
                    "interpret recorded medication gaps with medication-field-present or any-recorded-medication "
                    "sensitivity when records are incomplete, and retain documentation-sensitive claim guardrails"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "unsupported_temporal_visit_site_variance_gap",
                "requirement": (
                    "calendar-year, repeated-visit, and site-variance findings require current evidence; missing "
                    "support becomes an analysis-campaign gap, not manuscript Results prose"
                ),
                "route_target": "analysis-campaign",
            },
            {
                "target_id": "figure_table_terminology_supplementary_retention",
                "requirement": (
                    "Figure/Table terminology, rate versus count labels, main/supplementary placement, and retained "
                    "supplementary evidence are checked before quality-gate closeout"
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
                    "medical_prose_write_repair, DM002 methods-display-package repair, and manuscript-story "
                    "repairs must produce a canonical paper/draft.md or paper/build/review_manuscript.md delta; "
                    "ledger-only repair evidence "
                    "with manuscript_story_surface_delta_missing remains a typed blocker, while current "
                    "AI reviewer eval-bound manuscript surfaces must be preserved instead of overwritten "
                    "by deterministic templates"
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
                "requirement": (
                    "internal runtime, quality-control, repeated defensive disclaimer, and AI/data-engineering "
                    "language stay outside the manuscript body"
                ),
                "route_target": "write",
            },
            *_shared_manuscript_quality_targets(),
        ],
    }


def _shared_manuscript_quality_targets() -> list[dict[str, str]]:
    return [
        {
            "target_id": "owner_chain_authority_monotonicity",
            "requirement": (
                "owner-authorized writer handoffs are preserved or consumed monotonically; "
                "materializer and dispatcher must not downgrade them to supervisor inline dispatch"
            ),
            "route_target": "controller",
        },
        {
            "target_id": "quality_repair_writer_handoff_currentness",
            "requirement": (
                "quality_repair_batch writer handoffs remain bound to current owner request, "
                "work-unit id, source fingerprint, and owner-route currentness basis"
            ),
            "route_target": "write",
        },
        {
            "target_id": "publication_work_unit_registry_consistency",
            "requirement": (
                "publication route-back work units have one consistent owner, allowed surface, "
                "delta evidence, quality target, and Agent Lab regression classification"
            ),
            "route_target": "controller",
        },
        {
            "target_id": "story_surface_delta_or_typed_blocker",
            "requirement": (
                "story-surface repairs must produce canonical paper/draft.md or "
                "paper/build/review_manuscript.md delta, or return a typed blocker; "
                "ledger-only closeout cannot satisfy manuscript progress"
            ),
            "route_target": "write",
        },
        {
            "target_id": "stale_ai_reviewer_current_eval_drift",
            "requirement": (
                "AI reviewer and publication-eval projections must bind to current reviewer record, "
                "source eval id, manuscript digest, and work-unit currentness; stale eval drift routes "
                "to a current owner action or typed blocker"
            ),
            "route_target": "ai_reviewer",
        },
        {
            "target_id": "dead_letter_stabilizes_to_owner_blocker",
            "requirement": (
                "OPL retry or dead-letter outcomes are converted into MAS-owned owner receipt, "
                "stable typed blocker, human gate, or stop-loss route instead of becoming terminal silence"
            ),
            "route_target": "controller",
        },
        {
            "target_id": "macro_state_no_stale_live",
            "requirement": (
                "study_macro_state and user-visible progress must not project old active_run_id or "
                "provider attempt provenance as live without current OPL liveness proof"
            ),
            "route_target": "controller",
        },
        {
            "target_id": "medical_manuscript_no_runtime_language",
            "requirement": (
                "formal medical manuscript body excludes MAS, AI reviewer, QA, package, readiness, "
                "handoff, blocker, runtime, and other internal operating-system language"
            ),
            "route_target": "write",
        },
        {
            "target_id": "methods_results_numeric_reproducibility_floor",
            "requirement": (
                "Methods and Results include reproducible data definitions, sample sizes, event counts, "
                "estimates, uncertainty, and display-to-claim support before publication gate recheck"
            ),
            "route_target": "write",
        },
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
