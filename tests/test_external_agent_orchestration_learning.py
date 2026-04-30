from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = "docs/program/external_agent_orchestration_learning_intake_2026_04_30.md"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_external_agent_orchestration_intake_records_sources_and_links() -> None:
    intake = _read(INTAKE_PATH)

    for required in (
        "openai/symphony@58cf97d",
        "msitarzewski/agency-agents@783f6a7",
        "Symphony README",
        "Symphony SPEC",
        "Symphony WORKFLOW",
        "Agency README",
        "NEXUS strategy",
        "handoff templates",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/README.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/SPEC.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/WORKFLOW.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/README.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/nexus-strategy.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/coordination/handoff-templates.md",
    ):
        assert required in intake


def test_external_agent_orchestration_intake_records_decisions_and_value() -> None:
    intake = _read(INTAKE_PATH)

    for decision in ("adopt_contract", "adopt_template", "watch_only", "reject"):
        assert decision in intake
    for value in (
        "长期自治",
        "work-unit 状态",
        "隔离 workspace",
        "retry/backoff/reconciliation",
        "observability",
        "structured handoff",
        "evidence-over-claims",
        "AI reviewer gate",
    ):
        assert value in intake


def test_external_agent_orchestration_intake_preserves_mas_owner_boundaries() -> None:
    intake = _read(INTAKE_PATH)

    for boundary in (
        "不引入 Linear 必需入口",
        "不引入 Symphony scheduler 作为 MAS owner",
        "不引入 generic persona library / NEXUS persona 库",
        "不改变 MAS study truth/publication judgment/controller decision owner",
        "MAS study truth/publication judgment/controller decision owner stays unchanged",
        "study_runtime_status",
        "runtime_watch",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
    ):
        assert boundary in intake


def test_status_points_to_external_agent_orchestration_learning_entry() -> None:
    status = _read("docs/status.md")

    assert "External Agent Orchestration Learning Intake 2026-04-30" in status
    assert INTAKE_PATH.replace("docs/", "./") in status
    assert "长期自治" in status
    assert "AI reviewer gate" in status
