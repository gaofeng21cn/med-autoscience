from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.runtime_control import owner_callable_for_action


def blocked_closeout_owner_handoff_authorization(
    runtime_state: Mapping[str, Any],
    *,
    action_names_for_authorization,
    mapping,
    text,
) -> dict[str, Any]:
    wakeup = runtime_state.get("last_explicit_user_wakeup")
    if not isinstance(wakeup, Mapping):
        return {}
    authorization = wakeup.get("owner_handoff_authorization")
    if not isinstance(authorization, Mapping):
        return {}
    normalized = dict(authorization)
    if text(normalized.get("authorization_basis")) != "blocked_turn_closeout_owner_handoff":
        return {}
    action_names = action_names_for_authorization(normalized)
    if len(action_names) != 1:
        return {}
    action_name = action_names[0]
    owner_callable = owner_callable_for_action(action_name)
    if not isinstance(owner_callable, Mapping):
        return {}
    next_owner = text(normalized.get("next_owner"))
    callable_owner = text(owner_callable.get("owner"))
    if next_owner is None or callable_owner is None or next_owner != callable_owner:
        return {}
    if text(normalized.get("owner_callable_surface")) != text(owner_callable.get("callable_surface")):
        return {}
    work_unit_id = text(normalized.get("work_unit_id"))
    if work_unit_id is None or work_unit_id != action_name:
        return {}
    next_work_unit = mapping(normalized.get("next_work_unit"))
    if text(next_work_unit.get("unit_id")) != action_name:
        return {}
    return normalized


def methodology_reframe_handoff_superseded_by_current_decision(
    authorization: Mapping[str, Any],
    current_authorization: Mapping[str, Any] | None,
    *,
    action_names_for_authorization,
    work_unit_ids_for_authorization,
    text,
) -> bool:
    if not isinstance(current_authorization, Mapping):
        return False
    if text(current_authorization.get("authorization_basis")) != "current_controller_decision":
        return False
    if "methodology_reframe_route_decision" not in action_names_for_authorization(authorization):
        return False
    if "methodology_reframe_route_decision" not in work_unit_ids_for_authorization(authorization):
        return False
    if text(authorization.get("next_owner")) != "decision":
        return False
    current_units = set(work_unit_ids_for_authorization(current_authorization))
    current_actions = set(action_names_for_authorization(current_authorization))
    if not current_units or "methodology_reframe_route_decision" in current_units:
        return False
    if "methodology_reframe_route_decision" in current_actions:
        return False
    downstream_units = {
        "provenance_limited_harmonization_audit",
        "unit_harmonized_external_validation_rerun",
        "unit_harmonized_validation_uncertainty_and_grouped_calibration",
    }
    downstream_actions = {
        "provenance_limited_harmonization_audit",
        "unit_harmonized_external_validation_rerun",
    }
    return bool(current_units.intersection(downstream_units) or current_actions.intersection(downstream_actions))


def terminal_source_provenance_handoff_superseded(
    authorization: Mapping[str, Any],
    *,
    study_root: Path | None,
    action_names_for_authorization,
    work_unit_ids_for_authorization,
    mapping,
    text,
) -> bool:
    if study_root is None:
        return False
    if "recover_transport_model_provenance" not in action_names_for_authorization(authorization):
        return False
    if text(authorization.get("next_owner")) != "source_provenance_owner":
        return False
    if "recover_transport_model_provenance" not in work_unit_ids_for_authorization(authorization):
        return False
    result = source_provenance_owner_result.read_result(study_root=study_root)
    if not source_provenance_owner_result.result_is_accepted_typed_blocker(result):
        return False
    return (
        text(mapping(result).get("next_owner")) == source_provenance_owner_result.TERMINAL_ROUTE_NEXT_OWNER
        and text(mapping(result).get("next_work_unit")) == "methodology_reframe_route_decision"
        and mapping(result).get("terminal_source_provenance_blocker") is True
    )


def owner_handoff_authorization_is_superseded(
    authorization: Mapping[str, Any],
    current_authorization: Mapping[str, Any] | None,
    *,
    terminal_source_provenance_superseded: bool,
    action_names_for_authorization,
    work_unit_ids_for_authorization,
    text,
) -> bool:
    return bool(terminal_source_provenance_superseded) or methodology_reframe_handoff_superseded_by_current_decision(
        authorization,
        current_authorization,
        action_names_for_authorization=action_names_for_authorization,
        work_unit_ids_for_authorization=work_unit_ids_for_authorization,
        text=text,
    )


__all__ = [
    "blocked_closeout_owner_handoff_authorization",
    "methodology_reframe_handoff_superseded_by_current_decision",
    "owner_handoff_authorization_is_superseded",
    "terminal_source_provenance_handoff_superseded",
]
