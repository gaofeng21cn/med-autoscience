from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = REPO_ROOT / "src" / "med_autoscience" / "overlay" / "templates"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_medical_stage_packet_block_defines_start_end_and_tool_discipline() -> None:
    packet = (TEMPLATE_ROOT / "medical-research-stage-packet.block.md").read_text(encoding="utf-8")

    assert "Stage-start packet" in packet
    assert "Stage-end packet" in packet
    assert "failed paths" in packet
    assert "winning path" in packet
    assert "exact resume point" in packet
    assert "Use memory only when a reusable lesson should change future default behavior" in packet
    assert "Medical route mapping" in packet
    assert "idea objective contract and candidate board" in packet
    assert "bounded campaign" in packet
    assert "evidence-bound repair" in packet
    assert "submission truth" in packet
    assert "route outcome from durable truth" in packet


def test_core_medical_stage_templates_reference_stage_packet_block() -> None:
    for filename in (
        "medical-research-idea.SKILL.md",
        "medical-research-analysis-campaign.block.md",
        "medical-research-write.SKILL.md",
        "medical-research-finalize.SKILL.md",
        "medical-research-decision.SKILL.md",
    ):
        text = (TEMPLATE_ROOT / filename).read_text(encoding="utf-8")
        assert "medical-research-stage-packet.block.md" in text, filename


def test_write_template_requires_formal_medical_manuscript_structure_pass() -> None:
    text = (TEMPLATE_ROOT / "medical-research-write.SKILL.md").read_text(encoding="utf-8")

    assert "formal manuscript-language pass" in text
    assert "Variable measurement and outcome definition" in text
    assert "Validation, sensitivity, and stratified analyses" in text
    assert "cohort inclusion/exclusion counts belong in the first Results subsection" in text
    assert "four paragraphs: principal findings and significance" in text
    assert "no main-text `Reporting boundary` heading" in text


def test_policy_docs_pin_stage_packet_and_tool_usage_boundaries() -> None:
    route_policy = _read("docs/policies/study_route_contract.md")
    evidence_policy = _read("docs/policies/evidence_review_contract.md")

    assert "## Stage Packet 规则" in route_policy
    assert "stage packet 是 route truth 的最小可接力单元" in route_policy
    assert "## Tool Usage 规则" in evidence_policy
    assert "memory 只记录会改变未来默认行为的 reusable lesson" in evidence_policy
    assert "execution logs 只作为第一手执行证据" in evidence_policy
