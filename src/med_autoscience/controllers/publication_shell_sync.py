from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _require_binding(*, registry_payload: dict[str, Any], requirement_key: str) -> dict[str, str]:
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json missing displays list")
    for item in displays:
        if not isinstance(item, dict):
            continue
        if str(item.get("requirement_key") or "").strip() != requirement_key:
            continue
        display_id = str(item.get("display_id") or "").strip()
        catalog_id = str(item.get("catalog_id") or "").strip()
        if not display_id or not catalog_id:
            raise ValueError(f"display binding for {requirement_key} is incomplete")
        return {
            "display_id": display_id,
            "catalog_id": catalog_id,
        }
    raise ValueError(f"missing required display binding: {requirement_key}")


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    normalized = normalized.strip("_")
    return normalized or "item"


def _load_csv_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    if not path.exists():
        raise FileNotFoundError(f"missing required CSV file: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    if len(rows) < 2:
        raise ValueError(f"expected header plus data rows in {path}")
    return rows[0], rows[1:]


def _load_csv_records(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing required CSV file: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [dict(item) for item in reader]
    if not rows:
        raise ValueError(f"expected at least one data row in {path}")
    return rows


def _load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _load_first_existing_json(*candidate_paths: Path) -> tuple[Path, dict[str, Any]]:
    for path in candidate_paths:
        if path.exists():
            return path, _load_json(path)
    joined_paths = ", ".join(str(path) for path in candidate_paths)
    raise FileNotFoundError(f"missing required JSON source; checked: {joined_paths}")


def _resolve_paper_relative_path(paper_root: Path, raw_path: str) -> Path:
    candidate = Path(str(raw_path).strip())
    if candidate.is_absolute():
        return candidate
    if candidate.parts and candidate.parts[0] == "paper":
        return (paper_root.parent / candidate).resolve()
    return (paper_root / candidate).resolve()


def _normalize_figure_catalog_id(raw_id: str) -> str:
    match = re.fullmatch(r"F(?:igure)?(\d+)", str(raw_id).strip(), flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported figure catalog_id `{raw_id}`")
    return f"F{int(match.group(1))}"


def _normalize_table_catalog_id(raw_id: str) -> str:
    match = re.fullmatch(r"T(?:able)?(\d+)", str(raw_id).strip(), flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"unsupported table catalog_id `{raw_id}`")
    return f"T{int(match.group(1))}"


def _catalog_id_matches(*, raw_id: object, target_id: str, kind: str) -> bool:
    normalized = str(raw_id or "").strip()
    if not normalized:
        return False
    try:
        if kind == "figure":
            return _normalize_figure_catalog_id(normalized) == _normalize_figure_catalog_id(target_id)
        return _normalize_table_catalog_id(normalized) == _normalize_table_catalog_id(target_id)
    except ValueError:
        return False


def _load_catalog_entry(
    *,
    paper_root: Path,
    catalog_kind: str,
    target_id: str,
) -> dict[str, Any]:
    if catalog_kind == "figure":
        payload = _load_json(paper_root / "figures" / "figure_catalog.json")
        collection_key = "figures"
        entry_key = "figure_id"
    else:
        payload = _load_json(paper_root / "tables" / "table_catalog.json")
        collection_key = "tables"
        entry_key = "table_id"
    collection = payload.get(collection_key)
    if not isinstance(collection, list):
        raise ValueError(f"{catalog_kind} catalog missing {collection_key} list")
    for item in collection:
        if isinstance(item, dict) and _catalog_id_matches(raw_id=item.get(entry_key), target_id=target_id, kind=catalog_kind):
            return item
    raise ValueError(f"missing required {catalog_kind} catalog entry: {target_id}")


def _maybe_load_catalog_entry(
    *,
    paper_root: Path,
    catalog_kind: str,
    target_id: str,
) -> dict[str, Any] | None:
    try:
        return _load_catalog_entry(paper_root=paper_root, catalog_kind=catalog_kind, target_id=target_id)
    except (FileNotFoundError, ValueError):
        return None


def _resolve_catalog_source_path(*, paper_root: Path, raw_path: str) -> Path:
    candidate = Path(str(raw_path).strip())
    if candidate.is_absolute():
        return candidate
    anchors = [paper_root.parent, paper_root]
    for anchor in anchors:
        resolved = (anchor / candidate).resolve()
        if resolved.exists():
            return resolved
    return (anchors[0] / candidate).resolve()


def _resolved_catalog_source_paths(*, paper_root: Path, catalog_entry: dict[str, Any] | None) -> list[Path]:
    if not isinstance(catalog_entry, dict):
        return []
    raw_paths: list[str] = []
    for key in ("source_artifacts", "source_paths", "derived_artifact_paths", "contract_paths", "asset_paths"):
        values = catalog_entry.get(key)
        if isinstance(values, list):
            raw_paths.extend(str(item).strip() for item in values if str(item).strip())
    for key in ("csv_path", "path"):
        value = str(catalog_entry.get(key) or "").strip()
        if value:
            raw_paths.append(value)
    resolved_paths: list[Path] = []
    seen: set[Path] = set()
    for raw_path in raw_paths:
        resolved = _resolve_catalog_source_path(paper_root=paper_root, raw_path=raw_path)
        if not resolved.exists() or resolved in seen:
            continue
        seen.add(resolved)
        resolved_paths.append(resolved)
    return resolved_paths


def _require_source_path_by_name(*, paths: list[Path], filename: str) -> Path:
    for path in paths:
        if path.name == filename:
            return path
    raise ValueError(f"missing required source file `{filename}` in catalog source_paths")


def _find_source_path_by_name(*, paths: list[Path], filename: str) -> Path | None:
    for path in paths:
        if path.name == filename:
            return path
    return None


def _parse_float(raw_value: object, *, label: str) -> float:
    try:
        return float(str(raw_value).strip())
    except ValueError as exc:
        raise ValueError(f"{label} must be numeric") from exc


def _require_int(value: object, *, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{label} must be an integer")
    return int(value)


def _normalize_cohort_steps(payload: object) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or not payload:
        raise ValueError("cohort flow steps must be a non-empty list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"cohort flow steps[{index}] must be an object")
        raw_n = item.get("n")
        if raw_n is None:
            raw_n = item.get("count")
        normalized.append(
            {
                "step_id": str(item.get("step_id") or item.get("step") or "").strip(),
                "label": str(item.get("label") or "").strip(),
                "n": _require_int(raw_n, label=f"steps[{index}].n"),
                "detail": str(item.get("detail") or "").strip(),
            }
        )
    return normalized


def _normalize_exclusions(payload: object) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("cohort flow exclusions must be a list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"cohort flow exclusions[{index}] must be an object")
        normalized.append(
            {
                "exclusion_id": str(item.get("exclusion_id") or item.get("branch_id") or "").strip(),
                "from_step_id": str(item.get("from_step_id") or "").strip(),
                "label": str(item.get("label") or "").strip(),
                "n": _require_int(item.get("n"), label=f"exclusions[{index}].n"),
                "detail": str(item.get("detail") or "").strip(),
            }
        )
    return normalized


def _normalize_endpoint_inventory(payload: object) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("cohort flow endpoint_inventory must be a list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"cohort flow endpoint_inventory[{index}] must be an object")
        raw_event_n = item.get("event_n")
        if raw_event_n is None:
            raw_event_n = item.get("n")
        normalized.append(
            {
                "endpoint_id": str(item.get("endpoint_id") or "").strip(),
                "label": str(item.get("label") or "").strip(),
                "event_n": _require_int(raw_event_n, label=f"endpoint_inventory[{index}].event_n"),
                "detail": str(item.get("detail") or "").strip(),
            }
        )
    return normalized


def _normalize_design_panels(payload: object) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("cohort flow design_panels must be a list")
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"cohort flow design_panels[{index}] must be an object")
        lines_payload = item.get("lines")
        if lines_payload is None:
            lines_payload = item.get("items")
        if not isinstance(lines_payload, list):
            raise ValueError(f"cohort flow design_panels[{index}].lines must be a list")
        lines: list[dict[str, str]] = []
        for line_index, line in enumerate(lines_payload):
            if not isinstance(line, dict):
                raise ValueError(f"cohort flow design_panels[{index}].lines[{line_index}] must be an object")
            lines.append(
                {
                    "label": str(line.get("label") or "").strip(),
                    "detail": str(line.get("detail") or "").strip(),
                }
            )
        normalized.append(
            {
                "panel_id": str(item.get("panel_id") or item.get("block_id") or "").strip(),
                "layout_role": str(item.get("layout_role") or item.get("block_type") or "").strip(),
                "title": str(item.get("title") or "").strip(),
                "lines": lines,
            }
        )
    return normalized


def _validation_contract_line(source_payload: dict[str, Any]) -> dict[str, str] | None:
    validation_contract = source_payload.get("validation_contract")
    if not isinstance(validation_contract, dict):
        return None
    repeats = validation_contract.get("repeats") or validation_contract.get("outer_repeats")
    outer_splits = validation_contract.get("outer_splits") or validation_contract.get("outer_folds")
    inner_splits = validation_contract.get("inner_splits") or validation_contract.get("inner_folds")
    detail_parts: list[str] = []
    if isinstance(repeats, int) and isinstance(outer_splits, int):
        detail_parts.append(f"{repeats} repeats x {outer_splits} outer folds")
    elif isinstance(outer_splits, int):
        detail_parts.append(f"{outer_splits} outer folds")
    if isinstance(inner_splits, int):
        detail_parts.append(f"{inner_splits}-fold inner tuning")
    tuning_metric = str(validation_contract.get("tuning_metric") or "").strip()
    if tuning_metric:
        detail_parts.append(f"Tuning metric: {tuning_metric}")
    if not detail_parts:
        return None
    return {
        "label": "Repeated nested validation",
        "detail": "; ".join(detail_parts),
    }


_PUBLICATION_SAFE_MODEL_HIERARCHY_LABELS: dict[str, str] = {
    "Preoperative Core Model": "Core preoperative model",
    "Clinical Utility Model": "Clinically informed preoperative model",
    "Pathology-Augmented Model": "Pathology-extended comparison",
    "Elastic-Net Benchmark": "Elastic-net comparison",
    "Random-Forest Benchmark": "Random-forest comparison",
}


def _publication_safe_cohort_text(text: object) -> str:
    return medical_surface_policy.rewrite_publication_safe_text(str(text or "").strip())


def _publication_safe_model_hierarchy_label(label: object) -> str:
    normalized = str(label or "").strip()
    if not normalized:
        return ""
    return _PUBLICATION_SAFE_MODEL_HIERARCHY_LABELS.get(normalized, _publication_safe_cohort_text(normalized))


def _sync_cohort_flow_payload(
    *,
    source_payload: dict[str, Any],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    if isinstance(source_payload.get("steps"), list):
        title = str(source_payload.get("title") or "Cohort derivation, endpoint inventory, and study design").strip()
        caption = str(source_payload.get("caption") or "").strip()
        steps = _normalize_cohort_steps(source_payload.get("steps"))
        exclusions = _normalize_exclusions(source_payload.get("exclusions") or source_payload.get("exclusion_branches"))
        endpoint_inventory = _normalize_endpoint_inventory(source_payload.get("endpoint_inventory"))
        design_panels = _normalize_design_panels(source_payload.get("design_panels") or source_payload.get("sidecar_blocks"))
    elif isinstance(source_payload.get("cohort_flow"), list):
        title = str(source_payload.get("title") or "Study cohort assembly with exclusion accounting").strip()
        caption = str(
            source_payload.get("caption")
            or "Source-to-analysis cohort derivation with manuscript endpoint inventory and study-design sidecars."
        ).strip()
        steps = _normalize_cohort_steps(source_payload.get("cohort_flow"))
        exclusions = []
        endpoint_inventory = []
        analysis_cohort = source_payload.get("analysis_cohort")
        if isinstance(analysis_cohort, dict):
            non_gtr_cases = analysis_cohort.get("non_gtr_cases")
            if isinstance(non_gtr_cases, int):
                endpoint_inventory.append(
                    {
                        "endpoint_id": "early_residual_non_gtr",
                        "label": "Early residual / non-GTR",
                        "event_n": non_gtr_cases,
                        "detail": "Primary manuscript endpoint",
                    }
                )
        design_panels = []
        validation_line = _validation_contract_line(source_payload)
        if validation_line is not None:
            design_panels.append(
                {
                    "panel_id": "validation_contract",
                    "layout_role": "wide_top",
                    "title": "Validation design",
                    "lines": [validation_line],
                }
            )
        model_hierarchy = source_payload.get("model_hierarchy")
        if isinstance(model_hierarchy, list) and model_hierarchy:
            lines: list[dict[str, str]] = []
            for item in model_hierarchy:
                if not isinstance(item, dict):
                    continue
                label = _publication_safe_model_hierarchy_label(item.get("label"))
                role = _publication_safe_cohort_text(item.get("role"))
                surface = _publication_safe_cohort_text(item.get("surface"))
                detail = "; ".join(part for part in (role, surface) if part)
                if label:
                    lines.append({"label": label, "detail": detail})
            if lines:
                design_panels.append(
                    {
                        "panel_id": "model_hierarchy",
                        "layout_role": "right_bottom",
                        "title": "Model comparison frame",
                        "lines": lines,
                    }
                )
    else:
        source_total_cases = _require_int(source_payload["source_total_cases"], label="source_total_cases")
        first_surgery_cases = _require_int(source_payload["first_surgery_cases"], label="first_surgery_cases")
        excluded_non_first_surgery = _require_int(
            source_payload.get("excluded_non_first_surgery") or 0,
            label="excluded_non_first_surgery",
        )
        complete_3_month_landmark_cases = _require_int(
            source_payload["complete_3_month_landmark_cases"],
            label="complete_3_month_landmark_cases",
        )
        complete_later_endpoint_cases = _require_int(
            source_payload["complete_later_endpoint_cases"],
            label="complete_later_endpoint_cases",
        )
        analysis_cases = _require_int(source_payload["analysis_cases"], label="analysis_cases")
        analysis_event_n = _require_int(source_payload.get("analysis_event_n") or 0, label="analysis_event_n")
        title = "Cohort derivation, endpoint inventory, and score-construction design"
        caption = (
            "Unified Figure 1 shell covering cohort restriction, manuscript endpoint inventory, and study-design "
            "panels required for manuscript-safe population accounting."
        )
        steps = [
            {
                "step_id": "source_total_cases",
                "label": "Source study records",
                "n": source_total_cases,
                "detail": f"Dataset version: {source_payload.get('dataset_version') or 'unspecified'}",
            },
            {
                "step_id": "first_surgery_cases",
                "label": "First-surgery cohort",
                "n": first_surgery_cases,
                "detail": "Restricted to the first eligible surgery per patient",
            },
            {
                "step_id": "complete_3_month_landmark_cases",
                "label": "Complete 3-month landmark",
                "n": complete_3_month_landmark_cases,
                "detail": "All prespecified landmark variables available",
            },
            {
                "step_id": "complete_later_endpoint_cases",
                "label": "Complete later endpoint follow-up",
                "n": complete_later_endpoint_cases,
                "detail": "Later endpoint ascertainment completed",
            },
            {
                "step_id": "analysis_cases",
                "label": "Final analysis cohort",
                "n": analysis_cases,
                "detail": f"Later persistent global hypopituitarism events: {analysis_event_n}",
            },
        ]
        exclusions = []
        if excluded_non_first_surgery > 0:
            exclusions.append(
                {
                    "exclusion_id": "excluded_non_first_surgery",
                    "from_step_id": "source_total_cases",
                    "label": "Repeat / non-first-surgery cases",
                    "n": excluded_non_first_surgery,
                    "detail": "Excluded before the first-surgery landmark cohort",
                }
            )
        endpoint_inventory = []
        if analysis_event_n > 0:
            endpoint_inventory.append(
                {
                    "endpoint_id": "later_persistent_global_hypopituitarism",
                    "label": "Later persistent global hypopituitarism",
                    "event_n": analysis_event_n,
                    "detail": "Primary manuscript endpoint",
                }
            )
        design_panels = []
        score_definition = source_payload.get("score_definition")
        if isinstance(score_definition, dict):
            lines: list[dict[str, str]] = []
            simple_score = str(score_definition.get("simple_score") or "").strip()
            if simple_score:
                lines.append({"label": "Simple score", "detail": simple_score})
            group_rule = str(score_definition.get("group_rule") or "").strip()
            if group_rule:
                lines.append({"label": "Grouped risk rule", "detail": group_rule})
            if lines:
                design_panels.append(
                    {
                        "panel_id": "score_definition",
                        "layout_role": "wide_top",
                        "title": "Score-construction design",
                        "lines": lines,
                    }
                )
        validation_line = _validation_contract_line(source_payload)
        if validation_line is not None:
            design_panels.append(
                {
                    "panel_id": "validation_contract",
                    "layout_role": "left_bottom",
                    "title": "Validation design",
                    "lines": [validation_line],
                }
            )

    title = _publication_safe_cohort_text(title)
    caption = _publication_safe_cohort_text(caption)
    design_panels = [
        {
            **panel,
            "title": _publication_safe_cohort_text(panel.get("title")),
            "lines": [
                {
                    **line,
                    "label": _publication_safe_cohort_text(line.get("label")),
                    "detail": _publication_safe_cohort_text(line.get("detail")),
                }
                for line in panel.get("lines", [])
                if isinstance(line, dict)
            ],
        }
        for panel in design_panels
        if isinstance(panel, dict)
    ]

    return {
        "schema_version": 1,
        "shell_id": "cohort_flow_figure",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": caption,
        "steps": steps,
        "exclusions": exclusions,
        "endpoint_inventory": endpoint_inventory,
        "design_panels": design_panels,
    }


def _sync_table1_payload(
    *,
    header: list[str],
    rows: list[list[str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    groups = [{"group_id": _slugify(label), "label": label} for label in header[1:]]
    variables: list[dict[str, Any]] = []
    for row in rows:
        if len(row) != len(header):
            raise ValueError("Table1 CSV row length does not match header length")
        variables.append(
            {
                "variable_id": _slugify(row[0]),
                "label": row[0],
                "values": row[1:],
            }
        )
    return {
        "schema_version": 1,
        "table_shell_id": "table1_baseline_characteristics",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": "Baseline characteristics at the 3-month postoperative landmark",
        "caption": "Descriptive cohort characteristics at the 3-month postoperative landmark stratified by later endpoint status.",
        "groups": groups,
        "variables": variables,
    }


_PHASE_C_MODEL_ORDER: tuple[str, ...] = (
    "simple_score_only",
    "core_logistic",
    "context_logistic",
    "benchmark_rf",
    "coarse_q006",
    "A0",
    "A1",
    "B0",
    "M0_elastic",
    "M0_hgb",
)

_PHASE_C_MODEL_LABELS: dict[str, str] = {
    "simple_score_only": "Simple 3-month score",
    "core_logistic": "Core logistic confirmation",
    "context_logistic": "Context-enhanced logistic audit",
    "benchmark_rf": "Random forest benchmark",
    "coarse_q006": "Legacy coarse burden rule",
    "A0": "Core preoperative model",
    "A1": "Clinically informed preoperative model",
    "B0": "Pathology-augmented model",
    "M0_elastic": "Elastic-net comparison model",
    "M0_hgb": "Random forest comparison model",
    "treat_all": "Treat all",
    "treat_none": "Treat none",
}

_PHASE_C_MODEL_IDS_BY_LABEL: dict[str, str] = {
    str(label).strip().lower(): model_id
    for model_id, label in _PHASE_C_MODEL_LABELS.items()
}

_PHASE_C_FEATURE_LABELS: dict[str, str] = {
    "age": "Age",
    "diameter": "Tumor diameter",
    "e_axis_burden": "3-month axis burden",
    "hypopituitarism": "Preoperative hypopituitarism",
    "non_gtr": "Non-GTR burden",
    "knosp": "Knosp grade",
    "sex": "Female sex",
    "invasiveness": "Invasiveness",
}


def _model_label(model_id: str, fallback: str = "") -> str:
    normalized = str(model_id).strip()
    return _PHASE_C_MODEL_LABELS.get(normalized, str(fallback or normalized).strip() or normalized)


def _feature_label(feature_id: str) -> str:
    normalized = str(feature_id).strip()
    return _PHASE_C_FEATURE_LABELS.get(normalized, normalized.replace("_", " ").strip().title())


def _canonical_model_id(raw_value: object) -> str:
    normalized = str(raw_value or "").strip()
    if not normalized:
        raise ValueError("model label must be non-empty")
    if normalized in _PHASE_C_MODEL_ORDER:
        return normalized
    by_label = _PHASE_C_MODEL_IDS_BY_LABEL.get(normalized.lower())
    if by_label:
        return by_label
    raise ValueError(f"unsupported phase-c model label `{normalized}`")


def _ordered_model_ids(model_ids: set[str]) -> list[str]:
    ordered = [model_id for model_id in _PHASE_C_MODEL_ORDER if model_id in model_ids]
    ordered.extend(sorted(model_ids - set(ordered)))
    return ordered


def _select_story_models(
    *,
    available_model_ids: set[str],
    summary_payload: dict[str, Any] | None = None,
) -> tuple[str | None, str | None]:
    if not available_model_ids:
        return None, None
    ordered_model_ids = _ordered_model_ids(available_model_ids)
    candidate_story_model = str((summary_payload or {}).get("candidate_story_model") or "").strip()
    primary_model_id = candidate_story_model if candidate_story_model in available_model_ids else ordered_model_ids[0]
    if primary_model_id != "A0" and "A0" in available_model_ids:
        comparator_model_id = "A0"
    else:
        comparator_model_id = next((model_id for model_id in ordered_model_ids if model_id != primary_model_id), primary_model_id)
    return primary_model_id, comparator_model_id


def _normalize_calibration_rows(calibration_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not calibration_rows:
        return []
    if any(str(row.get("model_id") or "").strip() for row in calibration_rows):
        return calibration_rows
    normalized_rows: list[dict[str, str]] = []
    for row in calibration_rows:
        model_id = str(row.get("model") or "").strip()
        if not model_id:
            continue
        normalized_rows.append(
            {
                "model_id": model_id,
                "model_label": _model_label(model_id),
                "calibration_bin": str(row.get("bin_id") or row.get("calibration_bin") or "").strip(),
                "mean_predicted_probability": str(row.get("mean_predicted_probability") or "").strip(),
                "observed_probability": str(
                    row.get("observed_probability") or row.get("observed_non_gtr_rate") or row.get("risk_rate") or ""
                ).strip(),
            }
        )
    return normalized_rows


def _normalize_decision_rows(decision_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not decision_rows:
        return []
    if any(str(row.get("model_id") or "").strip() for row in decision_rows):
        return decision_rows
    normalized_rows: list[dict[str, str]] = []
    seen_keys: set[tuple[str, str]] = set()
    for row in decision_rows:
        threshold = str(row.get("threshold") or "").strip()
        model_id = str(row.get("model") or "").strip()
        model_net_benefit = str(row.get("net_benefit_model") or row.get("net_benefit") or "").strip()
        if model_id and threshold and model_net_benefit:
            key = (model_id, threshold)
            if key not in seen_keys:
                seen_keys.add(key)
                normalized_rows.append(
                    {
                        "model_id": model_id,
                        "model_label": _model_label(model_id),
                        "threshold": threshold,
                        "net_benefit": model_net_benefit,
                    }
                )
        for reference_model_id, net_benefit_key in (("treat_none", "net_benefit_treat_none"), ("treat_all", "net_benefit_treat_all")):
            reference_net_benefit = str(row.get(net_benefit_key) or "").strip()
            if not threshold or not reference_net_benefit:
                continue
            key = (reference_model_id, threshold)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            normalized_rows.append(
                {
                    "model_id": reference_model_id,
                    "model_label": _model_label(reference_model_id),
                    "threshold": threshold,
                    "net_benefit": reference_net_benefit,
                }
            )
    return normalized_rows


def _normalize_metrics_summary(metrics_summary: dict[str, Any]) -> dict[str, Any]:
    model_metrics = metrics_summary.get("model_metrics")
    if isinstance(model_metrics, list):
        return metrics_summary

    raw_metrics = metrics_summary.get("overall_metrics")
    if isinstance(raw_metrics, dict):
        return {
            "model_metrics": [
                {
                    "model_id": str(model_id).strip(),
                    "model_label": _model_label(str(model_id).strip()),
                    **metric_payload,
                }
                for model_id, metric_payload in raw_metrics.items()
                if isinstance(metric_payload, dict)
            ]
        }

    return {
        "model_metrics": [
            {
                "model_id": str(model_id).strip(),
                "model_label": _model_label(str(model_id).strip()),
                **metric_payload,
            }
            for model_id, metric_payload in metrics_summary.items()
            if isinstance(metric_payload, dict)
        ]
    }


def _normalize_metric_column_name(raw_label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", str(raw_label).strip().lower()).strip()
    metric_aliases = {
        "auroc": "roc_auc",
        "area under the receiver operating characteristic curve": "roc_auc",
        "auprc": "average_precision",
        "area under the precision recall curve": "average_precision",
        "average precision": "average_precision",
        "brier score": "brier_score",
        "calibration intercept": "calibration_intercept",
        "calibration slope": "calibration_slope",
    }
    return metric_aliases.get(normalized, normalized.replace(" ", "_"))


def _build_metrics_summary_from_performance_table(*, header: list[str], rows: list[list[str]]) -> dict[str, Any]:
    if len(header) < 2:
        raise ValueError("performance summary table must include a model column plus metrics")
    column_index = {
        _normalize_metric_column_name(label): index
        for index, label in enumerate(header)
        if index > 0
    }
    required_metric_keys = (
        "roc_auc",
        "average_precision",
        "brier_score",
        "calibration_intercept",
        "calibration_slope",
    )
    missing_metric_keys = [key for key in required_metric_keys if key not in column_index]
    if missing_metric_keys:
        missing = ", ".join(missing_metric_keys)
        raise ValueError(f"performance summary table missing required metric columns: {missing}")
    model_metrics: list[dict[str, Any]] = []
    for row in rows:
        if not row:
            continue
        model_id = _canonical_model_id(row[0])
        model_metrics.append(
            {
                "model_id": model_id,
                "model_label": _model_label(model_id, fallback=row[0]),
                **{metric_key: row[column_index[metric_key]] for metric_key in required_metric_keys},
            }
        )
    if not model_metrics:
        raise ValueError("performance summary table must include at least one model row")
    return {"model_metrics": model_metrics}


def _resolve_phase_c_performance_table_path(*, study_root: Path, paper_root: Path) -> Path:
    study_table2_path = study_root / "artifacts" / "final" / "tables" / "Table2.csv"
    if study_table2_path.exists():
        return study_table2_path
    table2_entry = _maybe_load_catalog_entry(paper_root=paper_root, catalog_kind="table", target_id="Table2")
    if table2_entry is None:
        raise ValueError("missing required table catalog entry: Table2")
    resolved_paths = _resolved_catalog_source_paths(paper_root=paper_root, catalog_entry=table2_entry)
    for filename in ("Table2.csv", "T2_main_metrics.csv"):
        matched = _find_source_path_by_name(paths=resolved_paths, filename=filename)
        if matched is not None:
            return matched
    csv_paths = [path for path in resolved_paths if path.suffix.lower() == ".csv"]
    if len(csv_paths) == 1:
        return csv_paths[0]
    if len(csv_paths) > 1:
        joined_paths = ", ".join(str(path) for path in csv_paths)
        raise ValueError(f"ambiguous Table2 CSV sources: {joined_paths}")
    raise ValueError("missing required Table2 CSV source")


def _maybe_binding(*, registry_payload: dict[str, Any], requirement_key: str) -> dict[str, str] | None:
    try:
        return _require_binding(registry_payload=registry_payload, requirement_key=requirement_key)
    except ValueError:
        return None


def _sync_risk_layering_payload(
    *,
    score_rows: list[dict[str, str]],
    grouped_rows: list[dict[str, str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
    title: str,
    left_panel_title: str = "Score bands",
    left_x_label: str = "Simple score",
    right_panel_title: str = "Grouped follow-up strata",
    right_x_label: str = "Grouped risk",
) -> dict[str, Any]:
    left_bars = [
        {
            "label": _feature_label(str(row.get("score_band") or row.get("risk_group") or "").strip()),
            "cases": int(str(row.get("n") or "").strip()),
            "events": int(str(row.get("events") or row.get("non_gtr_events") or "").strip()),
            "risk": _parse_float(
                row.get("risk_rate") or row.get("observed_non_gtr_rate"),
                label="score_risk_table.risk_rate",
            ),
        }
        for row in score_rows
    ]
    right_bars = [
        {
            "label": _feature_label(str(row.get("risk_group") or "").strip()),
            "cases": int(str(row.get("n") or "").strip()),
            "events": int(str(row.get("events") or row.get("non_gtr_events") or "").strip()),
            "risk": _parse_float(
                row.get("risk_rate") or row.get("observed_non_gtr_rate"),
                label="grouped_risk_table.risk_rate",
            ),
        }
        for row in grouped_rows
    ]
    return {
        "schema_version": 1,
        "input_schema_id": "risk_layering_monotonic_inputs_v1",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "displays": [
            {
                "display_id": display_id,
                "catalog_id": catalog_id,
                "template_id": "risk_layering_monotonic_bars",
                "title": title,
                "caption": (
                    "Observed risk of later persistent global hypopituitarism rises monotonically across score bands "
                    "and grouped follow-up strata."
                ),
                "y_label": "Risk of later persistent global hypopituitarism (%)",
                "left_panel_title": left_panel_title,
                "left_x_label": left_x_label,
                "left_bars": left_bars,
                "right_panel_title": right_panel_title,
                "right_x_label": right_x_label,
                "right_bars": right_bars,
            }
        ],
    }


def _sync_binary_calibration_decision_curve_payload(
    *,
    calibration_rows: list[dict[str, str]],
    decision_rows: list[dict[str, str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
    title: str,
) -> dict[str, Any]:
    calibration_rows = _normalize_calibration_rows(calibration_rows)
    decision_rows = _normalize_decision_rows(decision_rows)
    calibration_series: list[dict[str, Any]] = []
    for model_id in _PHASE_C_MODEL_ORDER:
        rows = [row for row in calibration_rows if str(row.get("model_id") or "").strip() == model_id]
        if not rows:
            continue
        sorted_rows = sorted(rows, key=lambda item: _parse_float(item.get("calibration_bin"), label="calibration_bin"))
        calibration_series.append(
            {
                "label": _model_label(model_id, fallback=str(sorted_rows[0].get("model_label") or "").strip()),
                "x": [
                    _parse_float(item.get("mean_predicted_probability"), label="mean_predicted_probability")
                    for item in sorted_rows
                ],
                "y": [
                    _parse_float(item.get("observed_probability"), label="observed_probability")
                    for item in sorted_rows
                ],
            }
        )

    filtered_decision_rows = [
        row
        for row in decision_rows
        if 0.15 <= _parse_float(row.get("threshold"), label="decision_curve.threshold") <= 0.40
    ]
    decision_series: list[dict[str, Any]] = []
    for model_id in _PHASE_C_MODEL_ORDER:
        rows = [row for row in filtered_decision_rows if str(row.get("model_id") or "").strip() == model_id]
        if not rows:
            continue
        sorted_rows = sorted(rows, key=lambda item: _parse_float(item.get("threshold"), label="decision_curve.threshold"))
        decision_series.append(
            {
                "label": _model_label(model_id, fallback=str(sorted_rows[0].get("model_label") or "").strip()),
                "x": [_parse_float(item.get("threshold"), label="decision_curve.threshold") for item in sorted_rows],
                "y": [_parse_float(item.get("net_benefit"), label="decision_curve.net_benefit") for item in sorted_rows],
            }
        )

    decision_reference_lines: list[dict[str, Any]] = []
    for model_id in ("treat_none", "treat_all"):
        rows = [row for row in filtered_decision_rows if str(row.get("model_id") or "").strip() == model_id]
        if not rows:
            continue
        sorted_rows = sorted(rows, key=lambda item: _parse_float(item.get("threshold"), label="decision_curve.threshold"))
        decision_reference_lines.append(
            {
                "label": _model_label(model_id, fallback=str(sorted_rows[0].get("model_label") or "").strip()),
                "x": [_parse_float(item.get("threshold"), label="decision_curve.threshold") for item in sorted_rows],
                "y": [_parse_float(item.get("net_benefit"), label="decision_curve.net_benefit") for item in sorted_rows],
            }
        )

    return {
        "schema_version": 1,
        "input_schema_id": "binary_calibration_decision_curve_panel_inputs_v1",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "displays": [
            {
                "display_id": display_id,
                "catalog_id": catalog_id,
                "template_id": "binary_calibration_decision_curve_panel",
                "title": title,
                "caption": (
                    "Calibration and decision-curve evidence across candidate packages within the prespecified "
                    "clinical threshold window."
                ),
                "calibration_x_label": "Mean predicted probability",
                "calibration_y_label": "Observed probability",
                "decision_x_label": "Threshold probability",
                "decision_y_label": "Net benefit",
                "calibration_reference_line": {"label": "Ideal", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                "calibration_series": calibration_series,
                "decision_series": decision_series,
                "decision_reference_lines": decision_reference_lines,
                "decision_focus_window": {"xmin": 0.15, "xmax": 0.40},
            }
        ],
    }


def _sync_model_complexity_audit_payload(
    *,
    metrics_summary: dict[str, Any],
    coefficient_rows: list[dict[str, str]],
    feature_importance_rows: list[dict[str, str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
    title: str,
) -> dict[str, Any]:
    metrics_summary = _normalize_metrics_summary(metrics_summary)
    metric_by_model = {
        str(item.get("model_id") or "").strip(): item
        for item in metrics_summary.get("model_metrics", [])
        if isinstance(item, dict)
    }

    def build_metric_panel(
        *,
        panel_id: str,
        panel_label: str,
        title: str,
        x_label: str,
        metric_key: str,
        reference_value: float | None = None,
    ) -> dict[str, Any]:
        rows = []
        for model_id in _PHASE_C_MODEL_ORDER:
            metric_payload = metric_by_model.get(model_id)
            if metric_payload is None:
                continue
            rows.append(
                {
                    "label": _model_label(model_id, fallback=str(metric_payload.get("model_label") or "").strip()),
                    "value": _parse_float(metric_payload.get(metric_key), label=f"metrics_summary.{metric_key}"),
                }
            )
        panel = {
            "panel_id": panel_id,
            "panel_label": panel_label,
            "title": title,
            "x_label": x_label,
            "rows": rows,
        }
        if reference_value is not None:
            panel["reference_value"] = reference_value
        return panel

    core_logistic_order = ("hypopituitarism", "e_axis_burden", "non_gtr")
    core_logistic_rows = {
        str(item.get("feature") or "").strip(): item
        for item in coefficient_rows
        if str(item.get("model_id") or "").strip() == "core_logistic"
    }
    odds_ratio_rows = [
        {
            "label": _feature_label(feature_id),
            "value": _parse_float(core_logistic_rows[feature_id].get("odds_ratio_mean"), label="odds_ratio_mean"),
        }
        for feature_id in core_logistic_order
        if feature_id in core_logistic_rows
    ]

    benchmark_rows = [
        item
        for item in feature_importance_rows
        if str(item.get("model_id") or "").strip() == "benchmark_rf"
    ]
    benchmark_rows = sorted(
        benchmark_rows,
        key=lambda item: _parse_float(item.get("importance_mean"), label="importance_mean"),
        reverse=True,
    )[:5]
    feature_importance_panel_rows = [
        {
            "label": _feature_label(str(item.get("feature") or "").strip()),
            "value": _parse_float(item.get("importance_mean"), label="importance_mean"),
        }
        for item in benchmark_rows
    ]

    if not odds_ratio_rows:
        coefficient_values_by_feature: dict[str, list[float]] = {}
        for item in coefficient_rows:
            feature_id = str(item.get("feature_name") or item.get("feature") or "").strip()
            raw_value = item.get("odds_ratio") or item.get("odds_ratio_mean")
            if not feature_id or raw_value is None:
                continue
            coefficient_values_by_feature.setdefault(feature_id, []).append(
                _parse_float(raw_value, label=f"{feature_id}.odds_ratio")
            )
        odds_ratio_rows = [
            {
                "label": _feature_label(feature_id),
                "value": sum(values) / len(values),
            }
            for feature_id, values in coefficient_values_by_feature.items()
            if values
        ]

    if not feature_importance_panel_rows:
        feature_importance_panel_rows = [
            {
                "label": str(item.get("domain") or "").strip(),
                "value": _parse_float(item.get("mean_abs_coefficient"), label="mean_abs_coefficient"),
            }
            for item in feature_importance_rows
            if str(item.get("domain") or "").strip()
            and item.get("mean_abs_coefficient") is not None
        ]

    core_logistic_title = "Core logistic odds ratios" if core_logistic_rows else "Coefficient stability"
    rf_importance_title = "Random forest feature importance" if benchmark_rows else "Domain stability"
    rf_importance_x_label = "Mean feature importance" if benchmark_rows else "Mean absolute coefficient"

    return {
        "schema_version": 1,
        "input_schema_id": "model_complexity_audit_panel_inputs_v1",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "displays": [
            {
                "display_id": display_id,
                "catalog_id": catalog_id,
                "template_id": "model_complexity_audit_panel",
                "title": title,
                "caption": (
                    "Discrimination, overall error, calibration, and bounded complexity audit across the "
                    "candidate packages."
                ),
                "metric_panels": [
                    build_metric_panel(
                        panel_id="auroc_panel",
                        panel_label="A",
                        title="Discrimination",
                        x_label="AUROC",
                        metric_key="roc_auc",
                    ),
                    build_metric_panel(
                        panel_id="brier_panel",
                        panel_label="B",
                        title="Overall error",
                        x_label="Brier score",
                        metric_key="brier_score",
                    ),
                    build_metric_panel(
                        panel_id="slope_panel",
                        panel_label="C",
                        title="Calibration",
                        x_label="Calibration slope",
                        metric_key="calibration_slope",
                        reference_value=1.0,
                    ),
                ],
                "audit_panels": [
                    {
                        "panel_id": "core_logistic_or_panel",
                        "panel_label": "D",
                        "title": core_logistic_title,
                        "x_label": "Mean odds ratio",
                        "reference_value": 1.0,
                        "rows": odds_ratio_rows,
                    },
                    {
                        "panel_id": "rf_importance_panel",
                        "panel_label": "E",
                        "title": rf_importance_title,
                        "x_label": rf_importance_x_label,
                        "rows": feature_importance_panel_rows,
                    },
                ],
            }
        ],
    }


def _sync_generic_performance_table_payload(
    *,
    header: list[str],
    rows: list[list[str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
    title: str,
) -> dict[str, Any]:
    columns = [
        {"column_id": _slugify(label), "label": label}
        for label in header[1:]
    ]
    normalized_rows = [
        {
            "row_id": _slugify(row[0]),
            "label": row[0],
            "values": row[1:],
        }
        for row in rows
    ]
    return {
        "schema_version": 1,
        "table_shell_id": "performance_summary_table_generic",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": (
            "Pooled out-of-fold discrimination, overall prediction error, and calibration summaries across "
            "the candidate packages."
        ),
        "row_header_label": header[0],
        "columns": columns,
        "rows": normalized_rows,
    }


def _sync_grouped_risk_event_table_payload(
    *,
    header: list[str],
    rows: list[list[str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
    title: str,
) -> dict[str, Any]:
    if len(header) != 5:
        raise ValueError("Table3 CSV must contain exactly five columns")
    normalized_rows = [
        {
            "row_id": _slugify(f"{row[0]}_{row[1]}"),
            "surface": row[0],
            "stratum": row[1],
            "cases": int(row[2]),
            "events": int(row[3]),
            "risk_display": row[4],
        }
        for row in rows
    ]
    return {
        "schema_version": 1,
        "table_shell_id": "grouped_risk_event_summary_table",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": title,
        "caption": (
            "Observed event counts and risks across score-band and grouped-risk strata for later persistent "
            "global hypopituitarism."
        ),
        "surface_column_label": header[0],
        "stratum_column_label": header[1],
        "cases_column_label": header[2],
        "events_column_label": header[3],
        "risk_column_label": header[4],
        "rows": normalized_rows,
    }


def _build_story_group_rows(*, risk_rows: list[dict[str, str]], model_id: str) -> list[dict[str, str]]:
    rows = [row for row in risk_rows if str(row.get("model") or row.get("model_id") or "").strip() == model_id]
    order = {"low": 0, "intermediate": 1, "high": 2}
    return sorted(rows, key=lambda item: order.get(str(item.get("risk_group") or "").strip().lower(), 99))


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def run_publication_shell_sync(*, study_root: Path, paper_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve()

    registry_payload = _load_json(resolved_paper_root / "display_registry.json")
    cohort_binding = _require_binding(registry_payload=registry_payload, requirement_key="cohort_flow_figure")
    table_binding = _require_binding(registry_payload=registry_payload, requirement_key="table1_baseline_characteristics")
    risk_layering_binding = _maybe_binding(
        registry_payload=registry_payload,
        requirement_key="risk_layering_monotonic_bars",
    )
    binary_calibration_binding = _maybe_binding(
        registry_payload=registry_payload,
        requirement_key="binary_calibration_decision_curve_panel",
    )
    model_complexity_binding = _maybe_binding(
        registry_payload=registry_payload,
        requirement_key="model_complexity_audit_panel",
    )
    generic_performance_binding = _maybe_binding(
        registry_payload=registry_payload,
        requirement_key="performance_summary_table_generic",
    )
    grouped_risk_event_binding = _maybe_binding(
        registry_payload=registry_payload,
        requirement_key="grouped_risk_event_summary_table",
    )

    cohort_source_path, cohort_source = _load_first_existing_json(
        resolved_study_root / "paper" / "derived" / "cohort_flow.json",
        resolved_study_root / "paper" / "derived" / "study_design_cohort_flow.json",
        resolved_paper_root / "derived" / "cohort_flow.json",
        resolved_paper_root / "derived" / "study_design_cohort_flow.json",
    )
    table_header, table_rows = _load_csv_rows(resolved_study_root / "artifacts" / "final" / "tables" / "Table1.csv")
    existing_cohort_payload = _load_json(resolved_paper_root / "cohort_flow.json")
    existing_table_payload = _load_json(resolved_paper_root / "baseline_characteristics_schema.json")

    cohort_payload = _sync_cohort_flow_payload(
        source_payload=cohort_source,
        existing_payload=existing_cohort_payload,
        display_id=cohort_binding["display_id"],
        catalog_id=cohort_binding["catalog_id"],
    )
    table_payload = _sync_table1_payload(
        header=table_header,
        rows=table_rows,
        existing_payload=existing_table_payload,
        display_id=table_binding["display_id"],
        catalog_id=table_binding["catalog_id"],
    )

    cohort_path = resolved_paper_root / "cohort_flow.json"
    table_path = resolved_paper_root / "baseline_characteristics_schema.json"
    _write_json(cohort_path, cohort_payload)
    _write_json(table_path, table_payload)

    written_files = [str(cohort_path), str(table_path)]
    source_paths: dict[str, object] = {
        "cohort_flow_source": str(cohort_source_path),
        "table1_source": str(resolved_study_root / "artifacts" / "final" / "tables" / "Table1.csv"),
    }

    if risk_layering_binding is not None:
        figure2_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure2")
        score_risk_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "score_risk_table.csv"
        grouped_risk_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "grouped_risk_table.csv"
        existing_risk_layering_payload = _load_json_if_exists(resolved_paper_root / "risk_layering_monotonic_inputs.json")
        risk_layering_sources: list[str]
        score_rows: list[dict[str, str]]
        grouped_rows: list[dict[str, str]]
        left_panel_title = "Score bands"
        left_x_label = "Simple score"
        right_panel_title = "Grouped follow-up strata"
        right_x_label = "Grouped risk"
        risk_layering_payload: dict[str, Any] | None = None
        if score_risk_path.exists() and grouped_risk_path.exists():
            score_rows = _load_csv_records(score_risk_path)
            grouped_rows = _load_csv_records(grouped_risk_path)
            risk_layering_sources = [str(score_risk_path), str(grouped_risk_path)]
        else:
            try:
                resolved_paths = _resolved_catalog_source_paths(paper_root=resolved_paper_root, catalog_entry=figure2_entry)
                risk_stratification_path = _require_source_path_by_name(paths=resolved_paths, filename="risk_stratification.csv")
                summary_path = _require_source_path_by_name(paths=resolved_paths, filename="summary.json")
                risk_rows = _load_csv_records(risk_stratification_path)
                summary_payload = _load_json(summary_path)
                available_model_ids = {
                    str(row.get("model") or row.get("model_id") or "").strip()
                    for row in risk_rows
                    if str(row.get("model") or row.get("model_id") or "").strip()
                }
                primary_model_id, comparator_model_id = _select_story_models(
                    available_model_ids=available_model_ids,
                    summary_payload=summary_payload,
                )
                if primary_model_id is None or comparator_model_id is None:
                    raise ValueError("risk stratification source must include at least one model")
                score_rows = _build_story_group_rows(risk_rows=risk_rows, model_id=comparator_model_id)
                grouped_rows = _build_story_group_rows(risk_rows=risk_rows, model_id=primary_model_id)
                left_panel_title = "Core preoperative comparator"
                left_x_label = "Predicted-risk tertile"
                right_panel_title = "Clinically informed model"
                right_x_label = "Predicted-risk tertile"
                risk_layering_sources = [str(risk_stratification_path), str(summary_path)]
            except (FileNotFoundError, ValueError):
                if not existing_risk_layering_payload:
                    raise
                risk_layering_payload = existing_risk_layering_payload
                risk_layering_sources = [str(resolved_paper_root / "risk_layering_monotonic_inputs.json")]
        if risk_layering_payload is None:
            risk_layering_payload = _sync_risk_layering_payload(
                score_rows=score_rows,
                grouped_rows=grouped_rows,
                existing_payload=existing_risk_layering_payload,
                display_id=risk_layering_binding["display_id"],
                catalog_id=risk_layering_binding["catalog_id"],
                title=str((figure2_entry or {}).get("title") or "Monotonic risk layering of the 3-month endocrine burden score").strip(),
                left_panel_title=left_panel_title,
                left_x_label=left_x_label,
                right_panel_title=right_panel_title,
                right_x_label=right_x_label,
            )
        risk_layering_path = resolved_paper_root / "risk_layering_monotonic_inputs.json"
        _write_json(risk_layering_path, risk_layering_payload)
        written_files.append(str(risk_layering_path))
        source_paths["risk_layering_sources"] = risk_layering_sources

    if binary_calibration_binding is not None:
        figure2_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure2")
        figure3_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure3")
        calibration_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "calibration_curve.csv"
        decision_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "decision_curve.csv"
        existing_binary_payload = _load_json_if_exists(resolved_paper_root / "binary_calibration_decision_curve_panel_inputs.json")
        binary_calibration_sources: list[str]
        if not calibration_path.exists() or not decision_path.exists():
            try:
                resolved_paths = _resolved_catalog_source_paths(paper_root=resolved_paper_root, catalog_entry=figure3_entry)
                calibration_path = _require_source_path_by_name(paths=resolved_paths, filename="calibration_curve.csv")
                decision_path = _require_source_path_by_name(paths=resolved_paths, filename="decision_curve.csv")
            except (FileNotFoundError, ValueError):
                try:
                    fallback_paths = _resolved_catalog_source_paths(paper_root=resolved_paper_root, catalog_entry=figure2_entry)
                    calibration_path = _require_source_path_by_name(paths=fallback_paths, filename="calibration_curve.csv")
                    decision_path = _require_source_path_by_name(paths=fallback_paths, filename="decision_curve.csv")
                except (FileNotFoundError, ValueError):
                    if not existing_binary_payload:
                        raise
                    binary_calibration_payload = existing_binary_payload
                    binary_calibration_sources = [str(resolved_paper_root / "binary_calibration_decision_curve_panel_inputs.json")]
                else:
                    binary_calibration_payload = _sync_binary_calibration_decision_curve_payload(
                        calibration_rows=_load_csv_records(calibration_path),
                        decision_rows=_load_csv_records(decision_path),
                        existing_payload=existing_binary_payload,
                        display_id=binary_calibration_binding["display_id"],
                        catalog_id=binary_calibration_binding["catalog_id"],
                        title=str(
                            (figure3_entry or {}).get("title")
                            or "Calibration and decision-curve comparison of the candidate packages"
                        ).strip(),
                    )
                    binary_calibration_sources = [str(calibration_path), str(decision_path)]
            else:
                binary_calibration_payload = _sync_binary_calibration_decision_curve_payload(
                    calibration_rows=_load_csv_records(calibration_path),
                    decision_rows=_load_csv_records(decision_path),
                    existing_payload=existing_binary_payload,
                    display_id=binary_calibration_binding["display_id"],
                    catalog_id=binary_calibration_binding["catalog_id"],
                    title=str(
                        (figure3_entry or {}).get("title") or "Calibration and decision-curve comparison of the candidate packages"
                    ).strip(),
                )
                binary_calibration_sources = [str(calibration_path), str(decision_path)]
        else:
            binary_calibration_payload = _sync_binary_calibration_decision_curve_payload(
                calibration_rows=_load_csv_records(calibration_path),
                decision_rows=_load_csv_records(decision_path),
                existing_payload=existing_binary_payload,
                display_id=binary_calibration_binding["display_id"],
                catalog_id=binary_calibration_binding["catalog_id"],
                title=str((figure3_entry or {}).get("title") or "Calibration and decision-curve comparison of the candidate packages").strip(),
            )
            binary_calibration_sources = [str(calibration_path), str(decision_path)]
        binary_calibration_path = resolved_paper_root / "binary_calibration_decision_curve_panel_inputs.json"
        _write_json(binary_calibration_path, binary_calibration_payload)
        written_files.append(str(binary_calibration_path))
        source_paths["binary_calibration_decision_curve_sources"] = binary_calibration_sources

    if model_complexity_binding is not None:
        figure3_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure3")
        figure4_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure4")
        metrics_summary_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "metrics_summary.json"
        coefficient_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "coefficient_summary.csv"
        feature_importance_path = resolved_study_root / "artifacts" / "run1_followup_stratifier" / "feature_importance_summary.csv"
        figure3_paths = _resolved_catalog_source_paths(paper_root=resolved_paper_root, catalog_entry=figure3_entry)
        existing_model_complexity_payload = _load_json_if_exists(resolved_paper_root / "model_complexity_audit_panel_inputs.json")
        model_complexity_sources: list[str]
        try:
            if metrics_summary_path.exists():
                metrics_summary_payload = _load_json(metrics_summary_path)
                metrics_source_path = metrics_summary_path
            else:
                legacy_metrics_path = _find_source_path_by_name(paths=figure3_paths, filename="metrics.json")
                if legacy_metrics_path is not None:
                    metrics_summary_payload = _load_json(legacy_metrics_path)
                    metrics_source_path = legacy_metrics_path
                else:
                    metrics_source_path = _resolve_phase_c_performance_table_path(
                        study_root=resolved_study_root,
                        paper_root=resolved_paper_root,
                    )
                    metrics_header, metrics_rows = _load_csv_rows(metrics_source_path)
                    metrics_summary_payload = _build_metrics_summary_from_performance_table(
                        header=metrics_header,
                        rows=metrics_rows,
                    )
            if not coefficient_path.exists():
                coefficient_path = _require_source_path_by_name(
                    paths=figure3_paths,
                    filename="clinical_utility_model_coefficient_stability.csv",
                )
            if not feature_importance_path.exists():
                feature_importance_path = _require_source_path_by_name(
                    paths=figure3_paths,
                    filename="clinical_utility_model_domain_summary.csv",
                )
            model_complexity_payload = _sync_model_complexity_audit_payload(
                metrics_summary=metrics_summary_payload,
                coefficient_rows=_load_csv_records(coefficient_path),
                feature_importance_rows=_load_csv_records(feature_importance_path),
                existing_payload=existing_model_complexity_payload,
                display_id=model_complexity_binding["display_id"],
                catalog_id=model_complexity_binding["catalog_id"],
                title=str((figure4_entry or {}).get("title") or "Unified model comparison and comparative model assessment").strip(),
            )
            model_complexity_sources = [
                str(metrics_source_path),
                str(coefficient_path),
                str(feature_importance_path),
            ]
        except (FileNotFoundError, ValueError):
            if not existing_model_complexity_payload:
                raise
            model_complexity_payload = existing_model_complexity_payload
            model_complexity_sources = [str(resolved_paper_root / "model_complexity_audit_panel_inputs.json")]
        model_complexity_path = resolved_paper_root / "model_complexity_audit_panel_inputs.json"
        _write_json(model_complexity_path, model_complexity_payload)
        written_files.append(str(model_complexity_path))
        source_paths["model_complexity_audit_sources"] = model_complexity_sources

    if generic_performance_binding is not None:
        table2_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="table", target_id="Table2")
        table2_csv_path = _resolve_phase_c_performance_table_path(
            study_root=resolved_study_root,
            paper_root=resolved_paper_root,
        )
        generic_header, generic_rows = _load_csv_rows(table2_csv_path)
        generic_performance_payload = _sync_generic_performance_table_payload(
            header=generic_header,
            rows=generic_rows,
            existing_payload=_load_json_if_exists(resolved_paper_root / "performance_summary_table_generic.json"),
            display_id=generic_performance_binding["display_id"],
            catalog_id=generic_performance_binding["catalog_id"],
            title=str((table2_entry or {}).get("title") or "Unified repeated nested validation results across candidate packages").strip(),
        )
        generic_performance_path = resolved_paper_root / "performance_summary_table_generic.json"
        _write_json(generic_performance_path, generic_performance_payload)
        written_files.append(str(generic_performance_path))
        source_paths["performance_summary_table_source"] = str(table2_csv_path)

    if grouped_risk_event_binding is not None:
        figure2_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure2")
        figure4_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="figure", target_id="Figure4")
        table3_entry = _maybe_load_catalog_entry(paper_root=resolved_paper_root, catalog_kind="table", target_id="Table3")
        table3_csv_path = resolved_study_root / "artifacts" / "final" / "tables" / "Table3.csv"
        existing_grouped_risk_payload = _load_json_if_exists(resolved_paper_root / "grouped_risk_event_summary_table.json")
        grouped_risk_event_payload: dict[str, Any] | None = None
        grouped_risk_event_source = ""
        if not table3_csv_path.exists() and table3_entry is not None:
            fallback_table3_csv = str(table3_entry.get("csv_path") or "").strip()
            if fallback_table3_csv:
                table3_csv_path = _resolve_paper_relative_path(resolved_paper_root, fallback_table3_csv)
        if table3_csv_path.exists():
            grouped_header, grouped_rows = _load_csv_rows(table3_csv_path)
            if len(grouped_header) == 5:
                grouped_risk_event_payload = _sync_grouped_risk_event_table_payload(
                    header=grouped_header,
                    rows=grouped_rows,
                    existing_payload=existing_grouped_risk_payload,
                    display_id=grouped_risk_event_binding["display_id"],
                    catalog_id=grouped_risk_event_binding["catalog_id"],
                    title=str((table3_entry or {}).get("title") or "Event rates across the simple-score and grouped-risk surfaces").strip(),
                )
                grouped_risk_event_source = str(table3_csv_path)
            else:
                table3_csv_path = None
        if grouped_risk_event_payload is None:
            try:
                figure4_paths = _resolved_catalog_source_paths(paper_root=resolved_paper_root, catalog_entry=figure4_entry)
                figure2_paths = _resolved_catalog_source_paths(paper_root=resolved_paper_root, catalog_entry=figure2_entry)
                risk_stratification_path = _find_source_path_by_name(paths=figure4_paths, filename="risk_stratification.csv")
                if risk_stratification_path is None:
                    risk_stratification_path = _require_source_path_by_name(paths=figure2_paths, filename="risk_stratification.csv")
                summary_path = _find_source_path_by_name(paths=figure4_paths, filename="summary.json")
                if summary_path is None:
                    summary_path = _find_source_path_by_name(paths=figure2_paths, filename="summary.json")
                if summary_path is None:
                    raise ValueError("missing required source file `summary.json` in Figure2/Figure4 catalog source_paths")
                risk_rows = _load_csv_records(risk_stratification_path)
                summary_payload = _load_json(summary_path)
                available_model_ids = {
                    str(row.get("model") or row.get("model_id") or "").strip()
                    for row in risk_rows
                    if str(row.get("model") or row.get("model_id") or "").strip()
                }
                primary_model_id, comparator_model_id = _select_story_models(
                    available_model_ids=available_model_ids,
                    summary_payload=summary_payload,
                )
                if primary_model_id is None or comparator_model_id is None:
                    raise ValueError("grouped risk source must include at least one model")
                grouped_story_rows: list[list[str]] = []
                for model_id in (comparator_model_id, primary_model_id):
                    for row in _build_story_group_rows(risk_rows=risk_rows, model_id=model_id):
                        grouped_story_rows.append(
                            [
                                _model_label(model_id),
                                _feature_label(str(row.get("risk_group") or "").strip()),
                                str(row.get("n") or "").strip(),
                                str(row.get("non_gtr_events") or row.get("events") or "").strip(),
                                _format_percent(
                                    _parse_float(
                                        row.get("observed_non_gtr_rate") or row.get("risk_rate"),
                                        label="risk_stratification.observed_non_gtr_rate",
                                    )
                                ),
                            ]
                        )
                grouped_risk_event_payload = _sync_grouped_risk_event_table_payload(
                    header=["Surface", "Stratum", "Cases", "Events", "Risk of later persistent global hypopituitarism"],
                    rows=grouped_story_rows,
                    existing_payload=existing_grouped_risk_payload,
                    display_id=grouped_risk_event_binding["display_id"],
                    catalog_id=grouped_risk_event_binding["catalog_id"],
                    title=str((table3_entry or {}).get("title") or "Grouped risk-event summary").strip(),
                )
                grouped_risk_event_source = str(risk_stratification_path)
            except (FileNotFoundError, ValueError):
                if not existing_grouped_risk_payload:
                    raise
                grouped_risk_event_payload = existing_grouped_risk_payload
                grouped_risk_event_source = str(resolved_paper_root / "grouped_risk_event_summary_table.json")
        grouped_risk_event_path = resolved_paper_root / "grouped_risk_event_summary_table.json"
        _write_json(grouped_risk_event_path, grouped_risk_event_payload)
        written_files.append(str(grouped_risk_event_path))
        source_paths["grouped_risk_event_table_source"] = grouped_risk_event_source or str(grouped_risk_event_path)

    report_path = resolved_paper_root / "direct_migration" / "publication_shell_sync_report.json"
    report = {
        "status": "synced",
        "recorded_at": _utc_now(),
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "written_files": [*written_files, str(report_path)],
        "source_paths": source_paths,
    }
    _write_json(report_path, report)
    return report
