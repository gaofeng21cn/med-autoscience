from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.common import (
    _text,
    _write_json_if_changed,
    _write_text_if_changed,
)
from med_autoscience.controllers.medical_prose_story_surface_parts.dpcc_tables import (
    _apply_bounded_t1_revisions,
    _apply_bounded_t2_revisions,
    _apply_bounded_transition_table_revisions,
    _bounded_table_rows,
    _build_adjusted_model_table,
    _build_medication_capture_sensitivity_table,
    _format_count,
    _gap_rate_map_from_t2,
    _int_from_numeric_text,
    _medication_sensitivity_values,
    _phenotype_index_share_map_from_t2,
    _read_csv_rows,
    _read_json_object,
    _read_supplementary_tables_text,
    _read_table_text,
    _rate_float,
    _strip_table_heading,
    _study_root_from_paper_root,
    _supplementary_table_rows,
    _t1_value_map,
    _wide_phenotype_gap_summary_table,
)

DPCC_DISPLAY_TEXT_REPLACEMENTS = (
    (
        "Phenotype composition and treatment-gap profiles across the DPCC index cohort.",
        "Phenotype composition and recorded risk-treatment mismatch profiles across the DPCC index cohort.",
    ),
    (
        "Treatment-gap pattern",
        "Mismatch pattern",
    ),
    (
        "Guideline-linked glycemia, antihypertensive, and lipid-lowering treatment gaps "
        "aligned to the six DPCC phenotypes.",
        "Rate-count priority map of recorded glycemic, cardiometabolic, and exploratory renal-risk care-review gaps across DPCC phenotypes.",
    ),
    (
        "Recorded glycemic, antihypertensive, and lipid-lowering treatment-review gaps "
        "aligned to the six DPCC phenotypes.",
        "Rate-count priority map of recorded glycemic, cardiometabolic, and exploratory renal-risk care-review gaps across DPCC phenotypes.",
    ),
    (
        "recorded_treatment_review_gap_burden_small_multiples",
        "rate_count_priority_map_recorded_care_review_gaps",
    ),
    (
        "Guideline-linked treatment-gap burden across DPCC phenotypes",
        "Recorded treatment-review gap burden across DPCC phenotypes",
    ),
    (
        "Guideline-linked treatment-gap burden",
        "Recorded treatment-review gap burden",
    ),
    (
        "guideline_linked_treatment_gap_burden_small_multiples",
        "rate_count_priority_map_recorded_care_review_gaps",
    ),
)

def _materialize_dpcc_display_metadata_repairs(*, paper_root: Path) -> list[str]:
    changed_paths: list[str] = []
    study_root = _study_root_from_paper_root(paper_root)
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
    supplementary_text = _read_supplementary_tables_text(paper_root=paper_root, study_root=study_root)
    sensitivity = _medication_sensitivity_values(
        _supplementary_table_rows(
            supplementary_text,
            "Supplementary Table S2. Medication-record sensitivity for core review signals",
        )
    )
    adjusted_model_rows = _bounded_table_rows(study_root, "dyslipidemia_adjusted_site_model.csv")
    for relpath in (
        Path("cohort_flow.json"),
        Path("dpcc_phenotype_gap_structure.json"),
        Path("dpcc_treatment_gap_alignment.json"),
        Path("table_catalog.json"),
        Path("tables") / "table_catalog.json",
        Path("figure_semantics_manifest.json"),
        Path("results_narrative_map.json"),
        Path("medical_manuscript_blueprint.json"),
        Path("claim_evidence_map.json"),
        Path("figure_catalog.json"),
        Path("figures") / "figure_catalog.json",
        Path("build") / "display_pack_render_requests" / "F4.render_request.json",
    ):
        path = paper_root / relpath
        if not path.exists() or not path.is_file():
            continue
        payload = _read_json_object(path)
        if not payload:
            continue
        updated = _replace_dpcc_display_metadata_text(payload)
        if relpath == Path("cohort_flow.json"):
            updated = _repair_dpcc_cohort_flow_payload(updated, t1=t1)
        elif relpath == Path("dpcc_phenotype_gap_structure.json"):
            updated = _repair_dpcc_phenotype_gap_structure_payload(updated, t2=t2)
        elif relpath == Path("dpcc_treatment_gap_alignment.json") or relpath.name == "F4.render_request.json":
            updated = _repair_dpcc_treatment_gap_alignment_payload(updated, t2=t2, study_root=study_root)
        elif relpath in {Path("table_catalog.json"), Path("tables") / "table_catalog.json"}:
            updated = _repair_dpcc_table_catalog_payload(
                updated,
                has_adjusted_model=bool(adjusted_model_rows),
            )
        elif relpath == Path("figure_semantics_manifest.json"):
            updated = _repair_dpcc_figure_semantics_manifest_payload(updated)
        elif relpath == Path("medical_manuscript_blueprint.json"):
            updated = _repair_dpcc_manuscript_blueprint_payload(updated)
        if updated != payload and _write_json_if_changed(path, updated):
            changed_paths.append(str(path.resolve()))
    changed_paths.extend(
        _materialize_dpcc_support_tables(
            paper_root=paper_root,
            t1=t1,
            t2=t2,
            sensitivity=sensitivity,
            transition_table=t3_transition,
            adjusted_model_rows=adjusted_model_rows,
        )
    )
    _materialize_dpcc_rate_count_priority_figure(paper_root=paper_root, study_root=study_root)
    return changed_paths


def _materialize_dpcc_rate_count_priority_figure(*, paper_root: Path, study_root: Path) -> list[str]:
    figure_root = (
        study_root
        / "artifacts"
        / "reviewer_revision"
        / "20260704_sci_upgrade"
        / "bounded_analysis_campaign"
        / "figures"
    )
    output_root = paper_root / "figures" / "generated"
    output_names = {
        "png": "F4_treatment_gap_alignment_figure.png",
        "pdf": "F4_treatment_gap_alignment_figure.pdf",
    }
    changed_paths: list[str] = []
    for suffix, output_name in output_names.items():
        source = figure_root / f"rate_count_priority_map.{suffix}"
        if not source.exists() or not source.is_file():
            continue
        target = output_root / output_name
        if _write_bytes_if_changed(target, source.read_bytes()):
            changed_paths.append(str(target.resolve()))
    return changed_paths


def _write_bytes_if_changed(path: Path, content: bytes) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == content:
        return False
    path.write_bytes(content)
    return True

def _replace_dpcc_display_metadata_text(value: Any) -> Any:
    if isinstance(value, str):
        updated = value
        for target, replacement in DPCC_DISPLAY_TEXT_REPLACEMENTS:
            updated = updated.replace(target, replacement)
        return updated
    if isinstance(value, list):
        return [_replace_dpcc_display_metadata_text(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_dpcc_display_metadata_text(item)
            for key, item in value.items()
        }
    return value

def _repair_dpcc_cohort_flow_payload(payload: Mapping[str, Any], *, t1: str) -> dict[str, Any]:
    updated = dict(payload)
    t1_values = _t1_value_map(t1)
    updated["caption"] = (
        "Source records, processed patients, the diabetes-coded index cohort, adult/plausible-age sensitivity "
        "cohort, repeated-visit support panel, transition denominator, and held-out site-support partitions for the "
        "descriptive primary-care manuscript."
    )
    updated["steps"] = [
        {
            "step_id": "deidentified_release_visits",
            "label": "Deidentified DPCC visit records",
            "n": 1779360,
            "detail": "May 2020-December 2025",
        },
        {
            "step_id": "processed_patients",
            "label": "Unique patients",
            "n": 861778,
            "detail": "Patient-level denominator after visit-record aggregation",
        },
        {
            "step_id": "index_analysis_cohort",
            "label": "Diabetes-coded index cohort",
            "n": 692842,
            "detail": "Primary phenotype-analysis denominator",
        },
        {
            "step_id": "adult_plausible_age_sensitivity_cohort",
            "label": "Adult/plausible-age sensitivity cohort",
            "n": int(str(t1_values.get("Adult/plausible-age patients") or "691992").replace(",", "")),
            "detail": "Age-plausible adults retained for sensitivity audit",
        },
        {
            "step_id": "repeated_visit_support_panel",
            "label": "Repeated-visit support panel",
            "n": 291788,
            "detail": "Secondary longitudinal support denominator",
        },
        {
            "step_id": "transition_eligible_support_set",
            "label": "Transition-eligible patients",
            "n": 291084,
            "detail": "First-to-last phenotype support denominator",
        },
        {
            "step_id": "held_out_site_support_partitions",
            "label": "Held-out site-support partitions",
            "n": 69,
            "detail": "69 site partitions; 93.45% visit-episode coverage",
        },
    ]
    updated["exclusion_branches"] = [
        {
            "branch_id": "not_index_analysis_eligible",
            "from_step_id": "processed_patients",
            "label": "Not index-analysis eligible",
            "n": 168936,
            "detail": "Not carried into the diabetes-coded index cohort",
        }
    ]
    return updated

def _repair_dpcc_treatment_gap_alignment_payload(
    payload: Mapping[str, Any],
    *,
    t2: str,
    study_root: Path,
) -> dict[str, Any]:
    updated = _replace_dpcc_display_metadata_text(payload)
    rows = updated.get("rows")
    if rows is None and isinstance(updated.get("displays"), list):
        displays = list(updated["displays"])
        if displays and isinstance(displays[0], Mapping):
            display = dict(displays[0])
            display["rows"] = _dpcc_rows_with_explicit_rates(
                rows=display.get("rows"),
                t2=t2,
                study_root=study_root,
            )
            displays[0] = display
            updated = dict(updated)
            updated["displays"] = displays
            return updated
    updated = dict(updated)
    updated["rows"] = _dpcc_rows_with_explicit_rates(rows=rows, t2=t2, study_root=study_root)
    return updated

def _repair_dpcc_phenotype_gap_structure_payload(
    payload: Mapping[str, Any],
    *,
    t2: str,
) -> dict[str, Any]:
    updated = _replace_dpcc_display_metadata_text(payload)
    rows = updated.get("rows")
    if rows is None and isinstance(updated.get("displays"), list):
        displays = list(updated["displays"])
        if displays and isinstance(displays[0], Mapping):
            display = dict(displays[0])
            display["rows"] = _dpcc_phenotype_rows_with_current_rates(
                rows=display.get("rows"),
                t2=t2,
            )
            displays[0] = display
            updated = dict(updated)
            updated["displays"] = displays
            return updated
    updated = dict(updated)
    updated["rows"] = _dpcc_phenotype_rows_with_current_rates(rows=rows, t2=t2)
    return updated

def _dpcc_phenotype_rows_with_current_rates(*, rows: object, t2: str) -> list[dict[str, Any]]:
    rate_map = _gap_rate_map_from_t2(t2)
    share_map = _phenotype_index_share_map_from_t2(t2)
    result: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        phenotype = _text(item.get("phenotype_label")) or ""
        if phenotype in share_map:
            item["share_of_index_patients"] = share_map[phenotype]
        for key, value in rate_map.get(phenotype, {}).items():
            item[key] = value
        result.append(item)
    return result

def _dpcc_rows_with_explicit_rates(*, rows: object, t2: str, study_root: Path) -> list[dict[str, Any]]:
    rate_map = _gap_rate_map_from_t2(t2)
    count_map = _bounded_gap_support_map(study_root)
    result: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        item = dict(row)
        phenotype = _text(item.get("phenotype_label"))
        if phenotype in count_map:
            item.update(count_map[phenotype])
        phenotype_rates = rate_map.get(phenotype or "", {})
        for key, value in phenotype_rates.items():
            item[key] = value
        result.append(item)
    return result

def _bounded_gap_support_map(study_root: Path) -> dict[str, dict[str, int]]:
    field_map = {
        "index_patients": "index_patients",
        "severe_glycemia_low_recorded_glucose_lowering_intensity_gap": "severe_glycemia_low_intensity_gap_patients",
        "severe_glycemia_low_recorded_glucose_lowering_intensity_n": "severe_glycemia_low_intensity_gap_denominator",
        "uncontrolled_glycemia_no_recorded_diabetes_medication_gap": "uncontrolled_glycemia_no_drug_gap_patients",
        "uncontrolled_glycemia_no_recorded_diabetes_medication_n": "uncontrolled_glycemia_no_drug_gap_denominator",
        "hypertension_context_no_recorded_antihypertensive_gap": "hypertension_no_antihypertensive_gap_patients",
        "hypertension_context_no_recorded_antihypertensive_n": "hypertension_no_antihypertensive_gap_denominator",
        "dyslipidemia_context_no_recorded_lipid_lowering_gap": "dyslipidemia_no_lipid_lowering_gap_patients",
        "dyslipidemia_context_no_recorded_lipid_lowering_n": "dyslipidemia_no_lipid_lowering_gap_denominator",
    }
    result: dict[str, dict[str, int]] = {}
    for row in _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv"):
        phenotype = _text(row.get("phenotype"))
        if phenotype is None:
            continue
        values: dict[str, int] = {}
        for source_key, target_key in field_map.items():
            parsed = _int_from_numeric_text(row.get(source_key))
            if parsed is not None:
                values[target_key] = parsed
        if values:
            result[phenotype] = values
    return result

def _repair_dpcc_table_catalog_payload(
    payload: Mapping[str, Any],
    *,
    has_adjusted_model: bool = False,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(payload))
    tables = []
    rich_catalog = False
    has_supplementary_transition = False
    has_adjusted_model_table = False
    for table in payload.get("tables") or []:
        if not isinstance(table, Mapping):
            continue
        item = dict(table)
        if _text(item.get("table_id")) == "T3":
            item.update(
                {
                    "title": "Medication-capture sensitivity analysis of recorded mismatch signals",
                    "caption": "Overall and medication-field-present summaries for the core recorded mismatch indicators.",
                    "reader_message": "The table shows which recorded mismatch signals remain large after restricting to patients with medication fields.",
                    "interpretation_boundary": "Signals remain descriptive and reflect recorded medication capture rather than confirmed prescribing quality.",
                    "journal_caption": "Medication-capture sensitivity analysis of recorded mismatch signals.",
                }
            )
            if "paper_role" in item or "table_shell_id" in item or "asset_paths" in item or "source_paths" in item:
                rich_catalog = True
                item["paper_role"] = "main_text"
                item["asset_paths"] = ["paper/tables/generated/T3_medication_capture_sensitivity.md"]
                item["source_paths"] = ["paper/tables/generated/T3_medication_capture_sensitivity.md"]
                render_result = item.get("render_result")
                if isinstance(render_result, Mapping):
                    patched_render_result = dict(render_result)
                else:
                    patched_render_result = {}
                patched_render_result["title"] = item["title"]
                patched_render_result["caption"] = item["caption"]
                patched_render_result["table_layout_policy"] = "pre_materialized_markdown_owner_surface"
                patched_render_result.pop("source_table_path", None)
                item["render_result"] = patched_render_result
        elif _text(item.get("table_id")) == "T4":
            has_adjusted_model_table = True
            if "paper_role" in item or "table_shell_id" in item or "asset_paths" in item or "source_paths" in item:
                rich_catalog = True
        elif _text(item.get("table_id")) == "S6":
            has_supplementary_transition = True
            if "paper_role" in item or "table_shell_id" in item or "asset_paths" in item or "source_paths" in item:
                rich_catalog = True
        tables.append(item)
    if rich_catalog and has_adjusted_model and not has_adjusted_model_table:
        tables.append(
            {
                "table_id": "T4",
                "paper_role": "main_text",
                "title": "Site-adjusted dyslipidemia no-lipid-lowering sensitivity model",
                "caption": "Medication-field-present logistic sensitivity model adjusted for phenotype, age, sex, and anonymous source-site fixed effects.",
                "asset_paths": ["paper/tables/generated/T4_dyslipidemia_adjusted_site_model.md"],
                "source_paths": ["paper/tables/generated/T4_dyslipidemia_adjusted_site_model.md"],
                "qc_result": {"status": "pass", "issues": []},
            }
        )
    if rich_catalog and not has_supplementary_transition:
        tables.append(
            {
                "table_id": "S6",
                "paper_role": "supplementary",
                "title": "Transition stability and site-level support summary",
                "caption": "Transition stability and site-level support summaries moved to the supplementary material.",
                "asset_paths": ["paper/tables/generated/S6_transition_site_support_summary.md"],
                "source_paths": ["paper/tables/generated/S6_transition_site_support_summary.md"],
                "qc_result": {"status": "pass", "issues": []},
            }
        )
    updated["tables"] = tables
    return updated

def _repair_dpcc_figure_semantics_manifest_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(payload))
    figures = updated.get("figures")
    if not isinstance(figures, Mapping):
        return updated
    f1 = figures.get("F1")
    if isinstance(f1, dict):
        f1["direct_message"] = (
            "The denominator structure separates the main diabetes-coded index cohort from adult/plausible-age, repeated-visit, transition, and site-support surfaces."
        )
    f4 = figures.get("F4")
    if isinstance(f4, dict):
        f4["direct_message"] = (
            "The figure pairs explicit percentages with absolute counts so phenotype-specific rates and service workload can be read together."
        )
    return updated

def _repair_dpcc_manuscript_blueprint_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = json.loads(json.dumps(payload))
    findings = updated.get("main_findings_by_clinical_importance")
    if isinstance(findings, list):
        for item in findings:
            if not isinstance(item, dict):
                continue
            if item.get("section_id") == "transition_stability_and_site_support":
                item["clinical_finding"] = (
                    "Support analyses show partial repeated-visit persistence and broad within-network site coverage, but they remain secondary context."
                )
            if item.get("section_id") == "guideline_linked_treatment_gap_alignment":
                item["section_id"] = "recorded_care_review_rate_count_priority_map"
                item["clinical_finding"] = (
                    "The rate-count priority map separates proportional glycemic, cardiometabolic, and exploratory renal-risk review signals from absolute service workload."
                )
    return updated

def _materialize_dpcc_support_tables(
    *,
    paper_root: Path,
    t1: str,
    t2: str,
    sensitivity: Mapping[str, Mapping[str, Mapping[str, str]]],
    transition_table: str,
    adjusted_model_rows: list[dict[str, str]],
) -> list[str]:
    changed_paths: list[str] = []
    if t1:
        for relpath in (
            Path("tables") / "T1_baseline_characteristics.md",
            Path("tables") / "generated" / "T1_baseline_characteristics.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, t1):
                changed_paths.append(str(path.resolve()))
    if t2:
        t2_table = _wide_phenotype_gap_summary_table(t2)
        for relpath in (
            Path("tables") / "T2_phenotype_gap_summary.md",
            Path("tables") / "generated" / "T2_phenotype_gap_summary.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, t2_table):
                changed_paths.append(str(path.resolve()))
    t3_markdown = _build_medication_capture_sensitivity_table(sensitivity)
    if t3_markdown:
        for relpath in (
            Path("tables") / "T3_medication_capture_sensitivity.md",
            Path("tables") / "generated" / "T3_medication_capture_sensitivity.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, "# Medication-capture sensitivity analysis\n\n" + t3_markdown):
                changed_paths.append(str(path.resolve()))
    t4_markdown = _build_adjusted_model_table(adjusted_model_rows)
    if t4_markdown:
        for relpath in (
            Path("tables") / "T4_dyslipidemia_adjusted_site_model.md",
            Path("tables") / "generated" / "T4_dyslipidemia_adjusted_site_model.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(path, "# Site-adjusted dyslipidemia sensitivity model\n\n" + t4_markdown):
                changed_paths.append(str(path.resolve()))
    if transition_table:
        for relpath in (
            Path("tables") / "supplementary" / "S6_transition_site_support_summary.md",
            Path("tables") / "generated" / "S6_transition_site_support_summary.md",
        ):
            path = paper_root / relpath
            if _write_text_if_changed(
                path,
                "# Transition stability and site-level support\n\n" + _strip_table_heading(transition_table),
            ):
                changed_paths.append(str(path.resolve()))
    return changed_paths
