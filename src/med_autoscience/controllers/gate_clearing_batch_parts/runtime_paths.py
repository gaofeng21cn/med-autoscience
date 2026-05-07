from __future__ import annotations

from pathlib import Path

from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience.controllers.gate_clearing_batch_parts.io_utils import non_empty_text, read_json


def quest_root(profile: WorkspaceProfile, *, quest_id: str) -> Path:
    return profile.med_deepscientist_runtime_root / "quests" / quest_id


def resolve_profile_for_study_root(study_root: Path) -> WorkspaceProfile | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    workspace_root = resolved_study_root.parent.parent
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    profile_path: Path | None = None
    if config_env_path.exists():
        configured = med_deepscientist_transport._read_optional_config_env_value(
            path=config_env_path,
            key="MED_AUTOSCIENCE_PROFILE",
        )
        if configured is not None:
            profile_path = Path(configured).expanduser().resolve()
    if profile_path is None:
        candidates = sorted((workspace_root / "ops" / "medautoscience" / "profiles").glob("*.local.toml"))
        if len(candidates) == 1:
            profile_path = candidates[0].resolve()
    if profile_path is None or not profile_path.exists():
        return None
    return load_profile(profile_path)


def latest_scientific_anchor_mapping_path(*, quest_root: Path) -> Path | None:
    worktrees_root = quest_root / ".ds" / "worktrees"
    candidates = sorted(
        worktrees_root.glob("analysis-*/experiments/analysis/*/*/outputs/scientific_anchor_mapping.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )
    return candidates[0] if candidates else None


def current_workspace_root(*, quest_root: Path, default: Path) -> Path:
    research_state = read_json(quest_root / ".ds" / "research_state.json")
    raw = non_empty_text(research_state.get("current_workspace_root"))
    if raw is None:
        return default
    return Path(raw).expanduser().resolve()
