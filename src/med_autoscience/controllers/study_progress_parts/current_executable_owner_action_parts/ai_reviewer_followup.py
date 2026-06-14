from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import (
    AI_REVIEWER_ACTION,
    AI_REVIEWER_WORK_UNIT,
    REPAIR_PROGRESS_SOURCE,
    TERMINAL_NEXT_FORCED_DELTA_ACTIONS,
)


def consumed_ai_reviewer_followup_allows_publication_repair(payload: Mapping[str, Any]) -> bool:
    return _consumed_ai_reviewer_followup_routes_to_write_repair(
        payload
    ) or _record_only_ai_reviewer_closeout_routes_to_publication_repair(payload)


def terminal_stage_closeout_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status not in {
        "closed_with_domain_owner_refs",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "executed_with_owner_receipt",
        "record_only_archive_materialized",
    } and outcome not in {"owner_receipt", "closed_with_domain_owner_refs"}:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    next_owner = (
        _non_empty_text(next_forced_delta.get("owner"))
        or _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
    )
    next_action_type = _non_empty_text(owner_action.get("action_type")) or _non_empty_text(
        next_forced_delta.get("action_type")
    )
    if _terminal_stage_semantically_consumes_ai_reviewer_followup(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
    ):
        return next_action_type in TERMINAL_NEXT_FORCED_DELTA_ACTIONS or next_action_type in {
            "return_to_write",
        }
    if next_owner != "mas_controller":
        return False
    if next_action_type not in {
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner",
        "return_to_write",
    }:
        return False
    action_stage_attempt = _stage_attempt_id_from_refs(action.get("acceptance_refs"))
    terminal_stage_attempt = _non_empty_text(terminal.get("stage_attempt_id")) or _stage_attempt_id_from_refs(
        [terminal.get("source_path")]
    )
    if action_stage_attempt is not None and terminal_stage_attempt is not None:
        return action_stage_attempt == terminal_stage_attempt
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    if terminal_stage_attempt is not None and source_eval_id is not None:
        return terminal_stage_attempt in source_eval_id
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("source_fingerprint"))
    )
    terminal_refs = [terminal.get("source_path"), *_text_items(terminal.get("closeout_refs"))]
    return action_fingerprint is not None and any(
        action_fingerprint in ref for ref in terminal_refs if isinstance(ref, str)
    )


def ai_reviewer_eval_receipt_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    if _non_empty_text(consumption.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    receipt_ref = _non_empty_text(consumption.get("receipt_ref"))
    if receipt_ref is None or "publication_eval" not in receipt_ref:
        return False
    if _non_empty_text(consumption.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    return _ai_reviewer_eval_receipt_binds_repair_followup(
        action=action,
        consumption=consumption,
    )


def _consumed_ai_reviewer_followup_routes_to_write_repair(payload: Mapping[str, Any]) -> bool:
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    if _terminal_stage_semantically_consumes_ai_reviewer_followup(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
    ):
        return True
    return _record_only_ai_reviewer_closeout_routes_to_write_repair(
        terminal=terminal,
        next_forced_delta=next_forced_delta,
    )


def _record_only_ai_reviewer_closeout_routes_to_publication_repair(payload: Mapping[str, Any]) -> bool:
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status not in {
        "closed_with_domain_owner_refs",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "record_only_archive_materialized",
    } and outcome not in {"closed_with_domain_owner_refs"}:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    next_owner = (
        _non_empty_text(next_forced_delta.get("owner"))
        or _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
    )
    next_action_type = _non_empty_text(owner_action.get("action_type")) or _non_empty_text(
        next_forced_delta.get("action_type")
    )
    if next_owner != "mas_controller":
        return False
    if next_action_type != "consume_record_only_ai_reviewer_closeout_or_route_next_owner":
        return False
    if _non_empty_text(next_forced_delta.get("required_delta_kind")) != (
        "mas_owner_route_reconcile_or_typed_blocker_consumption"
    ):
        return False
    reviewer_record_ref = _non_empty_text(next_forced_delta.get("reviewer_record_ref"))
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    return (reviewer_record_ref is not None and "publication_eval" in reviewer_record_ref) or (
        source_eval_id is not None and "publication-eval" in source_eval_id
    )


def _terminal_stage_semantically_consumes_ai_reviewer_followup(
    *,
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> bool:
    required_delta_kind = _non_empty_text(next_forced_delta.get("required_delta_kind"))
    if required_delta_kind not in {
        "same_line_write_repair_or_gate_replay_route",
        "same_line_write_repair_or_typed_blocker_consumption",
    }:
        return False
    next_work_unit = _non_empty_text(next_forced_delta.get("work_unit_id"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    if _non_empty_text(owner_action.get("work_unit_id")) not in {next_work_unit, None}:
        return False
    if next_work_unit in {None, AI_REVIEWER_WORK_UNIT}:
        return False
    progress_delta_classification = (
        _non_empty_text(paper_stage_log.get("progress_delta_classification"))
        or _non_empty_text(terminal.get("progress_delta_classification"))
    )
    if progress_delta_classification not in {"deliverable_progress", "paper_progress", "mixed"}:
        return False
    refs = _dedupe_text(
        [
            terminal.get("source_path"),
            *list(terminal.get("closeout_refs") or []),
            *list(terminal.get("changed_paper_surfaces") or []),
            *list(paper_stage_log.get("changed_paper_surfaces") or []),
            _mapping_copy(next_forced_delta.get("target_surface")).get("surface_ref"),
            _mapping_copy(next_forced_delta.get("target_surface")).get("publication_eval_latest_ref"),
        ]
    )
    return any("publication_eval/ai_reviewer_responses" in ref for ref in refs)


def _record_only_ai_reviewer_closeout_routes_to_write_repair(
    *,
    terminal: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> bool:
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status != "closed_with_domain_owner_refs" and outcome != "closed_with_domain_owner_refs":
        return False
    if _non_empty_text(next_forced_delta.get("required_delta_kind")) != (
        "mas_owner_route_reconcile_or_typed_blocker_consumption"
    ):
        return False
    next_owner = _non_empty_text(next_forced_delta.get("owner"))
    if next_owner != "mas_controller":
        return False
    if _non_empty_text(next_forced_delta.get("action_type")) != (
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner"
    ):
        return False
    terminal_stage_attempt = _non_empty_text(terminal.get("stage_attempt_id")) or _stage_attempt_id_from_refs(
        [terminal.get("source_path")]
    )
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    if terminal_stage_attempt is None or source_eval_id is None or terminal_stage_attempt not in source_eval_id:
        return False
    if "ai-reviewer-record" in source_eval_id:
        return True
    reviewer_record_ref = _non_empty_text(next_forced_delta.get("reviewer_record_ref"))
    return reviewer_record_ref is not None and "publication_eval/ai_reviewer_responses" in reviewer_record_ref


def _latest_ai_reviewer_terminal_stage(payload: Mapping[str, Any]) -> dict[str, Any]:
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
        if _non_empty_text(terminal.get("action_type")) == AI_REVIEWER_ACTION:
            return terminal
    return {}


def _stage_attempt_id_from_refs(value: object) -> str | None:
    for ref in _text_items(value):
        for part in ref.replace("#", "/").replace(".", "/").split("/"):
            if part.startswith("sat_"):
                return part
    return None


def _ai_reviewer_eval_receipt_binds_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    repair_precedence = _mapping_copy(action.get("repair_progress_precedence"))
    target_surface = _mapping_copy(action.get("target_surface"))
    expected_source_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(repair_precedence.get("source_fingerprint"))
    )
    binding_mappings = _ai_reviewer_consumption_binding_mappings(consumption)
    if expected_source_fingerprint is not None:
        explicit_fingerprints = {
            text
            for mapping in binding_mappings
            for key in (
                "repair_source_fingerprint",
                "repair_progress_source_fingerprint",
                "repair_execution_source_fingerprint",
            )
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_source_fingerprint in explicit_fingerprints:
            return True
    expected_refs = set(
        _dedupe_text(
            [
                action.get("source_ref"),
                target_surface.get("request_ref"),
                target_surface.get("gate_replay_request_ref"),
                *list(action.get("acceptance_refs") or []),
            ]
        )
    )
    if expected_refs:
        explicit_refs = {
            text
            for mapping in binding_mappings
            for key in (
                "repair_execution_evidence_ref",
                "owner_receipt_ref",
                "ai_reviewer_recheck_request_ref",
                "request_ref",
                "gate_replay_request_ref",
            )
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_refs.intersection(explicit_refs):
            return True
    expected_source_eval_id = _non_empty_text(repair_precedence.get("source_eval_id"))
    if expected_source_eval_id is not None:
        explicit_source_eval_ids = {
            text
            for mapping in binding_mappings
            for key in ("repair_source_eval_id", "repair_progress_source_eval_id")
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_source_eval_id in explicit_source_eval_ids:
            return True
    return False


def _ai_reviewer_consumption_binding_mappings(consumption: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    canonical = _mapping_copy(consumption.get("canonical_work_unit_identity"))
    owner_route_basis = _mapping_copy(consumption.get("owner_route_currentness_basis"))
    canonical_owner_route_basis = _mapping_copy(canonical.get("owner_route_currentness_basis"))
    source_refs = _mapping_copy(consumption.get("source_refs"))
    source_refs_basis = _mapping_copy(source_refs.get("owner_route_currentness_basis"))
    return [
        consumption,
        canonical,
        owner_route_basis,
        canonical_owner_route_basis,
        source_refs,
        source_refs_basis,
    ]


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


__all__ = [
    "ai_reviewer_eval_receipt_consumes_repair_followup",
    "consumed_ai_reviewer_followup_allows_publication_repair",
    "terminal_stage_closeout_consumes_repair_followup",
]
