from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers.owner_route_reconcile_parts.owner_tokens import owner_token


def text(value: object) -> str | None:
    item = str(value or "").strip()
    return item or None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def clear_current_controller_owner_handoff(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    read_json_object: Callable[[Path], dict[str, Any] | None],
    write_json: Callable[[Path, Mapping[str, Any]], None] | None = None,
    append_json_line: Callable[[Path, Mapping[str, Any]], None] | None = None,
    source: str,
) -> dict[str, Any]:
    _ = (write_json, append_json_line)
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
        "cleared": True,
        "cleared_keys": clearable_keys,
        "path": str(runtime_state_path),
        "runtime_state_mutated": False,
        "events_jsonl_mutated": False,
        "delegated_runtime_owner": "one-person-lab",
        "source": source,
        "study_id": study_id,
        "quest_id": text(runtime_state.get("quest_id")) or quest_id,
        "clear_reason": "current_controller_owner_handoff_redrive",
        "proposed_runtime_state": {
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "runtime_platform_repair_redrive",
            "active_run_id": None,
            "worker_running": False,
            "same_fingerprint_auto_turn_count": 0,
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }


__all__ = ["clear_current_controller_owner_handoff"]
