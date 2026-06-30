from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def compact_mapping(payload: Mapping[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in keys:
        if key in payload:
            result[key] = payload[key]
    return result


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [mapping(item) for item in value if isinstance(item, Mapping)]


def first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        mapped = mapping(value)
        if mapped:
            return mapped
    return {}


def text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def text_items(value: object) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, Iterable):
        return []
    items: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return items


def first_text(values: Iterable[object]) -> str | None:
    for value in values:
        item = text(value)
        if item:
            return item
    return None


def first_non_empty(*values: object) -> str | None:
    return first_text(values)


def dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def int_or_zero(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    return 0
