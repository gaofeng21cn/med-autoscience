from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.runtime_protocol import quest_state, user_message
from med_autoscience.study_decision_record import StudyDecisionRecord

from ..study_runtime_status import (
    StudyRuntimeDecision,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)


_CONTROLLER_DECISION_RUNTIME_AUTHORIZATION_ACTIONS = {
    "ensure_study_runtime",
    "ensure_study_runtime_relaunch_stopped",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}
_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY = "last_controller_decision_authorization"
_CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS = {
    "run_gate_clearing_batch",
}
_CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS = {
    "ensure_study_runtime_relaunch_stopped",
}
_QUALITY_REPAIR_DOWNSTREAM_WORK_UNIT_IDS = {
    "publication_gate_replay",
    "submission_authority_sync_closure",
    "submission_delivery_sync_closure",
    "submission_minimal_refresh",
}
_WORK_UNIT_TARGET_CONTEXT_KEYS = (
    "specificity_targets",
    "work_unit_targets",
    "blocking_artifact_refs",
    "blocker_details",
    "gate_blocker_details",
    "gaps",
    "source_path",
)
_CONTROL_INTENT_LIFECYCLE_STATE_KEY = "control_intent_lifecycle"
_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY = "last_live_controller_reroute_restart"
_ROUTE_TARGET_LABELS = {
    "analysis-campaign": "有限补充分析",
    "write": "当前论文主线写作",
    "review": "质量复评",
    "finalize": "finalize / 投稿包收口",
}


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError):
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _artifact_payload_from_ref(*, study_root: Path, artifact_path: str) -> dict[str, Any]:
    path = Path(str(artifact_path or "").strip()).expanduser()
    if not path.is_absolute():
        path = Path(study_root).expanduser().resolve() / path
    return _read_json_mapping(path)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _text_sequence(value: object) -> tuple[str, ...]:
    if isinstance(value, (list, tuple, set)):
        return tuple(sorted({text for item in value if (text := _text(item))}))
    text = _text(value)
    return (text,) if text is not None else ()


def _stable_blocking_artifact_refs(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    refs: list[str] = []
    for item in value:
        if isinstance(item, dict):
            refs.append(json.dumps(item, ensure_ascii=True, sort_keys=True, separators=(",", ":")))
            continue
        text = _text(item)
        if text is not None:
            refs.append(text)
    return tuple(sorted(set(refs)))


def _compact_work_unit_payload(value: object) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    unit_id = _text(value.get("unit_id"))
    if unit_id is None:
        return None
    payload = {"unit_id": unit_id}
    for key in ("lane", "summary", "control_surface", "user_feedback_priority"):
        text = _text(value.get(key))
        if text is not None:
            payload[key] = text
    return payload


def _publication_eval_work_unit_context(publication_eval_payload: dict[str, Any]) -> dict[str, Any]:
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return {}
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        next_work_unit = _compact_work_unit_payload(action.get("next_work_unit"))
        if next_work_unit is None:
            continue
        unit_id = next_work_unit["unit_id"]
        unit_summary = _text(next_work_unit.get("summary"))
        route_key_question = f"{unit_id}: {unit_summary}" if unit_summary else unit_id
        route_rationale = (
            _text(action.get("route_rationale"))
            or _text(action.get("reason"))
            or unit_summary
            or _text(action.get("route_key_question"))
            or f"Publication gate selected work unit `{unit_id}` as the next controller-owned action."
        )
        blocking_work_units = [
            compact
            for item in action.get("blocking_work_units") or []
            if (compact := _compact_work_unit_payload(item)) is not None
        ]
        return {
            "work_unit_id": unit_id,
            "work_unit_fingerprint": _text(action.get("work_unit_fingerprint")),
            "next_work_unit": next_work_unit,
            "blocking_work_units": blocking_work_units,
            "route_target": _text(next_work_unit.get("lane")) or _text(action.get("route_target")),
            "route_key_question": route_key_question,
            "route_rationale": route_rationale,
            "source_route_key_question": _text(action.get("route_key_question")),
        }
    return {}


def _publication_action_target_context(
    publication_eval_payload: dict[str, Any],
    work_unit_context: dict[str, Any],
) -> dict[str, Any]:
    work_unit_fingerprint = _text(work_unit_context.get("work_unit_fingerprint"))
    work_unit_id = _text(work_unit_context.get("work_unit_id")) or _text(
        _mapping(work_unit_context.get("next_work_unit")).get("unit_id")
    )
    if work_unit_fingerprint is None and work_unit_id is None:
        return {}
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return {}
    matching_actions: list[dict[str, Any]] = []
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        next_work_unit = _compact_work_unit_payload(action.get("next_work_unit"))
        action_fingerprint = _text(action.get("work_unit_fingerprint")) or (
            _text(next_work_unit.get("fingerprint")) if next_work_unit is not None else None
        )
        action_unit_id = _text(next_work_unit.get("unit_id")) if next_work_unit is not None else None
        fingerprint_matches = (
            work_unit_fingerprint is not None
            and action_fingerprint is not None
            and action_fingerprint == work_unit_fingerprint
        )
        unit_matches = work_unit_fingerprint is None and work_unit_id is not None and action_unit_id == work_unit_id
        if fingerprint_matches or unit_matches:
            matching_actions.append(action)
    if len(matching_actions) != 1:
        return {}
    action = matching_actions[0]
    return {key: action[key] for key in _WORK_UNIT_TARGET_CONTEXT_KEYS if key in action}


def _record_work_unit_context(record: StudyDecisionRecord) -> dict[str, Any]:
    next_work_unit = _compact_work_unit_payload(record.next_work_unit)
    if next_work_unit is None:
        return {}
    unit_id = next_work_unit["unit_id"]
    unit_summary = _text(next_work_unit.get("summary"))
    route_key_question = f"{unit_id}: {unit_summary}" if unit_summary else unit_id
    blocking_work_units = [
        compact
        for item in record.blocking_work_units
        if (compact := _compact_work_unit_payload(item)) is not None
    ]
    return {
        "work_unit_id": unit_id,
        "work_unit_fingerprint": record.work_unit_fingerprint,
        "next_work_unit": next_work_unit,
        "blocking_work_units": blocking_work_units,
        "route_target": _text(next_work_unit.get("lane")) or record.route_target,
        "route_key_question": route_key_question,
        "route_rationale": record.route_rationale,
        "source_route_key_question": record.route_key_question,
    }


def _stable_publication_authority_fingerprint(
    *,
    study_root: Path,
    record: StudyDecisionRecord,
) -> str:
    publication_eval_payload = _artifact_payload_from_ref(
        study_root=study_root,
        artifact_path=record.publication_eval_ref.artifact_path,
    )
    work_unit_context = _record_work_unit_context(record) or _publication_eval_work_unit_context(publication_eval_payload)
    target_context = _publication_action_target_context(publication_eval_payload, work_unit_context)
    if target_context:
        work_unit_context = {**work_unit_context, **target_context}
    canonical_payload: dict[str, Any] = {
        "gate_fingerprint": _text(publication_eval_payload.get("gate_fingerprint")),
        "work_unit_fingerprint": _text(work_unit_context.get("work_unit_fingerprint")),
        "next_work_unit": work_unit_context.get("next_work_unit"),
        "blocking_work_units": work_unit_context.get("blocking_work_units"),
        "evaluated_source_signature": _text(
            publication_eval_payload.get("evaluated_source_signature")
            or publication_eval_payload.get("submission_minimal_evaluated_source_signature")
        ),
        "authority_source_signature": _text(
            publication_eval_payload.get("authority_source_signature")
            or publication_eval_payload.get("submission_minimal_authority_source_signature")
        ),
        "current_required_action": _text(publication_eval_payload.get("current_required_action")),
        "blockers": list(_text_sequence(publication_eval_payload.get("blockers"))),
        "blocking_artifact_refs": list(_stable_blocking_artifact_refs(publication_eval_payload.get("blocking_artifact_refs"))),
        "work_unit_target_context": {
            key: work_unit_context[key] for key in _WORK_UNIT_TARGET_CONTEXT_KEYS if key in work_unit_context
        },
    }
    if not any(canonical_payload.values()):
        canonical_payload = {
            "publication_eval_artifact_path": _text(record.publication_eval_ref.artifact_path),
            "runtime_escalation_artifact_path": _text(record.runtime_escalation_ref.artifact_path),
        }
    encoded = json.dumps(canonical_payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return f"authority:{hashlib.sha256(encoded).hexdigest()[:24]}"


def _controller_decision_authorization_identity(
    authorization_context: dict[str, Any],
) -> control_intent.ControlIntentIdentity:
    return control_intent.build_control_intent_identity(
        study_id=str(authorization_context.get("study_id") or ""),
        quest_id=str(authorization_context.get("quest_id") or "") or None,
        route_target=str(authorization_context.get("route_target") or ""),
        work_unit_id=str(
            authorization_context.get("work_unit_id")
            or authorization_context.get("route_key_question")
            or ""
        ),
        blocker_authority_fingerprint=str(authorization_context.get("blocker_authority_fingerprint") or ""),
        controller_actions=authorization_context.get("controller_actions") or (),
        source_kind="controller_decision_authorization",
    )


def _load_controller_decision_authorization_context(*, study_root: Path) -> dict[str, Any] | None:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    record = _read_controller_decision_record(decision_path)
    if record is None or not _controller_decision_record_has_route(record):
        return None
    resolved_study_root = Path(study_root).expanduser().resolve()
    work_unit_context = _controller_decision_work_unit_context(
        record=record,
        study_root=resolved_study_root,
    )
    route_fields = _controller_decision_authorization_route_fields(
        record=record,
        work_unit_context=work_unit_context,
    )
    controller_actions = tuple(action.action_type.value for action in record.controller_actions)
    blocker_authority_fingerprint = _controller_decision_blocker_authority_fingerprint(
        study_root=resolved_study_root,
        record=record,
        work_unit_context=work_unit_context,
    )
    intent_identity = control_intent.build_control_intent_identity(
        study_id=record.study_id,
        quest_id=record.quest_id,
        route_target=route_fields["route_target"],
        work_unit_id=route_fields["work_unit_id"],
        blocker_authority_fingerprint=blocker_authority_fingerprint,
        controller_actions=controller_actions,
        source_kind="controller_decision_authorization",
    )
    return _controller_decision_authorization_context_payload(
        decision_path=decision_path,
        record=record,
        route_fields=route_fields,
        work_unit_context=work_unit_context,
        controller_actions=controller_actions,
        blocker_authority_fingerprint=blocker_authority_fingerprint,
        intent_identity=intent_identity,
    )


def _read_controller_decision_record(decision_path: Path) -> StudyDecisionRecord | None:
    if not decision_path.exists():
        return None
    try:
        payload = json.loads(decision_path.read_text(encoding="utf-8")) or {}
        return StudyDecisionRecord.from_payload(payload if isinstance(payload, dict) else {})
    except (OSError, ValueError, TypeError):
        return None


def _controller_decision_record_has_route(record: StudyDecisionRecord) -> bool:
    return all((record.route_target, record.route_key_question, record.route_rationale))


def _controller_decision_work_unit_context(
    *,
    record: StudyDecisionRecord,
    study_root: Path,
) -> dict[str, Any]:
    publication_eval_payload = _artifact_payload_from_ref(
        study_root=study_root,
        artifact_path=record.publication_eval_ref.artifact_path,
    )
    work_unit_context = _record_work_unit_context(record) or _publication_eval_work_unit_context(publication_eval_payload)
    target_context = _publication_action_target_context(publication_eval_payload, work_unit_context)
    if target_context:
        return {**work_unit_context, **target_context}
    return work_unit_context


def _controller_decision_authorization_route_fields(
    *,
    record: StudyDecisionRecord,
    work_unit_context: dict[str, Any],
) -> dict[str, str]:
    route_target = str(work_unit_context.get("route_target") or record.route_target or "").strip()
    route_key_question = str(work_unit_context.get("route_key_question") or record.route_key_question or "").strip()
    route_rationale = str(work_unit_context.get("route_rationale") or record.route_rationale or "").strip()
    work_unit_id = str(work_unit_context.get("work_unit_id") or route_key_question).strip()
    return {
        "route_target": route_target,
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "work_unit_id": work_unit_id,
    }


def _controller_decision_blocker_authority_fingerprint(
    *,
    study_root: Path,
    record: StudyDecisionRecord,
    work_unit_context: dict[str, Any],
) -> str:
    blocker_authority_fingerprint = str(work_unit_context.get("work_unit_fingerprint") or "").strip()
    if not blocker_authority_fingerprint:
        return _stable_publication_authority_fingerprint(
            study_root=study_root,
            record=record,
        )
    return blocker_authority_fingerprint


def _controller_decision_authorization_context_payload(
    *,
    decision_path: Path,
    record: StudyDecisionRecord,
    route_fields: dict[str, str],
    work_unit_context: dict[str, Any],
    controller_actions: tuple[str, ...],
    blocker_authority_fingerprint: str,
    intent_identity: control_intent.ControlIntentIdentity,
) -> dict[str, Any]:
    route_target = route_fields["route_target"]
    authorization_context: dict[str, Any] = {
        "decision_id": record.decision_id,
        "study_id": record.study_id,
        "quest_id": record.quest_id,
        "decision_type": record.decision_type.value,
        "requires_human_confirmation": record.requires_human_confirmation,
        "controller_actions": controller_actions,
        "decision_path": str(decision_path),
        "route_target": route_target,
        "route_target_label": _ROUTE_TARGET_LABELS.get(route_target, route_target),
        "route_key_question": route_fields["route_key_question"],
        "route_rationale": route_fields["route_rationale"],
        "source_route_key_question": record.route_key_question,
        "work_unit_id": route_fields["work_unit_id"],
        "work_unit_fingerprint": str(work_unit_context.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": dict(work_unit_context.get("next_work_unit") or {}),
        "blocking_work_units": list(work_unit_context.get("blocking_work_units") or []),
        "blocker_authority_fingerprint": blocker_authority_fingerprint,
        "control_intent_identity": intent_identity.to_dict(),
        "control_intent_key": intent_identity.business_key,
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in work_unit_context:
            authorization_context[key] = work_unit_context[key]
    return authorization_context


def _load_controller_decision_route_context(*, study_root: Path) -> dict[str, str] | None:
    authorization_context = _load_controller_decision_authorization_context(study_root=study_root)
    if not isinstance(authorization_context, dict):
        return None
    route_context = {
        key: str(authorization_context.get(key) or "").strip()
        for key in ("route_target", "route_target_label", "route_key_question", "route_rationale")
    }
    if not all(route_context.values()):
        return None
    return route_context


def _controller_decision_authorizes_runtime(authorization_context: dict[str, Any] | None) -> bool:
    if not isinstance(authorization_context, dict):
        return False
    if bool(authorization_context.get("requires_human_confirmation")):
        return False
    controller_actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    return bool(controller_actions & _CONTROLLER_DECISION_RUNTIME_AUTHORIZATION_ACTIONS)


def _active_run_id_from_status_or_state(*, status: StudyRuntimeStatus, runtime_state: dict[str, Any]) -> str | None:
    active_run_id = str(runtime_state.get("active_run_id") or "").strip()
    if active_run_id:
        return active_run_id
    payload = status.extras.get("runtime_liveness_audit")
    if isinstance(payload, dict):
        active_run_id = str(payload.get("active_run_id") or "").strip()
        if active_run_id:
            return active_run_id
        runtime_audit = payload.get("runtime_audit")
        if isinstance(runtime_audit, dict):
            active_run_id = str(runtime_audit.get("active_run_id") or "").strip()
            if active_run_id:
                return active_run_id
    return None


def _controller_decision_authorization_already_relayed(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
) -> bool:
    marker = runtime_state.get(_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if not isinstance(marker, dict):
        return False
    if not _controller_target_context_matches(marker=marker, authorization_context=authorization_context):
        return False
    intent_match = _controller_intent_key_match(marker=marker, authorization_context=authorization_context)
    if intent_match is not None:
        return intent_match
    return _controller_route_marker_match(marker=marker, authorization_context=authorization_context)


def _controller_target_context_matches(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return all(
        key not in authorization_context or marker.get(key) == authorization_context.get(key)
        for key in _WORK_UNIT_TARGET_CONTEXT_KEYS
    )


def _controller_intent_key_match(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool | None:
    expected_intent_key = str(authorization_context.get("control_intent_key") or "").strip()
    marker_intent_key = str(marker.get("control_intent_key") or "").strip()
    if not expected_intent_key or not marker_intent_key:
        return None
    return marker_intent_key == expected_intent_key


def _controller_route_marker_match(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return (
        str(marker.get("decision_id") or "").strip() == str(authorization_context.get("decision_id") or "").strip()
        and str(marker.get("route_target") or "").strip() == str(authorization_context.get("route_target") or "").strip()
        and str(marker.get("route_key_question") or "").strip()
        == str(authorization_context.get("route_key_question") or "").strip()
    )


def _controller_decision_authorization_lifecycle(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
) -> dict[str, Any]:
    return control_intent.lifecycle_state(
        study_root=study_root,
        identity=_controller_decision_authorization_identity(authorization_context),
    )


def _controller_decision_authorization_dedupe_key(
    *,
    authorization_context: dict[str, Any],
    active_run_id: str | None,
) -> str:
    intent_key = str(authorization_context.get("control_intent_key") or "").strip()
    if intent_key:
        return intent_key
    canonical_payload = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
    }
    encoded = json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return f"controller-decision-authorization:{hashlib.sha256(encoded).hexdigest()}"


def _controller_work_unit_lifecycle_projection(lifecycle: dict[str, Any] | None) -> dict[str, Any]:
    payload = lifecycle if isinstance(lifecycle, dict) else {}
    return {
        "lifecycle_state": str(payload.get("lifecycle_state") or "new").strip() or "new",
        "latest_event_type": payload.get("latest_event_type"),
        "delivery_blocked": bool(payload.get("delivery_blocked")),
        "block_reason": payload.get("block_reason"),
        "terminal_consumed": bool(payload.get("terminal_consumed")),
    }


def _controller_decision_authorization_message(*, authorization_context: dict[str, Any]) -> str:
    route_target = str(authorization_context.get("route_target") or "").strip()
    route_target_label = str(authorization_context.get("route_target_label") or route_target).strip()
    route_key_question = str(authorization_context.get("route_key_question") or "").strip()
    route_rationale = str(authorization_context.get("route_rationale") or "").strip()
    decision_id = str(authorization_context.get("decision_id") or "").strip()
    decision_path = str(authorization_context.get("decision_path") or "artifacts/controller_decisions/latest.json").strip()
    controller_actions = _controller_actions_markdown(authorization_context)
    work_unit_lines = _controller_work_unit_message_lines(authorization_context)
    return (
        "MAS controller authorization. "
        f"`{decision_path}` is the active MAS authorization for this runtime turn.\n\n"
        f"- decision_id: `{decision_id}`\n"
        f"- controller_actions: {controller_actions}\n"
        f"- route_target: `{route_target}` ({route_target_label})\n"
        f"- route_key_question: {route_key_question}\n"
        f"- route_rationale: {route_rationale}\n"
        f"{work_unit_lines}"
        "- requires_human_confirmation: false\n"
        "- Runtime instruction: do not park solely because `publication_eval/latest.json` still says "
        "`requires_controller_decision=true`; execute the authorized route_key_question / active_work_unit_id and write durable "
        "evidence, review, or route outputs. Only stop for a true external credential, human-only choice, "
        "or startup boundary."
    )


def _controller_actions_markdown(authorization_context: dict[str, Any]) -> str:
    return ", ".join(
        f"`{action}`"
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    )


def _controller_work_unit_message_lines(authorization_context: dict[str, Any]) -> str:
    source_route_key_question = str(authorization_context.get("source_route_key_question") or "").strip()
    route_key_question = str(authorization_context.get("route_key_question") or "").strip()
    work_unit_id = str(authorization_context.get("work_unit_id") or "").strip()
    work_unit_fingerprint = str(authorization_context.get("work_unit_fingerprint") or "").strip()
    lines: list[str] = []
    _append_optional_line(lines, "active_work_unit_id", work_unit_id, code=True)
    _append_optional_line(lines, "work_unit_fingerprint", work_unit_fingerprint, code=True)
    _append_json_line(lines, "next_work_unit", authorization_context.get("next_work_unit"))
    _append_json_line(lines, "blocking_work_units", authorization_context.get("blocking_work_units"))
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        _append_json_line(lines, key, authorization_context.get(key))
    if source_route_key_question and source_route_key_question != route_key_question:
        lines.append(f"- source_route_key_question: {source_route_key_question}")
    return "\n".join(lines) + ("\n" if lines else "")


def _append_optional_line(lines: list[str], key: str, value: str, *, code: bool = False) -> None:
    if not value:
        return
    rendered = f"`{value}`" if code else value
    lines.append(f"- {key}: {rendered}")


def _append_json_line(lines: list[str], key: str, value: Any) -> None:
    if isinstance(value, dict) and value:
        lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}")
    elif isinstance(value, list) and value:
        lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False, sort_keys=True)}")


def _runtime_message_id(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    nested_message = payload.get("message")
    if isinstance(nested_message, dict):
        message_id = str(nested_message.get("id") or nested_message.get("message_id") or "").strip()
        if message_id:
            return message_id
    message_id = str(payload.get("message_id") or payload.get("id") or "").strip()
    return message_id or None


def _write_runtime_state(*, quest_root: Path, runtime_state: dict[str, Any]) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _reset_same_fingerprint_count_for_new_control_intent(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    current_key = str(authorization_context.get("control_intent_key") or "").strip()
    if not current_key:
        return False
    previous_keys: list[str] = []
    marker = runtime_state.get(_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if isinstance(marker, dict):
        previous_keys.append(str(marker.get("control_intent_key") or "").strip())
    lifecycle = runtime_state.get(_CONTROL_INTENT_LIFECYCLE_STATE_KEY)
    if isinstance(lifecycle, dict):
        previous_keys.append(str(lifecycle.get("control_intent_key") or "").strip())
    if not any(previous_key and previous_key != current_key for previous_key in previous_keys):
        return False
    runtime_state["same_fingerprint_auto_turn_count"] = 0
    runtime_state.pop(_CONTROL_INTENT_LIFECYCLE_STATE_KEY, None)
    runtime_state.pop(_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY, None)
    return True


def _mark_controller_decision_authorization_relayed(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    delivery_mode: str,
    message_id: str | None,
    source: str,
) -> None:
    _reset_same_fingerprint_count_for_new_control_intent(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    )
    runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY] = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
        "source_route_key_question": str(authorization_context.get("source_route_key_question") or "").strip() or None,
        "work_unit_id": str(authorization_context.get("work_unit_id") or "").strip() or None,
        "work_unit_fingerprint": str(authorization_context.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": dict(authorization_context.get("next_work_unit") or {}),
        "blocking_work_units": list(authorization_context.get("blocking_work_units") or []),
        "control_intent_key": str(authorization_context.get("control_intent_key") or "").strip() or None,
        "control_intent_identity": dict(authorization_context.get("control_intent_identity") or {}),
        "active_run_id": active_run_id,
        "delivery_mode": delivery_mode,
        "message_id": message_id,
        "source": source,
        "controller_work_unit_lifecycle": _controller_work_unit_lifecycle_projection(
            authorization_context.get("controller_work_unit_lifecycle")
        ),
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in authorization_context:
            runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY][key] = authorization_context[key]
    _write_runtime_state(quest_root=quest_root, runtime_state=runtime_state)


def _runtime_state_awaits_artifact_delta_or_gate_replay(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    lifecycle = runtime_state.get(_CONTROL_INTENT_LIFECYCLE_STATE_KEY)
    if not isinstance(lifecycle, dict):
        return False
    if str(lifecycle.get("state") or "").strip() != control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY:
        return False
    lifecycle_key = str(lifecycle.get("control_intent_key") or "").strip()
    current_key = str(authorization_context.get("control_intent_key") or "").strip()
    return bool(lifecycle_key and current_key and lifecycle_key == current_key)


def _controller_decision_authorization_allowed_while_waiting(
    *,
    status: StudyRuntimeStatus,
    authorization_context: dict[str, Any],
) -> bool:
    controller_actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    if controller_actions & _CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS:
        return True
    if (
        "run_quality_repair_batch" in controller_actions
        and _quality_repair_authorization_has_current_work_unit(
            status=status,
            authorization_context=authorization_context,
        )
    ):
        return True
    if (
        status.decision is StudyRuntimeDecision.RELAUNCH_STOPPED
        and controller_actions & _CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS
    ):
        return True
    return False


def _quality_repair_authorization_has_current_work_unit(
    *,
    status: StudyRuntimeStatus,
    authorization_context: dict[str, Any],
) -> bool:
    next_work_unit = authorization_context.get("next_work_unit")
    if not isinstance(next_work_unit, dict):
        return False
    unit_id = _text(next_work_unit.get("unit_id"))
    work_unit_fingerprint = _text(authorization_context.get("work_unit_fingerprint"))
    if unit_id is None or work_unit_fingerprint is None:
        return False
    supervisor_payload = status.extras.get("publication_supervisor_state")
    if (
        isinstance(supervisor_payload, dict)
        and bool(supervisor_payload.get("bundle_tasks_downstream_only"))
        and unit_id in _QUALITY_REPAIR_DOWNSTREAM_WORK_UNIT_IDS
    ):
        return False
    return True


def _relay_controller_decision_authorization_if_required(
    *,
    status: StudyRuntimeStatus,
    context: Any,
) -> dict[str, Any] | None:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
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
    if _runtime_state_awaits_artifact_delta_or_gate_replay(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    ) and not _controller_decision_authorization_allowed_while_waiting(
        status=status,
        authorization_context=authorization_context,
    ):
        identity = _controller_decision_authorization_identity(authorization_context)
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
