from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _validate_contract_status(
    *,
    contract_path: Path,
    missing_blocker: str,
    invalid_blocker: str,
    unsupported_blocker: str,
    unresolved_blocker: str,
) -> tuple[str | None, str | None]:
    if not contract_path.exists():
        return None, missing_blocker
    try:
        payload = _read_json_dict(contract_path)
    except (json.JSONDecodeError, OSError, ValueError):
        return None, invalid_blocker
    status = str(payload.get("status") or "").strip()
    if status == "resolved":
        return status, None
    if status == "unsupported":
        return status, unsupported_blocker
    return status or None, unresolved_blocker


def _normalize_display_shell_plan(reporting_contract: dict[str, Any]) -> list[dict[str, str]]:
    plan = reporting_contract.get("display_shell_plan")
    normalized: list[dict[str, str]] = []
    if isinstance(plan, list):
        for item in plan:
            if not isinstance(item, dict):
                continue
            display_id = str(item.get("display_id") or "").strip()
            display_kind = str(item.get("display_kind") or "").strip()
            requirement_key = str(item.get("requirement_key") or "").strip()
            if display_id and display_kind and requirement_key:
                normalized.append(
                    {
                        "display_id": display_id,
                        "display_kind": display_kind,
                        "requirement_key": requirement_key,
                    }
                )
    return normalized


def run_validation(*, quest_root: Path) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    analysis_path = resolved_quest_root / "paper" / "medical_analysis_contract.json"
    reporting_path = resolved_quest_root / "paper" / "medical_reporting_contract.json"
    blockers: list[str] = []
    analysis_status, analysis_blocker = _validate_contract_status(
        contract_path=analysis_path,
        missing_blocker="missing_medical_analysis_contract",
        invalid_blocker="invalid_medical_analysis_contract",
        unsupported_blocker="unsupported_medical_analysis_contract",
        unresolved_blocker="unresolved_medical_analysis_contract",
    )
    reporting_status, reporting_blocker = _validate_contract_status(
        contract_path=reporting_path,
        missing_blocker="missing_medical_reporting_contract",
        invalid_blocker="invalid_medical_reporting_contract",
        unsupported_blocker="unsupported_medical_reporting_contract",
        unresolved_blocker="unresolved_medical_reporting_contract",
    )
    if analysis_blocker is not None:
        blockers.append(analysis_blocker)
    if reporting_blocker is not None:
        blockers.append(reporting_blocker)

    if reporting_blocker is None:
        reporting_payload = _read_json_dict(reporting_path)
        display_shell_plan = _normalize_display_shell_plan(reporting_payload)
        if bool(reporting_payload.get("display_registry_required", bool(display_shell_plan))):
            display_registry_path = resolved_quest_root / "paper" / "display_registry.json"
            if not display_registry_path.exists():
                blockers.append("missing_display_registry")
            for item in display_shell_plan:
                if item["display_kind"] == "figure":
                    shell_path = resolved_quest_root / "paper" / "figures" / f"{item['display_id']}.shell.json"
                else:
                    shell_path = resolved_quest_root / "paper" / "tables" / f"{item['display_id']}.shell.json"
                if not shell_path.exists():
                    blockers.append(f"missing_{item['display_id'].lower()}_shell")

    report = {
        "status": "blocked" if blockers else "clear",
        "recorded_at": _utc_now(),
        "quest_root": str(resolved_quest_root),
        "blockers": blockers,
        "contract_statuses": {
            "medical_analysis_contract": analysis_status,
            "medical_reporting_contract": reporting_status,
        },
        "checked_paths": {
            "medical_analysis_contract_path": str(analysis_path),
            "medical_reporting_contract_path": str(reporting_path),
        },
    }
    _write_json(
        resolved_quest_root / "artifacts" / "reports" / "startup" / "hydration_validation_report.json",
        report,
    )
    return report
