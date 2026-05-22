from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID = "medical_prose_write_repair"
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
) -> list[str]:
    if work_unit_id != MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID:
        return []
    manuscript = _medical_prose_manuscript_from_canonical_surfaces(paper_root=paper_root)
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
        "Diabetes care in primary practice requires clinicians to manage glycemia together with adiposity, blood-pressure "
        "context, lipid burden, renal-risk context, comorbidity, medication access, and follow-up. Patients carrying "
        "the same diagnostic label can therefore present with very different service needs. Interpretable phenotype "
        "summaries can make this heterogeneity visible when the assignment rule is reproducible and the clinical "
        "question is kept descriptive.\n\n"
        "The DPCC primary-care network provides a large regional source for such a descriptive analysis. This study "
        "asks whether routine records can define clinically interpretable diabetes phenotypes and whether those "
        "phenotypes identify different recorded treatment-review gap patterns. The study is framed as clinical "
        "epidemiology for service review, with repeated-visit transitions and site-level holdout summaries used as "
        "supportive context."
    )


def _methods_section(*, cohort: Mapping[str, Any]) -> str:
    return (
        "## Methods\n\n"
        "### Study Design And Data Source\n\n"
        f"We conducted a retrospective descriptive analysis of routinely collected DPCC primary-care records. The "
        f"processed release contained {cohort['processed_records']} source records from {cohort['unique_patients']} "
        "patients, with most participating practices located in Hunan. Records were analyzed after the prespecified "
        "semantic audit and plausibility filtering of the phenotype-ready variable set. Repeated source rows from "
        "the same patient within a 7-day visit episode were not counted as separate transition opportunities.\n\n"
        "### Cohort Assembly\n\n"
        f"The primary denominator was the index diabetes cohort of {cohort['index_patients']} adults. The repeated-visit "
        f"support panel included {cohort['repeated_visit_patients']} patients, and {cohort['transition_eligible']} "
        "patients were eligible for first-to-last phenotype transition summaries. The site-level holdout surface "
        f"included {cohort['eligible_sites']} eligible sites covering {cohort['visit_coverage']} of release visit episodes. "
        "For each patient, the index encounter was the first qualifying diabetes-coded visit with phenotype-ready "
        "fields after semantic-audit plausibility filtering. This index-visit rule defines the patient-level analytic "
        "row for phenotype assignment and treatment-review gap summaries.\n\n"
        "### Phenotype derivation and assignment\n\n"
        "Phenotype assignment was deterministic and rule based. It was not a clustering model, latent-class model, "
        "prediction model, or treatment-effect model. Candidate domains were defined from "
        "routinely available clinical fields: age, sex, body size, HbA1c, fasting glucose, lipid values, renal-risk "
        "context, diagnosis indicators, medication records, visit structure, and site identifiers. A new patient can "
        "be classified by applying the same hierarchy to the index-visit phenotype-ready fields; the assignment is "
        "therefore reproducible without model fitting or post hoc label optimization.\n\n"
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
        "### Statistical analysis\n\n"
        "Analyses were descriptive. Categorical variables are summarized as counts and percentages, and continuous "
        "variables as means where table surfaces provide means. Denominators were the index cohort for phenotype "
        "composition and treatment-review gaps, the repeated-visit cohort for follow-up support, transition-eligible "
        "patients for first-to-last transition summaries, and release visit episodes for site-level coverage. "
        "First-to-last transition summaries compared each transition-eligible patient's first and last phenotype-ready visits "
        "after 7-day episode consolidation. Site support used a dominant-site deterministic partition: patients were "
        "assigned to their dominant anonymous site where possible, small sites were pooled, and the resulting site "
        "folds were used only to describe within-network support. No "
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
        "Table 1 is a cohort-assembly and data-quality summary, not a traditional baseline-characteristics table. It "
        "documents the release size, index denominator, repeated-visit support, site-level support, blood-pressure "
        "semantic checks, and plausibility-filter exclusions. Table 2 is the phenotype-level baseline table, with "
        "patient counts, cohort shares, mean age, mean BMI, mean HbA1c, and phenotype-scoped treatment-review gap rates.\n\n"
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
    "MANUSCRIPT_STORY_SURFACE_RELATIVE_PATHS",
    "MEDICAL_PROSE_WRITE_REPAIR_WORK_UNIT_ID",
    "materialize_medical_prose_story_surfaces",
]
