from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.stable_json import write_stable_json


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    write_stable_json(path, payload)


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return items
