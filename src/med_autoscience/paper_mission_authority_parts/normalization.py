from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def normalized_path(value: str) -> str:
    path = Path(value).as_posix().lower()
    return path.replace("\\", "/")


def path_matches(path: str, parts: tuple[str, ...]) -> bool:
    position = 0
    for part in parts:
        found = path.find(part, position)
        if found < 0:
            return False
        position = found + len(part)
    return True


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def first_mapping(*values: Mapping[str, Any]) -> dict[str, Any]:
    for value in values:
        mapped = mapping(value)
        if mapped:
            return mapped
    return {}


def first_text(*values: object) -> str | None:
    for value in values:
        text = text_or_none(value)
        if text is not None:
            return text
    return None


def text_list(value: object) -> list[str]:
    if isinstance(value, str):
        items: Sequence[object] = [value]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        items = value
    else:
        items = []
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = text_or_none(item)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def dedupe(values: Sequence[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = text_or_none(value)
        if text is None or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def text_or_none(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "dedupe",
    "first_mapping",
    "first_text",
    "mapping",
    "normalized_path",
    "path_matches",
    "text_list",
    "text_or_none",
]
