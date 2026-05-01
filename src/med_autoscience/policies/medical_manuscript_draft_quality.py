from __future__ import annotations

import re
from typing import Any


FORBIDDEN_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("deployment-facing", "deployment-facing", r"\bdeployment-facing\b", re.IGNORECASE),
    ("baseline-comparable", "baseline-comparable", r"\bbaseline-comparable\b", re.IGNORECASE),
    ("locked study freeze", "locked study freeze", r"\blocked study freeze\b", re.IGNORECASE),
    ("locked cohort", "locked cohort", r"\blocked cohort\b", re.IGNORECASE),
    ("locked comparison", "locked comparison", r"\blocked comparison\b", re.IGNORECASE),
    ("locked validation", "locked validation", r"\blocked validation\b", re.IGNORECASE),
    ("locked probability", "locked probability", r"\blocked probability\b", re.IGNORECASE),
    ("contract", "contract", r"\bcontract\b", re.IGNORECASE),
    ("analysis surface", "analysis surface", r"\banalysis surface\b", re.IGNORECASE),
    ("study surface", "study surface", r"\bstudy surface\b", re.IGNORECASE),
    ("predictor surface", "predictor surface", r"\bpredictor surfaces?\b", re.IGNORECASE),
    ("validation surface", "validation surface", r"\bvalidation surface\b", re.IGNORECASE),
    ("paper-facing", "paper-facing", r"\bpaper-facing\b", re.IGNORECASE),
    ("frontier", "frontier", r"\bfrontier\b", re.IGNORECASE),
    ("mainline", "mainline", r"\bmainline\b", re.IGNORECASE),
    ("sidecar", "sidecar", r"\bsidecar\b", re.IGNORECASE),
    ("endpoint-alignment evidence", "endpoint-alignment evidence", r"\bendpoint[\s-]+alignment evidence\b", re.IGNORECASE),
    ("control endpoint", "control endpoint", r"\bcontrol endpoint\b", re.IGNORECASE),
    ("limitation-aware", "limitation-aware", r"\blimitation-aware\b", re.IGNORECASE),
    ("post-gate", "post-gate", r"\bpost-gate\b", re.IGNORECASE),
    ("frozen analysis outputs", "frozen analysis outputs", r"\bfrozen analysis outputs?\b", re.IGNORECASE),
    ("supportive endpoint", "supportive endpoint", r"\bsupportive endpoint\b", re.IGNORECASE),
    (
        "manuscript provenance and reporting boundary",
        "Manuscript provenance and reporting boundary",
        r"\bmanuscript provenance and reporting boundary\b",
        re.IGNORECASE,
    ),
    ("this manuscript should be read as", "This manuscript should be read as", r"\bthis manuscript should be read as\b", re.IGNORECASE),
    ("Clinical Utility Model", "Clinical Utility Model", r"\bClinical Utility Model\b", 0),
    ("Preoperative Core Model", "Preoperative Core Model", r"\bPreoperative Core Model\b", 0),
    ("Pathology-Augmented Model", "Pathology-Augmented Model", r"\bPathology-Augmented Model\b", 0),
    ("Elastic-Net Benchmark", "Elastic-Net Benchmark", r"\bElastic-Net Benchmark\b", 0),
    ("Random-Forest Benchmark", "Random-Forest Benchmark", r"\bRandom-Forest Benchmark\b", 0),
    ("roc_auc", "roc_auc", r"\broc_auc\b", re.IGNORECASE),
    ("average_precision", "average_precision", r"\baverage_precision\b", re.IGNORECASE),
    ("brier_score", "brier_score", r"\bbrier_score\b", re.IGNORECASE),
    ("calibration_intercept", "calibration_intercept", r"\bcalibration_intercept\b", re.IGNORECASE),
    ("calibration_slope", "calibration_slope", r"\bcalibration_slope\b", re.IGNORECASE),
    ("open-source disclosure", "open-source:", r"\bopen-source:\s*https?://\S+", re.IGNORECASE),
    ("online service disclosure", "online service:", r"\bonline service:\s*https?://\S+", re.IGNORECASE),
    ("deepscientist", "deepscientist", r"\bdeepscientist\b", re.IGNORECASE),
    ("poster sources label", "Sources:", r"\bSources:", re.IGNORECASE),
    ("poster why-this-matters label", "Why this matters", r"\bWhy this matters\b", re.IGNORECASE),
    ("comparison framework", "comparison framework", r"\bcomparison framework\b", re.IGNORECASE),
    ("model surface", "model surface", r"\bmodel surfaces?\b", re.IGNORECASE),
    ("version label", "v2026-03-28", r"\bv\d{4}-\d{2}-\d{2}\b", re.IGNORECASE),
    ("internal model code", "A1", r"\b(?:A\d|B\d|M\d(?:_[A-Za-z0-9]+)?)\b", 0),
]

RESULTS_NARRATION_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("figure shows", "Figure 1 shows", r"\bFigure\s+\d+[A-Za-z]?\s+shows\b", re.IGNORECASE),
    ("figure illustrates", "Figure 1 illustrates", r"\bFigure\s+\d+[A-Za-z]?\s+illustrates\b", re.IGNORECASE),
    ("figure demonstrates", "Figure 1 demonstrates", r"\bFigure\s+\d+[A-Za-z]?\s+demonstrates\b", re.IGNORECASE),
    ("table shows", "Table 1 shows", r"\bTable\s+\d+[A-Za-z]?\s+shows\b", re.IGNORECASE),
    ("table summarizes", "Table 1 summarizes", r"\bTable\s+\d+[A-Za-z]?\s+summarizes\b", re.IGNORECASE),
    ("table presents", "Table 1 presents", r"\bTable\s+\d+[A-Za-z]?\s+presents\b", re.IGNORECASE),
]

ANALYSIS_PLANE_JARGON_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("support_mismatch", "support mismatch", r"\bsupport mismatch\b", re.IGNORECASE),
    ("risk_compression", "risk compression", r"\brisk(?:[\s-]+scale)? compression\b", re.IGNORECASE),
    ("self_quantile", "self-quantile", r"\bself[\s-]+quantile\b", re.IGNORECASE),
    ("one_bin_collapse", "one-bin collapse", r"\bone[\s-]+bin collapse\b", re.IGNORECASE),
    ("contextual_layer", "contextual layer", r"\bcontextual layer\b", re.IGNORECASE),
    ("analysis_slice", "analysis slice", r"\banalysis slice\b", re.IGNORECASE),
    ("transportability_surface", "transportability surface", r"\btransportability surface\b", re.IGNORECASE),
    ("residual_ordering_signal", "residual ordering signal", r"\bresidual ordering signal\b", re.IGNORECASE),
    ("claim_boundary_surface", "claim boundary", r"\bclaim boundary\b", re.IGNORECASE),
]

WORK_REPORT_RESIDUE_PATTERN_IDS = frozenset(
    {
        "work_report_question_answer_frame",
        "manuscript_self_description_residue",
        "figure_table_anchor_section_residue",
        "figure_legend_work_report_residue",
        "submission_placeholder_instruction_residue",
        "paper_scaffold_role_residue",
    }
)

PUBLICATION_SURFACE_RESIDUE_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    (
        "work_report_question_answer_frame",
        "The first clinical question was / the answer was",
        r"\b(?:first|second|third|final)\s+clinical question\b|\bthe answer was\b",
        re.IGNORECASE,
    ),
    (
        "manuscript_self_description_residue",
        "the manuscript remains / this manuscript should",
        r"\bthe manuscript remains\b|\bthis manuscript should\b",
        re.IGNORECASE,
    ),
    ("figure_table_anchor_section_residue", "Figure and Table Anchors", r"^\s*#{0,6}\s*Figure and Table Anchors\s*$", re.IGNORECASE | re.MULTILINE),
    (
        "figure_legend_work_report_residue",
        "This figure defines / Reviewers can identify",
        r"\bReviewers can identify\b|\bThis (?:figure|illustration) (?:defines|supports)\b",
        re.IGNORECASE,
    ),
    (
        "submission_placeholder_instruction_residue",
        "not yet been confirmed / Replace this placeholder",
        r"\bnot yet been confirmed\b|\bReplace this placeholder\b|\bInsert the author-confirmed\b|\bverify the exact wording\b|\bshould be replaced\b",
        re.IGNORECASE,
    ),
    ("paper_scaffold_role_residue", "paper protagonist / bounded complexity benchmark", r"\bpaper protagonist\b|\bbounded complexity benchmark\b|\bmodel-complexity competition\b", re.IGNORECASE),
    ("residual_hypopituitarism_endpoint_label", "later persistent global hypopituitarism", r"\blater persistent global hypopituitarism\b", re.IGNORECASE),
    (
        "process_instruction_reaudit_methods",
        "Keep ... re-audit ... methods",
        r"\bKeep\b.{0,180}\bre-audit\b.{0,120}\bmethods\b",
        re.IGNORECASE,
    ),
    ("confirmed_historical_specification_residue", "confirmed historical specification", r"\bconfirmed historical specification\b", re.IGNORECASE),
    ("manuscript_facing_analyses_residue", "manuscript-facing analyses", r"\bmanuscript-facing analyses\b", re.IGNORECASE),
    ("comparator_drift_residue", "comparator drift", r"\bcomparator drift\b", re.IGNORECASE),
]

METHOD_LABEL_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    ("knowledge-guided", "knowledge-guided", r"\bknowledge-guided\b", re.IGNORECASE),
    ("causal", "causal", r"\bcausal\b", re.IGNORECASE),
    ("mechanistic", "mechanistic", r"\bmechanistic\b", re.IGNORECASE),
    ("calibration-first", "calibration-first", r"\bcalibration-first\b", re.IGNORECASE),
]

MEDICAL_JOURNAL_PROSE_PATTERN_SPECS: list[tuple[str, str, str, int]] = [
    (
        "figure_table_subject_results_sentence",
        "Figure/Table as Results sentence subject",
        r"\b(?:Figure|Table)\s+\d+[A-Za-z]?\s+(?:shows|summarizes|presents|demonstrates|illustrates)\b",
        re.IGNORECASE,
    ),
    (
        "unsupported_no_difference_claim",
        "unsupported no difference/no association claim",
        r"\b(?:there\s+was|there\s+were|we\s+found|the\s+analysis\s+found)\s+no\s+(?:statistically\s+significant\s+)?(?:difference|association|relationship)\b",
        re.IGNORECASE,
    ),
    (
        "overstated_best_or_novelty_claim",
        "best/novel without explicit support",
        r"\bbest\s+model\s+for\s+clinical\s+use\b|\b(?:the\s+)?(?:best|first|novel|unique|unprecedented|state-of-the-art)\s+(?:study|model|analysis|method|tool|approach)\b",
        re.IGNORECASE,
    ),
    (
        "project_status_report_opening",
        "project/status-report prose",
        r"\b(?:this project has completed|current package|current bundle|submission tasks|controller-approved|writing route continued|outputs were synchronized)\b",
        re.IGNORECASE,
    ),
    (
        "controller_artifact_subject",
        "controller/artifact as manuscript subject",
        r"\b(?:controller checklist|controller|analysis surface|claim boundary surface|run logs?|packaging metadata|paper bundle)\b",
        re.IGNORECASE,
    ),
    (
        "tool_runtime_provenance_body",
        "tool/runtime provenance in manuscript body",
        r"\b(?:quest|worktree|run logs?|packaging metadata|current package)\b|\b(?:pipeline|artifact)s?\s+(?:completed|generated|synchronized|refreshed)\b",
        re.IGNORECASE,
    ),
    (
        "weak_success_language",
        "worked well / ready for review",
        r"\b(?:worked well|ready for review|good performance|performed well)\b",
        re.IGNORECASE,
    ),
]

SOURCE_BASIS = (
    {
        "authority": "ICMJE Recommendations",
        "url": "https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html",
        "role": "IMRAD manuscript structure and section-purpose baseline",
    },
    {
        "authority": "EQUATOR Network",
        "url": "https://www.equator-network.org/",
        "role": "reporting-guideline selection before drafting",
    },
    {
        "authority": "TRIPOD / TRIPOD+AI",
        "url": "https://www.tripod-statement.org/",
        "role": "prediction-model manuscript reporting contract",
    },
    {
        "authority": "STROBE Statement",
        "url": "https://www.strobe-statement.org/",
        "role": "observational-study manuscript reporting contract",
    },
)

PROSE_STYLE_SOURCE_BASIS = (
    "Zeiger biomedical research paper writing",
    "JAMA editors precision and concrete wording",
    "Gopen and Swan reader expectation model",
    "general medical journal original research exemplars",
)


def build_medical_prose_style_contract() -> dict[str, Any]:
    return {
        "style_profile_id": "general_medical_journal_prose_v1",
        "target_voice": "neutral_clinical_original_research",
        "target_readers": ["clinician_researcher", "statistical_reviewer", "journal_editor"],
        "introduction_rhetoric": {
            "paragraph_sequence": [
                "clinical_problem_to_evidence_gap_to_objective",
                "why_the_gap_matters_for_patients_or_clinicians",
                "present_study_objective_and_contribution",
            ],
            "forbidden_openings": [
                "project_status_report",
                "pipeline_progress_summary",
                "generic_disease_burden_without_study_gap",
            ],
        },
        "sentence_information_flow": {
            "required_patterns": [
                "old_to_new_information_flow",
                "known_context_before_new_claim",
                "stress_position_contains_finding_or_boundary",
            ],
            "forbidden_patterns": [
                "controller_term_as_topic",
                "file_or_artifact_as_topic",
                "chronological_execution_log_flow",
            ],
        },
        "results_prose": {
            "required_patterns": [
                "clinical_finding_as_sentence_subject",
                "quantitative_result_before_display_citation",
                "clinical_meaning_after_metric_when_supported",
            ],
            "forbidden_patterns": [
                "figure_or_table_as_sentence_subject",
                "question_answer_work_report_frame",
                "metric_name_without_clinical_referent",
            ],
        },
        "discussion_prose": {
            "paragraph_sequence": [
                "principal_finding_then_prior_work_then_interpretation_then_limitations",
                "clinical_implication_with_explicit_boundary",
                "conservative_conclusion_without_claim_upgrade",
            ],
            "forbidden_patterns": [
                "claim_boundary_meta_language",
                "submission_or_gate_status_language",
                "unsupported_practice_recommendation",
            ],
        },
        "forbidden_scientific_style": [
            "unsupported_no_difference_or_no_association",
            "overstated_novelty_or_best_language",
            "administrative_or_author_instruction_in_body",
            "tool_or_runtime_provenance_in_body",
        ],
        "source_basis": list(PROSE_STYLE_SOURCE_BASIS),
    }


def build_medical_manuscript_blueprint_contract() -> dict[str, Any]:
    return {
        "surface": "medical_manuscript_blueprint",
        "required_before": "first_full_draft",
        "gate_relaxation_allowed": False,
        "required_fields": [
            "clinical_problem",
            "evidence_gap",
            "target_population",
            "study_design",
            "primary_results",
            "clinical_interpretation",
            "limitations",
            "claim_evidence_map",
            "figure_table_roles",
        ],
        "required_source_surfaces": [
            "study_charter.paper_quality_contract",
            "paper/results_narrative_map.json",
            "paper/claim_evidence_map.json",
            "paper/figure_semantics_manifest.json",
            "paper/evidence_ledger.json",
        ],
        "writer_rule": (
            "compile this blueprint before prose generation and route back when the manuscript voice "
            "would otherwise be derived from run logs, controller checklists, or packaging metadata"
        ),
    }


def build_work_report_residue_clause(top_hits: object) -> str:
    if not isinstance(top_hits, list):
        return ""
    top_hit_pattern_ids = {str(hit.get("pattern_id") or "") for hit in top_hits if isinstance(hit, dict)}
    if not (top_hit_pattern_ids & WORK_REPORT_RESIDUE_PATTERN_IDS):
        return ""
    return (
        " Remove work-report residue from manuscript-facing prose: do not write Results as "
        "`the clinical question was ... the answer was ...`, do not leave `Figure and Table Anchors`, "
        "author-confirmation placeholders, or figure self-explanation paragraphs in the article body, and rewrite those "
        "parts into journal-style medical prose organized as background, methods, results, interpretation, and limitations."
    )


def _normalize_family(value: str | None) -> str:
    return str(value or "").strip().upper().replace("_", "-").replace(" ", "-")


def build_first_draft_manuscript_quality_contract(
    *,
    guideline_family: str | None,
    manuscript_family: str | None,
) -> dict[str, Any]:
    family = _normalize_family(guideline_family) or "STROBE"
    return {
        "surface": "first_draft_manuscript_quality_contract",
        "schema_version": 1,
        "guideline_family": family,
        "manuscript_family": manuscript_family,
        "source_basis": list(SOURCE_BASIS),
        "required_before": "first_full_draft",
        "gate_relaxation_allowed": False,
        "core_structure": {
            "article_body": ["Title", "Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion"],
            "abstract": ["clinical_context", "objective", "design_setting_participants", "exposures_or_predictors", "main_outcome", "results", "conclusion_and_boundary"],
            "introduction": ["clinical_problem", "specific_gap", "study_objective_and_contribution"],
            "discussion": ["principal_findings", "relation_to_prior_work", "clinical_interpretation", "limitations", "conclusion"],
        },
        "guideline_specific_obligations": _guideline_specific_obligations(family),
        "manuscript_native_prose": {
            "required": True,
            "forbidden_modes": [
                "work_report_question_answer_frame",
                "figure_table_anchor_section",
                "author_confirmation_placeholder",
                "figure_self_explanation_paragraph",
                "analysis_or_controller_jargon",
                "claim_boundary_meta_language_in_body",
            ],
            "result_section_rule": "answer the clinical finding directly, then cite supporting figures or tables",
            "scope_boundary_rule": "state limits as clinical interpretation and limitations, not as controller notes",
        },
        "medical_prose_style_contract": build_medical_prose_style_contract(),
        "medical_manuscript_blueprint_contract": build_medical_manuscript_blueprint_contract(),
        "first_draft_generation_model": {
            "pre_draft_inputs": [
                "clinical_problem",
                "study_design",
                "target_population",
                "prediction_timepoint_or_exposure_window",
                "outcome_definition_and_horizon",
                "analysis_plan",
                "display_to_claim_map",
                "reader_facing_contribution",
                "medical_manuscript_blueprint",
                "medical_prose_style_contract",
            ],
            "writer_obligations": [
                "convert research questions into clinical findings rather than question-answer prose",
                "separate manuscript body from submission metadata, author confirmations, and operations notes",
                "write figure legends as reader interpretation aids rather than reviewer instructions",
                "stage Results from cohort and endpoint profile to main finding, validation, clinical utility, and sensitivity or subgroup evidence",
                "stage Discussion from principal finding to prior literature, interpretation, limitations, and practical next step",
            ],
            "route_back_if_missing": "return_to_outline_or_analysis_campaign_before_first_full_draft",
        },
        "must_bind_existing_surfaces": [
            "paper/reporting_guideline_checklist.json",
            "paper/results_narrative_map.json",
            "paper/figure_semantics_manifest.json",
            "paper/claim_evidence_map.json",
            "paper/evidence_ledger.json",
            "paper/review_ledger.json",
        ],
    }


def _guideline_specific_obligations(family: str) -> list[str]:
    if family in {"TRIPOD", "TRIPOD+AI"}:
        obligations = [
            "define target population, prediction timepoint, outcome horizon, and intended use before drafting",
            "report candidate predictors, missing-data handling, model specification, validation, calibration, and clinical utility",
            "separate performance comparison from clinical implementation claims",
        ]
        if family == "TRIPOD+AI":
            obligations.append("report AI preprocessing, training, tuning, fairness/explainability, and human-use context")
        return obligations
    if family == "STROBE":
        return [
            "define design, setting, participants, variables, data sources, bias, missing data, statistical methods, and generalizability",
            "keep exposure/outcome language observational unless causal identification is actually supported",
        ]
    if family == "RECORD":
        return [
            "state routinely collected data sources, linkage, code lists or algorithms, cleaning, denominator accounting, and privacy limits",
        ]
    if family in {"CONSORT", "CONSORT-AI"}:
        return [
            "state trial design, allocation, intervention, outcomes, sample size, participant flow, harms, and protocol deviations",
        ]
    if family == "PRISMA":
        return ["state protocol, eligibility, search, selection, data extraction, risk of bias, synthesis, and certainty"]
    return ["state design, population, variables, methods, results, limitations, and applicability before drafting"]
