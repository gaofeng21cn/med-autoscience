from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _compact_non_null_mapping(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}


def _paper_mission_sorted_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in sorted(value)
        if isinstance(key, str) and value.get(key) is not None
    }


def _stable_sha256(value: Mapping[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _load_json_object(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_optional_json_object(path: object) -> dict[str, Any] | None:
    text = _optional_text(path)
    return _load_json_object(Path(text)) if text is not None else None


def _parse_json_object(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _first_mapping(*values: dict[str, Any]) -> dict[str, Any]:
    for value in values:
        if value:
            return value
    return {}


def _compact_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item is not None}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    items: list[str] = []
    for item in value:
        text = _optional_text(item)
        if text is not None:
            items.append(text)
    return items


def _dedupe_optional_texts(values: list[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = _optional_text(value)
        if text is None or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _optional_text(value)
        if text is not None:
            return text
    return None


def _first_text_item(value: object) -> str | None:
    if isinstance(value, (list, tuple, set)):
        for item in value:
            text = _optional_text(item)
            if text is not None:
                return text
    return _optional_text(value)


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _slug(value: str) -> str:
    chars = [char.lower() if char.isalnum() else "-" for char in value]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug[:64] or "paper-mission"


__all__ = [
    "_compact_mapping",
    "_compact_non_null_mapping",
    "_dedupe_optional_texts",
    "_first_mapping",
    "_first_text",
    "_first_text_item",
    "_is_relative_to",
    "_load_json_object",
    "_load_optional_json_object",
    "_mapping",
    "_mapping_list",
    "_optional_text",
    "_paper_mission_sorted_mapping",
    "_parse_json_object",
    "_slug",
    "_stable_sha256",
    "_text_list",
]
