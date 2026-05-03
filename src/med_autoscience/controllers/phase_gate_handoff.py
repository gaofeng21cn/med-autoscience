from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_SUPPORTED_TRANSITIONS = frozenset(
    {
        ("analysis-campaign", "write"),
        ("write", "finalize"),
    }
)
_PASS_GATE_RESULTS = frozenset({"PASS", "pass"})
_PRODUCT_EXPERIMENT_TERMS = (
    "a/b",
    "ab test",
    "activation",
    "conversion",
    "growth metric",
    "retention",
    "variant",
)


@dataclass(frozen=True)
class AnalysisCampaignPlan:
    active_hypothesis: str
    endpoint: str
    cohort_data_constraints: tuple[str, ...]
    statistical_method: str
    subgroup_multiplicity_guardrails: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    failure_criteria: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "active_hypothesis": self.active_hypothesis,
            "endpoint": self.endpoint,
            "cohort_data_constraints": list(self.cohort_data_constraints),
            "statistical_method": self.statistical_method,
            "subgroup_multiplicity_guardrails": list(self.subgroup_multiplicity_guardrails),
            "acceptance_criteria": list(self.acceptance_criteria),
            "failure_criteria": list(self.failure_criteria),
        }


@dataclass(frozen=True)
class PhaseGateHandoff:
    from_route: str
    to_route: str
    study_id: str
    quest_id: str
    preconditions: tuple[str, ...]
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    gate_result: str
    decision_owner: str
    carry_forward_risks: tuple[str, ...]
    next_route: str
    analysis_campaign_plan: AnalysisCampaignPlan | None = None

    @property
    def transition_id(self) -> str:
        return f"{self.from_route}->{self.to_route}"

    @property
    def advance_allowed(self) -> bool:
        return self.gate_result in _PASS_GATE_RESULTS and self.next_route == self.to_route

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "surface": "phase_gate_handoff",
            "schema_version": 1,
            "transition_id": self.transition_id,
            "from_route": self.from_route,
            "to_route": self.to_route,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "preconditions": list(self.preconditions),
            "input_refs": list(self.input_refs),
            "output_refs": list(self.output_refs),
            "evidence_refs": list(self.evidence_refs),
            "acceptance_criteria": list(self.acceptance_criteria),
            "gate_result": self.gate_result,
            "decision_owner": self.decision_owner,
            "carry_forward_risks": list(self.carry_forward_risks),
            "next_route": self.next_route,
            "advance_allowed": self.advance_allowed,
        }
        if self.analysis_campaign_plan is not None:
            payload["analysis_campaign_plan"] = self.analysis_campaign_plan.to_dict()
        return payload


def _text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field} is required")
    return text


def _texts(value: object, field: str) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise ValueError(f"{field} must be a non-empty list")
    items = tuple(text for item in value if (text := str(item or "").strip()))
    if not items:
        raise ValueError(f"{field} must be a non-empty list")
    return items


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be a mapping")
    return value


def _reject_product_experiment_authority(payload: Mapping[str, Any]) -> None:
    tokens: list[str] = []
    for value in payload.values():
        if isinstance(value, str):
            tokens.append(value.lower())
        elif isinstance(value, list | tuple):
            tokens.extend(str(item).lower() for item in value)
    searchable = " ".join(tokens)
    if any(term in searchable for term in _PRODUCT_EXPERIMENT_TERMS):
        raise ValueError("analysis_campaign_plan must not use product experiment authority")


def validate_analysis_campaign_plan(payload: Mapping[str, Any]) -> AnalysisCampaignPlan:
    plan = _mapping(payload, "analysis_campaign_plan")
    _reject_product_experiment_authority(plan)
    return AnalysisCampaignPlan(
        active_hypothesis=_text(plan.get("active_hypothesis"), "analysis_campaign_plan.active_hypothesis"),
        endpoint=_text(plan.get("endpoint"), "analysis_campaign_plan.endpoint"),
        cohort_data_constraints=_texts(
            plan.get("cohort_data_constraints"),
            "analysis_campaign_plan.cohort_data_constraints",
        ),
        statistical_method=_text(plan.get("statistical_method"), "analysis_campaign_plan.statistical_method"),
        subgroup_multiplicity_guardrails=_texts(
            plan.get("subgroup_multiplicity_guardrails"),
            "analysis_campaign_plan.subgroup_multiplicity_guardrails",
        ),
        acceptance_criteria=_texts(
            plan.get("acceptance_criteria"),
            "analysis_campaign_plan.acceptance_criteria",
        ),
        failure_criteria=_texts(
            plan.get("failure_criteria"),
            "analysis_campaign_plan.failure_criteria",
        ),
    )


def build_phase_gate_handoff(payload: Mapping[str, Any]) -> PhaseGateHandoff:
    handoff = _mapping(payload, "phase_gate_handoff")
    from_route = _text(handoff.get("from_route"), "from_route")
    to_route = _text(handoff.get("to_route"), "to_route")
    if (from_route, to_route) not in _SUPPORTED_TRANSITIONS:
        raise ValueError(f"unsupported phase gate transition: {from_route}->{to_route}")

    analysis_campaign_plan = None
    if (from_route, to_route) == ("analysis-campaign", "write"):
        analysis_campaign_plan = validate_analysis_campaign_plan(
            _mapping(handoff.get("analysis_campaign_plan"), "analysis_campaign_plan")
        )
    elif handoff.get("analysis_campaign_plan") is not None:
        analysis_campaign_plan = validate_analysis_campaign_plan(
            _mapping(handoff.get("analysis_campaign_plan"), "analysis_campaign_plan")
        )

    record = PhaseGateHandoff(
        from_route=from_route,
        to_route=to_route,
        study_id=_text(handoff.get("study_id"), "study_id"),
        quest_id=_text(handoff.get("quest_id"), "quest_id"),
        preconditions=_texts(handoff.get("preconditions"), "preconditions"),
        input_refs=_texts(handoff.get("input_refs"), "input_refs"),
        output_refs=_texts(handoff.get("output_refs"), "output_refs"),
        evidence_refs=_texts(handoff.get("evidence_refs"), "evidence_refs"),
        acceptance_criteria=_texts(handoff.get("acceptance_criteria"), "acceptance_criteria"),
        gate_result=_text(handoff.get("gate_result"), "gate_result"),
        decision_owner=_text(handoff.get("decision_owner"), "decision_owner"),
        carry_forward_risks=_texts(handoff.get("carry_forward_risks"), "carry_forward_risks"),
        next_route=_text(handoff.get("next_route"), "next_route"),
        analysis_campaign_plan=analysis_campaign_plan,
    )
    if not record.advance_allowed:
        raise ValueError("phase gate handoff does not allow advance")
    return record
