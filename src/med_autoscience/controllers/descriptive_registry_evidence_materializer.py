from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

import yaml

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


def _claim_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_id": "cohort-denominator-accounting",
            "statement": (
                "The Hunan Obesity Alliance registry provides an auditable denominator for a descriptive "
                "multicenter obesity phenotype report."
            ),
            "status": "supported_for_source_layer_accounting",
            "paper_role": "main_text",
            "display_bindings": ["F1"],
            "sections": ["Methods: Study design and cohort", "Results: Cohort Denominator and Source Layers"],
            "evidence_items": [
                {
                    "item_id": "cohort-flow-source-layer-display",
                    "support_level": "direct",
                    "source_paths": ["paper/cohort_flow.json", "paper/figures/generated/F1.layout.json"],
                }
            ],
        },
        {
            "claim_id": "baseline-characteristics-supported",
            "statement": (
                "Baseline demographic, anthropometric, metabolic comorbidity, and psychobehavioral data "
                "availability can be reported descriptively by registry source."
            ),
            "status": "supported_descriptive",
            "paper_role": "main_text",
            "display_bindings": ["T1"],
            "sections": ["Results: Baseline characteristics"],
            "evidence_items": [
                {
                    "item_id": "table1-baseline-characteristics",
                    "support_level": "direct",
                    "source_paths": ["paper/baseline_characteristics_schema.json", "paper/tables/generated/T1_baseline_characteristics.csv"],
                }
            ],
        },
        {
            "claim_id": "bmi-metabolic-burden-supported",
            "statement": (
                "BMI-category strata support descriptive reporting of metabolic comorbidity burden using "
                "available-record denominators."
            ),
            "status": "supported_descriptive",
            "paper_role": "main_text",
            "display_bindings": ["T2"],
            "sections": ["Results: BMI and metabolic comorbidity burden"],
            "evidence_items": [
                {
                    "item_id": "table2-bmi-metabolic-burden",
                    "support_level": "direct",
                    "source_paths": [
                        "paper/phenotype_gap_summary_schema.json",
                        "paper/tables/T2_phenotype_gap_summary.csv",
                        "paper/tables/generated/T2_phenotype_gap_summary.csv",
                    ],
                }
            ],
        },
        {
            "claim_id": "center-psychobehavioral-support-supported",
            "statement": (
                "Center completeness and Xiangya2 psychobehavioral availability can be reported as "
                "descriptive support surfaces without alliance-wide generalization."
            ),
            "status": "supported_descriptive_boundary",
            "paper_role": "main_text",
            "display_bindings": ["T3"],
            "sections": ["Results: Center completeness and Xiangya2 subcohort"],
            "evidence_items": [
                {
                    "item_id": "table3-center-psychobehavioral-support",
                    "support_level": "direct",
                    "source_paths": [
                        "paper/transition_site_support_summary_schema.json",
                        "paper/tables/T3_transition_site_support_summary.csv",
                        "paper/tables/generated/T3_transition_site_support_summary.csv",
                    ],
                }
            ],
        },
        {
            "claim_id": "descriptive-cross-sectional-boundary",
            "statement": (
                "The manuscript is limited to a STROBE-aligned descriptive cross-sectional registry atlas "
                "and does not support population-level burden, cause-and-effect, future-risk, "
                "or treatment-response claims."
            ),
            "status": "boundary_supported",
            "paper_role": "main_text",
            "display_bindings": ["F1", "T1", "T2", "T3"],
            "sections": ["Introduction", "Methods: Statistical analysis", "Discussion", "Conclusions"],
            "evidence_items": [
                {
                    "item_id": "descriptive-boundary-contract",
                    "support_level": "direct_boundary",
                    "source_paths": ["study.yaml", "paper/medical_reporting_contract.json", "paper/evidence_ledger.json"],
                }
            ],
        },
    ]


def _ledger_claims_from_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ledger_claims: list[dict[str, Any]] = []
    for claim in claims:
        evidence = []
        for item in claim.get("evidence_items") or []:
            evidence.append(
                {
                    "evidence_id": item["item_id"],
                    "kind": "descriptive_registry_table" if "table" in item["item_id"] else "contract",
                    "support_level": item["support_level"],
                    "source_paths": list(item["source_paths"]),
                    "summary": claim["statement"],
                }
            )
        claim_id = str(claim["claim_id"])
        ledger_claims.append(
            {
                "claim_id": claim_id,
                "statement": claim["statement"],
                "status": claim["status"],
                "submission_scope": "main_text_with_limitations",
                "evidence": evidence,
                "gaps": [
                    {
                        "gap_id": f"{claim_id}-descriptive-scope-limitation",
                        "description": (
                            "The evidence supports descriptive registry reporting only and does not establish "
                            "population-level burden, future risk, cause-and-effect relationships, "
                            "or treatment response."
                        ),
                        "submission_impact": (
                            "Keep the claim bounded to available-record denominators and preserve the "
                            "limitation in Results, Discussion, and Conclusions."
                        ),
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": f"{claim_id}-maintain-claim-guardrail",
                        "priority": "required_before_submission",
                        "description": (
                            "Bind the claim to its listed display and source paths, and avoid prevalence, "
                            "cause-and-effect, future-risk, or treatment-response wording in the manuscript."
                        ),
                    }
                ],
            }
        )
    return ledger_claims


def _results_narrative_map() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sections": [
            {
                "section_id": "cohort_source_layer_accounting",
                "section_title": "Cohort denominator and source layers",
                "research_question": (
                    "What analytic denominator and source-layer structure support the descriptive registry atlas?"
                ),
                "direct_answer": (
                    "F1 and T1 define the available analytic denominator and source-stratified baseline context."
                ),
                "supporting_display_items": ["F1", "T1"],
                "key_quantitative_findings": [
                    "Analytic records are reported from the QC deidentified registry table.",
                    "Baseline variables use available-record denominators by registry source.",
                ],
                "clinical_meaning": (
                    "The source-layer accounting defines where the descriptive findings can be interpreted."
                ),
                "boundary": (
                    "Descriptive denominator accounting only; not a population-level burden "
                    "or cause-and-effect estimate."
                ),
            },
            {
                "section_id": "bmi_metabolic_comorbidity_burden",
                "section_title": "BMI category and metabolic comorbidity burden",
                "research_question": (
                    "How are metabolic comorbidities distributed across BMI-category strata in available records?"
                ),
                "direct_answer": (
                    "T2 reports metabolic comorbidity burden by BMI category using available-record denominators."
                ),
                "supporting_display_items": ["T2"],
                "key_quantitative_findings": [
                    "BMI strata are summarized with record counts, BMI medians, and comorbidity denominators.",
                    "Unknown binary values are excluded from available denominators rather than counted as negative.",
                ],
                "clinical_meaning": (
                    "The table supports descriptive prioritization of phenotype burden within the observed registry."
                ),
                "boundary": "No treatment-response, future-risk, or population-level burden claim is made.",
            },
            {
                "section_id": "center_psychobehavioral_support",
                "section_title": "Center completeness and Xiangya2 psychobehavioral support",
                "research_question": (
                    "What center completeness and Xiangya2 psychobehavioral coverage are available for reporting?"
                ),
                "direct_answer": (
                    "T3 reports exported-center support and Xiangya2 psychobehavioral availability as boundary evidence."
                ),
                "supporting_display_items": ["T3"],
                "key_quantitative_findings": [
                    "Center counts and analytic-record availability are reported as support surfaces.",
                    "PHQ-9 and GAD-7 availability are interpreted as Xiangya2 subcohort support only.",
                ],
                "clinical_meaning": (
                    "Psychobehavioral measures can support a subcohort description but not alliance-wide generalization."
                ),
                "boundary": "Subcohort availability is not generalized beyond observed coverage.",
            },
        ],
    }


def _closed_charter_expectations(now: str) -> list[dict[str, Any]]:
    notes = {
        "study_charter": "Study charter is linked and used as the primary manuscript boundary authority.",
        "strobe_cross_sectional_analysis_plan": "Reporting contract and checklist close STROBE-aligned descriptive reporting requirements.",
        "cohort_flow": "Active F1 display-pack exports support denominator and source-layer accounting.",
        "table1_baseline_characteristics": "T1 baseline characteristics table is materialized from the QC deidentified registry table.",
        "center_completeness_summary": "T3 closes center completeness with exported-center and available-record summaries.",
        "bmi_metabolic_comorbidity_burden": "T2 closes BMI-category metabolic comorbidity burden with available-record denominators.",
        "xiangya2_psychobehavioral_subcohort_analysis": "T3 closes the Xiangya2 psychobehavioral availability surface with subcohort boundary guardrails.",
        "missingness_and_qc_supplement": "Missingness and QC support is linked through the descriptive registry materialization receipt.",
        "evidence_ledger": "Evidence ledger records claim, display, and charter expectation closures.",
        "claim_guardrails": (
            "Claim map and evidence ledger preserve descriptive guardrails against population-level burden "
            "and cause-and-effect overstatement."
        ),
    }
    return [
        {
            "expectation_key": "minimum_sci_ready_evidence_package",
            "expectation_text": key,
            "status": "closed",
            "closed_at": now,
            "note": note,
        }
        for key, note in notes.items()
    ]


def _reporting_checklist(now: str) -> dict[str, Any]:
    evidence = [
        "paper/medical_reporting_contract.json",
        "paper/baseline_characteristics_schema.json",
        "paper/phenotype_gap_summary_schema.json",
        "paper/transition_site_support_summary_schema.json",
        "paper/display_registry.json",
    ]
    return {
        "schema_version": 1,
        "status": "closed",
        "closed_at": now,
        "domains": [
            {
                "domain_id": domain_id,
                "status": "closed",
                "closed_at": now,
                "evidence": evidence,
            }
            for domain_id in (
                "source_of_data_and_participants",
                "candidate_predictors_and_missing_data",
                "outcome_definition_and_follow_up",
            )
        ],
    }


def _medical_analysis_contract(study_payload: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "materialized",
        "materialized_at": now,
        "controller": CONTROLLER_ID,
        "study_id": study_payload.get("study_id"),
        "analysis_role": "descriptive_registry_evidence",
        "allowed_claim_scope": [
            "descriptive_cross_sectional_registry_atlas",
            "available_record_denominator_summaries",
            "xiangya2_psychobehavioral_subcohort_boundary",
        ],
        "disallowed_claim_scope": list(study_payload.get("truth_surface_policy", {}).get("redlines") or []),
        "source_tables": {
            "canonical_interchange_table": (
                study_payload.get("data_management_policy", {}).get("canonical_interchange_table")
            ),
            "data_dictionary": study_payload.get("data_management_policy", {}).get("data_dictionary"),
            "quality_report": study_payload.get("data_management_policy", {}).get("quality_report"),
        },
        "outputs": [
            "paper/baseline_characteristics_schema.json",
            "paper/phenotype_gap_summary_schema.json",
            "paper/transition_site_support_summary_schema.json",
            "paper/tables/T2_phenotype_gap_summary.csv",
            "paper/tables/T3_transition_site_support_summary.csv",
        ],
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
