from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


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
    terminal = _latest_terminal_stage(progress, mapping=mapping)
    if not terminal or not _terminal_stage_blocks_action(
        terminal,
        action=action_payload,
        mapping=mapping,
        text=text,
        action_type=action_type,
        work_unit_id=work_unit_id,
    ):
        return None
    blocker_type = _terminal_stage_blocker_reason(terminal, mapping=mapping, text=text)
    resolved_work_unit_id = work_unit_id(action_payload.get("work_unit_id")) or work_unit_id(
        action_payload.get("next_work_unit")
    )
    currentness_basis = mapping(action_payload.get("owner_route_currentness_basis"))
    resolved_work_unit_fingerprint = work_unit_fingerprint(action_payload, currentness_basis=currentness_basis)
    source_ref = text(terminal.get("source_path")) or text(terminal.get("record_path"))
    return {
        key: value
        for key, value in {
            "blocker_type": blocker_type,
            "blocker_id": blocker_type,
            "blocked_reason": blocker_type,
            "owner": _terminal_stage_blocker_owner(terminal, mapping=mapping, text=text),
            "action_type": action_type(action_payload),
            "work_unit_id": resolved_work_unit_id,
            "work_unit_fingerprint": resolved_work_unit_fingerprint,
            "action_fingerprint": action_fingerprint(action_payload, currentness_basis=currentness_basis),
            "source_ref": source_ref,
            "acceptance_refs": text_items(terminal.get("closeout_refs"))
            + text_items(terminal.get("evidence_refs"))
            + ([source_ref] if source_ref is not None else []),
            "terminal_closeout_status": text(terminal.get("status")),
            "terminal_closeout_outcome": text(terminal.get("outcome")),
            "progress_delta_classification": text(terminal.get("progress_delta_classification")),
        }.items()
        if value not in (None, "", [], {})
    }


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


def _latest_terminal_stage(
    progress: Mapping[str, Any],
    *,
    mapping: MappingReader,
) -> dict[str, Any]:
    progress_first = mapping(progress.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        progress.get("latest_terminal_stage"),
        progress.get("latest_terminal_stage_log"),
    ):
        terminal = mapping(value)
        if terminal:
            return terminal
    return {}


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
    mapping: MappingReader,
    text: TextReader,
) -> str:
    typed_blocker = mapping(terminal.get("typed_blocker"))
    return (
        text(typed_blocker.get("owner"))
        or text(terminal.get("owner"))
        or text(terminal.get("current_owner"))
        or "one-person-lab"
    )


def _action_source_eval_id(
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

