from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from .layout import build_workspace_runtime_layout


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


def _extract_study_id_from_payload(payload: dict[str, Any]) -> str | None:
    direct = payload.get("study_id")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    runtime_reentry_gate = payload.get("runtime_reentry_gate")
    if isinstance(runtime_reentry_gate, dict):
        nested = runtime_reentry_gate.get("study_id")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()

    startup_contract = payload.get("startup_contract")
    if isinstance(startup_contract, dict):
        nested = startup_contract.get("study_id")
        if isinstance(nested, str) and nested.strip():
            return nested.strip()
        runtime_reentry_gate = startup_contract.get("runtime_reentry_gate")
        if isinstance(runtime_reentry_gate, dict):
            nested = runtime_reentry_gate.get("study_id")
            if isinstance(nested, str) and nested.strip():
                return nested.strip()
    return None


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
    study_id = _extract_study_id_from_payload(payload)
    if study_id:
        return study_id

    quest_root = resolve_quest_root_from_worktree_root(resolved_worktree_root)
    quest_root_yaml_path = quest_root / "quest.yaml"
    if quest_root_yaml_path.exists():
        quest_payload = _load_yaml_mapping(quest_root_yaml_path)
        study_id = _extract_study_id_from_payload(quest_payload)
        if study_id:
            return study_id

    fallback_quest_id = payload.get("quest_id")
    if not isinstance(fallback_quest_id, str) or not fallback_quest_id.strip():
        raise ValueError(f"missing string quest_id in {quest_yaml_path}")
    return fallback_quest_id.strip()


def _resolve_workspace_root_from_quest_root(quest_root: Path) -> Path:
    resolved = _resolve_path(quest_root)
    try:
        workspace_root = resolved.parents[4]
    except IndexError as exc:
        raise ValueError(f"quest_root is not under an ops/med-deepscientist/runtime/quests layout: {quest_root}") from exc
    layout = build_workspace_runtime_layout(workspace_root=workspace_root)
    if resolved.parent != layout.quests_root or resolved.parent.parent != layout.runtime_root:
        raise ValueError(f"quest_root is not under an ops/med-deepscientist/runtime/quests layout: {quest_root}")
    return layout.workspace_root


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
