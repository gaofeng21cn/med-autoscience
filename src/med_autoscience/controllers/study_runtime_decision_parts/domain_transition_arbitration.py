from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import (
    study_domain_transition_table,
    study_macro_state,
    study_state_matrix,
)
from med_autoscience.controllers.study_runtime_status_parts import StudyRuntimeStatus
from med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission import _load_json_dict


def record_domain_transition_if_required(*, status: StudyRuntimeStatus, study_root: Path) -> None:
    status_payload = status.to_dict()
    delivered_package = study_state_matrix._delivered_package_observation(status=status_payload)
    if not _domain_transition_status_candidate(
        status_payload,
        delivered_package=delivered_package,
        study_root=study_root,
    ):
        return
    if delivered_package.get("observed") is True:
        status_payload = {**status_payload, "delivered_package": delivered_package}
    macro_state = study_macro_state.derive_study_macro_state(
        study_id=status.study_id,
        status=status_payload,
        progress={},
    )
    active_run_id = study_state_matrix._resolved_active_run_id(
        status=status_payload,
        macro_state=macro_state,
    )
    transition = study_domain_transition_table.project_domain_transition(
        study_id=status.study_id,
        study_root=study_root,
        status=status_payload,
        macro_state=macro_state,
        active_run_id=active_run_id,
        delivered_package=delivered_package,
    )
    if _domain_transition_consumable_by_interaction_arbitration(transition):
        status.extras["domain_transition"] = transition


def _domain_transition_status_candidate(
    status_payload: dict[str, object],
    *,
    delivered_package: dict[str, object],
    study_root: Path,
) -> bool:
    if delivered_package.get("observed") is True:
        return True
    supervisor_state = status_payload.get("publication_supervisor_state")
    if isinstance(supervisor_state, dict):
        supervisor_phase = str(supervisor_state.get("supervisor_phase") or "").strip()
        current_required_action = str(supervisor_state.get("current_required_action") or "").strip()
        if supervisor_phase in {"stop_loss", "bundle_stage_blocked"}:
            return True
        if current_required_action in {"stop_loss", "stop_runtime", "complete_bundle_stage"}:
            return True
    controller_decision = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    if controller_decision.get("requires_human_confirmation") is True:
        return True
    decision_type = str(controller_decision.get("decision_type") or "").strip()
    route_decision = str(controller_decision.get("route_decision") or "").strip()
    route_target = str(controller_decision.get("route_target") or "").strip()
    if decision_type == "stop_loss" or route_decision in {"stop_loss", "terminal_stop"} or route_target == "stop":
        return True
    return False


def _domain_transition_consumable_by_interaction_arbitration(transition: dict[str, object]) -> bool:
    decision_type = str(transition.get("decision_type") or "").strip()
    return decision_type in {"delivered_package_handoff", "human_gate", "publication_gate_blocker", "stop_loss"}


__all__ = ["record_domain_transition_if_required"]
