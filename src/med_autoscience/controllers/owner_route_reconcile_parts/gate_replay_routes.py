from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.controllers import publication_work_units


GATE_CLEARING_BATCH_RELATIVE_PATH = Path("artifacts/controller/gate_clearing_batch/latest.json")


def current_gate_replay_routeback_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / GATE_CLEARING_BATCH_RELATIVE_PATH
    batch = _read_json_object(batch_path)
    if batch is None:
        return None
    if _text(batch.get("source_eval_id")) != _text(publication_eval_payload.get("eval_id")):
        return None
    gate_report = _gate_replay_report_payload(batch, study_root=resolved_study_root)
    if gate_report is None:
        return None
    if _text(gate_report.get("status")) != "blocked" or gate_report.get("allow_write") is True:
        return None
    batch_work_unit = _mapping(batch.get("current_publication_work_unit"))
    batch_write_route_back = _text(batch_work_unit.get("lane")) == "write"
    work_units = publication_work_units.derive_publication_work_units(gate_report)
    next_work_unit = batch_work_unit if batch_write_route_back else _first_work_unit_for_lane(work_units, lane="write")
    if (
        _text(gate_report.get("medical_publication_surface_route_back_recommendation")) != "return_to_write"
        and not batch_write_route_back
        and next_work_unit is None
    ):
        return None
    if next_work_unit is None:
        return None
    work_unit_id = _text(next_work_unit.get("unit_id"))
    if work_unit_id is None:
        return None
    fingerprint = (
        _text(batch.get("work_unit_fingerprint"))
        or _text(work_units.get("fingerprint"))
        or _text(gate_report.get("gate_fingerprint"))
    )
    source_eval_id = _text(publication_eval_payload.get("eval_id"))
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_quality_repair_batch"],
        "route_target": "write",
        "route_key_question": "What is the narrowest same-line manuscript repair or continuation step required now?",
        "route_rationale": _text(gate_report.get("controller_stage_note")),
        "source_route_key_question": "publication_gate_replay_blocked_route_back",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": f"gate-replay-route-back::write::{fingerprint or work_unit_id}",
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve(),
            ),
        },
        "next_work_unit": dict(next_work_unit),
        "blocking_work_units": [
            dict(item)
            for item in work_units.get("blocking_work_units") or []
            if isinstance(item, Mapping)
        ],
        "gate_report_path": _text(_mapping(batch.get("gate_replay")).get("report_json")),
        "gate_clearing_batch_path": str(batch_path),
        "gate_fingerprint": _text(gate_report.get("gate_fingerprint")),
        "gate_blockers": sorted(_string_set(gate_report.get("blockers"))),
        "source": "owner_route_reconcile_gate_replay_routeback",
        "authorization_basis": "gate_replay_route_back",
    }


def current_gate_replay_submission_refresh_route(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    batch_path = resolved_study_root / GATE_CLEARING_BATCH_RELATIVE_PATH
    batch = _read_json_object(batch_path)
    if batch is None:
        return None
    if _text(batch.get("source_eval_id")) != _text(publication_eval_payload.get("eval_id")):
        return None
    gate_report = _gate_replay_report_payload(batch, study_root=resolved_study_root)
    if gate_report is None:
        return None
    if _text(gate_report.get("status")) != "blocked" or gate_report.get("allow_write") is True:
        return None
    batch_work_unit = _mapping(batch.get("current_publication_work_unit"))
    work_unit_id = _text(batch_work_unit.get("unit_id"))
    if work_unit_id != "submission_minimal_refresh":
        return None
    if _text(batch_work_unit.get("lane")) != "finalize":
        return None
    work_units = publication_work_units.derive_publication_work_units(gate_report)
    if _first_work_unit_for_lane(work_units, lane="write") is not None:
        return None
    fingerprint = (
        _text(batch.get("work_unit_fingerprint"))
        or _text(_mapping(batch.get("work_unit_currentness")).get("current_work_unit_fingerprint"))
        or _text(gate_report.get("gate_fingerprint"))
    )
    source_eval_id = _text(publication_eval_payload.get("eval_id"))
    return {
        "decision_path": None,
        "decision_id": None,
        "controller_actions": ["run_gate_clearing_batch"],
        "route_target": "finalize",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": f"gate-replay-route-back::finalize::{fingerprint or work_unit_id}",
        "publication_eval_id": source_eval_id,
        "publication_eval_ref": {
            "eval_id": source_eval_id,
            "artifact_path": ai_reviewer_publication_eval_records.projection_source_ref(
                publication_eval_payload,
                (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve(),
            ),
        },
        "next_work_unit": dict(batch_work_unit),
        "gate_report_path": _text(_mapping(batch.get("gate_replay")).get("report_json")),
        "gate_clearing_batch_path": str(batch_path),
        "gate_fingerprint": _text(gate_report.get("gate_fingerprint")),
        "gate_blockers": sorted(_string_set(gate_report.get("blockers"))),
        "source": "owner_route_reconcile_gate_replay_submission_refresh",
        "authorization_basis": "gate_replay_submission_minimal_refresh",
    }


def _gate_replay_report_payload(batch: Mapping[str, Any], *, study_root: Path) -> dict[str, Any] | None:
    gate_replay = _mapping(batch.get("gate_replay"))
    report_ref = _text(gate_replay.get("report_json")) or _text(gate_replay.get("report_path"))
    if report_ref:
        report_path = Path(report_ref).expanduser()
        if not report_path.is_absolute():
            report_path = study_root / report_path
        report = _read_json_object(report_path)
        if report is not None:
            return report
    return gate_replay or None


def _first_work_unit_for_lane(work_units: Mapping[str, Any], *, lane: str) -> dict[str, Any] | None:
    candidates: list[Any] = []
    next_work_unit = work_units.get("next_work_unit")
    if isinstance(next_work_unit, Mapping):
        candidates.append(next_work_unit)
    candidates.extend(work_units.get("blocking_work_units") or [])
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            continue
        if _text(candidate.get("lane")) == lane:
            return dict(candidate)
    return None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_set(value: object) -> set[str]:
    if isinstance(value, str):
        item = value.strip()
        return {item} if item else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _text(item)) is not None}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "GATE_CLEARING_BATCH_RELATIVE_PATH",
    "current_gate_replay_routeback_route",
    "current_gate_replay_submission_refresh_route",
]
