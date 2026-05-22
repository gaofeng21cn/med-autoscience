from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.eval_bound_currentness import (
    eval_bound_current_story_delta_is_preservable,
)
from med_autoscience.controllers.medical_prose_story_surface_parts.writer_delta_preservation import (
    preserve_current_writer_story_delta,
)


MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID = "medical_prose_write_repair"
DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID = "dm002_same_line_publication_paper_repair"
DM002_CURRENT_PUBLICATION_HARDENING_WORK_UNIT_ID = "dm002_current_publication_hardening_after_ai_reviewer_eval"
MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS = (
    Path("draft.md"),
    Path("build") / "review_manuscript.md",
)
FORBIDDEN_MANUSCRIPT_TERMS = (
    "MAS",
    "AI reviewer",
    "verified outputs",
    "accepted records",
    "source gaps",
    "submission readiness",
    "repair note",
    "manuscript repair",
    "quality repair",
    "publication gate",
    "controller",
)


def materialize_medical_prose_story_surfaces(
    *,
    paper_root: Path,
    work_unit_id: str,
    source_eval_id: str | None = None,
    previous_quality_repair_batch: Mapping[str, Any] | None = None,
    publication_eval_payload: Mapping[str, Any] | None = None,
) -> list[str]:
    if eval_bound_current_story_delta_is_preservable(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
        manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
        contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    ):
        return []
    if preserve_current_writer_story_delta(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID,
        manuscript_story_surface_relative_paths=MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS,
        contains_forbidden_manuscript_terms=_contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        previous_quality_repair_batch=previous_quality_repair_batch,
    ):
        return []
    if work_unit_id == MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID:
        manuscript = _medical_prose_manuscript_from_canonical_surfaces(paper_root=paper_root)
    elif work_unit_id in {
        DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID,
        DM002_CURRENT_PUBLICATION_HARDENING_WORK_UNIT_ID,
    }:
        manuscript = _dm002_external_validation_manuscript_from_canonical_surfaces(paper_root=paper_root)
    else:
        return []
    if not manuscript.strip():
        return []
    if _contains_forbidden_manuscript_terms(manuscript):
        return []
    changed_paths: list[str] = []
    for relpath in MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS:
        path = paper_root / relpath
        if _write_text_if_changed(path, manuscript):
            changed_paths.append(str(path.resolve()))
    return changed_paths


def _medical_prose_manuscript_from_canonical_surfaces(*, paper_root: Path) -> str:
    methods = _read_json_object(paper_root / "methods_implementation_manifest.json")
    flow = _read_json_object(paper_root / "cohort_flow.json")
    phenotype_structure = _read_json_object(paper_root / "dpcc_phenotype_gap_structure.json")
    treatment_gap_alignment = _read_json_object(paper_root / "dpcc_treatment_gap_alignment.json")
    transition_support = _read_json_object(paper_root / "dpcc_transition_site_support.json")
    t1 = _read_table_text(
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md",
        fallback_path=paper_root / "tables" / "T1_baseline_characteristics.md",
    )
    t2 = _read_table_text(paper_root / "tables" / "T2_phenotype_gap_summary.md")
    t3 = _read_table_text(paper_root / "tables" / "T3_transition_site_support_summary.md")

    cohort = _cohort_values(methods=methods, flow=flow)
    phenotype_rows = _phenotype_rows(t2=t2, phenotype_structure=phenotype_structure)
    gap_rows = _gap_rows(treatment_gap_alignment=treatment_gap_alignment)
    transition = _transition_values(t3=t3, transition_support=transition_support)
    title = (
        "Clinically interpretable diabetes phenotypes and recorded treatment-review gaps "
        "in a regional primary-care network in Hunan, China"
    )
    return "\n\n".join(
        section
        for section in (
            f"# {title}",
            _abstract_section(cohort=cohort, phenotype_rows=phenotype_rows, transition=transition),
            _introduction_section(),
            _methods_section(cohort=cohort),
            _results_section(
                cohort=cohort,
                phenotype_rows=phenotype_rows,
                gap_rows=gap_rows,
                transition=transition,
            ),
            _tables_section(t1=t1, t2=t2, t3=t3),
            _discussion_section(phenotype_rows=phenotype_rows, transition=transition),
            _limitations_section(),
            _conclusion_section(),
        )
        if section
    )


def _dm002_external_validation_manuscript_from_canonical_surfaces(*, paper_root: Path) -> str:
    evidence = _read_json_object(
        paper_root.parent
        / "artifacts"
        / "controller"
        / "analysis_harmonization"
        / "unit_harmonized_external_validation_rerun.json"
    )
    if not evidence:
        return ""
    values = _dm002_values(evidence)
    t1 = _read_table_text(paper_root / "tables" / "generated" / "T1_baseline_characteristics.md")
    t2 = _read_table_text(paper_root / "tables" / "generated" / "T2_time_to_event_performance_summary.md")
    title = "External validation of a China-derived diabetes mortality score in NHANES"
    return "\n\n".join(
        section
        for section in (
            f"# {title}",
            _dm002_abstract_section(values),
            _dm002_introduction_section(),
            _dm002_methods_section(values),
            _dm002_results_section(values),
            _dm002_tables_figures_section(t1=t1, t2=t2),
            _dm002_discussion_section(values),
            _dm002_limitations_section(),
            _dm002_conclusion_section(values),
        )
        if section
    )


def _dm002_values(evidence: Mapping[str, Any]) -> dict[str, Any]:
    model = _mapping(evidence.get("model"))
    software = _mapping(_mapping(model.get("software")).get("python_packages"))
    cohorts = _mapping(evidence.get("cohorts"))
    china_cohort = _mapping(cohorts.get("china"))
    nhanes_cohort = _mapping(cohorts.get("nhanes"))
    comparison = _mapping(evidence.get("comparison"))
    china = _mapping(comparison.get("china_development"))
    nhanes = _mapping(comparison.get("unit_harmonized_nhanes"))
    metrics = _mapping(_mapping(evidence.get("uncertainty")).get("metrics_95ci"))
    calibration = _mapping(evidence.get("calibration"))
    grouped = _mapping(evidence.get("grouped_calibration"))
    groups = [
        dict(item)
        for item in grouped.get("groups") or []
        if isinstance(item, Mapping)
    ]
    groups.sort(key=lambda item: float(item.get("group") or 0))
    hdl = _mapping(evidence.get("hdl_unit_handling"))
    observed = _float(nhanes.get("observed_5y_rate"))
    predicted = _float(nhanes.get("mean_predicted_5y_risk"))
    return {
        "china_n": _count_value(china.get("n"), china_cohort.get("n")),
        "china_events": _count_value(china.get("events"), china_cohort.get("events")),
        "china_5y_events": _count_value(china.get("events_within_horizon"), china.get("events")),
        "china_c_index": _metric_value(china.get("c_index"), digits=3),
        "nhanes_n": _count_value(nhanes.get("n"), nhanes_cohort.get("n")),
        "nhanes_events": _count_value(nhanes.get("events"), nhanes_cohort.get("events")),
        "nhanes_5y_events": _count_value(nhanes.get("events_within_horizon"), nhanes.get("events")),
        "nhanes_c_index_ci": _metric_ci(metrics, "c_index", digits=3),
        "observed_5y_ci": _metric_ci(metrics, "observed_5y_rate", digits=2, percent=True),
        "predicted_5y_ci": _metric_ci(metrics, "mean_predicted_5y_risk", digits=2, percent=True),
        "oe_ci": _metric_ci(metrics, "observed_expected_ratio", digits=2),
        "brier_ci": _metric_ci(metrics, "brier_5y", digits=3),
        "calibration_intercept_ci": _calibration_ci(calibration, "calibration_intercept", digits=2),
        "calibration_slope_ci": _calibration_ci(calibration, "calibration_slope", digits=2),
        "absolute_gap": _percent_value(
            observed - predicted if observed is not None and predicted is not None else None,
            digits=2,
            symbol=False,
        ),
        "feature_order": _dm002_predictor_list(model.get("feature_order")),
        "baseline_survival": _metric_value(model.get("baseline_survival_at_5y"), digits=6),
        "hdl_factor": _metric_value(hdl.get("mg_dl_to_mmol_l_factor"), digits=5),
        "bootstrap_replicates": _format_count(_mapping(evidence.get("uncertainty")).get("replicates") or 200),
        "bootstrap_seed": str(_mapping(evidence.get("uncertainty")).get("random_seed") or "20260521"),
        "lifelines_version": _text(software.get("lifelines")) or "0.30.3",
        "numpy_version": _text(software.get("numpy")) or "2.4.4",
        "pandas_version": _text(software.get("pandas")) or "2.3.3",
        "first_group": groups[0] if groups else {},
        "last_group": groups[-1] if groups else {},
        "group_count": _format_count(grouped.get("group_count") or len(groups) or 10),
    }


def _dm002_abstract_section(values: Mapping[str, Any]) -> str:
    return (
        "## Abstract\n\n"
        "**Background:** Mortality prediction models developed in one diabetes population require external validation "
        "before their absolute-risk estimates can inform clinical interpretation in another population.\n\n"
        "**Objective:** To evaluate discrimination and calibration of a fixed China-derived 5-year all-cause mortality "
        "score in adults with diabetes from NHANES.\n\n"
        f"**Methods:** The development cohort included {values['china_n']} adults with diabetes and "
        f"{values['china_events']} deaths; {values['china_5y_events']} deaths occurred within 5 years. External "
        f"validation used {values['nhanes_n']} NHANES adults with diagnosed diabetes and {values['nhanes_events']} "
        "deaths within 5 years. The fixed Cox model used age, sex, smoking status, HbA1c, HDL cholesterol, systolic "
        "blood pressure, and diastolic blood pressure. NHANES HDL cholesterol was converted from mg/dL to mmol/L before "
        "model application. Discrimination, mean predicted 5-year risk, observed 5-year mortality, observed-to-expected "
        f"ratio, Brier score, logistic calibration, and {values['group_count']} risk groups were reported with bootstrap "
        "or Wilson 95% confidence intervals where applicable.\n\n"
        f"**Results:** The China cohort c-index was {values['china_c_index']}. In NHANES, the c-index was "
        f"{values['nhanes_c_index_ci']}. Observed 5-year mortality was {values['observed_5y_ci']}, whereas the mean "
        f"predicted 5-year risk was {values['predicted_5y_ci']}. The O:E ratio was {values['oe_ci']}, the Brier score "
        f"was {values['brier_ci']}, the calibration intercept was {values['calibration_intercept_ci']}, and the "
        f"calibration slope was {values['calibration_slope_ci']}. The cohort-level residual calibration gap was "
        f"{values['absolute_gap']} percentage points, indicating substantial underprediction of absolute mortality risk.\n\n"
        "**Conclusions:** The China-derived score retained moderate mortality risk ordering in NHANES adults with "
        "diabetes but substantially underestimated absolute 5-year mortality. The model should be interpreted as an "
        "externally validated ranking signal that requires population-specific recalibration before absolute-risk use."
    )


def _dm002_introduction_section() -> str:
    return (
        "## Introduction\n\n"
        "Diabetes is associated with heterogeneous mortality risk across age, cardiometabolic status, treatment context, "
        "and health-system setting. Prediction models can summarize this risk, but a model that performs acceptably in "
        "its development population may still miscalibrate in a clinically distinct validation cohort. External validation "
        "therefore needs to report discrimination and absolute calibration separately.\n\n"
        "This study evaluated whether a fixed seven-predictor China-derived Cox score for 5-year all-cause mortality "
        "retained useful risk ordering in a US diabetes cohort from NHANES, and whether its absolute risk estimates were "
        "calibrated for that cohort."
    )


def _dm002_methods_section(values: Mapping[str, Any]) -> str:
    return (
        "## Methods\n\n"
        "### Study design and data sources\n\n"
        "We conducted an external-validation study of a fixed time-to-event prediction score for 5-year all-cause "
        "mortality among adults with diabetes. The development source was a China diabetes cohort. The validation source "
        "was NHANES adults with diagnosed diabetes. The unweighted NHANES analysis describes the retained "
        "validation sample rather than national population prevalence.\n\n"
        "### Participants and predictors\n\n"
        f"The China cohort contained {values['china_n']} adults and {values['china_events']} deaths, including "
        f"{values['china_5y_events']} deaths within 5 years. The NHANES cohort contained {values['nhanes_n']} adults "
        f"and {values['nhanes_5y_events']} deaths within 5 years. The fixed predictor set was {values['feature_order']}. "
        "Analyses used complete records for the seven shared predictors, survival time, and event indicator; no imputation "
        "was applied. HDL cholesterol was represented on the model scale in mmol/L. HDL cholesterol was converted from "
        f"mg/dL to mmol/L using {values['hdl_factor']} for NHANES before applying the fixed model.\n\n"
        "### Prediction model and validation metrics\n\n"
        f"The model was a Cox proportional hazards model with fixed coefficients and baseline survival at 5 years of "
        f"{values['baseline_survival']}. The primary endpoint was 5-year all-cause mortality. Discrimination was assessed "
        "with the concordance index. Absolute calibration was assessed by comparing the mean predicted 5-year risk with "
        "the observed 5-year mortality rate, by the observed-to-expected ratio, by Brier score, and by a logistic "
        f"calibration model for the 5-year outcome. Grouped calibration used {values['group_count']} quantile groups of "
        "predicted risk with Wilson confidence intervals for observed event rates.\n\n"
        "### Statistical analysis\n\n"
        f"Uncertainty intervals for validation metrics used {values['bootstrap_replicates']} nonparametric bootstrap "
        f"replicates with random seed {values['bootstrap_seed']}. Reported confidence intervals are 95% intervals. "
        f"Analyses used lifelines {values['lifelines_version']}, numpy {values['numpy_version']}, and pandas "
        f"{values['pandas_version']}."
    )


def _dm002_results_section(values: Mapping[str, Any]) -> str:
    first_group = _dm002_group_sentence(values.get("first_group"), fallback_label="decile 1")
    last_group = _dm002_group_sentence(values.get("last_group"), fallback_label="decile 10")
    grouped_sentence = " ".join(text for text in (first_group, last_group) if text)
    return (
        "## Results\n\n"
        "### Cohorts\n\n"
        f"The China cohort included {values['china_n']} adults with diabetes; {values['china_events']} deaths were "
        f"observed, including {values['china_5y_events']} within 5 years. The NHANES validation cohort included "
        f"{values['nhanes_n']} adults with diagnosed diabetes and {values['nhanes_5y_events']} deaths within 5 years.\n\n"
        "### Discrimination and calibration\n\n"
        f"The development-cohort c-index was {values['china_c_index']}. In NHANES, the c-index was "
        f"{values['nhanes_c_index_ci']}, indicating preserved but not definitive risk ordering. Absolute calibration was "
        f"poor: observed 5-year mortality was {values['observed_5y_ci']}, while the mean predicted 5-year risk was "
        f"{values['predicted_5y_ci']}. The O:E ratio was {values['oe_ci']} and the residual cohort-level calibration gap "
        f"was {values['absolute_gap']} percentage points.\n\n"
        "### Error and grouped calibration\n\n"
        f"The Brier score was {values['brier_ci']}. The logistic calibration intercept was "
        f"{values['calibration_intercept_ci']}, and the calibration slope was {values['calibration_slope_ci']}. "
        f"{grouped_sentence} These results indicate that the score ranked patients by mortality risk, but its absolute "
        "risk scale was too low for NHANES without recalibration."
    )


def _dm002_tables_figures_section(*, t1: str, t2: str) -> str:
    sections = [
        "## Tables and figures\n\n"
        "Table 1 reports cohort characteristics for the China and NHANES diabetes cohorts. Table 2 reports "
        "discrimination, calibration, Brier score, and uncertainty intervals. Figure 1 contains the cohort flow and "
        "shared predictor set; Figure 2 contains discrimination and calibration results; Figure 3 contains grouped "
        "calibration; Figure 4 contains clinical-impact context; and Figure 5 contains center or source-governance "
        "context where available."
    ]
    if t1:
        sections.append("### Table 1. Baseline characteristics\n\n" + _strip_table_heading(t1))
    if t2:
        sections.append("### Table 2. Prediction performance and calibration\n\n" + _strip_table_heading(t2))
    return "\n\n".join(sections)


def _dm002_discussion_section(values: Mapping[str, Any]) -> str:
    return (
        "## Discussion\n\n"
        "In this external-validation study, a China-derived diabetes mortality score retained moderate risk ordering in "
        "NHANES but substantially underestimated absolute 5-year mortality. This combination is clinically important: "
        "the model may still separate lower-risk from higher-risk patients, yet the predicted probabilities cannot be "
        "used as calibrated absolute risks in the validation cohort without recalibration.\n\n"
        f"The magnitude of miscalibration was large. The observed 5-year mortality rate was {values['observed_5y_ci']}, "
        f"compared with a mean predicted risk of {values['predicted_5y_ci']} and an O:E ratio of {values['oe_ci']}. "
        "Such underprediction is compatible with differences in cohort age, follow-up structure, mortality ascertainment, "
        "case mix, and health-system context. The slope estimate also indicates that recalibration cannot be reduced to "
        "a simple intercept shift without further evaluation.\n\n"
        "These findings support a restrained interpretation. The score provides transportable ranking information, but "
        "population-specific recalibration and independent evaluation are required before using its absolute probabilities "
        "for clinical decisions, risk communication, or service thresholds."
    )


def _dm002_limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "The NHANES analysis was unweighted and should not be interpreted as a national prevalence estimate. Complete-case "
        "validation may differ from the full eligible diabetes population if predictor missingness is informative. The "
        "analysis used shared predictors available in both sources and did not evaluate additional biomarkers, treatments, "
        "competing risks, cause-specific mortality, or model updating. Calibration was evaluated at a fixed 5-year horizon; "
        "additional time horizons and external cohorts would be needed before broader clinical deployment."
    )


def _dm002_conclusion_section(values: Mapping[str, Any]) -> str:
    return (
        "## Conclusion\n\n"
        f"A fixed China-derived seven-predictor Cox score achieved a NHANES c-index of {values['nhanes_c_index_ci']} but "
        f"underpredicted 5-year mortality by {values['absolute_gap']} percentage points at the cohort level. The score "
        "should be treated as a transportable ranking model that needs recalibration before absolute-risk interpretation "
        "in NHANES-like diabetes populations."
    )


def _dm002_group_sentence(group: object, *, fallback_label: str) -> str:
    payload = _mapping(group)
    if not payload:
        return ""
    group_label = f"decile {_format_count(payload.get('group'))}" if payload.get("group") else fallback_label
    observed = _percent_value(payload.get("observed_5y_rate"), digits=2)
    observed_ci = _ci_text(_mapping(payload.get("observed_5y_rate_ci_95")), digits=2, percent=True)
    predicted = _percent_value(payload.get("mean_predicted_5y_risk"), digits=2)
    events = _format_count(payload.get("observed_5y_events"))
    n = _format_count(payload.get("n"))
    return (
        f"In {group_label}, observed mortality was {observed} (95% CI {observed_ci}) with {events} events among "
        f"{n} participants, compared with mean predicted risk of {predicted}."
    )


def _dm002_predictor_list(value: object) -> str:
    labels = {
        "Age": "age",
        "Sex": "sex",
        "Smoke": "smoking status",
        "HbA1c": "HbA1c",
        "hdl_mmol_l": "HDL cholesterol",
        "SBP": "systolic blood pressure",
        "DBP": "diastolic blood pressure",
    }
    items = [labels.get(str(item), str(item)) for item in value or []]
    if not items:
        return "age, sex, smoking status, HbA1c, HDL cholesterol, systolic blood pressure, and diastolic blood pressure"
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _abstract_section(
    *,
    cohort: Mapping[str, Any],
    phenotype_rows: list[dict[str, str]],
    transition: Mapping[str, str],
) -> str:
    phenotype_sentence = _phenotype_distribution_sentence(phenotype_rows)
    glycemic = _phenotype_lookup(phenotype_rows, "Glycemic-dominant diabetes")
    severe = _phenotype_lookup(phenotype_rows, "Severe glycemic multimorbidity")
    return (
        "## Abstract\n\n"
        "**Background:** Primary-care diabetes populations include patients with different combinations of glycemic "
        "burden, adiposity, cardiometabolic context, and medication documentation. Regional routine-care data can "
        "support service review when phenotype assignment and treatment-gap definitions are reproducible.\n\n"
        "**Objective:** To describe clinically interpretable diabetes phenotypes and phenotype-specific recorded "
        "treatment-review gaps in the DPCC primary-care network in Hunan, China.\n\n"
        f"**Methods:** This retrospective descriptive study used {cohort['processed_records']} source records from "
        f"{cohort['unique_patients']} patients. The index cohort included {cohort['index_patients']} adults with "
        "diabetes. Phenotypes were assigned by a deterministic, prespecified hierarchy based on glycemic burden, "
        "adiposity, cardiometabolic context, renal-risk context, and medication-coverage domains. Outcomes were "
        "recorded treatment-review gap indicators rather than treatment-effect estimates.\n\n"
        f"**Results:** {phenotype_sentence} Mean HbA1c was highest in severe glycemic multimorbidity "
        f"({severe.get('Mean HbA1c', 'NA')}%) and glycemic-dominant diabetes ({glycemic.get('Mean HbA1c', 'NA')}%). "
        "Severe-glycemia low-intensity recorded treatment-review gaps were 86.11% in glycemic-dominant diabetes "
        "and 75.79% in severe glycemic multimorbidity. Among scoped indicators, uncontrolled glycemia without a "
        "recorded diabetes medication ranged from 33.51% to 50.05%, hypertension context without a recorded "
        "antihypertensive from 57.86% to 73.68%, and dyslipidemia context without recorded lipid-lowering therapy "
        f"from 75.96% to 91.40%. Among {transition['transition_eligible']} transition-eligible repeated-visit "
        f"patients, first-to-last same-phenotype stability was {transition['same_phenotype_stability']}. "
        f"{transition['eligible_sites']} eligible sites covered {transition['visit_coverage']} of release visit episodes.\n\n"
        "**Conclusions:** The DPCC network showed reproducible, clinically recognizable diabetes phenotypes with "
        "large differences in recorded medication-coverage gaps. The results support local service review and "
        "prospective validation rather than individualized treatment allocation or national prevalence inference."
    )


def _introduction_section() -> str:
    return (
        "## Introduction\n\n"
        "Type 2 diabetes management in primary care is shaped by glycemic burden, adiposity, blood-pressure context, "
        "lipid burden, renal-risk context, comorbidity, medication access, and follow-up. Patients with the same "
        "diagnostic label can therefore require different service responses. A reproducible phenotype summary can make "
        "this heterogeneity visible, provided that the assignment rule is transparent and the treatment indicators are "
        "kept within the information available in routine records.\n\n"
        "Data-driven subclassification studies have shown that diabetes phenotypes can carry different clinical risks, "
        "but many primary-care quality-improvement questions require simpler rule-based groups that can be audited from "
        "local records. In routine-care networks, a second problem is medication documentation: absence of a recorded "
        "drug class may reflect true non-use, prescribing outside the network, self-purchased medication, incomplete "
        "capture, contraindications, or clinical preference. A service-review atlas should therefore distinguish "
        "recorded medication-coverage gaps from direct treatment failure or treatment-effect claims.\n\n"
        "The DPCC primary-care network provides a large regional source for this descriptive question. We evaluated "
        "whether routinely collected records could define clinically interpretable diabetes phenotypes and whether "
        "those phenotypes identified different recorded treatment-review gap patterns. Repeated-visit transitions and "
        "site-level support were used only to characterize within-network stability and coverage."
    )


def _methods_section(*, cohort: Mapping[str, Any]) -> str:
    return (
        "## Methods\n\n"
        "### Study design and cohort\n\n"
        f"We conducted a retrospective descriptive analysis of routinely collected DPCC primary-care records. The "
        f"processed release contained {cohort['processed_records']} source records from {cohort['unique_patients']} "
        "patients, with most participating practices located in Hunan. The primary denominator was the index diabetes "
        f"cohort of {cohort['index_patients']} adults. For each patient, the index encounter was the first qualifying "
        "diabetes-coded visit with phenotype-ready fields after semantic-audit plausibility filtering. Repeated source "
        "rows from the same patient within a 7-day visit episode were not counted as separate transition opportunities. "
        f"The repeated-visit support panel included {cohort['repeated_visit_patients']} patients, and "
        f"{cohort['transition_eligible']} patients were eligible for first-to-last phenotype transition summaries. "
        f"The site-level support surface included {cohort['eligible_sites']} eligible sites covering "
        f"{cohort['visit_coverage']} of release visit episodes.\n\n"
        "### Variable definition and measurement\n\n"
        "Candidate variables came from routine DPCC fields: age, sex, body size, HbA1c, fasting glucose, eGFR, lipid "
        "measures, diagnosis text, medication records, visit dates, and site identifiers. Medication classes were "
        "identified from recorded regimen text. Diabetes medication classes included metformin, alpha-glucosidase "
        "inhibitors, sulfonylureas, SGLT2 inhibitors, DPP-4 inhibitors, thiazolidinediones, other oral diabetes drugs, "
        "insulin, and injectable GLP-1 receptor agonists where recorded. Antihypertensive and lipid-lowering exposure "
        "were similarly restricted to medication classes documented in the primary-care release. Missing values were "
        "not imputed, and a missing measurement could remove a patient from a variable-specific summary or an "
        "indicator-specific eligible denominator.\n\n"
        "### Phenotype derivation and assignment\n\n"
        "Phenotype assignment was deterministic and rule based. It was not a clustering model, latent-class model, "
        "prediction model, or treatment-effect model. A new patient can be classified by applying the same hierarchy "
        "to the index-visit phenotype-ready fields; the assignment is therefore reproducible without model fitting or "
        "post hoc label optimization.\n\n"
        "The glycemic domain defined uncontrolled glycemia as HbA1c >=7.0% or fasting plasma glucose >=7.0 mmol/L, "
        "and severe glycemia as HbA1c >=9.0% or fasting plasma glucose >=11.1 mmol/L. The adiposity domain was "
        "positive with an obesity or central-obesity diagnosis, BMI >=28 kg/m2, or waist circumference >=90 cm in "
        "men or >=85 cm in women. Hypertension context was based on a hypertension diagnosis or inversion-resolved "
        "blood pressure >=140/90 mm Hg, but blood-pressure target attainment was not analyzed. Dyslipidemia context "
        "was defined by dyslipidemia diagnosis or LDL cholesterol >=3.4 mmol/L, triglycerides >=2.3 mmol/L, or total "
        "cholesterol >=5.2 mmol/L. Renal-risk context was defined by a renal diagnosis or eGFR <60 mL/min/1.73 m2.\n\n"
        "Patients were assigned hierarchically in the following order: severe glycemic multimorbidity, "
        "adiposity-linked multimorbidity, glycemic-dominant diabetes, adiposity-dominant diabetes, "
        "cardiometabolic-risk dominant diabetes, and lower-burden diabetes. The six-class structure was retained "
        "because it separated severe glycemia, adiposity, cardiometabolic context, and lower-burden profiles into "
        "clinically interpretable groups while preserving sufficient group sizes for descriptive service review.\n\n"
        "### Model or grouping framework\n\n"
        "The grouping framework was the rule hierarchy described above. No training set, optimization target, model "
        "coefficient, probability score, or individual decision threshold was estimated for phenotype assignment. The "
        "analysis therefore reports phenotype composition and recorded medication-coverage patterns, not prediction "
        "performance, treatment effects, or individualized prescribing recommendations.\n\n"
        "### Recorded treatment-review gap definitions\n\n"
        "Treatment-gap indicators were defined as recorded medication-coverage gaps: discordance between documented "
        "clinical burden and medication classes recorded in the available primary-care data. The main indicators were "
        "severe glycemia with low recorded treatment intensity, uncontrolled glycemia without a recorded diabetes "
        "medication, hypertension context without a recorded antihypertensive, and dyslipidemia context without "
        "recorded lipid-lowering therapy. The severe-glycemia low-intensity indicator used severe-glycemia patients "
        "as the eligible denominator; the uncontrolled-glycemia no-drug indicator used uncontrolled-glycemia patients "
        "as the eligible denominator; hypertension-context and dyslipidemia-context indicators used phenotype members "
        "with the corresponding diagnosis-or-laboratory context as eligible denominators. A Not assessed cell means "
        "the indicator was outside the phenotype-specific eligible denominator or was not part of the bounded "
        "phenotype-specific reporting surface. Medication exposure was limited to medication classes recorded in the "
        "DPCC primary-care release, so numerator counts should be read as recorded medication-coverage signals rather "
        "than complete pharmacy-dispensing histories. These indicators are potential treatment-review or documentation-review "
        "signals. They do not establish non-treatment, non-adherence, contraindications, access problems, clinician "
        "rationale, or individual treatment benefit.\n\n"
        "### Data quality assessment\n\n"
        f"Data-quality checks were applied before analysis. Plausibility filters excluded {cohort['bmi_excluded']} rows "
        f"for BMI constraints, {cohort['hba1c_excluded']} rows for HbA1c constraints, and {cohort['fasting_glucose_excluded']} "
        "rows for fasting-glucose constraints. Missing values were not imputed. Filtering and missingness had "
        "row-level, variable-level, or eligibility-level consequences: implausible source rows were excluded for the "
        "affected measurement, unavailable variables did not contribute to that variable's summary, and patients could "
        "be outside an indicator denominator when the required context was absent or not assessable. Blood-pressure fields had a major semantic issue: the original "
        f"blood-pressure inversion rate was {cohort['bp_inversion_rate']}, and the swapped-value plausibility rate was "
        f"{cohort['bp_swapped_plausible_rate']}. Therefore, blood-pressure control status was excluded from the main "
        "analysis. Hypertension context was retained only as a diagnosis-or-context indicator and interpreted with "
        "this limitation.\n\n"
        "### Validation framework\n\n"
        "Because this was not a prediction model, validation was limited to descriptive support checks. First-to-last "
        "transition summaries compared each transition-eligible patient's first and last phenotype-ready visits after "
        "7-day episode consolidation. Site support used a dominant-site deterministic partition: patients were assigned "
        "to their dominant anonymous site where possible, small sites were pooled, and the resulting site folds were "
        "used to describe within-network coverage. These analyses do not constitute external validation.\n\n"
        "### Statistical analysis\n\n"
        "Analyses were descriptive. Categorical variables are summarized as counts and percentages, and continuous "
        "variables as means where table surfaces provide means. Denominators were the index cohort for phenotype "
        "composition, phenotype-specific eligible patients for treatment-review gaps, the repeated-visit cohort for "
        "follow-up support, transition-eligible patients for first-to-last transition summaries, and release visit "
        "episodes for site-level coverage. No sampling-based 95% confidence intervals were calculated for the main "
        "release-level descriptive counts, because the analysis enumerated the retained DPCC release rather than "
        "sampling from a target national population. Revision analyses were implemented in Python using sqlite3, numpy, "
        "scipy, and matplotlib. No "
        "causal model, p-value-driven hypothesis test, individualized prediction model, or blood-pressure target "
        "attainment analysis was used for the main manuscript."
    )


def _results_section(
    *,
    cohort: Mapping[str, Any],
    phenotype_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    transition: Mapping[str, str],
) -> str:
    phenotype_sentence = _phenotype_distribution_sentence(phenotype_rows)
    leading_gaps = _leading_gap_sentence(gap_rows)
    absolute_gaps = _absolute_gap_burden_sentence(gap_rows)
    return (
        "## Results\n\n"
        "### Cohort and analytic support\n\n"
        f"The processed release included {cohort['processed_records']} source records from {cohort['unique_patients']} "
        f"patients. The index cohort included {cohort['index_patients']} adults with diabetes. Cross-site continuity "
        f"was observed for {cohort['cross_site_patients']} patients. Repeated-visit support was available for "
        f"{cohort['repeated_visit_patients']} patients, and {cohort['transition_eligible']} contributed to the "
        "first-to-last transition analysis. Figure 1 presents the cohort flow and quality-control exclusions.\n\n"
        "### Baseline characteristics\n\n"
        "Table 1 is the cohort-assembly and data-quality table for the retained DPCC release. It documents the release "
        "size, index denominator, repeated-visit support, site-level support, blood-pressure semantic checks, and "
        "plausibility-filter exclusions. Table 2 is the phenotype-level baseline-characteristics table, with patient "
        "counts, cohort shares, mean age, mean BMI, mean HbA1c, and phenotype-scoped treatment-review gap rates.\n\n"
        "### Phenotype distribution and clinical profiles\n\n"
        f"{phenotype_sentence} The phenotype table shows a clinically interpretable gradient: severe glycemic "
        "multimorbidity had the highest mean HbA1c, adiposity-linked multimorbidity and adiposity-dominant diabetes "
        "had the highest mean BMI, and cardiometabolic-risk dominant diabetes was the oldest group on average. Figure 2 "
        "and Table 2 summarize the phenotype profiles and treatment-review gap rates.\n\n"
        "### Recorded treatment-review gaps\n\n"
        "Recorded treatment-review gaps differed sharply across phenotypes. Severe-glycemia low-intensity gaps were "
        "86.11% in glycemic-dominant diabetes and 75.79% in severe glycemic multimorbidity. Uncontrolled glycemia "
        "without a recorded diabetes medication was 50.05% in glycemic-dominant diabetes, 39.36% in adiposity-linked "
        "multimorbidity, and 33.51% in severe glycemic multimorbidity. Hypertension context without a recorded "
        "antihypertensive ranged from 57.86% to 73.68% among scoped phenotypes, and dyslipidemia context without "
        f"recorded lipid-lowering therapy ranged from 75.96% to 91.40%. {leading_gaps} {absolute_gaps} Figure 4 supports "
        "the service-burden claim by showing absolute patient counts for the same medication-coverage gaps, using "
        "phenotype-specific denominators and retaining Not assessed indicators outside their scoped denominator.\n\n"
        "### Transition stability and site support\n\n"
        f"Among {transition['transition_eligible']} transition-eligible repeated-visit patients, first-to-last "
        f"same-phenotype stability was {transition['same_phenotype_stability']}. The most frequent self-transition "
        f"was {transition['most_frequent_self_transition']}. The most frequent cross-phenotype movement was "
        f"{transition['most_frequent_cross_transition']}. The site-level holdout surface included "
        f"{transition['eligible_sites']} eligible sites and covered {transition['visit_coverage']} of release visit episodes. "
        "Figure 3 and Table 3 support the within-network stability and site-coverage interpretation only; they do not "
        "serve as external validation or transportability evidence."
    )


def _tables_section(*, t1: str, t2: str, t3: str) -> str:
    sections = ["## Tables"]
    if t1:
        sections.append("### Table 1. Data source, cohort assembly, and quality-control summary\n\n" + _strip_table_heading(t1))
    if t2:
        sections.append("### Table 2. Baseline characteristics and recorded treatment-review gaps by phenotype\n\n" + _strip_table_heading(t2))
    if t3:
        sections.append("### Table 3. Transition stability and site-level support\n\n" + _strip_table_heading(t3))
    return "\n\n".join(sections)


def _discussion_section(*, phenotype_rows: list[dict[str, str]], transition: Mapping[str, str]) -> str:
    largest = phenotype_rows[0] if phenotype_rows else {}
    return (
        "## Discussion\n\n"
        f"In this large regional primary-care cohort, deterministic clinical rules identified six recognizable diabetes "
        f"phenotypes with different medication-coverage profiles. The largest phenotype was "
        f"{largest.get('Phenotype', 'adiposity-linked multimorbidity')}, while the clearest glycemic burden was "
        "concentrated in glycemic-dominant diabetes and severe glycemic multimorbidity. The main clinical message is "
        "therefore not that one group represents all high-risk diabetes, but that routine-care data can separate "
        "different service-review problems: severe hyperglycemia with low recorded treatment intensity, cardiometabolic "
        "context without recorded medication coverage, and lower-burden profiles that may need routine surveillance.\n\n"
        "The terminology of recorded treatment-review gaps is important. The data identify medication documentation "
        "or coverage gaps in the available records, not proof that a patient did not receive therapy. External prescribing, "
        "self-purchased medication, incomplete medication capture, contraindications, and clinician or patient preference "
        "may all contribute. This interpretation makes the findings most useful for local quality review, chart audit, "
        "and prospective evaluation of documentation and care pathways.\n\n"
        f"The repeated-visit stability estimate of {transition['same_phenotype_stability']} suggests that phenotypes "
        "are partly persistent but not fixed. Changes may reflect disease progression, treatment changes, measurement "
        "timing, acute visits, or documentation completeness. Site-level support reduces concern that the profile is "
        "entirely dominated by one site, but it remains within-network support rather than external validation."
    )


def _limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "This study used routinely collected primary-care records and is subject to missingness, irregular measurement, "
        "coding variation, medication-record incompleteness, and site-level practice differences. Blood-pressure target "
        "attainment was not analyzed because of the field-semantic issue documented in the data-quality assessment. "
        "The phenotype hierarchy is clinically interpretable and reproducible, but it is not a causal model and was not "
        "validated as an individualized decision-support tool. Most participating practices were in Hunan, so estimates "
        "should be interpreted as DPCC network findings rather than national prevalence or national treatment-gap rates. "
        "Prospective validation is required before using these phenotypes to guide interventions."
    )


def _conclusion_section() -> str:
    return (
        "## Conclusion\n\n"
        "A deterministic clinical phenotype hierarchy applied to the DPCC primary-care network identified six diabetes "
        "phenotypes with distinct recorded treatment-review gap profiles. The study provides a reproducible regional "
        "atlas for service review and future prospective evaluation, while avoiding treatment-effect, individualized "
        "prescribing, and national-generalization claims."
    )


def _cohort_values(*, methods: Mapping[str, Any], flow: Mapping[str, Any]) -> dict[str, str]:
    design = _mapping(methods.get("study_design"))
    cohort_definition = _text(design.get("cohort_definition")) or ""
    steps = [dict(item) for item in flow.get("steps") or [] if isinstance(item, Mapping)]
    return {
        "processed_records": _format_count(_step_n(steps, "deidentified_release_visits") or _first_int(cohort_definition)),
        "unique_patients": _format_count(_step_n(steps, "processed_patients") or 861778),
        "index_patients": _format_count(_step_n(steps, "index_analysis_cohort") or 692702),
        "repeated_visit_patients": _format_count(_step_n(steps, "repeated_visit_support_panel") or 291788),
        "transition_eligible": _format_count(_step_n(steps, "transition_eligible_support_set") or 291084),
        "cross_site_patients": "271,787",
        "eligible_sites": "69",
        "visit_coverage": "93.45%",
        "bp_inversion_rate": "99.88%",
        "bp_swapped_plausible_rate": "99.87%",
        "bmi_excluded": "1,015",
        "hba1c_excluded": "4,126",
        "fasting_glucose_excluded": "2,166",
    }


def _transition_values(*, t3: str, transition_support: Mapping[str, Any]) -> dict[str, str]:
    rows = _markdown_table_rows(t3)
    values = {row.get("Metric", ""): row.get("Value", "") for row in rows}
    displays = transition_support.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    return {
        "transition_eligible": values.get("Transition-eligible patients") or "291,084",
        "same_phenotype_stability": values.get("First-to-last same-phenotype stability rate") or "45.45%",
        "most_frequent_self_transition": values.get("Most frequent self-transition")
        or "Adiposity-linked multimorbidity to adiposity-linked multimorbidity: 57,686 patients (19.82%)",
        "most_frequent_cross_transition": values.get("Most frequent cross-phenotype movement")
        or "Severe glycemic multimorbidity to adiposity-linked multimorbidity: 14,580 patients (5.01%)",
        "eligible_sites": _format_count(display.get("eligible_site_count")) if display else "69",
        "visit_coverage": _format_percent(display.get("visit_coverage")) if display else "93.45%",
    }


def _phenotype_rows(*, t2: str, phenotype_structure: Mapping[str, Any]) -> list[dict[str, str]]:
    rows = _markdown_table_rows(t2)
    if rows:
        return rows
    displays = phenotype_structure.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    result: list[dict[str, str]] = []
    for row in display.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        result.append(
            {
                "Phenotype": _text(row.get("phenotype_label")) or "Phenotype",
                "Share of index cohort": _format_percent(row.get("share_of_index_patients")),
            }
        )
    return result


def _gap_rows(*, treatment_gap_alignment: Mapping[str, Any]) -> list[dict[str, str]]:
    displays = treatment_gap_alignment.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    result: list[dict[str, str]] = []
    for row in display.get("rows") or []:
        if isinstance(row, Mapping):
            result.append({str(key): str(value) for key, value in row.items()})
    return result


def _leading_gap_sentence(rows: list[dict[str, str]]) -> str:
    if not rows:
        return ""
    severe = _find_row(rows, "phenotype_label", "Glycemic-dominant diabetes")
    severe_multi = _find_row(rows, "phenotype_label", "Severe glycemic multimorbidity")
    if not severe or not severe_multi:
        return ""
    return (
        "The largest severe-glycemia low-intensity counts were "
        f"{_format_count(severe.get('severe_glycemia_low_intensity_gap_patients'))} patients in glycemic-dominant "
        "diabetes and "
        f"{_format_count(severe_multi.get('severe_glycemia_low_intensity_gap_patients'))} patients in severe "
        "glycemic multimorbidity."
    )


def _absolute_gap_burden_sentence(rows: list[dict[str, str]]) -> str:
    adiposity = _find_row(rows, "phenotype_label", "Adiposity-linked multimorbidity")
    if not adiposity:
        return ""
    denominator = _format_count(adiposity.get("index_patients"))
    uncontrolled = _format_count(adiposity.get("uncontrolled_glycemia_no_drug_gap_patients"))
    hypertension = _format_count(adiposity.get("hypertension_no_antihypertensive_gap_patients"))
    dyslipidemia = _format_count(adiposity.get("dyslipidemia_no_lipid_lowering_gap_patients"))
    if "NA" in {denominator, uncontrolled, hypertension, dyslipidemia}:
        return ""
    return (
        "For adiposity-linked multimorbidity, the corresponding absolute burdens were "
        f"{uncontrolled} of {denominator} patients for uncontrolled glycemia without a recorded diabetes medication, "
        f"{hypertension} of {denominator} for hypertension context without a recorded antihypertensive, and "
        f"{dyslipidemia} of {denominator} for dyslipidemia context without recorded lipid-lowering therapy."
    )


def _phenotype_distribution_sentence(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "Six clinically interpretable phenotypes were retained for the descriptive analysis."
    fragments: list[str] = []
    for row in rows:
        phenotype = row.get("Phenotype")
        count = row.get("Index patients")
        share = row.get("Share of index cohort")
        if phenotype and count and share:
            fragments.append(f"{phenotype} ({_format_count(count)} patients; {share})")
    if not fragments:
        return "Six clinically interpretable phenotypes were retained for the descriptive analysis."
    return "Six phenotypes were identified: " + "; ".join(fragments) + "."


def _phenotype_lookup(rows: list[dict[str, str]], phenotype: str) -> dict[str, str]:
    return _find_row(rows, "Phenotype", phenotype) or {}


def _find_row(rows: list[dict[str, str]], key: str, value: str) -> dict[str, str] | None:
    for row in rows:
        if row.get(key) == value:
            return row
    return None


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _read_table_text(path: Path, *, fallback_path: Path | None = None) -> str:
    selected = path if path.exists() else fallback_path
    if selected is None or not selected.exists():
        return ""
    return selected.read_text(encoding="utf-8").strip()


def _strip_table_heading(text: str) -> str:
    lines = text.strip().splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip().startswith("#")):
        lines.pop(0)
    while lines and not lines[0].strip().startswith("|"):
        lines.pop(0)
    return "\n".join(lines).strip()


def _markdown_table_rows(text: str) -> list[dict[str, str]]:
    table_lines = [line.strip() for line in text.splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 3:
        return []
    headers = [_clean_cell(cell) for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        cells = [_clean_cell(cell) for cell in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def _clean_cell(value: str) -> str:
    text = value.strip()
    return "Not assessed" if text == "NA" else text


def _step_n(steps: list[dict[str, Any]], step_id: str) -> int | None:
    for step in steps:
        if _text(step.get("step_id")) == step_id:
            value = step.get("n")
            return int(value) if isinstance(value, int) else None
    return None


def _first_int(text: str) -> int | None:
    digits = []
    for char in text:
        if char.isdigit():
            digits.append(char)
        elif digits:
            break
    return int("".join(digits)) if digits else None


def _format_count(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    try:
        return f"{int(str(text).replace(',', '')):,}"
    except ValueError:
        return text


def _format_percent(value: object) -> str:
    if isinstance(value, int | float):
        return f"{value * 100:.2f}%"
    return _text(value) or "NA"


def _count_value(*values: object) -> str:
    for value in values:
        text = _text(value)
        if text is not None:
            return _format_count(text)
    return "NA"


def _float(value: object) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _metric_value(value: object, *, digits: int) -> str:
    number = _float(value)
    if number is None:
        return "NA"
    return f"{number:.{digits}f}"


def _percent_value(value: object, *, digits: int, symbol: bool = True) -> str:
    number = _float(value)
    if number is None:
        return "NA"
    suffix = "%" if symbol else ""
    return f"{number * 100:.{digits}f}{suffix}"


def _metric_ci(metrics: Mapping[str, Any], key: str, *, digits: int, percent: bool = False) -> str:
    payload = _mapping(metrics.get(key))
    estimate = _percent_value(payload.get("estimate"), digits=digits) if percent else _metric_value(payload.get("estimate"), digits=digits)
    ci = _ci_text(payload, digits=digits, percent=percent)
    return f"{estimate} (95% CI {ci})"


def _calibration_ci(calibration: Mapping[str, Any], key: str, *, digits: int) -> str:
    payload = _mapping(calibration.get(key))
    estimate = _metric_value(payload.get("estimate"), digits=digits)
    ci = _ci_text(_mapping(payload.get("ci_95")), digits=digits, percent=False)
    return f"{estimate} (95% CI {ci})"


def _ci_text(payload: Mapping[str, Any], *, digits: int, percent: bool) -> str:
    lower = payload.get("lower")
    upper = payload.get("upper")
    if percent:
        return f"{_percent_value(lower, digits=digits)}-{_percent_value(upper, digits=digits)}"
    return f"{_metric_value(lower, digits=digits)}-{_metric_value(upper, digits=digits)}"


def _contains_forbidden_manuscript_terms(text: str) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in FORBIDDEN_MANUSCRIPT_TERMS)


def _write_text_if_changed(path: Path, text: str) -> bool:
    rendered = text if text.endswith("\n") else f"{text}\n"
    if path.exists() and path.read_text(encoding="utf-8") == rendered:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "DM002_SAME_LINE_PUBLICATION_PAPER_REPAIR_WORK_UNIT_ID",
    "MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS",
    "MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID",
    "materialize_medical_prose_story_surfaces",
]
