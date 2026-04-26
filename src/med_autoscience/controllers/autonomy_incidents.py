from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


PLATFORM_INCIDENT_TYPES: tuple[str, ...] = (
    "no_live",
    "stalled",
    "status_drift",
    "wrong_milestone_claim",
    "quality_reopen",
    "runtime_recovery_failure",
    "surface_ownership_drift",
)

PREVENTION_ACTION_TYPES: tuple[str, ...] = (
    "guard",
    "test",
    "contract",
    "runbook",
    "runtime_taxonomy",
    "strangler_rule",
)

_INCIDENT_BOTTLENECKS = frozenset(
    {
        "runtime_recovery_churn",
        "repeated_controller_decision",
        "publication_gate_blocked",
        "non_actionable_gate",
    }
)
_PLATFORM_INCIDENT_LABELS = {
    "no_live": "no-live",
    "stalled": "stalled",
    "status_drift": "status drift",
    "wrong_milestone_claim": "wrong milestone claim",
    "quality_reopen": "quality reopen",
    "runtime_recovery_failure": "runtime recovery failure",
    "surface_ownership_drift": "surface ownership drift",
}
_PREVENTION_ACTION_BY_INCIDENT = {
    "no_live": {
        "action_type": "runtime_taxonomy",
        "controller_surface": "runtime_watch",
        "summary": "Classify no-live runtime loss before any resume or work-unit dispatch.",
    },
    "stalled": {
        "action_type": "guard",
        "controller_surface": "runtime_watch",
        "summary": "Guard against stalled turns by requiring a fresh heartbeat/progress observation.",
    },
    "status_drift": {
        "action_type": "contract",
        "controller_surface": "study_runtime_status",
        "summary": "Pin status ownership to the durable runtime status contract before operator claims.",
    },
    "wrong_milestone_claim": {
        "action_type": "test",
        "controller_surface": "controller_decisions/latest.json",
        "summary": "Add a regression check that milestone claims match current truth surfaces.",
    },
    "quality_reopen": {
        "action_type": "guard",
        "controller_surface": "publication_eval/latest.json",
        "summary": "Require reopened quality gates to route through quality-preserving controller work.",
    },
    "runtime_recovery_failure": {
        "action_type": "runbook",
        "controller_surface": "runtime_watch",
        "summary": "Escalate repeated recovery failures through a platform runbook before retrying.",
    },
    "surface_ownership_drift": {
        "action_type": "strangler_rule",
        "controller_surface": "controller_decisions/latest.json",
        "summary": "Keep ownership drift behind a strangler rule instead of spreading ad-hoc writes.",
    },
    "runtime_recovery_churn": {
        "action_type": "runtime_taxonomy",
        "controller_surface": "runtime_watch",
        "summary": "Classify recovery churn into the runtime taxonomy before resuming.",
    },
    "repeated_controller_decision": {
        "action_type": "guard",
        "controller_surface": "controller_decisions/latest.json",
        "summary": "Guard controller dispatch against repeated decision fingerprints.",
    },
    "publication_gate_blocked": {
        "action_type": "contract",
        "controller_surface": "publication_eval/latest.json",
        "summary": "Keep publication blockers expressed as concrete controller contracts.",
    },
    "non_actionable_gate": {
        "action_type": "contract",
        "controller_surface": "publication_eval/latest.json",
        "summary": "Require non-actionable gate findings to become concrete blocker contracts.",
    },
    "stale_current_package": {
        "action_type": "runbook",
        "controller_surface": "submission_minimal",
        "summary": "Refresh human-facing packages only after authority surfaces settle.",
    },
}
_NORMALIZED_PLATFORM_INCIDENTS = {
    incident_type: incident_type for incident_type in PLATFORM_INCIDENT_TYPES
} | {
    label.replace("-", "_").replace(" ", "_"): incident_type
    for incident_type, label in _PLATFORM_INCIDENT_LABELS.items()
}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _normalize_platform_incident_type(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    normalized = text.lower().replace("-", "_").replace(" ", "_")
    return _NORMALIZED_PLATFORM_INCIDENTS.get(normalized)


def _prevention_action(incident_type: str) -> dict[str, Any]:
    action = _PREVENTION_ACTION_BY_INCIDENT.get(incident_type)
    if action is None:
        action = {
            "action_type": "runbook",
            "controller_surface": "autonomy_incidents",
            "summary": "Record the incident in an operator runbook before any retry.",
        }
    action_type = str(action["action_type"])
    if action_type not in PREVENTION_ACTION_TYPES:
        raise ValueError(f"unsupported prevention action type: {action_type}")
    return {
        **dict(action),
        "gate_relaxation_allowed": False,
    }


def _incident_id(*, study_id: str, incident_type: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"autonomy-incident::{study_id}::{incident_type}::{digest}"


def _candidate_with_id(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    study_id = str(payload.get("study_id") or "").strip()
    incident_type = str(payload.get("incident_type") or "").strip()
    payload["prevention_action"] = _prevention_action(incident_type)
    payload["gate_relaxation_allowed"] = False
    payload["incident_id"] = _incident_id(
        study_id=study_id,
        incident_type=incident_type,
        payload=payload,
    )
    return payload


def incident_candidates_from_profile(profile_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = str(profile_payload.get("study_id") or "").strip()
    sli_summary = profile_payload.get("sli_summary") if isinstance(profile_payload.get("sli_summary"), Mapping) else {}
    gate_summary = profile_payload.get("gate_blocker_summary")
    next_work_unit = (
        gate_summary.get("next_work_unit")
        if isinstance(gate_summary, Mapping)
        else None
    )
    candidates: list[dict[str, Any]] = []
    bottlenecks = profile_payload.get("bottlenecks")
    if not isinstance(bottlenecks, list):
        return candidates
    for bottleneck in bottlenecks:
        if not isinstance(bottleneck, Mapping):
            continue
        bottleneck_id = str(bottleneck.get("bottleneck_id") or "").strip()
        if bottleneck_id not in _INCIDENT_BOTTLENECKS:
            continue
        candidate = {
            "source": "profile-cycle",
            "study_id": study_id,
            "incident_type": bottleneck_id,
            "severity": str(bottleneck.get("severity") or "").strip() or "unknown",
            "sli_summary": dict(sli_summary),
            "next_work_unit": dict(next_work_unit) if isinstance(next_work_unit, Mapping) else None,
        }
        candidates.append(_candidate_with_id(candidate))
    return candidates


def _explicit_platform_incidents(profile_payload: Mapping[str, Any]) -> list[str]:
    event_types: list[str] = []
    for key in ("platform_incident_types", "platform_event_types"):
        for item in _list(profile_payload.get(key)):
            incident_type = _normalize_platform_incident_type(item)
            if incident_type is not None:
                event_types.append(incident_type)
    for key in ("platform_incidents", "platform_events"):
        for item in _list(profile_payload.get(key)):
            if isinstance(item, Mapping):
                incident_type = _normalize_platform_incident_type(
                    item.get("incident_type") or item.get("event_type") or item.get("type")
                )
                if incident_type is not None:
                    event_types.append(incident_type)
    return event_types


def _derived_platform_incidents(profile_payload: Mapping[str, Any]) -> list[str]:
    incidents: list[str] = []
    state_machine = _mapping(profile_payload.get("autonomy_state_machine"))
    current_state = _normalize_platform_incident_type(state_machine.get("current_state"))
    if current_state in {"no_live", "stalled"}:
        incidents.append(current_state)
    mds_activity = _mapping(profile_payload.get("mds_worker_activity"))
    if _text(mds_activity.get("heartbeat_state")) == "missing_live_session":
        incidents.append("no_live")
    if _text(mds_activity.get("activity_state")) == "stalled":
        incidents.append("stalled")
    diagnosis = _mapping(profile_payload.get("mds_failure_diagnosis")) or _mapping(
        profile_payload.get("runtime_failure_diagnosis")
    )
    diagnosis_code = _text(diagnosis.get("diagnosis_code") or diagnosis.get("code"))
    if diagnosis_code == "daemon_no_live_worker":
        incidents.append("no_live")
    if diagnosis_code == "daemon_stalled_live_turn":
        incidents.append("stalled")
    current_state_summary = _mapping(profile_payload.get("current_state_summary"))
    if _text(current_state_summary.get("runtime_health_status")) == "escalated":
        incidents.append("runtime_recovery_failure")
    if _text(current_state_summary.get("runtime_reason")) == "quest_marked_running_but_no_live_session":
        incidents.append("no_live")
    return incidents


def _platform_incident_candidate(
    *,
    study_id: str,
    quest_id: str | None,
    incident_type: str,
    source: str,
) -> dict[str, Any]:
    candidate = {
        "source": source,
        "study_id": study_id,
        "quest_id": quest_id,
        "incident_type": incident_type,
        "incident_label": _PLATFORM_INCIDENT_LABELS[incident_type],
        "scope": "platform",
        "severity": "high" if incident_type in {"runtime_recovery_failure", "surface_ownership_drift"} else "medium",
    }
    return _candidate_with_id(candidate)


def platform_incident_candidates_from_profile(profile_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = _text(profile_payload.get("study_id")) or "unknown-study"
    quest_id = _text(profile_payload.get("quest_id"))
    ordered: list[str] = []
    seen: set[str] = set()
    source_by_type: dict[str, str] = {}
    for source, incident_types in (
        ("explicit_platform_event", _explicit_platform_incidents(profile_payload)),
        ("derived_platform_state", _derived_platform_incidents(profile_payload)),
    ):
        for incident_type in incident_types:
            if incident_type not in PLATFORM_INCIDENT_TYPES or incident_type in seen:
                continue
            seen.add(incident_type)
            ordered.append(incident_type)
            source_by_type[incident_type] = source
    return [
        _platform_incident_candidate(
            study_id=study_id,
            quest_id=quest_id,
            incident_type=incident_type,
            source=source_by_type[incident_type],
        )
        for incident_type in ordered
    ]


def build_platform_incident_learning_loop(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    incidents = platform_incident_candidates_from_profile(profile_payload)
    return {
        "surface": "autonomy_incident_learning_loop",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "incident_scope": "platform_only",
        "allowed_incident_types": list(PLATFORM_INCIDENT_TYPES),
        "allowed_prevention_action_types": list(PREVENTION_ACTION_TYPES),
        "incident_count": len(incidents),
        "incidents": incidents,
        "gate_relaxation_allowed": False,
    }


def write_incident_record(*, study_root: Path, candidate: Mapping[str, Any], recorded_at: str) -> Path:
    incident_id = str(candidate.get("incident_id") or "").strip()
    if not incident_id:
        raise ValueError("incident candidate must include incident_id")
    payload = dict(candidate)
    incident_type = str(payload.get("incident_type") or "").strip()
    payload.setdefault("prevention_action", _prevention_action(incident_type))
    payload["gate_relaxation_allowed"] = False
    payload["recorded_at"] = recorded_at
    target = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "runtime"
        / "autonomy_incidents"
        / f"{incident_id.replace(':', '-')}.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target
