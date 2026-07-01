from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from med_autoscience.controllers import gate_clearing_batch_currentness
from med_autoscience.controllers import gate_clearing_batch_package_freshness
from med_autoscience.controllers import gate_clearing_batch_submission
from med_autoscience.controllers import publication_work_unit_lifecycle


def gate_replay_report_payload(
    *,
    gate_replay: dict[str, Any],
    read_json: Callable[[Path], dict[str, Any]],
    non_empty_text: Callable[[object], str | None],
) -> dict[str, Any]:
    report_path_text = non_empty_text(gate_replay.get("report_json")) or non_empty_text(
        gate_replay.get("latest_gate_path")
    )
    if report_path_text is None:
        return gate_replay
    report_payload = read_json(Path(report_path_text).expanduser())
    if not report_payload:
        return gate_replay
    return {**gate_replay, **report_payload}


def freshness_gate_report_payload(
    *,
    gate_report: dict[str, Any],
    gate_replay: dict[str, Any],
    read_json: Callable[[Path], dict[str, Any]],
    non_empty_text: Callable[[object], str | None],
) -> dict[str, Any]:
    replay_report = gate_replay_report_payload(
        gate_replay=gate_replay,
        read_json=read_json,
        non_empty_text=non_empty_text,
    )
    if gate_clearing_batch_submission.study_delivery_status(replay_report) == "current":
        return replay_report
    return gate_report


def closed_batch_current_freshness_proof(
    *,
    latest_batch: dict[str, Any],
    study_root: Path,
    source_eval_id: str,
    read_json: Callable[[Path], dict[str, Any]],
    non_empty_text: Callable[[object], str | None],
    clock_snapshot: Callable[[], tuple[int, str]],
    schema_version: int,
) -> dict[str, Any] | None:
    if isinstance(latest_batch.get("current_package_freshness_proof"), dict):
        proof = dict(latest_batch["current_package_freshness_proof"])
        if gate_clearing_batch_package_freshness.freshness_proof_paths_exist(proof, require_proof_path=True):
            return proof
        gate_clearing_batch_package_freshness.stable_current_package_freshness_path(
            study_root=study_root
        ).unlink(missing_ok=True)
    gate_replay = latest_batch.get("gate_replay")
    if not isinstance(gate_replay, dict):
        return None
    return gate_clearing_batch_package_freshness.write_current_package_freshness_proof(
        study_root=study_root,
        source_eval_id=source_eval_id,
        gate_report=gate_replay_report_payload(
            gate_replay=gate_replay,
            read_json=read_json,
            non_empty_text=non_empty_text,
        ),
        unit_results=[],
        clock=clock_snapshot,
        schema_version=schema_version,
    )


def base_publication_work_unit(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: item
        for key, item in value.items()
        if key not in {"lifecycle", "lifecycle_status", "retry", "status"}
    }


def closed_batch_lifecycle_record(
    *,
    latest_batch: dict[str, Any],
    study_id: str,
    quest_id: str,
    source_eval_id: str,
    gate_report: dict[str, Any] | None,
    non_empty_text: Callable[[object], str | None],
) -> dict[str, Any] | None:
    selected_work_unit = base_publication_work_unit(latest_batch.get("selected_publication_work_unit"))
    if selected_work_unit is None:
        existing_lifecycle = latest_batch.get("publication_work_unit_lifecycle")
        if isinstance(existing_lifecycle, dict):
            selected_work_unit = base_publication_work_unit(existing_lifecycle.get("work_unit"))
    unit_results = [
        dict(item)
        for item in (latest_batch.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    gate_replay = dict(latest_batch.get("gate_replay") or {})
    if current_gate_settles_authority_sync(
        latest_batch=latest_batch,
        gate_report=gate_report,
        non_empty_text=non_empty_text,
    ):
        unit_results = [
            {
                **item,
                "status": "settled_by_current_gate"
                if non_empty_text(item.get("status")) == "skipped_authority_not_settled"
                else item.get("status"),
            }
            for item in unit_results
        ]
        gate_replay = {
            **gate_replay,
            "status": "clear",
            "allow_write": True,
        }
    if selected_work_unit is None or not unit_results:
        return None
    return publication_work_unit_lifecycle.build_lifecycle_record(
        source_eval_id=source_eval_id,
        study_id=study_id,
        quest_id=quest_id,
        selected_work_unit=selected_work_unit,
        unit_results=unit_results,
        gate_replay=gate_replay,
    )


def normalize_closed_batch_lifecycle_surface(
    *,
    latest_batch: dict[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str,
    source_eval_id: str,
    gate_report: dict[str, Any] | None,
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, dict[str, Any]], None],
    non_empty_text: Callable[[object], str | None],
) -> tuple[dict[str, Any] | None, bool]:
    lifecycle_record = closed_batch_lifecycle_record(
        latest_batch=latest_batch,
        study_id=study_id,
        quest_id=quest_id,
        source_eval_id=source_eval_id,
        gate_report=gate_report,
        non_empty_text=non_empty_text,
    )
    if lifecycle_record is None:
        return None, False
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=study_root
    )
    current_record = read_json(lifecycle_path)
    current_status = non_empty_text(current_record.get("status"))
    current_source_eval_id = non_empty_text(current_record.get("source_eval_id"))
    normalized_status = non_empty_text(lifecycle_record.get("status"))
    if (
        current_source_eval_id == source_eval_id
        and current_status == normalized_status
        and ("retry" in current_record) == ("retry" in lifecycle_record)
    ):
        return dict(current_record), False
    write_json(lifecycle_path, lifecycle_record)
    return lifecycle_record, True


def write_normalized_closed_batch_record(
    *,
    study_root: Path,
    latest_batch: dict[str, Any],
    lifecycle_record: dict[str, Any] | None,
    current_package_freshness_proof: dict[str, Any] | None,
    stable_gate_clearing_batch_path: Callable[..., Path],
    write_json: Callable[[Path, dict[str, Any]], None],
    non_empty_text: Callable[[object], str | None],
) -> None:
    if lifecycle_record is None and current_package_freshness_proof is None:
        return
    normalized_batch_record = dict(latest_batch)
    if lifecycle_record is not None:
        normalized_batch_record["publication_work_unit_lifecycle"] = lifecycle_record
        lifecycle_unit_statuses = {
            non_empty_text(item.get("unit_id")): non_empty_text(item.get("status"))
            for item in (lifecycle_record.get("unit_statuses") or [])
            if isinstance(item, dict)
        }
        unit_results = latest_batch.get("unit_results")
        if isinstance(unit_results, list):
            normalized_batch_record["unit_results"] = [
                {
                    **item,
                    "status": lifecycle_unit_statuses.get(non_empty_text(item.get("unit_id")), item.get("status")),
                }
                if isinstance(item, dict)
                else item
                for item in unit_results
            ]
        selected_work_unit = normalized_batch_record.get("selected_publication_work_unit")
        if isinstance(selected_work_unit, dict):
            normalized_batch_record["selected_publication_work_unit"] = (
                publication_work_unit_lifecycle.enrich_selected_work_unit(
                    selected_work_unit=base_publication_work_unit(selected_work_unit),
                    lifecycle_record=lifecycle_record,
                )
            )
    if current_package_freshness_proof is not None:
        normalized_batch_record["current_package_freshness_proof"] = current_package_freshness_proof
        normalized_batch_record["gate_fingerprint"] = current_package_freshness_proof.get(
            "gate_fingerprint",
            normalized_batch_record.get("gate_fingerprint"),
        )
        normalized_batch_record["evaluated_source_signature"] = current_package_freshness_proof.get(
            "source_signature",
            normalized_batch_record.get("evaluated_source_signature"),
        )
        normalized_batch_record["authority_source_signature"] = current_package_freshness_proof.get(
            "authority_source_signature",
            normalized_batch_record.get("authority_source_signature"),
        )
    if normalized_batch_record != latest_batch:
        write_json(stable_gate_clearing_batch_path(study_root=study_root), normalized_batch_record)


def latest_batch_closed_for_eval(latest_batch: dict[str, Any], current_eval_id: str | None) -> bool:
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(latest_batch, source_eval_id=current_eval_id)


def latest_batch_closed_for_current_gate(
    latest_batch: dict[str, Any],
    current_eval_id: str | None,
    gate_report: dict[str, Any],
    quality_authority_currentness: dict[str, Any] | None = None,
) -> bool:
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(
        latest_batch,
        source_eval_id=current_eval_id,
        gate_report=gate_report,
        quality_authority_currentness=quality_authority_currentness,
    )


def current_gate_settles_authority_sync(
    *,
    latest_batch: dict[str, Any],
    gate_report: dict[str, Any] | None,
    non_empty_text: Callable[[object], str | None],
) -> bool:
    if not isinstance(gate_report, dict):
        return False
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(
        latest_batch,
        source_eval_id=non_empty_text(latest_batch.get("source_eval_id")),
        gate_report=gate_report,
    ) and not gate_clearing_batch_currentness.batch_closed_for_source_eval(
        latest_batch,
        source_eval_id=non_empty_text(latest_batch.get("source_eval_id")),
    )


__all__ = [
    "base_publication_work_unit",
    "closed_batch_current_freshness_proof",
    "closed_batch_lifecycle_record",
    "current_gate_settles_authority_sync",
    "freshness_gate_report_payload",
    "gate_replay_report_payload",
    "latest_batch_closed_for_current_gate",
    "latest_batch_closed_for_eval",
    "normalize_closed_batch_lifecycle_surface",
    "write_normalized_closed_batch_record",
]
