from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPAIR_LIFECYCLE_RELATIVE_PATH = Path("artifacts/autonomy/repair_lifecycle/latest.json")


def read_ai_repair_lifecycle(*, study_root: Path) -> dict[str, Any] | None:
    path = Path(study_root).expanduser().resolve() / REPAIR_LIFECYCLE_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) else None
