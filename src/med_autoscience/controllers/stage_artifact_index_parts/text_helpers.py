from __future__ import annotations

from typing import Any, Mapping


def mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def required_text(value: object, field: str) -> str:
    text = text_or_none(value)
    if text is None:
        raise ValueError(f"missing required text field: {field}")
    return text


def text_or_none(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = text_or_none(item)
        if text is not None:
            result.append(text)
    return result
