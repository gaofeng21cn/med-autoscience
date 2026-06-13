from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
)
from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import (
    AI_REVIEWER_ACTION,
    GATE_CLEARING_ACTION,
    GATE_CLEARING_OWNER,
    QUALITY_REPAIR_ACTION,
    TERMINAL_NEXT_FORCED_DELTA_ACTIONS,
)


def owner_action_from_terminal_next_forced_delta(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    terminal = _latest_terminal_stage_with_next_forced_delta(payload)
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    raw_action_type = (
        _non_empty_text(owner_action.get("action_type"))
        or _non_empty_text(next_forced_delta.get("action_type"))
        or _non_empty_text(terminal.get("action_type"))
    )
    action_type = _terminal_next_forced_delta_action_type(raw_action_type)
    if action_type not in TERMINAL_NEXT_FORCED_DELTA_ACTIONS:
        return None
    work_unit_id = (
        _non_empty_text(owner_action.get("work_unit_id"))
        or _non_empty_text(next_forced_delta.get("work_unit_id"))
        or _non_empty_text(paper_stage_log.get("stage_name"))
    )
    owner = (
        _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
        or _non_empty_text(next_forced_delta.get("next_owner"))
        or _terminal_next_forced_delta_default_owner(raw_action_type)
        or _terminal_next_forced_delta_default_owner(action_type)
    )
    if owner is None and work_unit_id is None:
        return None
    if _terminal_closeout_replays_same_gate_clearing_action(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
        owner_action=owner_action,
        action_type=action_type,
        work_unit_id=work_unit_id,
    ):
        return None
    source_ref = _non_empty_text(terminal.get("source_path"))
    required_delta_kind = (
        _non_empty_text(next_forced_delta.get("required_delta_kind"))
        or "paper_progress_delta_or_typed_blocker"
    )
    target_surface = _mapping_copy(next_forced_delta.get("target_surface")) or {
        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
    }
    source_eval_id = _non_empty_text(owner_action.get("source_eval_id")) or _non_empty_text(
        next_forced_delta.get("source_eval_id")
    )
    fingerprint = _terminal_next_forced_delta_fingerprint(
        payload=payload,
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
        owner_action=owner_action,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    if fingerprint is None and action_type != GATE_CLEARING_ACTION:
        return None
    owner_route_currentness_basis = _compact(
        {
            "source": "study_progress.next_forced_delta.owner_action",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "terminal_stage_status": _non_empty_text(terminal.get("status")),
            "terminal_stage_action_type": _non_empty_text(terminal.get("action_type")),
        }
    )
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": owner_route_currentness_basis or None,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": required_delta_kind,
            "target_surface": target_surface,
            "target_surface_specificity": _non_empty_text(
                next_forced_delta.get("target_surface_specificity")
            )
            or "terminal_stage_next_forced_delta",
            "terminal_stage_next_forced_delta": True,
            "acceptance_refs": _dedupe_text(
                [source_ref, *_text_items(next_forced_delta.get("acceptance_refs"))]
            ),
            "authority_boundary": _authority_boundary(),
        }
    )


def _terminal_next_forced_delta_default_owner(action_type: str | None) -> str | None:
    if action_type == "return_to_write":
        return "write"
    if action_type == GATE_CLEARING_ACTION:
        return GATE_CLEARING_OWNER
    if action_type == QUALITY_REPAIR_ACTION:
        return "write"
    if action_type == "consume_record_only_ai_reviewer_closeout_or_route_next_owner":
        return "mas_controller"
    return None


def _terminal_next_forced_delta_action_type(action_type: str | None) -> str | None:
    if action_type == "return_to_write":
        return QUALITY_REPAIR_ACTION
    return action_type


def _terminal_closeout_replays_same_gate_clearing_action(
    *,
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
) -> bool:
    if action_type != GATE_CLEARING_ACTION:
        return False
    if _non_empty_text(terminal.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    if _non_empty_text(terminal.get("status")) not in {
        "closed",
        "completed",
        "executed",
        "failed",
        "repeat_suppressed",
    }:
        return False
    terminal_work_unit_id = (
        _non_empty_text(terminal.get("work_unit_id"))
        or _non_empty_text(paper_stage_log.get("work_unit_id"))
        or _non_empty_text(next_forced_delta.get("work_unit_id"))
    )
    if work_unit_id is None or terminal_work_unit_id != work_unit_id:
        return False
    owner = _non_empty_text(owner_action.get("next_owner")) or _non_empty_text(
        owner_action.get("owner")
    )
    if owner not in {None, GATE_CLEARING_OWNER}:
        return False
    terminal_fingerprint = (
        _non_empty_text(terminal.get("work_unit_fingerprint"))
        or _non_empty_text(terminal.get("action_fingerprint"))
        or _non_empty_text(paper_stage_log.get("work_unit_fingerprint"))
        or _non_empty_text(paper_stage_log.get("action_fingerprint"))
    )
    owner_action_fingerprint = (
        _non_empty_text(owner_action.get("work_unit_fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint"))
        or _non_empty_text(next_forced_delta.get("work_unit_fingerprint"))
        or _non_empty_text(next_forced_delta.get("action_fingerprint"))
    )
    return owner_action_fingerprint is None or terminal_fingerprint == owner_action_fingerprint


def _latest_terminal_stage_with_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if not terminal:
            continue
        paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
        next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
            paper_stage_log.get("next_forced_delta")
        )
        owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
        action_type = _terminal_next_forced_delta_action_type(
            _non_empty_text(owner_action.get("action_type"))
            or _non_empty_text(next_forced_delta.get("action_type"))
            or _non_empty_text(terminal.get("action_type"))
        )
        if action_type in TERMINAL_NEXT_FORCED_DELTA_ACTIONS:
            return terminal
    return {}


def _terminal_next_forced_delta_fingerprint(
    *,
    payload: Mapping[str, Any],
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
    source_eval_id: str | None,
) -> str | None:
    explicit_fingerprint = (
        _non_empty_text(owner_action.get("work_unit_fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint"))
        or _non_empty_text(owner_action.get("fingerprint"))
        or _non_empty_text(next_forced_delta.get("work_unit_fingerprint"))
        or _non_empty_text(next_forced_delta.get("action_fingerprint"))
        or _non_empty_text(next_forced_delta.get("fingerprint"))
    )
    if explicit_fingerprint is not None:
        return explicit_fingerprint
    if work_unit_id == _non_empty_text(paper_stage_log.get("work_unit_id")):
        paper_stage_fingerprint = (
            _non_empty_text(paper_stage_log.get("work_unit_fingerprint"))
            or _non_empty_text(paper_stage_log.get("action_fingerprint"))
            or _non_empty_text(paper_stage_log.get("fingerprint"))
        )
        if paper_stage_fingerprint is not None:
            return paper_stage_fingerprint
    if work_unit_id == _non_empty_text(terminal.get("work_unit_id")):
        terminal_fingerprint = (
            _non_empty_text(terminal.get("work_unit_fingerprint"))
            or _non_empty_text(terminal.get("action_fingerprint"))
            or _non_empty_text(terminal.get("fingerprint"))
        )
        if terminal_fingerprint is not None:
            return terminal_fingerprint
    if action_type != GATE_CLEARING_ACTION:
        return _terminal_closeout_next_forced_delta_fingerprint(
            payload=payload,
            terminal=terminal,
            next_forced_delta=next_forced_delta,
            owner_action=owner_action,
            action_type=action_type,
            work_unit_id=work_unit_id,
            source_eval_id=source_eval_id,
        )
    study_id = _non_empty_text(payload.get("study_id"))
    return current_ai_reviewer_gate_replay_fingerprint(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )


def _terminal_closeout_next_forced_delta_fingerprint(
    *,
    payload: Mapping[str, Any],
    terminal: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
    source_eval_id: str | None,
) -> str | None:
    terminal_ref = (
        _non_empty_text(terminal.get("source_path"))
        or _non_empty_text(terminal.get("source_ref"))
        or _non_empty_text(terminal.get("closeout_ref"))
    )
    stage_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    reviewer_record_ref = _non_empty_text(
        next_forced_delta.get("reviewer_record_ref")
    ) or _non_empty_text(owner_action.get("reviewer_record_ref"))
    publication_eval_ref = _non_empty_text(
        _mapping_copy(next_forced_delta.get("target_surface")).get("publication_eval_latest_ref")
    )
    if not any(
        (terminal_ref, stage_attempt_id, reviewer_record_ref, publication_eval_ref, source_eval_id)
    ):
        return None
    terminal_action_type = _non_empty_text(terminal.get("action_type"))
    if (
        action_type == QUALITY_REPAIR_ACTION
        and terminal_action_type == AI_REVIEWER_ACTION
        and not any((reviewer_record_ref, publication_eval_ref, source_eval_id))
    ):
        return None
    return control_identity.stable_route_currentness_fingerprint(
        study_id=_non_empty_text(payload.get("study_id")),
        source="study_progress.next_forced_delta.owner_action",
        work_unit_id=work_unit_id,
        action_type=action_type,
        next_owner=_non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
        or _terminal_next_forced_delta_default_owner(action_type),
        source_eval_id=source_eval_id,
        target_surface_ref=publication_eval_ref or reviewer_record_ref or terminal_ref,
        required_delta_kind=_non_empty_text(next_forced_delta.get("required_delta_kind")),
    )


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe_text(items: list[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = ["owner_action_from_terminal_next_forced_delta"]
