from __future__ import annotations

from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.runtime_protocol import quest_state, user_message

from ..study_runtime_status import StudyRuntimeDecision, StudyRuntimeStatus, _LIVE_QUEST_STATUSES
from .controller_authorization_context import (
    _WORK_UNIT_TARGET_CONTEXT_KEYS,
    _controller_decision_authorization_identity,
    _controller_decision_authorizes_runtime,
    _load_controller_decision_authorization_context,
    _load_controller_decision_route_context,
)
from .controller_authorization_messages import _controller_decision_authorization_message
from .controller_authorization_receipts import (
    _CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS,
    _CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS,
    _active_run_id_from_status_or_state,
    _controller_authorization_marker_lacks_target_context,
    _controller_decision_authorization_allowed_while_waiting,
    _controller_decision_authorization_already_relayed,
    _controller_decision_authorization_dedupe_key,
    _controller_decision_authorization_lifecycle,
    _mark_controller_decision_authorization_relayed,
    _reset_same_fingerprint_count_for_new_control_intent,
    _runtime_message_id,
    _runtime_state_awaits_artifact_delta_or_gate_replay,
    _write_runtime_state,
)
from .work_unit_evidence_adoption import (
    adopt_controller_work_unit_evidence_if_present,
    record_controller_work_unit_evidence_adoption,
)


def _relay_controller_decision_authorization_if_required(
    *,
    status: StudyRuntimeStatus,
    context: Any,
) -> dict[str, Any] | None:
    if (
        status.quest_status not in _LIVE_QUEST_STATUSES
        and status.decision not in {StudyRuntimeDecision.RESUME, StudyRuntimeDecision.RELAUNCH_STOPPED}
    ):
        return None
    if status.decision not in {StudyRuntimeDecision.NOOP, StudyRuntimeDecision.RESUME, StudyRuntimeDecision.RELAUNCH_STOPPED}:
        return None
    authorization_context = _load_controller_decision_authorization_context(study_root=context.study_root)
    if not _controller_decision_authorizes_runtime(authorization_context):
        return None
    assert authorization_context is not None
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return None
    runtime_state["quest_id"] = status.quest_id
    if _reset_same_fingerprint_count_for_new_control_intent(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    ):
        _write_runtime_state(quest_root=context.quest_root, runtime_state=runtime_state)
    active_run_id = _active_run_id_from_status_or_state(status=status, runtime_state=runtime_state)
    identity = _controller_decision_authorization_identity(authorization_context)
    evidence_adoption = adopt_controller_work_unit_evidence_if_present(
        study_root=context.study_root,
        quest_root=context.quest_root,
        authorization_context=authorization_context,
        identity=identity,
        active_run_id=active_run_id,
        source=context.source,
    )
    if evidence_adoption is not None:
        record_controller_work_unit_evidence_adoption(
            status=status,
            study_root=context.study_root,
            identity=identity,
            authorization_context=authorization_context,
            evidence_adoption=evidence_adoption,
        )
        return None
    if _runtime_state_awaits_artifact_delta_or_gate_replay(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    ) and not _controller_decision_authorization_allowed_while_waiting(
        status=status,
        authorization_context=authorization_context,
    ):
        control_intent.append_skipped_duplicate_if_needed(
            study_root=context.study_root,
            identity=identity,
            payload={
                "reason": control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
                "active_run_id": active_run_id,
                "source": context.source,
            },
        )
        status.extras["controller_decision_authorization_deferred"] = {
            "control_intent_key": authorization_context.get("control_intent_key"),
            "reason": control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY,
            "allowed_actions": sorted(
                _CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS
                | _CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS
            ),
        }
        return None
    if _controller_decision_authorization_already_relayed(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
    ):
        return None
    lifecycle = _controller_decision_authorization_lifecycle(
        study_root=context.study_root,
        authorization_context=authorization_context,
    )
    authorization_context["controller_work_unit_lifecycle"] = lifecycle
    marker_lacks_target_context = _controller_authorization_marker_lacks_target_context(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    )
    if bool(lifecycle.get("delivery_blocked")) and not marker_lacks_target_context:
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

    message = _controller_decision_authorization_message(authorization_context=authorization_context)
    dedupe_key = _controller_decision_authorization_dedupe_key(
        authorization_context=authorization_context,
        active_run_id=active_run_id,
    )
    relay: dict[str, Any] = {
        "decision_id": authorization_context.get("decision_id"),
        "route_target": authorization_context.get("route_target"),
        "route_key_question": authorization_context.get("route_key_question"),
        "source_route_key_question": authorization_context.get("source_route_key_question"),
        "work_unit_id": authorization_context.get("work_unit_id"),
        "work_unit_fingerprint": authorization_context.get("work_unit_fingerprint"),
        "next_work_unit": authorization_context.get("next_work_unit"),
        "blocking_work_units": authorization_context.get("blocking_work_units"),
        "decision_path": authorization_context.get("decision_path"),
        "control_intent_key": authorization_context.get("control_intent_key"),
        "active_run_id": active_run_id,
        "delivery_mode": None,
        "message_id": None,
        "source": context.source,
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in authorization_context:
            relay[key] = authorization_context[key]
    try:
        response = context.runtime_backend.chat_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            text=message,
            source=context.source,
        )
    except Exception as exc:
        relay["backend_submit_error"] = str(exc)
    else:
        relay["delivery_mode"] = "managed_runtime_chat"
        relay["message_id"] = _runtime_message_id(response)
        _mark_controller_decision_authorization_relayed(
            quest_root=context.quest_root,
            runtime_state=runtime_state,
            authorization_context=authorization_context,
            active_run_id=active_run_id,
            delivery_mode="managed_runtime_chat",
            message_id=relay["message_id"],
            source=context.source,
        )
        control_intent.append_event(
            study_root=context.study_root,
            identity=_controller_decision_authorization_identity(authorization_context),
            event_type="delivered",
            payload={
                "delivery_mode": "managed_runtime_chat",
                "message_id": relay["message_id"],
                "active_run_id": active_run_id,
                "source": context.source,
            },
        )
        status.extras["controller_decision_authorization_relay"] = relay
        return relay

    record = user_message.enqueue_user_message(
        quest_root=context.quest_root,
        runtime_state=runtime_state,
        message=message,
        source=context.source,
        dedupe_key=dedupe_key,
    )
    updated_runtime_state = quest_state.load_runtime_state(context.quest_root)
    relay["delivery_mode"] = "durable_queue_fallback"
    relay["message_id"] = record.get("message_id")
    relay["reply_to_interaction_id"] = record.get("reply_to_interaction_id")
    _mark_controller_decision_authorization_relayed(
        quest_root=context.quest_root,
        runtime_state=updated_runtime_state,
        authorization_context=authorization_context,
        active_run_id=active_run_id,
        delivery_mode="durable_queue_fallback",
        message_id=str(record.get("message_id") or "").strip() or None,
        source=context.source,
    )
    control_intent.append_event(
        study_root=context.study_root,
        identity=_controller_decision_authorization_identity(authorization_context),
        event_type="delivered",
        payload={
            "delivery_mode": "durable_queue_fallback",
            "message_id": relay["message_id"],
            "active_run_id": active_run_id,
            "source": context.source,
        },
    )
    status.extras["controller_decision_authorization_relay"] = relay
    return relay


def adopt_controller_work_unit_evidence_for_current_authorization(
    *,
    status: StudyRuntimeStatus,
    context: Any,
) -> dict[str, Any] | None:
    authorization_context = _load_controller_decision_authorization_context(study_root=context.study_root)
    if not _controller_decision_authorizes_runtime(authorization_context):
        return None
    assert authorization_context is not None
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return None
    active_run_id = _active_run_id_from_status_or_state(status=status, runtime_state=runtime_state)
    identity = _controller_decision_authorization_identity(authorization_context)
    evidence_adoption = adopt_controller_work_unit_evidence_if_present(
        study_root=context.study_root,
        quest_root=context.quest_root,
        authorization_context=authorization_context,
        identity=identity,
        active_run_id=active_run_id,
        source=context.source,
    )
    if evidence_adoption is None:
        return None
    record_controller_work_unit_evidence_adoption(
        status=status,
        study_root=context.study_root,
        identity=identity,
        authorization_context=authorization_context,
        evidence_adoption=evidence_adoption,
    )
    return evidence_adoption
