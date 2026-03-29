from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from med_autoscience.overlay import DEFAULT_MEDICAL_OVERLAY_SKILL_IDS
from med_autoscience.policies.research_route_bias import DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID
from med_autoscience.policies.study_archetypes import DEFAULT_STUDY_ARCHETYPE_IDS


@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    workspace_root: Path
    runtime_root: Path
    studies_root: Path
    portfolio_root: Path
    deepscientist_runtime_root: Path
    default_publication_profile: str
    default_citation_style: str
    enable_medical_overlay: bool
    medical_overlay_scope: str
    medical_overlay_skills: tuple[str, ...]
    research_route_bias_policy: str
    preferred_study_archetypes: tuple[str, ...]


def load_profile(path: str | Path) -> WorkspaceProfile:
    profile_path = Path(path).expanduser().resolve()
    payload = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    return WorkspaceProfile(
        name=str(payload["name"]),
        workspace_root=Path(payload["workspace_root"]).expanduser().resolve(),
        runtime_root=Path(payload["runtime_root"]).expanduser().resolve(),
        studies_root=Path(payload["studies_root"]).expanduser().resolve(),
        portfolio_root=Path(payload["portfolio_root"]).expanduser().resolve(),
        deepscientist_runtime_root=Path(payload["deepscientist_runtime_root"]).expanduser().resolve(),
        default_publication_profile=str(payload["default_publication_profile"]),
        default_citation_style=str(payload["default_citation_style"]),
        enable_medical_overlay=bool(payload.get("enable_medical_overlay", True)),
        medical_overlay_scope=str(payload.get("medical_overlay_scope", "global")),
        medical_overlay_skills=tuple(str(item) for item in payload.get("medical_overlay_skills", DEFAULT_MEDICAL_OVERLAY_SKILL_IDS)),
        research_route_bias_policy=str(payload.get("research_route_bias_policy", DEFAULT_RESEARCH_ROUTE_BIAS_POLICY_ID)),
        preferred_study_archetypes=tuple(
            str(item) for item in payload.get("preferred_study_archetypes", DEFAULT_STUDY_ARCHETYPE_IDS)
        ),
    )
