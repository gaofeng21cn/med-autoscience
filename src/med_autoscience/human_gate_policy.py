from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionType


@dataclass(frozen=True)
class HumanGatePolicyVerdict:
    decision_type: str
    allowed: bool
    category: str
    reason_code: str
    controller_action_types: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "decision_type": self.decision_type,
            "allowed": self.allowed,
            "category": self.category,
            "reason_code": self.reason_code,
            "controller_action_types": list(self.controller_action_types),
        }


_HUMAN_CONFIRMATION_DECISION_TYPES = frozenset(
    {
        StudyDecisionType.REROUTE_STUDY.value,
        StudyDecisionType.STOP_LOSS.value,
        StudyDecisionType.PROMOTE_TO_DELIVERY.value,
    }
)
_AUTONOMOUS_DECISION_TYPES = frozenset(
    {
        StudyDecisionType.CONTINUE_SAME_LINE.value,
        StudyDecisionType.RELAUNCH_BRANCH.value,
    }
)
_CATEGORY_BY_DECISION_TYPE = {
    StudyDecisionType.REROUTE_STUDY.value: "major_direction_pivot",
    StudyDecisionType.STOP_LOSS.value: "stop_loss",
    StudyDecisionType.PROMOTE_TO_DELIVERY.value: "final_submission_audit",
    StudyDecisionType.CONTINUE_SAME_LINE.value: "mas_autonomous_scientific_decision",
    StudyDecisionType.RELAUNCH_BRANCH.value: "mas_autonomous_runtime_recovery",
}


def _normalized_decision_type(value: object) -> str:
    raw = value.value if isinstance(value, StudyDecisionType) else value
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("human gate policy decision_type must be non-empty")
    normalized = raw.strip()
    try:
        return StudyDecisionType(normalized).value
    except ValueError as exc:
        raise ValueError(f"unknown human gate policy decision_type: {normalized}") from exc


def _normalized_action_types(values: Iterable[object] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        raw = value.value if isinstance(value, StudyDecisionActionType) else value
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("human gate policy controller action types must be non-empty")
        action_type = StudyDecisionActionType(raw.strip()).value
        if action_type in seen:
            continue
        normalized.append(action_type)
        seen.add(action_type)
    return tuple(normalized)


def controller_human_gate_policy(
    *,
    decision_type: object,
    controller_action_types: Iterable[object] | None = None,
) -> HumanGatePolicyVerdict:
    normalized_decision_type = _normalized_decision_type(decision_type)
    normalized_action_types = _normalized_action_types(controller_action_types)
    category = _CATEGORY_BY_DECISION_TYPE[normalized_decision_type]
    if normalized_decision_type in _HUMAN_CONFIRMATION_DECISION_TYPES:
        return HumanGatePolicyVerdict(
            decision_type=normalized_decision_type,
            allowed=True,
            category=category,
            reason_code="human_gate_allowed_for_major_boundary",
            controller_action_types=normalized_action_types,
        )
    if normalized_decision_type in _AUTONOMOUS_DECISION_TYPES:
        return HumanGatePolicyVerdict(
            decision_type=normalized_decision_type,
            allowed=False,
            category=category,
            reason_code="mas_autonomous_decision_must_not_create_human_gate",
            controller_action_types=normalized_action_types,
        )
    raise ValueError(f"unsupported human gate policy decision_type: {normalized_decision_type}")


def controller_human_gate_allowed(
    *,
    decision_type: object,
    controller_action_types: Iterable[object] | None = None,
) -> bool:
    return controller_human_gate_policy(
        decision_type=decision_type,
        controller_action_types=controller_action_types,
    ).allowed


def require_controller_human_gate_allowed(
    *,
    decision_type: object,
    controller_action_types: Iterable[object] | None = None,
) -> HumanGatePolicyVerdict:
    verdict = controller_human_gate_policy(
        decision_type=decision_type,
        controller_action_types=controller_action_types,
    )
    if not verdict.allowed:
        raise ValueError(
            "controller human confirmation is reserved for major direction pivots, stop-loss, "
            "and final submission audit decisions"
        )
    return verdict
