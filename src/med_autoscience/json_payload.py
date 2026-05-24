from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePath
from typing import Any


def json_safe(value: Any) -> Any:
    if isinstance(value, PurePath):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [json_safe(item) for item in value]
    if isinstance(value, frozenset | set):
        return [json_safe(item) for item in sorted(value, key=str)]
    return value
