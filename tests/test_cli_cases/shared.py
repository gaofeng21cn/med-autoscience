from __future__ import annotations

import argparse
import builtins
import importlib
import json
from pathlib import Path
import sys

import pytest

from med_autoscience.agent_entry.renderers import (
    render_codex_entry_skill,
    render_entry_modes_guide,
    render_entry_modes_payload,
    render_openclaw_entry_prompt,
    render_public_yaml,
)
from med_autoscience.figure_routes import (
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
    FIGURE_ROUTE_SCRIPT_FIX,
    build_figure_route,
)


def write_profile(
    path: Path,
    *,
    workspace_root: Path | str = "/Users/gaofeng/workspace/Yang/无功能垂体瘤",
    med_deepscientist_repo_root: Path | str = "/Users/gaofeng/workspace/med-deepscientist",
    hermes_agent_repo_root: Path | str = "/Users/gaofeng/workspace/_external/hermes-agent",
) -> None:
    workspace_root = Path(workspace_root)
    med_deepscientist_repo_root = Path(med_deepscientist_repo_root)
    hermes_agent_repo_root = Path(hermes_agent_repo_root)
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                f'med_deepscientist_repo_root = "{med_deepscientist_repo_root}"',
                f'hermes_agent_repo_root = "{hermes_agent_repo_root}"',
                'hermes_home_root = "~/.hermes"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'medical_overlay_bootstrap_mode = "ensure_ready"',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
                "",
                "[[default_submission_targets]]",
                'publication_profile = "frontiers_family_harvard"',
                "primary = true",
                "package_required = true",
                'story_surface = "general_medical_journal"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )













































































































































































