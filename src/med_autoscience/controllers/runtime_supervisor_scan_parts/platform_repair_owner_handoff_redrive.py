from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text(value: object) -> str | None:
    item = str(value or "").strip()
    return item or None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def owner_token(value: object) -> str | None:
    item = text(value)
    if item is None:
        return None
    return item.lower().replace("/", "_").replace("-", "_")


def clear_current_controller_owner_handoff(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    read_json_object: Callable[[Path], dict[str, Any] | None],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_json_line: Callable[[Path, Mapping[str, Any]], None],
    source: str,
) -> dict[str, Any]:
    runtime_state = read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"cleared": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return {"cleared": False, "reason": "pending_user_messages_present", "path": str(runtime_state_path)}
    blocked_closeout = mapping(runtime_state.get("blocked_turn_closeout"))
    if text(runtime_state.get("continuation_reason")) != "blocked_turn_closeout_waiting_for_owner":
        return {"cleared": False, "reason": "blocked_turn_closeout_wait_not_found", "path": str(runtime_state_path)}
    if owner_token(blocked_closeout.get("next_owner")) != "mas_controller":
        return {"cleared": False, "reason": "mas_controller_owner_handoff_not_found", "path": str(runtime_state_path)}

    cleared_keys: list[str] = []
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
            runtime_state.pop(key, None)
            cleared_keys.append(key)
    runtime_state["quest_id"] = text(runtime_state.get("quest_id")) or quest_id
    runtime_state["active_run_id"] = None
    runtime_state["worker_running"] = False
    runtime_state["continuation_policy"] = "auto"
    runtime_state["continuation_anchor"] = "decision"
    runtime_state["continuation_reason"] = "runtime_platform_repair_redrive"
    runtime_state["continuation_updated_at"] = utc_now()
    runtime_state["same_fingerprint_auto_turn_count"] = 0
    runtime_state["last_runtime_platform_repair"] = {
        "study_id": study_id,
        "quest_id": quest_id,
        "source": source,
        "clear_reason": "current_controller_owner_handoff_redrive",
        "cleared_keys": cleared_keys,
        "applied_at": utc_now(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }
    write_json(runtime_state_path, runtime_state)
    append_json_line(
        runtime_state_path.parent / "events.jsonl",
        {
            "event_id": f"mas-runtime-platform-repair::{study_id}::{utc_now()}",
            "type": "mas.runtime_platform_repair",
            "study_id": study_id,
            "quest_id": quest_id,
            "source": source,
            "clear_reason": "current_controller_owner_handoff_redrive",
            "cleared_keys": cleared_keys,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "created_at": utc_now(),
        },
    )
    return {"cleared": True, "cleared_keys": cleared_keys, "path": str(runtime_state_path)}


__all__ = ["clear_current_controller_owner_handoff"]
