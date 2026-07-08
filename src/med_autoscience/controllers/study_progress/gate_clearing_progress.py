from __future__ import annotations

from pathlib import Path
from typing import Any

from .shared import _display_text, _mapping_copy, _non_empty_text, _normalize_timestamp, _time_label


def append_progress_signal(
    *,
    signals: list[dict[str, Any]],
    timestamp: object,
    source: str,
    summary: object,
) -> bool:
    normalized_timestamp = _normalize_timestamp(timestamp)
    rendered_summary = _display_text(summary)
    if normalized_timestamp is None or rendered_summary is None:
        return False
    signals.append(
        {
            "timestamp": normalized_timestamp,
            "time_label": _time_label(normalized_timestamp),
            "source": source,
            "summary": rendered_summary,
        }
    )
    return True


def append_gate_clearing_batch_progress_signal(
    *,
    signals: list[dict[str, Any]],
    gate_clearing_batch_payload: dict[str, Any] | None,
    gate_clearing_batch_path: Path | None,
    publication_eval_payload: dict[str, Any] | None,
) -> None:
    if not isinstance(gate_clearing_batch_payload, dict):
        return
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    source_eval_id = _non_empty_text(gate_clearing_batch_payload.get("source_eval_id"))
    if current_eval_id is not None and source_eval_id is not None and current_eval_id != source_eval_id:
        return
    gate_replay = _mapping_copy(gate_clearing_batch_payload.get("gate_replay"))
    gate_replay_step = _mapping_copy(gate_clearing_batch_payload.get("gate_replay_step"))
    gate_replay_status = _non_empty_text(gate_replay_step.get("status")) or _non_empty_text(gate_replay.get("status"))
    if _non_empty_text(gate_clearing_batch_payload.get("status")) != "executed" and gate_replay_status is None:
        return
    blockers = [_non_empty_text(item) for item in (gate_replay.get("blockers") or []) if _non_empty_text(item)]
    if gate_replay_status == "clear":
        summary = "gate-clearing batch closed with publication gate replay clear."
    elif blockers:
        summary = f"gate-clearing batch closed; gate replay still has {len(blockers)} blocker(s)."
    else:
        summary = "gate-clearing batch closed and wrote a gate replay result."
    appended = append_progress_signal(
        signals=signals,
        timestamp=(
            _non_empty_text(gate_replay_step.get("finished_at"))
            or _non_empty_text(gate_clearing_batch_payload.get("finished_at"))
            or _non_empty_text(gate_clearing_batch_payload.get("generated_at"))
            or _non_empty_text(gate_clearing_batch_payload.get("emitted_at"))
            or _non_empty_text(gate_clearing_batch_payload.get("recorded_at"))
        ),
        source="gate_clearing_batch",
        summary=summary,
    )
    if appended:
        signals[-1]["artifact_path"] = str(gate_clearing_batch_path) if gate_clearing_batch_path is not None else None
