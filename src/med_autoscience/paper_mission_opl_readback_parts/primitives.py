from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def study_relative_ref(*, study_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(study_root.resolve()))
    except ValueError:
        return str(path.resolve())


def workspace_root_for_study_root(study_root: Path) -> Path | None:
    parent = study_root.parent
    if parent.name != "studies":
        return None
    return parent.parent


def workspace_relative_ref(*, workspace_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        return str(path.resolve())


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def first_mapping(*values: Mapping[str, Any]) -> dict[str, Any]:
    for value in values:
        if value:
            return dict(value)
    return {}


def text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := text_value(item)) is not None]


def first_text(*values: object) -> str | None:
    for value in values:
        text = text_value(value)
        if text is not None:
            return text
    return None


def text_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
