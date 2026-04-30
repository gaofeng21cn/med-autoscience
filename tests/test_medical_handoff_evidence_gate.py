from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_agent_entry_modes_documents_structured_medical_handoff_fields() -> None:
    doc = _read("docs/runtime/agent_entry_modes.md")

    assert "structured medical handoff" in doc
    for field in (
        "from_route",
        "to_route",
        "study_id",
        "quest_id",
        "active_claim_boundary",
        "changed_artifact_refs",
        "evidence_refs",
        "review_refs",
        "acceptance_criteria",
        "next_owner",
        "human_gate_reason",
    ):
        assert field in doc


def test_evidence_contract_requires_durable_medical_evidence_refs() -> None:
    doc = _read("docs/policies/evidence_review_contract.md")

    for ref in (
        "evidence_ledger",
        "review_ledger",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "manuscript/package refs",
    ):
        assert ref in doc
    assert "不能只靠聊天总结、memory 或 terminal prose" in doc
    assert "不能把 screenshot-style QA 当成证据面" in doc


def test_medical_qa_feedback_loop_routes_back_to_narrowest_route() -> None:
    combined = "\n".join(
        (
            _read("docs/runtime/agent_entry_modes.md"),
            _read("docs/policies/evidence_review_contract.md"),
        )
    )

    assert "PASS" in combined
    assert "FAIL" in combined
    assert "NEEDS_REVIEW" in combined
    assert "claim/evidence/rigor/submission hygiene gap" in combined
    assert "route back to the narrowest route" in combined
    assert "最窄 route" in combined


def test_ai_reviewer_gate_blocks_projection_only_quality_authority() -> None:
    combined = "\n".join(
        (
            _read("docs/runtime/agent_entry_modes.md"),
            _read("docs/policies/evidence_review_contract.md"),
        )
    )

    assert "AI reviewer-backed `publication_eval/latest.json`" in combined
    assert "reviewer-first ready" in combined
    assert "finalize-ready" in combined
    assert "review_required" in combined
    assert "projection_only" in combined
    assert "mechanical projection" in combined


def test_claim_only_ready_sources_cannot_be_medical_quality_authority() -> None:
    combined = "\n".join(
        (
            _read("docs/runtime/agent_entry_modes.md"),
            _read("docs/policies/evidence_review_contract.md"),
        )
    )

    for forbidden_authority in (
        "claim-only ready",
        "generic persona library",
        "non-medical QA gate",
        "NEXUS role approval",
        "screenshot-style QA",
        "MAS owner authority",
        "medical paper quality authority",
    ):
        assert forbidden_authority in combined
