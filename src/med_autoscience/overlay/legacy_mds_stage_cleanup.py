from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any


LEGACY_MDS_STAGE_TARGET_PREFIX = "deepscientist"


def cleanup_legacy_mds_stage_skills(*, quest_root: Path | None) -> dict[str, Any]:
    if quest_root is None:
        return {
            "scope": "disabled",
            "target_root": None,
            "removed": [],
            "removed_count": 0,
        }

    resolved_root = Path(quest_root).expanduser().resolve()
    skills_root = resolved_root / ".codex" / "skills"
    removed: list[str] = []
    for target_root in sorted(skills_root.glob(f"{LEGACY_MDS_STAGE_TARGET_PREFIX}-*"), reverse=True):
        if target_root.is_dir():
            shutil.rmtree(target_root)
        else:
            target_root.unlink(missing_ok=True)
        removed.append(str(target_root))

    return {
        "scope": "quest",
        "target_root": str(skills_root),
        "removed": removed,
        "removed_count": len(removed),
    }
