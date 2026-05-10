from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from med_autoscience.controllers import stage_knowledge_plane


SCHEMA_VERSION = 1
SURFACE = "stage_knowledge_visibility"


def build_stage_knowledge_visibility(
    *,
    study_root: Path,
    study_id: str,
    stages: Sequence[str] = stage_knowledge_plane.EXPLORATORY_STAGES,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    stage_rows = [
        _stage_row(study_root=resolved_study_root, study_id=study_id, stage=stage)
        for stage in stages
    ]
    receipt_rows = _receipt_rows(study_root=resolved_study_root)
    accepted_writes = [write for receipt in receipt_rows for write in _mapping_list(receipt.get("accepted_writes"))]
    rejected_writes = [write for receipt in receipt_rows for write in _mapping_list(receipt.get("rejected_writes"))]
    route_impacts = _route_impacts(stage_rows=stage_rows, accepted_writes=accepted_writes, rejected_writes=rejected_writes)
    missing_reasons = [
        reason
        for row in stage_rows
        for reason in _text_list(row.get("missing_reasons"))
    ]
    status = "available" if any(row.get("status") == "available" for row in stage_rows) or receipt_rows else "missing"
    if missing_reasons and status == "missing":
        status = "missing"
    elif missing_reasons:
        status = "partial"
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "study_id": _text(study_id) or "unknown-study",
        "stage_count": len(stage_rows),
        "stages": stage_rows,
        "stage_knowledge_packet_refs": [
            row["stage_knowledge_packet_ref"]
            for row in stage_rows
            if _text(row.get("stage_knowledge_packet_ref"))
        ],
        "consumed_refs": _dedupe_text(
            ref
            for row in stage_rows
            for ref in _text_list(row.get("consumed_refs"))
        ),
        "closeout_receipt_refs": [
            _text(receipt.get("receipt_ref"))
            for receipt in receipt_rows
            if _text(receipt.get("receipt_ref"))
        ],
        "accepted_writes": accepted_writes,
        "rejected_writes": rejected_writes,
        "route_impact": route_impacts,
        "next_owner": _next_owner(route_impacts=route_impacts, accepted_writes=accepted_writes, rejected_writes=rejected_writes),
        "missing_reasons": _dedupe_text(missing_reasons),
        "authority_boundary": {
            "kind": "read_only_visibility",
            "writes_authority_surface": False,
            "can_authorize_publication_quality": False,
            "can_replace_controller_decision": False,
            "can_replace_evidence_ledger": False,
        },
    }


def _stage_row(*, study_root: Path, study_id: str, stage: str) -> dict[str, Any]:
    packet_ref = f"artifacts/stage_knowledge/{_safe_stage(stage)}/latest.json"
    packet_path = study_root / packet_ref
    packet = _read_json(packet_path)
    closeout_refs = [
        _relative(path, study_root)
        for path in sorted((packet_path.parent / "closeouts").glob("*.json"))
        if path.is_file()
    ]
    if not packet:
        return {
            "stage": stage,
            "status": "missing",
            "study_id": study_id,
            "stage_knowledge_packet_ref": packet_ref,
            "packet_freshness": "missing",
            "missing_reasons": [f"missing_stage_knowledge_packet:{stage}"],
            "consumed_refs": [],
            "closeout_packet_refs": closeout_refs,
        }
    return {
        "stage": stage,
        "status": "available" if _text(packet.get("status")) == "ready" else _text(packet.get("status")) or "available",
        "study_id": _text(packet.get("study_id")) or study_id,
        "stage_knowledge_packet_ref": packet_ref,
        "packet_freshness": "present",
        "source_fingerprint": _text(packet.get("source_fingerprint")),
        "idempotency_key": _text(packet.get("idempotency_key")),
        "missing_reasons": _text_list(packet.get("missing_reasons")),
        "consumed_refs": _packet_consumed_refs(packet),
        "literature_gaps": _text_list(packet.get("literature_gaps")),
        "failed_paths": _text_list(packet.get("failed_paths")),
        "citation_readiness": _mapping(packet.get("citation_readiness")),
        "closeout_packet_refs": closeout_refs,
    }


def _receipt_rows(*, study_root: Path) -> list[dict[str, Any]]:
    receipt_root = study_root / "artifacts" / "stage_knowledge" / "memory_write_router_receipts"
    rows: list[dict[str, Any]] = []
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        if not payload:
            continue
        rows.append(
            {
                **payload,
                "receipt_ref": _relative(path, study_root),
            }
        )
    return rows


def _packet_consumed_refs(packet: Mapping[str, Any]) -> list[str]:
    refs = []
    for item in _mapping_list(packet.get("input_refs")):
        path = _text(item.get("path"))
        ref_id = _text(item.get("ref_id"))
        if path:
            refs.append(path)
        elif ref_id:
            refs.append(ref_id)
    return _dedupe_text(refs)


def _route_impacts(
    *,
    stage_rows: Sequence[Mapping[str, Any]],
    accepted_writes: Sequence[Mapping[str, Any]],
    rejected_writes: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    impacts: list[dict[str, Any]] = []
    for row in stage_rows:
        stage = _text(row.get("stage"))
        for failed_path in _text_list(row.get("failed_paths")):
            impacts.append({"stage": stage, "kind": "failed_path", "ref": failed_path, "next_owner": "mas_controller"})
    for write in accepted_writes:
        impacts.append(
            {
                "stage": _text(write.get("stage")),
                "kind": _text(write.get("source_category")) or _text(write.get("destination")),
                "write_id": _text(write.get("write_id")),
                "destination": _text(write.get("destination")),
                "next_owner": _text(write.get("owner_target")),
            }
        )
    for write in rejected_writes:
        impacts.append(
            {
                "stage": _text(write.get("stage")),
                "kind": "rejected_write",
                "write_id": _text(write.get("write_id")),
                "reason": _text(write.get("reason")),
                "next_owner": _text(write.get("owner_target")) or "stage_closeout_author",
            }
        )
    return [impact for impact in impacts if any(value for value in impact.values())]


def _next_owner(
    *,
    route_impacts: Sequence[Mapping[str, Any]],
    accepted_writes: Sequence[Mapping[str, Any]],
    rejected_writes: Sequence[Mapping[str, Any]],
) -> str | None:
    for item in route_impacts:
        owner = _text(item.get("next_owner"))
        if owner:
            return owner
    for item in accepted_writes:
        owner = _text(item.get("owner_target"))
        if owner:
            return owner
    if rejected_writes:
        return "stage_closeout_author"
    return None


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str:
    return str(value or "").strip()


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe_text(items: Sequence[str] | Any) -> list[str]:
    return list(dict.fromkeys([_text(item) for item in items if _text(item)]))


def _safe_stage(stage: str) -> str:
    return _text(stage).replace("/", "_")


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


__all__ = ["build_stage_knowledge_visibility"]
