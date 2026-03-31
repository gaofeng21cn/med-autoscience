from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import quest_state


def find_latest(paths: list[Path]) -> Path | None:
    return quest_state.find_latest(paths)


def load_runtime_state(quest_root: Path) -> dict[str, Any]:
    return quest_state.load_runtime_state(quest_root)


def quest_status(quest_root: Path) -> str:
    return quest_state.quest_status(quest_root)


def iter_active_quests(runtime_root: Path) -> list[Path]:
    return quest_state.iter_active_quests(runtime_root)


def find_latest_main_result(quest_root: Path) -> Path:
    return quest_state.find_latest_main_result(quest_root)


def resolve_active_stdout_path(*, quest_root: Path, runtime_state: dict[str, Any]) -> Path | None:
    return quest_state.resolve_active_stdout_path(quest_root=quest_root, runtime_state=runtime_state)


def read_recent_stdout_lines(stdout_path: Path | None, *, limit: int = 40) -> list[str]:
    return quest_state.read_recent_stdout_lines(stdout_path, limit=limit)
