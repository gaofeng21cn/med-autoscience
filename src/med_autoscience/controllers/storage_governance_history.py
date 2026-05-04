from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "storage_governance_history_projection"
HISTORY_RELATIVE_PATH = Path("artifacts/storage_governance/history.jsonl")
DEFAULT_HISTORY_LIMIT = 90


def build_storage_governance_history_projection(
    *,
    workspaces: Iterable[Mapping[str, Any]],
    summary: Mapping[str, Any],
    source_totals: Mapping[str, Any],
    limit: int = DEFAULT_HISTORY_LIMIT,
) -> dict[str, Any]:
    history_entries = _bounded_history_entries(workspaces, limit=limit)
    recordable_entry = _recordable_entry(summary=summary, source_totals=source_totals)
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "mutation_policy": _mutation_policy(),
        "history_path": str(HISTORY_RELATIVE_PATH),
        "history_entries": history_entries,
        "previous_snapshot": history_entries[-1] if history_entries else None,
        "recordable_entry": recordable_entry,
    }


def _bounded_history_entries(
    workspaces: Iterable[Mapping[str, Any]],
    *,
    limit: int,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for workspace in workspaces:
        workspace_root = _text(workspace.get("workspace_root"))
        if not workspace_root:
            continue
        entries.extend(_read_history_entries(Path(workspace_root) / HISTORY_RELATIVE_PATH))
    return sorted(entries, key=lambda item: _text(item.get("observed_at")))[-limit:]


def _read_history_entries(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return entries
    for line in lines:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        entry = _history_entry(payload)
        if entry is not None:
            entries.append(entry)
    return entries


def _history_entry(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, Mapping):
        return None
    observed_at = _text(payload.get("observed_at"))
    total_bytes = _int(payload.get("total_bytes"))
    if not observed_at:
        return None
    entry = {
        "observed_at": observed_at,
        "total_bytes": total_bytes,
    }
    source_totals = _source_totals_snapshot(_mapping(payload.get("source_totals")))
    if source_totals:
        entry["source_totals"] = source_totals
    return entry


def _recordable_entry(
    *,
    summary: Mapping[str, Any],
    source_totals: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "observed_at": "",
        "total_bytes": _int(summary.get("total_bytes")),
        "classified_bytes": _int(summary.get("classified_bytes")),
        "statistical_bytes": _int(summary.get("statistical_bytes")),
        "source_totals": _source_totals_snapshot(source_totals),
    }


def _source_totals_snapshot(source_totals: Mapping[str, Any]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for source_bucket, totals_value in source_totals.items():
        totals = _mapping(totals_value)
        bytes_count = _int(totals.get("bytes"))
        file_count = _int(totals.get("file_count"))
        if bytes_count <= 0 and file_count <= 0:
            continue
        snapshot[str(source_bucket)] = {
            "bytes": bytes_count,
            "file_count": file_count,
        }
    return snapshot


def _mutation_policy() -> dict[str, Any]:
    return {
        "read_only": True,
        "writes_workspace": False,
        "recordable_entry_only": True,
        "history_append_performed": False,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "DEFAULT_HISTORY_LIMIT",
    "HISTORY_RELATIVE_PATH",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_storage_governance_history_projection",
]
