from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)
from med_autoscience.profiles import WorkspaceProfile


def capture_apply_readback_snapshot(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
    enabled: bool,
) -> dict[str, dict[str, Any]]:
    return _progress_snapshot(
        profile=profile,
        study_ids=study_ids,
        enabled=enabled,
    )


def attach_apply_readback_summary(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
    before: Mapping[str, Mapping[str, Any]],
    enabled: bool,
) -> None:
    if not enabled or profile is None:
        return
    before_snapshot = {
        **_report_snapshot(report),
        **{study_id: dict(payload) for study_id, payload in before.items()},
    }
    target_study_ids = _target_study_ids(
        report=report,
        explicit_study_ids=study_ids,
        before=before_snapshot,
    )
    after = _progress_snapshot(
        profile=profile,
        study_ids=target_study_ids,
        enabled=True,
    )
    studies: list[dict[str, Any]] = []
    for study_id in target_study_ids:
        before_payload = dict(before_snapshot.get(study_id) or {})
        after_payload = dict(after.get(study_id) or {})
        if not before_payload and not after_payload:
            continue
        studies.append(
            {
                "study_id": study_id,
                "quest_id": _non_empty_text(after_payload.get("quest_id"))
                or _non_empty_text(before_payload.get("quest_id")),
                "before": before_payload,
                "after": after_payload,
                "delta": _delta(before_payload, after_payload),
            }
        )
    report["dhd_apply_readback_summary"] = {
        "surface": "domain_health_diagnostic_apply_readback_summary",
        "schema_version": 1,
        "study_count": len(studies),
        "studies": studies,
    }


def _report_snapshot(report: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    snapshots: dict[str, dict[str, Any]] = {}
    progress_currentness = _mapping(
        _mapping(report.get("current_execution_evidence")).get("progress_currentness")
    )
    for study_id, payload in progress_currentness.items():
        if not isinstance(payload, Mapping):
            continue
        text_id = _non_empty_text(study_id)
        if text_id is None:
            continue
        snapshots[text_id] = _snapshot_from_progress(payload)
    for action in report.get("managed_study_actions") or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None:
            continue
        current = snapshots.get(study_id, {})
        snapshots[study_id] = {
            **_snapshot_from_progress(action),
            **current,
        }
    return snapshots


def _target_study_ids(
    *,
    report: Mapping[str, Any],
    explicit_study_ids: tuple[str, ...],
    before: Mapping[str, Mapping[str, Any]],
) -> tuple[str, ...]:
    candidates: list[str] = []
    candidates.extend(_text_items(explicit_study_ids))
    candidates.extend(before.keys())
    candidates.extend(
        _non_empty_text(action.get("study_id"))
        for action in report.get("managed_study_actions") or []
        if isinstance(action, Mapping)
    )
    candidates.extend(
        _non_empty_text(outcome.get("study_id"))
        for outcome in report.get("managed_study_obligation_actuator_outcomes") or []
        if isinstance(outcome, Mapping)
    )
    return tuple(dict.fromkeys(study_id for study_id in candidates if study_id is not None))


def _progress_snapshot(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
    enabled: bool,
) -> dict[str, dict[str, Any]]:
    if not enabled or profile is None or not study_ids:
        return {}
    try:
        from med_autoscience.controllers import study_progress
    except Exception:
        return {}
    snapshots: dict[str, dict[str, Any]] = {}
    for study_id in tuple(dict.fromkeys(_text_items(study_ids))):
        try:
            progress = study_progress.read_study_progress(
                profile=profile,
                study_id=study_id,
                sync_runtime_summary=False,
                materialize_read_model_artifacts=False,
            )
        except Exception:
            continue
        if not isinstance(progress, Mapping):
            continue
        snapshots[study_id] = _snapshot_from_progress(progress)
    return snapshots


def _snapshot_from_progress(progress: Mapping[str, Any]) -> dict[str, Any]:
    snapshot: dict[str, Any] = {}
    for key in (
        "quest_id",
        "generated_at",
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "human_gate",
        "terminal_closeout_consumed",
        "provider_admission_pending_count",
        "provider_admission_candidates",
    ):
        if key not in progress:
            continue
        value = progress.get(key)
        if isinstance(value, Mapping):
            snapshot[key] = dict(value)
        elif isinstance(value, list):
            snapshot[key] = [
                dict(item) if isinstance(item, Mapping) else item
                for item in value
            ]
        else:
            snapshot[key] = value
    return snapshot


def _delta(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, bool]:
    before_work_unit = _mapping(before.get("current_work_unit"))
    after_work_unit = _mapping(after.get("current_work_unit"))
    before_envelope = _mapping(before.get("current_execution_envelope"))
    after_envelope = _mapping(after.get("current_execution_envelope"))
    running_attempt = _mapping(after.get("running_provider_attempt"))
    return {
        "current_work_unit_changed": before_work_unit != after_work_unit,
        "current_execution_envelope_changed": before_envelope != after_envelope,
        "provider_admission_pending_changed": before.get("provider_admission_pending_count")
        != after.get("provider_admission_pending_count"),
        "running_provider_attempt_started": (
            _non_empty_text(after_work_unit.get("status")) == "running_provider_attempt"
            or _non_empty_text(after_envelope.get("state_kind")) == "running_provider_attempt"
            or running_attempt.get("running_provider_attempt") is True
        ),
        "typed_blocker_observed": bool(_mapping(after.get("typed_blocker"))),
        "human_gate_observed": bool(_mapping(after.get("human_gate"))),
        "terminal_closeout_consumed": bool(after.get("terminal_closeout_consumed")),
    }


__all__ = [
    "attach_apply_readback_summary",
    "capture_apply_readback_snapshot",
]
