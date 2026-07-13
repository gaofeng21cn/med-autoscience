from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_opl_state_index_source_adapter"
SCHEMA_VERSION = 1
SOURCE_ADAPTER_STATUS = "opl_state_index_source_adapter_emitted"
SOURCE_ADAPTER_ROLE = "opl_state_index_source_adapter_for_domain_authority_refs"
REPLACEMENT_OWNER_SURFACE = "one-person-lab StateIndexKernel"
STATE_INDEX_SOURCE_ADAPTER_REF = (
    "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json"
)
SOURCE_FAMILIES = (
    "authority_ref_metadata",
    "archive_refs",
    "owner_route_receipts",
    "runtime_receipt_refs",
    "stage_artifact_delta_refs",
)


def emit_owner_route_receipt_source(
    *,
    receipt: Mapping[str, Any],
    receipt_path: Path,
) -> dict[str, Any]:
    _require_text("receipt.study_id", receipt.get("study_id"))
    _require_text("receipt.idempotency_key", receipt.get("idempotency_key"))
    return _source_result(
        family="owner_route_receipts",
        scope="study",
        source_path=receipt_path,
        payload=receipt,
    )


def emit_stage_artifact_delta_source(
    *,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
) -> dict[str, Any]:
    return _study_receipt_source(
        family="stage_artifact_delta_refs",
        study_root=study_root,
        receipt=receipt,
        receipt_path=receipt_path,
    )


def normalize_state_index_refs(
    refs: object,
) -> list[dict[str, str]]:
    if not isinstance(refs, Sequence) or isinstance(refs, (str, bytes)):
        return []
    normalized: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for raw in refs:
        if not isinstance(raw, Mapping):
            continue
        source_ref = str(raw.get("source_ref") or "").strip()
        payload_sha256 = str(raw.get("payload_sha256") or "").strip()
        if not source_ref or not payload_sha256:
            continue
        key = (source_ref, payload_sha256)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(
            {
                "source_ref": source_ref,
                "payload_sha256": payload_sha256,
                "source_family": str(raw.get("source_family") or "stage_folder_refs").strip(),
                "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
            }
        )
    return normalized


def source_adapter_contract() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "active_caller_adapter",
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "mas_role": SOURCE_ADAPTER_ROLE,
        "source_families": list(SOURCE_FAMILIES),
        "source_adapter_manifest_ref": STATE_INDEX_SOURCE_ADAPTER_REF,
        "local_persistence": "absent",
        "body_included": False,
        "authority_boundary": _authority_boundary(),
    }


def source_adapter_manifest() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "source_adapter_manifest_projected",
        "manifest_ref": STATE_INDEX_SOURCE_ADAPTER_REF,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "source_adapter_role": SOURCE_ADAPTER_ROLE,
        "source_families": list(SOURCE_FAMILIES),
        "local_persistence": "absent",
        "body_included": False,
        "authority_boundary": _authority_boundary(),
    }


def _study_receipt_source(
    *,
    family: str,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
) -> dict[str, Any]:
    for field in (
        "receipt_id",
        "study_id",
        "idempotency_key",
        "intent_fingerprint",
        "source_fingerprint",
        "receipt_status",
        "recorded_at",
    ):
        _require_text(f"receipt.{field}", receipt.get(field))
    result = _source_result(
        family=family,
        scope="study",
        source_path=receipt_path,
        payload=receipt,
    )
    result.update(
        {
            "study_root": str(Path(study_root).expanduser().resolve()),
            "started_worker": False,
            "worker_start_ref": None,
            "outbox_record": False,
        }
    )
    return result


def _source_result(
    *,
    family: str,
    scope: str,
    source_path: Path,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if family not in SOURCE_FAMILIES:
        raise ValueError(f"unsupported authority ref family: {family}")
    resolved_source_path = Path(source_path).expanduser().resolve()
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": SOURCE_ADAPTER_STATUS,
        "scope": scope,
        "source_family": family,
        "source_path": str(resolved_source_path),
        "source_ref": str(resolved_source_path),
        "payload_sha256": _sha256(payload),
        "manifest_ref": STATE_INDEX_SOURCE_ADAPTER_REF,
        "source_adapter_role": SOURCE_ADAPTER_ROLE,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "body_included": False,
        "derived_index_rebuildable": True,
        "local_persistence": "absent",
        "opl_state_index_kernel_required": True,
        "authority_boundary": _authority_boundary(),
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_state_index_source_adapter_boundary",
        "refs_only": True,
        "body_included": False,
        "rebuildable": True,
        "started_worker": False,
        "outbox_record": False,
        "can_start_worker": False,
        "can_create_outbox_record": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_generate_next_action_authority": False,
        "can_authorize_currentness": False,
        "can_authorize_provider_attempt": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "mas_state_index_authority": False,
        "state_index_owner": "one-person-lab",
    }


def _sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


__all__ = [
    "REPLACEMENT_OWNER_SURFACE",
    "SCHEMA_VERSION",
    "SOURCE_ADAPTER_ROLE",
    "SOURCE_ADAPTER_STATUS",
    "SOURCE_FAMILIES",
    "SURFACE_KIND",
    "STATE_INDEX_SOURCE_ADAPTER_REF",
    "emit_owner_route_receipt_source",
    "emit_stage_artifact_delta_source",
    "normalize_state_index_refs",
    "source_adapter_contract",
    "source_adapter_manifest",
]
