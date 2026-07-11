from __future__ import annotations

from importlib import import_module
from typing import Any

from med_autoscience.runtime_event_record import (
    RuntimeEventRecord,
    RuntimeEventRecordRef,
)
_LAZY_EXPORTS = {
    "QuestRuntimeSnapshot": ".quest_state",
    "StudyRuntimeArtifacts": ".study_runtime",
    "StudyRuntimeContext": ".study_runtime",
    "find_latest": ".quest_state",
    "find_latest_main_result_path": ".quest_state",
    "inspect_quest_runtime": ".quest_state",
    "iter_active_quests": ".quest_state",
    "load_runtime_state": ".quest_state",
    "persist_runtime_artifacts": ".study_runtime",
    "quest_status": ".quest_state",
    "read_recent_stdout_lines": ".quest_state",
    "read_runtime_event_record_ref": ".study_runtime",
    "resolve_active_stdout_path": ".quest_state",
    "resolve_study_runtime_context": ".study_runtime",
    "write_launch_report": ".study_runtime",
    "write_runtime_binding": ".study_runtime",
    "write_runtime_event_record": ".study_runtime",
}

__all__ = [
    "RuntimeEventRecord",
    "RuntimeEventRecordRef",
    *_LAZY_EXPORTS,
]


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
