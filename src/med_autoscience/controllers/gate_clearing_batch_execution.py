from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import publication_work_unit_lifecycle


@dataclass(frozen=True)
class GateClearingRepairUnit:
    unit_id: str
    label: str
    parallel_safe: bool
    run: Callable[[], dict[str, Any]]
    depends_on: tuple[str, ...] = ()


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def latest_unit_result(latest_batch: dict[str, Any], *, unit_id: str) -> dict[str, Any] | None:
    for item in (latest_batch.get("unit_results") or []):
        if not isinstance(item, dict):
            continue
        if _non_empty_text(item.get("unit_id")) != unit_id:
            continue
        return item
    return None


def latest_unit_status(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    item = latest_unit_result(latest_batch, unit_id=unit_id)
    if item is None:
        return None
    return _non_empty_text(item.get("status"))


def unit_status_is_success(status: str | None) -> bool:
    return status not in {
        None,
        "failed",
        "missing",
        "skipped_failed_dependency",
        "skipped_matching_unit_fingerprint",
        "skipped_authority_not_settled",
    }


def latest_unit_success_status(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    item = latest_unit_result(latest_batch, unit_id=unit_id)
    if item is None:
        return None
    last_success_status = _non_empty_text(item.get("last_success_status"))
    if last_success_status is not None:
        return last_success_status
    status = _non_empty_text(item.get("status"))
    if unit_status_is_success(status):
        return status
    return None


def latest_unit_fingerprint(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    payload = latest_batch.get("unit_fingerprints")
    if not isinstance(payload, dict):
        return None
    return _non_empty_text(payload.get(unit_id))


def can_skip_repair_unit(
    latest_batch: dict[str, Any],
    *,
    unit_id: str,
    unit_fingerprint: str | None,
) -> bool:
    if unit_fingerprint is None:
        return False
    previous_fingerprint = latest_unit_fingerprint(latest_batch, unit_id=unit_id)
    if previous_fingerprint != unit_fingerprint:
        return False
    return latest_unit_success_status(latest_batch, unit_id=unit_id) is not None


def unit_status_blocks_dependents(status: str | None) -> bool:
    return status in {"failed", "missing", "skipped_failed_dependency", "skipped_authority_not_settled"}


def existing_dependency_ids(
    repair_units: list[GateClearingRepairUnit],
    *candidate_unit_ids: str,
) -> tuple[str, ...]:
    existing_ids = {unit.unit_id for unit in repair_units}
    return tuple(unit_id for unit_id in candidate_unit_ids if unit_id in existing_ids)


def run_repair_unit(
    *,
    unit: GateClearingRepairUnit,
    latest_batch: dict[str, Any],
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: Any,
    repair_unit_fingerprint: Callable[..., str | None],
    clock_snapshot: Callable[[], tuple[int, str]],
) -> tuple[dict[str, Any], str | None]:
    unit_fingerprint = repair_unit_fingerprint(
        unit_id=unit.unit_id,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    item: dict[str, Any]
    if can_skip_repair_unit(latest_batch, unit_id=unit.unit_id, unit_fingerprint=unit_fingerprint):
        previous_status = latest_unit_status(latest_batch, unit_id=unit.unit_id)
        last_success_status = latest_unit_success_status(latest_batch, unit_id=unit.unit_id)
        item = {
            "unit_id": unit.unit_id,
            "label": unit.label,
            "parallel_safe": unit.parallel_safe,
            "status": "skipped_matching_unit_fingerprint",
            "previous_status": previous_status,
            **publication_work_unit_lifecycle.instant_timing(clock=clock_snapshot),
        }
        if last_success_status is not None:
            item["last_success_status"] = last_success_status
    else:
        started_ns, started_at = clock_snapshot()
        try:
            result = unit.run()
            finished_ns, finished_at = clock_snapshot()
            timing = {
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
            }
            item = {
                "unit_id": unit.unit_id,
                "label": unit.label,
                "parallel_safe": unit.parallel_safe,
                "status": str(result.get("status") or "ok"),
                "result": result,
                **timing,
            }
            publication_work_unit_lifecycle.copy_step_surface_metadata(item, result)
            if unit_status_is_success(_non_empty_text(item.get("status"))):
                item["last_success_status"] = item["status"]
        except Exception as exc:
            item = {
                "unit_id": unit.unit_id,
                "label": unit.label,
                "parallel_safe": unit.parallel_safe,
                "status": "failed",
                "error": str(exc),
            }
            finished_ns, finished_at = clock_snapshot()
            item.update(
                {
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
                }
            )
    if unit.depends_on:
        item["depends_on"] = list(unit.depends_on)
    if unit_fingerprint is not None:
        item["fingerprint"] = unit_fingerprint
    return item, unit_fingerprint


def execute_repair_units(
    *,
    repair_units: list[GateClearingRepairUnit],
    latest_batch: dict[str, Any],
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: Any,
    repair_unit_fingerprint: Callable[..., str | None],
    clock_snapshot: Callable[[], tuple[int, str]],
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, int]]:
    unit_results_by_id: dict[str, dict[str, Any]] = {}
    unit_fingerprints: dict[str, str] = {}
    execution_summary = {
        "parallel_wave_count": 0,
        "parallel_unit_count": 0,
        "sequential_unit_count": 0,
        "skipped_dependency_unit_count": 0,
    }
    pending_units = list(repair_units)
    while pending_units:
        remaining_units: list[GateClearingRepairUnit] = []
        ready_parallel_units: list[GateClearingRepairUnit] = []
        ready_sequential_units: list[GateClearingRepairUnit] = []
        for unit in pending_units:
            dependency_statuses = {
                dependency_id: _non_empty_text((unit_results_by_id.get(dependency_id) or {}).get("status"))
                for dependency_id in unit.depends_on
                if dependency_id in unit_results_by_id
            }
            failed_dependencies = [
                dependency_id
                for dependency_id, status in dependency_statuses.items()
                if unit_status_blocks_dependents(status)
            ]
            if failed_dependencies:
                unit_results_by_id[unit.unit_id] = {
                    "unit_id": unit.unit_id,
                    "label": unit.label,
                    "parallel_safe": unit.parallel_safe,
                    "status": "skipped_failed_dependency",
                    "failed_dependencies": failed_dependencies,
                    "depends_on": list(unit.depends_on),
                    **publication_work_unit_lifecycle.instant_timing(clock=clock_snapshot),
                }
                execution_summary["skipped_dependency_unit_count"] += 1
                continue
            unresolved_dependencies = [
                dependency_id for dependency_id in unit.depends_on if dependency_id not in unit_results_by_id
            ]
            if unresolved_dependencies:
                remaining_units.append(unit)
                continue
            if unit.parallel_safe:
                ready_parallel_units.append(unit)
            else:
                ready_sequential_units.append(unit)
        if not ready_parallel_units and not ready_sequential_units:
            if not remaining_units:
                break
            raise RuntimeError("gate-clearing batch repair dependency graph could not be resolved")
        if ready_parallel_units:
            execution_summary["parallel_wave_count"] += 1
            execution_summary["parallel_unit_count"] += len(ready_parallel_units)
            with ThreadPoolExecutor(max_workers=len(ready_parallel_units)) as executor:
                futures = {
                    unit.unit_id: executor.submit(
                        run_repair_unit,
                        unit=unit,
                        latest_batch=latest_batch,
                        paper_root=paper_root,
                        gate_report=gate_report,
                        profile=profile,
                        repair_unit_fingerprint=repair_unit_fingerprint,
                        clock_snapshot=clock_snapshot,
                    )
                    for unit in ready_parallel_units
                }
                for unit in ready_parallel_units:
                    item, unit_fingerprint = futures[unit.unit_id].result()
                    unit_results_by_id[unit.unit_id] = item
                    if unit_fingerprint is not None:
                        unit_fingerprints[unit.unit_id] = unit_fingerprint
        for unit in ready_sequential_units:
            item, unit_fingerprint = run_repair_unit(
                unit=unit,
                latest_batch=latest_batch,
                paper_root=paper_root,
                gate_report=gate_report,
                profile=profile,
                repair_unit_fingerprint=repair_unit_fingerprint,
                clock_snapshot=clock_snapshot,
            )
            unit_results_by_id[unit.unit_id] = item
            if unit_fingerprint is not None:
                unit_fingerprints[unit.unit_id] = unit_fingerprint
            execution_summary["sequential_unit_count"] += 1
        pending_units = remaining_units
    unit_results = [
        unit_results_by_id[unit.unit_id]
        for unit in repair_units
        if unit.unit_id in unit_results_by_id
    ]
    return unit_results, unit_fingerprints, execution_summary


def reuse_embedded_submission_delivery_sync(
    *,
    create_submission_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(create_submission_result, dict):
        return None
    delivery_sync = create_submission_result.get("delivery_sync")
    if not isinstance(delivery_sync, dict) or not delivery_sync:
        return None
    return {
        "unit_id": "sync_submission_minimal_delivery",
        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
        "parallel_safe": False,
        "status": _non_empty_text(delivery_sync.get("status")) or "updated",
        "result": delivery_sync,
        "reused_embedded_delivery_sync": True,
        "depends_on": ["create_submission_minimal_package"],
    }
