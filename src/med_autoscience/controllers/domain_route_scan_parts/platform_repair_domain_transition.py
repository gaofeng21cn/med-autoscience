from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner
from med_autoscience.profiles import WorkspaceProfile


def text(value: object) -> str | None:
    item = str(value or "").strip()
    return item or None


def apply_domain_transition_runtime_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    status: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
    apply_current_controller_runtime_redrive: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    decision_type = domain_transition_guard.runtime_redrive_decision_type(status)
    if decision_type is None:
        return None
    if decision_type == "ai_reviewer_re_eval":
        return None
    story_surface_redrive = _story_surface_delta_redrive(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        runtime_state_path=runtime_state_path,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        base=base,
        decision_type=decision_type,
        apply_current_controller_runtime_redrive=apply_current_controller_runtime_redrive,
    )
    if story_surface_redrive is not None:
        return story_surface_redrive
    if decision_type == "publication_gate_blocker":
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": "domain_transition_publication_gate_blocker",
            "repair_kind": "domain_transition_publication_gate_blocker",
            "domain_transition_decision_type": decision_type,
        }
    route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if route is None:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": domain_transition_guard.CURRENT_ROUTE_MISSING_REASON,
            "repair_kind": f"domain_transition_{decision_type}_redrive",
            "domain_transition_decision_type": decision_type,
        }
    apply_result = apply_current_controller_runtime_redrive(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        runtime_state_path=runtime_state_path,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        base={**dict(base), "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON},
        repair_kind=f"domain_transition_{decision_type}_redrive",
    )
    return {
        **apply_result,
        "domain_transition_decision_type": decision_type,
        "domain_transition_controller_route": route,
    }


def _story_surface_delta_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
    decision_type: str,
    apply_current_controller_runtime_redrive: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    story_surface_route = current_truth_owner.current_story_surface_delta_blocker_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if story_surface_route is None:
        return None
    apply_result = apply_current_controller_runtime_redrive(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        runtime_state_path=runtime_state_path,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        base={**dict(base), "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON},
        repair_kind=f"domain_transition_{decision_type}_story_surface_delta_redrive",
    )
    return {
        **apply_result,
        "domain_transition_decision_type": decision_type,
        "domain_transition_controller_route": story_surface_route,
    }


__all__ = ["apply_domain_transition_runtime_redrive"]
