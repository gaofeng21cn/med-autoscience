from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
INTAKE_PATH = "docs/program/paper_orchestra_learning_intake_2026_05_02.md"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_paper_orchestra_intake_records_source_snapshot_and_links() -> None:
    intake = _read(INTAKE_PATH)

    for required in (
        "Ar9av/PaperOrchestra@d5dce670e37d51011f36fa382ffe2b1870d623e0",
        "2026-04-28T11:27:40Z",
        "arXiv:2604.05018v1",
        "PaperOrchestra README",
        "PaperOrchestra architecture",
        "paper-orchestra orchestrator skill",
        "pipeline reference",
        "outline agent",
        "plotting agent",
        "literature review agent",
        "section writing agent",
        "content refinement agent",
        "paper autoraters",
        "agent research aggregator",
        "https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/README.md",
        "https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/docs/architecture.md",
        "https://github.com/Ar9av/PaperOrchestra/blob/d5dce670e37d51011f36fa382ffe2b1870d623e0/skills/content-refinement-agent/SKILL.md",
    ):
        assert required in intake


def test_paper_orchestra_intake_records_decisions_and_mas_mapping() -> None:
    intake = _read(INTAKE_PATH)

    for decision in ("adopt_contract", "adopt_template", "watch_only", "reject"):
        assert decision in intake
    for mapping in (
        "pre_draft_quality_runtime",
        "authoring workplan projection",
        "evidence_ledger",
        "review_ledger",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "Artifact OS",
        "Evaluation OS",
        "Runtime OS",
        "Quality OS",
        "citation, numeric grounding, display grounding, internal-language leakage, and artifact rebuild proof",
    ):
        assert mapping in intake


def test_paper_orchestra_intake_preserves_mas_authority_boundaries() -> None:
    intake = _read(INTAKE_PATH)

    for boundary in (
        "不是引入 PaperOrchestra 作为 MAS runtime",
        "This does not create a PaperOrchestra runtime inside MAS",
        "Mechanical gates cannot authorize scientific quality or submission readiness",
        "No second publication owner is introduced",
        "不让 deterministic gate 替代 AI reviewer-backed `publication_eval/latest.json`",
        "不让 agent cache aggregation 替代 MAS durable evidence 或 review ledger",
        "study truth",
        "publication judgment",
        "artifact authority",
        "controller decisions",
    ):
        assert boundary in intake


def test_paper_orchestra_intake_records_saturation_protocol() -> None:
    intake = _read(INTAKE_PATH)

    for required in (
        "Continued Learning Saturation Protocol",
        "MAS-actionable saturated",
        "source file coverage",
        "`saturated_by_existing_contract`",
        "`new_contract_landing`",
        "`new_template_landing`",
        "`reject_saturated`",
        "CS-conference-specific mechanics",
        "generic LaTeX packaging",
        "non-medical benchmark labels",
        "provider-specific plotting runtime",
        "paper autoraters",
        "PaperWritingBench",
        "future Evaluation OS calibration",
    ):
        assert required in intake
