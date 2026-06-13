from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from ..domain_action_request_materializer import CONSUMER_LATEST_RELATIVE_PATH


EXECUTION_RELATIVE_ROOT = Path("artifacts/supervision/consumer/default_executor_execution")
EXECUTION_LATEST_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "latest.json"
EXECUTION_HISTORY_RELATIVE_PATH = EXECUTION_RELATIVE_ROOT / "history.jsonl"
EXECUTION_LEDGER_LIMIT = 80


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def consumer_latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / CONSUMER_LATEST_RELATIVE_PATH


def execution_latest_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return study_root(profile, study_id) / EXECUTION_LATEST_RELATIVE_PATH


def execution_history_path(profile: WorkspaceProfile, study_id: str) -> Path:
    return study_root(profile, study_id) / EXECUTION_HISTORY_RELATIVE_PATH


def merged_execution_ledger(
    *,
    previous_payload: Mapping[str, Any] | None,
    study_executions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for execution in [
        *_mapping_list(_mapping(previous_payload).get("execution_ledger")),
        *_mapping_list(_mapping(previous_payload).get("executions")),
        *study_executions,
    ]:
        merged[_execution_identity(execution)] = dict(execution)
    return list(merged.values())[-EXECUTION_LEDGER_LIMIT:]


def _execution_identity(execution: Mapping[str, Any]) -> str:
    return (
        _text(execution.get("execution_id"))
        or "::".join(
            item
            for item in (
                _text(execution.get("action_type")),
                _text(execution.get("idempotency_key")),
                _text(execution.get("generated_at")),
            )
            if item
        )
        or json.dumps(dict(execution), ensure_ascii=False, sort_keys=True)
    )


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "EXECUTION_HISTORY_RELATIVE_PATH",
    "EXECUTION_LATEST_RELATIVE_PATH",
    "EXECUTION_LEDGER_LIMIT",
    "EXECUTION_RELATIVE_ROOT",
    "append_json_line",
    "consumer_latest_path",
    "execution_history_path",
    "execution_latest_path",
    "merged_execution_ledger",
    "read_json_object",
    "study_root",
    "write_json",
]
