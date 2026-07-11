from __future__ import annotations

from importlib import import_module
from typing import Any

_LAZY_EXPORTS = {
    "QuestRuntimeSnapshot": ".quest_state",
    "find_latest": ".quest_state",
    "find_latest_main_result_path": ".quest_state",
    "inspect_quest_runtime": ".quest_state",
    "iter_active_quests": ".quest_state",
    "load_runtime_state": ".quest_state",
    "quest_status": ".quest_state",
    "read_recent_stdout_lines": ".quest_state",
    "resolve_active_stdout_path": ".quest_state",
}

__all__ = [
    *_LAZY_EXPORTS,
]


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
