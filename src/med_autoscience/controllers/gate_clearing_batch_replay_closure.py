from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import gate_clearing_batch_submission


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
    if not gate_clearing_batch_submission.stale_submission_authority_signature_current(gate_report=gate_report):
        return False
    return marker.get("handshake") == stale_gate_replay_handshake(gate_report)


def stale_gate_replay_closure_marker(
    *,
    gate_report: dict[str, Any],
    gate_replay: dict[str, Any],
    gate_replay_timing: dict[str, Any],
    schema_version: int,
) -> dict[str, Any] | None:
    if not gate_clearing_batch_submission.stale_submission_authority_signature_current(gate_report=gate_report):
        return None
    gate_replay_status = _non_empty_text(gate_replay.get("status"))
    if gate_replay_status != "clear" and gate_replay.get("allow_write") is not True:
        return None
    return {
        "schema_version": schema_version,
        "status": "closed",
        "closure_reason": "stale_submission_minimal_authority_replay_closed",
        "handshake": stale_gate_replay_handshake(gate_report),
        "gate_replay_status": gate_replay_status,
        "gate_replay_allow_write": bool(gate_replay.get("allow_write")),
        "gate_replay_report_json": _non_empty_text(gate_replay.get("report_json")),
        "closed_at": _non_empty_text(gate_replay_timing.get("finished_at")),
    }
