from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import control_plane_state


AUTONOMY_STATES = control_plane_state.CONTROL_PLANE_STATES


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def autonomy_state_catalog() -> dict[str, dict[str, Any]]:
    return control_plane_state.control_plane_state_catalog()


def state_spec(state: str) -> dict[str, Any]:
    return control_plane_state.control_plane_state_spec(state)


def resolve_autonomy_state(profile_payload: Mapping[str, Any]) -> str:
    return control_plane_state.resolve_control_plane_state(profile_payload)


def build_autonomy_state_machine_surface(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    canonical = control_plane_state.build_control_plane_state_surface(profile_payload)
    current_state = canonical["current_state"]
    current_state_spec = _mapping(canonical["current_state_spec"])
    return {
        "surface": "autonomy_state_machine",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "current_state": current_state,
        "current_state_spec": dict(current_state_spec),
        "control_plane_state": canonical,
        "control_plane_facts": canonical["control_plane_facts"],
        "auto_runtime_parked": canonical["auto_runtime_parked"],
        "runtime_failure_classification": canonical["runtime_failure_classification"],
        "states": canonical["states"],
        "transition_policy": canonical["transition_policy"],
        "quality_constraint": canonical["quality_constraint"],
        "gate_relaxation_allowed": False,
        "owner": current_state_spec["owner"],
        "auto_recovery_allowed": current_state_spec["auto_recovery_allowed"],
        "resource_release_expected": current_state_spec["resource_release_expected"],
        "long_write_turn_allowed": current_state_spec["long_write_turn_allowed"],
        "operator_summary": current_state_spec["operator_summary"],
    }
