from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.controllers.phase_gate_handoff import (
    build_phase_gate_handoff,
    validate_analysis_campaign_plan,
)


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


def test_phase_gate_handoff_typed_record_allows_analysis_campaign_to_write_when_plan_is_complete() -> None:
    record = build_phase_gate_handoff(
        {
            "from_route": "analysis-campaign",
            "to_route": "write",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "preconditions": ["publication_eval routes same-line blocker to bounded analysis"],
            "input_refs": ["artifacts/publication_eval/latest.json"],
            "output_refs": ["paper/analysis_campaign_summary.json"],
            "evidence_refs": ["paper/evidence_ledger.json#analysis-campaign-001"],
            "acceptance_criteria": ["write may cite only claims supported by generated result refs"],
            "gate_result": "PASS",
            "decision_owner": "controller",
            "carry_forward_risks": ["subgroup estimates remain exploratory"],
            "next_route": "write",
            "analysis_campaign_plan": {
                "active_hypothesis": "High-risk phenotype is associated with time-to-event outcome.",
                "endpoint": "time_to_event_mortality",
                "cohort_data_constraints": ["complete baseline covariates", "minimum follow-up window documented"],
                "statistical_method": "Cox proportional hazards model with prespecified covariates",
                "subgroup_multiplicity_guardrails": [
                    "subgroup analyses are prespecified",
                    "multiplicity handled by false discovery rate disclosure",
                ],
                "acceptance_criteria": ["effect direction and uncertainty are reportable"],
                "failure_criteria": ["non-convergence or missing endpoint invalidates downstream claim"],
            },
        }
    )

    assert record.transition_id == "analysis-campaign->write"
    assert record.advance_allowed is True
    assert record.analysis_campaign_plan is not None
    assert record.to_dict()["analysis_campaign_plan"]["statistical_method"].startswith("Cox")


def test_phase_gate_handoff_typed_record_allows_write_to_finalize_without_analysis_plan() -> None:
    record = build_phase_gate_handoff(
        {
            "from_route": "write",
            "to_route": "finalize",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "preconditions": ["draft claims match evidence ledger"],
            "input_refs": ["paper/manuscript_draft.md", "paper/review_ledger.json"],
            "output_refs": ["manuscript/current_package/README.md"],
            "evidence_refs": ["artifacts/publication_eval/latest.json"],
            "acceptance_criteria": ["finalize may only package AI-reviewed draft state"],
            "gate_result": "PASS",
            "decision_owner": "controller",
            "carry_forward_risks": ["journal-specific metadata remains administrative"],
            "next_route": "finalize",
        }
    )

    assert record.transition_id == "write->finalize"
    assert record.advance_allowed is True
    assert record.analysis_campaign_plan is None


def test_phase_gate_handoff_blocks_write_to_finalize_when_gate_is_not_passed() -> None:
    with pytest.raises(ValueError, match="does not allow advance"):
        build_phase_gate_handoff(
            {
                "from_route": "write",
                "to_route": "finalize",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "preconditions": ["draft claims match evidence ledger"],
                "input_refs": ["paper/manuscript_draft.md"],
                "output_refs": ["manuscript/current_package/README.md"],
                "evidence_refs": ["artifacts/publication_eval/latest.json"],
                "acceptance_criteria": ["AI reviewer-backed draft state required"],
                "gate_result": "NEEDS_REVIEW",
                "decision_owner": "controller",
                "carry_forward_risks": ["review gap remains open"],
                "next_route": "finalize",
            }
        )


def test_phase_gate_handoff_blocks_analysis_campaign_to_write_without_complete_plan() -> None:
    with pytest.raises(ValueError, match="analysis_campaign_plan.statistical_method"):
        build_phase_gate_handoff(
            {
                "from_route": "analysis-campaign",
                "to_route": "write",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "preconditions": ["bounded analysis completed"],
                "input_refs": ["artifacts/publication_eval/latest.json"],
                "output_refs": ["paper/analysis_campaign_summary.json"],
                "evidence_refs": ["paper/evidence_ledger.json#analysis-campaign-001"],
                "acceptance_criteria": ["write may cite only supported claims"],
                "gate_result": "PASS",
                "decision_owner": "controller",
                "carry_forward_risks": ["none"],
                "next_route": "write",
                "analysis_campaign_plan": {
                    "active_hypothesis": "Risk phenotype is associated with endpoint.",
                    "endpoint": "time_to_event_mortality",
                    "cohort_data_constraints": ["complete baseline covariates"],
                    "subgroup_multiplicity_guardrails": ["prespecified subgroup only"],
                    "acceptance_criteria": ["reportable uncertainty"],
                    "failure_criteria": ["invalid endpoint"],
                },
            }
        )


def test_analysis_campaign_plan_rejects_product_experiment_authority() -> None:
    with pytest.raises(ValueError, match="product experiment authority"):
        validate_analysis_campaign_plan(
            {
                "active_hypothesis": "Variant A improves conversion.",
                "endpoint": "activation",
                "cohort_data_constraints": ["eligible users"],
                "statistical_method": "A/B test conversion lift",
                "subgroup_multiplicity_guardrails": ["segment readout"],
                "acceptance_criteria": ["growth metric improves"],
                "failure_criteria": ["retention drops"],
            }
        )


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
