from __future__ import annotations

from typing import Any, Mapping


_BASE_TRUTH_SURFACES = (
    "study_runtime_status",
    "runtime_watch",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
)
_QUALITY_TRUTH_SURFACES = (
    "study_charter",
    "paper/evidence_ledger.json",
    "paper/review_ledger.json",
    "artifacts/controller/gate_clearing_batch/latest.json",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bottleneck_ids(profile_payload: Mapping[str, Any]) -> set[str]:
    return {
        bottleneck_id
        for item in _list(profile_payload.get("bottlenecks"))
        if isinstance(item, Mapping)
        if (bottleneck_id := _text(item.get("bottleneck_id"))) is not None
    }


def _current_blockers(profile_payload: Mapping[str, Any]) -> list[str]:
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    return [
        blocker
        for item in _list(gate_summary.get("current_blockers"))
        if (blocker := _text(item)) is not None
    ]


def build_study_soak_replay_case(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _text(profile_payload.get("study_id")) or "unknown-study"
    bottleneck_ids = _bottleneck_ids(profile_payload)
    runtime_failure = _mapping(profile_payload.get("runtime_failure_classification"))
    runtime_action_mode = _text(runtime_failure.get("action_mode"))
    blockers = _current_blockers(profile_payload)
    if runtime_action_mode in {"external_fix_required", "provider_backoff_and_recheck"} or (
        "runtime_recovery_churn" in bottleneck_ids
    ):
        case_family = "runtime_recovery_taxonomy"
        must_assert = [
            "external_runtime_blocker_is_not_retried_as_mas_work",
            "quality_gate_relaxation_allowed_false",
            "same_study_progress_truth_surfaces_present",
        ]
        surfaces = list(_BASE_TRUTH_SURFACES)
    elif "publication_gate_blocked" in bottleneck_ids or blockers:
        case_family = "same_line_quality_gate_fast_lane"
        must_assert = [
            "same_line_quality_repair_stays_controller_owned",
            "publication_gate_replay_follows_repair_batch",
            "quality_gate_relaxation_allowed_false",
        ]
        surfaces = [*_BASE_TRUTH_SURFACES, *_QUALITY_TRUTH_SURFACES]
    else:
        case_family = "long_run_autonomy_baseline"
        must_assert = [
            "progress_truth_surfaces_remain_consistent",
            "quality_gate_relaxation_allowed_false",
        ]
        surfaces = list(_BASE_TRUTH_SURFACES)
    return {
        "surface": "study_soak_replay_case",
        "schema_version": 1,
        "study_id": study_id,
        "case_id": f"study-soak-replay::{study_id}::{case_family}",
        "case_family": case_family,
        "source_bottlenecks": sorted(bottleneck_ids),
        "source_blockers": blockers,
        "runtime_failure_action_mode": runtime_action_mode,
        "required_truth_surfaces": surfaces,
        "must_assert": must_assert,
        "edits_paper_body": False,
        "gate_relaxation_allowed": False,
    }
