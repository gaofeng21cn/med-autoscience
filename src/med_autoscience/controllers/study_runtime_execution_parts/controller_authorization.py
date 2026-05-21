from __future__ import annotations

from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.runtime_protocol import quest_state

from ..study_runtime_status import StudyRuntimeDecision, StudyRuntimeReason, StudyRuntimeStatus, _LIVE_QUEST_STATUSES
from .controller_authorization_context import (
    _WORK_UNIT_TARGET_CONTEXT_KEYS,
    _controller_decision_authorization_identity,
    _controller_decision_authorizes_runtime,
    _load_controller_decision_authorization_context,
)
from .controller_authorization_messages import _controller_decision_authorization_message
from .controller_authorization_receipts import (
    _CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS,
    _CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS,
    _active_run_id_from_status_or_state,
    _controller_authorization_marker_lacks_target_context,
    _closed_publication_work_unit_lifecycle,
    _controller_decision_authorization_allowed_while_waiting,
    _controller_decision_authorization_already_relayed,
    _controller_decision_authorization_lifecycle,
    _runtime_state_awaits_artifact_delta_or_gate_replay,
    relay_controller_decision_authorization_to_runtime,
)
from .work_unit_evidence_adoption import (
    adopt_controller_work_unit_evidence_if_present,
    record_controller_work_unit_evidence_adoption,
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
        "dispatch_surface": "medautosci sidecar dispatch",
        "recommended_task_kind": "domain_route/reconcile-apply",
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
    status: StudyRuntimeStatus,
    context: Any,
) -> dict[str, Any] | None:
    opl_runtime_owner_route_handoff = (
        status.decision is StudyRuntimeDecision.BLOCKED
        and status.reason is StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE
    )
    if (
        status.quest_status not in _LIVE_QUEST_STATUSES
        and status.decision not in {StudyRuntimeDecision.RESUME, StudyRuntimeDecision.RELAUNCH_STOPPED}
        and not opl_runtime_owner_route_handoff
    ):
        return None
    if status.decision not in {
        StudyRuntimeDecision.NOOP,
        StudyRuntimeDecision.RESUME,
        StudyRuntimeDecision.RELAUNCH_STOPPED,
    } and not opl_runtime_owner_route_handoff:
        return None
    authorization_context = _load_controller_decision_authorization_context(study_root=context.study_root)
    if not _controller_decision_authorizes_runtime(authorization_context):
        return None
    assert authorization_context is not None
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    runtime_state["quest_id"] = status.quest_id
    active_run_id = _active_run_id_from_status_or_state(status=status, runtime_state=runtime_state)
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

    def adopt_current_evidence_if_present() -> bool:
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
                quest_root=context.quest_root,
                identity=identity,
                authorization_context=authorization_context,
                evidence_adoption=evidence_adoption,
            )
            return True
        return False

    if adopt_current_evidence_if_present():
        return None
    if _runtime_state_awaits_artifact_delta_or_gate_replay(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    ):
        if _controller_decision_authorization_allowed_while_waiting(
            status=status,
            authorization_context=authorization_context,
        ):
            return relay_controller_decision_authorization_to_runtime(
                status=status,
                context=context,
                runtime_state=runtime_state,
                authorization_context=authorization_context,
                active_run_id=active_run_id,
            )
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
    marker_lacks_target_context = _controller_authorization_marker_lacks_target_context(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    )
    if bool(lifecycle.get("delivery_blocked")) and not marker_lacks_target_context:
        if adopt_current_evidence_if_present():
            return None
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
        quest_root=context.quest_root,
        identity=identity,
        authorization_context=authorization_context,
        evidence_adoption=evidence_adoption,
    )
    return evidence_adoption
