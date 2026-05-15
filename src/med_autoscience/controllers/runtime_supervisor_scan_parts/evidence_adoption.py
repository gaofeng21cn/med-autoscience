from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.runtime_supervisor_scan_parts import runtime_facts


ADOPTED_REASON = "controller_work_unit_evidence_adopted"
RECHECK_REASON = "publication_gate_recheck_required"
OWNER_HANDOFF_REASON = "controller_work_unit_owner_handoff_required"


def adopted_controller_work_unit(status: Mapping[str, Any]) -> bool:
    if _text(status.get("reason")) != ADOPTED_REASON:
        return False
    next_route = _mapping(status.get("controller_work_unit_next_route"))
    if next_route.get("runtime_relaunch_required") is not False:
        return False
    return bool(status.get("controller_work_unit_evidence_adoption")) and _text(next_route.get("owner")) is not None


def adopted_next_owner(status: Mapping[str, Any]) -> str | None:
    if not adopted_controller_work_unit(status):
        return None
    return _text(_mapping(status.get("controller_work_unit_next_route")).get("owner"))


def should_suppress_runtime_platform_repair(
    status: Mapping[str, Any],
    *,
    live_activity_timeout_redrive_required: bool = False,
) -> bool:
    if live_activity_timeout_redrive_required:
        return False
    return adopted_controller_work_unit(status)


def platform_repair_required(
    *,
    status: Mapping[str, Any],
    submission_milestone_parked: bool,
    base_required: bool,
    live_activity_timeout_redrive_required: bool = False,
) -> bool:
    if not base_required or submission_milestone_parked:
        return False
    if not adopted_controller_work_unit(status):
        return True
    return live_activity_timeout_redrive_required


def platform_repair_required_from_scan(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    study_root: Any,
    gate_specificity: Mapping[str, Any] | None,
    submission_milestone_parked: bool,
) -> bool:
    if domain_transition_guard.blocks_auto_redrive(status):
        return False
    if domain_transition_guard.runtime_redrive_decision_type(status) is not None:
        return True
    base_required = runtime_facts.runtime_platform_repair_apply_required(
        status=status,
        progress=progress,
        publication_eval_payload=publication_eval_payload,
        study_root=study_root,
        gate_specificity=gate_specificity,
    )
    live_redrive_required = runtime_facts.live_activity_timeout_current_controller_route_available(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    return platform_repair_required(
        status=status,
        submission_milestone_parked=submission_milestone_parked,
        base_required=base_required,
        live_activity_timeout_redrive_required=live_redrive_required,
    )


def resolved_lifecycle(status: Mapping[str, Any], lifecycle: Mapping[str, Any]) -> dict[str, Any]:
    if not adopted_controller_work_unit(status):
        return dict(lifecycle)
    if _text(lifecycle.get("blocked_reason")) in {
        "runtime_recovery_retry_budget_exhausted",
        "runtime_relaunch_no_live_run_started",
        "abnormal_stopped_runtime_resume_required",
        "runtime_controller_redrive_required",
    }:
        return {}
    return dict(lifecycle)


def why_not_applied(status: Mapping[str, Any]) -> str | None:
    if adopted_controller_work_unit(status):
        if adopted_next_owner(status) != "publication_gate":
            return OWNER_HANDOFF_REASON
        return RECHECK_REASON
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ADOPTED_REASON",
    "OWNER_HANDOFF_REASON",
    "RECHECK_REASON",
    "adopted_controller_work_unit",
    "adopted_next_owner",
    "platform_repair_required",
    "platform_repair_required_from_scan",
    "resolved_lifecycle",
    "should_suppress_runtime_platform_repair",
    "why_not_applied",
]
