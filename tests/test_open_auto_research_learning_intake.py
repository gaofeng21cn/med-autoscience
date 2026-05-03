from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = "docs/program/open_auto_research_learning_intake_2026_05_04.md"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_open_auto_research_intake_records_source_families_and_links() -> None:
    intake = _read(INTAKE_PATH)

    for required in (
        "PaperOrchestra",
        "AI-Scientist-v2",
        "Agent Laboratory",
        "AutoResearchClaw",
        "OpenAI PaperBench",
        "ResearchTown",
        "PaperQA2 / paper-qa",
        "Open Deep Research",
        "STORM / Co-STORM",
        "GPT Researcher",
        "AutoSurvey",
        "SurveyX",
        "OpenResearcher",
        "MiroFlow",
        "OpenHands",
        "LangGraph durable execution",
        "SWE-agent",
        "CAMEL Workforce",
        "CrewAI Flows",
        "Microsoft AutoGen",
        "MetaGPT",
        "https://github.com/SakanaAI/AI-Scientist-v2",
        "https://openai.com/index/paperbench/",
        "https://github.com/Future-House/paper-qa",
        "https://github.com/langchain-ai/open_deep_research",
        "https://github.com/stanford-oval/storm",
        "https://docs.openhands.dev/usage/architecture/runtime",
        "https://docs.langchain.com/oss/python/langgraph/durable-execution",
        "https://swe-agent.com/0.7/usage/trajectories/",
    ):
        assert required in intake


def test_open_auto_research_intake_records_decisions_and_mas_mappings() -> None:
    intake = _read(INTAKE_PATH)

    for decision in ("adopt_contract", "adopt_template", "watch_only", "reject"):
        assert decision in intake
    for mapping in (
        "Evaluation OS rubric tree",
        "Medical literature evidence graph",
        "Runtime trajectory proof",
        "Candidate path graph",
        "PaperBench hierarchical rubrics",
        "PaperQA2 scientific literature RAG",
        "STORM multi-perspective question asking",
        "Open Deep Research graph decomposition",
        "LangGraph checkpoint / replay / human interrupt discipline",
        "OpenHands action-observation sandbox and SWE-agent trajectories",
        "AI-Scientist-v2 progressive agentic tree search",
        "AutoResearchClaw 23-stage PIVOT / REFINE",
        "CAMEL Workforce pause / resume / status / KPI",
    ):
        assert mapping in intake


def test_open_auto_research_intake_preserves_mas_authority_boundaries() -> None:
    intake = _read(INTAKE_PATH)

    for boundary in (
        "不是把外部框架、skill pack、provider runtime 或论文生成器接成 `MAS` 第二运行时",
        "No external framework becomes MAS product entry, publication owner or study truth owner.",
        "MAS study truth",
        "MAS Quality OS",
        "MAS Evaluation OS",
        "MAS Runtime OS",
        "MAS Artifact OS",
        "cannot authorize publication quality by itself",
        "cannot silently re-execute side-effect actions without idempotency evidence",
        "external generators cannot directly patch `current_package`",
        "External projects stay source references",
    ):
        assert boundary in intake


def test_open_auto_research_intake_records_saturation_protocol() -> None:
    intake = _read(INTAKE_PATH)

    for required in (
        "Continued Learning Saturation Protocol",
        "MAS-actionable saturated",
        "`saturated_by_existing_contract`",
        "provider / UI / generic role-play",
        "non-medical benchmark",
        "license-risk code adoption",
        "skill-pack identity",
        "unbounded autonomous paper generation",
        "selective learning",
    ):
        assert required in intake


def test_status_points_to_open_auto_research_learning_entry() -> None:
    status = _read("docs/status.md")

    assert "Open Auto Research Learning Intake 2026-05-04" in status
    assert INTAKE_PATH.replace("docs/", "./") in status
    assert "PaperBench-style hierarchical rubrics" in status
    assert "PaperQA2-style scientific literature evidence graph" in status
    assert "LangGraph/OpenHands/SWE-agent-style runtime trajectory proof" in status
    assert "AI-Scientist-v2 / AutoResearchClaw-style candidate path graph" in status
