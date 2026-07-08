from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.runtime_control import owner_callable_registry


def owner_token(value: str | None) -> str:
    normalized = (value or "").strip().lower().replace("-", "_")
    if ":" in normalized:
        normalized = normalized.split(":", 1)[0].strip()
    compact = normalized.replace("/", "_")
    if (
        compact == "mas_controller"
        or "mas controller" in normalized
        or ("mas" in normalized and "controller" in normalized and "route authorization owner" in normalized)
    ):
        return "mas/controller"
    return normalized


def blocked_closeout_owner_handoff_authorization(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    blocked_closeout: dict[str, Any],
    next_owner: str,
) -> dict[str, Any] | None:
    owner_callable = _callable_for_owner_token(next_owner)
    if owner_callable is None:
        return None
    owner = str(owner_callable.get("owner") or "").strip()
    action_type = str(owner_callable.get("action_type") or "").strip()
    callable_surface = str(owner_callable.get("callable_surface") or "").strip()
    if not owner or not action_type or not callable_surface:
        return None
    previous_authorization = runtime_state.get("last_controller_decision_authorization")
    previous_authorization = previous_authorization if isinstance(previous_authorization, dict) else {}
    blocked_reason = str(blocked_closeout.get("blocked_reason") or "").strip() or "blocked_turn_closeout_owner_handoff"
    route_target = str(previous_authorization.get("route_target") or "").strip() or None
    study_id = (
        str(previous_authorization.get("study_id") or "").strip()
        or str(runtime_state.get("study_id") or "").strip()
        or quest_root.name
    )
    quest_id = (
        str(previous_authorization.get("quest_id") or "").strip()
        or str(runtime_state.get("quest_id") or "").strip()
        or quest_root.name
    )
    next_work_unit: dict[str, Any] = {
        "unit_id": action_type,
        "owner": owner,
        "required_output": owner_callable.get("required_outputs"),
    }
    if route_target:
        next_work_unit["lane"] = route_target
    return {
        "authorization_basis": "blocked_turn_closeout_owner_handoff",
        "study_id": study_id,
        "quest_id": quest_id,
        "source_run_id": str(blocked_closeout.get("run_id") or "").strip() or None,
        "source_closeout_path": str(blocked_closeout.get("closeout_path") or "").strip() or None,
        "source_blocked_reason": blocked_reason,
        "blocked_reason": blocked_reason,
        "previous_controller_decision_id": str(previous_authorization.get("decision_id") or "").strip() or None,
        "controller_actions": [action_type],
        "next_owner": owner,
        "work_unit_id": action_type,
        "work_unit_fingerprint": f"{owner_token(owner)}::{action_type}::{blocked_reason}",
        "next_work_unit": next_work_unit,
        "owner_callable_surface": callable_surface,
        "required_output_surface": owner_callable.get("required_outputs"),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "medical_claim_authoring_allowed": False,
        "current_package_write_allowed": False,
    }


def _callable_for_owner_token(raw_owner_token: str) -> dict[str, Any] | None:
    normalized_owner = owner_token(raw_owner_token)
    if normalized_owner == "controller":
        normalized_owner = "mas/controller"
    matches = [
        dict(payload)
        for owner, payload in owner_callable_registry().items()
        if owner_token(owner) == normalized_owner
        or (normalized_owner == "mas_controller" and owner_token(owner) == "mas/controller")
    ]
    if len(matches) != 1:
        return None
    return matches[0]


__all__ = [
    "blocked_closeout_owner_handoff_authorization",
    "owner_token",
]
