from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = 1
STABLE_PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH = Path(
    "artifacts/controller/publication_work_unit_lifecycle/latest.json"
)
_BLOCKING_STATUSES = frozenset({"failed", "missing", "skipped_failed_dependency", "skipped_authority_not_settled"})
STEP_SURFACE_METADATA_KEYS = (
    "authority_fingerprints",
    "settle_window_ns",
    "retry_reason",
    "retry_after",
    "retry_after_seconds",
)


def clock_snapshot() -> tuple[int, str]:
    return time.time_ns(), datetime.now(timezone.utc).isoformat()


def duration_seconds(started_ns: int, finished_ns: int) -> float:
    return round(max(0, finished_ns - started_ns) / 1_000_000_000, 9)


def instant_timing(*, clock: Callable[[], tuple[int, str]]) -> dict[str, Any]:
    started_ns, started_at = clock()
    finished_ns, finished_at = clock()
    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds(started_ns, finished_ns),
    }


def timed_step(
    *,
    clock: Callable[[], tuple[int, str]],
    run: Callable[[], dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    started_ns, started_at = clock()
    try:
        result = run()
    finally:
        finished_ns, finished_at = clock()
    timing = {
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds(started_ns, finished_ns),
    }
    return result, timing


def copy_step_surface_metadata(item: dict[str, Any], result: dict[str, Any]) -> None:
    for key in STEP_SURFACE_METADATA_KEYS:
        if key in result:
            item[key] = result[key]


def submission_delivery_sync_unit_item(
    *,
    result: dict[str, Any],
    timing: dict[str, Any],
    depends_on: list[str],
) -> dict[str, Any]:
    item = {
        "unit_id": "sync_submission_minimal_delivery",
        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
        "parallel_safe": False,
        "status": str(result.get("status") or "updated"),
        "result": result,
        "authority_fingerprints": result.get("authority_fingerprints"),
        "settle_window_ns": result.get("settle_window_ns"),
        "depends_on": depends_on,
        **timing,
    }
    copy_step_surface_metadata(item, result)
    return item


def authority_not_settled_sync_unit_item(
    *,
    authority_fingerprints: list[dict[str, Any]],
    settle_window_ns: int,
    retry_metadata: dict[str, Any],
    timing: dict[str, Any],
    depends_on: list[str],
) -> dict[str, Any]:
    return {
        "unit_id": "sync_submission_minimal_delivery",
        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
        "parallel_safe": False,
        "status": "skipped_authority_not_settled",
        "authority_fingerprints": authority_fingerprints,
        "settle_window_ns": settle_window_ns,
        **retry_metadata,
        "depends_on": depends_on,
        **timing,
    }


def gate_replay_step(*, gate_replay: dict[str, Any], timing: dict[str, Any]) -> dict[str, Any]:
    return {
        "step_id": "publication_gate_replay",
        "status": str(gate_replay.get("status") or "unknown"),
        "result": gate_replay,
        **timing,
    }


def stable_publication_work_unit_lifecycle_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH


def retry_metadata_from_unit_results(unit_results: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in unit_results:
        if str(item.get("status") or "").strip() != "skipped_authority_not_settled":
            continue
        reason = str(item.get("retry_reason") or "authority_not_settled").strip()
        retry: dict[str, Any] = {"reason": reason}
        retry_after = item.get("retry_after")
        retry_after_seconds = item.get("retry_after_seconds")
        if isinstance(retry_after, str) and retry_after.strip():
            retry["retry_after"] = retry_after.strip()
        if isinstance(retry_after_seconds, (int, float)):
            retry["retry_after_seconds"] = retry_after_seconds
        return retry
    return None


def classify_lifecycle_status(
    *,
    selected_work_unit: dict[str, Any] | None,
    unit_results: list[dict[str, Any]],
    gate_replay: dict[str, Any],
) -> str:
    if selected_work_unit is None:
        return "skipped"
    if not unit_results:
        return "skipped"
    statuses = {str(item.get("status") or "").strip() for item in unit_results}
    if statuses & _BLOCKING_STATUSES:
        return "blocked"
    gate_status = str(gate_replay.get("status") or "").strip()
    if gate_status == "clear" or gate_replay.get("allow_write") is True:
        return "done"
    return "blocked"


def build_lifecycle_record(
    *,
    source_eval_id: str,
    study_id: str,
    quest_id: str,
    selected_work_unit: dict[str, Any] | None,
    unit_results: list[dict[str, Any]],
    gate_replay: dict[str, Any],
) -> dict[str, Any]:
    retry = retry_metadata_from_unit_results(unit_results)
    status = classify_lifecycle_status(
        selected_work_unit=selected_work_unit,
        unit_results=unit_results,
        gate_replay=gate_replay,
    )
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source_eval_id": source_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "status": status,
        "work_unit": selected_work_unit,
        "unit_statuses": [
            {
                "unit_id": item.get("unit_id"),
                "status": item.get("status"),
            }
            for item in unit_results
        ],
        "gate_replay_status": gate_replay.get("status"),
    }
    if retry is not None:
        record["retry"] = retry
    return record


def enrich_selected_work_unit(
    *,
    selected_work_unit: dict[str, Any] | None,
    lifecycle_record: dict[str, Any],
) -> dict[str, Any] | None:
    if selected_work_unit is None:
        return None
    enriched = dict(selected_work_unit)
    status = str(lifecycle_record.get("status") or "").strip()
    enriched["lifecycle_status"] = status
    enriched["status"] = status
    enriched["lifecycle"] = {"status": status}
    retry = lifecycle_record.get("retry")
    if isinstance(retry, dict):
        enriched["retry"] = retry
        enriched["lifecycle"]["retry"] = retry
    return enriched
