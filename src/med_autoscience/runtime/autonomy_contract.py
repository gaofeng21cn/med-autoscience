from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


def require_text(label: str, value: Any) -> str:
    raw = value.value if hasattr(value, "value") else value
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"autonomy governance {label} must be non-empty")
    return raw.strip()


def normalize_text_sequence(label: str, values: Iterable[Any] | None) -> tuple[str, ...]:
    if values is None:
        return ()
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = require_text(label, value)
        if text in seen:
            continue
        normalized.append(text)
        seen.add(text)
    return tuple(normalized)


@dataclass(frozen=True)
class AutonomyGovernanceContract:
    lane_id: str
    continuation_scope: str
    next_stage: str
    human_gate_class: str
    requires_human_confirmation: bool
    controller_action_types: tuple[str, ...]
    decision_type: str
    reason_code: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "lane_id", require_text("lane_id", self.lane_id))
        object.__setattr__(self, "continuation_scope", require_text("continuation_scope", self.continuation_scope))
        object.__setattr__(self, "next_stage", require_text("next_stage", self.next_stage))
        object.__setattr__(self, "human_gate_class", require_text("human_gate_class", self.human_gate_class))
        if not isinstance(self.requires_human_confirmation, bool):
            raise TypeError("autonomy governance requires_human_confirmation must be bool")
        object.__setattr__(
            self,
            "controller_action_types",
            normalize_text_sequence("controller_action_types", self.controller_action_types),
        )
        object.__setattr__(self, "decision_type", require_text("decision_type", self.decision_type))
        object.__setattr__(self, "reason_code", require_text("reason_code", self.reason_code))

    def to_dict(self) -> dict[str, object]:
        return {
            "contract_kind": "study_autonomy_governance_contract",
            "lane_id": self.lane_id,
            "continuation_scope": self.continuation_scope,
            "next_stage": self.next_stage,
            "human_gate_class": self.human_gate_class,
            "requires_human_confirmation": self.requires_human_confirmation,
            "controller_action_types": list(self.controller_action_types),
            "decision_type": self.decision_type,
            "reason_code": self.reason_code,
        }

