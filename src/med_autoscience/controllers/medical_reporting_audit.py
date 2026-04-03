from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.runtime_protocol import paper_artifacts


def _load_json_dict(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _normalize_display_shell_plan(reporting_contract: dict[str, object]) -> list[dict[str, str]]:
    plan = reporting_contract.get("display_shell_plan")
    normalized: list[dict[str, str]] = []
    if isinstance(plan, list):
        for item in plan:
            if not isinstance(item, dict):
                continue
            display_id = str(item.get("display_id") or "").strip()
            display_kind = str(item.get("display_kind") or "").strip()
            requirement_key = str(item.get("requirement_key") or "").strip()
            if not display_id or not display_kind or not requirement_key:
                continue
            normalized.append(
                {
                    "display_id": display_id,
                    "display_kind": display_kind,
                    "requirement_key": requirement_key,
                }
            )
        return normalized

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
        normalized.append(
            {
                "display_id": "Figure1",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
            }
        )
    if baseline_enabled:
        normalized.append(
            {
                "display_id": "Table1",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
            }
        )
    return normalized


def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    del apply
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    try:
        paper_root = paper_artifacts.resolve_latest_paper_root(resolved_quest_root)
    except FileNotFoundError:
        paper_root = resolved_quest_root / "paper"
    blockers: list[str] = []
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    if not reporting_contract_path.exists():
        blockers.append("missing_medical_reporting_contract")
        reporting_contract: dict[str, object] = {}
    else:
        try:
            reporting_contract = _load_json_dict(reporting_contract_path) or {}
        except (OSError, ValueError, json.JSONDecodeError):
            blockers.append("invalid_medical_reporting_contract")
            reporting_contract = {}

    display_shell_plan = _normalize_display_shell_plan(reporting_contract)
    if bool(reporting_contract.get("display_registry_required", bool(display_shell_plan))):
        display_registry_path = paper_root / "display_registry.json"
        if not display_registry_path.exists():
            blockers.append("missing_display_registry")
        else:
            try:
                display_registry = _load_json_dict(display_registry_path) or {}
            except (OSError, ValueError, json.JSONDecodeError):
                blockers.append("invalid_display_registry")
                display_registry = {}
            registry_items = display_registry.get("displays")
            if isinstance(registry_items, list):
                registry_keys = {
                    (
                        str(item.get("display_id") or "").strip(),
                        str(item.get("display_kind") or "").strip(),
                        str(item.get("requirement_key") or "").strip(),
                    )
                    for item in registry_items
                    if isinstance(item, dict)
                }
                contract_keys = {
                    (item["display_id"], item["display_kind"], item["requirement_key"])
                    for item in display_shell_plan
                }
                if registry_keys != contract_keys:
                    blockers.append("registry_contract_mismatch")
            else:
                blockers.append("invalid_display_registry")

    for item in display_shell_plan:
        if item["display_kind"] == "figure":
            shell_path = paper_root / "figures" / f"{item['display_id']}.shell.json"
            if not shell_path.exists():
                blockers.append(f"missing_{item['display_id'].lower()}_shell")
        else:
            shell_path = paper_root / "tables" / f"{item['display_id']}.shell.json"
            if not shell_path.exists():
                blockers.append(f"missing_{item['display_id'].lower()}_shell")

        if item["requirement_key"] == "cohort_flow_figure" and not (paper_root / "cohort_flow.json").exists():
            blockers.append("missing_cohort_flow")
        if item["requirement_key"] == "table1_baseline_characteristics" and not (
            paper_root / "baseline_characteristics_schema.json"
        ).exists():
            blockers.append("missing_baseline_characteristics_schema")

    if not (paper_root / "reporting_guideline_checklist.json").exists():
        blockers.append("missing_reporting_guideline_checklist")
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "action": "clear",
        "quest_root": str(resolved_quest_root),
        "report_json": None,
        "report_markdown": None,
    }
