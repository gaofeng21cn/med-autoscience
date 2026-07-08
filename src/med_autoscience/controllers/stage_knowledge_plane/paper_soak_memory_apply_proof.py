from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol.workspace_artifacts import workspace_runtime_artifact_path
from med_autoscience.stage_knowledge_contract import (
    PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE,
    SCHEMA_VERSION,
    STAGE_KNOWLEDGE_ROOT,
    authority_boundary,
)


def build_paper_soak_memory_apply_proof_projection(
    *,
    study_id: str,
    stage: str,
    study_root: Path,
    workspace_root: Path,
    stage_packet_path: Path,
    publication_route_memory_pack_root: Path,
    route_memory_refs: object,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_stage_packet_path = Path(stage_packet_path).expanduser().resolve()
    resolved_pack_root = Path(publication_route_memory_pack_root).expanduser().resolve()
    resolved_study_id = _required_text("study_id", study_id)
    readonly_route_memory_refs = _readonly_route_memory_refs(route_memory_refs)
    closeout_proposal_refs = _closeout_proposal_refs(study_root=resolved_study_root)
    router_receipt_refs = _router_receipt_refs(study_root=resolved_study_root)
    writeback_receipt_refs = _workspace_writeback_receipt_refs(pack_root=resolved_pack_root)
    domain_handler_receipt_refs = _domain_handler_dispatch_receipt_refs(
        workspace_root=resolved_workspace_root,
        study_id=resolved_study_id,
    )
    opl_aion_refs = _opl_aion_readonly_receipt_refs(
        router_receipt_refs=router_receipt_refs,
        writeback_receipt_refs=writeback_receipt_refs,
        domain_handler_receipt_refs=domain_handler_receipt_refs,
    )
    missing = _paper_soak_proof_missing_reasons(
        route_memory_refs=readonly_route_memory_refs,
        closeout_proposal_refs=closeout_proposal_refs,
        router_receipt_refs=router_receipt_refs,
        opl_aion_refs=opl_aion_refs,
    )
    input_refs = _dedupe_text(
        [
            str(resolved_stage_packet_path),
            *[ref["ref"] for ref in closeout_proposal_refs if _text(ref.get("ref"))],
            *[ref["ref"] for ref in router_receipt_refs if _text(ref.get("ref"))],
            *[ref["ref"] for ref in writeback_receipt_refs if _text(ref.get("ref"))],
            *[ref["ref"] for ref in domain_handler_receipt_refs if _text(ref.get("ref"))],
        ]
    )
    source_fingerprint = _fingerprint(
        {
            "stage": stage,
            "route_memory_refs": readonly_route_memory_refs,
            "closeout_proposal_refs": closeout_proposal_refs,
            "router_receipt_refs": router_receipt_refs,
            "writeback_receipt_refs": writeback_receipt_refs,
            "domain_handler_receipt_refs": domain_handler_receipt_refs,
        }
    )
    return {
        "surface": PAPER_SOAK_MEMORY_APPLY_PROOF_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "study_id": resolved_study_id,
        "stage": stage,
        "status": "ready" if not missing else "missing",
        "input_refs": input_refs,
        "missing_reasons": missing,
        "stage_entry": {
            "stage_knowledge_packet_ref": str(resolved_stage_packet_path),
            "publication_route_memory_refs": readonly_route_memory_refs,
            "route_memory_ref_count": len(readonly_route_memory_refs),
        },
        "typed_closeout_writeback_proposals": closeout_proposal_refs,
        "mas_router_receipt_refs": router_receipt_refs,
        "workspace_writeback_receipt_refs": writeback_receipt_refs,
        "opl_aion_readonly_receipt_refs": opl_aion_refs,
        "source_fingerprint": source_fingerprint,
        "authority_boundary": authority_boundary(),
        "read_only_display_policy": {
            "projection_owner": "MedAutoScience",
            "consumer_role": "OPL/Aion read-only display",
            "repo_tracks_real_paper_artifacts": False,
            "repo_tracks_memory_body": False,
            "repo_tracks_receipt_instances": False,
            "can_authorize_publication_quality": False,
            "can_write_memory_body": False,
            "can_write_study_truth": False,
            "can_write_artifact_authority": False,
        },
        "idempotency_key": f"paper_soak_memory_apply_proof:{resolved_study_id}:{stage}:{source_fingerprint}",
    }


def _readonly_route_memory_refs(refs: object) -> list[dict[str, Any]]:
    sanitized = []
    for ref in refs:
        sanitized.append(
            {
                "ref_kind": _text(ref.get("ref_kind")) or "workspace_memory_card_ref",
                "memory_id": _text(ref.get("memory_id")),
                "route_family": _text(ref.get("route_family")),
                "route_memory_summary": _text(ref.get("route_memory_summary")),
                "stage_applicability": _text_list(ref.get("stage_applicability")),
                "memory_pack_ref": _text(ref.get("memory_pack_ref")),
                "source_receipt_ref": _text(ref.get("source_receipt_ref")),
                "authority_boundary": _text(ref.get("authority_boundary"))
                or "context_only_not_publication_authority",
            }
        )
    return sanitized


def _closeout_proposal_refs(*, study_root: Path) -> list[dict[str, Any]]:
    refs = []
    root = study_root / STAGE_KNOWLEDGE_ROOT
    for path in sorted(root.glob("*/closeouts/*.json")):
        payload = _read_json(path)
        proposed = _mapping_list(payload.get("proposed_writes"))
        refs.append(
            {
                "ref_kind": "stage_memory_closeout_packet",
                "ref": str(path),
                "stage": _text(payload.get("stage")),
                "idempotency_key": _text(payload.get("idempotency_key")),
                "source_fingerprint": _text(payload.get("source_fingerprint")),
                "proposed_write_count": len(proposed),
                "proposed_write_refs": [
                    {
                        "write_id": _text(item.get("write_id")),
                        "source_category": _text(item.get("source_category")),
                        "destination": _text(item.get("destination")),
                        "owner_target": _text(item.get("owner_target")),
                    }
                    for item in proposed
                ],
                "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
                "body_included": False,
            }
        )
    return refs


def _router_receipt_refs(*, study_root: Path) -> list[dict[str, Any]]:
    refs = []
    receipt_root = study_root / STAGE_KNOWLEDGE_ROOT / "memory_write_router_receipts"
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        refs.append(
            {
                "ref_kind": "memory_write_router_receipt",
                "ref": str(path),
                "stage": _text(payload.get("stage")),
                "status": _text(payload.get("status")),
                "idempotency_key": _text(payload.get("idempotency_key")),
                "accepted_write_refs": _receipt_write_refs(payload.get("accepted_writes")),
                "rejected_write_refs": _receipt_write_refs(payload.get("rejected_writes")),
                "typed_blocker_count": len(_mapping_list(payload.get("typed_blockers"))),
                "body_included": False,
            }
        )
    return refs


def _receipt_write_refs(value: object) -> list[dict[str, Any]]:
    return [
        {
            "write_id": _text(item.get("write_id")),
            "destination": _text(item.get("destination")),
            "owner_target": _text(item.get("owner_target")),
            "status": "rejected" if _text(item.get("reason")) else "accepted",
            "reason": _text(item.get("reason")),
            "proposal_ref": _text(item.get("proposal_ref")),
            "receipt_ref": _text(item.get("receipt_ref")),
        }
        for item in _mapping_list(value)
    ]


def _workspace_writeback_receipt_refs(*, pack_root: Path) -> list[dict[str, Any]]:
    refs = []
    receipt_root = pack_root / "writeback_receipts"
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        refs.append(
            {
                "ref_kind": "publication_route_memory_writeback_receipt",
                "ref": str(path),
                "status": _text(payload.get("status")),
                "idempotency_key": _text(payload.get("idempotency_key")),
                "accepted_count": len(_mapping_list(payload.get("accepted_writes"))),
                "rejected_count": len(_mapping_list(payload.get("rejected_writes"))),
                "body_included": False,
            }
        )
    return refs


def _domain_handler_dispatch_receipt_refs(*, workspace_root: Path, study_id: str) -> list[dict[str, Any]]:
    refs = []
    receipt_root = workspace_runtime_artifact_path(workspace_root, "opl_family_domain_handler", "dispatch_receipts")
    for path in sorted(receipt_root.glob("*.json")):
        payload = _read_json(path)
        dispatch = payload.get("dispatch") if isinstance(payload.get("dispatch"), Mapping) else {}
        receipt_study_id = _text(dispatch.get("study_id"))
        if receipt_study_id and receipt_study_id != study_id:
            continue
        refs.append(
            {
                "ref_kind": "mas_family_domain_handler_dispatch_receipt",
                "ref": str(path),
                "task_id": _text(payload.get("task_id")),
                "task_kind": _text(payload.get("task_kind")),
                "accepted": payload.get("accepted") is True,
                "reason": _text(payload.get("reason")),
                "study_id": receipt_study_id,
                "body_included": False,
            }
        )
    return refs


def _opl_aion_readonly_receipt_refs(
    *,
    router_receipt_refs: Sequence[Mapping[str, Any]],
    writeback_receipt_refs: Sequence[Mapping[str, Any]],
    domain_handler_receipt_refs: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    refs = []
    for source in (*router_receipt_refs, *writeback_receipt_refs, *domain_handler_receipt_refs):
        ref = _text(source.get("ref"))
        if not ref:
            continue
        refs.append(
            {
                "ref_kind": _text(source.get("ref_kind")),
                "ref": ref,
                "status": _text(source.get("status")) or ("accepted" if source.get("accepted") is True else ""),
                "display_role": "receipt_ref_only",
                "consumer": "OPL/Aion",
                "body_included": False,
                "authority_boundary": "read_only_display_not_mas_truth_authority",
            }
        )
    return refs


def _paper_soak_proof_missing_reasons(
    *,
    route_memory_refs: Sequence[Mapping[str, Any]],
    closeout_proposal_refs: Sequence[Mapping[str, Any]],
    router_receipt_refs: Sequence[Mapping[str, Any]],
    opl_aion_refs: Sequence[Mapping[str, Any]],
) -> list[str]:
    missing = []
    if not route_memory_refs:
        missing.append("missing_stage_entry_route_memory_refs")
    if not closeout_proposal_refs:
        missing.append("missing_typed_closeout_writeback_proposal")
    if not router_receipt_refs:
        missing.append("missing_mas_memory_router_receipt_ref")
    if not opl_aion_refs:
        missing.append("missing_opl_aion_readonly_receipt_refs")
    return missing


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


def _dedupe_text(items: Sequence[str]) -> list[str]:
    return list(dict.fromkeys([item for item in items if item]))


def _required_text(field: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    return text


def _fingerprint(payload: object) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


__all__ = ["build_paper_soak_memory_apply_proof_projection"]
