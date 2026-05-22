from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TOP_LEVEL_BLOCKERS = frozenset(
    {
        "invalid_analysis_history_residue_present",
        "manuscript_story_surface_delta_missing",
    }
)


def selected_work_unit_id_from_gate_result(
    gate_clearing_result: Mapping[str, Any],
    *,
    upstream_work_unit_ids: frozenset[str],
) -> str | None:
    explicit = _selected_work_unit_id_for_key(gate_clearing_result, key="explicit_publication_work_unit")
    if explicit in upstream_work_unit_ids:
        return explicit
    for key in ("selected_publication_work_unit", "current_publication_work_unit", "explicit_publication_work_unit"):
        text = _selected_work_unit_id_for_key(gate_clearing_result, key=key)
        if text:
            return text
    for item in gate_clearing_result.get("unit_results") or []:
        if not isinstance(item, Mapping):
            continue
        text = _non_empty_text(item.get("unit_id"))
        if text in upstream_work_unit_ids:
            return text
    return None


def merge_upstream_unit_result(
    *,
    gate_clearing_result: Mapping[str, Any],
    upstream_unit_result: Mapping[str, Any] | None,
) -> dict[str, Any]:
    result = dict(gate_clearing_result)
    if not isinstance(upstream_unit_result, Mapping):
        return result
    unit_results = [
        dict(item)
        for item in (result.get("unit_results") or [])
        if isinstance(item, Mapping)
    ]
    unit_id = _non_empty_text(upstream_unit_result.get("unit_id"))
    if unit_id and not any(_non_empty_text(item.get("unit_id")) == unit_id for item in unit_results):
        unit_results.insert(0, dict(upstream_unit_result))
    result["unit_results"] = unit_results
    return result


def blocked_repair_execution_reason(repair_execution_evidence: Mapping[str, Any]) -> str | None:
    if _non_empty_text(repair_execution_evidence.get("status")) != "blocked":
        return None
    for blocker in repair_execution_evidence.get("blockers") or ():
        text = _non_empty_text(blocker)
        if text in TOP_LEVEL_BLOCKERS:
            return text
    return None


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _selected_work_unit_id_for_key(gate_clearing_result: Mapping[str, Any], *, key: str) -> str | None:
    payload = gate_clearing_result.get(key)
    if isinstance(payload, Mapping):
        return _non_empty_text(payload.get("unit_id"))
    return None


__all__ = [
    "blocked_repair_execution_reason",
    "merge_upstream_unit_result",
    "selected_work_unit_id_from_gate_result",
]
