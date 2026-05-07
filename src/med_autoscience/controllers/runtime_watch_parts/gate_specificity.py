from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent, runtime_watch_work_units, study_outer_loop
from med_autoscience.controllers.runtime_watch_parts.managed_wakeup import _candidate_path, _non_empty_text
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.runtime_protocol import quest_state


_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE = "runtime_watch_outer_loop_wakeup"
_REQUIRED_SPECIFICITY_TARGET_KINDS = (
    "claim",
    "display",
    "evidence_source",
    "citation",
    "metric",
    "package_artifact",
    "authorization_provenance",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_runtime_state(*, quest_root: Path, runtime_state: Mapping[str, Any]) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(dict(runtime_state), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _compact_work_unit_payload(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _gate_specificity_non_executable_contract() -> dict[str, Any]:
    return {
        "controller_work_unit_executable": False,
        "non_executable_reason": "gate_needs_specificity_without_targets",
        "required_target_kinds": list(_REQUIRED_SPECIFICITY_TARGET_KINDS),
    }


def _specificity_control_intent_identity(
    *,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> control_intent.ControlIntentIdentity | None:
    next_work_unit = _compact_work_unit_payload(tick_request.get("next_work_unit"))
    unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    work_unit_fingerprint = _non_empty_text(tick_request.get("work_unit_fingerprint"))
    study_id = _non_empty_text(status_payload.get("study_id"))
    if unit_id is None or work_unit_fingerprint is None or study_id is None:
        return None
    return control_intent.build_control_intent_identity(
        study_id=study_id,
        quest_id=_non_empty_text(status_payload.get("quest_id")),
        route_target="controller",
        work_unit_id=unit_id,
        blocker_authority_fingerprint=work_unit_fingerprint,
        controller_actions=("request_gate_specificity",),
        source_kind="controller_decision_authorization",
    )


def _clear_quest_user_messages_for_superseded_specificity(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
) -> None:
    queue_path = Path(quest_root).expanduser().resolve() / ".ds" / "user_message_queue.json"
    if not queue_path.exists():
        runtime_state["pending_user_message_count"] = 0
        runtime_state.pop("pending_user_message_ids", None)
        return
    try:
        queue_payload = json.loads(queue_path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        queue_payload = {}
    if not isinstance(queue_payload, dict):
        queue_payload = {}
    pending = [item for item in (queue_payload.get("pending") or []) if isinstance(item, dict)]
    completed = [item for item in (queue_payload.get("completed") or []) if isinstance(item, dict)]
    superseded_at = utc_now()
    retained_pending: list[dict[str, Any]] = []
    superseded: list[dict[str, Any]] = []
    for item in pending:
        dedupe_key = str(item.get("dedupe_key") or "").strip()
        content = str(item.get("content") or "").strip()
        is_controller_authorization = (
            dedupe_key.startswith("control-intent::")
            or dedupe_key.startswith("controller-decision-authorization:")
            or content.startswith("MAS controller authorization.")
        )
        if not is_controller_authorization:
            retained_pending.append(item)
            continue
        item["status"] = "superseded_by_gate_specificity"
        item["superseded_at"] = superseded_at
        superseded.append(item)
    queue_payload["pending"] = retained_pending
    queue_payload["completed"] = [*completed, *superseded]
    queue_path.write_text(json.dumps(queue_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runtime_state["pending_user_message_count"] = len(retained_pending)
    runtime_state["pending_user_message_ids"] = [
        str(item.get("message_id") or "")
        for item in retained_pending
        if str(item.get("message_id") or "").strip()
    ]


def _materialize_specificity_controller_state(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    wakeup_audit: Mapping[str, Any],
) -> dict[str, Any]:
    decision_payload = runtime_watch_work_units.strip_context(tick_request)
    decision_payload["study_root"] = study_root
    decision_payload["route_target"] = str(decision_payload.get("route_target") or "").strip() or "controller"
    decision_payload["route_key_question"] = str(decision_payload.get("route_key_question") or "").strip() or (
        "gate_needs_specificity: Which exact claim, figure, table, metric, source path, or package artifact is blocking the publication gate?"
    )
    decision_payload["route_rationale"] = str(decision_payload.get("route_rationale") or "").strip() or (
        str(decision_payload.get("reason") or "").strip()
        or "Publication gate needs concrete blocker targets before dispatch."
    )
    decision_payload.pop("specificity_questions", None)
    if not decision_payload.get("controller_actions"):
        decision_payload["controller_actions"] = [
            {
                "action_type": "request_gate_specificity",
                "payload_ref": str((Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json").resolve()),
            }
        ]
    decision_result = study_outer_loop.materialize_non_dispatching_outer_loop_decision(
        profile=profile,
        status_payload=dict(status_payload),
        source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
        recorded_at=_non_empty_text(wakeup_audit.get("recorded_at")),
        **decision_payload,
    )
    quest_root = _candidate_path(status_payload.get("quest_root"))
    identity = _specificity_control_intent_identity(
        status_payload=status_payload,
        tick_request=tick_request,
    )
    if quest_root is None or identity is None:
        return decision_result
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="needs_specificity",
        payload={
            "source": _MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
            "wakeup_outcome": "needs_specificity",
            "wakeup_reason": _non_empty_text(wakeup_audit.get("reason")),
        },
        recorded_at=_non_empty_text(wakeup_audit.get("recorded_at")) or utc_now(),
    )
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    runtime_state = quest_state.load_runtime_state(quest_root)
    runtime_state["quest_id"] = _non_empty_text(status_payload.get("quest_id")) or runtime_state.get("quest_id")
    _clear_quest_user_messages_for_superseded_specificity(quest_root=quest_root, runtime_state=runtime_state)
    runtime_state["last_controller_decision_authorization"] = {
        "decision_id": _non_empty_text((decision_result.get("study_decision_ref") or {}).get("decision_id")),
        "route_target": "controller",
        "route_key_question": str(tick_request.get("route_key_question") or "").strip(),
        "source_route_key_question": str(tick_request.get("source_route_key_question") or "").strip() or None,
        "work_unit_id": "gate_needs_specificity",
        "work_unit_fingerprint": _non_empty_text(tick_request.get("work_unit_fingerprint")),
        "next_work_unit": _compact_work_unit_payload(tick_request.get("next_work_unit")),
        "blocking_work_units": [
            dict(item)
            for item in (tick_request.get("blocking_work_units") or [])
            if isinstance(item, dict)
        ],
        "control_intent_key": identity.business_key,
        "control_intent_identity": identity.to_dict(),
        "active_run_id": None,
        "delivery_mode": "controller_terminal_projection",
        "message_id": None,
        "source": _MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
        **_gate_specificity_non_executable_contract(),
        "controller_work_unit_lifecycle": {
            "lifecycle_state": str(lifecycle.get("lifecycle_state") or "needs_specificity"),
            "latest_event_type": lifecycle.get("latest_event_type"),
            "delivery_blocked": bool(lifecycle.get("delivery_blocked")),
            "block_reason": lifecycle.get("block_reason"),
            "terminal_consumed": bool(lifecycle.get("terminal_consumed")),
        },
    }
    runtime_state["control_intent_lifecycle"] = {
        "state": "needs_specificity",
        "control_intent_key": identity.business_key,
        "work_unit_id": "gate_needs_specificity",
        "work_unit_fingerprint": _non_empty_text(tick_request.get("work_unit_fingerprint")),
    }
    _write_runtime_state(quest_root=quest_root, runtime_state=runtime_state)
    return decision_result


def _specificity_terminal_status_payload(
    *,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(status_payload)
    payload["decision"] = "blocked"
    payload["reason"] = "gate_needs_specificity"
    payload["last_controller_decision_authorization"] = {
        "work_unit_id": "gate_needs_specificity",
        "work_unit_fingerprint": _non_empty_text(tick_request.get("work_unit_fingerprint")),
        "next_work_unit": _compact_work_unit_payload(tick_request.get("next_work_unit")),
        "blocking_work_units": [
            dict(item)
            for item in (tick_request.get("blocking_work_units") or [])
            if isinstance(item, dict)
        ],
        **_gate_specificity_non_executable_contract(),
        "controller_work_unit_lifecycle": {
            "lifecycle_state": "needs_specificity",
            "latest_event_type": "needs_specificity",
            "delivery_blocked": True,
            "block_reason": "needs_specificity",
            "terminal_consumed": True,
        },
    }
    payload["control_intent_lifecycle"] = {
        "state": "needs_specificity",
        "work_unit_id": "gate_needs_specificity",
        "work_unit_fingerprint": _non_empty_text(tick_request.get("work_unit_fingerprint")),
    }
    return payload


def _study_requests_gate_specificity_terminal(
    *,
    study_root: Path,
) -> bool:
    try:
        publication_eval = read_publication_eval_latest(study_root=study_root)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return False
    recommended_actions = publication_eval.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return False
    for action in recommended_actions:
        if not isinstance(action, Mapping):
            continue
        if _non_empty_text(action.get("action_type")) != "return_to_controller":
            continue
        next_work_unit = action.get("next_work_unit")
        if not isinstance(next_work_unit, Mapping):
            continue
        if _non_empty_text(next_work_unit.get("unit_id")) == "gate_needs_specificity":
            return True
    return False


__all__ = [
    "_clear_quest_user_messages_for_superseded_specificity",
    "_compact_work_unit_payload",
    "_gate_specificity_non_executable_contract",
    "_materialize_specificity_controller_state",
    "_specificity_control_intent_identity",
    "_specificity_terminal_status_payload",
    "_study_requests_gate_specificity_terminal",
    "_write_runtime_state",
]
