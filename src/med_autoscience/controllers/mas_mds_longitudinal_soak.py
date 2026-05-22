from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SURFACE = "mas_mds_longitudinal_soak_proof"
READ_MODEL = "mas_mds_longitudinal_soak_read_model"
DEFAULT_LATENCY_THRESHOLD_MINUTES = 120

REQUIRED_EVENTS = (
    "pre_submission",
    "revision",
    "reopen_same_paper_line",
    "route_change_line_switch",
    "final_rebuild",
    "draft_authorization_to_submission_package_rebuild_latency",
    "failure_recovery_replay_evidence",
)

PROHIBITED_WRITES = {
    "live_study",
    "progress_projection",
    "domain_health_diagnostic",
    "current_package",
    "publication_eval",
    "publication_eval/latest.json",
    "artifacts/publication_eval/latest.json",
    "controller_decisions",
    "controller_decisions/latest.json",
    "artifacts/controller_decisions/latest.json",
    "delivery_truth",
}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _text(value: object, default: str = "") -> str:
    text = str(value or "").strip()
    return text or default


def _int(value: object, default: int) -> int:
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _events(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw_events = payload.get("events") or payload.get("timeline") or payload.get("items")
    if isinstance(raw_events, Mapping):
        return [
            {**event, "event_id": event.get("event_id") or str(event_id)}
            for event_id, event in raw_events.items()
            if isinstance(event, Mapping)
        ]
    return [event for event in _sequence(raw_events) if isinstance(event, Mapping)]


def _event_type(event: Mapping[str, Any]) -> str:
    return _text(event.get("event_type") or event.get("type"))


def _authority_contract() -> dict[str, Any]:
    return {
        "mode": "evidence_only",
        "writes_live_study": False,
        "writes_current_package": False,
        "writes_publication_eval": False,
        "writes_controller_decisions": False,
        "writes_delivery_truth": False,
        "can_authorize_submission": False,
        "can_authorize_quality": False,
    }


def _blocking_gaps(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for event in events:
        event_id = _text(event.get("event_id"), "unknown")
        for surface in _sequence(event.get("writes")):
            surface_name = _text(surface)
            if surface_name in PROHIBITED_WRITES:
                gaps.append(
                    {
                        "event_id": event_id,
                        "code": "authority_write_prohibited",
                        "surface": surface_name,
                    }
                )
    return gaps


def _coverage(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    covered = []
    observed_types = {_event_type(event) for event in events}
    for event_type in REQUIRED_EVENTS:
        if event_type in observed_types:
            covered.append(event_type)
    return {
        "required_events": list(REQUIRED_EVENTS),
        "covered_events": covered,
        "missing_events": [event_type for event_type in REQUIRED_EVENTS if event_type not in observed_types],
    }


def _paper_lines(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lines: dict[str, dict[str, Any]] = {}
    for event in events:
        paper_line_id = _text(event.get("paper_line_id"), "unknown")
        if paper_line_id not in lines:
            lines[paper_line_id] = {
                "paper_line_id": paper_line_id,
                "study_ids": [],
                "event_count": 0,
            }
        line = lines[paper_line_id]
        study_id = _text(event.get("study_id"))
        if study_id and study_id not in line["study_ids"]:
            line["study_ids"].append(study_id)
        line["event_count"] += 1
    return list(lines.values())


def _route_changes(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for event in events:
        if _event_type(event) != "route_change_line_switch":
            continue
        changes.append(
            {
                "event_id": _text(event.get("event_id"), "unknown"),
                "from_paper_line_id": _text(event.get("previous_paper_line_id"), "unknown"),
                "to_paper_line_id": _text(event.get("paper_line_id"), "unknown"),
                "route_action": _text(event.get("route_action"), "switch_line"),
            }
        )
    return changes


def _same_line_reopens(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    reopens: list[dict[str, Any]] = []
    for event in events:
        if _event_type(event) != "reopen_same_paper_line":
            continue
        reopens.append(
            {
                "event_id": _text(event.get("event_id"), "unknown"),
                "paper_line_id": _text(event.get("paper_line_id"), "unknown"),
                "study_id": _text(event.get("study_id"), "unknown"),
            }
        )
    return reopens


def _parse_time(value: object) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _latency_minutes(event: Mapping[str, Any]) -> int | None:
    explicit = event.get("latency_minutes")
    if explicit is not None:
        return _int(explicit, -1) if _int(explicit, -1) >= 0 else None
    started = _parse_time(event.get("started_at") or event.get("authorized_at"))
    finished = _parse_time(event.get("finished_at") or event.get("rebuilt_at"))
    if started is None or finished is None:
        return None
    return int((finished - started).total_seconds() // 60)


def _latency_acceptance(
    events: Sequence[Mapping[str, Any]],
    *,
    threshold_minutes: int,
) -> dict[str, Any]:
    measurements: list[dict[str, Any]] = []
    for event in events:
        if _event_type(event) != "draft_authorization_to_submission_package_rebuild_latency":
            continue
        minutes = _latency_minutes(event)
        accepted = minutes is not None and minutes <= threshold_minutes
        measurements.append(
            {
                "event_id": _text(event.get("event_id"), "unknown"),
                "latency_minutes": minutes,
                "accepted": accepted,
                "evidence_refs": [
                    str(ref) for ref in _sequence(event.get("evidence_refs")) if _text(ref)
                ],
            }
        )
    return {
        "threshold_minutes": threshold_minutes,
        "accepted": bool(measurements) and all(item["accepted"] for item in measurements),
        "measurements": measurements,
    }


def _failure_recovery_replay(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    replay: list[dict[str, Any]] = []
    for event in events:
        if _event_type(event) != "failure_recovery_replay_evidence":
            continue
        replay.append(
            {
                "event_id": _text(event.get("event_id"), "unknown"),
                "failure_event_id": _text(event.get("failure_event_id"), "unknown"),
                "recovery_event_id": _text(event.get("recovery_event_id"), "unknown"),
                "replay_evidence_refs": [
                    str(ref)
                    for ref in _sequence(
                        event.get("replay_evidence_refs") or event.get("evidence_refs")
                    )
                    if _text(ref)
                ],
            }
        )
    return replay


def _read_model(
    events: Sequence[Mapping[str, Any]],
    *,
    coverage: Mapping[str, Any],
    threshold_minutes: int,
) -> dict[str, Any]:
    return {
        "covered_events": list(_sequence(coverage.get("covered_events"))),
        "paper_lines": _paper_lines(events),
        "route_changes": _route_changes(events),
        "same_line_reopens": _same_line_reopens(events),
        "latency_acceptance": _latency_acceptance(
            events,
            threshold_minutes=threshold_minutes,
        ),
        "failure_recovery_replay": _failure_recovery_replay(events),
        "authority": _authority_contract(),
    }


def _missing_evidence_gaps(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    for event in events:
        event_type = _event_type(event)
        if event_type not in REQUIRED_EVENTS:
            continue
        if event_type == "failure_recovery_replay_evidence":
            refs = _sequence(event.get("replay_evidence_refs") or event.get("evidence_refs"))
        else:
            refs = _sequence(event.get("evidence_refs"))
        if refs:
            continue
        gaps.append(
            {
                "event_id": _text(event.get("event_id"), "unknown"),
                "code": "evidence_refs_missing",
                "event_type": event_type,
            }
        )
    return gaps


def _status(
    *,
    blocking_gaps: Sequence[Mapping[str, Any]],
    missing_events: Sequence[object],
    evidence_gaps: Sequence[Mapping[str, Any]],
    latency: Mapping[str, Any],
) -> str:
    if blocking_gaps:
        return "blocked"
    if missing_events or evidence_gaps or latency.get("accepted") is not True:
        return "partial"
    return "ready"


def _next_action(
    *,
    status: str,
    blocking_gaps: Sequence[Mapping[str, Any]],
    missing_events: Sequence[object],
    evidence_gaps: Sequence[Mapping[str, Any]],
    latency: Mapping[str, Any],
) -> str:
    if blocking_gaps:
        return "remove_authority_write_from_longitudinal_soak_proof"
    if missing_events:
        return f"materialize_{str(missing_events[0])}"
    if evidence_gaps:
        return "materialize_longitudinal_soak_evidence_refs"
    if latency.get("accepted") is not True:
        return "reduce_submission_package_rebuild_latency"
    if status == "ready":
        return "continue_l1_longitudinal_soak"
    return "review_l1_longitudinal_soak_gaps"


def build_longitudinal_soak_proof(
    *,
    catalog_payload: Mapping[str, Any] | None = None,
    catalog_path: Path | str | None = None,
) -> dict[str, Any]:
    payload = _mapping(catalog_payload)
    resolved_catalog_path = ""
    if catalog_path is not None:
        path = Path(catalog_path).expanduser().resolve()
        payload = _read_json(path)
        resolved_catalog_path = str(path)

    event_items = _events(payload)
    threshold_minutes = _int(
        payload.get("latency_threshold_minutes"),
        DEFAULT_LATENCY_THRESHOLD_MINUTES,
    )
    coverage = _coverage(event_items)
    read_model = _read_model(
        event_items,
        coverage=coverage,
        threshold_minutes=threshold_minutes,
    )
    blocking_gaps = _blocking_gaps(event_items)
    evidence_gaps = _missing_evidence_gaps(event_items)
    latency = _mapping(read_model.get("latency_acceptance"))
    status = _status(
        blocking_gaps=blocking_gaps,
        missing_events=_sequence(coverage.get("missing_events")),
        evidence_gaps=evidence_gaps,
        latency=latency,
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "catalog_source": {
            "kind": "path" if catalog_path is not None else "payload",
            "path": resolved_catalog_path,
            "catalog_id": _text(payload.get("catalog_id")),
        },
        "overall_status": status,
        "next_action": _next_action(
            status=status,
            blocking_gaps=blocking_gaps,
            missing_events=_sequence(coverage.get("missing_events")),
            evidence_gaps=evidence_gaps,
            latency=latency,
        ),
        "coverage": coverage,
        "blocking_gaps": blocking_gaps,
        "evidence_gaps": evidence_gaps,
        "read_model_projection": read_model,
        "authority_contract": _authority_contract(),
    }


def summarize_l1_longitudinal_outputs(proof: Mapping[str, Any]) -> dict[str, Any]:
    read_model = _mapping(proof.get("read_model_projection"))
    authority = _mapping(read_model.get("authority") or proof.get("authority_contract"))
    return {
        "surface": _text(proof.get("surface"), SURFACE),
        "read_model": _text(proof.get("read_model"), READ_MODEL),
        "overall_status": _text(proof.get("overall_status"), "unknown"),
        "covered_events": list(_sequence(read_model.get("covered_events"))),
        "authority_mode": _text(authority.get("mode"), "evidence_only"),
    }
