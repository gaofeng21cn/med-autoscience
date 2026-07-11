from __future__ import annotations

from typing import Any

from med_autoscience.controllers import control_intent

from ..progress_projection import StudyRuntimeDecision, StudyRuntimeReason, ProgressProjectionStatus, _LIVE_QUEST_STATUSES
from .controller_authorization_context import (
    _WORK_UNIT_TARGET_CONTEXT_KEYS,
    _controller_decision_authorization_identity,
    _controller_decision_authorizes_runtime,
    _load_controller_decision_authorization_context,
)
from .controller_authorization_messages import _controller_decision_authorization_message
from .controller_authorization_receipts import (
    _active_run_id_from_status,
    _closed_publication_work_unit_lifecycle,
    _controller_decision_authorization_lifecycle,
)


def _controller_decision_owner_route_ref(
    *,
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    source: str,
) -> dict[str, Any]:
    ref: dict[str, Any] = {
        "surface_kind": "mas_controller_decision_owner_route_ref",
        "domain_truth_owner": "med-autoscience",
        "queue_owner": "one-person-lab",
        "dispatch_surface": "action_catalog:domain_handler_dispatch",
        "recommended_task_kind": "stage_outcome/opl-handoff",
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_submits_runtime_chat": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
        "decision_id": authorization_context.get("decision_id"),
        "route_target": authorization_context.get("route_target"),
        "route_key_question": authorization_context.get("route_key_question"),
        "source_route_key_question": authorization_context.get("source_route_key_question"),
        "work_unit_id": authorization_context.get("work_unit_id"),
        "work_unit_fingerprint": authorization_context.get("work_unit_fingerprint"),
        "next_work_unit": authorization_context.get("next_work_unit"),
        "blocking_work_units": authorization_context.get("blocking_work_units"),
        "decision_path": authorization_context.get("decision_path"),
        "publication_eval_path": authorization_context.get("publication_eval_path"),
        "control_intent_key": authorization_context.get("control_intent_key"),
        "control_intent_identity": authorization_context.get("control_intent_identity"),
        "active_run_id": active_run_id,
        "source": source,
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in authorization_context:
            ref[key] = authorization_context[key]
    return ref


def _owner_route_ref_already_projected_for_current_authorization(
    *,
    study_root: Any,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> bool:
    latest = control_intent.latest_event(study_root=study_root, business_key=identity.business_key)
    if not isinstance(latest, dict) or str(latest.get("event_type") or "").strip() != "owner_handoff":
        return False
    decision_emitted_at = str(authorization_context.get("decision_emitted_at") or "").strip()
    if not decision_emitted_at:
        return True
    recorded_at = str(latest.get("recorded_at") or "").strip()
    return bool(recorded_at and recorded_at >= decision_emitted_at)


def _relay_controller_decision_authorization_if_required(
    *,
    status: ProgressProjectionStatus,
    context: Any,
) -> dict[str, Any] | None:
    opl_stage_attempt_admission_handoff = (
        status.decision is StudyRuntimeDecision.HANDOFF_REQUIRED
        and status.reason is StudyRuntimeReason.OPL_STAGE_ATTEMPT_ADMISSION_REQUIRED
    )
    if (
        status.quest_status not in _LIVE_QUEST_STATUSES
        and status.decision not in {StudyRuntimeDecision.RESUME, StudyRuntimeDecision.RELAUNCH_STOPPED}
        and not opl_stage_attempt_admission_handoff
    ):
        return None
    if status.decision not in {
        StudyRuntimeDecision.NOOP,
        StudyRuntimeDecision.RESUME,
        StudyRuntimeDecision.RELAUNCH_STOPPED,
    } and not opl_stage_attempt_admission_handoff:
        return None
    authorization_context = _load_controller_decision_authorization_context(study_root=context.study_root)
    if not _controller_decision_authorizes_runtime(authorization_context):
        return None
    assert authorization_context is not None
    active_run_id = _active_run_id_from_status(status=status)
    identity = _controller_decision_authorization_identity(authorization_context)
    if _owner_route_ref_already_projected_for_current_authorization(
        study_root=context.study_root,
        identity=identity,
        authorization_context=authorization_context,
    ):
        status.extras["controller_decision_authorization_deduped"] = {
            "control_intent_key": authorization_context.get("control_intent_key"),
            "source": "control_intent_ledger",
            "reason": "owner_route_ref_already_projected_for_opl_runtime",
        }
        return None

    lifecycle = _controller_decision_authorization_lifecycle(
        study_root=context.study_root,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
    )
    authorization_context["controller_work_unit_lifecycle"] = lifecycle
    closed_publication_work_unit = _closed_publication_work_unit_lifecycle(
        study_root=context.study_root,
        authorization_context=authorization_context,
    )
    if closed_publication_work_unit is not None:
        status.extras["controller_decision_authorization_closed"] = {
            **closed_publication_work_unit,
            "control_intent_key": authorization_context.get("control_intent_key"),
            "active_run_id": active_run_id,
            "source": context.source,
        }
        return None
    if bool(lifecycle.get("delivery_blocked")):
        control_intent.append_skipped_duplicate_if_needed(
            study_root=context.study_root,
            identity=_controller_decision_authorization_identity(authorization_context),
            payload={
                "reason": lifecycle.get("block_reason"),
                "latest_event_type": lifecycle.get("latest_event_type"),
                "active_run_id": active_run_id,
                "source": context.source,
            },
        )
        status.extras["controller_decision_authorization_deduped"] = {
            "control_intent_key": authorization_context.get("control_intent_key"),
            "source": "control_intent_ledger",
            "lifecycle": lifecycle,
        }
        return None

    owner_route_ref = _controller_decision_owner_route_ref(
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        source=context.source,
    )
    control_intent.append_event(
        study_root=context.study_root,
        identity=_controller_decision_authorization_identity(authorization_context),
        event_type="owner_handoff",
        payload={
            "handoff_kind": "opl_owner_route_ref",
            "owner_route_ref": owner_route_ref,
            "active_run_id": active_run_id,
            "source": context.source,
        },
    )
    status.extras["controller_decision_authorization_owner_route_ref"] = owner_route_ref
    return owner_route_ref
