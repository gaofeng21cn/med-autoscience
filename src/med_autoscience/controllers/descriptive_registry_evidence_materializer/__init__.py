from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers.descriptive_registry_evidence_materializer.reporting_contract import (
    _claim_rows,
    _closed_charter_expectations,
    _ledger_claims_from_claims,
    _medical_analysis_contract,
    _reporting_checklist,
    _results_narrative_map,
)
from med_autoscience.policies.medical_reporting_checklist import (
    BASELINE_CHARACTERISTICS_REPORTING_ITEMS,
    CLINICAL_ACTIONABILITY_ITEMS,
    DATA_QUALITY_REPORTING_ITEMS,
    MANUSCRIPT_VOICE_REPORTING_ITEMS,
    METHODS_COMPLETENESS_ITEMS,
    PHENOTYPE_DERIVATION_REPORTING_ITEMS,
    STATISTICAL_REPORTING_ITEMS,
    TREATMENT_GAP_REPORTING_ITEMS,
)
from med_autoscience.policies.medical_reporting_contract import (
    display_story_role_for_requirement_key,
    resolve_medical_reporting_contract,
)

CONTROLLER_ID = "descriptive_registry_evidence_materializer"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, headers: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def _resolve_ref(value: object, *, base: Path) -> Path:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("expected non-empty path ref")
    path = Path(raw).expanduser()
    if path.is_absolute():
        return path.resolve()
    return (base / path).resolve()


def _read_study_yaml(study_root: Path) -> dict[str, Any]:
    payload = yaml.safe_load((study_root / "study.yaml").read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("study.yaml must contain a YAML mapping")
    return payload


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [{str(key): str(value or "").strip() for key, value in row.items()} for row in reader]


def _float_value(row: dict[str, str], column: str) -> float | None:
    raw = str(row.get(column) or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _nonmissing(row: dict[str, str], column: str) -> bool:
    return str(row.get(column) or "").strip() != ""


def _truthy_binary(value: str) -> bool | None:
    raw = str(value or "").strip().lower()
    if raw in {"1", "true", "yes", "y", "是", "有"}:
        return True
    if raw in {"0", "false", "no", "n", "否", "无"}:
        return False
    return None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _format_median(values: list[float]) -> str:
    value = _median(values)
    if value is None:
        return "NA"
    return f"{value:.1f} (n={len(values)})"


def _format_count_pct(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "NA"
    return f"{numerator}/{denominator} ({(numerator / denominator) * 100:.1f}%)"


def _format_count(numerator: int, denominator: int) -> str:
    return f"{numerator}/{denominator}"


def _normalize_source_label(row: dict[str, str]) -> str:
    label = str(row.get("source_label") or row.get("source") or "").strip()
    if label:
        return label
    return "Unspecified source"


def _normalize_source_key(row: dict[str, str]) -> str:
    return str(row.get("source") or "").strip().lower()


def _source_groups(rows: list[dict[str, str]]) -> list[tuple[str, list[dict[str, str]]]]:
    groups: list[tuple[str, list[dict[str, str]]]] = [("Overall", rows)]
    source_order = (
        ("Alliance platform", "alliance"),
        ("Xiangya2 management clinic", "management"),
        ("Xiangya2 precision clinic", "precision"),
    )
    consumed_source_keys: set[str] = set()
    consumed_labels: set[str] = set()
    for display_label, source_key in source_order:
        subset = [row for row in rows if _normalize_source_key(row) == source_key]
        if not subset:
            continue
        groups.append((display_label, subset))
        consumed_source_keys.add(source_key)
        consumed_labels.update(_normalize_source_label(row) for row in subset)
    labels = sorted({_normalize_source_label(row) for row in rows if _normalize_source_key(row) not in consumed_source_keys})
    for label in labels:
        if label in consumed_labels:
            continue
        subset = [row for row in rows if _normalize_source_label(row) == label]
        groups.append((label, subset))
    return groups


def _binary_summary(rows: list[dict[str, str]], column: str) -> str:
    observed = [_truthy_binary(str(row.get(column) or "")) for row in rows]
    denominator = sum(value is not None for value in observed)
    numerator = sum(value is True for value in observed)
    return _format_count_pct(numerator, denominator)


def _female_sex_summary(rows: list[dict[str, str]]) -> str:
    observed: list[bool | None] = []
    for row in rows:
        raw = str(row.get("sex") or "").strip().lower()
        if raw in {"女", "female", "f", "woman", "women"}:
            observed.append(True)
        elif raw in {"男", "male", "m", "man", "men"}:
            observed.append(False)
        else:
            observed.append(None)
    denominator = sum(value is not None for value in observed)
    numerator = sum(value is True for value in observed)
    return _format_count_pct(numerator, denominator)


def _available_summary(rows: list[dict[str, str]], column: str) -> str:
    return _format_count(sum(_nonmissing(row, column) for row in rows), len(rows))


def _build_baseline_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    grouped_rows = _source_groups(rows)
    groups = [{"label": label, "n": len(group_rows)} for label, group_rows in grouped_rows]

    def numeric_values(column: str, group_rows: list[dict[str, str]]) -> list[float]:
        return [value for row in group_rows if (value := _float_value(row, column)) is not None]

    variables = [
        {"label": "Records, n", "values": [str(len(group_rows)) for _, group_rows in grouped_rows]},
        {
            "label": "Age, median (available n)",
            "values": [_format_median(numeric_values("age", group_rows)) for _, group_rows in grouped_rows],
        },
        {"label": "Female sex, n/N (%)", "values": [_female_sex_summary(group_rows) for _, group_rows in grouped_rows]},
        {
            "label": "BMI, median kg/m2 (available n)",
            "values": [_format_median(numeric_values("bmi_final", group_rows)) for _, group_rows in grouped_rows],
        },
        {
            "label": "Waist circumference, median cm (available n)",
            "values": [_format_median(numeric_values("waist_cm", group_rows)) for _, group_rows in grouped_rows],
        },
    ]
    for column, label in (
        ("diabetes", "Diabetes, n/N (%)"),
        ("hypertension", "Hypertension, n/N (%)"),
        ("dyslipidemia", "Dyslipidemia, n/N (%)"),
        ("mafld", "MAFLD, n/N (%)"),
        ("sleep_apnea", "Sleep apnea, n/N (%)"),
    ):
        variables.append({"label": label, "values": [_binary_summary(group_rows, column) for _, group_rows in grouped_rows]})
    variables.extend(
        [
            {"label": "PHQ-9 available, n/N", "values": [_available_summary(group_rows, "phq9_total") for _, group_rows in grouped_rows]},
            {"label": "GAD-7 available, n/N", "values": [_available_summary(group_rows, "gad7_total") for _, group_rows in grouped_rows]},
        ]
    )
    return {
        "schema_version": 1,
        "table_shell_id": "table1_baseline_characteristics",
        "title": "Baseline characteristics by registry source",
        "caption": (
            "Descriptive baseline characteristics across prespecified registry sources. "
            "Denominators are available-record denominators and do not support population-level burden "
            "or cause-and-effect claims."
        ),
        "groups": groups,
        "variables": variables,
        "source_paths": ["paper/analysis/descriptive_registry_evidence/materialization_receipt.json"],
    }


def _bmi_category(row: dict[str, str]) -> str:
    category = str(row.get("bmi_category_china") or "").strip()
    return category or "BMI category missing"


def _build_t2_source_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    output: list[list[str]] = []
    for category in sorted({_bmi_category(row) for row in rows}):
        group_rows = [row for row in rows if _bmi_category(row) == category]
        bmi_values = [value for row in group_rows if (value := _float_value(row, "bmi_final")) is not None]
        output.append(
            [
                category,
                str(len(group_rows)),
                _format_median(bmi_values),
                _binary_summary(group_rows, "diabetes"),
                _binary_summary(group_rows, "hypertension"),
                _binary_summary(group_rows, "dyslipidemia"),
                _binary_summary(group_rows, "mafld"),
                _binary_summary(group_rows, "sleep_apnea"),
            ]
        )
    return output


def _build_t3_source_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    center_codes = {str(row.get("center_code") or "").strip() for row in rows if str(row.get("center_code") or "").strip()}
    xiangya2_rows = [
        row
        for row in rows
        if "xiangya" in _normalize_source_label(row).lower() or "湘雅" in str(row.get("center_name") or "")
    ]
    phq9_rows = [row for row in rows if _nonmissing(row, "phq9_total")]
    gad7_rows = [row for row in rows if _nonmissing(row, "gad7_total")]
    return [
        ["Center completeness", "Centers with exported records", str(len(center_codes)), "center_code distinct count"],
        ["Center completeness", "Records in analytic table", str(len(rows)), "QC deidentified analysis table"],
        ["Center completeness", "BMI available", _available_summary(rows, "bmi_final"), "available-record denominator"],
        ["Center completeness", "Waist circumference available", _available_summary(rows, "waist_cm"), "available-record denominator"],
        ["Xiangya2 subcohort", "Records matching Xiangya source/center labels", str(len(xiangya2_rows)), "subcohort boundary only"],
        ["Xiangya2 subcohort", "PHQ-9 available", _available_summary(rows, "phq9_total"), "do not generalize beyond observed coverage"],
        ["Xiangya2 subcohort", "GAD-7 available", _available_summary(rows, "gad7_total"), "do not generalize beyond observed coverage"],
        ["Xiangya2 subcohort", "PHQ-9 records with Xiangya labels", str(len([row for row in phq9_rows if row in xiangya2_rows])), "subcohort trace"],
        ["Xiangya2 subcohort", "GAD-7 records with Xiangya labels", str(len([row for row in gad7_rows if row in xiangya2_rows])), "subcohort trace"],
    ]


def _source_rows_for_key(rows: list[dict[str, str]], source_key: str) -> list[dict[str, str]]:
    return [row for row in rows if _normalize_source_key(row) == source_key]


def _xiangya2_subcohort_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if _normalize_source_key(row) in {"management", "precision"}
        or "xiangya" in _normalize_source_label(row).lower()
        or "湘雅" in str(row.get("center_name") or "")
    ]


def _build_cohort_flow_payload(rows: list[dict[str, str]]) -> dict[str, Any]:
    source_layers = [
        {
            "layer_id": "alliance_platform_records",
            "step_id": "alliance_platform_records",
            "label": "Alliance platform source layer",
            "detail": "Records attributed to the Hunan Obesity Alliance platform source.",
            "n": len(_source_rows_for_key(rows, "alliance")),
        },
        {
            "layer_id": "xiangya2_management_records",
            "step_id": "xiangya2_management_records",
            "label": "Xiangya Second Hospital management clinic source layer",
            "detail": "Records attributed to the Xiangya Second Hospital management clinic source.",
            "n": len(_source_rows_for_key(rows, "management")),
        },
        {
            "layer_id": "xiangya2_precision_records",
            "step_id": "xiangya2_precision_records",
            "label": "Xiangya Second Hospital precision clinic source layer",
            "detail": "Records attributed to the Xiangya Second Hospital precision clinic source.",
            "n": len(_source_rows_for_key(rows, "precision")),
        },
    ]
    xiangya2_rows = _xiangya2_subcohort_rows(rows)
    phq9_rows = [row for row in xiangya2_rows if _nonmissing(row, "phq9_total")]
    gad7_rows = [row for row in xiangya2_rows if _nonmissing(row, "gad7_total")]
    exported_centers = len(
        {str(row.get("center_code") or "").strip() for row in rows if str(row.get("center_code") or "").strip()}
    )
    return {
        "schema_version": 1,
        "shell_id": "fenggaolab.org.medical-display-core::cohort_flow_figure",
        "display_id": "cohort_flow",
        "catalog_id": "F1",
        "paper_role": "main_text",
        "flow_mode": "source_layer_accounting",
        "denominator_step_id": "registry_records",
        "title": "Cohort and source-layer accounting for the Hunan Obesity Alliance registry",
        "caption": (
            f"Cohort and source-layer accounting for {len(rows)} de-identified records in the first descriptive "
            "obesity phenotype atlas. Counts distinguish alliance platform records, Xiangya Second Hospital "
            "management clinic records, and Xiangya Second Hospital precision clinic records; psychobehavioral "
            "interpretation remains limited to the Xiangya Second Hospital subcohort unless wider coverage is proven."
        ),
        "steps": [
            {
                "step_id": "registry_records",
                "label": "Declared analytic registry records",
                "detail": "De-identified records available for descriptive cohort accounting.",
                "n": len(rows),
            },
            *[
                {
                    "step_id": layer["step_id"],
                    "label": layer["label"],
                    "detail": layer["detail"],
                    "n": layer["n"],
                }
                for layer in source_layers
            ],
        ],
        "source_layers": source_layers,
        "subcohort_coverage": [
            {
                "coverage_id": "xiangya2_subcohort",
                "label": "Xiangya Second Hospital subcohort",
                "detail": "Management and precision clinic records.",
                "n": len(xiangya2_rows),
                "denominator_n": len(rows),
            },
            {
                "coverage_id": "phq9_available",
                "label": "PHQ-9 available",
                "detail": "Psychobehavioral availability within the Xiangya2 subcohort.",
                "n": len(phq9_rows),
                "denominator_n": len(xiangya2_rows),
            },
            {
                "coverage_id": "gad7_available",
                "label": "GAD-7 available",
                "detail": "Psychobehavioral availability within the Xiangya2 subcohort.",
                "n": len(gad7_rows),
                "denominator_n": len(xiangya2_rows),
            },
        ],
        "exported_centers": exported_centers,
        "exclusions": [],
    }


def _build_structured_reporting_contract(evidence_refs: list[str]) -> dict[str, Any]:
    def close_items(
        items: tuple[str, ...],
        *,
        status: str = "closed",
        note: str = "",
        applicability: str = "",
    ) -> dict[str, dict[str, Any]]:
        return {
            item: {
                "status": status,
                "evidence_refs": evidence_refs,
                **({"rationale": note} if note else {}),
                **({"applicability": applicability} if applicability else {}),
            }
            for item in items
        }

    no_treatment_note = (
        "Closed by descriptive-scope guardrails: this registry atlas reports available-record "
        "denominators and phenotype support only; treatment response and practice-changing "
        "claims are explicitly out of scope."
    )
    return {
        "study_archetype": "clinical_subtype_reconstruction",
        "paper_archetype": "clinical_subtype_reconstruction",
        "manuscript_family": "clinical_observation",
        "endpoint_type": "descriptive",
        "methods_completeness": close_items(METHODS_COMPLETENESS_ITEMS),
        "statistical_reporting": close_items(STATISTICAL_REPORTING_ITEMS),
        "clinical_actionability_required": True,
        "clinical_actionability": close_items(
            CLINICAL_ACTIONABILITY_ITEMS,
            note=no_treatment_note,
            applicability="closed_by_descriptive_scope_guardrail",
        ),
        "treatment_gap_reporting": close_items(
            TREATMENT_GAP_REPORTING_ITEMS,
            note=no_treatment_note,
            applicability="closed_by_descriptive_scope_guardrail",
        ),
        "manuscript_voice_reporting_required": True,
        "manuscript_voice_reporting": close_items(MANUSCRIPT_VOICE_REPORTING_ITEMS),
        "phenotype_derivation_reporting": close_items(PHENOTYPE_DERIVATION_REPORTING_ITEMS),
        "baseline_characteristics_reporting": close_items(BASELINE_CHARACTERISTICS_REPORTING_ITEMS),
        "data_quality_reporting": close_items(DATA_QUALITY_REPORTING_ITEMS),
        "table_figure_claim_map_required": True,
        "table_figure_claim_map": [
            {"claim_id": "baseline-characteristics-supported", "display_bindings": ["T1"]},
            {"claim_id": "bmi-metabolic-burden-supported", "display_bindings": ["T2"]},
            {"claim_id": "center-psychobehavioral-support-supported", "display_bindings": ["T3"]},
            {"claim_id": "cohort-denominator-accounting", "display_bindings": ["F1"]},
        ],
    }


def _display_registry_payload() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "descriptive_registry_evidence_materialized",
        "source_contract_path": "paper/medical_reporting_contract.json",
        "displays": [
            {
                "display_id": "cohort_flow",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
                "catalog_id": "F1",
                "paper_role": "main_text",
                "shell_path": "paper/figures/cohort_flow.shell.json",
                "source_path": "paper/cohort_flow.json",
                "claim_ids": ["cohort-denominator-accounting", "descriptive-cross-sectional-boundary"],
            },
            {
                "display_id": "baseline_characteristics",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
                "catalog_id": "T1",
                "paper_role": "main_text",
                "shell_path": "paper/tables/baseline_characteristics.shell.json",
                "claim_ids": ["baseline-characteristics-supported"],
            },
            {
                "display_id": "phenotype_gap_summary",
                "display_kind": "table",
                "requirement_key": "table2_phenotype_gap_summary",
                "catalog_id": "T2",
                "paper_role": "main_text",
                "shell_path": "paper/tables/phenotype_gap_summary.shell.json",
                "claim_ids": ["bmi-metabolic-burden-supported"],
            },
            {
                "display_id": "transition_site_support_summary",
                "display_kind": "table",
                "requirement_key": "table3_transition_site_support_summary",
                "catalog_id": "T3",
                "paper_role": "main_text",
                "shell_path": "paper/tables/transition_site_support_summary.shell.json",
                "claim_ids": ["center-psychobehavioral-support-supported"],
            },
        ],
    }


def _figure_shell_payload(display_id: str, requirement_key: str, catalog_id: str, title: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "source_contract_path": "paper/medical_reporting_contract.json",
        "display_id": display_id,
        "display_kind": "figure",
        "requirement_key": requirement_key,
        "shell_id": requirement_key,
        "catalog_id": catalog_id,
        "paper_role": "main_text",
        "story_role": display_story_role_for_requirement_key(requirement_key),
        "title": title,
    }


def _table_shell_payload(display_id: str, requirement_key: str, catalog_id: str, title: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "display_id": display_id,
        "display_kind": "table",
        "requirement_key": requirement_key,
        "shell_id": requirement_key,
        "catalog_id": catalog_id,
        "paper_role": "main_text",
        "story_role": display_story_role_for_requirement_key(requirement_key),
        "title": title,
    }


def _build_materialization_payload(*, study_root: Path, paper_root: Path) -> dict[str, Any]:
    study_payload = _read_study_yaml(study_root)
    policy = study_payload.get("data_management_policy")
    if not isinstance(policy, dict):
        raise ValueError("study.yaml data_management_policy must be a mapping")
    table_path = _resolve_ref(policy.get("canonical_interchange_table"), base=study_root)
    rows = _read_csv_rows(table_path)
    if not rows:
        raise ValueError(f"canonical interchange table is empty: {table_path}")
    now = utc_now()
    claims = _claim_rows()
    evidence_refs = [
        "paper/baseline_characteristics_schema.json",
        "paper/phenotype_gap_summary_schema.json",
        "paper/transition_site_support_summary_schema.json",
        "paper/tables/T2_phenotype_gap_summary.csv",
        "paper/tables/T3_transition_site_support_summary.csv",
        "paper/analysis/descriptive_registry_evidence/materialization_receipt.json",
    ]
    reporting_contract = resolve_medical_reporting_contract(
        study_archetype=str(study_payload.get("study_archetype") or "clinical_subtype_reconstruction"),
        manuscript_family=str(study_payload.get("manuscript_family") or "clinical_observation"),
        endpoint_type=str(study_payload.get("endpoint_type") or "descriptive"),
        submission_target_family="general_medical_journal",
    )
    display_shell_plan = [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
            "story_role": "study_setup",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
            "story_role": "study_setup",
        },
        {
            "display_id": "phenotype_gap_summary",
            "display_kind": "table",
            "requirement_key": "table2_phenotype_gap_summary",
            "catalog_id": "T2",
            "story_role": "result_evidence",
        },
        {
            "display_id": "transition_site_support_summary",
            "display_kind": "table",
            "requirement_key": "table3_transition_site_support_summary",
            "catalog_id": "T3",
            "story_role": "result_evidence",
        },
    ]
    medical_reporting_contract = {
        "schema_version": 1,
        "reporting_guideline_family": reporting_contract.reporting_guideline_family,
        "study_archetype": study_payload.get("study_archetype"),
        "manuscript_family": study_payload.get("manuscript_family"),
        "endpoint_type": study_payload.get("endpoint_type"),
        "display_registry_required": True,
        "display_shell_plan": display_shell_plan,
        "figure_shell_requirements": ["cohort_flow_figure"],
        "table_shell_requirements": [
            "table1_baseline_characteristics",
            "table2_phenotype_gap_summary",
            "table3_transition_site_support_summary",
        ],
        "cohort_flow_required": True,
        "baseline_characteristics_required": True,
        "quality_gate_expectation": {
            "gate_relaxation_allowed": False,
            "current_package_write_allowed": False,
        },
        "structured_reporting_contract": _build_structured_reporting_contract(evidence_refs),
    }
    receipt = {
        "schema_version": 1,
        "controller": CONTROLLER_ID,
        "authority": "controller_owned_repair_receipt",
        "status": "materialized",
        "materialized_at": now,
        "study_root": str(study_root),
        "paper_root": str(paper_root),
        "source_paths": [str(table_path)],
        "row_count": len(rows),
        "current_package_write_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "closed_charter_expectations": [
            "table1_baseline_characteristics",
            "center_completeness_summary",
            "bmi_metabolic_comorbidity_burden",
            "xiangya2_psychobehavioral_subcohort_analysis",
        ],
        "written_surface_roles": [
            "medical_reporting_contract",
            "medical_analysis_contract",
            "display_registry",
            "cohort_flow_payload",
            "table_shell_payloads",
            "claim_evidence_map",
            "evidence_ledger",
        ],
    }
    payloads: dict[Path, dict[str, Any]] = {
        Path("medical_reporting_contract.json"): medical_reporting_contract,
        Path("medical_analysis_contract.json"): _medical_analysis_contract(study_payload, now),
        Path("display_registry.json"): _display_registry_payload(),
        Path("cohort_flow.json"): _build_cohort_flow_payload(rows),
        Path("baseline_characteristics_schema.json"): _build_baseline_payload(rows),
        Path("phenotype_gap_summary_schema.json"): {
            "schema_version": 1,
            "table_shell_id": "table2_phenotype_gap_summary",
            "title": "BMI category and metabolic comorbidity burden",
            "caption": "Descriptive BMI-category metabolic comorbidity burden with available-record denominators.",
            "group_columns": [{"key": "bmi_category", "label": "BMI category"}],
        },
        Path("transition_site_support_summary_schema.json"): {
            "schema_version": 1,
            "table_shell_id": "table3_transition_site_support_summary",
            "title": "Center completeness and Xiangya2 psychobehavioral support",
            "caption": "Descriptive center completeness and Xiangya2 psychobehavioral availability support.",
            "group_columns": [{"key": "domain", "label": "Domain"}],
        },
        Path("figures/cohort_flow.shell.json"): _figure_shell_payload(
            "cohort_flow",
            "cohort_flow_figure",
            "F1",
            "Cohort and source-layer accounting for the Hunan Obesity Alliance registry",
        ),
        Path("tables/baseline_characteristics.shell.json"): _table_shell_payload(
            "baseline_characteristics",
            "table1_baseline_characteristics",
            "T1",
            "Baseline characteristics by registry source",
        ),
        Path("tables/phenotype_gap_summary.shell.json"): _table_shell_payload(
            "phenotype_gap_summary",
            "table2_phenotype_gap_summary",
            "T2",
            "BMI category and metabolic comorbidity burden",
        ),
        Path("tables/transition_site_support_summary.shell.json"): _table_shell_payload(
            "transition_site_support_summary",
            "table3_transition_site_support_summary",
            "T3",
            "Center completeness and Xiangya2 psychobehavioral support",
        ),
        Path("reporting_guideline_checklist.json"): _reporting_checklist(now),
        Path("table_figure_claim_map.json"): {
            "schema_version": 1,
            "status": "closed",
            "items": [
                {"claim_id": claim["claim_id"], "display_bindings": claim["display_bindings"]}
                for claim in claims
            ],
        },
        Path("results_narrative_map.json"): _results_narrative_map(),
        Path("claim_evidence_map.json"): {
            "schema_version": 1,
            "claims": claims,
            "controller_repair_receipts": [receipt],
        },
        Path("evidence_ledger.json"): {
            "schema_version": 1,
            "charter_expectation_closures": _closed_charter_expectations(now),
            "claims": _ledger_claims_from_claims(claims),
            "controller_repair_receipts": [receipt],
        },
        Path("analysis/descriptive_registry_evidence/materialization_receipt.json"): receipt,
    }
    csv_outputs: dict[Path, tuple[list[str], list[list[str]]]] = {
        Path("tables/T2_phenotype_gap_summary.csv"): (
            [
                "BMI category",
                "Records",
                "BMI median kg/m2 (available n)",
                "Diabetes",
                "Hypertension",
                "Dyslipidemia",
                "MAFLD",
                "Sleep apnea",
            ],
            _build_t2_source_rows(rows),
        ),
        Path("tables/T3_transition_site_support_summary.csv"): (
            ["Domain", "Measure", "Value", "Interpretation boundary"],
            _build_t3_source_rows(rows),
        ),
    }
    return {
        "study_payload": study_payload,
        "source_rows": len(rows),
        "json_payloads": payloads,
        "csv_outputs": csv_outputs,
        "receipt": receipt,
    }


def materialize_descriptive_registry_evidence(
    *,
    study_root: Path,
    paper_root: Path,
    apply: bool,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    materialization = _build_materialization_payload(
        study_root=resolved_study_root,
        paper_root=resolved_paper_root,
    )
    json_payloads: dict[Path, dict[str, Any]] = materialization["json_payloads"]
    csv_outputs: dict[Path, tuple[list[str], list[list[str]]]] = materialization["csv_outputs"]
    planned_files = [str(resolved_paper_root / relpath) for relpath in sorted(json_payloads)]
    planned_files.extend(str(resolved_paper_root / relpath) for relpath in sorted(csv_outputs))
    written_files: list[str] = []
    if apply:
        for relpath, payload in json_payloads.items():
            target = resolved_paper_root / relpath
            _write_json(target, payload)
            written_files.append(str(target))
        for relpath, (headers, rows) in csv_outputs.items():
            target = resolved_paper_root / relpath
            _write_csv(target, headers, rows)
            written_files.append(str(target))
    return {
        "surface_kind": "descriptive_registry_evidence_materializer_result",
        "schema_version": 1,
        "status": "materialized" if apply else "planned",
        "apply": bool(apply),
        "controller": CONTROLLER_ID,
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "source_row_count": materialization["source_rows"],
        "planned_files": planned_files,
        "written_files": written_files,
        "closed_charter_expectations": materialization["receipt"]["closed_charter_expectations"],
        "current_package_write_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }


__all__ = ["materialize_descriptive_registry_evidence"]
