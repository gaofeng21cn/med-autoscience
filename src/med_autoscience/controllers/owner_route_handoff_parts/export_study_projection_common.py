from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    value_text = str(value or "").strip()
    return value_text or None


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


__all__ = [
    "mapping",
    "read_json_object",
    "text",
    "workspace_relative",
]
