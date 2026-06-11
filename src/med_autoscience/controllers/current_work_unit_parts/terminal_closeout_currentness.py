from __future__ import annotations

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
    resolved_work_unit_id = work_unit_id(action_payload.get("work_unit_id")) or work_unit_id(
        action_payload.get("next_work_unit")
    )
    currentness_basis = mapping(action_payload.get("owner_route_currentness_basis"))
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    resolved_work_unit_fingerprint = work_unit_fingerprint(action_payload, currentness_basis=currentness_basis)
    source_ref = text(terminal.get("source_path")) or text(terminal.get("record_path"))
    return {
        key: value
        for key, value in {
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
            "action_fingerprint": action_fingerprint(action_payload, currentness_basis=currentness_basis),
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
    if expected_action is None:
        return False
    if terminal_action is not None and terminal_action != expected_action:
        return False
    expected_work_unit = work_unit_id(action.get("work_unit_id")) or work_unit_id(action.get("next_work_unit"))
    terminal_work_units = {
        item
        for value in (
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
        resolved = text(value)
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
    explicit_owner = (
        text(typed_blocker.get("owner"))
        or text(typed_blocker.get("next_owner"))
        or text(paper_owner_action.get("next_owner"))
        or text(paper_owner_action.get("owner"))
        or text(terminal.get("owner"))
        or text(terminal.get("current_owner"))
    )
    contract = owner_reason_contract(reason=blocker_reason, owner=explicit_owner)
    return (
        explicit_owner
        or text(contract.get("owner"))
        or "one-person-lab"
    )


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
