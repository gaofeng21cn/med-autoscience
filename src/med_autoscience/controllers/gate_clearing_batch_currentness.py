from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers.gate_clearing_batch_work_units import explicit_next_publication_work_unit


GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID = "gate_needs_specificity"
ANALYSIS_CLAIM_EVIDENCE_REPAIR_WORK_UNIT_ID = "analysis_claim_evidence_repair"


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


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


def gate_specificity_terminal_reason(
    *,
    explicit_publication_work_unit: dict[str, Any] | None,
    selected_publication_work_unit: dict[str, Any] | None,
    current_publication_work_unit_payload: dict[str, Any],
    work_unit_currentness: dict[str, Any],
) -> str | None:
    explicit_work_unit_id = publication_work_unit_id(explicit_publication_work_unit)
    current_work_unit_id = publication_work_unit_id(current_publication_work_unit_payload.get("next_work_unit"))
    if explicit_work_unit_id == GATE_NEEDS_SPECIFICITY_WORK_UNIT_ID:
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
        "work_unit_fingerprint": current_publication_work_unit_payload.get("fingerprint"),
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
