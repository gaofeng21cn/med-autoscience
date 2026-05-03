from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any
from uuid import uuid4


MDS_STAGE_TARGET_PREFIX = "deepscientist"


def _discover_mds_skill_roots(source_root: Path) -> list[tuple[str, Path]]:
    if not source_root.exists():
        return []
    discovered: list[tuple[str, Path]] = []
    for skill_md in sorted(source_root.glob("*/SKILL.md")):
        skill_id = skill_md.parent.name
        if skill_id.startswith("."):
            continue
        discovered.append((skill_id, skill_md.parent))
    return discovered


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.parent / f".{path.name}.tmp-{uuid4().hex}"
    temp_path.write_bytes(payload)
    temp_path.replace(path)


def _sync_file(source_path: Path, target_path: Path) -> None:
    payload = source_path.read_bytes()
    if target_path.exists():
        try:
            if target_path.read_bytes() == payload:
                return
        except OSError:
            pass
    _write_bytes_atomic(target_path, payload)


def _sync_tree(source_root: Path, target_root: Path) -> None:
    target_root.mkdir(parents=True, exist_ok=True)
    expected_paths: set[Path] = set()
    for source_path in sorted(source_root.rglob("*")):
        relative = source_path.relative_to(source_root)
        expected_paths.add(relative)
        target_path = target_root / relative
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        else:
            _sync_file(source_path, target_path)

    for target_path in sorted(target_root.rglob("*"), reverse=True):
        relative = target_path.relative_to(target_root)
        if relative in expected_paths:
            continue
        if target_path.is_dir():
            shutil.rmtree(target_path)
        else:
            target_path.unlink(missing_ok=True)


def _prune_stale_mds_targets(skills_root: Path, expected_names: set[str]) -> list[str]:
    pruned: list[str] = []
    for target_root in sorted(skills_root.glob(f"{MDS_STAGE_TARGET_PREFIX}-*"), reverse=True):
        if target_root.name in expected_names:
            continue
        if target_root.is_dir():
            shutil.rmtree(target_root)
        else:
            target_root.unlink(missing_ok=True)
        pruned.append(str(target_root))
    return pruned


def sync_mds_stage_skills(
    *,
    quest_root: Path | None,
    med_deepscientist_repo_root: Path | None,
    skill_ids: tuple[str, ...],
) -> dict[str, Any]:
    if quest_root is None or med_deepscientist_repo_root is None:
        return {
            "scope": "disabled",
            "target_root": None,
            "source_root": str(med_deepscientist_repo_root) if med_deepscientist_repo_root is not None else None,
            "overlay_skill_ids": list(skill_ids),
            "synced": [],
            "missing": [],
            "pruned": [],
            "synced_count": 0,
        }
    resolved_root = Path(quest_root).expanduser().resolve()
    source_root = Path(med_deepscientist_repo_root).expanduser().resolve() / "src" / "skills"
    skills_root = resolved_root / ".codex" / "skills"
    synced = []
    discovered = _discover_mds_skill_roots(source_root)
    expected_names: set[str] = set()
    for skill_id, source_skill_root in discovered:
        target_root = skills_root / f"{MDS_STAGE_TARGET_PREFIX}-{skill_id}"
        expected_names.add(target_root.name)
        _sync_tree(source_skill_root, target_root)
        synced.append(
            {
                "skill_id": skill_id,
                "target_root": str(target_root),
                "skill_path": str(target_root / "SKILL.md"),
                "source_root": str(source_skill_root),
                "source_skill_path": str(source_skill_root / "SKILL.md"),
            }
        )
    pruned = _prune_stale_mds_targets(skills_root, expected_names) if skills_root.exists() else []
    return {
        "scope": "quest",
        "target_root": str(skills_root),
        "source_root": str(source_root),
        "overlay_skill_ids": list(skill_ids),
        "synced": synced,
        "missing": [] if source_root.exists() else list(skill_ids),
        "pruned": pruned,
        "synced_count": len(synced),
    }
