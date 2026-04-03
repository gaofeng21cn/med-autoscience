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


def _extract_string_field(payload: dict[str, Any], key: str) -> str | None:
    value = payload.get(key)
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _extract_declared_study_id(payload: dict[str, Any], *, quest_yaml_path: Path) -> str | None:
    explicit_study_id = _extract_string_field(payload, "study_id")
    runtime_reentry_gate = payload.get("runtime_reentry_gate")
    reentry_study_id = (
        _extract_string_field(runtime_reentry_gate, "study_id")
        if isinstance(runtime_reentry_gate, dict)
        else None
    )
    startup_contract = payload.get("startup_contract")
    nested_startup_study_id = (
        _extract_string_field(startup_contract, "study_id")
        if isinstance(startup_contract, dict)
        else None
    )
    nested_runtime_reentry_gate = (
        startup_contract.get("runtime_reentry_gate")
        if isinstance(startup_contract, dict)
        else None
    )
    nested_reentry_study_id = (
        _extract_string_field(nested_runtime_reentry_gate, "study_id")
        if isinstance(nested_runtime_reentry_gate, dict)
        else None
    )

    declared_candidates = [
        value
        for value in (
            explicit_study_id,
            reentry_study_id,
            nested_startup_study_id,
            nested_reentry_study_id,
        )
        if value
    ]
    if declared_candidates and len(set(declared_candidates)) != 1:
        raise ValueError(
            f"conflicting study_id declarations in {quest_yaml_path}: "
            + ", ".join(repr(item) for item in declared_candidates)
        )
    return declared_candidates[0] if declared_candidates else None


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
    worktree_study_id = _extract_declared_study_id(payload, quest_yaml_path=quest_yaml_path)

    quest_root = resolve_quest_root_from_worktree_root(resolved_worktree_root)
    quest_root_yaml_path = quest_root / "quest.yaml"
    quest_root_study_id = None
    if quest_root_yaml_path.exists():
        quest_payload = _load_yaml_mapping(quest_root_yaml_path)
        quest_root_study_id = _extract_declared_study_id(quest_payload, quest_yaml_path=quest_root_yaml_path)
        if worktree_study_id and quest_root_study_id and worktree_study_id != quest_root_study_id:
            raise ValueError(
                f"conflicting study_id declarations between {quest_yaml_path} and {quest_root_yaml_path}: "
                f"{worktree_study_id!r} != {quest_root_study_id!r}"
            )

    if worktree_study_id or quest_root_study_id:
        return worktree_study_id or quest_root_study_id or ""

    fallback_quest_id = _extract_string_field(payload, "quest_id")
    if fallback_quest_id:
        return fallback_quest_id
    if quest_root_yaml_path.exists():
        quest_payload = _load_yaml_mapping(quest_root_yaml_path)
        fallback_quest_id = _extract_string_field(quest_payload, "quest_id")
        if fallback_quest_id:
            return fallback_quest_id
    raise ValueError(f"missing string quest_id in {quest_yaml_path}")


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


def _resolve_study_binding_from_runtime_binding(
    *,
    workspace_root: Path,
    quest_id: str,
) -> tuple[str, Path] | None:
    studies_root = workspace_root / "studies"
    if not studies_root.exists():
        return None
    for runtime_binding_path in sorted(studies_root.glob("*/runtime_binding.yaml")):
        payload = _load_yaml_mapping(runtime_binding_path)
        bound_quest_id = payload.get("quest_id")
        if not isinstance(bound_quest_id, str) or bound_quest_id.strip() != quest_id:
            continue
        study_root = runtime_binding_path.parent
        study_id = payload.get("study_id")
        if not isinstance(study_id, str) or not study_id.strip():
            study_id = study_root.name
        return study_id.strip(), study_root
    return None


def _resolve_study_binding(paper_root: Path) -> tuple[Path, Path, Path, str, Path]:
    resolved_paper_root = _resolve_path(paper_root)
    worktree_root = resolve_worktree_root_from_paper_root(resolved_paper_root)
    quest_root = resolve_quest_root_from_worktree_root(worktree_root)
    quest_id = resolve_study_id_from_worktree_root(worktree_root)
    workspace_root = _resolve_workspace_root_from_quest_root(quest_root)
    study_id = quest_id
    study_root = workspace_root / "studies" / study_id
    if not (study_root / "study.yaml").exists():
        binding = _resolve_study_binding_from_runtime_binding(
            workspace_root=workspace_root,
            quest_id=quest_id,
        )
        if binding is None:
            raise FileNotFoundError(f"unable to resolve studies root for `{study_id}` from {paper_root}")
        study_id, study_root = binding
        if not (study_root / "study.yaml").exists():
            raise FileNotFoundError(f"runtime binding resolved `{study_id}` but study.yaml is missing at {study_root}")
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
