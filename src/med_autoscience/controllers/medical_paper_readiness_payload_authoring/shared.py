from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def text(value: object) -> str:
    return str(value or "").strip()


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def mapping_list(value: object) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def text_list(value: object) -> list[str]:
    return [text(item) for item in list_items(value) if text(item)]


def list_items(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def slug(value: object) -> str:
    rendered = "".join(char if char.isalnum() else "-" for char in text(value).lower()).strip("-")
    while "--" in rendered:
        rendered = rendered.replace("--", "-")
    return rendered or "ref"
