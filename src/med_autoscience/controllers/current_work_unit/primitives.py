from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    text_value = str(value or "").strip()
    return text_value or None


def text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text_value = text(value)
        return [text_value] if text_value is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text_value = text(item)
        if text_value is not None and text_value not in result:
            result.append(text_value)
    return result


def first_text(items: Sequence[str]) -> str | None:
    return items[0] if items else None


__all__ = [
    "first_text",
    "mapping",
    "text",
    "text_items",
]
