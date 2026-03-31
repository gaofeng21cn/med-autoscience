from __future__ import annotations

from pathlib import Path


def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    del apply
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    paper_root = resolved_quest_root / "paper"
    blockers: list[str] = []
    if not (paper_root / "medical_reporting_contract.json").exists():
        blockers.append("missing_medical_reporting_contract")
    if not (paper_root / "cohort_flow.json").exists():
        blockers.append("missing_cohort_flow")
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
