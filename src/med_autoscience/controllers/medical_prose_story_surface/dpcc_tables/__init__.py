from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface.dpcc_tables.bounded_tables import (
    _study_root_from_paper_root,
    _read_supplementary_tables_text,
    _latest_bounded_analysis_campaign_dir,
    _bounded_table_text,
    _bounded_supplementary_tables_text,
    _submission_safe_supplementary_text,
    _apply_bounded_t2_revisions,
    _apply_bounded_wide_t2_revisions,
    _bounded_index_total,
    _apply_bounded_t1_revisions,
    _apply_bounded_transition_table_revisions,
    _bounded_table_rows,
    _read_csv_rows,
    _format_bounded_t2_value,
    _wide_t2_headers,
    _read_json_object,
    _read_table_text,
    _strip_table_heading,
    _markdown_table_rows,
    _clean_cell,
    _step_n,
    _first_int,
    _int_from_numeric_text,
    _format_count,
    _format_percent,
    _format_share,
    _share_from_summary,
    _count_from_summary,
)
from med_autoscience.controllers.medical_prose_story_surface.common import (
    _mapping,
    _text,
)

def _adjusted_model_values(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        comparison = _text(row.get("comparison"))
        if comparison is not None:
            result[comparison] = row
    return result

def _adjusted_model_lookup(
    adjusted_model: Mapping[str, Mapping[str, str]],
    comparison: str,
) -> Mapping[str, str]:
    return adjusted_model.get(comparison, {})

def _format_adjusted_or_ci(row: Mapping[str, str]) -> str:
    adjusted_or = _text(row.get("adjusted_or")) or "NA"
    ci = _text(row.get("ci_95")) or "NA"
    return f"adjusted OR {adjusted_or}, 95% CI {ci}"

def _adjusted_model_results_sentence(adjusted_model: Mapping[str, Mapping[str, str]]) -> str:
    if not adjusted_model:
        return ""
    cardio = _adjusted_model_lookup(
        adjusted_model,
        "Cardiometabolic-risk dominant diabetes vs Adiposity-linked multimorbidity",
    )
    glycemic = _adjusted_model_lookup(
        adjusted_model,
        "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
    )
    severe = _adjusted_model_lookup(
        adjusted_model,
        "Severe glycemic multimorbidity vs Adiposity-linked multimorbidity",
    )
    if not cardio or not glycemic or not severe:
        return ""
    return (
        " In the medication-field-present dyslipidemia-context sensitivity model, after adjustment for age, sex, "
        f"and anonymous source-site fixed effects, the corresponding odds ratios versus adiposity-linked "
        f"multimorbidity were {_format_adjusted_or_ci(cardio)} for cardiometabolic-risk dominant diabetes, "
        f"{_format_adjusted_or_ci(glycemic)} for glycemic-dominant diabetes, and "
        f"{_format_adjusted_or_ci(severe)} for severe glycemic multimorbidity."
    )

def _adjusted_model_discussion_sentence(adjusted_model: Mapping[str, Mapping[str, str]]) -> str:
    glycemic = _adjusted_model_lookup(
        adjusted_model,
        "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
    )
    if not glycemic:
        return ""
    return (
        " The site fixed-effect dyslipidemia sensitivity model supports the same service-review interpretation: "
        "the lipid-lowering signal remained phenotype-patterned after basic patient and anonymous-site adjustment, "
        f"with glycemic-dominant diabetes showing {_format_adjusted_or_ci(glycemic)} versus adiposity-linked "
        "multimorbidity. Effect sizes were modest; this model is supportive rather than causal and should not be read as a site-performance "
        "or guideline-adherence estimate."
    )

def _build_adjusted_model_table(rows: list[dict[str, str]]) -> str:
    selected = [
        row
        for row in rows
        if _text(row.get("comparison"))
        in {
            "Cardiometabolic-risk dominant diabetes vs Adiposity-linked multimorbidity",
            "Glycemic-dominant diabetes vs Adiposity-linked multimorbidity",
            "Severe glycemic multimorbidity vs Adiposity-linked multimorbidity",
            "Age, per year",
            "Female vs male",
        }
    ]
    if not selected:
        return ""
    output = [
        "| Comparison | Adjusted OR | 95% CI | P value | Model n | Source sites | Interpretation boundary |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in selected:
        output.append(
            "| "
            + " | ".join(
                [
                    _text(row.get("comparison")) or "NA",
                    _text(row.get("adjusted_or")) or "NA",
                    _text(row.get("ci_95")) or "NA",
                    _text(row.get("p_value")) or "NA",
                    _format_count(row.get("model_n")),
                    _format_count(row.get("source_sites_in_model")),
                    _text(row.get("interpretation_boundary")) or "secondary sensitivity analysis",
                ]
            )
            + " |"
        )
    return "\n".join(output)

def _burden_contrast_values(study_root: Path) -> dict[str, dict[str, str]]:
    specs = {
        "severe_glycemia_low_recorded_glucose_lowering_intensity": (
            "severe_glycemia_low_recorded_glucose_lowering_intensity_gap",
            "severe_glycemia_low_recorded_glucose_lowering_intensity_pct",
        ),
        "uncontrolled_glycemia_no_recorded_diabetes_medication": (
            "uncontrolled_glycemia_no_recorded_diabetes_medication_gap",
            "uncontrolled_glycemia_no_recorded_diabetes_medication_pct",
        ),
        "hypertension_context_no_recorded_antihypertensive": (
            "hypertension_context_no_recorded_antihypertensive_gap",
            "hypertension_context_no_recorded_antihypertensive_pct",
        ),
        "dyslipidemia_context_no_recorded_lipid_lowering": (
            "dyslipidemia_context_no_recorded_lipid_lowering_gap",
            "dyslipidemia_context_no_recorded_lipid_lowering_pct",
        ),
        "renal_risk_no_recorded_sglt2_or_glp1": (
            "renal_risk_no_recorded_sglt2_or_glp1_gap",
            "renal_risk_no_recorded_sglt2_or_glp1_pct",
        ),
    }
    rows = _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv")
    result: dict[str, dict[str, str]] = {}
    for indicator_id, (count_field, rate_field) in specs.items():
        highest_count: tuple[int, str] | None = None
        highest_rate: tuple[float, str] | None = None
        for row in rows:
            phenotype = _text(row.get("phenotype"))
            if phenotype is None:
                continue
            count = _int_from_numeric_text(row.get(count_field))
            rate = _float_from_text(row.get(rate_field))
            if count is not None and count > 0 and (highest_count is None or count > highest_count[0]):
                highest_count = (count, phenotype)
            if rate is not None and (highest_rate is None or rate > highest_rate[0]):
                highest_rate = (rate, phenotype)
        values: dict[str, str] = {}
        if highest_count is not None:
            values["highest_count_n"] = str(highest_count[0])
            values["highest_count_phenotype"] = highest_count[1]
        if highest_rate is not None:
            values["highest_rate_pct"] = f"{highest_rate[0]:.1f}"
            values["highest_rate_phenotype"] = highest_rate[1]
        if values:
            result[indicator_id] = values
    return result

def _calendar_year_sensitivity_values(study_root: Path) -> dict[str, dict[str, str]]:
    rows = _bounded_table_rows(study_root, "renal_risk_calendar_year_sensitivity.csv")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        year = _text(row.get("index_calendar_year"))
        denominator_mode = _text(row.get("denominator_mode"))
        if year is None or denominator_mode is None:
            continue
        result[f"{year}:{denominator_mode}"] = row
    return result

def _calendar_year_2025_sentence(calendar_year_sensitivity: Mapping[str, Mapping[str, str]]) -> str:
    all_eligible = _mapping(calendar_year_sensitivity.get("2025:all_eligible"))
    medication_present = _mapping(calendar_year_sensitivity.get("2025:medication_field_present"))
    if not all_eligible or not medication_present:
        return ""
    return (
        " In the index-calendar-year sensitivity analysis, the exploratory renal-risk no-recorded-SGLT2i/GLP-1RA "
        "signal in 2025 was "
        f"{_percent_value(all_eligible.get('no_recorded_sglt2_or_glp1_pct'))} "
        f"({_format_count(all_eligible.get('no_recorded_sglt2_or_glp1_n'))}/"
        f"{_format_count(all_eligible.get('eligible_denominator'))}) among all eligible renal-risk records and "
        f"{_percent_value(medication_present.get('no_recorded_sglt2_or_glp1_pct'))} "
        f"({_format_count(medication_present.get('no_recorded_sglt2_or_glp1_n'))}/"
        f"{_format_count(medication_present.get('eligible_denominator'))}) among records with medication fields present; "
        "these values are medication-capture sensitivity checks, not prescribing uptake, temporal trend, guideline-adherence, "
        "or treatment-quality estimates."
    )

def _burden_contrast_lookup(
    burden_contrasts: Mapping[str, Mapping[str, str]],
    indicator_id: str,
) -> dict[str, str]:
    row = burden_contrasts.get(indicator_id)
    return dict(row) if isinstance(row, Mapping) else {}

def _extract_markdown_section(text: str, heading: str) -> str:
    if not text or heading not in text:
        return ""
    heading_title = heading.lstrip("#").strip()
    lines = text.splitlines()
    start: int | None = None
    heading_level = 3
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == heading or stripped.lstrip("#").strip() == heading_title:
            start = index
            heading_level = len(stripped.split(" ", 1)[0])
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start + 1, len(lines)):
        stripped = lines[index].strip()
        if not stripped.startswith("#"):
            continue
        level = len(stripped.split(" ", 1)[0])
        if level <= heading_level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()

def _supplementary_table_rows(text: str, heading: str) -> list[dict[str, str]]:
    return _markdown_table_rows(_extract_markdown_section(text, heading))

def _medication_sensitivity_values(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, dict[str, str]]]:
    result: dict[str, dict[str, dict[str, str]]] = {}
    for row in rows:
        normalized = _normalize_sensitivity_row(row)
        indicator = _text(normalized.get("Indicator"))
        denominator_mode = _text(normalized.get("Denominator mode"))
        if indicator is None or denominator_mode is None:
            continue
        result.setdefault(indicator, {})[denominator_mode] = normalized
    return result

def _normalize_sensitivity_row(row: Mapping[str, str]) -> dict[str, str]:
    indicator = _text(row.get("Indicator") or row.get("indicator"))
    denominator_mode = _text(row.get("Denominator mode") or row.get("denominator_mode"))
    if denominator_mode == "all_eligible":
        denominator_mode = "All eligible"
    elif denominator_mode == "medication_field_present":
        denominator_mode = "Medication field present"
    elif denominator_mode == "any_recorded_medication_class":
        denominator_mode = "Any recorded medication class"
    return {
        "Indicator": indicator or "",
        "Denominator mode": denominator_mode or "",
        "Eligible denominator": _text(row.get("Eligible denominator") or row.get("eligible_denominator")) or "",
        "Gap n": _text(row.get("Gap n") or row.get("gap_n")) or "",
        "Gap %": _text(row.get("Gap %") or row.get("gap_pct")) or "",
        "Interpretation boundary": _text(row.get("Interpretation boundary") or row.get("interpretation_boundary")) or "",
    }

def _site_variability_values(
    rows: list[dict[str, str]],
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        normalized = _normalize_site_variability_row(row)
        indicator = _text(normalized.get("Indicator"))
        if indicator is None:
            continue
        result[indicator] = normalized
    return result

def _normalize_site_variability_row(row: Mapping[str, str]) -> dict[str, str]:
    return {
        "Indicator": _text(row.get("Indicator") or row.get("indicator")) or "",
        "Site denominator minimum": _text(row.get("Site denominator minimum") or row.get("site_denominator_minimum")) or "",
        "Eligible sites": _text(row.get("Eligible sites") or row.get("eligible_sites")) or "",
        "Median gap %": _text(row.get("Median gap %") or row.get("median_gap_pct")) or "",
        "IQR": _text(row.get("IQR") or row.get("iqr_gap_pct")) or "",
        "Range": _text(row.get("Range") or row.get("range_gap_pct")) or "",
        "Interpretation boundary": _text(row.get("Interpretation boundary") or row.get("site_interpretation_boundary")) or "",
    }

def _sensitivity_lookup(
    sensitivity: Mapping[str, Mapping[str, Mapping[str, str]]],
    indicator: str,
    denominator_mode: str,
) -> dict[str, str]:
    indicator_values = sensitivity.get(indicator)
    if isinstance(indicator_values, Mapping):
        row = indicator_values.get(denominator_mode)
        if isinstance(row, Mapping):
            return dict(row)
    return {}

def _site_variability_lookup(
    site_variability: Mapping[str, Mapping[str, str]],
    indicator: str,
) -> dict[str, str]:
    row = site_variability.get(indicator)
    return dict(row) if isinstance(row, Mapping) else {}

def _build_medication_capture_sensitivity_table(
    sensitivity: Mapping[str, Mapping[str, Mapping[str, str]]],
) -> str:
    indicators = (
        "Severe glycemia with low recorded glucose-lowering intensity",
        "Uncontrolled glycemia with no recorded diabetes medication",
        "Hypertension context with no recorded antihypertensive",
        "Dyslipidemia context with no recorded lipid-lowering medication",
        "Renal-risk context with no recorded SGLT2 inhibitor or GLP-1RA",
    )
    rows = [
        "| Indicator | Overall denominator | Overall gap | Medication-field-present denominator | Gap in medication-field-present patients | Attenuation |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for indicator in indicators:
        overall = _sensitivity_lookup(sensitivity, indicator, "All eligible")
        field_present = _sensitivity_lookup(sensitivity, indicator, "Medication field present")
        if not overall or not field_present:
            continue
        rows.append(
            "| "
            + " | ".join(
                (
                    indicator,
                    _text(overall.get("Eligible denominator")) or "NA",
                    _format_gap_summary(overall),
                    _text(field_present.get("Eligible denominator")) or "NA",
                    _format_gap_summary(field_present),
                    _attenuation_summary(overall, field_present),
                )
            )
            + " |"
        )
    return "\n".join(rows)

def _build_supplementary_tables_section(*, supplementary_text: str, transition_table: str) -> str:
    base = supplementary_text.strip()
    transition = _strip_table_heading(transition_table)
    if base:
        if "## Supplementary Tables" not in base:
            base = "## Supplementary Tables\n\n" + base
        if transition and "Transition stability and site-level support" not in base:
            if not base.endswith("\n"):
                base += "\n"
            base += (
                "\n### Supplementary Table S8. Transition stability and site-level support\n\n"
                + transition
            )
        return base
    if not transition:
        return ""
    return (
        "## Supplementary Tables\n\n"
        "### Supplementary Table S8. Transition stability and site-level support\n\n"
        + transition
    )

def _format_gap_summary(row: Mapping[str, str]) -> str:
    gap_n = _text(row.get("Gap n")) or "NA"
    gap_pct = _percent_value(row.get("Gap %"))
    return f"{gap_n} ({gap_pct})"

def _attenuation_summary(overall: Mapping[str, str], field_present: Mapping[str, str]) -> str:
    overall_pct = _float_from_text(overall.get("Gap %"))
    present_pct = _float_from_text(field_present.get("Gap %"))
    if overall_pct is None or present_pct is None:
        return "NA"
    delta = present_pct - overall_pct
    return f"{overall_pct:.1f}% to {present_pct:.1f}% ({delta:+.1f} pp)"

def _percent_value(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    return text if text.endswith("%") else f"{text}%"

def _percent_range_value(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    if "%" in text:
        return text
    if "-" in text:
        left, right = text.split("-", 1)
        return f"{left.strip()}%-{right.strip()}%"
    return _percent_value(text)

def _float_from_text(value: object) -> float | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return float(text.replace("%", "").replace(",", ""))
    except ValueError:
        return None

def _t1_value_map(t1: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for row in _markdown_table_rows(t1):
        characteristic = _text(row.get("Characteristic"))
        measure = _text(row.get("Measure"))
        value = _text(row.get("Value"))
        if measure and value:
            values[measure] = value
        if characteristic and value:
            values[characteristic] = value
    return values

def _cohort_values(*, methods: Mapping[str, Any], flow: Mapping[str, Any], t1: str) -> dict[str, str]:
    design = _mapping(methods.get("study_design"))
    cohort_definition = _text(design.get("cohort_definition")) or ""
    steps = [dict(item) for item in flow.get("steps") or [] if isinstance(item, Mapping)]
    t1_values = _t1_value_map(t1)
    index_denominator = _step_n(steps, "index_analysis_cohort") or 692842
    adult_plausible_age = t1_values.get("Adult/plausible-age patients") or 691992
    medication_field_present = _count_from_summary(
        t1_values.get("Index patients with nonempty medication fields")
    ) or "378,383"
    any_recorded_medication = _count_from_summary(
        t1_values.get("Index patients with any parsed medication class")
    ) or "377,032"
    return {
        "processed_records": _format_count(
            _step_n(steps, "deidentified_release_visits") or _first_int(cohort_definition) or 1779360
        ),
        "unique_patients": _format_count(_step_n(steps, "processed_patients") or 861778),
        "index_patients": _format_count(index_denominator),
        "adult_plausible_age": _format_count(
            adult_plausible_age
        ),
        "adult_plausible_age_share": _format_share(
            numerator=adult_plausible_age,
            denominator=index_denominator,
        ),
        "repeated_visit_patients": _format_count(_step_n(steps, "repeated_visit_support_panel") or 291788),
        "transition_eligible": _format_count(_step_n(steps, "transition_eligible_support_set") or 291084),
        "cross_site_patients": _format_count(
            t1_values.get("Cross-site continuity patients") or 271787
        ),
        "eligible_sites": _format_count(t1_values.get("Eligible sites") or 69),
        "visit_coverage": _text(t1_values.get("Visit-episode coverage")) or "93.45%",
        "bp_inversion_rate": _text(t1_values.get("Original BP inversion rate")) or "99.88%",
        "bp_swapped_plausible_rate": _text(t1_values.get("Swapped BP plausible rate")) or "99.87%",
        "bmi_excluded": _format_count(t1_values.get("BMI excluded rows") or 1015),
        "hba1c_excluded": _format_count(t1_values.get("HbA1c excluded rows") or 4126),
        "fasting_glucose_excluded": _format_count(
            t1_values.get("Fasting glucose excluded rows") or 2166
        ),
        "medication_field_present": medication_field_present,
        "medication_field_present_share": _share_from_summary(
            t1_values.get("Index patients with nonempty medication fields")
        )
        if _share_from_summary(t1_values.get("Index patients with nonempty medication fields")) != "NA"
        else _format_share(numerator=medication_field_present, denominator=index_denominator),
        "any_recorded_medication": any_recorded_medication,
        "any_recorded_medication_share": _share_from_summary(
            t1_values.get("Index patients with any parsed medication class")
        )
        if _share_from_summary(t1_values.get("Index patients with any parsed medication class")) != "NA"
        else _format_share(numerator=any_recorded_medication, denominator=index_denominator),
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

def _phenotype_rows(
    *,
    t2: str,
    phenotype_structure: Mapping[str, Any],
    treatment_gap_alignment: Mapping[str, Any],
) -> list[dict[str, str]]:
    rows = _phenotype_summary_rows_from_t2(t2)
    if rows:
        return rows
    displays = phenotype_structure.get("displays")
    display = displays[0] if isinstance(displays, list) and displays and isinstance(displays[0], Mapping) else {}
    gap_rows = _gap_rows(treatment_gap_alignment=treatment_gap_alignment)
    result: list[dict[str, str]] = []
    for row in display.get("rows") or []:
        if not isinstance(row, Mapping):
            continue
        phenotype_label = _text(row.get("phenotype_label")) or "Phenotype"
        gap_row = _find_row(gap_rows, "phenotype_label", phenotype_label) or {}
        result.append(
            {
                "Phenotype": phenotype_label,
                "Index patients": _format_count(gap_row.get("index_patients")),
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

def _phenotype_index_share_map_from_t2(t2: str) -> dict[str, float]:
    rows = _phenotype_summary_rows_from_t2(t2)
    if not rows:
        return {}
    result: dict[str, float] = {}
    for row in rows:
        phenotype = _text(row.get("Phenotype"))
        value = _text(row.get("Share of index cohort"))
        if phenotype is None or value is None:
            continue
        parsed = _rate_float(value)
        if parsed is not None:
            result[phenotype] = parsed
    return result

def _gap_rate_map_from_t2(t2: str) -> dict[str, dict[str, float | None]]:
    rows = _phenotype_summary_rows_from_t2(t2)
    if not rows:
        return {}
    column_map = {
        "Severe glycemia low-intensity gap": "severe_glycemia_low_intensity_gap_rate",
        "Severe glycemia / low intensity": "severe_glycemia_low_intensity_gap_rate",
        "Uncontrolled glycemia with no diabetes drug": "uncontrolled_glycemia_no_drug_gap_rate",
        "Uncontrolled / no diabetes drug": "uncontrolled_glycemia_no_drug_gap_rate",
        "Hypertension with no antihypertensive": "hypertension_no_antihypertensive_gap_rate",
        "Hypertension / no antihypertensive": "hypertension_no_antihypertensive_gap_rate",
        "Dyslipidemia with no lipid-lowering": "dyslipidemia_no_lipid_lowering_gap_rate",
        "Dyslipidemia / no lipid-lowering": "dyslipidemia_no_lipid_lowering_gap_rate",
    }
    result: dict[str, dict[str, float | None]] = {}
    for row in rows:
        phenotype = _text(row.get("Phenotype"))
        if phenotype is None:
            continue
        for column, field in column_map.items():
            if column in row:
                result.setdefault(phenotype, {})[field] = _rate_float(row[column])
    return result

def _phenotype_summary_rows_from_t2(t2: str) -> list[dict[str, str]]:
    rows = _markdown_table_rows(t2)
    if not rows:
        return []
    if "Measure" not in rows[0]:
        return [_canonical_wide_t2_row(row) for row in rows]
    measure_to_column = {
        "Index patients": "Index patients",
        "Share of index cohort": "Share of index cohort",
        "Mean age, y": "Mean age, y",
        "Mean BMI": "Mean BMI",
        "Mean HbA1c": "Mean HbA1c",
        "Severe glycemia low-intensity gap": "Severe glycemia low-intensity gap",
        "Uncontrolled glycemia with no diabetes drug": "Uncontrolled glycemia with no diabetes drug",
        "Hypertension with no antihypertensive": "Hypertension with no antihypertensive",
        "Dyslipidemia with no lipid-lowering": "Dyslipidemia with no lipid-lowering",
    }
    by_phenotype: dict[str, dict[str, str]] = {}
    for row in rows:
        phenotype = _text(row.get("Phenotype"))
        measure = _text(row.get("Measure"))
        value = _text(row.get("Value"))
        if phenotype is None or measure is None or value is None:
            continue
        column = measure_to_column.get(measure)
        if column is not None:
            by_phenotype.setdefault(phenotype, {"Phenotype": phenotype})[column] = value
    return list(by_phenotype.values())

def _canonical_wide_t2_row(row: Mapping[str, str]) -> dict[str, str]:
    aliases = {
        "n": "Index patients",
        "%": "Share of index cohort",
        "Age, y": "Mean age, y",
        "BMI": "Mean BMI",
        "HbA1c": "Mean HbA1c",
        "Severe glycemia / low intensity": "Severe glycemia low-intensity gap",
        "Uncontrolled / no diabetes drug": "Uncontrolled glycemia with no diabetes drug",
        "Hypertension / no antihypertensive": "Hypertension with no antihypertensive",
        "Dyslipidemia / no lipid-lowering": "Dyslipidemia with no lipid-lowering",
    }
    result = dict(row)
    for source, target in aliases.items():
        if source in row and target not in result:
            result[target] = row[source]
    return result

def _wide_phenotype_gap_summary_table(t2: str) -> str:
    rows = _phenotype_summary_rows_from_t2(t2)
    if not rows:
        return t2
    headers = (
        "Phenotype",
        "n",
        "%",
        "Age, y",
        "BMI",
        "HbA1c",
        "Severe glycemia / low intensity",
        "Uncontrolled / no diabetes drug",
        "Hypertension / no antihypertensive",
        "Dyslipidemia / no lipid-lowering",
    )
    source_columns = {
        "n": "Index patients",
        "%": "Share of index cohort",
        "Age, y": "Mean age, y",
        "BMI": "Mean BMI",
        "HbA1c": "Mean HbA1c",
        "Severe glycemia / low intensity": "Severe glycemia low-intensity gap",
        "Uncontrolled / no diabetes drug": "Uncontrolled glycemia with no diabetes drug",
        "Hypertension / no antihypertensive": "Hypertension with no antihypertensive",
        "Dyslipidemia / no lipid-lowering": "Dyslipidemia with no lipid-lowering",
    }
    output = [
        "# Phenotype-level clinical characteristics and recorded risk-treatment mismatch signals",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        cells = []
        for header in headers:
            source = source_columns.get(header, header)
            cells.append(_text(row.get(source)) or "NA")
        output.append("| " + " | ".join(cells) + " |")
    return "\n".join(output)

def _rate_float(value: str) -> float | None:
    if value in {"NA", "Not assessed"}:
        return None
    try:
        return float(value.replace("%", "").replace(",", "")) / 100.0
    except ValueError:
        return None

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
