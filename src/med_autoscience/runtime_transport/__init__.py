from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "DEFAULT_DAEMON_TIMEOUT_SECONDS",
    "artifact_complete_quest",
    "artifact_interact",
    "chat_quest",
    "complete_turn_and_normalize",
    "create_quest",
    "inspect_turn_lifecycle",
    "pause_quest",
    "resolve_daemon_url",
    "resume_quest",
    "schedule_turn",
    "stop_quest",
    "update_quest_startup_context",
]


def __getattr__(name: str) -> Any:
    if name not in __all__:
        raise AttributeError(name)
    module = import_module("med_autoscience.runtime_transport.mas_runtime_core")
    value = getattr(module, name)
    globals()[name] = value
    return value
