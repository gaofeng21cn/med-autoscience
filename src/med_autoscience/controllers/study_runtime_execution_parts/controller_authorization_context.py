from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.publication_eval_specificity_targets import specificity_target_status
from med_autoscience.study_decision_record import StudyDecisionRecord


_CONTROLLER_DECISION_RUNTIME_AUTHORIZATION_ACTIONS = {
    "ensure_study_runtime",
    "ensure_study_runtime_relaunch_stopped",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
    "return_to_ai_reviewer_workflow",
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
_ROUTE_TARGET_LABELS = {
    "analysis-campaign": "有限补充分析",
    "write": "当前论文主线写作",
    "review": "质量复评",
    "finalize": "finalize / 投稿包收口",
}
_UPSTREAM_PAPER_REPAIR_WORK_UNIT_IDS = frozenset(
    {
        "analysis_claim_evidence_repair",
        "figure_results_trace_repair",
        "manuscript_story_repair",
        "treatment_gap_reporting_repair",
    }
)
_FINALIZE_WORK_UNIT_IDS = frozenset(
    {
        "submission_authority_sync_closure",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
        "publication_gate_replay",
    }
)
_EXECUTION_SURFACE_LANES = frozenset({"controller"})
_ROUTE_TARGETS = frozenset({"analysis-campaign", "write", "review", "finalize", "publication_gate", "stop"})


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


def _publication_eval_payload_for_record(
    *,
    study_root: Path,
    record: StudyDecisionRecord,
) -> dict[str, Any]:
    payload = _artifact_payload_from_ref(
        study_root=study_root,
        artifact_path=record.publication_eval_ref.artifact_path,
    )
    payload_eval_id = _text(payload.get("eval_id"))
    record_eval_id = _text(record.publication_eval_ref.eval_id)
    if payload_eval_id is not None and record_eval_id is not None and payload_eval_id != record_eval_id:
        return {}
    return payload


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


def _compact_work_unit_payload(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    unit_id = _text(value.get("unit_id"))
    if unit_id is None:
        return None
    payload: dict[str, Any] = {"unit_id": unit_id}
    for key in ("lane", "summary", "control_surface", "user_feedback_priority"):
        text = _text(value.get(key))
        if text is not None:
            payload[key] = text
    if value.get("hard_methodology") is True:
        payload["hard_methodology"] = True
    for key in (
        "required_owner",
        "required_next_work_unit",
        "typed_blocker",
        "selected_route_option",
        "required_output",
    ):
        text = _text(value.get(key))
        if text is not None:
            payload[key] = text
    for key in (
        "terminal_source_provenance_blocker_consumed",
        "current_transport_claim_must_not_be_used_as_medical_conclusion",
    ):
        if value.get(key) is True:
            payload[key] = True
    required_prior_owner_outputs = [
        text for item in value.get("required_prior_owner_outputs") or [] if (text := _text(item)) is not None
    ]
    if required_prior_owner_outputs:
        payload["required_prior_owner_outputs"] = required_prior_owner_outputs
    route_options = [
        text
        for item in value.get("route_options") or []
        if (text := _text(item)) is not None
    ]
    if route_options:
        payload["route_options"] = route_options
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
        route_target = _text(action.get("route_target"))
        next_work_unit_lane = _text(next_work_unit.get("lane"))
        if route_target is None and next_work_unit_lane not in _EXECUTION_SURFACE_LANES:
            route_target = next_work_unit_lane
        return {
            "work_unit_id": unit_id,
            "work_unit_fingerprint": _text(action.get("work_unit_fingerprint")),
            "next_work_unit": next_work_unit,
            "blocking_work_units": blocking_work_units,
            "route_target": route_target,
            "route_key_question": route_key_question,
            "route_rationale": route_rationale,
            "source_route_key_question": _text(action.get("route_key_question")),
        }
    return {}


def _upstream_repair_units_from_specificity_targets(specificity_targets: object) -> list[dict[str, str]]:
    target_status = specificity_target_status(specificity_targets)
    if target_status.get("complete") is not True:
        return []
    target_kinds = {
        str(item.get("target_kind") or "").strip()
        for item in target_status.get("targets") or []
        if isinstance(item, dict)
    }
    units: list[dict[str, str]] = []
    if target_kinds & {"claim", "metric", "source_path", "table"}:
        units.append(
            {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
            }
        )
    if "figure" in target_kinds:
        units.append(
            {
                "unit_id": "figure_results_trace_repair",
                "lane": "write",
                "summary": "Repair figure and results traceability against the publication evidence surface.",
            }
        )
    return units


def _upstream_repair_work_unit_context_from_replay_targets(
    *,
    record: StudyDecisionRecord,
    publication_eval_payload: dict[str, Any],
    work_unit_context: dict[str, Any],
) -> dict[str, Any] | None:
    next_work_unit = _compact_work_unit_payload(work_unit_context.get("next_work_unit"))
    if next_work_unit is None or next_work_unit.get("unit_id") != "publication_gate_replay":
        return None
    if record.route_target not in {"analysis-campaign", "write"}:
        return None
    recommended_actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(recommended_actions, list):
        return None
    for action in recommended_actions:
        if not isinstance(action, dict):
            continue
        action_next_work_unit = _compact_work_unit_payload(action.get("next_work_unit"))
        if action_next_work_unit is None or action_next_work_unit.get("unit_id") != "publication_gate_replay":
            continue
        repair_units = _upstream_repair_units_from_specificity_targets(action.get("specificity_targets"))
        if not repair_units:
            continue
        return {
            **work_unit_context,
            "work_unit_id": repair_units[0]["unit_id"],
            "next_work_unit": repair_units[0],
            "blocking_work_units": repair_units,
            "route_target": repair_units[0]["lane"],
            "route_key_question": (
                f"{repair_units[0]['unit_id']}: {repair_units[0]['summary']}"
            ),
            "route_rationale": (
                _text(action.get("route_rationale"))
                or _text(action.get("reason"))
                or "Publication gate replay carried concrete paper-facing targets; route to upstream paper repair."
            ),
            "source_route_key_question": _text(action.get("route_key_question")) or record.route_key_question,
            "specificity_targets": [
                dict(item) for item in specificity_target_status(action.get("specificity_targets")).get("targets") or []
            ],
        }
    return None


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
    route_target = record.route_target if record.route_target in _ROUTE_TARGETS else None
    next_work_unit_lane = _text(next_work_unit.get("lane"))
    if route_target is None and next_work_unit_lane not in _EXECUTION_SURFACE_LANES:
        route_target = next_work_unit_lane
    if unit_id in _FINALIZE_WORK_UNIT_IDS and route_target in {None, "analysis-campaign", "write"}:
        route_target = "finalize"
    return {
        "work_unit_id": unit_id,
        "work_unit_fingerprint": record.work_unit_fingerprint,
        "next_work_unit": next_work_unit,
        "blocking_work_units": blocking_work_units,
        "route_target": route_target,
        "route_key_question": route_key_question,
        "route_rationale": record.route_rationale,
        "source_route_key_question": record.route_key_question,
    }


def _publication_eval_work_unit_context_is_relayable_for_record(
    *,
    record: StudyDecisionRecord,
    work_unit_context: dict[str, Any],
) -> bool:
    next_work_unit = _mapping(work_unit_context.get("next_work_unit"))
    unit_id = _text(work_unit_context.get("work_unit_id")) or _text(next_work_unit.get("unit_id"))
    lane = _text(next_work_unit.get("lane")) or _text(work_unit_context.get("route_target"))
    if unit_id in _UPSTREAM_PAPER_REPAIR_WORK_UNIT_IDS or unit_id in _FINALIZE_WORK_UNIT_IDS:
        return True
    return lane is not None and lane == record.route_target


def _stable_publication_authority_fingerprint(
    *,
    study_root: Path,
    record: StudyDecisionRecord,
) -> str:
    publication_eval_payload = _publication_eval_payload_for_record(
        study_root=study_root,
        record=record,
    )
    work_unit_context = _controller_decision_work_unit_context(record=record, study_root=study_root)
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
    publication_eval_payload = _publication_eval_payload_for_record(
        study_root=study_root,
        record=record,
    )
    record_context = _record_work_unit_context(record)
    publication_context = {} if record_context else _publication_eval_work_unit_context(publication_eval_payload)
    work_unit_context = record_context or publication_context
    upstream_context = _upstream_repair_work_unit_context_from_replay_targets(
        record=record,
        publication_eval_payload=publication_eval_payload,
        work_unit_context=work_unit_context,
    )
    if upstream_context is not None:
        return upstream_context
    if (
        not record_context
        and work_unit_context
        and not _publication_eval_work_unit_context_is_relayable_for_record(
            record=record,
            work_unit_context=work_unit_context,
        )
    ):
        return {}
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
        "decision_emitted_at": record.emitted_at,
        "study_id": record.study_id,
        "quest_id": record.quest_id,
        "decision_type": record.decision_type.value,
        "requires_human_confirmation": record.requires_human_confirmation,
        "controller_actions": controller_actions,
        "decision_path": str(decision_path),
        "publication_eval_id": record.publication_eval_ref.eval_id,
        "publication_eval_path": record.publication_eval_ref.artifact_path,
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
