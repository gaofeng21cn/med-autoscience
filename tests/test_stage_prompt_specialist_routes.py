from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

STAGE_ROUTES = {
    "agent/prompts/bounded_analysis_campaign.md": {
        "medical-statistical-review",
        "medical-data-governance",
        "medical-table-design",
        "medical-figure-design",
        "medical-research-lit",
    },
    "agent/prompts/manuscript_authoring.md": {
        "medical-manuscript-writing",
        "medical-research-lit",
        "medical-statistical-review",
        "medical-table-design",
        "medical-figure-design",
        "medical-data-governance",
        "medical-submission-prep",
    },
    "agent/prompts/review_and_quality_gate.md": {
        "medical-manuscript-review",
        "medical-research-lit",
        "medical-statistical-review",
        "medical-table-design",
        "medical-figure-design",
        "medical-data-governance",
        "medical-submission-prep",
    },
    "agent/prompts/finalize_and_publication_handoff.md": {
        "medical-submission-prep",
        "medical-manuscript-review",
        "medical-manuscript-writing",
        "medical-research-lit",
        "medical-statistical-review",
        "medical-table-design",
        "medical-figure-design",
        "medical-data-governance",
    },
}


@pytest.mark.parametrize(("repo_path", "required_routes"), STAGE_ROUTES.items())
def test_stage_prompt_surface_routes_to_required_specialists(
    repo_path: str,
    required_routes: set[str],
) -> None:
    text = (REPO_ROOT / repo_path).read_text(encoding="utf-8")
    routed_skills = set(re.findall(r"`(medical-[a-z-]+)`", text))

    assert "## Specialist Skill Routes" in text, repo_path
    assert "owner gate" in text.lower(), repo_path
    assert required_routes <= routed_skills, repo_path
