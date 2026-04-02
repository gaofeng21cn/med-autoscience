from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from med_autoscience.profiles import WorkspaceProfile


@dataclass(frozen=True)
class WorkspaceRuntimeLayout:
    workspace_root: Path
    ops_root: Path
    runtime_root: Path
    quests_root: Path
    bin_root: Path
    startup_briefs_root: Path
    startup_payloads_root: Path
    config_env_path: Path
    config_env_example_path: Path
    readme_path: Path
    behavior_gate_path: Path

    def quest_root(self, quest_id: str) -> Path:
        return self.quests_root / quest_id

    def startup_payload_root(self, study_id: str) -> Path:
        return self.startup_payloads_root / study_id

    def startup_brief_path(self, study_id: str) -> Path:
        return self.startup_briefs_root / f"{study_id}.md"


def build_workspace_runtime_layout(*, workspace_root: Path) -> WorkspaceRuntimeLayout:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    ops_root = resolved_workspace_root / "ops" / "med-deepscientist"
    runtime_root = ops_root / "runtime"
    return WorkspaceRuntimeLayout(
        workspace_root=resolved_workspace_root,
        ops_root=ops_root,
        runtime_root=runtime_root,
        quests_root=runtime_root / "quests",
        bin_root=ops_root / "bin",
        startup_briefs_root=ops_root / "startup_briefs",
        startup_payloads_root=ops_root / "startup_payloads",
        config_env_path=ops_root / "config.env",
        config_env_example_path=ops_root / "config.env.example",
        readme_path=ops_root / "README.md",
        behavior_gate_path=ops_root / "behavior_equivalence_gate.yaml",
    )


def build_workspace_runtime_layout_for_profile(profile: WorkspaceProfile) -> WorkspaceRuntimeLayout:
    return build_workspace_runtime_layout(workspace_root=profile.workspace_root)


def resolve_runtime_root_from_quest_root(quest_root: Path) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    return resolved_quest_root.parent.parent
