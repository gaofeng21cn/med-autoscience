from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import gate_clearing_batch_submission


_SYNC_BLOCKING_STATUSES = frozenset(
    {
        "failed",
        "missing",
        "skipped_failed_dependency",
        "skipped_authority_not_settled",
    }
)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _stable_blocking_artifact_refs(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    refs: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            compact = {str(key): item[key] for key in sorted(item) if str(item.get(key) or "").strip()}
            if compact:
                refs.append(compact)
            continue
        text = str(item or "").strip()
        if text:
            refs.append({"ref": text})
    return sorted(refs, key=lambda item: json.dumps(item, ensure_ascii=True, sort_keys=True))


def stale_gate_replay_handshake(gate_report: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
        "evaluated_source_signature": _non_empty_text(
            gate_report.get("submission_minimal_evaluated_source_signature")
        ),
        "authority_source_signature": _non_empty_text(
            gate_report.get("submission_minimal_authority_source_signature")
        ),
        "blocking_artifact_refs": _stable_blocking_artifact_refs(gate_report.get("blocking_artifact_refs")),
    }


def stale_gate_replay_closed(latest_batch: dict[str, Any], *, gate_report: dict[str, Any]) -> bool:
    marker = latest_batch.get("stale_gate_replay_closure")
    if not isinstance(marker, Mapping) or _non_empty_text(marker.get("status")) != "closed":
        return False
    if not _closure_marker_applies_to_gate_report(marker=marker, gate_report=gate_report):
        return False
    return marker.get("handshake") == stale_gate_replay_handshake(gate_report)


def _sync_completed_current_package(unit_results: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    for item in unit_results or []:
        if not isinstance(item, Mapping) or _non_empty_text(item.get("unit_id")) != "sync_submission_minimal_delivery":
            continue
        status = _non_empty_text(item.get("status"))
        if status is None or status in _SYNC_BLOCKING_STATUSES:
            continue
        result = item.get("result") if isinstance(item.get("result"), Mapping) else {}
        source_signature = _non_empty_text((result or {}).get("source_signature")) or _non_empty_text(
            (result or {}).get("evaluated_source_signature")
        )
        authority_signature = _non_empty_text((result or {}).get("authority_source_signature"))
        if source_signature is not None and authority_signature is not None and source_signature != authority_signature:
            continue
        return {"status": status, "result": dict(result or {})}
    return None


def _stale_delivery_replay_candidate(*, gate_report: dict[str, Any]) -> bool:
    blockers = {str(item or "").strip() for item in (gate_report.get("blockers") or []) if str(item or "").strip()}
    if "stale_study_delivery_mirror" not in blockers:
        return False
    return gate_clearing_batch_submission.submission_minimal_authority_signature_current(gate_report=gate_report)


def _closure_marker_applies_to_gate_report(*, marker: Mapping[str, Any], gate_report: dict[str, Any]) -> bool:
    closed_blockers = {
        str(item or "").strip()
        for item in (marker.get("closed_blockers") or [])
        if str(item or "").strip()
    }
    if (
        "stale_submission_minimal_authority" in closed_blockers
        and gate_clearing_batch_submission.stale_submission_authority_signature_current(gate_report=gate_report)
    ):
        return True
    if "stale_study_delivery_mirror" in closed_blockers and _stale_delivery_replay_candidate(gate_report=gate_report):
        return True
    return False


def stale_gate_replay_closure_marker(
    *,
    gate_report: dict[str, Any],
    gate_replay: dict[str, Any],
    gate_replay_timing: dict[str, Any],
    unit_results: list[dict[str, Any]] | None = None,
    schema_version: int,
) -> dict[str, Any] | None:
    closed_blockers: list[str] = []
    delivery_sync = _sync_completed_current_package(unit_results)
    if gate_clearing_batch_submission.stale_submission_authority_signature_current(gate_report=gate_report):
        closed_blockers.append("stale_submission_minimal_authority")
    if delivery_sync is not None and _stale_delivery_replay_candidate(gate_report=gate_report):
        closed_blockers.append("stale_study_delivery_mirror")
    if not closed_blockers:
        return None
    gate_replay_status = _non_empty_text(gate_replay.get("status"))
    if gate_replay_status != "clear" and gate_replay.get("allow_write") is not True:
        return None
    closure_reason = (
        "stale_submission_minimal_authority_replay_closed"
        if "stale_submission_minimal_authority" in closed_blockers
        else "stale_study_delivery_mirror_replay_closed"
    )
    marker = {
        "schema_version": schema_version,
        "status": "closed",
        "closure_reason": closure_reason,
        "closed_blockers": closed_blockers,
        "handshake": stale_gate_replay_handshake(gate_report),
        "gate_replay_status": gate_replay_status,
        "gate_replay_allow_write": bool(gate_replay.get("allow_write")),
        "gate_replay_report_json": _non_empty_text(gate_replay.get("report_json")),
        "closed_at": _non_empty_text(gate_replay_timing.get("finished_at")),
    }
    if delivery_sync is not None:
        marker["delivery_sync_status"] = delivery_sync["status"]
    return marker
