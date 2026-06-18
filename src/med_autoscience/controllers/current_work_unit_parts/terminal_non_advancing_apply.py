from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


MappingReader = Callable[[object], dict[str, Any]]
TextReader = Callable[[object], str | None]


NON_ADVANCING_APPLY_REASON = "fresh_readback_did_not_advance_same_aggregate"
NON_ADVANCING_TERMINAL_STATUSES = frozenset(
    {
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "executed",
    }
)
ADVANCING_PROGRESS_DELTA_CLASSIFICATIONS = frozenset(
    {
        "deliverable_progress",
        "paper_progress",
    }
)


def terminal_stage_non_advancing_apply(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    if not _terminal_stage_is_terminal_closeout(terminal, mapping=mapping, text=text):
        return False
    if not _terminal_declares_provider_completion_is_not_domain_completion(
        terminal,
        mapping=mapping,
        text=text,
    ) and _terminal_record_only_owner_receipt(terminal, mapping=mapping) is not True:
        return False
    return not _terminal_has_paper_or_deliverable_delta(terminal, mapping=mapping, text=text)


def terminal_non_advancing_apply_fields(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> dict[str, Any]:
    if not terminal_stage_non_advancing_apply(terminal, mapping=mapping, text=text):
        return {}
    owner_receipt_ref = _terminal_owner_receipt_ref(terminal, mapping=mapping, text=text)
    record_only = _terminal_record_only_owner_receipt(terminal, mapping=mapping) is True
    identity = terminal_non_advancing_apply_identity(terminal, mapping=mapping, text=text)
    return {
        key: value
        for key, value in {
            **identity,
            "blocked_reason": NON_ADVANCING_APPLY_REASON,
            "reason": NON_ADVANCING_APPLY_REASON,
            "non_advancing_apply": True,
            "provider_completion_is_domain_completion": False,
            "no_progress_signal": NON_ADVANCING_APPLY_REASON,
            "owner_receipt_ref": owner_receipt_ref,
            "record_only_surface": True if record_only else None,
        }.items()
        if value not in (None, "", [], {})
    }


def terminal_non_advancing_apply_identity(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> dict[str, Any]:
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    next_forced_delta = mapping(terminal.get("next_forced_delta")) or mapping(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = mapping(next_forced_delta.get("owner_action"))
    work_unit_id = (
        text(terminal.get("work_unit_id"))
        or text(terminal.get("stage_name"))
        or text(paper_stage_log.get("work_unit_id"))
        or text(next_forced_delta.get("work_unit_id"))
        or text(owner_action.get("work_unit_id"))
    )
    work_unit_fingerprint = (
        text(terminal.get("work_unit_fingerprint"))
        or text(terminal.get("action_fingerprint"))
        or text(paper_stage_log.get("work_unit_fingerprint"))
        or text(paper_stage_log.get("action_fingerprint"))
        or text(next_forced_delta.get("work_unit_fingerprint"))
        or text(owner_action.get("work_unit_fingerprint"))
    )
    action_fingerprint = (
        text(terminal.get("action_fingerprint"))
        or text(terminal.get("work_unit_fingerprint"))
        or text(paper_stage_log.get("action_fingerprint"))
        or text(paper_stage_log.get("work_unit_fingerprint"))
        or text(next_forced_delta.get("action_fingerprint"))
        or text(next_forced_delta.get("work_unit_fingerprint"))
        or text(owner_action.get("action_fingerprint"))
        or text(owner_action.get("work_unit_fingerprint"))
    )
    return {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint or work_unit_fingerprint,
        }.items()
        if value not in (None, "", [], {})
    }


def _terminal_stage_is_terminal_closeout(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    status = text(terminal.get("status")) or text(paper_stage_log.get("status"))
    outcome = text(terminal.get("outcome")) or text(paper_stage_log.get("outcome"))
    return (
        status in NON_ADVANCING_TERMINAL_STATUSES
        or (outcome is not None and outcome in NON_ADVANCING_TERMINAL_STATUSES)
        or (outcome is not None and "closed_with_existing_mas_owner_receipt_ref" in outcome)
    )


def _terminal_declares_provider_completion_is_not_domain_completion(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    if terminal.get("provider_completion_is_domain_completion") is False:
        return True
    if paper_stage_log.get("provider_completion_is_domain_completion") is False:
        return True
    values = [
        terminal.get("outcome"),
        terminal.get("blocked_reason"),
        terminal.get("blocker_type"),
        terminal.get("provider_completion_is_domain_completion"),
        paper_stage_log.get("outcome"),
        paper_stage_log.get("blocked_reason"),
        paper_stage_log.get("blocker_type"),
        paper_stage_log.get("provider_completion_is_domain_completion"),
        *_terminal_remaining_blockers(terminal, text=text),
        *_terminal_remaining_blockers(paper_stage_log, text=text),
    ]
    return any(
        (resolved := text(value)) is not None
        and "provider_completion_is_not_domain_completion" in resolved
        for value in values
    )


def _terminal_record_only_owner_receipt(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
) -> bool:
    owner_receipt = mapping(terminal.get("owner_receipt"))
    return owner_receipt.get("record_only_surface") is True or terminal.get("record_only_surface") is True


def _terminal_owner_receipt_ref(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> str | None:
    owner_receipt = mapping(terminal.get("owner_receipt"))
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    return (
        text(terminal.get("owner_receipt_ref"))
        or text(owner_receipt.get("owner_receipt_ref"))
        or text(paper_stage_log.get("owner_receipt_ref"))
    )


def _terminal_has_paper_or_deliverable_delta(
    terminal: Mapping[str, Any],
    *,
    mapping: MappingReader,
    text: TextReader,
) -> bool:
    paper_stage_log = mapping(terminal.get("paper_stage_log"))
    artifact_delta = mapping(terminal.get("artifact_delta"))
    for value in (
        terminal.get("changed_paper_surfaces"),
        paper_stage_log.get("changed_paper_surfaces"),
        artifact_delta.get("changed_paper_surfaces"),
    ):
        if _non_empty_sequence(value, text=text):
            return True
    for value in (
        terminal.get("paper_progress_delta"),
        paper_stage_log.get("paper_progress_delta"),
        terminal.get("deliverable_progress_delta"),
        paper_stage_log.get("deliverable_progress_delta"),
    ):
        if _delta_count(mapping(value)) > 0:
            return True
    classification = text(terminal.get("progress_delta_classification")) or text(
        paper_stage_log.get("progress_delta_classification")
    )
    return classification in ADVANCING_PROGRESS_DELTA_CLASSIFICATIONS


def _non_empty_sequence(value: object, *, text: TextReader) -> bool:
    if isinstance(value, str):
        return text(value) is not None
    if not isinstance(value, list | tuple):
        return False
    return any(text(item) is not None for item in value)


def _delta_count(delta: Mapping[str, Any]) -> int:
    value = delta.get("count")
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


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


__all__ = [
    "NON_ADVANCING_APPLY_REASON",
    "terminal_non_advancing_apply_fields",
    "terminal_non_advancing_apply_identity",
    "terminal_stage_non_advancing_apply",
]
