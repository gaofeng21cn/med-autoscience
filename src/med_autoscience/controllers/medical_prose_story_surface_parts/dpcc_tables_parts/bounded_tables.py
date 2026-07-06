from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.common import _text


def _study_root_from_paper_root(paper_root: Path) -> Path:
    resolved = paper_root.expanduser().resolve()
    for candidate in (resolved.parent, *resolved.parents):
        if (candidate / "artifacts").is_dir() and (
            (candidate / "artifacts" / "controller").exists()
            or (candidate / "artifacts" / "reviewer_revision").exists()
            or (candidate / "submission").exists()
        ):
            return candidate
    return resolved.parent

def _read_supplementary_tables_text(*, paper_root: Path, study_root: Path) -> str:
    reviewer_revision_supplement = _bounded_supplementary_tables_text(study_root)
    if reviewer_revision_supplement:
        return reviewer_revision_supplement
    candidates = (
        study_root / "submission" / "supplementary_tables.md",
        study_root / "submission" / "supplementary_material.md",
        paper_root / "submission_minimal" / "supplementary_tables.md",
        paper_root / "submission_minimal" / "supplementary_material.md",
    )
    for path in candidates:
        if path.exists() and path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if "Supplementary Table" in text:
                return text
    return ""

def _latest_bounded_analysis_campaign_dir(study_root: Path) -> Path | None:
    root = study_root / "artifacts" / "reviewer_revision"
    if not root.exists():
        return None
    candidates = [
        path
        for path in root.glob("*/bounded_analysis_campaign")
        if path.is_dir() and (path / "tables").is_dir()
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda path: (path.stat().st_mtime, str(path)))

def _bounded_table_text(study_root: Path, filename: str) -> str:
    campaign_dir = _latest_bounded_analysis_campaign_dir(study_root)
    if campaign_dir is None:
        return ""
    path = campaign_dir / "tables" / filename
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()

def _bounded_supplementary_tables_text(study_root: Path) -> str:
    sections: list[str] = []
    for title, filename in (
        (
            "Supplementary Table S1. Missingness and plausibility atlas for phenotype-defining variables",
            "missingness_plausibility_atlas.md",
        ),
        (
            "Supplementary Table S2. Medication-record sensitivity for core review signals",
            "medication_field_present_sensitivity.md",
        ),
        (
            "Supplementary Table S3. Anonymous source-site-code variability in recorded medication-review signals",
            "site_gap_variability_summary.md",
        ),
        (
            "Supplementary Table S4. Adult/plausible-age boundary sensitivity",
            "adult_boundary_sensitivity.md",
        ),
        (
            "Supplementary Table S5. Diagnostic variable ascertainment",
            "diagnostic_variable_ascertainment_table.md",
        ),
        (
            "Supplementary Table S6. Rate-count priority map for recorded medication-review signals",
            "rate_count_priority_map.md",
        ),
        (
            "Supplementary Table S7. Renal-risk calendar-year medication-capture sensitivity",
            "renal_risk_calendar_year_sensitivity.md",
        ),
    ):
        table = _bounded_table_text(study_root, filename)
        if not table:
            continue
        sections.append(f"### {title}\n\n{_submission_safe_supplementary_text(_strip_table_heading(table))}")
    if not sections:
        return ""
    return "## Supplementary Tables\n\n" + "\n\n".join(sections)

def _submission_safe_supplementary_text(text: str) -> str:
    return text.replace("糖尿病", "the Chinese diabetes term")

def _apply_bounded_t2_revisions(
    *,
    t2: str,
    study_root: Path,
    clinical_rows: list[dict[str, str]] | None = None,
) -> str:
    risk_rows = _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv")
    if not t2 or not risk_rows:
        return t2
    values_by_phenotype: dict[str, dict[str, str]] = {}
    for row in risk_rows:
        phenotype = _text(row.get("phenotype"))
        if phenotype is None:
            continue
        values_by_phenotype[phenotype] = row
    for row in clinical_rows or []:
        phenotype = _text(row.get("Phenotype"))
        if phenotype is None or phenotype not in values_by_phenotype:
            continue
        values_by_phenotype[phenotype].update(
            {
                "Mean age, y": _text(row.get("Mean age, y") or row.get("Age, y")) or "",
                "Mean BMI": _text(row.get("Mean BMI") or row.get("BMI")) or "",
                "Mean HbA1c": _text(row.get("Mean HbA1c") or row.get("HbA1c")) or "",
            }
        )
    measure_to_field = {
        "Index patients": "index_patients",
        "Share of index cohort": "share_of_index_cohort",
        "Mean age, y": "Mean age, y",
        "Mean BMI": "Mean BMI",
        "Mean HbA1c": "Mean HbA1c",
        "Severe glycemia low-intensity gap": "severe_glycemia_low_recorded_glucose_lowering_intensity_pct",
        "Uncontrolled glycemia with no diabetes drug": "uncontrolled_glycemia_no_recorded_diabetes_medication_pct",
        "Hypertension with no antihypertensive": "hypertension_context_no_recorded_antihypertensive_pct",
        "Dyslipidemia with no lipid-lowering": "dyslipidemia_context_no_recorded_lipid_lowering_pct",
    }
    changed = False
    output: list[str] = []
    for line in t2.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"---", "Phenotype"}:
            output.append(line)
            continue
        phenotype, measure, old_value = cells
        field = measure_to_field.get(measure)
        bounded_row = values_by_phenotype.get(phenotype)
        if field is None or bounded_row is None:
            output.append(line)
            continue
        new_value = _format_bounded_t2_value(bounded_row.get(field), percent=field.endswith("_pct") or field == "share_of_index_cohort")
        if new_value and new_value != old_value:
            cells[2] = new_value
            line = "| " + " | ".join(cells) + " |"
            changed = True
        output.append(line)
    updated = "\n".join(output) if changed else t2
    return _apply_bounded_wide_t2_revisions(t2=updated, values_by_phenotype=values_by_phenotype)

def _apply_bounded_wide_t2_revisions(
    *,
    t2: str,
    values_by_phenotype: Mapping[str, Mapping[str, str]],
) -> str:
    rows = _markdown_table_rows(t2)
    if not rows or "Measure" in rows[0]:
        return t2
    field_by_header = {
        "n": ("index_patients", False),
        "Index patients": ("index_patients", False),
        "%": ("share_of_index_cohort", True),
        "Share of index cohort": ("share_of_index_cohort", True),
        "Age, y": ("Mean age, y", False),
        "Mean age, y": ("Mean age, y", False),
        "BMI": ("Mean BMI", False),
        "Mean BMI": ("Mean BMI", False),
        "HbA1c": ("Mean HbA1c", False),
        "Mean HbA1c": ("Mean HbA1c", False),
        "Severe glycemia / low intensity": ("severe_glycemia_low_recorded_glucose_lowering_intensity_pct", True),
        "Severe glycemia low-intensity gap": ("severe_glycemia_low_recorded_glucose_lowering_intensity_pct", True),
        "Uncontrolled / no diabetes drug": ("uncontrolled_glycemia_no_recorded_diabetes_medication_pct", True),
        "Uncontrolled glycemia with no diabetes drug": ("uncontrolled_glycemia_no_recorded_diabetes_medication_pct", True),
        "Hypertension / no antihypertensive": ("hypertension_context_no_recorded_antihypertensive_pct", True),
        "Hypertension with no antihypertensive": ("hypertension_context_no_recorded_antihypertensive_pct", True),
        "Dyslipidemia / no lipid-lowering": ("dyslipidemia_context_no_recorded_lipid_lowering_pct", True),
        "Dyslipidemia with no lipid-lowering": ("dyslipidemia_context_no_recorded_lipid_lowering_pct", True),
    }
    changed = False
    output: list[str] = []
    for line in t2.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"---", "Phenotype"}:
            output.append(line)
            continue
        bounded_row = values_by_phenotype.get(cells[0])
        if bounded_row is None:
            output.append(line)
            continue
        headers = _wide_t2_headers(t2)
        if len(cells) != len(headers):
            output.append(line)
            continue
        for index, header in enumerate(headers):
            spec = field_by_header.get(header)
            if spec is None:
                continue
            field, percent = spec
            new_value = _format_bounded_t2_value(bounded_row.get(field), percent=percent)
            if new_value and new_value != cells[index]:
                cells[index] = new_value
                changed = True
        output.append("| " + " | ".join(cells) + " |")
    return "\n".join(output) if changed else t2

def _bounded_index_total(study_root: Path) -> int | None:
    total = 0
    seen = False
    for row in _bounded_table_rows(study_root, "risk_treatment_mismatch_matrix.csv"):
        value = _int_from_numeric_text(row.get("index_patients"))
        if value is None:
            continue
        total += value
        seen = True
    return total if seen else None

def _apply_bounded_t1_revisions(*, t1: str, study_root: Path) -> str:
    index_total = _bounded_index_total(study_root)
    if not t1 or index_total is None:
        return t1
    changed = False
    output: list[str] = []
    for line in t1.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"---", "Characteristic"}:
            output.append(line)
            continue
        characteristic, measure, old_value = cells
        if characteristic == "Cohort definition — Index patients" or measure == "Index patients":
            new_value = _format_count(index_total)
            if new_value != old_value:
                cells[2] = new_value
                line = "| " + " | ".join(cells) + " |"
                changed = True
        output.append(line)
    return "\n".join(output) if changed else t1

def _apply_bounded_transition_table_revisions(*, transition_table: str, study_root: Path) -> str:
    index_total = _bounded_index_total(study_root)
    if not transition_table or index_total is None:
        return transition_table
    changed = False
    output: list[str] = []
    for line in transition_table.splitlines():
        if not line.strip().startswith("|") or line.count("|") < 4:
            output.append(line)
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3 or cells[0] in {"---", "Section"}:
            output.append(line)
            continue
        section, metric, old_value = cells
        if section == "Transition support" and metric == "Index patients":
            new_value = _format_count(index_total)
            if new_value != old_value:
                cells[2] = new_value
                line = "| " + " | ".join(cells) + " |"
                changed = True
        output.append(line)
    return "\n".join(output) if changed else transition_table

def _bounded_table_rows(study_root: Path, filename: str) -> list[dict[str, str]]:
    campaign_dir = _latest_bounded_analysis_campaign_dir(study_root)
    if campaign_dir is None:
        return []
    path = campaign_dir / "tables" / filename
    if not path.exists() or not path.is_file():
        return []
    if path.suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    return _markdown_table_rows(path.read_text(encoding="utf-8"))

def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]

def _format_bounded_t2_value(value: object, *, percent: bool) -> str:
    text = _text(value)
    if text is None or text in {"", "NA", "Not assessed"}:
        return "NA"
    if percent:
        return text if text.endswith("%") else f"{text}%"
    return _format_count(text)

def _wide_t2_headers(t2: str) -> list[str]:
    for line in t2.splitlines():
        if line.strip().startswith("|"):
            return [_clean_cell(cell) for cell in line.strip().strip("|").split("|")]
    return []

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

def _int_from_numeric_text(value: object) -> int | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return int(text.replace(",", ""))
    except ValueError:
        return None

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

def _format_share(*, numerator: object, denominator: int) -> str:
    text = _text(numerator)
    if text is None or denominator <= 0:
        return "NA"
    try:
        value = int(text.replace(",", ""))
    except ValueError:
        return "NA"
    return f"{value / denominator * 100:.1f}%"

def _share_from_summary(value: object) -> str:
    text = _text(value)
    if text is None:
        return "NA"
    match = re.search(r"\(([^)]+)\)", text)
    return match.group(1) if match else "NA"

def _count_from_summary(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text.split("(", 1)[0].strip()
