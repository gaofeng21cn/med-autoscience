from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.paper_mission_receipt_owner_consumption_parts.common import (
    FORBIDDEN_AUTHORITY_WRITES,
    _mapping,
    _read_json_object,
    _text,
)

def latest_receipt_owner_consumption_readback(
    *,
    workspace_root: Path,
    study_id: str,
) -> dict[str, Any] | None:
    ledger_root = (
        workspace_root.expanduser().resolve()
        / "ops"
        / "medautoscience"
        / "paper_mission_receipt_owner_consumption"
    )
    if not ledger_root.exists():
        return None
    candidates: list[tuple[float, str, dict[str, Any]]] = []
    for packet_ref in ledger_root.glob(f"**/{study_id}/receipt_owner_consumption.json"):
        payload = _valid_owner_consumption_readback(
            packet_ref=packet_ref,
            study_id=study_id,
        )
        if payload is None:
            continue
        try:
            mtime = packet_ref.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append((mtime, str(packet_ref), payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _write_output_packet(
    *,
    output_root: Path,
    study_id: str,
    payload: Mapping[str, Any],
    writes_authority: bool = False,
) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    packet_path = output_root / study_id / "receipt_owner_consumption.json"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    packet_path.write_text(text + "\n", encoding="utf-8")
    return {
        "surface_kind": "paper_mission_receipt_owner_consumption_output_manifest",
        "schema_version": 1,
        "output_root": str(output_root),
        "packet_ref": str(packet_path),
        "packet_sha256": hashlib.sha256((text + "\n").encode("utf-8")).hexdigest(),
        "writes_authority": bool(writes_authority),
        "writes_yang_authority": False,
        "writes_receipt_owner_consumption": bool(writes_authority),
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
    }


def _valid_owner_consumption_readback(
    *,
    packet_ref: Path,
    study_id: str,
) -> dict[str, Any] | None:
    payload = _read_json_object(packet_ref)
    if payload.get("surface_kind") != "paper_mission_receipt_owner_consumption":
        return None
    if _text(payload.get("study_id")) != study_id:
        return None
    if payload.get("status") != "owner_consumption_applied":
        return None
    if payload.get("authority_materialized") is not True:
        return None
    decision = _mapping(payload.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    outcome_kind = _text(outcome.get("kind"))
    transition_kind = _text(outcome.get("transition_kind"))
    if outcome_kind == "typed_blocker":
        if decision.get("counts_as_typed_blocker") is not True:
            return None
    elif (
        outcome_kind == "next_stage_transition"
        and transition_kind == "route_back_candidate_checkpoint"
    ):
        if decision.get("counts_as_typed_blocker") is True:
            return None
    else:
        return None
    boundary = _mapping(decision.get("authority_boundary"))
    if any(
        boundary.get(flag) is True
        for flag in (
            "writes_owner_receipt",
            "writes_human_gate",
            "writes_current_package",
            "writes_submission_ready_package",
            "writes_runtime_queue_or_provider_attempt",
        )
    ):
        return None
    return {
        **payload,
        "source_ref": str(packet_ref),
        "decision_ref": str(packet_ref),
        "source_surface_kind": "paper_mission_receipt_owner_consumption_ledger",
    }
