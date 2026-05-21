from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner


OWNER = analysis_harmonization_owner.OWNER
WORK_UNIT = analysis_harmonization_owner.WORK_UNIT
BLOCKED_REASON = analysis_harmonization_owner.BLOCKED_REASON
MODEL_PROVENANCE_BLOCKED_REASON = analysis_harmonization_owner.MODEL_PROVENANCE_BLOCKED_REASON
MODEL_PROVENANCE_OWNER = analysis_harmonization_owner.MODEL_PROVENANCE_OWNER
MODEL_PROVENANCE_WORK_UNIT = analysis_harmonization_owner.MODEL_PROVENANCE_WORK_UNIT
RESULT_RELATIVE_PATH = analysis_harmonization_owner.RESULT_RELATIVE_PATH


def result_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RESULT_RELATIVE_PATH


def read_result(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(result_path(study_root=study_root))


def required_output_satisfied(*, study_root: Path) -> bool:
    if clean_rebuild_decision_supersedes_legacy_blocker(study_root=study_root):
        return False
    return result_satisfies_required_output(read_result(study_root=study_root))


def result_satisfies_required_output(payload: Mapping[str, Any] | None) -> bool:
    result = _mapping(payload)
    if not _matches_analysis_harmonization_result(result):
        return False
    if result.get("unit_harmonized_rerun_completed") is True:
        return _completed_result_has_required_evidence(result)
    return result_is_accepted_typed_blocker(result)


def result_is_accepted_typed_blocker(payload: Mapping[str, Any] | None) -> bool:
    result = _mapping(payload)
    if not _matches_analysis_harmonization_result(result):
        return False
    if _text(result.get("status")) != "blocked":
        return False
    if _text(result.get("blocked_reason")) != BLOCKED_REASON:
        return False
    if _text(result.get("typed_blocker_owner")) != OWNER:
        return False
    typed_blocker = _mapping(result.get("typed_blocker"))
    if typed_blocker and _text(typed_blocker.get("blocker_id")) != BLOCKED_REASON:
        return False
    return result.get("unit_harmonized_rerun_completed") is not True


def clean_rebuild_decision_supersedes_legacy_blocker(*, study_root: Path) -> bool:
    result = read_result(study_root=study_root)
    if not result_is_accepted_typed_blocker(result):
        return False
    if _mapping(result).get("unit_harmonized_rerun_completed") is True:
        return False
    decision = _read_json_object(Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json")
    next_work_unit = _mapping(_mapping(decision).get("next_work_unit"))
    if _text(next_work_unit.get("unit_id")) != WORK_UNIT:
        return False
    if _text(next_work_unit.get("selected_route_option")) != "rebuild_reproducible_model_route":
        return False
    return next_work_unit.get("clean_reproducible_model_rebuild_authorized") is True


def typed_blocker_state(*, study_root: Path) -> dict[str, Any] | None:
    payload = read_result(study_root=study_root)
    if not result_is_accepted_typed_blocker(payload):
        return None
    owner_route = blocking_owner_route(payload)
    return {
        "blocked_reason": owner_route["blocked_reason"],
        "next_owner": owner_route["next_owner"],
        "external_supervisor_required": False,
    }


def blocking_owner_route(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    result = _mapping(payload)
    route = _mapping(result.get("blocking_owner_route"))
    blocked_reason = _text(route.get("blocked_reason"))
    next_owner = _text(route.get("next_owner"))
    next_work_unit = _text(route.get("next_work_unit"))
    if blocked_reason and next_owner and next_work_unit:
        return {
            "blocked_reason": blocked_reason,
            "next_owner": next_owner,
            "next_work_unit": next_work_unit,
        }
    typed_blocker = _mapping(result.get("typed_blocker"))
    blocking_reasons = _string_items(typed_blocker.get("blocking_reasons"))
    if "cox_model_application_provenance_insufficient_for_rerun" in blocking_reasons:
        return {
            "blocked_reason": MODEL_PROVENANCE_BLOCKED_REASON,
            "next_owner": MODEL_PROVENANCE_OWNER,
            "next_work_unit": MODEL_PROVENANCE_WORK_UNIT,
        }
    return {
        "blocked_reason": BLOCKED_REASON,
        "next_owner": OWNER,
        "next_work_unit": WORK_UNIT,
    }


def output_pending_for_result(payload: Mapping[str, Any] | None) -> bool:
    return not result_satisfies_required_output(payload)


def _completed_result_has_required_evidence(payload: Mapping[str, Any]) -> bool:
    evidence = _mapping(payload.get("rerun_evidence"))
    evidence_ref = _text(payload.get("rerun_evidence_ref"))
    if not evidence and evidence_ref:
        evidence = _read_json_object(Path(evidence_ref).expanduser().resolve()) or {}
    if _text(evidence.get("surface")) != "unit_harmonized_external_validation_rerun_evidence":
        return False
    if _text(evidence.get("status")) != "completed":
        return False
    return (
        _has_uncertainty(evidence)
        and _has_calibration(evidence)
        and _has_grouped_calibration(evidence)
    )


def _has_uncertainty(evidence: Mapping[str, Any]) -> bool:
    uncertainty = _mapping(evidence.get("uncertainty"))
    intervals = _mapping(uncertainty.get("metrics_95ci"))
    required_metrics = ("c_index", "observed_expected_ratio", "brier_5y")
    return all(_has_interval(_mapping(intervals.get(metric))) for metric in required_metrics)


def _has_calibration(evidence: Mapping[str, Any]) -> bool:
    calibration = _mapping(evidence.get("calibration"))
    return _has_interval(_mapping(_mapping(calibration.get("calibration_intercept")).get("ci_95"))) and _has_interval(
        _mapping(_mapping(calibration.get("calibration_slope")).get("ci_95"))
    )


def _has_grouped_calibration(evidence: Mapping[str, Any]) -> bool:
    grouped = _mapping(evidence.get("grouped_calibration"))
    groups = grouped.get("groups")
    if not isinstance(groups, list) or not groups:
        return False
    for group in groups:
        item = _mapping(group)
        if item.get("n") is None:
            return False
        if item.get("mean_predicted_5y_risk") is None:
            return False
        if item.get("observed_5y_rate") is None:
            return False
        if not _has_interval(_mapping(item.get("observed_5y_rate_ci_95"))):
            return False
    return True


def _has_interval(interval: Mapping[str, Any]) -> bool:
    return interval.get("lower") is not None and interval.get("upper") is not None


def _matches_analysis_harmonization_result(payload: Mapping[str, Any]) -> bool:
    if _text(payload.get("surface")) != "analysis_harmonization_owner_result":
        return False
    if _text(payload.get("owner")) != OWNER:
        return False
    return _text(payload.get("work_unit")) == WORK_UNIT


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "BLOCKED_REASON",
    "MODEL_PROVENANCE_BLOCKED_REASON",
    "MODEL_PROVENANCE_OWNER",
    "MODEL_PROVENANCE_WORK_UNIT",
    "OWNER",
    "RESULT_RELATIVE_PATH",
    "WORK_UNIT",
    "blocking_owner_route",
    "clean_rebuild_decision_supersedes_legacy_blocker",
    "output_pending_for_result",
    "read_result",
    "required_output_satisfied",
    "result_is_accepted_typed_blocker",
    "result_path",
    "result_satisfies_required_output",
    "typed_blocker_state",
]
