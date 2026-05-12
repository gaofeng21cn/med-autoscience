from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def write_stable_json(path: Path, payload: Any, *, sort_keys: bool = False) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=sort_keys) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(target)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
