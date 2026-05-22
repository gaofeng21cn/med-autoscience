from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any


def read_json_object(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def blockers(*items: tuple[str, bool]) -> list[str]:
    return [name for name, blocked in items if blocked]


def source_ref_objects(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            ref = text(item.get("source_ref"))
            if ref:
                refs.append(ref)
    return refs


def string_refs(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [str(item) for item in value if text(item)]


def dedupe_text(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = text(value)
        if item is None or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
