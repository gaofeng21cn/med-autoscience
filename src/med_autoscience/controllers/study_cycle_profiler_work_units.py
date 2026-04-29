from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import work_unit_ledger


_TIMESTAMP_FIELDS = ("recorded_at", "generated_at", "emitted_at", "created_at", "updated_at")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_timestamp(value: object) -> datetime | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(timestamp: datetime | None) -> str | None:
    if timestamp is None:
        return None
    return timestamp.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _payload_latest_timestamp(payload: Mapping[str, Any] | None) -> datetime | None:
    if payload is None:
        return None
    for field_name in _TIMESTAMP_FIELDS:
        parsed = _parse_timestamp(payload.get(field_name))
        if parsed is not None:
            return parsed
    return None


def _max_dt(*values: datetime | None) -> datetime | None:
    candidates = [value for value in values if value is not None]
    return max(candidates) if candidates else None


def work_unit_lifecycle_summary(*, study_root: Path) -> dict[str, Any]:
    return work_unit_ledger.lifecycle_summary(study_root=study_root)


def publication_eval_replay_lag(
    *,
    publication_eval_latest: Mapping[str, Any] | None,
    publishability_gate_latest: Mapping[str, Any] | None,
    lifecycle_summary: Mapping[str, Any],
) -> dict[str, Any]:
    publication_eval_latest_at = _payload_latest_timestamp(publication_eval_latest)
    publishability_gate_latest_at = _payload_latest_timestamp(publishability_gate_latest)
    latest_gate_replayed_at = _max_dt(
        *(
            _parse_timestamp(unit.get("latest_gate_replayed_at"))
            for unit in lifecycle_summary.get("units", [])
            if isinstance(unit, Mapping)
        )
    )
    if latest_gate_replayed_at is None:
        return {
            "status": "not_observed",
            "lag_seconds": None,
            "publication_eval_latest_at": _iso(publication_eval_latest_at),
            "latest_gate_replayed_at": None,
            "publishability_gate_latest_at": _iso(publishability_gate_latest_at),
        }
    if publication_eval_latest_at is None:
        return {
            "status": "publication_eval_missing_after_gate_replay",
            "lag_seconds": None,
            "publication_eval_latest_at": None,
            "latest_gate_replayed_at": _iso(latest_gate_replayed_at),
            "publishability_gate_latest_at": _iso(publishability_gate_latest_at),
        }
    lag_seconds = int((latest_gate_replayed_at - publication_eval_latest_at).total_seconds())
    return {
        "status": "stale_after_gate_replay" if lag_seconds > 0 else "current_after_gate_replay",
        "lag_seconds": max(lag_seconds, 0),
        "publication_eval_latest_at": _iso(publication_eval_latest_at),
        "latest_gate_replayed_at": _iso(latest_gate_replayed_at),
        "publishability_gate_latest_at": _iso(publishability_gate_latest_at),
    }
