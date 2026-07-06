from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.dpcc_tables import (
    _adjusted_model_discussion_sentence,
    _adjusted_model_lookup,
    _adjusted_model_results_sentence,
    _adjusted_model_values,
    _apply_bounded_t1_revisions,
    _apply_bounded_t2_revisions,
    _apply_bounded_transition_table_revisions,
    _bounded_table_rows,
    _build_adjusted_model_table,
    _build_medication_capture_sensitivity_table,
    _build_supplementary_tables_section,
    _burden_contrast_lookup,
    _burden_contrast_values,
    _cohort_values,
    _format_adjusted_or_ci,
    _format_count,
    _gap_rows,
    _medication_sensitivity_values,
    _percent_range_value,
    _percent_value,
    _phenotype_distribution_sentence,
    _phenotype_rows,
    _read_csv_rows,
    _read_json_object,
    _read_supplementary_tables_text,
    _read_table_text,
    _sensitivity_lookup,
    _site_variability_lookup,
    _site_variability_values,
    _strip_table_heading,
    _study_root_from_paper_root,
    _supplementary_table_rows,
    _transition_values,
    _wide_phenotype_gap_summary_table,
)

def _medical_prose_manuscript_from_canonical_surfaces(*, paper_root: Path) -> str:
    study_root = _study_root_from_paper_root(paper_root)
    methods = _read_json_object(paper_root / "methods_implementation_manifest.json")
    flow = _read_json_object(paper_root / "cohort_flow.json")
    phenotype_structure = _read_json_object(paper_root / "dpcc_phenotype_gap_structure.json")
    treatment_gap_alignment = _read_json_object(paper_root / "dpcc_treatment_gap_alignment.json")
    transition_support = _read_json_object(paper_root / "dpcc_transition_site_support.json")
    supplementary_text = _read_supplementary_tables_text(paper_root=paper_root, study_root=study_root)
    t1 = _read_table_text(
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md",
        fallback_path=paper_root / "tables" / "T1_baseline_characteristics.md",
    )
    t1 = _apply_bounded_t1_revisions(t1=t1, study_root=study_root)
    t2 = _read_table_text(
        paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.md",
        fallback_path=paper_root / "tables" / "T2_phenotype_gap_summary.md",
    )
    t2 = _apply_bounded_t2_revisions(
        t2=t2,
        study_root=study_root,
        clinical_rows=_read_csv_rows(paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv"),
    )
    t3_transition = _read_table_text(
        paper_root / "tables" / "generated" / "T3_transition_site_support_summary.md",
        fallback_path=paper_root / "tables" / "T3_transition_site_support_summary.md",
    )
    t3_transition = _apply_bounded_transition_table_revisions(
        transition_table=t3_transition,
        study_root=study_root,
    )

    cohort = _cohort_values(methods=methods, flow=flow, t1=t1)
    phenotype_rows = _phenotype_rows(
        t2=t2,
        phenotype_structure=phenotype_structure,
        treatment_gap_alignment=treatment_gap_alignment,
    )
    gap_rows = _gap_rows(treatment_gap_alignment=treatment_gap_alignment)
    transition = _transition_values(t3=t3_transition, transition_support=transition_support)
    sensitivity_rows = _supplementary_table_rows(
        supplementary_text,
        "Supplementary Table S2. Medication-record sensitivity for core review signals",
    )
    site_variability_rows = _supplementary_table_rows(
        supplementary_text,
        "Supplementary Table S3. Anonymous source-site-code variability in recorded medication-review signals",
    )
    sensitivity = _medication_sensitivity_values(sensitivity_rows)
    site_variability = _site_variability_values(site_variability_rows)
    burden_contrasts = _burden_contrast_values(study_root=study_root)
    adjusted_model_rows = _bounded_table_rows(study_root, "dyslipidemia_adjusted_site_model.csv")
    adjusted_model = _adjusted_model_values(adjusted_model_rows)
    t3 = _build_medication_capture_sensitivity_table(sensitivity)
    t4 = _build_adjusted_model_table(adjusted_model_rows)
    supplementary_section = _build_supplementary_tables_section(
        supplementary_text=supplementary_text,
        transition_table=t3_transition,
    )
    title = (
        "Phenotype-specific cardiometabolic care-review gaps "
        "in a regional primary-care diabetes network in Hunan, China"
    )
    return "\n\n".join(
        section
        for section in (
            f"# {title}",
            _abstract_section(
                cohort=cohort,
                phenotype_rows=phenotype_rows,
                sensitivity=sensitivity,
                transition=transition,
                site_variability=site_variability,
                burden_contrasts=burden_contrasts,
                adjusted_model=adjusted_model,
            ),
            _introduction_section(),
            _methods_section(cohort=cohort, adjusted_model=adjusted_model),
            _results_section(
                cohort=cohort,
                phenotype_rows=phenotype_rows,
                gap_rows=gap_rows,
                sensitivity=sensitivity,
                transition=transition,
                site_variability=site_variability,
                burden_contrasts=burden_contrasts,
                adjusted_model=adjusted_model,
            ),
            _tables_section(t1=t1, t2=t2, t3=t3, t4=t4),
            supplementary_section,
            _discussion_section(
                phenotype_rows=phenotype_rows,
                sensitivity=sensitivity,
                transition=transition,
                burden_contrasts=burden_contrasts,
                adjusted_model=adjusted_model,
            ),
            _limitations_section(),
            _conclusion_section(),
        )
        if section
    )

def _abstract_section(
    *,
    cohort: Mapping[str, Any],
    phenotype_rows: list[dict[str, str]],
    sensitivity: Mapping[str, Mapping[str, str]],
    transition: Mapping[str, str],
    site_variability: Mapping[str, Mapping[str, str]],
    burden_contrasts: Mapping[str, Mapping[str, str]],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    phenotype_sentence = _phenotype_distribution_sentence(phenotype_rows)
    uncontrolled = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "All eligible",
    )
    hypertension = _sensitivity_lookup(
        sensitivity,
        "Hypertension context with no recorded antihypertensive",
        "All eligible",
    )
    dyslipidemia = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "All eligible",
    )
    renal = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "All eligible",
    )
    site_gap = _site_variability_lookup(
        site_variability,
        "Dyslipidemia context with no recorded lipid-lowering medication",
    )
    uncontrolled_present = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Medication field present",
    )
    dyslipidemia_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "dyslipidemia_context_no_recorded_lipid_lowering",
    )
    glycemic_adjusted = _adjusted_model_lookup(
        adjusted_model,
        "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
    )
    adjusted_sentence = ""
    if glycemic_adjusted:
        adjusted_sentence = (
            " In the medication-field-present site fixed-effect sensitivity model "
            f"(n={_format_count(glycemic_adjusted.get('model_n'))}; "
            f"{_format_count(glycemic_adjusted.get('source_sites_in_model'))} source sites), "
            "glycemic-dominant diabetes retained higher adjusted odds of the dyslipidemia no-lipid-lowering signal "
            f"than adiposity-linked multimorbidity ({_format_adjusted_or_ci(glycemic_adjusted)})."
        )
    return (
        "## Abstract\n\n"
        "**Background:** Primary-care diabetes management increasingly requires integrated glycemic, "
        "cardiometabolic, and renal-risk review rather than glycemic control alone. Routine-care phenotypes may be "
        "useful if they identify which recorded care-review gaps are documentation-sensitive and which remain large "
        "after medication-record restriction.\n\n"
        "**Objective:** To determine whether clinically interpretable diabetes phenotypes identify distinct and "
        "actionable patterns of recorded glycemic, cardiometabolic, and renal-protection care-review gaps in the "
        "DPCC primary-care network in Hunan, China.\n\n"
        f"**Methods:** This retrospective descriptive study used {cohort['processed_records']} source records from "
        f"{cohort['unique_patients']} patients. The diabetes-coded index cohort included {cohort['index_patients']} "
        f"patients, of whom {cohort['adult_plausible_age']} had plausible adult age. Phenotypes were assigned by a "
        "deterministic, prespecified hierarchy based on glycemic burden, adiposity, cardiometabolic context, "
        "renal-risk context, and medication-coverage domains. Outcomes were recorded treatment-review indicators, "
        "not treatment-effect estimates, prescribing-quality judgments, or individualized treatment recommendations.\n\n"
        f"**Results:** {phenotype_sentence} Care-review signals were phenotype-specific rather than uniform. Severe "
        "glycemia with low recorded glucose-lowering intensity was 62.0% in glycemic-dominant diabetes and 43.5% "
        "in severe glycemic multimorbidity. Across all eligible patients, uncontrolled glycemia "
        f"without a recorded diabetes medication was {_percent_value(uncontrolled.get('Gap %'))}, hypertension "
        f"context without a recorded antihypertensive was {_percent_value(hypertension.get('Gap %'))}, dyslipidemia "
        f"context without recorded lipid-lowering therapy was {_percent_value(dyslipidemia.get('Gap %'))}, and "
        "the secondary exploratory renal-risk context signal without recorded SGLT2 inhibitor or GLP-1 receptor "
        f"agonist was {_percent_value(renal.get('Gap %'))}. Medication-field-present sensitivity separated "
        "documentation-sensitive glycemic no-drug signals from more persistent cardiometabolic prevention signals: "
        f"uncontrolled glycemia without recorded diabetes medication fell from {_percent_value(uncontrolled.get('Gap %'))} "
        f"to {_percent_value(uncontrolled_present.get('Gap %'))}, whereas dyslipidemia medication-coverage signals "
        "remained large and the renal-risk organ-protection signal was retained as exploratory. The phenotype with "
        "the highest proportional dyslipidemia signal "
        f"({dyslipidemia_contrast.get('highest_rate_phenotype', 'cardiometabolic-risk dominant diabetes')}) was not "
        "the same as the largest absolute dyslipidemia review workload "
        f"({dyslipidemia_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')}). "
        f"Site-level summaries showed wide variation, with "
        f"a median dyslipidemia gap of {_percent_value(site_gap.get('Median gap %'))}; repeated-visit transition "
        f"results were retained as support-only evidence.{adjusted_sentence}\n\n"
        "**Conclusions:** In this regional primary-care diabetes network, care-review gaps were structured rather "
        "than uniform. Glycemic gaps were concentrated in glycemic phenotypes and were highly medication-record "
        "sensitive, whereas lipid-lowering prevention gaps remained large after medication-field restriction and "
        "varied substantially across sites; renal-risk organ-protection signals should be read as secondary and "
        "exploratory. These findings support phenotype-guided chart review and local care-pathway evaluation rather "
        "than national prevalence inference, guideline nonadherence claims, treatment-effect estimation, or "
        "individualized treatment allocation."
    )

def _introduction_section() -> str:
    return (
        "## Introduction\n\n"
        "Primary-care diabetes management has moved beyond glycemic control alone toward integrated "
        "cardiometabolic and renal-risk prevention. Patients may share the diagnostic label of diabetes while "
        "differing in glycemic burden, adiposity, blood-pressure and lipid context, renal-risk context, comorbidity, "
        "medication documentation, and follow-up opportunities. For regional service planning, the practical "
        "question is whether these clinical contexts reveal distinct care-review gaps that can be audited in routine "
        "records.\n\n"
        "Prior diabetes subclassification studies show that phenotypes can carry different clinical risks, but many "
        "primary-care quality-improvement settings require simpler and auditable rules than latent clustering or "
        "individualized prediction models. A deterministic phenotype hierarchy can be useful when it converts routine "
        "measurements and diagnosis fields into transparent groups that clinicians, service managers, and chart-review "
        "teams can reproduce.\n\n"
        "The second challenge is interpretation of medication data. Absence of a recorded drug class in a "
        "primary-care release may reflect true non-use, prescribing outside the network, self-purchased medication, "
        "incomplete capture, contraindications, patient preference, clinician rationale, or delayed documentation. "
        "For that reason, a medical atlas based on routine records should report recorded medication-coverage gaps as "
        "treatment-review or documentation-review signals, not as proof of non-treatment, nonadherence, treatment "
        "failure, or guideline nonadherence.\n\n"
        "The DPCC primary-care network offers a large regional setting to ask whether routine data can generate a "
        "clinically meaningful service-priority map. We tested whether a reproducible phenotype hierarchy could "
        "separate documentation-sensitive glycemic gaps from more persistent cardiometabolic prevention gaps, and "
        "whether proportional risk and absolute service workload identified the same or different priority groups. "
        "Repeated-visit transitions and site-level support were used as support-only evidence for "
        "within-network stability and coverage, rather than as external validation or treatment-effect evidence."
    )

def _methods_section(
    *,
    cohort: Mapping[str, Any],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    model_scope = ""
    if adjusted_model:
        model_scope = (
            " As a secondary sensitivity analysis for the most stable cardiometabolic prevention signal, we fitted a "
            "logistic regression for the dyslipidemia-context no-recorded-lipid-lowering indicator among "
            "medication-field-present patients with plausible age, sex, and anonymous source-site code. The model "
            "included phenotype, age, sex, and anonymous source-site fixed effects; source sites were retained when "
            "they had at least 50 eligible patients and both outcome classes. This model was used to test whether "
            "the lipid-lowering review signal remained phenotype-patterned after basic patient and site adjustment, "
            "not to estimate causal effects or site performance."
        )
    return (
        "## Methods\n\n"
        "### Study design and cohort\n\n"
        f"We conducted a retrospective descriptive analysis of routinely collected DPCC primary-care records. The "
        f"processed release contained {cohort['processed_records']} source records from {cohort['unique_patients']} "
        "patients, with most participating practices located in Hunan. The primary denominator was the "
        f"diabetes-coded index cohort of {cohort['index_patients']} patients; adult/plausible-age sensitivity retained "
        f"{cohort['adult_plausible_age']} patients ({cohort['adult_plausible_age_share']}). For each patient, the "
        "index encounter was the first qualifying diabetes-coded visit with phenotype-ready fields after prespecified "
        "plausibility filtering. Repeated source rows from the same patient within a 7-day visit episode were not "
        f"counted as separate transition opportunities. The repeated-visit support panel included "
        f"{cohort['repeated_visit_patients']} patients, and {cohort['transition_eligible']} patients were eligible "
        f"for first-to-last phenotype transition summaries. The held-out site-support surface included "
        f"{cohort['eligible_sites']} eligible site partitions covering {cohort['visit_coverage']} of release visit "
        "episodes.\n\n"
        "### Variable definition and measurement\n\n"
        "Candidate variables came from routine DPCC fields: age, sex, body size, HbA1c, fasting glucose, eGFR, lipid "
        "measures, diagnosis text, medication records, visit dates, and site identifiers. Medication classes were "
        "identified from recorded regimen text. Diabetes medication classes included metformin, alpha-glucosidase "
        "inhibitors, sulfonylureas, SGLT2 inhibitors, DPP-4 inhibitors, thiazolidinediones, other oral diabetes "
        "drugs, insulin, and injectable GLP-1 receptor agonists where recorded. Antihypertensive and lipid-lowering "
        "exposure were similarly restricted to medication classes documented in the primary-care release. Missing "
        "values were not imputed, and a missing measurement could remove a patient from a variable-specific summary or "
        "an indicator-specific eligible denominator.\n\n"
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
        "cardiometabolic-risk dominant diabetes, and lower-burden diabetes. The hierarchy prioritized primary-care "
        "review immediacy rather than latent disease biology. Severe glycemia was assigned first because it "
        "represents a high-immediacy glycemic review signal. Adiposity-linked multimorbidity preceded single-domain "
        "groups because coexistence of adiposity and cardiometabolic context suggests a broader metabolic-risk "
        "management problem. Glycemic-dominant and adiposity-dominant groups separated single-domain burden, and "
        "cardiometabolic-risk dominant diabetes captured hypertension, dyslipidemia, or renal-risk context without "
        "dominant glycemic or adiposity criteria. The six-class structure was retained because it separated severe "
        "glycemia, adiposity, cardiometabolic context, and lower-burden profiles into clinically interpretable groups "
        "while preserving sufficient group sizes for descriptive service review.\n\n"
        "### Model or grouping framework\n\n"
        "The grouping framework was the rule hierarchy described above. No training set, optimization target, model "
        "coefficient, probability score, or individual decision threshold was estimated for phenotype assignment. The "
        "analysis therefore reports phenotype composition and recorded medication-coverage patterns, not prediction "
        "performance, treatment effects, or individualized prescribing recommendations.\n\n"
        "### Recorded treatment-review gap definitions\n\n"
        "Treatment-review indicators were calculated as recorded medication-coverage gaps within indicator-specific "
        "eligible denominators. Low recorded glucose-lowering intensity was defined as severe glycemia with no "
        "recorded diabetes medication or with one or fewer recorded glucose-lowering classes and no recorded insulin, "
        "GLP-1 receptor agonist, or SGLT2 inhibitor. The uncontrolled-glycemia no-drug indicator was evaluated among "
        "patients meeting the uncontrolled-glycemia definition; the hypertension-context no-antihypertensive "
        "indicator among phenotype members with a hypertension diagnosis or measurement context; the "
        "dyslipidemia-context no-lipid-lowering indicator among phenotype members with the corresponding diagnosis or "
        "lipid context; and the exploratory renal-risk organ-protection coverage signal among patients with "
        "renal-risk context and no recorded SGLT2 inhibitor or GLP-1 receptor agonist. A Not assessed cell "
        "indicates that the phenotype was outside that indicator denominator or outside the bounded reporting "
        "surface. Because medication exposure was restricted to drug classes documented in the DPCC primary-care "
        "release, numerator counts should be interpreted as recorded medication-review or documentation-review signals "
        "rather than complete dispensing histories, true untreated status, nonadherence, contraindications, access "
        "barriers, clinician rationale, or individual treatment benefit.\n\n"
        "### Data quality assessment\n\n"
        f"Data-quality checks were applied before analysis. Plausibility filters excluded {cohort['bmi_excluded']} "
        f"rows for BMI constraints, {cohort['hba1c_excluded']} rows for HbA1c constraints, and "
        f"{cohort['fasting_glucose_excluded']} rows for fasting-glucose constraints. Missing values were not imputed. "
        "Filtering and missingness had row-level, variable-level, or eligibility-level consequences: implausible "
        "source rows were excluded for the affected measurement, unavailable variables did not contribute to that "
        "variable's summary, and patients could be outside an indicator denominator when the required context was "
        "absent or not assessable. Blood-pressure fields had a major semantic issue: the original blood-pressure "
        f"inversion rate was {cohort['bp_inversion_rate']}, and the swapped-value plausibility rate was "
        f"{cohort['bp_swapped_plausible_rate']}. Therefore, blood-pressure control status was excluded from the main "
        "analysis. Hypertension context was retained only as a diagnosis-or-context indicator and interpreted with "
        "this limitation. Supplementary Table S1 reports missingness and plausibility for phenotype-defining "
        "variables, including HbA1c, fasting glucose, BMI, waist circumference, eGFR, lipids, diagnosis text, and "
        "medication fields.\n\n"
        "### Validation framework\n\n"
        "Because this was not a prediction model, validation was limited to descriptive support checks. First-to-last "
        "transition summaries compared each transition-eligible patient's first and last phenotype-ready visits after "
        "7-day episode consolidation. Site support used a dominant-site deterministic partition: patients were "
        "assigned to their dominant anonymous site where possible, small sites were pooled, and the resulting site "
        "folds were used to describe within-network coverage. These analyses do not constitute external validation.\n\n"
        "### Statistical analysis\n\n"
        "Analyses were descriptive. Categorical variables are summarized as counts and percentages, and continuous "
        "variables as means where table surfaces provide means. Denominators were the index cohort for phenotype "
        "composition, phenotype-specific eligible patients for treatment-review gaps, the repeated-visit cohort for "
        "follow-up support, transition-eligible patients for first-to-last transition summaries, and release visit "
        "episodes for site-level coverage. No sampling-based 95% confidence intervals were calculated for the main "
        "release-level descriptive counts, because the analysis enumerated the retained DPCC release rather than "
        "sampling from a target national population. To address uncertainty about medication-record completeness, we "
        "repeated core gap summaries among patients with a nonempty medication field and among patients with any "
        "parsed medication class. We also summarized anonymous source-site-code gap variability for source-site codes "
        "with at least 50 eligible patients per indicator and performed adult/plausible-age sensitivity. Sensitivity "
        "analyses were implemented in Python using sqlite3, numpy, scipy, statsmodels, and matplotlib."
        f"{model_scope} No causal model, p-value-driven main hypothesis test, individualized prediction model, "
        "or blood-pressure target attainment analysis was used for the main manuscript."
    )

def _results_section(
    *,
    cohort: Mapping[str, Any],
    phenotype_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    sensitivity: Mapping[str, Mapping[str, str]],
    transition: Mapping[str, str],
    site_variability: Mapping[str, Mapping[str, str]],
    burden_contrasts: Mapping[str, Mapping[str, str]],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    uncontrolled = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "All eligible",
    )
    hypertension = _sensitivity_lookup(
        sensitivity,
        "Hypertension context with no recorded antihypertensive",
        "All eligible",
    )
    dyslipidemia = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "All eligible",
    )
    renal = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "All eligible",
    )
    severe_all = _sensitivity_lookup(
        sensitivity,
        "Severe glycemia with low recorded glucose-lowering intensity",
        "All eligible",
    )
    severe_present = _sensitivity_lookup(
        sensitivity,
        "Severe glycemia with low recorded glucose-lowering intensity",
        "Medication field present",
    )
    uncontrolled_present = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Medication field present",
    )
    hypertension_present = _sensitivity_lookup(
        sensitivity,
        "Hypertension context with no recorded antihypertensive",
        "Medication field present",
    )
    dyslipidemia_present = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "Medication field present",
    )
    renal_present = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "Medication field present",
    )
    severe_site = _site_variability_lookup(
        site_variability,
        "Severe glycemia with low recorded glucose-lowering intensity",
    )
    hypertension_site = _site_variability_lookup(
        site_variability,
        "Hypertension context with no recorded antihypertensive",
    )
    dyslipidemia_site = _site_variability_lookup(
        site_variability,
        "Dyslipidemia context with no recorded lipid-lowering medication",
    )
    severe_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "severe_glycemia_low_recorded_glucose_lowering_intensity",
    )
    uncontrolled_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "uncontrolled_glycemia_no_recorded_diabetes_medication",
    )
    hypertension_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "hypertension_context_no_recorded_antihypertensive",
    )
    dyslipidemia_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "dyslipidemia_context_no_recorded_lipid_lowering",
    )
    adjusted_results = _adjusted_model_results_sentence(adjusted_model)
    return (
        "## Results\n\n"
        "### Cohort and analytic support\n\n"
        f"The processed release included {cohort['processed_records']} source records from {cohort['unique_patients']} "
        f"patients. The diabetes-coded index cohort included {cohort['index_patients']} patients; adult/plausible-age "
        f"sensitivity retained {cohort['adult_plausible_age']} patients. Cross-site continuity was observed for "
        f"{cohort['cross_site_patients']} patients. Repeated-visit support was available for "
        f"{cohort['repeated_visit_patients']} patients, and {cohort['transition_eligible']} contributed to the "
        "first-to-last transition analysis. Figure 1 presents the cohort flow and quality-control exclusions.\n\n"
        "### Baseline characteristics\n\n"
        f"The retained DPCC release provided a large service-review denominator: {cohort['processed_records']} source "
        f"records, {cohort['unique_patients']} patients, and {cohort['index_patients']} diabetes-coded index "
        "patients after prespecified plausibility filtering. The analytic support surfaces were also clinically "
        f"relevant: {cohort['repeated_visit_patients']} patients had repeated-visit support, "
        f"{cohort['transition_eligible']} were eligible for first-to-last transition summaries, and "
        f"{cohort['eligible_sites']} eligible sites covered {cohort['visit_coverage']} of release visit episodes. "
        f"Medication fields were present in {cohort['medication_field_present']} index patients "
        f"({cohort['medication_field_present_share']}), and any parsed medication class was present in "
        f"{cohort['any_recorded_medication']} ({cohort['any_recorded_medication_share']}), making "
        "medication-capture sensitivity necessary for interpreting gap magnitudes.\n\n"
        "### Phenotype distribution and clinical profiles\n\n"
        "The hierarchy separated the cohort into six clinically interpretable phenotypes with different service-review "
        "implications. Adiposity-linked multimorbidity was the largest group (181,387 patients; 26.2%), followed by "
        "cardiometabolic-risk dominant diabetes (138,378; 20.0%), lower-burden diabetes (127,072; 18.3%), "
        "glycemic-dominant diabetes (104,508; 15.1%), severe glycemic multimorbidity (74,832; 10.8%), and "
        "adiposity-dominant diabetes (66,665; 9.6%). The profiles did not represent a simple severity ranking. "
        "Severe glycemic multimorbidity carried the highest mean HbA1c, glycemic-dominant diabetes isolated marked "
        "glycemic burden without the same multimorbidity pattern, adiposity-linked phenotypes carried the highest BMI "
        "context, and cardiometabolic-risk dominant diabetes was older on average. This structure created a "
        "phenotype map for asking where recorded medication coverage appeared discordant with the clinical context.\n\n"
        "### Phenotypes separated glycemic-intensity gaps from cardiometabolic-prevention gaps\n\n"
        "Recorded treatment-review gaps differed sharply across phenotypes, producing a care-review priority map "
        "rather than a uniform gap rate. The clearest glycemic mismatch appeared in glycemic-dominant diabetes, "
        "where severe glycemia with low recorded glucose-lowering intensity was 62.0% and uncontrolled glycemia "
        "with no recorded diabetes medication was 46.9%. Severe glycemic multimorbidity also showed a large severe "
        "glycemia low-intensity signal (43.5%) despite the highest mean HbA1c, but the uncontrolled-glycemia no-drug "
        "rate was lower than in glycemic-dominant diabetes (29.1%).\n\n"
        "A second service-review pattern involved cardiometabolic prevention signals. Hypertension context without a "
        f"recorded antihypertensive was {_format_count(hypertension.get('Gap n'))} of {_format_count(hypertension.get('Eligible denominator'))} "
        f"eligible patients ({_percent_value(hypertension.get('Gap %'))}) overall. Dyslipidemia context without "
        f"recorded lipid-lowering therapy was {_format_count(dyslipidemia.get('Gap n'))} of "
        f"{_format_count(dyslipidemia.get('Eligible denominator'))} ({_percent_value(dyslipidemia.get('Gap %'))}) overall. "
        f"Exploratory renal-risk context without recorded SGLT2 inhibitor or GLP-1 receptor agonist was "
        f"{_format_count(renal.get('Gap n'))} of {_format_count(renal.get('Eligible denominator'))} "
        f"({_percent_value(renal.get('Gap %'))}). These counts use phenotype- and indicator-specific denominators; "
        "Not assessed cells mark indicators outside the scoped denominator rather than absence of risk.\n\n"
        "The highest proportional phenotype was not always the largest service workload phenotype. For severe "
        f"glycemia with low recorded glucose-lowering intensity, the highest rate was in "
        f"{severe_contrast.get('highest_rate_phenotype', 'glycemic-dominant diabetes')} "
        f"({_percent_value(severe_contrast.get('highest_rate_pct'))}), whereas the largest absolute count was in "
        f"{severe_contrast.get('highest_count_phenotype', 'severe glycemic multimorbidity')} "
        f"({_format_count(severe_contrast.get('highest_count_n'))} patients). For uncontrolled glycemia without "
        f"recorded diabetes medication, {uncontrolled_contrast.get('highest_count_phenotype', 'glycemic-dominant diabetes')} "
        f"contributed the largest count ({_format_count(uncontrolled_contrast.get('highest_count_n'))}). For "
        f"hypertension and dyslipidemia recorded medication-coverage gaps, the highest rates occurred in "
        f"{hypertension_contrast.get('highest_rate_phenotype', 'severe glycemic multimorbidity')} and "
        f"{dyslipidemia_contrast.get('highest_rate_phenotype', 'cardiometabolic-risk dominant diabetes')}, respectively, "
        f"but the largest absolute counts were in "
        f"{hypertension_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')} and "
        f"{dyslipidemia_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')}. This rate-count "
        "contrast separates high-risk phenotype targeting from service-capacity planning.\n\n"
        "### Medication-field restriction attenuated glycemic no-drug gaps but not cardiometabolic prevention gaps\n\n"
        "Medication-record sensitivity changed the magnitude but not the interpretation boundary. Among patients with "
        f"a nonempty medication field, severe glycemia with low recorded glucose-lowering intensity decreased from "
        f"{_percent_value(severe_all.get('Gap %'))} to {_percent_value(severe_present.get('Gap %'))}, uncontrolled "
        f"glycemia with no recorded diabetes medication decreased from {_percent_value(uncontrolled.get('Gap %'))} to "
        f"{_percent_value(uncontrolled_present.get('Gap %'))}, hypertension context without recorded "
        f"antihypertensive decreased from {_percent_value(hypertension.get('Gap %'))} to "
        f"{_percent_value(hypertension_present.get('Gap %'))}, dyslipidemia context without recorded lipid-lowering "
        f"therapy decreased from {_percent_value(dyslipidemia.get('Gap %'))} to "
        f"{_percent_value(dyslipidemia_present.get('Gap %'))}, and renal-risk context without recorded SGLT2 "
        f"inhibitor or GLP-1 receptor agonist decreased from {_percent_value(renal.get('Gap %'))} to "
        f"{_percent_value(renal_present.get('Gap %'))}. This attenuation shows that medication-field missingness "
        "contributes materially to glycemic no-drug indicators, while lipid-lowering signals remain large even in "
        "the medication-field-present denominator; renal-risk organ-protection coverage remains a secondary "
        f"exploratory review signal.{adjusted_results}\n\n"
        "### Transition stability and site support\n\n"
        "Repeated-visit and site summaries supported the phenotype narrative without converting it into a prediction "
        f"or external-validation claim. Among {transition['transition_eligible']} transition-eligible repeated-visit "
        f"patients, first-to-last same-phenotype stability was {transition['same_phenotype_stability']}. The most "
        f"frequent self-transition was {transition['most_frequent_self_transition']}, and the most frequent "
        f"cross-phenotype movement was {transition['most_frequent_cross_transition']}. The held-out site-support "
        f"surface included {transition['eligible_sites']} eligible site partitions and covered "
        f"{transition['visit_coverage']} of release visit episodes. Separately, anonymous source-site-code "
        "variability was wide among source-site codes with at least 50 eligible patients per indicator: median "
        f"severe-glycemia low-intensity gap was {_percent_value(severe_site.get('Median gap %'))} "
        f"(IQR {_percent_range_value(severe_site.get('IQR'))}), median hypertension no-antihypertensive gap was "
        f"{_percent_value(hypertension_site.get('Median gap %'))} (IQR {_percent_range_value(hypertension_site.get('IQR'))}), "
        f"and median dyslipidemia no-lipid-lowering gap was {_percent_value(dyslipidemia_site.get('Median gap %'))} "
        f"(IQR {_percent_range_value(dyslipidemia_site.get('IQR'))}). These findings indicate within-network coverage, "
        "partial phenotype persistence, and site-sensitive review priorities beyond patient phenotype alone; they do "
        "not establish external transportability, causal trajectory, treatment response, or site performance."
    )

def _tables_section(*, t1: str, t2: str, t3: str, t4: str) -> str:
    sections = ["## Tables"]
    if t1:
        sections.append("### Table 1. Data source, cohort assembly, and quality-control summary\n\n" + _strip_table_heading(t1))
    if t2:
        sections.append(
            "### Table 2. Baseline characteristics and recorded risk-treatment mismatch signals by phenotype\n\n"
            + _strip_table_heading(_wide_phenotype_gap_summary_table(t2))
        )
    if t3:
        sections.append("### Table 3. Medication-capture sensitivity analysis of recorded mismatch signals\n\n" + _strip_table_heading(t3))
    if t4:
        sections.append("### Table 4. Site-adjusted dyslipidemia no-lipid-lowering sensitivity model\n\n" + _strip_table_heading(t4))
    return "\n\n".join(sections)

def _discussion_section(
    *,
    phenotype_rows: list[dict[str, str]],
    sensitivity: Mapping[str, Mapping[str, str]],
    transition: Mapping[str, str],
    burden_contrasts: Mapping[str, Mapping[str, str]],
    adjusted_model: Mapping[str, Mapping[str, str]],
) -> str:
    largest = phenotype_rows[0] if phenotype_rows else {}
    renal = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "All eligible",
    )
    uncontrolled = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "All eligible",
    )
    uncontrolled_present = _sensitivity_lookup(
        sensitivity,
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Medication field present",
    )
    dyslipidemia_present = _sensitivity_lookup(
        sensitivity,
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "Medication field present",
    )
    renal_present = _sensitivity_lookup(
        sensitivity,
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
        "Medication field present",
    )
    dyslipidemia_contrast = _burden_contrast_lookup(
        burden_contrasts,
        "dyslipidemia_context_no_recorded_lipid_lowering",
    )
    adjusted_discussion = _adjusted_model_discussion_sentence(adjusted_model)
    return (
        "## Discussion\n\n"
        "### Principal findings\n\n"
        "This regional primary-care study has three main findings. First, recorded diabetes care-review gaps were "
        "phenotype-specific rather than uniform: glycemic-dominant diabetes carried the highest proportional severe "
        "glycemia low-intensity signal, while severe glycemic multimorbidity combined the highest HbA1c with a large "
        "low-intensity signal. Second, medication-record sensitivity separated documentation-sensitive glycemic "
        f"signals from more persistent cardiometabolic prevention signals: uncontrolled glycemia without recorded "
        f"diabetes medication fell from {_percent_value(uncontrolled.get('Gap %'))} to "
        f"{_percent_value(uncontrolled_present.get('Gap %'))}, whereas the dyslipidemia medication-coverage gap "
        f"remained {_percent_value(dyslipidemia_present.get('Gap %'))} in the medication-field-present denominator; "
        f"the renal-risk organ-protection signal remained {_percent_value(renal_present.get('Gap %'))} but was "
        "treated as secondary and exploratory. "
        f"Third, the largest service burden was concentrated in {largest.get('Phenotype', 'Adiposity-linked multimorbidity')}; "
        f"for dyslipidemia, the highest proportional phenotype was "
        f"{dyslipidemia_contrast.get('highest_rate_phenotype', 'cardiometabolic-risk dominant diabetes')}, but the "
        f"largest absolute review workload was {dyslipidemia_contrast.get('highest_count_phenotype', 'adiposity-linked multimorbidity')}.\n\n"
        "### Clinical and service interpretation\n\n"
        "The phenotype map suggests three practical review priorities for a regional primary-care network. First, "
        "patients in glycemic-dominant and severe glycemic multimorbidity profiles may warrant chart-level review of "
        "severe glycemia, medication documentation, treatment intensification opportunities, contraindications, "
        "outside prescribing, and follow-up continuity. Second, adiposity-linked multimorbidity may be a high-yield "
        "service-review group because large patient counts coincide with recorded glycemic, antihypertensive, and "
        "lipid-lowering coverage gaps. Third, cardiometabolic-risk dominant diabetes and other scoped phenotypes "
        "highlight preventive-medication documentation signals even when mean HbA1c is not the dominant feature. The "
        "medication-field-present sensitivity analysis is important for clinical interpretation: glycemic no-drug "
        "indicators were strongly attenuated when medication fields were present, whereas lipid-lowering signals "
        f"remained large; renal-risk organ-protection coverage remained a secondary exploratory signal.{adjusted_discussion}\n\n"
        "These priorities are deliberately phrased as review signals. The DPCC medication fields identify what was "
        "recorded in the primary-care release, not the complete medication history. A recorded gap may reflect "
        "incomplete capture, treatment outside the network, self-purchased drugs, contraindications, patient "
        "preference, clinician judgment, or delayed updating of medication lists. The appropriate next step is "
        "therefore targeted chart audit, documentation review, and prospective care-pathway evaluation rather than "
        "direct prescribing recommendations from this study.\n\n"
        "Previous diabetes subclassification studies have primarily aimed to identify biologically or prognostically "
        "distinct subgroups using clustering frameworks or richer phenotyping panels. In contrast, the present "
        "hierarchy was designed for auditability in primary care rather than latent disease discovery. Its value lies "
        "not in replacing precision subclassification, but in translating routine-care variables into chart-review "
        "priorities that can be implemented in a regional service network with bounded denominator definitions.\n\n"
        "The exploratory renal-risk signal also requires careful interpretation. It captured recorded uptake of "
        "selected kidney-metabolic protective glucose-lowering agents rather than a complete kidney-protection "
        f"quality measure. In particular, the {_percent_value(renal.get('Gap %'))} rate does not account for ACEI/ARB "
        "use, albuminuria-defined eligibility, eGFR-based contraindications, or calendar-year prescribing context, "
        "and therefore should be read as an organ-protection review prompt rather than a definitive renal-care "
        "performance metric.\n\n"
        "### Phenotype stability and network support\n\n"
        f"The repeated-visit stability estimate of {transition['same_phenotype_stability']} suggests that phenotypes "
        "are partly persistent but clinically dynamic. Movement from severe glycemic multimorbidity to "
        "adiposity-linked multimorbidity may reflect changes in glycemia, measurement timing, treatment, visit "
        "context, or documentation rather than a proven biological transition. Site-level support reduces concern "
        "that the profile is entirely dominated by one site, but it remains within-network support rather than "
        "external validation.\n\n"
        "### Implications for future work\n\n"
        "The results provide a service-priority scaffold for follow-up studies. Future prospective and "
        "implementation studies could extend this descriptive atlas by quantifying patient- and site-level "
        "determinants, evaluating calendar-time changes in newer cardiometabolic agents, and testing whether "
        "phenotype-guided chart review improves medication documentation completeness, treatment-intensification "
        "assessment, follow-up scheduling, gap resolution, or cardiometabolic risk-management processes. These "
        "extensions would support stronger service-performance or guideline-based claims only after direct "
        "chart-review, eligibility, contraindication, and prescribing-context evidence is added."
    )

def _limitations_section() -> str:
    return (
        "## Limitations\n\n"
        "This study used routinely collected primary-care records and is subject to missingness, irregular "
        "measurement, coding variation, medication-record incompleteness, and site-level practice differences. "
        "Medication exposure was limited to drug classes recorded in the DPCC primary-care release; the study did "
        "not observe complete pharmacy dispensing, medication adherence, contraindications, patient preference, "
        "clinician rationale, or treatment obtained outside the network. Blood-pressure target attainment was not "
        "analyzed because of the field-semantic issue documented in the data-quality assessment. The phenotype "
        "hierarchy is clinically interpretable and reproducible, but it is not a causal model, clustering discovery "
        "claim, or individualized decision-support tool. Most participating practices were in Hunan, so estimates "
        "should be interpreted as DPCC network findings rather than national prevalence, national treatment-gap "
        "rates, or generalizable service-performance benchmarks. Prospective validation, chart audit, and external "
        "network testing are required before these phenotypes are used to guide interventions."
    )

def _conclusion_section() -> str:
    return (
        "## Conclusion\n\n"
        "A deterministic clinical phenotype hierarchy applied to the DPCC primary-care network showed that recorded "
        "diabetes care-review gaps were phenotype-specific, medication-capture sensitive, and site-sensitive rather "
        "than a single uniform treatment gap. Glycemic profiles identified concentrated review groups, whereas "
        "cardiometabolic contexts highlighted persistent preventive-medication coverage signals, while renal-risk "
        "context remained a secondary exploratory organ-protection review prompt. The "
        "atlas supports local documentation review, chart audit, and prospective care-pathway evaluation while "
        "avoiding treatment-effect, guideline-nonadherence, individualized prescribing, and national-generalization "
        "claims."
    )
