from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any


OWNER_PICKUP_OVERDUE_HOURS = 2
DEVELOPER_SUPERVISOR_ATTENTION_HOURS = 6


def decorate_action_queue_slo(
    *,
    studies: list[dict[str, Any]],
    previous_payload: Mapping[str, Any] | None,
    generated_at: str,
) -> dict[str, Any]:
    prior_by_fingerprint = _prior_actions_by_fingerprint(previous_payload)
    repeat_fingerprints: dict[str, dict[str, Any]] = {}
    totals = {
        "owner_pickup_overdue_count": 0,
        "developer_supervisor_attention_required_count": 0,
        "max_queue_age_hours": 0.0,
    }
    for study in studies:
        _decorate_study_actions(
            study=study,
            prior_by_fingerprint=prior_by_fingerprint,
            repeat_fingerprints=repeat_fingerprints,
            totals=totals,
            generated_at=generated_at,
        )
    return {
        **totals,
        "repeat_fingerprints": list(repeat_fingerprints.values()),
    }


def _decorate_study_actions(
    *,
    study: dict[str, Any],
    prior_by_fingerprint: Mapping[str, Mapping[str, Any]],
    repeat_fingerprints: dict[str, dict[str, Any]],
    totals: dict[str, Any],
    generated_at: str,
) -> None:
    study_counts = {
        "max_queue_age_hours": 0.0,
        "owner_pickup_overdue_count": 0,
        "developer_supervisor_attention_required_count": 0,
    }
    for action in study.get("action_queue") or []:
        if isinstance(action, dict):
            _decorate_action_slo(
                action=action,
                study=study,
                prior_by_fingerprint=prior_by_fingerprint,
                repeat_fingerprints=repeat_fingerprints,
                study_counts=study_counts,
                totals=totals,
                generated_at=generated_at,
            )
    study["queue_slo"] = dict(study_counts)
    study["owner_pickup_overdue"] = study_counts["owner_pickup_overdue_count"] > 0
    study["developer_supervisor_attention_required"] = (
        study_counts["developer_supervisor_attention_required_count"] > 0
    )


def _decorate_action_slo(
    *,
    action: dict[str, Any],
    study: Mapping[str, Any],
    prior_by_fingerprint: Mapping[str, Mapping[str, Any]],
    repeat_fingerprints: dict[str, dict[str, Any]],
    study_counts: dict[str, Any],
    totals: dict[str, Any],
    generated_at: str,
) -> None:
    fingerprint = _action_fingerprint(action)
    prior = prior_by_fingerprint.get(fingerprint, {})
    timing = _queue_timing(action=action, prior=prior, generated_at=generated_at)
    owner_pickup_overdue = timing["owner_duration_hours"] >= OWNER_PICKUP_OVERDUE_HOURS
    attention_required = timing["unconsumed_duration_hours"] >= DEVELOPER_SUPERVISOR_ATTENTION_HOURS
    action["fingerprint"] = fingerprint
    action["queued_first_seen_at"] = timing["queued_first_seen_at"]
    action["queue_age_hours"] = timing["queue_age_hours"]
    action["repeat_fingerprint"] = _repeat_fingerprint(
        fingerprint=fingerprint,
        prior=prior,
        queued_first_seen_at=timing["queued_first_seen_at"],
        queue_age_hours=timing["queue_age_hours"],
        generated_at=generated_at,
    )
    action["owner_pickup"] = _owner_pickup_payload(
        action=action,
        study=study,
        first_seen_at=timing["owner_first_seen_at"],
        duration_hours=timing["owner_duration_hours"],
        overdue=owner_pickup_overdue,
    )
    action["consumption"] = _consumption_payload(
        first_seen_at=timing["consumption_first_seen_at"],
        duration_hours=timing["unconsumed_duration_hours"],
        attention_required=attention_required,
    )
    _record_slo_counts(
        action=action,
        repeat_fingerprints=repeat_fingerprints,
        study_counts=study_counts,
        totals=totals,
        owner_pickup_overdue=owner_pickup_overdue,
        attention_required=attention_required,
    )


def _queue_timing(
    *,
    action: Mapping[str, Any],
    prior: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    queued_first_seen_at = (
        _text(prior.get("queued_first_seen_at"))
        or _text(action.get("queued_first_seen_at"))
        or generated_at
    )
    owner_first_seen_at = _prior_first_seen_at(prior, "owner_pickup") or queued_first_seen_at
    consumption_first_seen_at = _prior_first_seen_at(prior, "consumption") or queued_first_seen_at
    return {
        "queued_first_seen_at": queued_first_seen_at,
        "owner_first_seen_at": owner_first_seen_at,
        "consumption_first_seen_at": consumption_first_seen_at,
        "queue_age_hours": _duration_hours(start_at=queued_first_seen_at, end_at=generated_at),
        "owner_duration_hours": _duration_hours(start_at=owner_first_seen_at, end_at=generated_at),
        "unconsumed_duration_hours": _duration_hours(start_at=consumption_first_seen_at, end_at=generated_at),
    }


def _repeat_fingerprint(
    *,
    fingerprint: str,
    prior: Mapping[str, Any],
    queued_first_seen_at: str,
    queue_age_hours: float,
    generated_at: str,
) -> dict[str, Any]:
    prior_repeat = _mapping(prior.get("repeat_fingerprint"))
    prior_count = prior_repeat.get("consecutive_scan_count", 1 if prior else 0)
    try:
        repeat_count = int(prior_count) + 1
    except (TypeError, ValueError):
        repeat_count = 1
    return {
        "fingerprint": fingerprint,
        "consecutive_scan_count": repeat_count,
        "first_seen_at": queued_first_seen_at,
        "last_seen_at": generated_at,
        "duration_hours": queue_age_hours,
    }


def _owner_pickup_payload(
    *,
    action: Mapping[str, Any],
    study: Mapping[str, Any],
    first_seen_at: str,
    duration_hours: float,
    overdue: bool,
) -> dict[str, Any]:
    return {
        "state": "overdue" if overdue else "pending",
        "owner": _owner_from_action(action) or _text(study.get("next_owner")),
        "first_seen_at": first_seen_at,
        "overdue_after_hours": OWNER_PICKUP_OVERDUE_HOURS,
        "duration_hours": duration_hours,
        "pickup_overdue": overdue,
    }


def _consumption_payload(
    *,
    first_seen_at: str,
    duration_hours: float,
    attention_required: bool,
) -> dict[str, Any]:
    return {
        "state": "attention_required" if attention_required else "unconsumed",
        "first_seen_at": first_seen_at,
        "unconsumed_duration_hours": duration_hours,
        "attention_required_after_hours": DEVELOPER_SUPERVISOR_ATTENTION_HOURS,
        "developer_supervisor_attention_required": attention_required,
    }


def _record_slo_counts(
    *,
    action: Mapping[str, Any],
    repeat_fingerprints: dict[str, dict[str, Any]],
    study_counts: dict[str, Any],
    totals: dict[str, Any],
    owner_pickup_overdue: bool,
    attention_required: bool,
) -> None:
    repeat_payload = _mapping(action.get("repeat_fingerprint"))
    repeat_fingerprints[str(repeat_payload.get("fingerprint") or "")] = dict(repeat_payload)
    queue_age_hours = float(action.get("queue_age_hours") or 0.0)
    study_counts["max_queue_age_hours"] = max(study_counts["max_queue_age_hours"], queue_age_hours)
    totals["max_queue_age_hours"] = max(totals["max_queue_age_hours"], queue_age_hours)
    if owner_pickup_overdue:
        totals["owner_pickup_overdue_count"] += 1
        study_counts["owner_pickup_overdue_count"] += 1
    if attention_required:
        totals["developer_supervisor_attention_required_count"] += 1
        study_counts["developer_supervisor_attention_required_count"] += 1


def _action_fingerprint(action: Mapping[str, Any]) -> str:
    explicit = _text(action.get("fingerprint"))
    if explicit is not None:
        return explicit
    return "::".join(
        item
        for item in (
            _text(action.get("action_type")) or "unknown_action",
            _text(action.get("reason")),
        )
        if item
    )


def _prior_actions_by_fingerprint(previous_payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    prior: dict[str, dict[str, Any]] = {}
    if previous_payload is None:
        return prior
    for action in previous_payload.get("action_queue") or []:
        if isinstance(action, Mapping):
            prior[_text(action.get("fingerprint")) or _action_fingerprint(action)] = dict(action)
    for study in previous_payload.get("studies") or []:
        if isinstance(study, Mapping):
            _add_study_prior_actions(study=study, prior=prior)
    return prior


def _add_study_prior_actions(*, study: Mapping[str, Any], prior: dict[str, dict[str, Any]]) -> None:
    for action in study.get("action_queue") or []:
        if isinstance(action, Mapping):
            prior.setdefault(_text(action.get("fingerprint")) or _action_fingerprint(action), dict(action))


def _prior_first_seen_at(prior: Mapping[str, Any], key: str) -> str | None:
    nested = _mapping(prior.get(key))
    return (
        _text(nested.get("first_seen_at"))
        or _text(prior.get(f"{key}_first_seen_at"))
        or _text(prior.get("queued_first_seen_at"))
    )


def _owner_from_action(action: Mapping[str, Any]) -> str | None:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _text(handoff_packet.get("next_executable_owner"))
    )


def _duration_hours(*, start_at: object, end_at: object) -> float:
    start = _parse_utc_datetime(start_at)
    end = _parse_utc_datetime(end_at)
    if start is None or end is None or end < start:
        return 0.0
    return round((end - start).total_seconds() / 3600, 3)


def _parse_utc_datetime(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
