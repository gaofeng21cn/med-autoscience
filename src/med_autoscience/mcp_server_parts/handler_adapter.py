from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, TypeAlias


ToolHandler: TypeAlias = Callable[[dict[str, Any]], dict[str, Any]]


def require_string(arguments: dict[str, Any], key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def optional_bool(arguments: dict[str, Any], key: str, *, default: bool = False) -> bool:
    value = arguments.get(key, default)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def optional_int(arguments: dict[str, Any], key: str) -> int | None:
    value = arguments.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def optional_float(arguments: dict[str, Any], key: str) -> float | None:
    value = arguments.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be a number")
    return float(value)


def optional_string(arguments: dict[str, Any], key: str, *, default: str) -> str:
    value = arguments.get(key, default)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def optional_path(arguments: dict[str, Any], key: str) -> Path | None:
    value = arguments.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string when provided")
    return Path(value)


def optional_mapping(value: Any, *, field_name: str = "authority_snapshot") -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be an object when provided")
    return value


def require_path_list(arguments: dict[str, Any], key: str, *, mode: str) -> list[Path]:
    values = arguments.get(key)
    if not isinstance(values, list) or not values:
        raise ValueError(f"{key} must be a non-empty list for {mode}")
    paths: list[Path] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} entries must be non-empty strings")
        paths.append(Path(value))
    return paths


def call_mode_handler(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    handlers: dict[str, ToolHandler],
) -> dict[str, Any]:
    mode = require_string(arguments, "mode")
    handler = handlers.get(mode)
    if handler is None:
        raise ValueError(f"Unsupported {tool_name} mode: {mode}")
    return handler(arguments)
