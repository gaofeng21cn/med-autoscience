from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def mark_existing_pending_user_message_handoff(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    source: str,
    runtime_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if runtime_state is None:
        return {"marked": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    pending_count = int(runtime_state.get("pending_user_message_count") or 0)
    if pending_count <= 0:
        return {"marked": False, "reason": "pending_user_messages_missing", "path": str(runtime_state_path)}
    clearable_keys: list[str] = []
    for key in (
        "last_controller_decision_authorization",
        "control_intent_lifecycle",
        "last_live_controller_reroute_restart",
        "retry_state",
        "last_stage_fingerprint",
        "last_stage_fingerprint_at",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ):
        if key in runtime_state:
            clearable_keys.append(key)
    return {
        "marked": True,
        "pending_user_message_count": pending_count,
        "cleared_keys": clearable_keys,
        "path": str(runtime_state_path),
        "runtime_state_mutated": False,
        "events_jsonl_mutated": False,
        "delegated_runtime_owner": "one-person-lab",
        "source": source,
        "study_id": study_id,
        "quest_id": _text(runtime_state.get("quest_id")) or quest_id,
        "clear_reason": "existing_pending_user_message_redrive",
        "proposed_runtime_state": {
            "continuation_policy": "auto",
            "continuation_anchor": "user_message_queue",
            "continuation_reason": "opl_owner_route_resume_existing_pending_user_message",
            "active_run_id": None,
            "worker_running": False,
            "same_fingerprint_auto_turn_count": 0,
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }


def blocked_turn_closeout_clear_result(clear_result: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(clear_result, Mapping):
        return None
    cleared_keys = _string_items(clear_result.get("cleared_keys"))
    if not any(key in {"blocked_turn_closeout", "last_liveness_reconcile_reason"} for key in cleared_keys):
        return None
    return {
        "cleared": True,
        "cleared_keys": [key for key in cleared_keys if key in {"blocked_turn_closeout", "last_liveness_reconcile_reason"}],
        "path": _text(clear_result.get("path")),
    }


__all__ = ["blocked_turn_closeout_clear_result", "mark_existing_pending_user_message_handoff"]
