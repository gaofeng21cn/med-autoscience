from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


ACTION_TYPE = "run_quality_repair_batch"
BLOCKED_REASON = "claim_evidence_alignment_required"
DEFAULT_EXECUTOR_EXECUTION_SURFACE = "artifacts/supervision/consumer/default_executor_execution/latest.json"
CONSUMER_REQUEST_SURFACE = "artifacts/supervision/consumer/run_quality_repair_batch.json"
REQUIRED_OUTPUT = (
    "claim-evidence map and evidence ledger alignment or "
    "typed blocker:claim_evidence_alignment_required"
)


def action_from_ai_reviewer_alignment_blocker(*, study_root: Path) -> dict[str, Any] | None:
    evidence = _latest_alignment_blocker_execution(study_root=study_root)
    if evidence is None:
        evidence = _pending_alignment_request(study_root=study_root)
    if evidence is None:
        return None
    owner_result = _mapping(evidence.get("owner_result"))
    claim_alignment = _mapping(owner_result.get("claim_evidence_alignment")) or _current_claim_alignment_gate(
        study_root=study_root
    )
    if _text(claim_alignment.get("status")) != "blocked":
        return None
    return {
        "action_type": ACTION_TYPE,
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": BLOCKED_REASON,
        "summary": (
            "AI reviewer workflow failed closed because claim_evidence_map references are not aligned "
            "with the evidence ledger; route the paper owner through quality-repair instead of retrying "
            "the same AI reviewer request."
        ),
        "required_output_surface": REQUIRED_OUTPUT,
        "route_target": "write",
        "next_work_unit": "claim_evidence_alignment_repair",
        "executable_work_unit": "claim_evidence_alignment_repair",
        "controller_action_type": ACTION_TYPE,
        "work_unit_fingerprint": _work_unit_fingerprint(claim_alignment),
        "source_blocked_reason": _text(evidence.get("blocked_reason")) or _text(evidence.get("reason")),
        "source_error": _text(evidence.get("error")),
        "source_execution_path": _text(evidence.get("source_execution_path")),
        "source_request_path": _text(evidence.get("source_request_path")),
        "claim_evidence_alignment": claim_alignment,
        "missing_evidence_item_refs": _missing_evidence_item_refs(claim_alignment, owner_result),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _latest_alignment_blocker_execution(*, study_root: Path) -> dict[str, Any] | None:
    source_path = Path(study_root).expanduser().resolve() / DEFAULT_EXECUTOR_EXECUTION_SURFACE
    record = _read_json_object(source_path)
    for execution in reversed(record.get("executions") or []):
        if not isinstance(execution, Mapping):
            continue
        if _text(execution.get("action_type")) != "return_to_ai_reviewer_workflow":
            continue
        if _text(execution.get("execution_status")) != "blocked":
            continue
        if _text(execution.get("blocked_reason")) != BLOCKED_REASON:
            continue
        return {**dict(execution), "source_execution_path": str(source_path)}
    return None


def _pending_alignment_request(*, study_root: Path) -> dict[str, Any] | None:
    source_path = Path(study_root).expanduser().resolve() / CONSUMER_REQUEST_SURFACE
    packet = _read_json_object(source_path)
    if _text(packet.get("request_kind")) != ACTION_TYPE and _text(packet.get("action_type")) != ACTION_TYPE:
        return None
    owner_route = _mapping(packet.get("owner_route"))
    owner_reason_contract = _mapping(owner_route.get("owner_reason_contract"))
    reason = (
        _text(packet.get("reason"))
        or _text(owner_route.get("owner_reason"))
        or _text(owner_route.get("failure_signature"))
        or _text(owner_reason_contract.get("reason"))
    )
    if reason != BLOCKED_REASON:
        return None
    if _text(packet.get("request_owner")) != "write" and _text(packet.get("next_executable_owner")) != "write":
        return None
    return {
        "action_type": ACTION_TYPE,
        "blocked_reason": BLOCKED_REASON,
        "reason": reason,
        "owner_result": {},
        "source_request_path": str(source_path),
    }


def _current_claim_alignment_gate(*, study_root: Path) -> dict[str, Any]:
    try:
        from med_autoscience.claim_evidence_alignment import build_claim_evidence_alignment_gate

        return build_claim_evidence_alignment_gate(
            study_root=study_root,
            claim_evidence_map_ref="paper/claim_evidence_map.json",
            evidence_ledger_ref="paper/evidence_ledger.json",
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "surface_kind": "claim_evidence_alignment_gate_v1",
            "status": "blocked",
            "blockers": ["claim_evidence_alignment_gate_unavailable"],
            "error": str(exc),
        }


def _missing_evidence_item_refs(claim_alignment: Mapping[str, Any], owner_result: Mapping[str, Any]) -> list[str]:
    refs = [str(item).strip() for item in owner_result.get("missing_evidence_item_refs") or [] if str(item).strip()]
    if refs:
        return list(dict.fromkeys(refs))
    for claim in claim_alignment.get("claims") or []:
        if not isinstance(claim, Mapping):
            continue
        refs.extend(str(item).strip() for item in claim.get("missing_evidence_item_refs") or [] if str(item).strip())
    return list(dict.fromkeys(refs))


def _work_unit_fingerprint(claim_alignment: Mapping[str, Any]) -> str:
    blockers = ",".join(str(item).strip() for item in claim_alignment.get("blockers") or [] if str(item).strip())
    return f"claim_evidence_alignment_repair::{blockers or 'blocked'}"


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ACTION_TYPE",
    "BLOCKED_REASON",
    "CONSUMER_REQUEST_SURFACE",
    "action_from_ai_reviewer_alignment_blocker",
]
