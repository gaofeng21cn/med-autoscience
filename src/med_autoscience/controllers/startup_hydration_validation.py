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
