from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import json
from pathlib import Path
from typing import Any

from med_autoscience.display_pack_resolver import get_pack_id, get_template_short_id


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _require_namespaced_registry_id(identifier: str, *, label: str) -> tuple[str, str]:
    try:
        pack_id = get_pack_id(identifier)
        short_id = get_template_short_id(identifier)
    except ValueError as exc:
        raise ValueError(f"{label} must be namespaced as '<pack_id>::<template_id>'") from exc
    return pack_id, short_id


def _read_bool_override(mapping: dict[str, Any], key: str, default: bool) -> bool:
    value = mapping.get(key)
    if isinstance(value, bool):
        return value
    return default


def _require_non_empty_string(value: object, *, label: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        raise ValueError(f"{label} must be non-empty")
    return normalized


def _require_numeric_value(value: object, *, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    return float(value)


def _require_non_negative_int(value: object, *, label: str, allow_zero: bool = True) -> int:
    numeric_value = _require_numeric_value(value, label=label)
    if not float(numeric_value).is_integer():
        raise ValueError(f"{label} must be an integer")
    normalized = int(numeric_value)
    if normalized < 0 or (normalized == 0 and not allow_zero):
        comparator = ">= 1" if not allow_zero else ">= 0"
        raise ValueError(f"{label} must be {comparator}")
    return normalized


def _format_percent_1dp(*, numerator: int, denominator: int) -> str:
    percent = (Decimal(numerator) * Decimal("100")) / Decimal(denominator)
    return f"{percent.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)}%"
