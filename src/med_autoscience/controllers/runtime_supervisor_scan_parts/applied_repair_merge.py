from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import runtime_facts


def merge_runtime_fact(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    apply_result: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not _applied(apply_result):
        return dict(status), dict(progress)
    resume_result = _mapping(_mapping(apply_result).get("resume_result"))
    active_run_id = runtime_facts.active_run_id(resume_result, progress)
    runtime_liveness = _mapping(resume_result.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    worker_running = runtime_audit.get("worker_running") is True or runtime_liveness.get("worker_running") is True
    merged_status = dict(status)
    if text := _text(resume_result.get("quest_status")):
        merged_status["quest_status"] = text
    if text := _text(resume_result.get("decision")):
        merged_status["decision"] = text
    if text := _text(resume_result.get("reason")):
        merged_status["reason"] = text
    for key in (
        "controller_work_unit_evidence_adoption",
        "controller_decision_authorization_deduped",
        "controller_work_unit_next_route",
    ):
        value = resume_result.get(key)
        if isinstance(value, Mapping):
            merged_status[key] = dict(value)
    if active_run_id is not None:
        merged_status["active_run_id"] = active_run_id
        merged_status["runtime_liveness_audit"] = {
            **_mapping(merged_status.get("runtime_liveness_audit")),
            "active_run_id": active_run_id,
            "runtime_audit": {
                **_mapping(_mapping(merged_status.get("runtime_liveness_audit")).get("runtime_audit")),
                "active_run_id": active_run_id,
                "worker_running": worker_running,
            },
        }
        runtime_health = _mapping(merged_status.get("runtime_health_snapshot"))
        runtime_health.update(
            {
                "active_run_id": active_run_id,
                "observed_quest_state": {
                    "quest_status": _text(merged_status.get("quest_status")),
                    "decision": _text(merged_status.get("decision")),
                    "reason": _text(merged_status.get("reason")),
                },
                "canonical_runtime_action": "continue_supervising_runtime",
                "attempt_state": "recovering",
                "retry_budget_remaining": _runtime_repair_retry_budget(runtime_health),
                "blocking_reasons": [
                    reason
                    for reason in _string_items(runtime_health.get("blocking_reasons"))
                    if reason != "runtime_recovery_retry_budget_exhausted"
                ],
            }
        )
        merged_status["runtime_health_snapshot"] = runtime_health
    merged_progress = dict(progress)
    if active_run_id is not None:
        merged_progress["supervision"] = {
            **_mapping(merged_progress.get("supervision")),
            "active_run_id": active_run_id,
            "health_status": "recovering",
        }
    return merged_status, merged_progress


def _applied(value: Mapping[str, Any] | None) -> bool:
    return value is not None and _text(value.get("dispatch_status")) == "applied"


def _runtime_repair_retry_budget(runtime_health: Mapping[str, Any]) -> int:
    remaining = runtime_health.get("retry_budget_remaining")
    if isinstance(remaining, int) and remaining > 0:
        return remaining
    return 3


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None

