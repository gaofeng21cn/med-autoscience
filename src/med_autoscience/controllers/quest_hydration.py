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


def run_hydration(*, quest_root: Path, hydration_payload: dict[str, object]) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    medical_analysis_contract = _require_dict(hydration_payload, "medical_analysis_contract")
    medical_reporting_contract = _require_dict(hydration_payload, "medical_reporting_contract")
    entry_state_summary = _require_str(hydration_payload, "entry_state_summary")

    analysis_path = resolved_quest_root / "paper" / "medical_analysis_contract.json"
    reporting_path = resolved_quest_root / "paper" / "medical_reporting_contract.json"
    report_path = resolved_quest_root / "artifacts" / "reports" / "startup" / "hydration_report.json"

    _write_json(analysis_path, medical_analysis_contract)
    _write_json(reporting_path, medical_reporting_contract)
    report = {
        "status": "hydrated",
        "recorded_at": _utc_now(),
        "quest_root": str(resolved_quest_root),
        "entry_state_summary": entry_state_summary,
        "written_files": [
            str(analysis_path),
            str(reporting_path),
        ],
    }
    _write_json(report_path, report)
    report["report_path"] = str(report_path)
    return report
