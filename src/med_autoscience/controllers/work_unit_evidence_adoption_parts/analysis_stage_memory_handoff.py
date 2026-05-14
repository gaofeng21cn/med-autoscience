from __future__ import annotations

from pathlib import Path
from typing import Any


RUNTIME_DIR_SUFFIX = Path("artifacts", "runtime", "analysis_claim_evidence_repair")
STAGE_MEMORY_CLOSEOUT_GLOB = "*_stage_memory_closeout_payload.json"
HANDOFF_ROUTE = "return_to_write"
HANDOFF_UNIT = "manuscript_story_repair"
HANDOFF_OWNER = "write/ai_reviewer"


def closeout_candidates(
    *,
    quest_root: Path,
    active_run_id: str | None,
) -> tuple[Path, ...]:
    stage_root = Path(quest_root).expanduser().resolve() / RUNTIME_DIR_SUFFIX
    if not stage_root.exists():
        return ()
    candidates = sorted(stage_root.glob(STAGE_MEMORY_CLOSEOUT_GLOB))
    if not candidates:
        return ()
    if active_run_id is not None:
        active_run_candidates = [path for path in candidates if active_run_id in path.name]
        if active_run_candidates:
            return tuple(active_run_candidates)
    return tuple(reversed(candidates))


def normalize_payload(
    payload: dict[str, Any],
    *,
    authorization_context: dict[str, Any],
    analysis_repair_work_unit_id: str,
    handoff_report_type: str,
    handoff_status: str,
) -> dict[str, Any]:
    if not is_handoff(payload):
        return payload
    request = _handoff_request(payload) or {}
    return {
        **payload,
        "repair_packet_type": handoff_report_type,
        "work_unit_id": analysis_repair_work_unit_id,
        "work_unit_fingerprint": _text(payload.get("work_unit_fingerprint"))
        or _text(authorization_context.get("work_unit_fingerprint")),
        "analysis_lane_status": handoff_status,
        "meaningful_artifact_delta": True,
        "next_owner": HANDOFF_OWNER,
        "next_work_unit": HANDOFF_UNIT,
        "dedupe_recommendation": _text(request.get("reason")),
    }


def is_handoff(payload: dict[str, Any]) -> bool:
    return (
        _text(payload.get("idempotency_key")) is not None
        and "stage_memory_closeout" in str(payload.get("idempotency_key"))
        and _source_refs_include_analysis_repair(payload)
        and _handoff_request(payload) is not None
    )


def _source_refs_include_analysis_repair(payload: dict[str, Any]) -> bool:
    source_refs = payload.get("source_refs")
    if not isinstance(source_refs, list):
        return False
    return any("analysis_claim_evidence_repair" in str(item) for item in source_refs)


def _handoff_request(payload: dict[str, Any]) -> dict[str, Any] | None:
    requests = payload.get("controller_decision_requests")
    if not isinstance(requests, list):
        return None
    for item in requests:
        if not isinstance(item, dict):
            continue
        if _text(item.get("requested_route")) != HANDOFF_ROUTE:
            continue
        if _text(item.get("next_work_unit")) != HANDOFF_UNIT:
            continue
        return dict(item)
    return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
