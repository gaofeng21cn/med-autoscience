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
        "Symphony logging guide",
        "Symphony token accounting guide",
        "Symphony path safety",
        "Symphony orchestrator",
        "Symphony status dashboard",
        "Agency README",
        "NEXUS strategy",
        "handoff templates",
        "NEXUS phase 3 build loop",
        "NEXUS phase 4 hardening gate",
        "NEXUS phase 6 operate loop",
        "Evidence Collector",
        "Reality Checker",
        "Experiment Tracker",
        "Agentic Identity Trust",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/README.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/SPEC.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/WORKFLOW.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/docs/logging.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/docs/token_accounting.md",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/lib/symphony_elixir/path_safety.ex",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/lib/symphony_elixir/orchestrator.ex",
        "https://github.com/openai/symphony/blob/58cf97da06d556c019ccea20c67f4f77da124bf3/elixir/lib/symphony_elixir/status_dashboard.ex",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/README.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/nexus-strategy.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/coordination/handoff-templates.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/playbooks/phase-3-build.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/playbooks/phase-4-hardening.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/strategy/playbooks/phase-6-operate.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/testing/testing-evidence-collector.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/testing/testing-reality-checker.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/project-management/project-management-experiment-tracker.md",
        "https://github.com/msitarzewski/agency-agents/blob/783f6a72bfd7f3135700ac273c619d92821b419a/specialized/agentic-identity-trust.md",
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
        "absolute token totals",
        "dashboard snapshots",
        "hosted worker safety preflight",
        "secret handling",
        "hook safety",
        "fail-closed authorization",
        "bounded medical repair",
        "analysis-campaign planning discipline",
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


def test_external_agent_orchestration_intake_records_saturation_protocol() -> None:
    intake = _read(INTAKE_PATH)

    for required in (
        "Continued Learning Saturation Protocol",
        "MAS-actionable saturation",
        "source file coverage",
        "`saturated_by_existing_contract`",
        "`new_contract_landed`",
        "`new_template_landed`",
        "`reject_saturated`",
        "tracker-specific mechanics",
        "generic persona routing",
        "marketing/product lifecycle",
        "non-medical QA label",
        "agentic identity/trust",
        "cryptographic delegation",
        "cross-runtime authorization gap",
        "trust boundary / secret handling / hook safety",
        "cryptographic identity layer",
        "trust score service",
    ):
        assert required in intake


def test_status_points_to_external_agent_orchestration_learning_entry() -> None:
    status = _read("docs/status.md")

    assert "External Agent Orchestration Learning Intake 2026-04-30" in status
    assert INTAKE_PATH.replace("docs/", "./") in status
    assert "长期自治" in status
    assert "AI reviewer gate" in status
    assert "hosted worker trust boundary" in status
    assert "Continued Learning Saturation Protocol" in status
    assert "MAS-actionable saturated" in status
    assert "cryptographic identity runtime" in status
