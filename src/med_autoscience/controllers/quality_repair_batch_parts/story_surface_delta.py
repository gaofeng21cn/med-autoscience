from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


BLOCKED_REASON = "manuscript_story_surface_delta_missing"
WORK_UNIT_ID = "manuscript_story_repair"


def blocker_supersedes_lifecycle(
    *,
    study_root: Path,
    lifecycle: Mapping[str, Any],
    batch_path: Path,
) -> bool:
    work_unit = lifecycle.get("work_unit")
    if not isinstance(work_unit, Mapping):
        return False
    if _non_empty_text(work_unit.get("unit_id")) != WORK_UNIT_ID:
        return False
    source_eval_id = _non_empty_text(lifecycle.get("source_eval_id"))
    if source_eval_id is None:
        return False
    batch = _read_json_object(batch_path)
    if _non_empty_text(batch.get("source_eval_id")) != source_eval_id:
        return False
    if _non_empty_text(batch.get("next_owner")) != "write":
        return False
    if _non_empty_text(batch.get("blocked_reason")) == BLOCKED_REASON:
        return True
    evidence = batch.get("repair_execution_evidence")
    if isinstance(evidence, Mapping) and BLOCKED_REASON in _string_set(evidence.get("blockers")):
        return True
    repair_evidence = _read_json_object(
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "repair_execution_evidence"
        / "latest.json"
    )
    return BLOCKED_REASON in _string_set(repair_evidence.get("blockers"))


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        item = value.strip()
        return {item} if item else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _non_empty_text(item)) is not None}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["BLOCKED_REASON", "WORK_UNIT_ID", "blocker_supersedes_lifecycle"]

