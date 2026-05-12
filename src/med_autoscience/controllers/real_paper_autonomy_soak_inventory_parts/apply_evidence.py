from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def build_mas_owner_apply_evidence(study: Mapping[str, Any]) -> dict[str, Any]:
    repair_receipt = _mapping(study.get("repair_execution_receipt"))
    repair_evidence = _mapping(study.get("repair_execution_evidence"))
    gate_replay = _mapping(study.get("gate_replay"))
    receipt_ref = _source_ref_path(study, "artifacts/controller/repair_execution_receipts/latest.json")
    evidence_ref = _source_ref_path(study, "artifacts/controller/repair_execution_evidence/latest.json")
    gate_replay_ref = _source_ref_path(study, "artifacts/controller/gate_replay_requests/latest.json")
    receipt_executed = (
        repair_receipt.get("surface") == "paper_repair_owner_receipt"
        and repair_receipt.get("accepted") is True
        and repair_receipt.get("execution_status") == "executed"
        and repair_receipt.get("direct_current_package_write") is False
        and repair_receipt.get("quality_authorized") is False
        and repair_receipt.get("submission_authorized") is False
    )
    evidence_progress_observed = (
        _mapping(repair_evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True
        or repair_evidence.get("progress_delta_candidate") is True
        or bool(repair_receipt.get("canonical_artifact_delta_refs"))
    )
    gate_replay_observed = gate_replay.get("surface") == "paper_repair_gate_replay_request"
    refs = []
    if receipt_executed and receipt_ref:
        refs.append(receipt_ref)
    if receipt_executed and evidence_progress_observed and evidence_ref:
        refs.append(evidence_ref)
    if gate_replay_observed and gate_replay_ref:
        refs.append(gate_replay_ref)
    return {
        "has_mas_owner_apply_receipt": bool((receipt_executed and evidence_progress_observed) or gate_replay_observed),
        "receipt_refs": list(dict.fromkeys(refs)),
        "receipt_surface": _text(repair_receipt.get("surface")),
        "receipt_execution_status": _text(repair_receipt.get("execution_status")),
        "evidence_progress_observed": evidence_progress_observed,
        "gate_replay_observed": gate_replay_observed,
    }


def empty_mas_owner_apply_evidence() -> dict[str, Any]:
    return {
        "has_mas_owner_apply_receipt": False,
        "receipt_refs": [],
        "receipt_surface": "",
        "receipt_execution_status": "",
        "evidence_progress_observed": False,
        "gate_replay_observed": False,
    }


def _source_ref_path(study: Mapping[str, Any], relative_ref: str) -> str:
    for item in study.get("source_refs", []):
        ref = _mapping(item)
        if ref.get("exists") is True and ref.get("relative_ref") == relative_ref:
            return _text(ref.get("path"))
    return ""


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["build_mas_owner_apply_evidence", "empty_mas_owner_apply_evidence"]
