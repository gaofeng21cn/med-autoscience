from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from med_autoscience.adapters.literature import pubmed as pubmed_adapter
from med_autoscience.controllers import literature_hydration as literature_hydration_controller


def _load_gap_report(quest_root: Path) -> dict[str, object]:
    gap_report_path = quest_root / "paper" / "review" / "reference_gap_report.json"
    if not gap_report_path.exists():
        return {}
    payload = json.loads(gap_report_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("reference gap report must be a JSON object")
    return payload


def _missing_pmids(payload: dict[str, object]) -> list[str]:
    value = payload.get("missing_pmids")
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("reference gap report missing_pmids must be a list")
    pmids: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError("reference gap report missing_pmids must contain non-empty strings")
        pmids.append(item.strip())
    return pmids


def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    payload = _load_gap_report(resolved_quest_root)
    missing_pmids = _missing_pmids(payload)
    action = "clear"
    if apply and missing_pmids:
        fetched_records = pubmed_adapter.fetch_pubmed_summary(pmids=missing_pmids)
        literature_hydration_controller.run_literature_hydration(
            quest_root=resolved_quest_root,
            records=[record if isinstance(record, dict) else asdict(record) for record in fetched_records],
        )
        action = "supplemented"
    blockers = ["reference_gaps_present"] if missing_pmids else []
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "action": action,
        "quest_root": str(resolved_quest_root),
        "report_json": None,
        "report_markdown": None,
    }
