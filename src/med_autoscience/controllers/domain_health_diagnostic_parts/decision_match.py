from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _decision_record_module():
    return import_module("med_autoscience.study_decision_record")


def _runtime_escalation_module():
    return import_module("med_autoscience.runtime_escalation_record")


def _latest_controller_decision_record(*, study_root: Path) -> Any | None:
    latest_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    payload = _read_json_object(latest_path)
    if payload is None:
        return None
    return _decision_record_module().StudyDecisionRecord.from_payload(payload)


def _desired_decision_refs(*, tick_request: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    decision_record = _decision_record_module()
    charter_ref = decision_record.StudyDecisionCharterRef.from_payload(
        dict(tick_request.get("charter_ref") or {})
    ).to_dict()
    publication_eval_ref = decision_record.StudyDecisionPublicationEvalRef.from_payload(
        dict(tick_request.get("publication_eval_ref") or {})
    ).to_dict()
    return charter_ref, publication_eval_ref


def _desired_controller_actions(*, tick_request: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    decision_record = _decision_record_module()
    return tuple(
        decision_record.StudyDecisionControllerAction.from_payload(action).to_dict()
        for action in (tick_request.get("controller_actions") or [])
        if isinstance(action, dict)
    )


def _desired_runtime_escalation_ref(*, status_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    payload = status_payload.get("runtime_escalation_ref")
    if not isinstance(payload, dict):
        return None
    return _runtime_escalation_module().RuntimeEscalationRecordRef.from_payload(dict(payload)).to_dict()


def _record_core_fields_match(
    *,
    record: Any,
    tick_request: Mapping[str, Any],
) -> bool:
    expected_fields = {
        "decision_type": _non_empty_text(tick_request.get("decision_type")),
        "reason": _non_empty_text(tick_request.get("reason")) or "",
        "route_target": _non_empty_text(tick_request.get("route_target")),
        "route_key_question": _non_empty_text(tick_request.get("route_key_question")),
        "route_rationale": _non_empty_text(tick_request.get("route_rationale")),
        "source_route_key_question": _non_empty_text(tick_request.get("source_route_key_question")),
        "work_unit_fingerprint": _non_empty_text(tick_request.get("work_unit_fingerprint")),
    }
    record_fields = {
        "decision_type": record.decision_type.value,
        "reason": record.reason,
        "route_target": record.route_target,
        "route_key_question": record.route_key_question,
        "route_rationale": record.route_rationale,
        "source_route_key_question": record.source_route_key_question,
        "work_unit_fingerprint": record.work_unit_fingerprint,
    }
    return (
        record_fields == expected_fields
        and record.requires_human_confirmation is bool(tick_request.get("requires_human_confirmation"))
    )


def _desired_next_work_unit(*, tick_request: Mapping[str, Any]) -> dict[str, Any] | None:
    next_work_unit = tick_request.get("next_work_unit")
    return dict(next_work_unit) if isinstance(next_work_unit, dict) else None


def _desired_blocking_work_units(*, tick_request: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(
        dict(unit)
        for unit in (tick_request.get("blocking_work_units") or [])
        if isinstance(unit, dict)
    )


def _record_work_units_match(*, record: Any, tick_request: Mapping[str, Any]) -> bool:
    return (
        record.next_work_unit == _desired_next_work_unit(tick_request=tick_request)
        and tuple(dict(unit) for unit in record.blocking_work_units)
        == _desired_blocking_work_units(tick_request=tick_request)
    )


def _record_refs_match(
    *,
    record: Any,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> bool:
    desired_charter_ref, desired_publication_eval_ref = _desired_decision_refs(tick_request=tick_request)
    desired_runtime_escalation_ref = _desired_runtime_escalation_ref(status_payload=status_payload)
    if record.charter_ref.to_dict() != desired_charter_ref:
        return False
    if record.publication_eval_ref.to_dict() != desired_publication_eval_ref:
        return False
    if desired_runtime_escalation_ref is None:
        return True
    return record.runtime_escalation_ref.to_dict() == desired_runtime_escalation_ref


def _record_actions_match(*, record: Any, tick_request: Mapping[str, Any]) -> bool:
    return tuple(action.to_dict() for action in record.controller_actions) == _desired_controller_actions(
        tick_request=tick_request
    )


def controller_decision_latest_matches_outer_loop_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
) -> bool:
    record = _latest_controller_decision_record(study_root=study_root)
    if record is None:
        return False
    return (
        _record_core_fields_match(record=record, tick_request=tick_request)
        and _record_work_units_match(record=record, tick_request=tick_request)
        and _record_refs_match(record=record, status_payload=status_payload, tick_request=tick_request)
        and _record_actions_match(record=record, tick_request=tick_request)
    )


__all__ = ["controller_decision_latest_matches_outer_loop_request"]
