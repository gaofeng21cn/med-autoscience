from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import gate_clearing_batch_execution
from med_autoscience.controllers import gate_clearing_batch_submission
from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers.gate_clearing_batch_parts.io_utils import non_empty_text
from med_autoscience.profiles import WorkspaceProfile


def append_delivery_sync_after_submission_refresh(
    *,
    unit_results: list[dict[str, Any]],
    execution_summary: dict[str, int],
    study_delivery_status: str,
    selected_work_unit_id: str | None = None,
    paper_root: Path,
    profile: WorkspaceProfile,
    sync_submission_minimal_delivery: Callable[..., dict[str, Any]],
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    settle_window_ns: int,
    clock_snapshot: Callable[[], tuple[int, str]],
) -> None:
    create_submission_unit_result = next(
        (
            item
            for item in unit_results
            if non_empty_text(item.get("unit_id")) == "create_submission_minimal_package"
        ),
        None,
    )
    submission_minimal_refreshed = (
        create_submission_unit_result is not None
        and not gate_clearing_batch_execution.unit_status_blocks_dependents(
            non_empty_text(create_submission_unit_result.get("status"))
        )
    )
    authority_sync_closure = selected_work_unit_id == "submission_authority_sync_closure"
    if not submission_minimal_refreshed or not (study_delivery_status.startswith("stale") or authority_sync_closure):
        return

    embedded_delivery_sync = gate_clearing_batch_execution.reuse_embedded_submission_delivery_sync(
        create_submission_result=create_submission_unit_result.get("result")
        if isinstance(create_submission_unit_result, dict)
        else None,
    )
    if embedded_delivery_sync is not None:
        _append_embedded_delivery_sync(
            unit_results=unit_results,
            execution_summary=execution_summary,
            embedded_delivery_sync=embedded_delivery_sync,
            paper_root=paper_root,
            path_fingerprints=path_fingerprints,
            settle_window_ns=settle_window_ns,
            clock_snapshot=clock_snapshot,
        )
        return

    _append_sequential_delivery_sync(
        unit_results=unit_results,
        execution_summary=execution_summary,
        paper_root=paper_root,
        profile=profile,
        sync_submission_minimal_delivery=sync_submission_minimal_delivery,
        path_fingerprints=path_fingerprints,
        settle_window_ns=settle_window_ns,
        clock_snapshot=clock_snapshot,
    )


def _append_embedded_delivery_sync(
    *,
    unit_results: list[dict[str, Any]],
    execution_summary: dict[str, int],
    embedded_delivery_sync: dict[str, Any],
    paper_root: Path,
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    settle_window_ns: int,
    clock_snapshot: Callable[[], tuple[int, str]],
) -> None:
    authority_settled, authority_fingerprints = (
        gate_clearing_batch_submission.current_package_authority_settled(
            paper_root=paper_root,
            path_fingerprints=path_fingerprints,
            settle_window_ns=settle_window_ns,
        )
    )
    if authority_settled:
        embedded_delivery_sync["authority_fingerprints"] = authority_fingerprints
        embedded_delivery_sync["settle_window_ns"] = settle_window_ns
        embedded_delivery_sync.update(publication_work_unit_lifecycle.instant_timing(clock=clock_snapshot))
        unit_results.append(embedded_delivery_sync)
    else:
        retry_metadata = gate_clearing_batch_submission.authority_not_settled_retry_metadata(
            authority_fingerprints=authority_fingerprints,
            settle_window_ns=settle_window_ns,
        )
        unit_results.append(
            publication_work_unit_lifecycle.authority_not_settled_sync_unit_item(
                authority_fingerprints=authority_fingerprints,
                settle_window_ns=settle_window_ns,
                retry_metadata=retry_metadata,
                timing=publication_work_unit_lifecycle.instant_timing(clock=clock_snapshot),
                depends_on=["create_submission_minimal_package"],
            )
        )
    execution_summary["sequential_unit_count"] += 1


def _append_sequential_delivery_sync(
    *,
    unit_results: list[dict[str, Any]],
    execution_summary: dict[str, int],
    paper_root: Path,
    profile: WorkspaceProfile,
    sync_submission_minimal_delivery: Callable[..., dict[str, Any]],
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    settle_window_ns: int,
    clock_snapshot: Callable[[], tuple[int, str]],
) -> None:
    started_ns, started_at = clock_snapshot()
    try:
        result = gate_clearing_batch_submission.sync_submission_minimal_delivery_after_settle(
            paper_root=paper_root,
            profile=profile,
            sync_submission_minimal_delivery=sync_submission_minimal_delivery,
            path_fingerprints=path_fingerprints,
            settle_window_ns=settle_window_ns,
        )
        finished_ns, finished_at = clock_snapshot()
        timing = {
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
        }
        unit_results.append(
            publication_work_unit_lifecycle.submission_delivery_sync_unit_item(
                result=result,
                timing=timing,
                depends_on=["create_submission_minimal_package"],
            )
        )
    except Exception as exc:
        finished_ns, finished_at = clock_snapshot()
        unit_results.append(
            {
                "unit_id": "sync_submission_minimal_delivery",
                "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
                "parallel_safe": False,
                "status": "failed",
                "error": str(exc),
                "depends_on": ["create_submission_minimal_package"],
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
            }
        )
    execution_summary["sequential_unit_count"] += 1
