from __future__ import annotations

import csv

from dataclasses import dataclass

from datetime import datetime, timezone

from decimal import Decimal, ROUND_HALF_UP

from functools import lru_cache

import html

import json

import math

import re

from pathlib import Path

import shutil

import subprocess

import tempfile

import textwrap

from typing import Any

import matplotlib

from matplotlib import pyplot as plt  # noqa: E402

from matplotlib.font_manager import FontProperties  # noqa: E402

from matplotlib.textpath import TextPath  # noqa: E402

from med_autoscience import display_layout_qc, display_pack_lock, display_pack_runtime, display_registry, publication_display_contract  # noqa: E402

from med_autoscience.display_source_contract import INPUT_FILENAME_BY_SCHEMA_ID, TABLE_INPUT_FILENAME_BY_SCHEMA_ID  # noqa: E402

from med_autoscience.display_pack_resolver import get_pack_id, get_template_short_id  # noqa: E402

from med_autoscience.policies.medical_reporting_contract import display_story_role_for_requirement_key  # noqa: E402


matplotlib.use("Agg")

matplotlib.rcParams["svg.fonttype"] = "none"

_INPUT_FILENAME_BY_SCHEMA_ID = INPUT_FILENAME_BY_SCHEMA_ID

_TABLE_INPUT_FILENAME_BY_SCHEMA_ID = TABLE_INPUT_FILENAME_BY_SCHEMA_ID

_ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID = {
    "cohort_flow_shell_inputs_v1": "cohort_flow.json",
    "submission_graphical_abstract_inputs_v1": "submission_graphical_abstract.json",
    "workflow_fact_sheet_panel_inputs_v1": "workflow_fact_sheet_panel.json",
    "design_evidence_composite_shell_inputs_v1": "design_evidence_composite_shell.json",
    "baseline_missingness_qc_panel_inputs_v1": "baseline_missingness_qc_panel.json",
    "center_coverage_batch_transportability_panel_inputs_v1": "center_coverage_batch_transportability_panel.json",
    "transportability_recalibration_governance_panel_inputs_v1": "transportability_recalibration_governance_panel.json",
}

_ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID = {
    "cohort_flow_figure": "cohort_flow",
    "submission_graphical_abstract": "graphical_abstract",
    "workflow_fact_sheet_panel": "workflow_fact_sheet_panel",
    "design_evidence_composite_shell": "design_evidence_composite_shell",
    "baseline_missingness_qc_panel": "baseline_missingness_qc_panel",
    "center_coverage_batch_transportability_panel": "center_coverage_batch_transportability_panel",
    "transportability_recalibration_governance_panel": "transportability_recalibration_governance_panel",
}

_ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID = {
    "cohort_flow_figure": (
        "Cohort flow",
        "Study cohort flow and analysis population accounting.",
    ),
    "submission_graphical_abstract": (
        "Submission graphical abstract",
        "",
    ),
    "workflow_fact_sheet_panel": (
        "Study workflow fact sheet",
        "Structured study-design and workflow summary for the audited manuscript-facing surface.",
    ),
    "design_evidence_composite_shell": (
        "Study design evidence composite",
        "Bounded study-design overview with workflow ribbon and manuscript-facing summary panels.",
    ),
    "baseline_missingness_qc_panel": (
        "Baseline balance, missingness, and QC overview",
        "Bounded cohort-quality overview combining baseline balance, missingness, and QC summary evidence.",
    ),
    "center_coverage_batch_transportability_panel": (
        "Center coverage, batch shift, and transportability overview",
        "Bounded center-coverage overview combining support counts, batch-shift governance, and transportability boundary evidence.",
    ),
    "transportability_recalibration_governance_panel": (
        "Transportability recalibration governance overview",
        "Bounded center-coverage overview combining support counts, batch-shift governance, and recalibration decision evidence.",
    ),
}

_TABLE_OUTPUT_CONFIG_BY_TEMPLATE_SHORT_ID: dict[str, dict[str, Any]] = {
    "table1_baseline_characteristics": {
        "stem": "baseline_characteristics",
        "needs_csv": True,
        "default_title": "Baseline characteristics",
        "default_caption": "Baseline characteristics across prespecified groups.",
    },
    "table2_time_to_event_performance_summary": {
        "stem": "time_to_event_performance_summary",
        "needs_csv": False,
        "default_title": "Time-to-event model performance summary",
        "default_caption": "Time-to-event discrimination and error metrics across analysis cohorts.",
    },
    "table3_clinical_interpretation_summary": {
        "stem": "clinical_interpretation_summary",
        "needs_csv": False,
        "default_title": "Clinical interpretation summary",
        "default_caption": "Clinical interpretation anchors for prespecified risk groups and use cases.",
    },
    "performance_summary_table_generic": {
        "stem": "performance_summary_table_generic",
        "needs_csv": True,
        "default_title": "Performance summary",
        "default_caption": "Structured repeated-validation performance summaries across candidate packages.",
    },
    "grouped_risk_event_summary_table": {
        "stem": "grouped_risk_event_summary_table",
        "needs_csv": True,
        "default_title": "Grouped risk event summary",
        "default_caption": "Observed case counts, event counts, and absolute risks across grouped-risk strata.",
    },
}

_REPO_ROOT = Path(__file__).resolve().parents[4]

def _resolve_illustration_shell_paper_role(
    *,
    shell_payload: dict[str, Any],
    requirement_key: str,
    allowed_paper_roles: tuple[str, ...],
) -> str:
    explicit_paper_role = str(shell_payload.get("paper_role") or "").strip()
    if explicit_paper_role:
        return explicit_paper_role
    story_role = display_story_role_for_requirement_key(requirement_key)
    if story_role == "study_setup" and "supplementary" in allowed_paper_roles:
        return "supplementary"
    return allowed_paper_roles[0]

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload

def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def _paper_relative_path(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.parent.resolve()).as_posix()

def _build_render_context(
    *,
    style_profile: publication_display_contract.PublicationStyleProfile,
    display_overrides: dict[tuple[str, str], publication_display_contract.DisplayOverride],
    display_id: str,
    template_id: str,
) -> dict[str, Any]:
    override = display_overrides.get((display_id, template_id))
    return {
        "style_profile_id": style_profile.style_profile_id,
        "palette": dict(style_profile.palette),
        "typography": dict(style_profile.typography),
        "stroke": dict(style_profile.stroke),
        "style_roles": publication_display_contract.resolve_style_roles(
            style_profile=style_profile,
            template_id=template_id,
        ),
        "layout_override": dict(override.layout_override) if override is not None else {},
        "readability_override": dict(override.readability_override) if override is not None else {},
    }

def _require_namespaced_registry_id(identifier: str, *, label: str) -> tuple[str, str]:
    try:
        pack_id = get_pack_id(identifier)
        short_id = get_template_short_id(identifier)
    except ValueError as exc:
        raise ValueError(f"{label} must be namespaced as '<pack_id>::<template_id>'") from exc
    return pack_id, short_id

def _read_bool_override(mapping: dict[str, Any], key: str, default: bool) -> bool:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    return default

def _normalize_figure_catalog_id(raw_id: str) -> str:
    item = str(raw_id).strip()
    graphical_abstract_match = re.fullmatch(r"(?:GraphicalAbstract|GA)(\d+)", item, flags=re.IGNORECASE)
    if graphical_abstract_match:
        return f"GA{int(graphical_abstract_match.group(1))}"
    supplementary_match = re.fullmatch(r"SupplementaryFigureS(\d+)", item, flags=re.IGNORECASE)
    if supplementary_match:
        return f"S{int(supplementary_match.group(1))}"
    supplementary_current_match = re.fullmatch(r"S(\d+)", item, flags=re.IGNORECASE)
    if supplementary_current_match:
        return f"S{int(supplementary_current_match.group(1))}"
    supplementary_short_match = re.fullmatch(r"FS(\d+)", item, flags=re.IGNORECASE)
    if supplementary_short_match:
        return f"S{int(supplementary_short_match.group(1))}"
    match = re.fullmatch(r"F(?:igure)?(\d+)([A-Z]?)", item, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported figure catalog_id `{raw_id}`")
    panel_suffix = str(match.group(2) or "").upper()
    return f"F{int(match.group(1))}{panel_suffix}"

def _normalize_table_catalog_id(raw_id: str) -> str:
    item = str(raw_id).strip()
    appendix_match = re.fullmatch(r"AppendixTable(\d+)", item, flags=re.IGNORECASE)
    if appendix_match:
        return f"TA{int(appendix_match.group(1))}"
    appendix_short_match = re.fullmatch(r"TA(\d+)", item, flags=re.IGNORECASE)
    if appendix_short_match:
        return f"TA{int(appendix_short_match.group(1))}"
    appendix_alias_match = re.fullmatch(r"A(\d+)", item, flags=re.IGNORECASE)
    if appendix_alias_match:
        return f"TA{int(appendix_alias_match.group(1))}"
    match = re.fullmatch(r"T(?:able)?(\d+)", item, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported table catalog_id `{raw_id}`")
    return f"T{int(match.group(1))}"

def _resolve_figure_catalog_id(*, display_id: str, catalog_id: str | None = None) -> str:
    if str(catalog_id or "").strip():
        return _normalize_figure_catalog_id(str(catalog_id))
    return _normalize_figure_catalog_id(str(display_id))

def _resolve_table_catalog_id(*, display_id: str, catalog_id: str | None = None) -> str:
    if str(catalog_id or "").strip():
        return _normalize_table_catalog_id(str(catalog_id))
    return _normalize_table_catalog_id(str(display_id))

def _replace_catalog_entry(items: list[dict[str, Any]], *, key: str, value: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    updated = [
        item
        for item in items
        if str(item.get(key) or "").strip() != value and str(item.get("catalog_id") or "").strip() != value
    ]
    updated.append(entry)
    return updated

def _collect_referenced_generated_surface_paths(
    *,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> set[str]:
    referenced_paths: set[str] = set()

    def maybe_add(path_value: object) -> None:
        normalized = str(path_value or "").strip()
        if not normalized.startswith("paper/") or "/generated/" not in normalized:
            return
        referenced_paths.add(normalized)

    for entry in figure_catalog.get("figures", []):
        if not isinstance(entry, dict):
            continue
        for export_path in entry.get("export_paths") or []:
            maybe_add(export_path)
        qc_result = entry.get("qc_result")
        if isinstance(qc_result, dict):
            maybe_add(qc_result.get("layout_sidecar_path"))

    for entry in table_catalog.get("tables", []):
        if not isinstance(entry, dict):
            continue
        for asset_path in entry.get("asset_paths") or []:
            maybe_add(asset_path)

    return referenced_paths

def _prune_unreferenced_generated_surface_outputs(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> list[str]:
    referenced_paths = _collect_referenced_generated_surface_paths(
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    )
    deleted_paths: list[str] = []
    generated_roots = (
        (paper_root / "figures" / "generated", {".png", ".pdf", ".svg", ".json"}),
        (paper_root / "tables" / "generated", {".csv", ".md"}),
    )
    for generated_root, allowed_suffixes in generated_roots:
        if not generated_root.exists():
            continue
        for candidate in sorted(generated_root.glob("*")):
            if not candidate.is_file() or candidate.suffix.lower() not in allowed_suffixes:
                continue
            relpath = f"paper/{candidate.relative_to(paper_root).as_posix()}"
            if relpath in referenced_paths:
                continue
            candidate.unlink()
            deleted_paths.append(relpath)
    return deleted_paths

def _build_paper_surface_readmes(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    table_catalog: dict[str, Any],
) -> dict[Path, str]:
    figure_ids = [
        str(entry.get("figure_id") or "").strip()
        for entry in figure_catalog.get("figures", [])
        if isinstance(entry, dict) and str(entry.get("figure_id") or "").strip()
    ]
    table_ids = [
        str(entry.get("table_id") or "").strip()
        for entry in table_catalog.get("tables", [])
        if isinstance(entry, dict) and str(entry.get("table_id") or "").strip()
    ]
    figure_id_line = ", ".join(figure_ids) if figure_ids else "(none materialized yet)"
    table_id_line = ", ".join(table_ids) if table_ids else "(none materialized yet)"
    return {
        paper_root / "README.md": textwrap.dedent(
            """\
            # Paper Authority Surface

            - This directory is the manuscript-facing authority surface for the active study line.
            - Figures: `paper/figures/figure_catalog.json` + `paper/figures/generated/`
            - Tables: `paper/tables/table_catalog.json` + `paper/tables/generated/`
            - Canonical submission package: `paper/submission_minimal/`
            - Human-facing delivery mirror: `../manuscript/`
            - Auxiliary finalize/runtime evidence only: `../artifacts/`

            If a human needs the latest authoritative display outputs, start here instead of `manuscript/` or `artifacts/`.
            """
        ),
        paper_root / "figures" / "README.md": textwrap.dedent(
            f"""\
            # Figure Authority Surface

            - Catalog contract: `paper/figures/figure_catalog.json`
            - Active rendered outputs: `paper/figures/generated/`
            - Current figure ids: {figure_id_line}

            Treat `figure_catalog.json` as the canonical routing/index surface. The files under `generated/` are the current paper-owned renders referenced by that catalog.
            """
        ),
        paper_root / "figures" / "generated" / "README.md": textwrap.dedent(
            f"""\
            # Generated Figure Outputs

            - Authority: `paper/figures/generated/`
            - Routed by: `paper/figures/figure_catalog.json`
            - Current figure ids: {figure_id_line}

            Every authoritative figure render for the active paper line lives here. Any unreferenced stale generated files are pruned during `materialize-display-surface`; use the catalog rather than guessing by filename age.
            """
        ),
        paper_root / "tables" / "README.md": textwrap.dedent(
            f"""\
            # Table Authority Surface

            - Catalog contract: `paper/tables/table_catalog.json`
            - Active rendered outputs: `paper/tables/generated/`
            - Current table ids: {table_id_line}

            Treat `table_catalog.json` as the canonical routing/index surface. The files under `generated/` are the current paper-owned table renders referenced by that catalog.
            """
        ),
        paper_root / "tables" / "generated" / "README.md": textwrap.dedent(
            f"""\
            # Generated Table Outputs

            - Authority: `paper/tables/generated/`
            - Routed by: `paper/tables/table_catalog.json`
            - Current table ids: {table_id_line}

            Every authoritative table render for the active paper line lives here. Any unreferenced stale generated files are pruned during `materialize-display-surface`; use the catalog rather than guessing by filename age.
            """
        ),
    }

def _require_non_empty_string(value: object, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    return normalized

def _require_numeric_list(value: object, *, label: str, min_length: int = 2) -> list[float]:
    if not isinstance(value, list) or len(value) < min_length:
        raise ValueError(f"{label} must contain at least {min_length} numeric values")
    normalized: list[float] = []
    for index, item in enumerate(value):
        if not isinstance(item, (int, float)) or isinstance(item, bool):
            raise ValueError(f"{label}[{index}] must be numeric")
        normalized.append(float(item))
    return normalized

def _require_numeric_value(value: object, *, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)

def _require_probability_value(value: object, *, label: str) -> float:
    normalized = _require_numeric_value(value, label=label)
    if normalized < 0.0 or normalized > 1.0:
        raise ValueError(f"{label} must be a probability between 0 and 1")
    return normalized

def _require_strictly_increasing_numeric_list(value: object, *, label: str, min_length: int = 2) -> list[float]:
    normalized = _require_numeric_list(value, label=label, min_length=min_length)
    for index, (previous_value, current_value) in enumerate(zip(normalized[:-1], normalized[1:], strict=True), start=1):
        if current_value > previous_value:
            continue
        raise ValueError(f"{label}[{index}] must be strictly greater than the previous value")
    return normalized

def _require_non_negative_int(value: object, *, label: str, allow_zero: bool = True) -> int:
    numeric_value = _require_numeric_value(value, label=label)
    if not float(numeric_value).is_integer():
        raise ValueError(f"{label} must be an integer")
    normalized = int(numeric_value)
    if normalized < 0 or (normalized == 0 and not allow_zero):
        comparator = ">= 1" if not allow_zero else ">= 0"
        raise ValueError(f"{label} must be {comparator}")
    return normalized

_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES: dict[str, str] = {
    "full_right": "wide_top",
}

def _format_percent_1dp(*, numerator: int, denominator: int) -> str:
    percent = (Decimal(numerator) * Decimal("100")) / Decimal(denominator)
    return f"{percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"

def _evidence_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported evidence input schema `{input_schema_id}`") from exc
    return paper_root / filename

def _illustration_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported illustration input schema `{input_schema_id}`") from exc
    return paper_root / filename

def _table_payload_path(*, paper_root: Path, input_schema_id: str) -> Path:
    try:
        filename = _TABLE_INPUT_FILENAME_BY_SCHEMA_ID[input_schema_id]
    except KeyError as exc:
        raise ValueError(f"unsupported table input schema `{input_schema_id}`") from exc
    return paper_root / filename


__all__ = [
    "Any",
    "Decimal",
    "FontProperties",
    "INPUT_FILENAME_BY_SCHEMA_ID",
    "Path",
    "ROUND_HALF_UP",
    "TABLE_INPUT_FILENAME_BY_SCHEMA_ID",
    "TextPath",
    "csv",
    "dataclass",
    "datetime",
    "display_layout_qc",
    "display_pack_lock",
    "display_pack_runtime",
    "display_registry",
    "display_story_role_for_requirement_key",
    "get_pack_id",
    "get_template_short_id",
    "html",
    "json",
    "lru_cache",
    "math",
    "matplotlib",
    "plt",
    "publication_display_contract",
    "re",
    "shutil",
    "subprocess",
    "tempfile",
    "textwrap",
    "timezone",
    "_INPUT_FILENAME_BY_SCHEMA_ID",
    "_TABLE_INPUT_FILENAME_BY_SCHEMA_ID",
    "_ILLUSTRATION_INPUT_FILENAME_BY_SCHEMA_ID",
    "_ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID",
    "_ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID",
    "_TABLE_OUTPUT_CONFIG_BY_TEMPLATE_SHORT_ID",
    "_REPO_ROOT",
    "_resolve_illustration_shell_paper_role",
    "utc_now",
    "load_json",
    "dump_json",
    "write_text",
    "_paper_relative_path",
    "_build_render_context",
    "_require_namespaced_registry_id",
    "_read_bool_override",
    "_normalize_figure_catalog_id",
    "_normalize_table_catalog_id",
    "_resolve_figure_catalog_id",
    "_resolve_table_catalog_id",
    "_replace_catalog_entry",
    "_collect_referenced_generated_surface_paths",
    "_prune_unreferenced_generated_surface_outputs",
    "_build_paper_surface_readmes",
    "_require_non_empty_string",
    "_require_numeric_list",
    "_require_numeric_value",
    "_require_probability_value",
    "_require_strictly_increasing_numeric_list",
    "_require_non_negative_int",
    "_COHORT_FLOW_DESIGN_PANEL_ROLE_ALIASES",
    "_format_percent_1dp",
    "_evidence_payload_path",
    "_illustration_payload_path",
    "_table_payload_path",
]
