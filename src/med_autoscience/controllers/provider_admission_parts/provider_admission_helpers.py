from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def first_text(value: object) -> str | None:
    for item in text_items(value):
        return item
    return None


def non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
