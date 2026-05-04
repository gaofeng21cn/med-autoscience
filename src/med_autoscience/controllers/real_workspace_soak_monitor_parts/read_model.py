from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.real_workspace_soak_monitor_parts.shared import (
    _sequence,
    _text,
    _truthy_bool,
)


def blocked_reason_summary(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for study in studies:
        reason = _text(study.get("blocked_reason"), "")
        gaps = [
            str(gap)
            for gap in _sequence(study.get("blocking_gaps")) or _sequence(study.get("missing_gaps"))
            if _text(gap, "")
        ]
        if not reason and not gaps:
            continue
        summary.append(
            {
                "study_id": _text(study.get("study_id")),
                "status": _text(study.get("status")),
                "blocked_reason": reason,
                "gaps": gaps,
            }
        )
    return summary


def route_decision_summary(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "route_action": _text(study.get("route_action"), "continue"),
            "result_strength": _text(study.get("result_strength"), "adequate"),
            "next_action": _text(study.get("next_action")),
            "reason": _text(study.get("route_reason"), ""),
        }
        for study in studies
        if _text(study.get("study_id"), "") != "multistudy_matrix"
    ]


def readiness_drift_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    drift: list[dict[str, Any]] = []
    for study in studies:
        previous = _text(study.get("previous_readiness_status"), "")
        current = _text(study.get("readiness_status"), "")
        if not previous or not current or previous == current:
            continue
        drift.append(
            {
                "study_id": _text(study.get("study_id")),
                "previous_status": previous,
                "current_status": current,
                "drift": f"{previous}->{current}",
                "last_green_at": _text(study.get("last_green_at"), ""),
                "last_green_scan_id": _text(study.get("last_green_scan_id"), ""),
            }
        )
    return drift


def route_decision_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "study_archetype": _text(study.get("study_archetype")),
            "route_action": _text(study.get("route_action"), "continue"),
            "reason": _text(study.get("route_reason"), ""),
            "result_strength": _text(study.get("result_strength"), "adequate"),
            "next_action": "stop_loss"
            if _truthy_bool(study.get("stop_loss_triggered"))
            else _text(study.get("next_action")),
        }
        for study in studies
        if _text(study.get("study_id"), "") != "multistudy_matrix"
    ]


def stop_loss_trigger_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    triggers: list[dict[str, Any]] = []
    for study in studies:
        if not _truthy_bool(study.get("stop_loss_triggered")):
            continue
        triggers.append(
            {
                "study_id": _text(study.get("study_id")),
                "route_action": _text(study.get("route_action"), "continue"),
                "result_strength": _text(study.get("result_strength"), "adequate"),
                "blocked_reason": _text(study.get("blocked_reason"), ""),
            }
        )
    return triggers


def proof_observation_read_model(studies: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "revision_reopen_seen": bool(study.get("revision_reopen_seen")),
            "runtime_recovery_seen": bool(study.get("runtime_recovery_seen")),
            "finalize_rebuild_seen": bool(study.get("finalize_rebuild_seen")),
        }
        for study in studies
        if _text(study.get("study_id"), "") != "multistudy_matrix"
    ]


def soak_read_model(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "readiness_drift": readiness_drift_read_model(studies),
        "blocked_reasons": blocked_reason_summary(studies),
        "route_decisions": route_decision_read_model(studies),
        "stop_loss_triggers": stop_loss_trigger_read_model(studies),
        "proof_observations": proof_observation_read_model(studies),
        "authority": {
            "writes_runtime_owned_surfaces": False,
            "can_authorize_quality": False,
            "can_authorize_submission": False,
            "can_authorize_finalize": False,
        },
    }
