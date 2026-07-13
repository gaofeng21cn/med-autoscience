from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_ROOT = REPO_ROOT / "agent" / "prompts"
PROMPT_PATHS = tuple(sorted(PROMPT_ROOT.glob("*.md")))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalized(path: Path) -> str:
    return " ".join(_read(path).split())


def test_stage_prompts_delegate_professional_methods_without_cli_recipe() -> None:
    assert len(PROMPT_PATHS) == 6

    for path in PROMPT_PATHS:
        text = _read(path)
        assert "medical_research_execution.md" in text, path
        assert "search -> inspect -> sync" not in text, path
        assert "The only allowed sequence" not in text, path
        assert "## External Specialist Skill Policy" not in text, path


def test_stage_prompts_preserve_domain_dependencies_and_progress_semantics() -> None:
    analysis = _read(PROMPT_ROOT / "bounded_analysis_campaign.md")
    manuscript = _normalized(PROMPT_ROOT / "manuscript_authoring.md")
    review = _normalized(PROMPT_ROOT / "review_and_quality_gate.md")
    finalize = _normalized(PROMPT_ROOT / "finalize_and_publication_handoff.md")

    assert "estimand or target quantity" in analysis
    assert "Record weak, negative, failed" in analysis
    assert "separate invocation" in review
    assert "Quality and ready claims fail closed" in review
    assert "Stage progression does not" in review
    assert "Mutate canonical source only through an authorized MAS path" in manuscript
    for dependency in (
        "exact already-reviewed refs and hashes",
        "deterministic inspection packaging",
        "earliest owning Stage",
        "cross-Stage Meta Review",
        "human gate",
    ):
        assert dependency in finalize
    assert "obtain MAS mutation authority" not in finalize
    assert "mutate canonical source; rebuild" not in finalize
    assert "This Stage never mutates canonical source" in finalize
    assert "decisive cross-Stage route owner" in finalize
    assert "route_impact.stage_route_decision" in finalize

    for text in (manuscript, review, finalize):
        assert "completed_with_quality_debt" in text
        assert "packet" in text.lower()
        assert "ready claim" in text.lower()


def test_external_skill_acquisition_policy_is_single_sourced_in_skill_layer() -> None:
    execution_policy = _normalized(
        REPO_ROOT / "agent" / "skills" / "medical_research_execution.md"
    )
    primary_skill = _normalized(REPO_ROOT / "agent" / "primary_skill" / "SKILL.md")

    for text in (execution_policy, primary_skill):
        assert "Acquire a new external Skill only" in text
        assert "identity" in text
        assert "provenance" in text
        assert "permissions" in text
        assert "before sync" in text.lower()
        assert "search and comparison order" in text.lower()

    plugin_skill = (
        REPO_ROOT
        / "plugins"
        / "med-autoscience"
        / "skills"
        / "med-autoscience"
        / "SKILL.md"
    )
    assert _read(plugin_skill) == _read(
        REPO_ROOT / "agent" / "primary_skill" / "SKILL.md"
    )


def test_manifest_bounds_tool_autonomy_by_professional_dependencies() -> None:
    manifest = json.loads(
        _read(REPO_ROOT / "agent" / "stages" / "manifest.json")
    )

    for stage in manifest["stages"]:
        autonomy = stage["tool_affordance_boundary"]["executor_autonomy"]
        assert autonomy["executor_can_choose_order_and_parallelism"] is True
        assert autonomy["executor_order_is_bounded_by_domain_dependencies"] is True
        assert autonomy["professional_policy_can_require_ordered_dependencies"] is True
        assert autonomy["tool_catalog_can_prescribe_tool_sequence"] is False
