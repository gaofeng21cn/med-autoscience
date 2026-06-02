from __future__ import annotations

from typing import Any


def execution_summary(*, study_id: str, study_executions: list[dict[str, Any]]) -> dict[str, Any]:
    selected_dispatch_count = len(study_executions)
    executed_count = sum(item.get("execution_status") in {"executed", "handoff_ready"} for item in study_executions)
    blocked_count = sum(item.get("execution_status") == "blocked" for item in study_executions)
    repeat_suppressed_count = sum(item.get("execution_status") == "repeat_suppressed" for item in study_executions)
    dry_run_count = sum(item.get("execution_status") == "dry_run" for item in study_executions)
    codex_dispatch_count = sum(item.get("will_start_llm") is True for item in study_executions)
    return {
        "study_id": study_id,
        "selected_dispatch_count": selected_dispatch_count,
        "executed_count": executed_count,
        "blocked_count": blocked_count,
        "repeat_suppressed_count": repeat_suppressed_count,
        "dry_run_count": dry_run_count,
        "codex_dispatch_count": codex_dispatch_count,
        "suppressed_dispatch_count": sum(
            item.get("execution_status") in {"repeat_suppressed", "blocked"} for item in study_executions
        ),
        "zero_dispatch_reason": "no_selected_dispatch_for_requested_action_types"
        if selected_dispatch_count == 0
        else None,
        "action_fingerprints": list(
            dict.fromkeys(item.get("action_fingerprint") for item in study_executions if item.get("action_fingerprint"))
        ),
        "execution_statuses": [item.get("execution_status") for item in study_executions],
    }


__all__ = ["execution_summary"]
