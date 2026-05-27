from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = non_empty_text(value)
        if text is not None:
            return text
    return None


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def first_mapping(*values: object) -> dict[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return dict(value)
    return {}


def first_non_empty_list(*values: object) -> list[Any]:
    for value in values:
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            items = list(value)
            if items:
                return items
    return []


def mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def projection_source_refs(value: Mapping[str, Any]) -> list[str]:
    return dedupe_refs(
        [
            *string_list(value.get("source_refs")),
            *string_list(value.get("evidence_refs")),
            non_empty_text(value.get("source_ref")),
            non_empty_text(value.get("receipt_ref")),
            non_empty_text(value.get("audit_ref")),
            non_empty_text(value.get("ref")),
        ]
    )


def receipt_refs(value: object) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        text = non_empty_text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping):
        refs.extend(projection_source_refs(value))
        for key in ("refs", "receipt_refs", "writeback_receipt_refs"):
            refs.extend(receipt_refs(value.get(key)))
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        for item in value:
            refs.extend(receipt_refs(item))
    return dedupe_refs(refs)


def dedupe_refs(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = non_empty_text(value)
        if text is not None and text not in result:
            result.append(text)
    return result
