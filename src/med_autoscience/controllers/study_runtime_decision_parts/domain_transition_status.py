from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import study_runtime_interaction_arbitration as interaction_arbitration_controller
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.human_gates import (
    _is_controller_owned_finalize_parking,
)
from med_autoscience.controllers.study_runtime_decision_parts.runtime_events.pending_interactions import (
    _stopped_controller_owned_auto_recovery_context,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
)


def _record_interaction_arbitration_if_required(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
    execution: dict[str, object],
    submission_metadata_only: bool,
    publication_gate_report: dict[str, object] | None,
) -> None:
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=status,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    if (
        status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not _is_controller_owned_finalize_parking(status)
        and stopped_recovery_context is None
    ):
        return
    payload = status.extras.get("pending_user_interaction")
    blocked_closeout = status.extras.get("blocked_turn_closeout")
    continuation_state = status.extras.get("continuation_state")
    controller_authorization = status.extras.get("last_controller_decision_authorization")
    domain_transition = status.extras.get("domain_transition")
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=payload if isinstance(payload, dict) else None,
        decision_policy=str(execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=submission_metadata_only,
        publication_gate_report=publication_gate_report if isinstance(publication_gate_report, dict) else None,
        blocked_closeout=blocked_closeout if isinstance(blocked_closeout, dict) else None,
        continuation_state=continuation_state if isinstance(continuation_state, dict) else None,
        controller_authorization=controller_authorization if isinstance(controller_authorization, dict) else None,
        domain_transition=domain_transition if isinstance(domain_transition, dict) else None,
    )
    status.record_interaction_arbitration(arbitration)


def _domain_transition_runtime_redrive_reason(status: StudyRuntimeStatus) -> StudyRuntimeReason | None:
    domain_transition = status.extras.get("domain_transition")
    if not isinstance(domain_transition, dict):
        return None
    arbitration = interaction_arbitration_controller.arbitrate_waiting_for_user(
        pending_interaction=None,
        decision_policy=str(status.execution.get("decision_policy") or "").strip() or None,
        submission_metadata_only=False,
        domain_transition=domain_transition,
    )
    if str(arbitration.get("classification") or "").strip() != "domain_transition_runtime_redrive":
        return None
    if str(arbitration.get("action") or "").strip() != "resume":
        return None
    status.record_interaction_arbitration(arbitration)
    reason_code = str(arbitration.get("reason_code") or "").strip()
    try:
        return StudyRuntimeReason(reason_code)
    except ValueError:
        return StudyRuntimeReason.QUEST_WAITING_PLATFORM_REPAIR_REDRIVE


__all__ = [
    "_record_interaction_arbitration_if_required",
    "_domain_transition_runtime_redrive_reason",
]
