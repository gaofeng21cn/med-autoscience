from __future__ import annotations

import importlib
from pathlib import Path


def test_prepare_external_research_creates_scaffold_prompt_and_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.external_research")
    workspace_root = tmp_path / "workspace"

    result = module.prepare_external_research(workspace_root=workspace_root, as_of_date="2026-03-30")

    research_memory_root = workspace_root / "portfolio" / "research_memory"
    prompts_root = research_memory_root / "prompts"
    external_reports_root = research_memory_root / "external_reports"
    prompt_path = prompts_root / "2026-03-30-workspace-topic-opportunity-deep-research-prompt.md"

    assert result["workspace_root"] == str(workspace_root.resolve())
    assert result["status"] == "ready"
    assert prompts_root.is_dir()
    assert external_reports_root.is_dir()
    assert prompt_path.is_file()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert "Deep Research Prompt" in prompt_text
    assert "refs/ 只用于理解数据与历史背景" in prompt_text
    assert "external_reports/YYYY-MM-DD-topic-opportunity-scout-<provider>.md" in prompt_text

    status = module.external_research_status(workspace_root=workspace_root)

    assert status["optional_module_ready"] is True
    assert status["prompt_file_count"] == 1
    assert status["external_report_count"] == 0
    assert "external_research_prompt_ready" in status["recommendations"]


def test_prepare_external_research_is_idempotent_and_preserves_existing_prompt(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.external_research")
    workspace_root = tmp_path / "workspace"

    module.prepare_external_research(workspace_root=workspace_root, as_of_date="2026-03-30")
    prompt_path = (
        workspace_root
        / "portfolio"
        / "research_memory"
        / "prompts"
        / "2026-03-30-workspace-topic-opportunity-deep-research-prompt.md"
    )
    prompt_path.write_text("# custom\n", encoding="utf-8")

    result = module.prepare_external_research(workspace_root=workspace_root, as_of_date="2026-03-30")

    assert str(prompt_path) in result["skipped_files"]
    assert prompt_path.read_text(encoding="utf-8") == "# custom\n"


def test_external_research_status_counts_reports_and_write_back_recommendation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.external_research")
    workspace_root = tmp_path / "workspace"

    module.prepare_external_research(workspace_root=workspace_root, as_of_date="2026-03-30")
    external_reports_root = workspace_root / "portfolio" / "research_memory" / "external_reports"
    (external_reports_root / "2026-03-30-topic-opportunity-scout-gemini.md").write_text("# report 1\n", encoding="utf-8")
    (external_reports_root / "2026-03-30-topic-opportunity-scout-chatgpt.md").write_text("# report 2\n", encoding="utf-8")

    status = module.external_research_status(workspace_root=workspace_root)

    assert status["external_report_count"] == 2
    assert "review_external_reports_and_write_back_stable_findings" in status["recommendations"]
