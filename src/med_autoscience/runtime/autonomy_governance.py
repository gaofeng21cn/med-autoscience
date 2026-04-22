from __future__ import annotations

from typing import Any, Iterable

from med_autoscience.runtime.autonomy_contract import (
    AutonomyGovernanceContract,
    normalize_text_sequence,
    require_text,
)


_AUTONOMOUS_SCIENTIFIC_DECISIONS = frozenset(
    {
        "continue_same_line",
        "route_back_same_line",
        "bounded_analysis",
    }
)
_AUTONOMOUS_RUNTIME_RECOVERY_DECISIONS = frozenset({"relaunch_branch"})
_MAJOR_HUMAN_GATE_DECISIONS = frozenset(
    {
        "reroute_study",
        "stop_loss",
        "promote_to_delivery",
    }
)


def _route_or_default(route_target: Any, default: str) -> str:
    if route_target is None:
        return default
    text = str(route_target).strip()
    return text or default


def _autonomous_contract(
    *,
    decision_type: str,
    controller_action_types: tuple[str, ...],
    route_target: str | None,
) -> AutonomyGovernanceContract:
    if decision_type == "bounded_analysis":
        return AutonomyGovernanceContract(
            lane_id="bounded_analysis",
            continuation_scope="bounded_supplementary_analysis",
            next_stage=_route_or_default(route_target, "analysis-campaign"),
            human_gate_class="none",
            requires_human_confirmation=False,
            controller_action_types=controller_action_types,
            decision_type=decision_type,
            reason_code="direction_locked_bounded_analysis_stays_autonomous",
        )
    if decision_type == "route_back_same_line":
        return AutonomyGovernanceContract(
            lane_id="same_line_route_back",
            continuation_scope="same_direction_quality_repair",
            next_stage=_route_or_default(route_target, "write"),
            human_gate_class="none",
            requires_human_confirmation=False,
            controller_action_types=controller_action_types,
            decision_type=decision_type,
            reason_code="direction_locked_same_line_repair_stays_autonomous",
        )
    return AutonomyGovernanceContract(
        lane_id="same_line_continuation",
        continuation_scope="same_direction_continuation",
        next_stage=_route_or_default(route_target, "write"),
        human_gate_class="none",
        requires_human_confirmation=False,
        controller_action_types=controller_action_types,
        decision_type=decision_type,
        reason_code="direction_locked_same_line_continuation_stays_autonomous",
    )


def _major_gate_contract(
    *,
    decision_type: str,
    controller_action_types: tuple[str, ...],
    route_target: str | None,
    major_anomaly: bool,
    explicit_human_override: bool,
) -> AutonomyGovernanceContract:
    if explicit_human_override:
        return AutonomyGovernanceContract(
            lane_id="human_override",
            continuation_scope="explicit_human_override",
            next_stage="human_override_review",
            human_gate_class="explicit_human_override",
            requires_human_confirmation=True,
            controller_action_types=controller_action_types,
            decision_type=decision_type,
            reason_code="explicit_human_override_requires_human_gate",
        )
    if decision_type == "promote_to_delivery":
        return AutonomyGovernanceContract(
            lane_id="final_submission_audit",
            continuation_scope="pre_submission_final_audit",
            next_stage=_route_or_default(route_target, "submission"),
            human_gate_class="final_submission_audit",
            requires_human_confirmation=True,
            controller_action_types=controller_action_types,
            decision_type=decision_type,
            reason_code="final_submission_audit_requires_human_gate",
        )
    if decision_type == "stop_loss" or major_anomaly:
        return AutonomyGovernanceContract(
            lane_id="major_anomaly_review",
            continuation_scope="major_anomaly_boundary",
            next_stage="major_anomaly_review",
            human_gate_class="major_anomaly",
            requires_human_confirmation=True,
            controller_action_types=controller_action_types,
            decision_type=decision_type,
            reason_code="major_anomaly_requires_human_gate",
        )
    return AutonomyGovernanceContract(
        lane_id="direction_reset",
        continuation_scope="direction_boundary_reset",
        next_stage="direction_reset_review",
        human_gate_class="direction_reset",
        requires_human_confirmation=True,
        controller_action_types=controller_action_types,
        decision_type=decision_type,
        reason_code="direction_reset_requires_human_gate",
    )


def build_autonomy_governance_contract(
    *,
    decision_type: Any,
    controller_action_types: Iterable[Any] | None = None,
    route_target: Any = None,
    requires_human_confirmation: bool,
    direction_locked: bool = True,
    major_anomaly: bool = False,
    explicit_human_override: bool = False,
) -> dict[str, object]:
    normalized_decision_type = require_text("decision_type", decision_type)
    normalized_action_types = normalize_text_sequence("controller_action_types", controller_action_types)
    if not isinstance(requires_human_confirmation, bool):
        raise TypeError("autonomy governance requires_human_confirmation must be bool")
    if not isinstance(direction_locked, bool):
        raise TypeError("autonomy governance direction_locked must be bool")
    if not isinstance(major_anomaly, bool):
        raise TypeError("autonomy governance major_anomaly must be bool")
    if not isinstance(explicit_human_override, bool):
        raise TypeError("autonomy governance explicit_human_override must be bool")

    if not direction_locked:
        if not requires_human_confirmation:
            raise ValueError("direction-unlocked controller decisions must require human confirmation")
        return AutonomyGovernanceContract(
            lane_id="direction_lock_required",
            continuation_scope="direction_lock",
            next_stage="direction_lock",
            human_gate_class="direction_not_locked",
            requires_human_confirmation=True,
            controller_action_types=normalized_action_types,
            decision_type=normalized_decision_type,
            reason_code="direction_not_locked_requires_human_gate",
        ).to_dict()

    if major_anomaly or explicit_human_override:
        if not requires_human_confirmation:
            raise ValueError("major controller boundary decisions must require human confirmation")
        return _major_gate_contract(
            decision_type=normalized_decision_type,
            controller_action_types=normalized_action_types,
            route_target=str(route_target).strip() if route_target is not None else None,
            major_anomaly=major_anomaly,
            explicit_human_override=explicit_human_override,
        ).to_dict()

    if normalized_decision_type in _AUTONOMOUS_RUNTIME_RECOVERY_DECISIONS:
        if requires_human_confirmation:
            raise ValueError("autonomous MAS decision cannot require human confirmation")
        return AutonomyGovernanceContract(
            lane_id="runtime_recovery",
            continuation_scope="same_study_runtime_recovery",
            next_stage=_route_or_default(route_target, "runtime_recovery"),
            human_gate_class="none",
            requires_human_confirmation=False,
            controller_action_types=normalized_action_types,
            decision_type=normalized_decision_type,
            reason_code="direction_locked_runtime_recovery_stays_autonomous",
        ).to_dict()

    if normalized_decision_type in _AUTONOMOUS_SCIENTIFIC_DECISIONS:
        if requires_human_confirmation:
            raise ValueError("autonomous MAS decision cannot require human confirmation")
        return _autonomous_contract(
            decision_type=normalized_decision_type,
            controller_action_types=normalized_action_types,
            route_target=str(route_target).strip() if route_target is not None else None,
        ).to_dict()

    if normalized_decision_type == "stop_loss" and not requires_human_confirmation:
        return AutonomyGovernanceContract(
            lane_id="controller_stop",
            continuation_scope="runtime_stop_contract",
            next_stage=_route_or_default(route_target, "stopped"),
            human_gate_class="none",
            requires_human_confirmation=False,
            controller_action_types=normalized_action_types,
            decision_type=normalized_decision_type,
            reason_code="controller_stop_contract_does_not_create_human_gate",
        ).to_dict()

    if normalized_decision_type in _MAJOR_HUMAN_GATE_DECISIONS:
        if not requires_human_confirmation:
            raise ValueError("major controller boundary decisions must require human confirmation")
        return _major_gate_contract(
            decision_type=normalized_decision_type,
            controller_action_types=normalized_action_types,
            route_target=str(route_target).strip() if route_target is not None else None,
            major_anomaly=major_anomaly,
            explicit_human_override=explicit_human_override,
        ).to_dict()

    raise ValueError(f"unknown autonomy governance decision_type: {normalized_decision_type}")
