from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


_INCIDENT_BOTTLENECKS = frozenset(
    {
        "runtime_recovery_churn",
        "repeated_controller_decision",
        "publication_gate_blocked",
        "non_actionable_gate",
    }
)


def _incident_id(*, study_id: str, incident_type: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]
    return f"autonomy-incident::{study_id}::{incident_type}::{digest}"


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
        candidate["incident_id"] = _incident_id(
            study_id=study_id,
            incident_type=bottleneck_id,
            payload=candidate,
        )
        candidates.append(candidate)
    return candidates


def write_incident_record(*, study_root: Path, candidate: Mapping[str, Any], recorded_at: str) -> Path:
    incident_id = str(candidate.get("incident_id") or "").strip()
    if not incident_id:
        raise ValueError("incident candidate must include incident_id")
    payload = dict(candidate)
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
