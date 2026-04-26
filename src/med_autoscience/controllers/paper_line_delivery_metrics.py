from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


_QUALITY_CLEAR_STATUSES = frozenset({"clear", "passed", "ready", "submission_ready"})
_QUALITY_BLOCKED_STATUSES = frozenset({"blocked", "failed", "needs_repair"})
_RUNTIME_BLOCKED_STATUSES = frozenset({"recovering", "degraded", "escalated", "inactive", "blocked"})
_RUNTIME_RECOVERED_STATUSES = frozenset({"live", "recovered"})
_FAST_LANE_SUCCESS_STATUSES = frozenset({"success", "succeeded", "executed", "skipped_duplicate_eval"})
_FAST_LANE_FAILURE_STATUSES = frozenset({"failed", "error", "blocked"})
_COARSE_SECONDS = 900


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_time(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp(payload: Mapping[str, Any]) -> datetime | None:
    for key in ("at", "recorded_at", "generated_at", "emitted_at", "created_at", "updated_at", "finished_at"):
        if (parsed := _parse_time(payload.get(key))) is not None:
            return parsed
    return None


def _duration_seconds(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return max(0, int((end - start).total_seconds()))


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 3)


def _has_human_admin_marker(text: str) -> bool:
    lowered = text.lower()
    if "伦理" in text or "作者" in text:
        return True
    tokens = {token for token in lowered.replace("-", "_").replace("/", "_").split("_") if token}
    return bool(tokens & {"author", "authors", "affiliation", "affiliations", "metadata", "human", "admin"})


def _quality_status(event: Mapping[str, Any]) -> str | None:
    status = _text(event.get("status"))
    if status in _QUALITY_CLEAR_STATUSES or event.get("allow_write") is True:
        return "clear"
    if status in _QUALITY_BLOCKED_STATUSES:
        return "blocked"
    if _list(event.get("blockers")) or _list(event.get("gaps")):
        return "blocked"
    return status


def _first_at(events: Sequence[Mapping[str, Any]], event_type: str) -> datetime | None:
    timestamps = [_timestamp(event) for event in events if _text(event.get("event_type")) == event_type]
    candidates = [timestamp for timestamp in timestamps if timestamp is not None]
    return min(candidates) if candidates else None


def _first_at_or_after(
    events: Sequence[Mapping[str, Any]],
    event_type: str,
    *,
    after: datetime | None,
) -> datetime | None:
    timestamps = [
        timestamp
        for event in events
        if _text(event.get("event_type")) == event_type
        if (timestamp := _timestamp(event)) is not None and (after is None or timestamp >= after)
    ]
    return min(timestamps) if timestamps else None


def _latest_at_or_before(
    events: Sequence[Mapping[str, Any]],
    event_type: str,
    *,
    before: datetime | None,
) -> datetime | None:
    timestamps = [
        timestamp
        for event in events
        if _text(event.get("event_type")) == event_type
        if (timestamp := _timestamp(event)) is not None and (before is None or timestamp <= before)
    ]
    return max(timestamps) if timestamps else None


def normalize_trace_identity(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    raw_identity = _mapping(profile_payload.get("trace_identity"))
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    next_work_unit = _mapping(gate_summary.get("next_work_unit"))
    sli_summary = _mapping(profile_payload.get("sli_summary"))
    study_id = _text(raw_identity.get("study_id")) or _text(profile_payload.get("study_id"))
    quest_id = _text(raw_identity.get("quest_id")) or _text(profile_payload.get("quest_id"))
    active_run_id = _text(raw_identity.get("active_run_id"))
    run_id = active_run_id or _text(raw_identity.get("run_id"))
    work_unit_id = (
        _text(raw_identity.get("work_unit_id"))
        or _text(next_work_unit.get("unit_id"))
        or _text(sli_summary.get("next_work_unit_id"))
    )
    scope_parts = [
        ("study", study_id),
        ("quest", quest_id),
        ("run", run_id),
        ("work_unit", work_unit_id),
    ]
    trace_scope = "|".join(f"{key}:{value}" for key, value in scope_parts if value is not None)
    trace_id = "paper-line::" + hashlib.sha256(trace_scope.encode("utf-8")).hexdigest()[:16]
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "active_run_id": active_run_id,
        "run_id": run_id,
        "work_unit_id": work_unit_id,
        "trace_scope": trace_scope,
        "trace_id": trace_id,
    }


def _manual_gate_count(events: Sequence[Mapping[str, Any]], blockers: Sequence[str]) -> int:
    explicit_gates = sum(1 for event in events if _text(event.get("event_type")) == "manual_gate")
    blocker_gates = sum(1 for blocker in blockers if _has_human_admin_marker(blocker))
    return explicit_gates + blocker_gates


def _runtime_recovery_durations(events: Sequence[Mapping[str, Any]]) -> list[int]:
    durations: list[int] = []
    blocked_at: datetime | None = None
    for event in sorted(events, key=lambda item: _timestamp(item) or datetime.max.replace(tzinfo=timezone.utc)):
        if _text(event.get("event_type")) != "runtime_supervision":
            continue
        status = _text(event.get("status"))
        timestamp = _timestamp(event)
        if timestamp is None:
            continue
        if status in _RUNTIME_BLOCKED_STATUSES:
            blocked_at = timestamp
        elif status in _RUNTIME_RECOVERED_STATUSES and blocked_at is not None:
            durations.append(max(0, int((timestamp - blocked_at).total_seconds())))
            blocked_at = None
    return durations


def _quality_reopen_rate(events: Sequence[Mapping[str, Any]]) -> float | None:
    clear_count = 0
    reopen_count = 0
    has_closed = False
    for event in sorted(events, key=lambda item: _timestamp(item) or datetime.max.replace(tzinfo=timezone.utc)):
        if _text(event.get("event_type")) != "quality_gate":
            continue
        status = _quality_status(event)
        if status == "clear":
            clear_count += 1
            has_closed = True
        elif status == "blocked" and has_closed:
            reopen_count += 1
            has_closed = False
    return _ratio(reopen_count, clear_count)


def _fast_lane_success_rate(events: Sequence[Mapping[str, Any]]) -> float | None:
    total = 0
    success = 0
    for event in events:
        if _text(event.get("event_type")) != "fast_lane":
            continue
        status = _text(event.get("status"))
        ok = event.get("ok")
        if ok is True or status in _FAST_LANE_SUCCESS_STATUSES:
            total += 1
            success += 1
        elif ok is False or status in _FAST_LANE_FAILURE_STATUSES:
            total += 1
    return _ratio(success, total)


def _summary(values: Sequence[int]) -> dict[str, int | None]:
    return {
        "count": len(values),
        "min_seconds": min(values) if values else None,
        "max_seconds": max(values) if values else None,
    }


def _blocker_class(gate_summary: Mapping[str, Any]) -> str:
    blockers = [
        blocker
        for item in _list(gate_summary.get("current_blockers"))
        if (blocker := _text(item)) is not None
    ]
    if gate_summary.get("actionability_status") == "blocked_by_non_actionable_gate":
        return "non_actionable_gate"
    if any(_has_human_admin_marker(blocker) for blocker in blockers):
        return "human_admin_missing"
    if any("claim" in blocker or "evidence" in blocker for blocker in blockers):
        return "claim_evidence"
    delivery_markers = ("submission", "package", "delivery", "current_package", "bundle")
    if blockers and all(any(marker in blocker for marker in delivery_markers) for blocker in blockers):
        return "delivery_only"
    return "delivery_only"


def _coarse_interval(samples: Sequence[int]) -> tuple[int, int]:
    lower = max(0, (min(samples) // _COARSE_SECONDS) * _COARSE_SECONDS)
    upper = ((max(samples) + _COARSE_SECONDS - 1) // _COARSE_SECONDS) * _COARSE_SECONDS
    if upper <= lower:
        upper = lower + _COARSE_SECONDS
    return lower, upper


def _eta_interval(
    *,
    blocker_class: str,
    lead_times: Mapping[str, int | None],
    recovery_durations: Sequence[int],
) -> dict[str, Any]:
    samples_by_class = {
        "claim_evidence": ("draft_to_quality_close_seconds",),
        "delivery_only": ("quality_close_to_package_seconds",),
        "runtime_recovering": ("blocked_to_recovered_seconds",),
    }
    if blocker_class in {"human_admin_missing", "non_actionable_gate"}:
        return {
            "classification": blocker_class,
            "min_seconds": None,
            "max_seconds": None,
            "basis": {
                "blocker_type": blocker_class,
                "observed_duration_keys": [],
                "sample_count": 0,
                "interval_source": "blocked_gate_requires_external_closure",
            },
        }
    duration_keys = list(samples_by_class.get(blocker_class, ("quality_close_to_package_seconds",)))
    samples = [
        int(lead_times[key])
        for key in duration_keys
        if isinstance(lead_times.get(key), int) and int(lead_times[key]) >= 0
    ]
    if blocker_class == "runtime_recovering":
        samples.extend(recovery_durations)
    if samples:
        lower, upper = _coarse_interval(samples)
        source = "observed_stage_duration"
    else:
        priors = {
            "claim_evidence": (7200, 21600),
            "delivery_only": (1800, 7200),
            "runtime_recovering": (1800, 5400),
        }
        lower, upper = priors.get(blocker_class, priors["delivery_only"])
        source = "blocker_type_prior"
    return {
        "classification": blocker_class,
        "min_seconds": lower,
        "max_seconds": upper,
        "basis": {
            "blocker_type": blocker_class,
            "observed_duration_keys": duration_keys if samples else [],
            "sample_count": len(samples),
            "interval_source": source,
        },
    }


def build_paper_line_delivery_metrics(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    events = [event for event in _list(profile_payload.get("paper_line_events")) if isinstance(event, Mapping)]
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    blockers = [
        blocker
        for item in _list(gate_summary.get("current_blockers"))
        if (blocker := _text(item)) is not None
    ]
    intake_at = _first_at(events, "task_intake")
    first_draft_at = _first_at_or_after(events, "first_draft", after=intake_at)
    quality_close_at = _first_at_or_after(
        [event for event in events if _quality_status(event) == "clear"],
        "quality_gate",
        after=first_draft_at,
    )
    package_at = _first_at_or_after(events, "package_refresh", after=quality_close_at)
    final_quality_close_at = _latest_at_or_before(
        [event for event in events if _quality_status(event) == "clear"],
        "quality_gate",
        before=package_at,
    ) or quality_close_at
    lead_times = {
        "intake_to_first_draft_seconds": _duration_seconds(intake_at, first_draft_at),
        "draft_to_quality_close_seconds": _duration_seconds(first_draft_at, quality_close_at),
        "quality_close_to_package_seconds": _duration_seconds(final_quality_close_at, package_at),
    }
    recovery_durations = _runtime_recovery_durations(events)
    blocker_class = _blocker_class(gate_summary)
    return {
        "surface": "paper_line_delivery_metrics",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "trace_identity": normalize_trace_identity(profile_payload),
        "event_count": len(events),
        "delivery_dora_metrics": {
            "lead_times": lead_times,
            "recovery": {"blocked_to_recovered_seconds": _summary(recovery_durations)},
            "manual_gate_count": _manual_gate_count(events, blockers),
            "quality_reopen_rate": _quality_reopen_rate(events),
            "fast_lane_success_rate": _fast_lane_success_rate(events),
        },
        "eta_interval": _eta_interval(
            blocker_class=blocker_class,
            lead_times=lead_times,
            recovery_durations=recovery_durations,
        ),
    }


def _event_identity(payload: Mapping[str, Any]) -> dict[str, str]:
    identity: dict[str, str] = {}
    for key in ("active_run_id", "run_id", "work_unit_id", "work_unit_dispatch_key", "work_unit_fingerprint"):
        if (value := _text(payload.get(key))) is not None:
            identity[key] = value
    next_work_unit = _mapping(payload.get("next_work_unit"))
    if "work_unit_id" not in identity and (unit_id := _text(next_work_unit.get("unit_id"))) is not None:
        identity["work_unit_id"] = unit_id
    return identity


def _event_record(event_type: str, at: datetime | str | None, **values: Any) -> dict[str, Any] | None:
    parsed_at = _parse_time(at) if isinstance(at, str) else at
    at_text = _iso(parsed_at)
    if at_text is None:
        return None
    return {"event_type": event_type, "at": at_text, **{key: value for key, value in values.items() if value is not None}}


def _quality_event_from_payload(payload: Mapping[str, Any], at: datetime | None) -> dict[str, Any] | None:
    blockers = [
        blocker
        for item in [*_list(payload.get("blockers")), *_list(payload.get("medical_publication_surface_blockers"))]
        if (blocker := _text(item)) is not None
    ]
    status = "clear" if _quality_status({"status": payload.get("status"), "allow_write": payload.get("allow_write")}) == "clear" else "blocked" if blockers else _text(payload.get("status"))
    return _event_record("quality_gate", at, status=status, blockers=blockers)


def events_from_cycle_profile(
    *,
    ordered_events: Iterable[object],
    study_root: Path,
    publication_eval_latest: Mapping[str, Any] | None,
    publishability_gate_latest: Mapping[str, Any] | None,
    package_currentness: Mapping[str, Any],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for event in ordered_events:
        category = _text(getattr(event, "category", None))
        payload = _mapping(getattr(event, "payload", None))
        timestamp = getattr(event, "timestamp", None)
        if not isinstance(timestamp, datetime):
            continue
        if category == "task_intake":
            record = _event_record("task_intake", timestamp, **_event_identity(payload))
        elif category == "runtime_supervision":
            health = _text(payload.get("health_status"))
            status = "recovered" if health in _RUNTIME_RECOVERED_STATUSES else "blocked" if health in _RUNTIME_BLOCKED_STATUSES else health
            record = _event_record("runtime_supervision", timestamp, status=status, **_event_identity(payload))
        elif category in {"publication_eval", "publishability_gate"}:
            record = _quality_event_from_payload(payload, timestamp)
        elif category in {"gate_clearing_batch", "quality_repair_batch"}:
            status = "success" if payload.get("ok") is True or _text(payload.get("status")) == "executed" else "failed"
            record = _event_record("fast_lane", timestamp, status=status, ok=payload.get("ok"), **_event_identity(payload))
        else:
            record = None
        if record is not None:
            records.append(record)
    for latest_payload in (publication_eval_latest, publishability_gate_latest):
        if isinstance(latest_payload, Mapping):
            record = _quality_event_from_payload(latest_payload, _timestamp(latest_payload))
            if record is not None:
                records.append(record)
    for candidate in ("paper/draft.md", "paper/manuscript.md", "paper/build/review_manuscript.md"):
        path = Path(study_root) / candidate
        if path.is_file():
            records.append(
                {
                    "event_type": "first_draft",
                    "at": _iso(datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)),
                    "source_path": str(path.resolve()),
                }
            )
            break
    package_at = _parse_time(package_currentness.get("current_package_latest_mtime"))
    if package_at is not None:
        records.append({"event_type": "package_refresh", "at": _iso(package_at)})
    return sorted(records, key=lambda item: item.get("at") or "")


def trace_identity_from_events(
    *,
    study_id: str | None,
    quest_id: str | None,
    events: Sequence[Mapping[str, Any]],
    gate_blocker_summary: Mapping[str, Any],
    sli_summary: Mapping[str, Any],
) -> dict[str, Any]:
    identity: dict[str, Any] = {"study_id": study_id, "quest_id": quest_id}
    for event in reversed(events):
        for key in ("active_run_id", "run_id", "work_unit_id"):
            if identity.get(key) is None and (value := _text(event.get(key))) is not None:
                identity[key] = value
    return normalize_trace_identity(
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "trace_identity": identity,
            "gate_blocker_summary": gate_blocker_summary,
            "sli_summary": sli_summary,
        }
    )


def json_dumps_stable(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
