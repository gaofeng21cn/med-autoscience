from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import stage_knowledge_plane


SCHEMA_VERSION = 1
SURFACE = "stage_knowledge_entry_read_model"


def build_stage_knowledge_entry(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    packet = stage_knowledge_plane.build_stage_knowledge_packet(
        study_id=study_id,
        stage=stage,
        study_root=study_root,
        workspace_root=workspace_root,
        quest_root=quest_root,
    )
    return _entry_from_packet(packet)


def materialize_stage_knowledge_entry(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
    quest_root: Path | None = None,
) -> dict[str, Any]:
    packet = stage_knowledge_plane.materialize_stage_knowledge_packet(
        study_id=study_id,
        stage=stage,
        study_root=study_root,
        workspace_root=workspace_root,
        quest_root=quest_root,
    )
    entry = _entry_from_packet(packet)
    return {
        **entry,
        "refs": {
            "stage_knowledge_packet_ref": entry["stage_knowledge_packet_ref"],
            "stage_knowledge_packet_path": packet.get("artifact_path"),
        },
    }


def inject_stage_knowledge_entry(
    payload: dict[str, Any],
    *,
    stage_entry: dict[str, Any],
) -> dict[str, Any]:
    injected = dict(payload)
    input_contract = dict(injected.get("input_contract") or {})
    required_refs = dict(input_contract.get("required_refs") or {})
    required_refs["stage_knowledge_packet"] = _stage_knowledge_input_ref(stage_entry)
    input_contract["required_refs"] = required_refs
    input_contract["required_surfaces"] = list(
        dict.fromkeys([*list(input_contract.get("required_surfaces") or []), "stage_knowledge_packet"])
    )
    missing = list(input_contract.get("missing_or_invalid_refs") or [])
    if stage_entry.get("status") != "ready":
        missing.append("stage_knowledge_packet")
    input_contract["missing_or_invalid_refs"] = list(dict.fromkeys(missing))
    input_contract["all_required_refs_present"] = not input_contract["missing_or_invalid_refs"]
    injected["input_contract"] = input_contract
    injected["stage_knowledge_entry"] = dict(stage_entry)
    injected["stage_knowledge_packet_ref"] = stage_entry.get("stage_knowledge_packet_ref")
    injected["stage_knowledge_status"] = stage_entry.get("status")
    injected["stage_knowledge_missing_reasons"] = list(stage_entry.get("missing_reasons") or [])
    return injected


def _entry_from_packet(packet: dict[str, Any]) -> dict[str, Any]:
    packet_ref = _stage_knowledge_packet_ref(stage=packet["stage"])
    missing_reasons = _missing_reasons(packet)
    status = "ready" if not missing_reasons and packet.get("status") == "ready" else "missing"
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": packet["study_id"],
        "stage": packet["stage"],
        "status": status,
        "stage_knowledge_packet_ref": packet_ref,
        "missing_reasons": missing_reasons,
        "packet_status": packet.get("status"),
        "packet_source_fingerprint": packet.get("source_fingerprint"),
        "packet_idempotency_key": packet.get("idempotency_key"),
        "authority_boundary": packet.get("authority_boundary"),
    }


def _stage_knowledge_packet_ref(*, stage: str) -> str:
    return f"artifacts/stage_knowledge/{_safe_stage(stage)}/latest.json"


def _missing_reasons(packet: dict[str, Any]) -> list[str]:
    reasons = [str(item) for item in packet.get("missing_reasons") or [] if str(item or "").strip()]
    if not packet.get("source_fingerprint"):
        reasons.append("missing_context:source_fingerprint")
    if not packet.get("idempotency_key"):
        reasons.append("missing_context:idempotency_key")
    if not packet.get("input_refs"):
        reasons.append("missing_context:input_refs")
    return list(dict.fromkeys(reasons))


def _stage_knowledge_input_ref(stage_entry: dict[str, Any]) -> dict[str, Any]:
    ref = stage_entry.get("stage_knowledge_packet_ref")
    return {
        "surface": "stage_knowledge_packet",
        "relative_path": ref,
        "ref": ref,
        "required": True,
        "present": stage_entry.get("status") == "ready",
        "valid": stage_entry.get("status") == "ready",
        "status": stage_entry.get("status"),
        "missing_reasons": list(stage_entry.get("missing_reasons") or []),
    }


def _safe_stage(stage: str) -> str:
    return str(stage or "").strip().replace("/", "_")


__all__ = [
    "build_stage_knowledge_entry",
    "inject_stage_knowledge_entry",
    "materialize_stage_knowledge_entry",
]
