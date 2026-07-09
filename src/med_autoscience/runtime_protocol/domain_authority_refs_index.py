from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol.workspace_artifacts import workspace_runtime_artifact_path


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_domain_authority_refs_source"
DEFAULT_SOURCE_REF = "opl_state_index_source_adapter/authority_refs_source.json"
AUTHORITY_REF_FAMILIES = (
    "authority_ref_metadata",
    "archive_refs",
    "owner_route_receipts",
    "dispatch_receipts",
    "paper_progress_transition_refs",
    "stage_artifact_delta_refs",
)

# Imported by the OPL-family projection until that projection owns its source vocabulary.
OPL_FAMILY_ADAPTER_SOURCE_TABLES = AUTHORITY_REF_FAMILIES


def domain_authority_refs_index_contract() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "role": "body_free_domain_authority_ref_source_adapter",
        "owner": "med-autoscience",
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
        "source_adapter_ref": f"runtime/artifacts/{DEFAULT_SOURCE_REF}",
        "source_families": list(AUTHORITY_REF_FAMILIES),
        "local_persistence": "absent",
        "derived_index_rebuildable": True,
        "body_included": False,
        "authority_boundary": _refs_only_authority_boundary(),
        "retired_surfaces": [
            "runtime:mas-refs-only-state-index-pilot-retired",
            "MAS-local authority refs persistence",
            "MAS-local authority refs inspection",
        ],
        "replacement_refs": [
            "src/med_autoscience/controllers/opl_state_index_kernel.py",
            "contracts/opl-framework/state-index-kernel-contract.json",
            "contracts/runtime/mas-runtime-surface-retirement-inventory.json#/surfaces/domain_authority_refs_index",
        ],
    }


def quest_authority_refs_index_path(quest_root: Path) -> Path:
    return (
        Path(quest_root).expanduser().resolve()
        / "artifacts"
        / "runtime"
        / DEFAULT_SOURCE_REF
    )


def workspace_authority_refs_index_path(workspace_root: Path) -> Path:
    return workspace_runtime_artifact_path(workspace_root, DEFAULT_SOURCE_REF)


def record_archive_ref(
    *,
    quest_root: Path,
    archive_ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    archive_path = Path(_require_text("archive_ref.archive_path", archive_ref.get("archive_path")))
    return _source_adapter_result(
        family="archive_refs",
        scope="quest",
        source_path=archive_path,
        payload=archive_ref,
        adapter_path=db_path or quest_authority_refs_index_path(quest_root),
    )


def record_owner_route_receipt(
    *,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    _require_text("receipt.study_id", receipt.get("study_id"))
    _require_text("receipt.idempotency_key", receipt.get("idempotency_key"))
    return _source_adapter_result(
        family="owner_route_receipts",
        scope="study",
        source_path=receipt_path,
        payload=receipt,
        adapter_path=db_path or _workspace_source_path(study_root),
    )


def record_dispatch_receipt(
    *,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    _require_text("receipt.study_id", receipt.get("study_id"))
    return _source_adapter_result(
        family="dispatch_receipts",
        scope="quest",
        source_path=receipt_path,
        payload=receipt,
        adapter_path=db_path or quest_authority_refs_index_path(quest_root),
    )


def record_paper_progress_transition_ref(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _record_study_receipt_ref(
        family="paper_progress_transition_refs",
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        adapter_path=db_path,
    )


def record_stage_artifact_delta_ref(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _record_study_receipt_ref(
        family="stage_artifact_delta_refs",
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        adapter_path=db_path,
    )


def _record_study_receipt_ref(
    *,
    family: str,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    adapter_path: Path | None,
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
    result = _source_adapter_result(
        family=family,
        scope="study",
        source_path=receipt_path,
        payload=receipt,
        adapter_path=adapter_path or _workspace_source_path(study_root),
    )
    result.update(
        {
            "quest_root": str(Path(quest_root).expanduser().resolve()),
            "started_worker": False,
            "worker_start_ref": None,
            "outbox_record": False,
        }
    )
    return result


def _source_adapter_result(
    *,
    family: str,
    scope: str,
    source_path: Path,
    payload: Mapping[str, Any],
    adapter_path: Path,
) -> dict[str, Any]:
    if family not in AUTHORITY_REF_FAMILIES:
        raise ValueError(f"unsupported authority ref family: {family}")
    resolved_source_path = Path(source_path).expanduser().resolve()
    resolved_adapter_path = Path(adapter_path).expanduser().resolve()
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "body_free_ref_source_encoded",
        "scope": scope,
        "source_family": family,
        "source_path": str(resolved_source_path),
        "source_ref": str(resolved_source_path),
        "payload_sha256": _sha256(payload),
        "source_adapter_path": str(resolved_adapter_path),
        "body_included": False,
        "derived_index_rebuildable": True,
        "local_persistence": "absent",
        "authority_boundary": _refs_only_authority_boundary(),
    }


def _refs_only_authority_boundary() -> dict[str, Any]:
    return {
        "refs_only": True,
        "body_included": False,
        "stores_domain_truth": False,
        "started_worker": False,
        "outbox_record": False,
        "can_generate_next_action_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "mas_state_index_authority": False,
        "state_index_owner": "one-person-lab",
    }


def _workspace_source_path(study_root: Path) -> Path:
    resolved = Path(study_root).expanduser().resolve()
    try:
        workspace_root = resolved.parents[1]
    except IndexError as exc:
        raise ValueError("study_root must be nested under a workspace studies directory") from exc
    return workspace_authority_refs_index_path(workspace_root)


def _sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require_text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


__all__ = [
    "AUTHORITY_REF_FAMILIES",
    "DEFAULT_SOURCE_REF",
    "OPL_FAMILY_ADAPTER_SOURCE_TABLES",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "domain_authority_refs_index_contract",
    "quest_authority_refs_index_path",
    "record_archive_ref",
    "record_dispatch_receipt",
    "record_owner_route_receipt",
    "record_paper_progress_transition_ref",
    "record_stage_artifact_delta_ref",
    "workspace_authority_refs_index_path",
]
