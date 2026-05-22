from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import (
    study_domain_transition_table,
    study_macro_state,
    study_state_matrix,
)
from med_autoscience.controllers.owner_route_reconcile_parts import hard_methodology_currentness
from med_autoscience.controllers.study_domain_transition_table_parts import ai_reviewer_transitions
from med_autoscience.controllers.progress_projection_parts import ProgressProjectionStatus
from med_autoscience.controllers.study_runtime_decision_parts.publication_and_submission import _load_json_dict


def record_domain_transition_if_required(*, status: ProgressProjectionStatus, study_root: Path) -> None:
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
    if (
        _domain_transition_consumable_by_interaction_arbitration(transition)
        and not _stale_ai_reviewer_transition_superseded_by_hard_methodology(
            transition=transition,
            study_root=study_root,
        )
    ):
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
        if supervisor_phase in {"stop_loss", "bundle_stage_ready", "bundle_stage_blocked"}:
            return True
        if current_required_action in {"stop_loss", "stop_runtime", "continue_bundle_stage", "complete_bundle_stage"}:
            return True
    controller_decision = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    if controller_decision.get("requires_human_confirmation") is True:
        return True
    decision_type = str(controller_decision.get("decision_type") or "").strip()
    route_decision = str(controller_decision.get("route_decision") or "").strip()
    route_target = str(controller_decision.get("route_target") or "").strip()
    if (
        decision_type in {"route_back_same_line", "stop_loss"}
        or route_decision in {"route_back_same_line", "stop_loss", "terminal_stop"}
        or route_target == "stop"
    ):
        return True
    publication_eval = _load_json_dict(study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH)
    if ai_reviewer_transitions.stale_after_reviewer_revision(
        study_root=study_root,
        publication_eval=publication_eval,
    ):
        return True
    return False


def _domain_transition_consumable_by_interaction_arbitration(transition: dict[str, object]) -> bool:
    decision_type = str(transition.get("decision_type") or "").strip()
    return decision_type in {
        "ai_reviewer_re_eval",
        "delivered_package_handoff",
        "human_gate",
        "publication_gate_blocker",
        "route_back_same_line",
        "stop_loss",
    }


def _stale_ai_reviewer_transition_superseded_by_hard_methodology(
    *,
    transition: dict[str, object],
    study_root: Path,
) -> bool:
    if str(transition.get("decision_type") or "").strip() != "ai_reviewer_re_eval":
        return False
    root = Path(study_root).expanduser().resolve()
    return hard_methodology_currentness.handoff_supersedes_paths(
        source_ref=hard_methodology_currentness.quality_repair_handoff_path(root),
        consumer_paths=(
            root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
            root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH,
            root / study_domain_transition_table.REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH,
        ),
    )


__all__ = ["record_domain_transition_if_required"]
