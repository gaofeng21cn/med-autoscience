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


def run_validation(*, quest_root: Path) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    analysis_path = resolved_quest_root / "paper" / "medical_analysis_contract.json"
    reporting_path = resolved_quest_root / "paper" / "medical_reporting_contract.json"
    blockers: list[str] = []
    if not analysis_path.exists():
        blockers.append("missing_medical_analysis_contract")
    if not reporting_path.exists():
        blockers.append("missing_medical_reporting_contract")

    report = {
        "status": "blocked" if blockers else "clear",
        "recorded_at": _utc_now(),
        "quest_root": str(resolved_quest_root),
        "blockers": blockers,
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
