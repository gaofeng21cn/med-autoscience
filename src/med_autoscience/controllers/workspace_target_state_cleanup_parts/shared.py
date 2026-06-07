from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


def path_present(path: Path) -> bool:
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    return True


def logical_abs(path: Path) -> Path:
    return path.expanduser().absolute()


def path_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    return "file"


def add_symlink_target(payload: dict[str, Any], source: Path) -> None:
    if not source.is_symlink():
        return
    try:
        payload["symlink_target"] = os.readlink(source)
    except OSError:
        return


def decision_counts(actions: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for action in actions:
        decision = str(action.get("decision") or "unknown")
        counts[decision] = counts.get(decision, 0) + 1
    return counts


def relative_ref(workspace_root: Path, path: Path) -> str:
    logical_root = logical_abs(workspace_root)
    logical_path = logical_abs(path)
    try:
        return logical_path.relative_to(logical_root).as_posix()
    except ValueError:
        return str(logical_path)


def dedupe(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def blocker_slug(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z]+", "_", text).strip("_").lower() or "root"

