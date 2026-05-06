from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any


def workspace_storage_audit_projection_payload(
    *,
    report: Mapping[str, Any],
    report_path: Path,
    latest_report_path: Path,
) -> str:
    categories = _mapping(report.get("categories"))
    runtime = _mapping(categories.get("runtime"))
    studies = runtime.get("studies")
    compact_studies: list[dict[str, Any]] = []
    if isinstance(studies, list):
        for item in studies:
            if not isinstance(item, Mapping):
                continue
            runtime_item = _mapping(item.get("runtime"))
            quest_runtime = _mapping(item.get("quest_runtime"))
            compaction = _mapping(item.get("restore_proof_compaction"))
            compact_studies.append(
                {
                    "study_id": _text(item.get("study_id")),
                    "quest_id": _text(item.get("quest_id")),
                    "quest_root": _text(item.get("quest_root")),
                    "status": _text(item.get("status")),
                    "quest_runtime_status": _text(quest_runtime.get("status")),
                    "active_run_id": _text(quest_runtime.get("active_run_id")),
                    "candidate_action": _text(runtime_item.get("candidate_action")),
                    "estimated_release_bytes": as_int(runtime_item.get("estimated_release_bytes")),
                    "actual_release_bytes": as_int(runtime_item.get("actual_release_bytes")),
                    "restore_proof_status": _text(compaction.get("status")),
                    "restore_proof_path": _text(compaction.get("restore_proof_path")),
                }
            )
    projection = {
        "schema_version": report.get("schema_version"),
        "recorded_at": report.get("recorded_at"),
        "workspace_root": report.get("workspace_root"),
        "mode": report.get("mode"),
        "summary": _mapping(report.get("summary")),
        "selection": _mapping(report.get("selection")),
        "runtime_projection": {
            "category": runtime.get("category"),
            "candidate_action": runtime.get("candidate_action"),
            "bytes": runtime.get("bytes"),
            "estimated_release_bytes": runtime.get("estimated_release_bytes"),
            "actual_release_bytes": runtime.get("actual_release_bytes"),
            "study_count": len(compact_studies),
            "studies": compact_studies,
        },
        "source_report_path": str(Path(report_path).expanduser().resolve()),
        "latest_report_path": str(Path(latest_report_path).expanduser().resolve()),
        "projection_policy": "compact_sqlite_index_full_report_in_file_authority",
    }
    return json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def as_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = ["as_int", "workspace_storage_audit_projection_payload"]
