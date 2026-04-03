from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import literature_hydration as literature_hydration_controller
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _require_dict(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"hydration payload must contain mapping: {key}")
    return dict(value)


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"hydration payload must contain non-empty string: {key}")
    return value.strip()


def _optional_record_list(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"hydration payload must contain list when provided: {key}")
    records: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"hydration payload {key} must contain mappings")
        records.append(dict(item))
    return records


def _normalize_display_shell_plan(reporting_contract: dict[str, object]) -> list[dict[str, str]]:
    plan = reporting_contract.get("display_shell_plan")
    normalized: list[dict[str, str]] = []
    if isinstance(plan, list):
        for item in plan:
            if not isinstance(item, dict):
                raise ValueError("medical_reporting_contract.display_shell_plan must contain mappings")
            display_id = str(item.get("display_id") or "").strip()
            display_kind = str(item.get("display_kind") or "").strip()
            requirement_key = str(item.get("requirement_key") or "").strip()
            if not display_id or not display_kind or not requirement_key:
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include display_id, display_kind, requirement_key"
                )
            normalized.append(
                {
                    "display_id": display_id,
                    "display_kind": display_kind,
                    "requirement_key": requirement_key,
                }
            )
        return normalized

    legacy_plan: list[dict[str, str]] = []
    figure_shell_requirements = list(reporting_contract.get("figure_shell_requirements") or [])
    table_shell_requirements = list(reporting_contract.get("table_shell_requirements") or [])
    cohort_flow_required = reporting_contract.get("cohort_flow_required")
    baseline_required = reporting_contract.get("baseline_characteristics_required")
    if cohort_flow_required is False:
        cohort_flow_enabled = False
    elif figure_shell_requirements:
        cohort_flow_enabled = "cohort_flow_figure" in figure_shell_requirements
    else:
        cohort_flow_enabled = True
    if baseline_required is False:
        baseline_enabled = False
    elif table_shell_requirements:
        baseline_enabled = "table1_baseline_characteristics" in table_shell_requirements
    else:
        baseline_enabled = True

    if cohort_flow_enabled:
        legacy_plan.append(
            {
                "display_id": "Figure1",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
            }
        )
    if baseline_enabled:
        legacy_plan.append(
            {
                "display_id": "Table1",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
            }
        )
    return legacy_plan


def _write_json_if_missing(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists():
        return False
    _write_json(path, payload)
    return True


def _write_display_surface_stubs(
    *,
    quest_root: Path,
    reporting_contract: dict[str, object],
) -> list[str]:
    paper_root = quest_root / "paper"
    reporting_contract_relpath = "paper/medical_reporting_contract.json"
    display_shell_plan = _normalize_display_shell_plan(reporting_contract)
    written_files: list[str] = []

    display_registry_required = bool(reporting_contract.get("display_registry_required", bool(display_shell_plan)))
    display_registry_path = paper_root / "display_registry.json"
    display_registry_payload = {
        "schema_version": 1,
        "source_contract_path": reporting_contract_relpath,
        "displays": [
            {
                **item,
                "shell_path": (
                    f"paper/figures/{item['display_id']}.shell.json"
                    if item["display_kind"] == "figure"
                    else f"paper/tables/{item['display_id']}.shell.json"
                ),
            }
            for item in display_shell_plan
        ],
    }
    if display_registry_required and _write_json_if_missing(display_registry_path, display_registry_payload):
        written_files.append(str(display_registry_path))

    for item in display_shell_plan:
        if item["display_kind"] == "figure":
            shell_path = paper_root / "figures" / f"{item['display_id']}.shell.json"
        else:
            shell_path = paper_root / "tables" / f"{item['display_id']}.shell.json"
        shell_payload = {
            "schema_version": 1,
            "source_contract_path": reporting_contract_relpath,
            "display_id": item["display_id"],
            "display_kind": item["display_kind"],
            "requirement_key": item["requirement_key"],
        }
        if _write_json_if_missing(shell_path, shell_payload):
            written_files.append(str(shell_path))

        if item["requirement_key"] == "cohort_flow_figure":
            cohort_flow_path = paper_root / "cohort_flow.json"
            cohort_flow_payload = {
                "schema_version": 1,
                "shell_id": "cohort_flow_figure",
                "display_id": item["display_id"],
                "source_contract_path": reporting_contract_relpath,
                "status": "required_pending_population_accounting",
                "population_accounting": [],
            }
            if _write_json_if_missing(cohort_flow_path, cohort_flow_payload):
                written_files.append(str(cohort_flow_path))
        if item["requirement_key"] == "table1_baseline_characteristics":
            baseline_schema_path = paper_root / "baseline_characteristics_schema.json"
            baseline_schema_payload = {
                "schema_version": 1,
                "table_shell_id": "table1_baseline_characteristics",
                "display_id": item["display_id"],
                "source_contract_path": reporting_contract_relpath,
                "status": "required_pending_table_materialization",
                "group_columns": [],
                "variables": [],
            }
            if _write_json_if_missing(baseline_schema_path, baseline_schema_payload):
                written_files.append(str(baseline_schema_path))

    return written_files


def run_hydration(*, quest_root: Path, hydration_payload: dict[str, object]) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    medical_analysis_contract = _require_dict(hydration_payload, "medical_analysis_contract")
    medical_reporting_contract = _require_dict(hydration_payload, "medical_reporting_contract")
    entry_state_summary = _require_str(hydration_payload, "entry_state_summary")
    literature_records = _optional_record_list(hydration_payload, "literature_records")

    analysis_path = resolved_quest_root / "paper" / "medical_analysis_contract.json"
    reporting_path = resolved_quest_root / "paper" / "medical_reporting_contract.json"

    _write_json(analysis_path, medical_analysis_contract)
    _write_json(reporting_path, medical_reporting_contract)
    display_surface_files = _write_display_surface_stubs(
        quest_root=resolved_quest_root,
        reporting_contract=medical_reporting_contract,
    )
    literature_report = literature_hydration_controller.run_literature_hydration(
        quest_root=resolved_quest_root,
        records=literature_records,
    )
    written_files = [
        str(analysis_path),
        str(reporting_path),
        *display_surface_files,
        literature_report["records_path"],
        literature_report["references_bib_path"],
        literature_report["coverage_report_path"],
    ]
    imported_records_path = literature_report.get("imported_records_path")
    if isinstance(imported_records_path, str) and imported_records_path:
        written_files.append(imported_records_path)
    report = study_runtime_protocol.write_startup_hydration_report(
        quest_root=resolved_quest_root,
        report=study_runtime_protocol.StartupHydrationReport(
            status=study_runtime_protocol.StartupHydrationStatus.HYDRATED,
            recorded_at=_utc_now(),
            quest_root=str(resolved_quest_root),
            entry_state_summary=entry_state_summary,
            literature_report=literature_report,
            written_files=tuple(written_files),
            report_path=None,
        ),
    )
    return report.to_dict()
