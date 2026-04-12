from __future__ import annotations

import csv
from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any


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


def _resolve_table1_source_path(*, study_root: Path) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    candidates = (
        resolved_study_root / "paper" / "submission_minimal" / "tables" / "Table1.csv",
        resolved_study_root / "manuscript" / "current_package" / "tables" / "Table1.csv",
        resolved_study_root / "manuscript" / "submission_package" / "tables" / "Table1.csv",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    expected_paths = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(
        "missing required Table1 CSV in the audited delivery surfaces; expected one of: "
        f"{expected_paths}"
    )


def _sync_cohort_flow_payload(
    *,
    source_payload: dict[str, Any],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    steps = [
        {
            "step_id": "source_total_cases",
            "label": "Source cases",
            "n": int(source_payload["source_total_cases"]),
            "detail": f"Dataset version: {source_payload.get('dataset_version') or 'unspecified'}",
        },
        {
            "step_id": "first_surgery_cases",
            "label": "First-surgery cohort",
            "n": int(source_payload["first_surgery_cases"]),
            "detail": f"Excluded non-first-surgery cases: {int(source_payload.get('excluded_non_first_surgery') or 0)}",
        },
        {
            "step_id": "complete_3_month_landmark_cases",
            "label": "Complete 3-month landmark",
            "n": int(source_payload["complete_3_month_landmark_cases"]),
            "detail": "All required landmark variables available",
        },
        {
            "step_id": "complete_later_endpoint_cases",
            "label": "Complete later endpoint follow-up",
            "n": int(source_payload["complete_later_endpoint_cases"]),
            "detail": "Later endpoint ascertainment completed",
        },
        {
            "step_id": "analysis_cases",
            "label": "Final analysis cohort",
            "n": int(source_payload["analysis_cases"]),
            "detail": f"Later persistent global hypopituitarism events: {int(source_payload.get('analysis_event_n') or 0)}",
        },
    ]
    return {
        "schema_version": 1,
        "shell_id": "cohort_flow_figure",
        "source_contract_path": str(existing_payload.get("source_contract_path") or "paper/medical_reporting_contract.json"),
        "display_id": display_id,
        "catalog_id": catalog_id,
        "title": "Cohort derivation at the 3-month postoperative landmark",
        "caption": (
            "Study derivation from the full source dataset to the first-surgery landmark cohort with complete later "
            "endpoint ascertainment."
        ),
        "steps": steps,
    }


def _sync_table1_payload(
    *,
    header: list[str],
    rows: list[list[str]],
    existing_payload: dict[str, Any],
    display_id: str,
    catalog_id: str,
) -> dict[str, Any]:
    groups = [
        {
            "group_id": _slugify(label),
            "label": label,
        }
        for label in header[1:]
    ]
    variables = []
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


def run_publication_shell_sync(*, study_root: Path, paper_root: Path) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    registry_payload = _load_json(resolved_paper_root / "display_registry.json")
    cohort_binding = _require_binding(registry_payload=registry_payload, requirement_key="cohort_flow_figure")
    table_binding = _require_binding(registry_payload=registry_payload, requirement_key="table1_baseline_characteristics")

    cohort_source = _load_json(resolved_study_root / "paper" / "derived" / "cohort_flow.json")
    table1_source_path = _resolve_table1_source_path(study_root=resolved_study_root)
    table_header, table_rows = _load_csv_rows(table1_source_path)
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

    report_path = resolved_paper_root / "direct_migration" / "publication_shell_sync_report.json"
    report = {
        "status": "synced",
        "recorded_at": _utc_now(),
        "study_root": str(resolved_study_root),
        "paper_root": str(resolved_paper_root),
        "written_files": [str(cohort_path), str(table_path), str(report_path)],
        "source_paths": {
            "cohort_flow_source": str(resolved_study_root / "paper" / "derived" / "cohort_flow.json"),
            "table1_source": str(table1_source_path),
        },
    }
    _write_json(report_path, report)
    return report
