from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.paper_mission_receipt_owner_consumption.common import (
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
    existing = (
        _valid_owner_consumption_readback(packet_ref=packet_path, study_id=study_id)
        if packet_path.exists()
        else None
    )
    if _existing_route_checkpoint_is_newer(
        existing=existing,
        incoming=payload,
        output_root=output_root,
    ):
        existing_text = packet_path.read_text(encoding="utf-8")
        return {
            "surface_kind": "paper_mission_receipt_owner_consumption_output_manifest",
            "schema_version": 1,
            "output_root": str(output_root),
            "packet_ref": str(packet_path),
            "packet_sha256": hashlib.sha256(existing_text.encode("utf-8")).hexdigest(),
            "writes_authority": False,
            "writes_yang_authority": False,
            "writes_receipt_owner_consumption": False,
            "write_skipped_stale_route_checkpoint": True,
            "preserved_route_checkpoint_evidence_ref": _route_checkpoint_ref(existing),
            "incoming_route_checkpoint_evidence_ref": _route_checkpoint_ref(payload),
            "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        }
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


def _existing_route_checkpoint_is_newer(
    *,
    existing: Mapping[str, Any] | None,
    incoming: Mapping[str, Any],
    output_root: Path,
) -> bool:
    if not existing:
        return False
    existing_ref = _route_checkpoint_ref(existing)
    incoming_ref = _route_checkpoint_ref(incoming)
    if existing_ref is None or incoming_ref is None or existing_ref == incoming_ref:
        return False
    if _consumption_status(existing) != "owner_consumed_route_checkpoint":
        return False
    if _consumption_status(incoming) != "owner_consumed_route_checkpoint":
        return False
    workspace_root = _workspace_root_from_output_root(output_root)
    if workspace_root is None:
        return False
    existing_mtime = _ref_mtime(workspace_root=workspace_root, ref=existing_ref)
    incoming_mtime = _ref_mtime(workspace_root=workspace_root, ref=incoming_ref)
    return (
        existing_mtime is not None
        and incoming_mtime is not None
        and existing_mtime > incoming_mtime
    )


def _route_checkpoint_ref(payload: Mapping[str, Any] | None) -> str | None:
    data = _mapping(payload)
    consumption = _mapping(data.get("mas_receipt_consumption"))
    stage = _mapping(data.get("stage_closure"))
    decision = _mapping(data.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    return (
        _text(consumption.get("route_checkpoint_evidence_ref"))
        or _text(stage.get("route_checkpoint_evidence_ref"))
        or _text(decision.get("route_checkpoint_evidence_ref"))
        or _text(outcome.get("route_checkpoint_evidence_ref"))
    )


def _consumption_status(payload: Mapping[str, Any]) -> str | None:
    return _text(_mapping(payload.get("mas_receipt_consumption")).get("status"))


def _workspace_root_from_output_root(output_root: Path) -> Path | None:
    resolved = output_root.expanduser().resolve()
    if len(resolved.parents) < 3:
        return None
    if resolved.name != "paper_mission_receipt_owner_consumption":
        return None
    if resolved.parent.name != "medautoscience" or resolved.parent.parent.name != "ops":
        return None
    return resolved.parents[2]


def _ref_mtime(*, workspace_root: Path, ref: str) -> float | None:
    path = Path(ref)
    if not path.is_absolute():
        path = workspace_root / path
    try:
        return path.stat().st_mtime
    except OSError:
        return None


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
