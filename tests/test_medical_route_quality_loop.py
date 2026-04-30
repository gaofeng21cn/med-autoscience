from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _combined_quality_docs() -> str:
    return "\n".join(
        (
            _read("docs/runtime/agent_entry_modes.md"),
            _read("docs/policies/evidence_review_contract.md"),
            _read("templates/codex/medautoscience-entry.SKILL.md"),
            _read("templates/openclaw/medautoscience-entry.prompt.md"),
        )
    )


def test_medical_route_quality_loop_is_rendered_from_agent_entry_contract() -> None:
    combined = _combined_quality_docs()

    for required in (
        "Medical Route Quality Loop",
        "bounded medical repair loop",
        "default needs review gate",
        "phase gate handoff",
        "analysis-campaign statistical discipline",
        "incident postmortem feedback loop",
    ):
        assert required in combined


def test_bounded_medical_repair_loop_requires_attempts_verdicts_and_escalation_refs() -> None:
    combined = _combined_quality_docs()

    for required in (
        "attempt_count",
        "verdict",
        "finding_refs",
        "fix_refs",
        "acceptance_criteria",
        "next_route",
        "escalation_ref",
        "explicit retry budget",
        "runtime_escalation_record.json",
        "不能无限重试",
    ):
        assert required in combined

    for verdict in ("PASS", "FAIL", "NEEDS_REVIEW"):
        assert verdict in combined


def test_default_needs_review_blocks_claim_only_ready_labels() -> None:
    combined = _combined_quality_docs()

    for required in (
        "readiness defaults to `NEEDS_REVIEW`",
        "durable evidence refs",
        "review refs",
        "AI reviewer-backed `publication_eval/latest.json`",
        "zero-issue",
        "production-ready",
        "owner decision surface",
    ):
        assert required in combined


def test_phase_gate_handoff_requires_evidence_and_decision_owner_before_advance() -> None:
    combined = _combined_quality_docs()

    for required in (
        "preconditions",
        "input refs",
        "output refs",
        "evidence refs",
        "gate result",
        "decision owner",
        "carry-forward risks",
        "no phase, route, write, finalize, or submission-facing advance may proceed",
        "claim-only",
    ):
        assert required in combined


def test_analysis_campaign_statistical_discipline_rejects_product_experiment_authority() -> None:
    combined = _combined_quality_docs()

    for required in (
        "active hypothesis",
        "endpoint",
        "cohort/data quality constraints",
        "statistical method",
        "subgroup or multiplicity guardrails",
        "sample-size, power, precision, or feasibility rationale",
        "product A/B testing vocabulary",
        "generic experiment success labels",
        "must not become medical evidence authority",
    ):
        assert required in combined


def test_incident_postmortem_loop_cannot_relax_evidence_or_reviewer_gates() -> None:
    combined = _combined_quality_docs()

    for required in (
        "timeline",
        "impact",
        "root cause",
        "prevention action",
        "follow-up status",
        "runtime recovery",
        "publication gate",
        "stale package",
        "evidence-review failures",
        "must not relax evidence gates, publication gates, or AI reviewer requirements",
        "不能放松 evidence gate、publication gate 或 AI reviewer requirement",
    ):
        assert required in combined
