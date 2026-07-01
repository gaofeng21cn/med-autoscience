from __future__ import annotations

from typing import Any, Mapping


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None
