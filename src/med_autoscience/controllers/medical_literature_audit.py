from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path

from med_autoscience.adapters.literature import pubmed as pubmed_adapter
from med_autoscience.controllers import literature_hydration as literature_hydration_controller
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def render_audit_markdown(report: dict[str, object]) -> str:
    missing_pmids = report.get("missing_pmids") or []
    lines = [
        "# Medical Literature Audit Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_root: `{report['quest_root']}`",
        f"- gap_report_path: `{report['gap_report_path']}`",
        f"- status: `{report['status']}`",
        f"- action: `{report['action']}`",
        f"- blockers: `{', '.join(report.get('blockers') or ['none'])}`",
        "",
        "## Missing PMIDs",
        "",
    ]
    if missing_pmids:
        lines.extend(f"- `{pmid}`" for pmid in missing_pmids)
    else:
        lines.append("- None")
    lines.append("")
    return "\n".join(lines)


def write_audit_files(quest_root: Path, report: dict[str, object]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="medical_literature_audit",
        timestamp=str(report["generated_at"]),
        report=report,
        markdown=render_audit_markdown(report),
    )


def run_controller(*, quest_root: Path, apply: bool) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    gap_report_path = resolved_quest_root / "paper" / "review" / "reference_gap_report.json"
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
    report = {
        "generated_at": utc_now(),
        "quest_root": str(resolved_quest_root),
        "gap_report_path": str(gap_report_path),
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "action": action,
        "missing_pmids": missing_pmids,
    }
    json_path, md_path = write_audit_files(resolved_quest_root, report)
    return {
        "status": str(report["status"]),
        "blockers": blockers,
        "action": action,
        "quest_root": str(resolved_quest_root),
        "missing_pmids": missing_pmids,
        "report_json": str(json_path),
        "report_markdown": str(md_path),
    }
