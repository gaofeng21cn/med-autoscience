from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def mark_existing_pending_user_message_redrive(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    source: str,
) -> dict[str, Any]:
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"marked": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    pending_count = int(runtime_state.get("pending_user_message_count") or 0)
    if pending_count <= 0:
        return {"marked": False, "reason": "pending_user_messages_missing", "path": str(runtime_state_path)}
    runtime_state["quest_id"] = _text(runtime_state.get("quest_id")) or quest_id
    runtime_state["active_run_id"] = None
    runtime_state["worker_running"] = False
    runtime_state["continuation_policy"] = "auto"
    runtime_state["continuation_anchor"] = "user_message_queue"
    runtime_state["continuation_reason"] = "runtime_platform_repair_resume_existing_pending_user_message"
    runtime_state["continuation_updated_at"] = _utc_now()
    runtime_state["same_fingerprint_auto_turn_count"] = 0
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
    runtime_state["last_runtime_platform_repair"] = {
        "study_id": study_id,
        "quest_id": quest_id,
        "source": source,
        "clear_reason": "existing_pending_user_message_redrive",
        "cleared_keys": cleared_keys,
        "pending_user_message_count": pending_count,
        "applied_at": _utc_now(),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }
    _write_json(runtime_state_path, runtime_state)
    _append_json_line(
        runtime_state_path.parent / "events.jsonl",
        {
            "event_id": f"mas-runtime-platform-repair::{study_id}::{_utc_now()}",
            "type": "mas.runtime_platform_repair",
            "study_id": study_id,
            "quest_id": quest_id,
            "source": source,
            "clear_reason": "existing_pending_user_message_redrive",
            "cleared_keys": cleared_keys,
            "pending_user_message_count": pending_count,
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "created_at": _utc_now(),
        },
    )
    return {
        "marked": True,
        "pending_user_message_count": pending_count,
        "cleared_keys": cleared_keys,
        "path": str(runtime_state_path),
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
