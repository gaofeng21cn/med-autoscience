from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any


EventPayloadReader = Callable[[Mapping[str, Any] | None], dict[str, Any]]
ActiveRunReader = Callable[[Mapping[str, Any]], str | None]


def event_sequence(event: Mapping[str, Any]) -> int | None:
    value = event.get("sequence")
    return value if isinstance(value, int) else None


def current_run_epoch_start_sequence(
    events: list[dict[str, Any]],
    active_run_id: str | None,
    *,
    event_payload: EventPayloadReader,
    active_run_from_payload: ActiveRunReader,
) -> int | None:
    if active_run_id is None:
        return None
    for event in events:
        if active_run_from_payload(event_payload(event)) != active_run_id:
            continue
        sequence = event_sequence(event)
        if sequence is not None:
            return sequence
    return None


def latest_release_sequence(events: list[dict[str, Any]]) -> int | None:
    for event in reversed(events):
        if str(event.get("event_type") or "") != "attempt_released":
            continue
        sequence = event_sequence(event)
        if sequence is not None:
            return sequence
    return None


def event_belongs_to_run_epoch(
    event: Mapping[str, Any],
    *,
    active_run_id: str | None,
    epoch_start_sequence: int | None,
    event_payload: EventPayloadReader,
    active_run_from_payload: ActiveRunReader,
) -> bool:
    if active_run_id is None:
        return True
    event_run_id = active_run_from_payload(event_payload(event))
    if event_run_id is not None:
        return event_run_id == active_run_id
    sequence = event_sequence(event)
    return (
        epoch_start_sequence is not None
        and sequence is not None
        and sequence >= epoch_start_sequence
    )


def events_for_budget(
    events: list[dict[str, Any]],
    event_types: Iterable[str],
    *,
    active_run_id: str | None,
    event_payload: EventPayloadReader,
    active_run_from_payload: ActiveRunReader,
) -> list[dict[str, Any]]:
    selected = [event for event in events if str(event.get("event_type") or "") in event_types]
    if active_run_id is None:
        release_sequence = latest_release_sequence(events)
        if release_sequence is None:
            return selected
        return [
            event
            for event in selected
            if (sequence := event_sequence(event)) is not None and sequence > release_sequence
        ]
    epoch_start_sequence = current_run_epoch_start_sequence(
        events,
        active_run_id,
        event_payload=event_payload,
        active_run_from_payload=active_run_from_payload,
    )
    return [
        event
        for event in selected
        if event_belongs_to_run_epoch(
            event,
            active_run_id=active_run_id,
            epoch_start_sequence=epoch_start_sequence,
            event_payload=event_payload,
            active_run_from_payload=active_run_from_payload,
        )
    ]
