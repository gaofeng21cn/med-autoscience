from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.stable_json import write_stable_json
from med_autoscience.controllers import gate_clearing_batch_replay_closure
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
    derived_next_publication_work_unit,
    explicit_next_publication_work_unit,
    submission_delivery_sync_closure_work_unit,
)
from med_autoscience.study_decision_record import StudyDecisionRecord


GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID = "gate_needs_specificity"
ANALYSIS_CLAIM_EVIDENCE_REPAIR_WORK_UNIT_ID = "analysis_claim_evidence_repair"
SUBMISSION_DELIVERY_TERMINAL_BLOCKER_WORK_UNIT_ID = "submission_delivery_terminal_blocker"
_BATCH_OPEN_UNIT_STATUSES = frozenset(
    {
        "control_plane_route_blocked",
        "failed",
        "missing",
        "skipped_failed_dependency",
    }
)
_TRANSIENT_OPEN_UNIT_STATUSES = frozenset({"skipped_authority_not_settled"})
_AUTHORITY_SYNC_WORK_UNIT_IDS = frozenset(
    {
        "submission_authority_sync_closure",
        "submission_delivery_sync_closure",
        "submission_minimal_refresh",
    }
)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def publication_work_unit_id(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    return _non_empty_text(value.get("unit_id"))


def explicit_publication_work_unit_fingerprint(publication_eval_payload: dict[str, Any]) -> str | None:
    recommended_actions = publication_eval_payload.get("recommended_actions") or []
    if not isinstance(recommended_actions, list):
        return None
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        if explicit_next_publication_work_unit({"recommended_actions": [action]}) is None:
            continue
        return _non_empty_text(action.get("work_unit_fingerprint"))
    return None


def latest_batch_work_unit_fingerprint(latest_batch: dict[str, Any]) -> str | None:
    fingerprint = _non_empty_text(latest_batch.get("work_unit_fingerprint"))
    if fingerprint is not None:
        return fingerprint
    currentness = latest_batch.get("work_unit_currentness")
    if isinstance(currentness, dict):
        return _non_empty_text(currentness.get("current_work_unit_fingerprint"))
    return None


def _matching_currentness_fields(
    *,
    current_values: dict[str, str | None],
    previous_values: dict[str, str | None],
) -> tuple[bool, dict[str, bool]]:
    comparisons: dict[str, bool] = {}
    for key, current_value in current_values.items():
        previous_value = previous_values.get(key)
        if current_value is None or previous_value is None:
            continue
        comparisons[key] = current_value == previous_value
    return bool(comparisons) and all(comparisons.values()), comparisons


def publication_work_unit_currentness(
    *,
    publication_eval_payload: dict[str, Any],
    latest_batch: dict[str, Any],
    gate_report: dict[str, Any],
    current_publication_work_unit_payload: dict[str, Any],
    explicit_publication_work_unit: dict[str, Any] | None,
    selected_publication_work_unit: dict[str, Any] | None,
) -> dict[str, Any]:
    explicit_work_unit_fingerprint = explicit_publication_work_unit_fingerprint(publication_eval_payload)
    current_work_unit_fingerprint = _non_empty_text(current_publication_work_unit_payload.get("fingerprint"))
    previous_work_unit_fingerprint = latest_batch_work_unit_fingerprint(latest_batch)
    current_values = {
        "work_unit_fingerprint": current_work_unit_fingerprint,
        "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
        "evaluated_source_signature": _non_empty_text(
            gate_report.get("submission_minimal_evaluated_source_signature")
        ),
        "authority_source_signature": _non_empty_text(
            gate_report.get("submission_minimal_authority_source_signature")
        ),
    }
    previous_values = {
        "work_unit_fingerprint": previous_work_unit_fingerprint,
        "gate_fingerprint": _non_empty_text(latest_batch.get("gate_fingerprint")),
        "evaluated_source_signature": _non_empty_text(latest_batch.get("evaluated_source_signature")),
        "authority_source_signature": _non_empty_text(latest_batch.get("authority_source_signature")),
    }
    fingerprint_or_source_signature_unchanged, unchanged_comparisons = _matching_currentness_fields(
        current_values=current_values,
        previous_values=previous_values,
    )
    explicit_matches_current = bool(
        explicit_work_unit_fingerprint
        and current_work_unit_fingerprint
        and explicit_work_unit_fingerprint == current_work_unit_fingerprint
    )
    actionability_status = _non_empty_text(current_publication_work_unit_payload.get("actionability_status"))
    current_next_work_unit = current_publication_work_unit_payload.get("next_work_unit")
    current_work_unit_id = publication_work_unit_id(current_next_work_unit)
    lacks_specific_blocker_object = (
        current_work_unit_id == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID
        and actionability_status == "blocked_by_non_actionable_gate"
    )
    return {
        "explicit_publication_work_unit_id": publication_work_unit_id(explicit_publication_work_unit),
        "selected_publication_work_unit_id": publication_work_unit_id(selected_publication_work_unit),
        "current_publication_work_unit_id": current_work_unit_id,
        "explicit_work_unit_fingerprint": explicit_work_unit_fingerprint,
        "current_work_unit_fingerprint": current_work_unit_fingerprint,
        "previous_work_unit_fingerprint": previous_work_unit_fingerprint,
        "explicit_work_unit_fingerprint_matches_current": explicit_matches_current,
        "fingerprint_or_source_signature_unchanged": fingerprint_or_source_signature_unchanged,
        "currentness_field_comparisons": unchanged_comparisons,
        "lacks_specific_blocker_object": lacks_specific_blocker_object,
        "current_actionability_status": actionability_status,
    }


def _compact_work_unit_payload(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    unit_id = _non_empty_text(value.get("unit_id"))
    if unit_id is None:
        return None
    payload = {"unit_id": unit_id}
    for key in ("lane", "summary", "control_surface", "user_feedback_priority"):
        text = _non_empty_text(value.get(key))
        if text is not None:
            payload[key] = text
    return payload


def controller_decision_publication_work_unit(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    source_eval_id: str | None,
) -> dict[str, str] | None:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    payload = _read_json(decision_path)
    if not payload:
        return None
    try:
        record = StudyDecisionRecord.from_payload(payload)
    except (TypeError, ValueError):
        return None
    if record.study_id != study_id or record.quest_id != quest_id:
        return None
    if record.requires_human_confirmation:
        return None
    action_types = {action.action_type.value for action in record.controller_actions}
    if "run_gate_clearing_batch" not in action_types:
        return None
    if source_eval_id and record.publication_eval_ref.eval_id != source_eval_id:
        return None
    return _compact_work_unit_payload(record.next_work_unit)


def gate_specificity_terminal_reason(
    *,
    explicit_publication_work_unit: dict[str, Any] | None,
    selected_publication_work_unit: dict[str, Any] | None,
    current_publication_work_unit_payload: dict[str, Any],
    work_unit_currentness: dict[str, Any],
) -> str | None:
    explicit_work_unit_id = publication_work_unit_id(explicit_publication_work_unit)
    selected_work_unit_id = publication_work_unit_id(selected_publication_work_unit)
    current_work_unit_id = publication_work_unit_id(current_publication_work_unit_payload.get("next_work_unit"))
    if (
        explicit_work_unit_id == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID
        and selected_work_unit_id == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID
    ):
        return "publication_eval_requested_gate_specificity"
    if current_work_unit_id != GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID:
        return None
    if explicit_work_unit_id == ANALYSIS_CLAIM_EVIDENCE_REPAIR_WORK_UNIT_ID and (
        work_unit_currentness.get("explicit_work_unit_fingerprint_matches_current") is True
        or work_unit_currentness.get("fingerprint_or_source_signature_unchanged") is True
        or work_unit_currentness.get("lacks_specific_blocker_object") is True
    ):
        return "current_gate_requires_specific_blocker_object"
    return None


def publication_work_unit_selection(
    *,
    publication_eval_payload: dict[str, Any],
    latest_batch: dict[str, Any],
    gate_report: dict[str, Any],
    authority_settle_delivery_redrive_requested: bool,
    direct_submission_delivery_sync_requested: bool = False,
    controller_decision_work_unit: dict[str, str] | None = None,
) -> dict[str, Any]:
    explicit_next_work_unit = explicit_next_publication_work_unit(publication_eval_payload)
    specificity_targets = publication_work_units.specificity_targets_from_publication_eval(publication_eval_payload)
    current_publication_work_unit_payload = publication_work_units.derive_publication_work_units(
        gate_report,
        specificity_targets=specificity_targets,
    )
    current_next_work_unit = current_publication_work_unit_payload.get("next_work_unit")
    selected_publication_work_unit = controller_decision_work_unit or explicit_next_work_unit or (
        current_next_work_unit if isinstance(current_next_work_unit, dict) else derived_next_publication_work_unit(gate_report)
    )
    selected_work_unit_id = publication_work_unit_id(selected_publication_work_unit)
    current_work_unit_id = publication_work_unit_id(current_next_work_unit)
    if (
        selected_work_unit_id == "publication_gate_replay"
        and current_work_unit_id in {"submission_authority_sync_closure", "submission_delivery_sync_closure"}
        and isinstance(current_next_work_unit, dict)
    ):
        selected_publication_work_unit = dict(current_next_work_unit)
        selected_work_unit_id = current_work_unit_id
    if (
        specificity_targets
        and selected_work_unit_id == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID
        and current_work_unit_id is not None
        and current_work_unit_id != GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID
        and isinstance(current_next_work_unit, dict)
    ):
        selected_publication_work_unit = dict(current_next_work_unit)
        selected_work_unit_id = current_work_unit_id
    if (
        specificity_targets
        and selected_work_unit_id == "publication_gate_replay"
        and current_work_unit_id in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
        and isinstance(current_next_work_unit, dict)
    ):
        selected_publication_work_unit = dict(current_next_work_unit)
        selected_work_unit_id = current_work_unit_id
    if (
        selected_work_unit_id
        in {GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID, SUBMISSION_DELIVERY_TERMINAL_BLOCKER_WORK_UNIT_ID}
        and gate_clearing_batch_replay_closure.stale_gate_replay_closed(latest_batch, gate_report=gate_report)
    ):
        selected_publication_work_unit = submission_delivery_sync_closure_work_unit()
        selected_work_unit_id = publication_work_unit_id(selected_publication_work_unit)
    if (
        authority_settle_delivery_redrive_requested
        and selected_work_unit_id not in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
    ):
        selected_publication_work_unit = submission_delivery_sync_closure_work_unit()
        selected_work_unit_id = publication_work_unit_id(selected_publication_work_unit)
    if direct_submission_delivery_sync_requested and publication_work_unit_id(
        explicit_next_work_unit
    ) == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID:
        selected_publication_work_unit = submission_delivery_sync_closure_work_unit()
    work_unit_currentness = publication_work_unit_currentness(
        publication_eval_payload=publication_eval_payload,
        latest_batch=latest_batch,
        gate_report=gate_report,
        current_publication_work_unit_payload=current_publication_work_unit_payload,
        explicit_publication_work_unit=explicit_next_work_unit,
        selected_publication_work_unit=selected_publication_work_unit,
    )
    terminal_reason = None
    if not authority_settle_delivery_redrive_requested and not direct_submission_delivery_sync_requested:
        terminal_reason = gate_specificity_terminal_reason(
            explicit_publication_work_unit=explicit_next_work_unit,
            selected_publication_work_unit=selected_publication_work_unit,
            current_publication_work_unit_payload=current_publication_work_unit_payload,
            work_unit_currentness=work_unit_currentness,
        )
    return {
        "explicit_next_work_unit": explicit_next_work_unit,
        "controller_decision_work_unit": controller_decision_work_unit,
        "current_publication_work_unit_payload": current_publication_work_unit_payload,
        "current_next_work_unit": current_next_work_unit,
        "selected_publication_work_unit": selected_publication_work_unit,
        "work_unit_currentness": work_unit_currentness,
        "terminal_reason": terminal_reason,
    }


def terminal_publication_work_unit(selection: dict[str, Any]) -> dict[str, Any]:
    selected_publication_work_unit = selection.get("selected_publication_work_unit")
    current_next_work_unit = selection.get("current_next_work_unit")
    if publication_work_unit_id(selected_publication_work_unit) == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID:
        return dict(selected_publication_work_unit)
    if isinstance(current_next_work_unit, dict):
        return dict(current_next_work_unit)
    return {
        "unit_id": GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID,
        "lane": "controller",
        "summary": "Ask the publication gate to identify concrete blocker targets.",
    }


def _write_json(path: Path, payload: object) -> None:
    write_stable_json(path, payload)


def _unit_results_have_open_failures(batch_payload: dict[str, Any]) -> bool:
    unit_results = batch_payload.get("unit_results")
    if not isinstance(unit_results, list):
        return False
    return any(
        isinstance(item, dict)
        and _non_empty_text(item.get("status")) in _BATCH_OPEN_UNIT_STATUSES
        for item in unit_results
    )


def _unit_results_have_transient_open_units(batch_payload: dict[str, Any]) -> bool:
    unit_results = batch_payload.get("unit_results")
    if not isinstance(unit_results, list):
        return False
    return any(
        isinstance(item, dict)
        and _non_empty_text(item.get("status")) in _TRANSIENT_OPEN_UNIT_STATUSES
        for item in unit_results
    )


def _gate_replay_closed(batch_payload: dict[str, Any]) -> bool:
    gate_replay = batch_payload.get("gate_replay")
    if not isinstance(gate_replay, dict):
        return False
    return _non_empty_text(gate_replay.get("status")) == "clear" or gate_replay.get("allow_write") is True


def _authority_current_gate_closed(gate_report: dict[str, Any] | None) -> bool:
    if not isinstance(gate_report, dict):
        return False
    return (
        (_non_empty_text(gate_report.get("status")) == "clear" or gate_report.get("allow_write") is True)
        and _non_empty_text(gate_report.get("submission_minimal_authority_status")) == "current"
        and _non_empty_text(gate_report.get("study_delivery_status")) == "current"
    )


def _selected_work_unit_id(batch_payload: dict[str, Any]) -> str | None:
    selected = batch_payload.get("selected_publication_work_unit")
    if isinstance(selected, dict):
        return publication_work_unit_id(selected)
    lifecycle = batch_payload.get("publication_work_unit_lifecycle")
    if isinstance(lifecycle, dict):
        return publication_work_unit_id(lifecycle.get("work_unit"))
    return None


def _platform_terminal_closed(batch_payload: dict[str, Any]) -> bool:
    if _non_empty_text(batch_payload.get("status")) != "platform_terminal":
        return False
    return batch_payload.get("platform_terminal") is True and (
        _non_empty_text(batch_payload.get("terminal_state")) == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID
    )


def _stale_gate_replay_marker_closed(batch_payload: dict[str, Any]) -> bool:
    marker = batch_payload.get("stale_gate_replay_closure")
    if not isinstance(marker, dict):
        return False
    return _non_empty_text(marker.get("status")) == "closed"


def batch_closed_for_source_eval(
    batch_payload: dict[str, Any],
    *,
    source_eval_id: str | None,
    gate_report: dict[str, Any] | None = None,
) -> bool:
    if source_eval_id is None or _non_empty_text(batch_payload.get("source_eval_id")) != source_eval_id:
        return False
    if _unit_results_have_open_failures(batch_payload):
        return False
    if _unit_results_have_transient_open_units(batch_payload):
        return (
            _selected_work_unit_id(batch_payload) in _AUTHORITY_SYNC_WORK_UNIT_IDS
            and _authority_current_gate_closed(gate_report)
        )
    return (
        _gate_replay_closed(batch_payload)
        or _platform_terminal_closed(batch_payload)
        or _stale_gate_replay_marker_closed(batch_payload)
    )


def write_gate_specificity_terminal_batch(
    *,
    record_path: Path,
    lifecycle_path: Path,
    schema_version: int,
    study_root: Path,
    study_id: str,
    quest_id: str,
    paper_root: Path,
    current_workspace_root: Path,
    source_eval_id: str,
    gate_report: dict[str, Any],
    gate_blockers: set[str],
    explicit_publication_work_unit: dict[str, Any] | None,
    terminal_publication_work_unit: dict[str, Any],
    current_publication_work_unit_payload: dict[str, Any],
    work_unit_currentness: dict[str, Any],
    terminal_reason: str,
    gate_replay_timing: dict[str, Any],
) -> dict[str, Any]:
    record, lifecycle_record = gate_specificity_terminal_batch_record(
        schema_version=schema_version,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        paper_root=paper_root,
        current_workspace_root=current_workspace_root,
        source_eval_id=source_eval_id,
        gate_report=gate_report,
        gate_blockers=gate_blockers,
        explicit_publication_work_unit=explicit_publication_work_unit,
        terminal_publication_work_unit=terminal_publication_work_unit,
        current_publication_work_unit_payload=current_publication_work_unit_payload,
        work_unit_currentness=work_unit_currentness,
        terminal_reason=terminal_reason,
        gate_replay_timing=gate_replay_timing,
    )
    _write_json(record_path, record)
    _write_json(lifecycle_path, lifecycle_record)
    return {"ok": True, "record_path": str(record_path), **record}


def stale_gate_replay_closed_result(
    *,
    source_eval_id: str,
    latest_record_path: Path,
    latest_batch: dict[str, Any],
    gate_report: dict[str, Any],
    selected_publication_work_unit: dict[str, Any],
    current_publication_work_unit_payload: dict[str, Any],
    work_unit_currentness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "skipped_stale_gate_replay_closed",
        "source_eval_id": source_eval_id,
        "latest_record_path": str(latest_record_path),
        "gate_fingerprint": gate_report.get("gate_fingerprint"),
        "evaluated_source_signature": gate_report.get("submission_minimal_evaluated_source_signature"),
        "authority_source_signature": gate_report.get("submission_minimal_authority_source_signature"),
        "blocking_artifact_refs": gate_report.get("blocking_artifact_refs") or [],
        "selected_publication_work_unit": selected_publication_work_unit,
        "work_unit_fingerprint": current_publication_work_unit_payload.get("fingerprint"),
        "work_unit_currentness": work_unit_currentness,
        "stale_gate_replay_closure": latest_batch.get("stale_gate_replay_closure"),
    }


def build_executed_batch_record(
    *,
    schema_version: int,
    study_root: Path,
    source_eval_id: str,
    quest_id: str,
    study_id: str,
    paper_root: Path,
    current_workspace_root: Path,
    gate_blockers: set[str],
    gate_report: dict[str, Any],
    selected_publication_work_unit: dict[str, Any] | None,
    explicit_publication_work_unit: dict[str, Any] | None,
    current_publication_work_unit_payload: dict[str, Any],
    work_unit_currentness: dict[str, Any],
    unit_results: list[dict[str, Any]],
    unit_fingerprints: dict[str, Any],
    repair_unit_execution_plan: dict[str, Any],
    execution_summary: dict[str, Any],
    gate_replay: dict[str, Any],
    gate_replay_step: dict[str, Any],
    lifecycle_record: dict[str, Any],
    repair_blocking_artifact_refs: list[dict[str, Any]],
    current_package_freshness_proof: dict[str, Any] | None,
    stale_gate_replay_closure: dict[str, Any] | None,
) -> dict[str, Any]:
    work_unit_fingerprint = _non_empty_text(current_publication_work_unit_payload.get("fingerprint"))
    record = {
        "schema_version": schema_version,
        "source_eval_id": source_eval_id,
        "source_work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        "status": "executed",
        "quest_id": quest_id,
        "study_id": study_id,
        "paper_root": str(paper_root),
        "workspace_root": str(paper_root.parent),
        "current_workspace_root": str(current_workspace_root),
        "gate_blockers": sorted(gate_blockers),
        "gate_fingerprint": gate_report.get("gate_fingerprint"),
        "evaluated_source_signature": gate_report.get("submission_minimal_evaluated_source_signature"),
        "authority_source_signature": gate_report.get("submission_minimal_authority_source_signature"),
        "blocking_artifact_refs": gate_report.get("blocking_artifact_refs") or [],
        "selected_publication_work_unit": selected_publication_work_unit,
        "explicit_publication_work_unit": explicit_publication_work_unit,
        "current_publication_work_unit": current_publication_work_unit_payload.get("next_work_unit"),
        "work_unit_fingerprint": work_unit_fingerprint,
        "work_unit_currentness": work_unit_currentness,
        "unit_results": unit_results,
        "unit_fingerprints": unit_fingerprints,
        "repair_unit_execution_plan": repair_unit_execution_plan,
        "execution_summary": execution_summary,
        "gate_replay": gate_replay,
        "gate_replay_step": gate_replay_step,
        "publication_work_unit_lifecycle": lifecycle_record,
        "repair_blocking_artifact_refs": repair_blocking_artifact_refs,
    }
    if current_package_freshness_proof is not None:
        record["current_package_freshness_proof"] = current_package_freshness_proof
    if stale_gate_replay_closure is not None:
        record["stale_gate_replay_closure"] = stale_gate_replay_closure
    return record


def selected_work_unit_after_stale_delivery_closure(
    *,
    stale_gate_replay_closure: dict[str, Any] | None,
    selected_publication_work_unit: dict[str, Any] | None,
    source_eval_id: str,
    study_id: str,
    quest_id: str,
    unit_results: list[dict[str, Any]],
    gate_replay: dict[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if stale_gate_replay_closure is None or "stale_study_delivery_mirror" not in (
        stale_gate_replay_closure.get("closed_blockers") or []
    ):
        return selected_publication_work_unit, None
    selected_work_unit = submission_delivery_sync_closure_work_unit()
    lifecycle_record = publication_work_unit_lifecycle.build_lifecycle_record(
        source_eval_id=source_eval_id,
        study_id=study_id,
        quest_id=quest_id,
        selected_work_unit=selected_work_unit,
        unit_results=unit_results,
        gate_replay=gate_replay,
    )
    return (
        publication_work_unit_lifecycle.enrich_selected_work_unit(
            selected_work_unit=selected_work_unit,
            lifecycle_record=lifecycle_record,
        ),
        lifecycle_record,
    )


def gate_specificity_terminal_batch_record(
    *,
    schema_version: int,
    study_root: Path,
    study_id: str,
    quest_id: str,
    paper_root: Path,
    current_workspace_root: Path,
    source_eval_id: str,
    gate_report: dict[str, Any],
    gate_blockers: set[str],
    explicit_publication_work_unit: dict[str, Any] | None,
    terminal_publication_work_unit: dict[str, Any],
    current_publication_work_unit_payload: dict[str, Any],
    work_unit_currentness: dict[str, Any],
    terminal_reason: str,
    gate_replay_timing: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    work_unit_fingerprint = _non_empty_text(current_publication_work_unit_payload.get("fingerprint"))
    gate_replay = {
        "status": "not_run",
        "reason": terminal_reason,
        "terminal_state": GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID,
    }
    gate_replay_step = {
        "step_id": "publication_gate_replay",
        "status": "not_run",
        "result": gate_replay,
        **gate_replay_timing,
    }
    lifecycle_record = {
        "schema_version": publication_work_unit_lifecycle.SCHEMA_VERSION,
        "source_eval_id": source_eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "status": "needs_specificity",
        "work_unit": terminal_publication_work_unit,
        "unit_statuses": [],
        "gate_replay_status": "not_run",
        "terminal_state": GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID,
        "platform_terminal": True,
        "terminal_reason": terminal_reason,
    }
    selected_publication_work_unit = publication_work_unit_lifecycle.enrich_selected_work_unit(
        selected_work_unit=terminal_publication_work_unit,
        lifecycle_record=lifecycle_record,
    )
    record = {
        "schema_version": schema_version,
        "source_eval_id": source_eval_id,
        "source_work_unit_fingerprint": work_unit_fingerprint,
        "source_eval_artifact_path": str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        "status": "platform_terminal",
        "terminal_state": GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID,
        "platform_terminal": True,
        "terminal_reason": terminal_reason,
        "quest_id": quest_id,
        "study_id": study_id,
        "paper_root": str(paper_root),
        "workspace_root": str(paper_root.parent),
        "current_workspace_root": str(current_workspace_root),
        "gate_blockers": sorted(gate_blockers),
        "gate_fingerprint": gate_report.get("gate_fingerprint"),
        "evaluated_source_signature": gate_report.get("submission_minimal_evaluated_source_signature"),
        "authority_source_signature": gate_report.get("submission_minimal_authority_source_signature"),
        "blocking_artifact_refs": gate_report.get("blocking_artifact_refs") or [],
        "selected_publication_work_unit": selected_publication_work_unit,
        "explicit_publication_work_unit": explicit_publication_work_unit,
        "current_publication_work_unit": current_publication_work_unit_payload.get("next_work_unit"),
        "work_unit_fingerprint": work_unit_fingerprint,
        "work_unit_currentness": work_unit_currentness,
        "unit_results": [],
        "unit_fingerprints": {},
        "repair_unit_execution_plan": {
            "status": "not_planned",
            "reason": terminal_reason,
            "execution_policy": {
                "mode": "platform_terminal",
                "gate_relaxation_allowed": False,
                "requires_publication_gate_replay": False,
                "requires_authority_surface_refresh": False,
            },
        },
        "execution_summary": {
            "parallel_wave_count": 0,
            "parallel_unit_count": 0,
            "sequential_unit_count": 0,
            "skipped_dependency_unit_count": 0,
        },
        "gate_replay": gate_replay,
        "gate_replay_step": gate_replay_step,
        "publication_work_unit_lifecycle": lifecycle_record,
        "repair_blocking_artifact_refs": [],
    }
    return record, lifecycle_record
