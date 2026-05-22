from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any


def dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = " ".join(str(value).strip().split())
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        item_text = text(item)
        if item_text is not None:
            result.append(item_text)
    return result


def text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if not stripped or stripped.lower() in {"none", "null", "unknown"}:
        return None
    return stripped


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "dedupe",
    "mapping",
    "mapping_list",
    "string_list",
    "text",
    "utc_now",
]
