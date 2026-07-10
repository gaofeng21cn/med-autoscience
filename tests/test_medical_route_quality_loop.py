import pytest
from med_autoscience.controllers import phase_gate_handoff as phase

pytestmark = pytest.mark.meta


def _payload():
    plan = dict(
        active_hypothesis="clinical risk", endpoint="mortality", cohort_data_constraints=["frozen cohort"],
        statistical_method="Cox model", subgroup_multiplicity_guardrails=["prespecified"],
        acceptance_criteria=["reportable"], failure_criteria=["invalid endpoint"],
    )
    return dict(
        from_route="analysis-campaign", to_route="write", study_id="s", quest_id="q",
        preconditions=["ready"], input_refs=["input"], output_refs=["output"], evidence_refs=["evidence"],
        acceptance_criteria=["supported"], gate_result="PASS", decision_owner="controller",
        carry_forward_risks=["none"], next_route="write", analysis_campaign_plan=plan,
    )


def test_phase_gate_handoff_accepts_complete_pass():
    record = phase.build_phase_gate_handoff(_payload())
    assert (record.transition_id, record.advance_allowed, record.analysis_campaign_plan.endpoint) == (
        "analysis-campaign->write", True, "mortality"
    )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [("gate_result", "NEEDS_REVIEW", "does not allow advance"),
     ("analysis_campaign_plan.statistical_method", "", "statistical_method"),
     ("analysis_campaign_plan.active_hypothesis", "Variant A improves conversion", "product experiment authority")],
)
def test_phase_gate_handoff_rejects_invalid_authority(field, value, message):
    payload = _payload()
    target = payload["analysis_campaign_plan"] if "." in field else payload
    target[field.rsplit(".", 1)[-1]] = value
    with pytest.raises(ValueError, match=message):
        phase.build_phase_gate_handoff(payload)
