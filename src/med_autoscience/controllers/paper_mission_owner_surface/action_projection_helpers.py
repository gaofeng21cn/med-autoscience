from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def string_items(value: object) -> list[str]:
    if isinstance(value, str):
        normalized = value.strip()
        return [normalized] if normalized else []
    if not isinstance(value, list | tuple | set):
        return []
    return list(dict.fromkeys(normalized for item in value if (normalized := text(item)) is not None))


def path(value: str | None) -> Path | None:
    return Path(value) if value is not None else None


__all__ = [
    "mapping",
    "path",
    "string_items",
    "text",
]
