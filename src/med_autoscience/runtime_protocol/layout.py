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
    archives_root: Path
    restore_index_root: Path
    runtime_artifacts_root: Path
    domain_authority_refs_index_path: Path
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
    ops_root = resolved_workspace_root / "ops" / "mas"
    runtime_root = resolved_workspace_root / "runtime"
    return _build_layout(
        workspace_root=resolved_workspace_root,
        ops_root=ops_root,
        runtime_root=runtime_root,
    )


def build_workspace_runtime_layout_for_profile(profile: WorkspaceProfile) -> WorkspaceRuntimeLayout:
    runtime_root = profile.managed_runtime_home.expanduser().resolve()
    workspace_root = profile.workspace_root.expanduser().resolve()
    ops_root = workspace_root / "ops" / "mas" if runtime_root == workspace_root / "runtime" else runtime_root.parent
    return _build_layout(
        workspace_root=workspace_root,
        ops_root=ops_root,
        runtime_root=runtime_root,
        quests_root=profile.managed_runtime_quests_root.expanduser().resolve(),
    )


def _build_layout(
    *,
    workspace_root: Path,
    ops_root: Path,
    runtime_root: Path,
    quests_root: Path | None = None,
) -> WorkspaceRuntimeLayout:
    resolved_workspace_root = workspace_root.expanduser().resolve()
    resolved_ops_root = ops_root.expanduser().resolve()
    resolved_runtime_root = runtime_root.expanduser().resolve()
    resolved_quests_root = (quests_root or resolved_runtime_root / "quests").expanduser().resolve()
    mas_first = resolved_runtime_root == resolved_workspace_root / "runtime"
    startup_root = resolved_runtime_root if mas_first else resolved_ops_root
    runtime_artifacts_root = resolved_workspace_root / "artifacts" / "runtime"
    return WorkspaceRuntimeLayout(
        workspace_root=resolved_workspace_root,
        ops_root=resolved_ops_root,
        runtime_root=resolved_runtime_root,
        quests_root=resolved_quests_root,
        archives_root=resolved_runtime_root / "archives",
        restore_index_root=resolved_runtime_root / "restore_index",
        runtime_artifacts_root=runtime_artifacts_root,
        domain_authority_refs_index_path=runtime_artifacts_root / "domain_authority_refs.sqlite",
        bin_root=resolved_ops_root / "bin",
        startup_briefs_root=startup_root / "startup_briefs",
        startup_payloads_root=startup_root / "startup_payloads",
        config_env_path=resolved_ops_root / "config.env",
        config_env_example_path=resolved_ops_root / "config.env.example",
        readme_path=resolved_ops_root / "README.md",
        behavior_gate_path=resolved_ops_root / "behavior_equivalence_gate.yaml",
    )


def resolve_runtime_root_from_quest_root(quest_root: Path) -> Path:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    return resolved_quest_root.parent.parent
