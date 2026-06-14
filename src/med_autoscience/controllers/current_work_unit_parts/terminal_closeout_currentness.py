from __future__ import annotations

import ast
from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    acceptance_refs,
    action_fingerprint,
    action_type,
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.runtime_control.owner_route_attempt_protocol import owner_reason_contract


MappingReader = Callable[[object], dict[str, Any]]
TextReader = Callable[[object], str | None]
TextItemsReader = Callable[[object], list[str]]
ActionTypeReader = Callable[[Mapping[str, Any]], str | None]
WorkUnitIdReader = Callable[[object], str | None]
FingerprintReader = Callable[[Mapping[str, Any]], str | None]


TERMINAL_ACTION_BLOCKING_STATUSES = frozenset(
    {
        "blocked",
        "repeat_suppressed",
        "typed_blocked",
    }
)
GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES = frozenset(
    {
        "closed",
        "completed",
        "executed",
        "fresh",
        "skipped_duplicate_eval",
        "skipped_stale_gate_replay_closed",
    }
)
OPL_RUNTIME_TERMINAL_BLOCKERS = frozenset(
    {
        "domain_closeout_provided_incomplete_user_stage_log",
        "medical_prose_review_request_rehydrate_required",
        "stage_packet_not_current_selected_dispatch",
        "typed_closeout_packet_required",
    }
)


def terminal_closeout_blocker_for_action(
    progress: Mapping[str, Any],
    *,
    action: Mapping[str, Any] | None,
    mapping: MappingReader,
    text: TextReader,
    text_items: TextItemsReader,
    action_type: ActionTypeReader,
    work_unit_id: WorkUnitIdReader,
    work_unit_fingerprint: FingerprintReader,
    action_fingerprint: FingerprintReader,
) -> dict[str, Any] | None:
    action_payload = mapping(action)
    if not action_payload:
        return None
    if _gate_replay_terminal_superseded_by_followthrough(
        progress,
        action=action_payload,
        mapping=mapping,
        text=text,
        action_type=action_type,
        work_unit_id=work_unit_id,
    ):
        return None
    terminal = None
    for candidate in _terminal_stage_candidates(progress, mapping=mapping):
        if _terminal_stage_blocks_action(
            candidate,
            action=action_payload,
            mapping=mapping,
            text=text,
            action_type=action_type,
            work_unit_id=work_unit_id,
        ):
            terminal = candidate
            break
    if terminal is None:
        return None
    blocker_type = _terminal_stage_blocker_reason(terminal, mapping=mapping, text=text)
    structured_blocker = mapping(terminal.get("typed_blocker"))
    terminal_fresh_current_identity = _terminal_fresh_current_control_identity(
        terminal,
        mapping=mapping,
        text=text,
    )
    resolved_work_unit_id = work_unit_id(terminal_fresh_current_identity.get("work_unit_id")) or work_unit_id(
        structured_blocker.get("work_unit_id")
    ) or work_unit_id(
        structured_blocker.get("next_work_unit")
    ) or work_unit_id(action_payload.get("work_unit_id")) or work_unit_id(
        action_payload.get("next_work_unit")
    )
    currentness_basis = mapping(action_payload.get("owner_route_currentness_basis"))
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    terminal_fingerprint = _terminal_identity_fingerprint(terminal, mapping=mapping, text=text)
    resolved_work_unit_fingerprint = terminal_fingerprint or work_unit_fingerprint(
        action_payload,
        currentness_basis=currentness_basis,
    )
    source_ref = text(terminal.get("source_path")) or text(terminal.get("record_path"))
    return {
        key: value
        for key, value in {
            **structured_blocker,
            "blocker_type": blocker_type,
            "blocker_id": blocker_type,
            "blocked_reason": blocker_type,
            "owner": _terminal_stage_blocker_owner(
                terminal,
                blocker_reason=blocker_type,
                mapping=mapping,
                text=text,
            ),
            "action_type": action_type(action_payload),
            "work_unit_id": resolved_work_unit_id,
            "work_unit_fingerprint": resolved_work_unit_fingerprint,
            "action_fingerprint": terminal_fingerprint
            or action_fingerprint(action_payload, currentness_basis=currentness_basis),
            "source_ref": source_ref,
            "acceptance_refs": text_items(terminal.get("closeout_refs"))
            + text_items(terminal.get("evidence_refs"))
            + ([source_ref] if source_ref is not None else []),
            "terminal_closeout_status": text(terminal.get("status")),
            "terminal_closeout_outcome": text(terminal.get("outcome")) or text(paper_stage_log.get("outcome")),
            "progress_delta_classification": text(terminal.get("progress_delta_classification"))
            or text(paper_stage_log.get("progress_delta_classification")),
        }.items()
        if value not in (None, "", [], {})
    }


def _gate_replay_terminal_superseded_by_followthrough(
    progress: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
    mapping: MappingReader,
    text: TextReader,
    action_type: ActionTypeReader,
    work_unit_id: WorkUnitIdReader,
) -> bool:
    if action_type(action) != "run_gate_clearing_batch":
        return False
    followthrough = mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return False
    if text(followthrough.get("status")) not in GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES:
        return False
    action_source_eval = _action_source_eval_id(action, mapping=mapping, text=text)
    followthrough_source_eval = text(followthrough.get("source_eval_id"))
    if action_source_eval is None or followthrough_source_eval != action_source_eval:
        return False
    action_work_unit = work_unit_id(action.get("work_unit_id")) or work_unit_id(action.get("next_work_unit"))
    followthrough_work_unit = (
        work_unit_id(followthrough.get("work_unit_id"))
        or work_unit_id(mapping(followthrough.get("work_unit_currentness")).get("explicit_publication_work_unit_id"))
        or work_unit_id(mapping(followthrough.get("explicit_publication_work_unit")).get("unit_id"))
    )
    return action_work_unit is not None and followthrough_work_unit == action_work_unit


def gate_replay_consumed_by_source_eval(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    if text(action.get("action_type")) != "run_gate_clearing_batch":
        return False
    if text(consumption.get("receipt_kind")) != "gate_clearing_batch":
        return False
    action_source_eval = _action_source_eval_id(action, mapping=mapping, text=text)
    consumed_source_eval = _consumption_source_eval_id(consumption, mapping=mapping, text=text)
    return bool(action_source_eval and action_source_eval == consumed_source_eval)


def consumed_gate_replay_blocker_for_action(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    currentness_basis: Mapping[str, Any],
    mapping: MappingReader,
    text: TextReader,
    text_items: TextItemsReader,
) -> dict[str, Any] | None:
    action_payload = mapping(action)
    if action_type(action_payload) != "run_gate_clearing_batch":
        return None
    followthrough = mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return None
    if text(followthrough.get("status")) not in GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES:
        return None
    if text(followthrough.get("gate_replay_status")) != "blocked":
        return None
    action_source_eval = _action_source_eval_id(
        action_payload,
        mapping=mapping,
        text=text,
        currentness_basis=currentness_basis,
    )
    followthrough_source_eval = text(followthrough.get("source_eval_id"))
    if action_source_eval is None or followthrough_source_eval != action_source_eval:
        return None
    action_work_unit = work_unit_id(action_payload.get("work_unit_id")) or work_unit_id(
        action_payload.get("next_work_unit")
    )
    followthrough_work_unit = (
        work_unit_id(followthrough.get("work_unit_id"))
        or work_unit_id(mapping(followthrough.get("work_unit_currentness")).get("explicit_publication_work_unit_id"))
        or work_unit_id(mapping(followthrough.get("explicit_publication_work_unit")).get("unit_id"))
    )
    if action_work_unit is None or followthrough_work_unit != action_work_unit:
        return None
    if _gate_followthrough_has_actionable_next_work_unit(
        followthrough,
        action_work_unit=action_work_unit,
        mapping=mapping,
        text=text,
    ):
        return None
    source_ref = text(followthrough.get("latest_record_path"))
    return {
        "blocker_type": "publication_gate_replay_blocked",
        "blocker_id": "publication_gate_replay_blocked",
        "blocked_reason": "publication_gate_replay_blocked",
        "owner": "publication_gate",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": action_work_unit,
        "work_unit_fingerprint": work_unit_fingerprint(action_payload, currentness_basis=currentness_basis),
        "action_fingerprint": action_fingerprint(action_payload, currentness_basis=currentness_basis),
        "source_eval_id": followthrough_source_eval,
        "source_ref": source_ref,
        "acceptance_refs": [ref for ref in [source_ref, *acceptance_refs(action_payload)] if ref],
        "gate_replay_status": "blocked",
        "gate_replay_blockers": text_items(followthrough.get("gate_replay_blockers")),
        "blocking_issue_count": followthrough.get("blocking_issue_count"),
        "failed_unit_count": followthrough.get("failed_unit_count"),
        "next_confirmation_signal": text(followthrough.get("next_confirmation_signal")),
    }


def _gate_followthrough_has_actionable_next_work_unit(
    followthrough: Mapping[str, Any],
    *,
    action_work_unit: str,
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    currentness = mapping(followthrough.get("work_unit_currentness"))
    if text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    current_work_unit = work_unit_id(currentness.get("current_publication_work_unit_id")) or work_unit_id(
        mapping(followthrough.get("current_publication_work_unit")).get("unit_id")
    )
    return current_work_unit is not None and current_work_unit != action_work_unit


def _latest_terminal_stage(
    progress: Mapping[str, Any],
    *,
    mapping: MappingReader,
) -> dict[str, Any]:
    for terminal in _terminal_stage_candidates(progress, mapping=mapping):
        return terminal
    return {}


def _terminal_stage_candidates(
    progress: Mapping[str, Any],
    *,
    mapping: MappingReader,
) -> tuple[dict[str, Any], ...]:
    progress_first = mapping(progress.get("progress_first_monitoring_summary"))
    handoff = mapping(progress.get("opl_current_control_state_handoff"))
    candidates: list[dict[str, Any]] = []
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        progress.get("latest_terminal_stage"),
        progress.get("latest_terminal_stage_log"),
    ):
        terminal = mapping(value)
        if terminal:
            candidates.append(terminal)
    return tuple(candidates)


def _terminal_stage_blocks_action(
    terminal: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
    mapping: MappingReader,
    text: TextReader,
    action_type: ActionTypeReader,
    work_unit_id: WorkUnitIdReader,
) -> bool:
    status = text(terminal.get("status"))
    outcome = text(terminal.get("outcome"))
    classification = text(terminal.get("progress_delta_classification"))
    if (
        status not in TERMINAL_ACTION_BLOCKING_STATUSES
        and outcome not in TERMINAL_ACTION_BLOCKING_STATUSES
        and classification != "typed_blocker"
        and not mapping(terminal.get("typed_blocker"))
    ):
        return False
    expected_action = action_type(action)
    terminal_action = text(terminal.get("action_type"))
    typed_blocker = mapping(terminal.get("typed_blocker"))
    typed_blocker_action = text(typed_blocker.get("action_type"))
    if expected_action is None:
        return False
    if typed_blocker_action is not None and typed_blocker_action != expected_action:
        return False
    if terminal_action is not None and terminal_action != expected_action:
        return False
    if _terminal_stage_identity_conflicts_action(
        terminal,
        action=action,
        mapping=mapping,
        text=text,
    ):
        return False
    expected_work_unit = work_unit_id(action.get("work_unit_id")) or work_unit_id(action.get("next_work_unit"))
    terminal_work_units = {
        item
        for value in (
            typed_blocker.get("work_unit_id"),
            typed_blocker.get("next_work_unit"),
            terminal.get("work_unit_id"),
            terminal.get("next_work_unit"),
            terminal.get("stage_name"),
            mapping(terminal.get("next_forced_delta")).get("work_unit_id"),
            mapping(mapping(terminal.get("next_forced_delta")).get("owner_action")).get("work_unit_id"),
            mapping(mapping(terminal.get("paper_stage_log")).get("next_forced_delta")).get("work_unit_id"),
            mapping(
                mapping(mapping(terminal.get("paper_stage_log")).get("next_forced_delta")).get("owner_action")
            ).get("work_unit_id"),
            mapping(mapping(terminal.get("terminal_closeout_semantic_completeness")).get("next_forced_delta")).get(
                "work_unit_id"
            ),
            mapping(
                mapping(
                    mapping(terminal.get("terminal_closeout_semantic_completeness")).get("next_forced_delta")
                ).get("owner_action")
            ).get("work_unit_id"),
        )
        if (item := work_unit_id(value)) is not None
    }
    if expected_work_unit is not None and terminal_work_units:
        return expected_work_unit in terminal_work_units
    return expected_work_unit is not None


def _terminal_stage_identity_conflicts_action(
    terminal: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    action_fp = _action_identity_fingerprint(action, mapping=mapping, text=text)
    terminal_fp = _terminal_identity_fingerprint(terminal, mapping=mapping, text=text)
    if action_fp is not None and terminal_fp is not None and action_fp != terminal_fp:
        return not _terminal_typed_blocker_supersedes_action_identity(
            terminal,
            action=action,
            mapping=mapping,
            text=text,
        )
    action_eval = _action_source_eval_id(action, mapping=mapping, text=text)
    terminal_eval = _terminal_source_eval_id(terminal, mapping=mapping, text=text)
    return action_eval is not None and terminal_eval is not None and action_eval != terminal_eval


def _terminal_typed_blocker_supersedes_action_identity(
    terminal: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    typed_blocker = mapping(terminal.get("typed_blocker"))
    if not typed_blocker:
        return False
    blocker_type = text(typed_blocker.get("blocker_type")) or text(typed_blocker.get("blocked_reason"))
    if blocker_type != "stage_packet_not_current_selected_dispatch":
        return False
    if text(typed_blocker.get("action_type")) != text(action.get("action_type")):
        return False
    fresh_current_identity = _terminal_fresh_current_control_identity(
        terminal,
        mapping=mapping,
        text=text,
    )
    typed_fp = (
        text(fresh_current_identity.get("work_unit_fingerprint"))
        or text(typed_blocker.get("work_unit_fingerprint"))
        or text(typed_blocker.get("action_fingerprint"))
    )
    terminal_top_fp = (
        text(terminal.get("work_unit_fingerprint"))
        or text(terminal.get("action_fingerprint"))
        or text(terminal.get("fingerprint"))
    )
    action_fp = _action_identity_fingerprint(action, mapping=mapping, text=text)
    return bool(typed_fp and action_fp and terminal_top_fp and terminal_top_fp == action_fp)


def _terminal_fresh_current_control_identity(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> dict[str, str]:
    typed_blocker = mapping(terminal.get("typed_blocker"))
    blocker_type = text(typed_blocker.get("blocker_type")) or text(typed_blocker.get("blocked_reason"))
    if blocker_type != "stage_packet_not_current_selected_dispatch":
        return {}
    domain_execution = mapping(terminal.get("domain_execution"))
    work_unit_id = text(domain_execution.get("fresh_current_control_work_unit_id"))
    work_unit_fingerprint = text(domain_execution.get("fresh_current_control_work_unit_fingerprint"))
    action_fingerprint = text(domain_execution.get("fresh_current_control_action_fingerprint"))
    return {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint or work_unit_fingerprint,
        }.items()
        if value is not None
    }


def _action_identity_fingerprint(
    action: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    source_refs = mapping(action.get("source_refs"))
    basis = mapping(action.get("owner_route_currentness_basis")) or mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    return (
        text(action.get("work_unit_fingerprint"))
        or text(action.get("action_fingerprint"))
        or text(action.get("fingerprint"))
        or text(basis.get("work_unit_fingerprint"))
        or text(basis.get("source_fingerprint"))
    )


def _terminal_identity_fingerprint(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    typed_blocker = mapping(terminal.get("typed_blocker"))
    fresh_current_identity = _terminal_fresh_current_control_identity(
        terminal,
        mapping=mapping,
        text=text,
    )
    next_forced_delta = mapping(terminal.get("next_forced_delta")) or mapping(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = mapping(next_forced_delta.get("owner_action"))
    semantic = mapping(terminal.get("terminal_closeout_semantic_completeness"))
    basis = mapping(terminal.get("owner_route_currentness_basis")) or mapping(
        semantic.get("owner_route_currentness_basis")
    )
    return (
        text(fresh_current_identity.get("work_unit_fingerprint"))
        or text(fresh_current_identity.get("action_fingerprint"))
        or text(typed_blocker.get("work_unit_fingerprint"))
        or text(typed_blocker.get("action_fingerprint"))
        or text(terminal.get("work_unit_fingerprint"))
        or text(terminal.get("action_fingerprint"))
        or text(terminal.get("fingerprint"))
        or text(paper_stage_log.get("work_unit_fingerprint"))
        or text(next_forced_delta.get("work_unit_fingerprint"))
        or text(owner_action.get("work_unit_fingerprint"))
        or text(basis.get("work_unit_fingerprint"))
        or text(basis.get("source_fingerprint"))
    )


def _terminal_source_eval_id(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    next_forced_delta = mapping(terminal.get("next_forced_delta")) or mapping(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = mapping(next_forced_delta.get("owner_action"))
    semantic = mapping(terminal.get("terminal_closeout_semantic_completeness"))
    basis = mapping(terminal.get("owner_route_currentness_basis")) or mapping(
        semantic.get("owner_route_currentness_basis")
    )
    return (
        text(terminal.get("source_eval_id"))
        or text(terminal.get("eval_id"))
        or text(paper_stage_log.get("source_eval_id"))
        or text(next_forced_delta.get("source_eval_id"))
        or text(owner_action.get("source_eval_id"))
        or text(basis.get("source_eval_id"))
    )


def _terminal_stage_blocker_reason(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str:
    typed_blocker = mapping(terminal.get("typed_blocker"))
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    paper_next_forced_delta = mapping(paper_stage_log.get("next_forced_delta"))
    paper_owner_action = mapping(paper_next_forced_delta.get("owner_action"))
    semantic = mapping(terminal.get("terminal_closeout_semantic_completeness"))
    for value in (
        terminal.get("blocked_reason"),
        terminal.get("typed_blocker_reason"),
        terminal.get("blocker_id"),
        terminal.get("blocker_type"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("reason"),
        semantic.get("typed_blocker"),
        paper_owner_action.get("reason"),
        paper_next_forced_delta.get("blocker_type"),
        paper_next_forced_delta.get("blocked_reason"),
        *_terminal_remaining_blockers(terminal, text=text),
        *_terminal_remaining_blockers(paper_stage_log, text=text),
    ):
        resolved = _structured_blocker_reason(value, mapping=mapping, text=text)
        if resolved is not None:
            return resolved
    if text(terminal.get("status")) == "repeat_suppressed" or text(terminal.get("outcome")) == "repeat_suppressed":
        return "anti_loop_budget_exhausted"
    return text(terminal.get("status")) or "terminal_closeout_observed"


def _terminal_stage_blocker_owner(
    terminal: Mapping[str, Any],
    *,
    blocker_reason: str,
    mapping: MappingReader,
    text: TextReader,
) -> str:
    typed_blocker = mapping(terminal.get("typed_blocker"))
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    paper_next_forced_delta = mapping(paper_stage_log.get("next_forced_delta"))
    paper_owner_action = mapping(paper_next_forced_delta.get("owner_action"))
    structured_blocker = _structured_blocker_mapping(
        typed_blocker,
        terminal.get("blocked_reason"),
        terminal.get("typed_blocker_reason"),
        terminal.get("blocker_id"),
        terminal.get("blocker_type"),
        typed_blocker.get("reason"),
        *_terminal_remaining_blockers(terminal, text=text),
        *_terminal_remaining_blockers(paper_stage_log, text=text),
        mapping=mapping,
        text=text,
    )
    explicit_owner = (
        text(typed_blocker.get("owner"))
        or text(typed_blocker.get("next_owner"))
        or text(structured_blocker.get("owner"))
        or text(structured_blocker.get("next_owner"))
        or text(paper_owner_action.get("next_owner"))
        or text(paper_owner_action.get("owner"))
        or text(terminal.get("owner"))
        or text(terminal.get("current_owner"))
    )
    if blocker_reason in OPL_RUNTIME_TERMINAL_BLOCKERS:
        return "one-person-lab"
    contract = owner_reason_contract(reason=blocker_reason, owner=explicit_owner)
    return (
        explicit_owner
        or text(contract.get("owner"))
        or "one-person-lab"
    )


def _structured_blocker_reason(
    value: object,
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    blocker = _structured_blocker_mapping(value, mapping=mapping, text=text)
    for key in ("blocker_id", "blocker_type", "blocked_reason", "reason"):
        resolved = text(blocker.get(key))
        if resolved is not None:
            return resolved
    return text(value)


def _structured_blocker_mapping(
    *values: object,
    mapping: MappingReader,
    text: TextReader,
) -> dict[str, Any]:
    for value in values:
        mapped = mapping(value)
        if mapped:
            return mapped
        parsed = _literal_mapping_from_prefixed_text(value, text=text)
        if parsed:
            return parsed
    return {}


def _literal_mapping_from_prefixed_text(
    value: object,
    *,
    text: TextReader,
) -> dict[str, Any]:
    raw = text(value)
    if raw is None:
        return {}
    stripped = raw.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidate = stripped
    elif stripped.startswith("blocked:{") and stripped.endswith("}"):
        candidate = stripped.removeprefix("blocked:")
    elif stripped.startswith("typed_blocker::{") and stripped.endswith("}"):
        candidate = stripped.removeprefix("typed_blocker::")
    else:
        return {}
    try:
        parsed = ast.literal_eval(candidate)
    except (SyntaxError, ValueError):
        return {}
    return dict(parsed) if isinstance(parsed, Mapping) else {}


def _terminal_remaining_blockers(
    terminal: Mapping[str, Any],
    *,
    text: TextReader,
) -> tuple[str, ...]:
    remaining = terminal.get("remaining_blockers")
    if isinstance(remaining, str):
        resolved = text(remaining)
        return (resolved,) if resolved is not None else ()
    if not isinstance(remaining, list | tuple):
        return ()
    return tuple(resolved for item in remaining if (resolved := text(item)) is not None)


def _action_source_eval_id(
    action: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
    currentness_basis: Mapping[str, Any] | None = None,
) -> str | None:
    source_refs = mapping(action.get("source_refs"))
    basis = (
        mapping(currentness_basis)
        or mapping(action.get("owner_route_currentness_basis"))
        or mapping(source_refs.get("owner_route_currentness_basis"))
    )
    return (
        text(action.get("source_eval_id"))
        or text(source_refs.get("source_eval_id"))
        or text(basis.get("source_eval_id"))
    )


def _consumption_source_eval_id(
    consumption: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    canonical = mapping(consumption.get("canonical_work_unit_identity"))
    basis = mapping(consumption.get("owner_route_currentness_basis"))
    return (
        text(canonical.get("source_eval_id"))
        or text(consumption.get("source_eval_id"))
        or text(consumption.get("eval_id"))
        or text(basis.get("source_eval_id"))
    )
