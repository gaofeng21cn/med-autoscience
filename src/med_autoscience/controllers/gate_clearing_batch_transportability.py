from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.profiles import WorkspaceProfile


TRANSPORTABILITY_REQUIREMENT_KEY = "center_transportability_governance_summary_panel"
TRANSPORTABILITY_INPUT_SCHEMA_ID = "center_transportability_governance_summary_panel_inputs_v1"
TRANSPORTABILITY_INPUT_FILENAME = "center_transportability_governance_summary_panel_inputs.json"


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists() and _read_json(path) == payload:
        return False
    _write_json(path, payload)
    return True


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _display_plan_for_contract(contract: dict[str, Any]) -> list[dict[str, Any]]:
    display_shell_plan = contract.get("display_shell_plan")
    if not isinstance(display_shell_plan, list):
        return []
    return [dict(item) for item in display_shell_plan if isinstance(item, dict)]


def _contract_requires_transportability_governance(contract: dict[str, Any]) -> bool:
    return any(
        _non_empty_text(item.get("requirement_key")) == TRANSPORTABILITY_REQUIREMENT_KEY
        for item in _display_plan_for_contract(contract)
    )


def _current_transportability_payload_is_substantive(*, paper_root: Path) -> bool:
    payload = _read_json(Path(paper_root) / TRANSPORTABILITY_INPUT_FILENAME)
    if _non_empty_text(payload.get("input_schema_id")) != TRANSPORTABILITY_INPUT_SCHEMA_ID:
        return False
    displays = payload.get("displays")
    if not isinstance(displays, list) or not displays:
        return False
    for item in displays:
        if not isinstance(item, dict):
            continue
        centers = item.get("centers")
        if isinstance(centers, list) and centers:
            return True
    return False


def transportability_reporting_contract_required(
    *,
    study_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any] | None:
    from med_autoscience.controllers import medical_reporting_contract as medical_reporting_contract_controller

    resolved_study_root = Path(study_root).expanduser().resolve()
    study_payload = _read_yaml(resolved_study_root / "study.yaml")
    if not study_payload:
        return None
    contract = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
        study_root=resolved_study_root,
        study_payload=study_payload,
        profile=profile,
    )
    if _non_empty_text(contract.get("status")) != "resolved":
        return None
    if _contract_requires_transportability_governance(contract):
        return contract
    return None


def sync_transportability_reporting_surface(
    *,
    study_root: Path,
    paper_root: Path,
    profile: WorkspaceProfile,
) -> dict[str, Any]:
    from med_autoscience.controllers import quest_hydration

    contract = transportability_reporting_contract_required(study_root=study_root, profile=profile)
    if contract is None:
        return {"status": "skipped", "reason": "study reporting contract does not require transportability F5"}
    reporting_contract_path = Path(paper_root) / "medical_reporting_contract.json"
    written_files: list[str] = []
    if _write_json_if_changed(reporting_contract_path, contract):
        written_files.append(str(reporting_contract_path))
    written_files.extend(
        quest_hydration._write_display_surface_stubs(
            paper_root=Path(paper_root),
            reporting_contract=contract,
        )
    )
    return {
        "status": "updated" if written_files else "current",
        "written_files": sorted(dict.fromkeys(written_files)),
        "reporting_contract_path": str(reporting_contract_path),
        "transportability_input_path": str(Path(paper_root) / TRANSPORTABILITY_INPUT_FILENAME),
        "materialization_owner": "time_to_event_direct_migration",
    }


def transportability_reporting_surface_needs_sync(
    *,
    study_root: Path,
    paper_root: Path,
    profile: WorkspaceProfile,
) -> bool:
    contract = transportability_reporting_contract_required(study_root=study_root, profile=profile)
    if contract is None:
        return False
    current_contract = _read_json(Path(paper_root) / "medical_reporting_contract.json")
    if current_contract != contract:
        return True
    registry_payload = _read_json(Path(paper_root) / "display_registry.json")
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        return True
    if not any(
        isinstance(item, dict) and _non_empty_text(item.get("requirement_key")) == TRANSPORTABILITY_REQUIREMENT_KEY
        for item in displays
    ):
        return True
    if not (Path(paper_root) / TRANSPORTABILITY_INPUT_FILENAME).exists():
        return True
    return False


def transportability_governance_display_inputs_need_refresh(*, paper_root: Path) -> bool:
    return not _current_transportability_payload_is_substantive(paper_root=paper_root)
