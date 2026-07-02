from __future__ import annotations

from med_autoscience.research_integrity import build_manuscript_consistency_meta_review


def test_manuscript_consistency_meta_review_clear_surface() -> None:
    result = build_manuscript_consistency_meta_review(
        manuscript_sections={
            "abstract": {"numeric_facts": [_fact("cohort_n", 312)]},
            "results": {"numeric_facts": [_fact("cohort_n", "312.0")]},
            "tables": {"numeric_facts": [_fact("cohort_n", 312)]},
            "figures": {"numeric_facts": [_fact("cohort_n", 312)]},
        },
        numeric_facts=[_fact("cohort_n", 312)],
        display_facts=[{"display_id": "Table1", **_fact("cohort_n", 312)}],
        reporting_checklist_expectations=[
            {"item_id": "cohort_flow_diagram", "status": "complete"},
        ],
    )

    assert result["surface_kind"] == "manuscript_consistency_meta_review"
    assert result["schema_version"] == 1
    assert result["status"] == "clear"
    assert result["findings"] == []
    assert result["blocker_candidates"] == []
    assert all(value is False for value in result["authority_boundary"].values())


def test_manuscript_consistency_meta_review_blocks_hard_conflicts_and_missing_checklist() -> None:
    result = build_manuscript_consistency_meta_review(
        manuscript_sections={
            "abstract": {
                "numeric_facts": [_fact("cohort_n", 312)],
                "logic_claims": [{"logic_id": "main_conclusion", "polarity": "benefit"}],
            },
            "results": {
                "numeric_facts": [_fact("cohort_n", 321), _fact("follow_up", 5, unit="years")],
                "logic_claims": [{"logic_id": "main_conclusion", "polarity": "no_benefit"}],
            },
            "tables": {"numeric_facts": [_fact("follow_up", 5, unit="months")]},
            "figures": {"numeric_facts": [_fact("cohort_n", 312)]},
        },
        numeric_facts=[_fact("cohort_n", 312), _fact("follow_up", 5, unit="years")],
        display_facts=[{"display_id": "Figure1", **_fact("cohort_n", 300)}],
        reporting_checklist_expectations=[
            {"item_id": "observed_event_rate_and_denominators", "status": "missing"},
        ],
    )

    assert result["status"] == "blocked"
    finding_codes = {finding["code"] for finding in result["findings"]}
    assert finding_codes == {
        "display_to_claim_mismatch",
        "numeric_fact_inconsistent",
        "reporting_guideline_checklist_gap",
        "section_logic_contradiction",
        "unit_population_window_mismatch",
    }
    blocker_reasons = {candidate["reason"] for candidate in result["blocker_candidates"]}
    assert blocker_reasons == finding_codes
    assert all(candidate["refs_only"] is True for candidate in result["blocker_candidates"])
    assert all(candidate["can_block_current_owner_action"] is False for candidate in result["blocker_candidates"])


def test_optional_reporting_gap_needs_review_without_blocker_candidate() -> None:
    result = build_manuscript_consistency_meta_review(
        manuscript_sections={
            "abstract": {"numeric_facts": [_fact("event_rate", "7.5", unit="%")]},
            "results": {"numeric_facts": [_fact("event_rate", "7.5", unit="%")]},
            "tables": {"numeric_facts": [_fact("event_rate", "7.5", unit="%")]},
            "figures": {"numeric_facts": [_fact("event_rate", "7.5", unit="%")]},
        },
        numeric_facts=[_fact("event_rate", "7.5", unit="%")],
        display_facts=[{"display_id": "Figure2", **_fact("event_rate", "7.5", unit="%")}],
        reporting_checklist_expectations=[
            {"item_id": "decision_curve_threshold_rationale", "status": "missing", "required": False},
        ],
    )

    assert result["status"] == "needs_review"
    assert result["blocker_candidates"] == []
    assert result["findings"] == [
        {
            "code": "reporting_guideline_checklist_gap",
            "severity": "review",
            "fact_id": "decision_curve_threshold_rationale",
            "message": "Reporting guideline checklist expectation is not closed.",
            "evidence": {"status": "missing", "required": False},
        }
    ]


def _fact(
    fact_id: str,
    value: object,
    *,
    unit: str = "patients",
    population: str = "eligible cohort",
    window: str = "2018-2022",
) -> dict[str, object]:
    return {
        "fact_id": fact_id,
        "reported_value": value,
        "unit": unit,
        "population": population,
        "window": window,
    }
