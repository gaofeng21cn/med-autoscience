from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def pending_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("pending_user_message_count") or 0)
    except (TypeError, ValueError):
        return 0


__all__ = ["pending_count"]
