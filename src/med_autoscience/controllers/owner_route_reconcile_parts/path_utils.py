from __future__ import annotations

from pathlib import Path


def path_or_none(value: object) -> Path | None:
    text = str(value or "").strip()
    return Path(text).expanduser().resolve() if text else None


__all__ = ["path_or_none"]
