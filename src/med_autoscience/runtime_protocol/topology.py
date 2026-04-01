from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PaperRootContext:
    paper_root: Path
    worktree_root: Path
    quest_root: Path
    study_id: str
    study_root: Path


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def resolve_worktree_root_from_paper_root(paper_root: Path) -> Path:
    resolved = _resolve_path(paper_root)
    if resolved.name != "paper":
        raise ValueError(f"paper_root must end with /paper: {paper_root}")
    worktree_root = resolved.parent
    resolve_quest_root_from_worktree_root(worktree_root)
    return worktree_root


def resolve_quest_root_from_worktree_root(worktree_root: Path) -> Path:
    resolved = _resolve_path(worktree_root)
    if resolved.parent.name != "worktrees" or resolved.parent.parent.name != ".ds":
        raise ValueError(f"worktree_root is not under a MedDeepScientist quest worktree layout: {worktree_root}")
    return resolved.parent.parent.parent


def resolve_study_id_from_worktree_root(worktree_root: Path) -> str:
    resolved_worktree_root = _resolve_path(worktree_root)
    quest_yaml_path = resolved_worktree_root / "quest.yaml"
    if not quest_yaml_path.exists():
        raise FileNotFoundError(f"missing worktree quest.yaml: {quest_yaml_path}")
    payload = _load_yaml_mapping(quest_yaml_path)
    study_id = payload.get("quest_id")
    if not isinstance(study_id, str) or not study_id.strip():
        raise ValueError(f"missing string quest_id in {quest_yaml_path}")
    return study_id.strip()


def _resolve_workspace_root_from_quest_root(quest_root: Path) -> Path:
    resolved = _resolve_path(quest_root)
    if (
        resolved.parent.name != "quests"
        or resolved.parent.parent.name != "runtime"
        or resolved.parent.parent.parent.name != "med-deepscientist"
        or resolved.parent.parent.parent.parent.name != "ops"
    ):
        raise ValueError(f"quest_root is not under an ops/med-deepscientist/runtime/quests layout: {quest_root}")
    return resolved.parent.parent.parent.parent.parent


def _resolve_study_binding(paper_root: Path) -> tuple[Path, Path, Path, str, Path]:
    resolved_paper_root = _resolve_path(paper_root)
    worktree_root = resolve_worktree_root_from_paper_root(resolved_paper_root)
    quest_root = resolve_quest_root_from_worktree_root(worktree_root)
    study_id = resolve_study_id_from_worktree_root(worktree_root)
    workspace_root = _resolve_workspace_root_from_quest_root(quest_root)
    study_root = workspace_root / "studies" / study_id
    if not (study_root / "study.yaml").exists():
        raise FileNotFoundError(f"unable to resolve studies root for `{study_id}` from {paper_root}")
    return resolved_paper_root, worktree_root, quest_root, study_id, study_root


def resolve_study_root_from_paper_root(paper_root: Path) -> tuple[str, Path]:
    _, _, _, study_id, study_root = _resolve_study_binding(paper_root)
    return study_id, study_root


def resolve_paper_root_context(paper_root: Path) -> PaperRootContext:
    resolved_paper_root, worktree_root, quest_root, study_id, study_root = _resolve_study_binding(paper_root)
    return PaperRootContext(
        paper_root=resolved_paper_root,
        worktree_root=worktree_root,
        quest_root=quest_root,
        study_id=study_id,
        study_root=study_root,
    )
