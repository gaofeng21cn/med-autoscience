from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


PREFERRED_STUDY_AUTHORITY_ROOT_NAME = "manuscript"
LEGACY_STUDY_AUTHORITY_ROOT_NAME = "paper"
STUDY_AUTHORITY_ROOT_NAMES = (
    PREFERRED_STUDY_AUTHORITY_ROOT_NAME,
    LEGACY_STUDY_AUTHORITY_ROOT_NAME,
)
_STAGE_NATIVE_BODY_ROOT_PARTS = (
    "artifacts",
    "stage_outputs",
    "_body_authority",
    "paper_authority_cutover",
    "current_body",
)


@dataclass(frozen=True)
class StudyPaperContext:
    paper_root: Path
    context_root: Path
    quest_root: Path
    quest_id: str
    study_id: str
    study_root: Path


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    import yaml

    if not path.exists():
        raise FileNotFoundError(f"missing explicit identity contract: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _required_identity(payload: dict[str, Any], key: str, *, path: Path) -> str:
    value = payload.get(key)
    normalized = value.strip() if isinstance(value, str) else ""
    if not normalized:
        raise ValueError(f"missing explicit {key} in {path}")
    return normalized


def _canonical_workspace_root(quest_root: Path) -> Path:
    resolved = _resolve_path(quest_root)
    if resolved.parent.name != "quests" or resolved.parent.parent.name != "runtime":
        raise ValueError(f"quest_root is not under the canonical runtime/quests layout: {quest_root}")
    return resolved.parent.parent.parent.resolve()


def _quest_identity(quest_root: Path) -> tuple[str, str]:
    resolved_quest_root = _resolve_path(quest_root)
    quest_yaml_path = resolved_quest_root / "quest.yaml"
    payload = _load_yaml_mapping(quest_yaml_path)
    quest_id = _required_identity(payload, "quest_id", path=quest_yaml_path)
    study_id = _required_identity(payload, "study_id", path=quest_yaml_path)
    if quest_id != resolved_quest_root.name:
        raise ValueError(
            f"conflicting quest_id declarations between {quest_yaml_path} and canonical quest root: "
            f"{quest_id!r} != {resolved_quest_root.name!r}"
        )
    return quest_id, study_id


def _study_root_for_identity(*, workspace_root: Path, study_id: str) -> Path:
    study_root = (workspace_root / "studies" / study_id).resolve()
    study_yaml_path = study_root / "study.yaml"
    payload = _load_yaml_mapping(study_yaml_path)
    declared_study_id = _required_identity(payload, "study_id", path=study_yaml_path)
    if declared_study_id != study_id:
        raise ValueError(
            f"conflicting study_id declarations between explicit quest and {study_yaml_path}: "
            f"{study_id!r} != {declared_study_id!r}"
        )
    return study_root


def resolve_study_root_from_quest_root(
    quest_root: Path,
    *,
    quest_id: str | None = None,
) -> tuple[str, Path]:
    resolved_quest_root = _resolve_path(quest_root)
    workspace_root = _canonical_workspace_root(resolved_quest_root)
    declared_quest_id, study_id = _quest_identity(resolved_quest_root)
    requested_quest_id = str(quest_id or "").strip()
    if requested_quest_id and requested_quest_id != declared_quest_id:
        raise ValueError(
            f"conflicting quest_id declarations: {requested_quest_id!r} != {declared_quest_id!r}"
        )
    return study_id, _study_root_for_identity(workspace_root=workspace_root, study_id=study_id)


def _quest_binding_for_study(*, workspace_root: Path, study_id: str) -> tuple[Path, str]:
    matches: list[tuple[Path, str]] = []
    quests_root = workspace_root / "runtime" / "quests"
    for quest_yaml_path in sorted(quests_root.glob("*/quest.yaml")):
        quest_root = quest_yaml_path.parent.resolve()
        quest_id, declared_study_id = _quest_identity(quest_root)
        if declared_study_id == study_id:
            matches.append((quest_root, quest_id))
    if not matches:
        raise FileNotFoundError(f"no canonical quest.yaml binds study_id {study_id!r}")
    if len(matches) != 1:
        refs = ", ".join(str(quest_root / "quest.yaml") for quest_root, _ in matches)
        raise ValueError(f"multiple canonical quest identities bind study_id {study_id!r}: {refs}")
    return matches[0]


def _stage_native_context(paper_root: Path) -> StudyPaperContext | None:
    resolved_paper_root = _resolve_path(paper_root)
    if resolved_paper_root.name not in STUDY_AUTHORITY_ROOT_NAMES:
        return None
    source_root = resolved_paper_root.parent
    if tuple(source_root.parts[-len(_STAGE_NATIVE_BODY_ROOT_PARTS) :]) != _STAGE_NATIVE_BODY_ROOT_PARTS:
        return None
    study_root = source_root.parents[len(_STAGE_NATIVE_BODY_ROOT_PARTS) - 1].resolve()
    if study_root.parent.name != "studies":
        raise ValueError(f"stage-native paper root is not under a canonical studies root: {paper_root}")
    study_yaml_path = study_root / "study.yaml"
    study_payload = _load_yaml_mapping(study_yaml_path)
    study_id = _required_identity(study_payload, "study_id", path=study_yaml_path)
    if study_id != study_root.name:
        raise ValueError(
            f"conflicting study_id declarations between {study_yaml_path} and canonical study root: "
            f"{study_id!r} != {study_root.name!r}"
        )
    workspace_root = study_root.parent.parent.resolve()
    quest_root, quest_id = _quest_binding_for_study(workspace_root=workspace_root, study_id=study_id)
    return StudyPaperContext(
        paper_root=resolved_paper_root,
        context_root=source_root.resolve(),
        quest_root=quest_root,
        quest_id=quest_id,
        study_id=study_id,
        study_root=study_root,
    )


def resolve_study_paper_context(paper_root: Path) -> StudyPaperContext:
    stage_native_context = _stage_native_context(paper_root)
    if stage_native_context is not None:
        return stage_native_context
    resolved_paper_root = _resolve_path(paper_root)
    if resolved_paper_root.name != LEGACY_STUDY_AUTHORITY_ROOT_NAME:
        raise ValueError(f"paper_root is not a canonical quest paper root: {paper_root}")
    quest_root = resolved_paper_root.parent.resolve()
    study_id, study_root = resolve_study_root_from_quest_root(quest_root)
    quest_id, _ = _quest_identity(quest_root)
    return StudyPaperContext(
        paper_root=resolved_paper_root,
        context_root=quest_root,
        quest_root=quest_root,
        quest_id=quest_id,
        study_id=study_id,
        study_root=study_root,
    )


def resolve_study_root_from_paper_root(paper_root: Path) -> tuple[str, Path]:
    context = resolve_study_paper_context(paper_root)
    return context.study_id, context.study_root
