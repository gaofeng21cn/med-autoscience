from __future__ import annotations

from typing import Any, Mapping

from .export_study_projection import mapping, text


def current_supervisor_decision(current_progress: Mapping[str, Any]) -> Mapping[str, Any]:
    recovery = mapping(current_progress.get("paper_recovery_state"))
    for candidate in (
        current_progress.get("paper_autonomy_supervisor_decision"),
        current_progress.get("supervisor_decision"),
        recovery.get("supervisor_decision"),
        recovery.get("paper_autonomy_supervisor_decision"),
    ):
        decision = mapping(candidate)
        if decision:
            return decision
    return {}


def supervisor_stop_decision_matches_current_work_unit(
    *,
    supervisor_decision: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
) -> bool:
    if text(supervisor_decision.get("decision")) != "stop_with_stable_typed_blocker":
        return False
    if supervisor_decision.get("identity_match") is not True:
        return False
    obligation = mapping(supervisor_decision.get("paper_autonomy_obligation"))
    if not obligation:
        return False
    for key in ("study_id", "quest_id", "action_type", "work_unit_id"):
        expected = text(obligation.get(key))
        actual = text(current_work_unit.get(key))
        if expected is not None and actual is not None and expected != actual:
            return False
    expected_fingerprint = text(obligation.get("work_unit_fingerprint"))
    actual_fingerprint = text(current_work_unit.get("work_unit_fingerprint")) or text(
        current_work_unit.get("action_fingerprint")
    )
    return expected_fingerprint is not None and expected_fingerprint == actual_fingerprint


def supervisor_stop_decision_resolution_shapes(
    *,
    current_work_unit: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
) -> list[str]:
    contract = mapping(current_work_unit.get("required_output_contract"))
    obligation = mapping(supervisor_decision.get("paper_autonomy_obligation"))
    desired_delta = mapping(obligation.get("desired_delta"))
    shapes = _text_list(contract.get("accepted_return_shape")) or _text_list(
        desired_delta.get("required_output_ref_family")
    )
    if not shapes:
        shapes = [
            "domain_owner_receipt_ref",
            "quality_gate_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_evidence_ref",
        ]
    return shapes


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        normalized = text(value)
        return [normalized] if normalized is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        normalized = text(item)
        if normalized is not None and normalized not in result:
            result.append(normalized)
    return result
