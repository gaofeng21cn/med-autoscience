from __future__ import annotations

from pathlib import Path


def write_profile(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/Users/gaofeng/workspace/Yang/NF-PitNET"',
                'runtime_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/runtime/quests"',
                'studies_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/studies"',
                'portfolio_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/portfolio"',
                'med_deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/runtime"',
                'med_deepscientist_repo_root = ""',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
