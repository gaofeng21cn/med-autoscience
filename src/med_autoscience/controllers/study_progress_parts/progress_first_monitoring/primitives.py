from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _compact_mapping(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in keys if key in value}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[object]:
    return list(value) if isinstance(value, list | tuple) else []


def _numeric(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return _dedupe_text(value)


def _dedupe_text(values: list[object] | tuple[object, ...] | set[object]) -> list[str]:
    result: list[str] = []
    for item in values:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _first_text(value: object) -> str | None:
    items = _text_list(value)
    return items[0] if items else _text(value)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return bool(value)
