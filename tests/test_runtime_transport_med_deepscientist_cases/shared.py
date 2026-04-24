from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
from urllib import error

import pytest


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _native_runtime_event_payload(*, quest_id: str, artifact_path: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": f"runtime-event::{quest_id}::runtime_control_applied::2026-04-11T00:00:00+00:00",
        "quest_id": quest_id,
        "emitted_at": "2026-04-11T00:00:00+00:00",
        "event_source": "daemon_app",
        "event_kind": "runtime_control_applied",
        "summary_ref": f"quest:{quest_id}:runtime_control_applied",
        "status_snapshot": {
            "quest_status": "paused",
            "display_status": "paused",
            "active_run_id": "run-native",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "stop_reason": "user_pause_requested",
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "paused_by_controller",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "outer_loop_input": {
            "quest_status": "paused",
            "display_status": "paused",
            "active_run_id": "run-native",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "stop_reason": "user_pause_requested",
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "paused_by_controller",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "artifact_path": str(artifact_path),
        "summary": "runtime paused by controller",
    }






































































































