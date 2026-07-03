from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

PROMPT_REQUIREMENTS = {
    "agent/prompts/bounded_analysis_campaign.md": {
        "max_lines": 95,
        "routes": {
            "medical-statistical-review",
            "medical-data-governance",
            "medical-table-design",
            "medical-figure-design",
            "medical-research-lit",
        },
    },
    "agent/prompts/manuscript_authoring.md": {
        "max_lines": 100,
        "routes": {
            "medical-manuscript-writing",
            "medical-research-lit",
            "medical-statistical-review",
            "medical-table-design",
            "medical-figure-design",
            "medical-data-governance",
            "medical-submission-prep",
        },
    },
    "agent/prompts/review_and_quality_gate.md": {
        "max_lines": 100,
        "routes": {
            "medical-manuscript-review",
            "medical-research-lit",
            "medical-statistical-review",
            "medical-table-design",
            "medical-figure-design",
            "medical-data-governance",
            "medical-submission-prep",
        },
    },
    "agent/prompts/finalize_and_publication_handoff.md": {
        "max_lines": 105,
        "routes": {
            "medical-submission-prep",
            "medical-manuscript-review",
            "medical-manuscript-writing",
            "medical-research-lit",
            "medical-statistical-review",
            "medical-table-design",
            "medical-figure-design",
            "medical-data-governance",
        },
    },
}

OVERLAY_REQUIREMENTS = {
    "src/med_autoscience/overlay/templates/medical-research-analysis-campaign.SKILL.md": {
        "routes": {"medical-statistical-review", "medical-data-governance"},
    },
    "src/med_autoscience/overlay/templates/medical-research-finalize.SKILL.md": {
        "routes": {"medical-submission-prep", "medical-manuscript-review"},
    },
    "src/med_autoscience/overlay/templates/medical-research-figure-polish.SKILL.md": {
        "routes": {"medical-figure-design", "medical-statistical-review"},
    },
    "src/med_autoscience/overlay/templates/medical-research-journal-resolution.SKILL.md": {
        "routes": {"medical-submission-prep", "medical-research-lit"},
    },
    "src/med_autoscience/overlay/templates/medical-research-write.SKILL.md": {
        "routes": {"medical-manuscript-writing", "medical-data-governance"},
    },
    "src/med_autoscience/overlay/templates/medical-research-review.SKILL.md": {
        "routes": {"medical-manuscript-review", "medical-submission-prep"},
    },
    "src/med_autoscience/overlay/templates/medical-research-figure.SKILL.md": {
        "routes": {"medical-figure-design", "medical-manuscript-review"},
    },
}

OLD_INLINE_METHOD_PACK_TOKENS = {
    "journal_response_pack",
    "manuscript_argument_pack",
    "statistical_reporting_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
    "figure_evidence_contract_pack",
    "paper_reader_grounding_pack",
    "paper_presentation_pack",
}


def _read(repo_path: str) -> str:
    return (REPO_ROOT / repo_path).read_text(encoding="utf-8")


def test_stage_prompts_remain_thin_and_route_to_specialist_skills() -> None:
    for repo_path, expectation in PROMPT_REQUIREMENTS.items():
        text = _read(repo_path)
        line_count = len(text.splitlines())

        assert line_count <= expectation["max_lines"], repo_path
        assert "## Specialist Skill Routes" in text, repo_path
        assert "owner gate" in text.lower(), repo_path
        for route in expectation["routes"]:
            assert route in text, f"{repo_path} missing {route}"


def test_stage_prompts_do_not_reembed_old_professional_pack_playbooks() -> None:
    prompt_text = "\n".join(_read(repo_path) for repo_path in PROMPT_REQUIREMENTS)

    for token in OLD_INLINE_METHOD_PACK_TOKENS:
        assert token not in prompt_text


def test_overlay_stage_projections_route_professional_work_to_scholar_skills() -> None:
    for repo_path, expectation in OVERLAY_REQUIREMENTS.items():
        text = _read(repo_path)

        assert "MAS Stage Projection Boundary" in text, repo_path
        assert "candidate" in text, repo_path
        for route in expectation["routes"]:
            assert route in text, f"{repo_path} missing {route}"
