from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import domain_authority_refs_index

SURFACE_KIND = "mas_opl_state_index_source_adapter"
SCHEMA_VERSION = 1
SOURCE_ADAPTER_STATUS = "opl_state_index_source_adapter_emitted"
SOURCE_ADAPTER_ROLE = "opl_state_index_source_adapter_for_domain_authority_refs"
REPLACEMENT_OWNER_SURFACE = "one-person-lab StateIndexKernel"
STATE_INDEX_SOURCE_ADAPTER_REF = "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json"


def workspace_authority_refs_index_path(workspace_root: Path) -> Path:
    return domain_authority_refs_index.workspace_authority_refs_index_path(workspace_root)


def quest_authority_refs_index_path(quest_root: Path) -> Path:
    return domain_authority_refs_index.quest_authority_refs_index_path(quest_root)


def emit_archive_ref_source(
    *,
    quest_root: Path,
    archive_ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _source_result(
        domain_authority_refs_index.record_archive_ref(
            quest_root=quest_root,
            archive_ref=archive_ref,
            db_path=db_path,
        )
    )


def emit_owner_route_receipt_source(
    *,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _source_result(
        domain_authority_refs_index.record_owner_route_receipt(
            study_root=study_root,
            receipt=receipt,
            receipt_path=receipt_path,
            db_path=db_path,
        )
    )


def emit_dispatch_receipt_source(
    *,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _source_result(
        domain_authority_refs_index.record_dispatch_receipt(
            quest_root=quest_root,
            receipt=receipt,
            receipt_path=receipt_path,
            db_path=db_path,
        )
    )


def emit_paper_progress_transition_source(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _source_result(
        domain_authority_refs_index.record_paper_progress_transition_ref(
            study_root=study_root,
            quest_root=quest_root,
            receipt=receipt,
            receipt_path=receipt_path,
            db_path=db_path,
        )
    )


def emit_stage_artifact_delta_source(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return _source_result(
        domain_authority_refs_index.record_stage_artifact_delta_ref(
            study_root=study_root,
            quest_root=quest_root,
            receipt=receipt,
            receipt_path=receipt_path,
            db_path=db_path,
        )
    )


def source_adapter_contract() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "active_caller_adapter",
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "mas_role": SOURCE_ADAPTER_ROLE,
        "legacy_sqlite_helper": (
            "med_autoscience.runtime_protocol.domain_authority_refs_index"
        ),
        "sqlite_persistence_allowed": False,
        "sqlite_persistence_parameter_exposed": False,
        "domain_authority_refs_index_persist_sqlite_allowed_use": (
            "explicit_history_replay_or_local_refs_inspection_only"
        ),
        "active_caller_status": "repo_active_callers_migrated_to_opl_state_index_source_adapter",
        "active_caller_effect": "opl_state_index_source_adapter_emitted_no_sqlite_persistence",
        "active_caller_retains_surface": False,
        "active_caller_retains_authority": False,
        "active_caller_retains_runtime_authority": False,
        "source_adapter_manifest_ref": STATE_INDEX_SOURCE_ADAPTER_REF,
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
        "live_takeover_required_before_physical_delete": True,
        "legacy_domain_authority_refs_index_role": (
            "explicit_history_replay_or_local_refs_inspection_only"
        ),
        "authority_boundary": _authority_boundary(),
    }


def source_adapter_manifest() -> dict[str, Any]:
    contract = source_adapter_contract()
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "source_adapter_manifest_projected",
        "manifest_ref": STATE_INDEX_SOURCE_ADAPTER_REF,
        "replacement_owner_surface": REPLACEMENT_OWNER_SURFACE,
        "source_adapter_role": SOURCE_ADAPTER_ROLE,
        "source_tables": list(domain_authority_refs_index.AUTHORITY_REF_TABLES),
        "forbidden_legacy_tables": list(domain_authority_refs_index.LEGACY_TABLE_POLICY),
        "legacy_sqlite_helper": contract["legacy_sqlite_helper"],
        "legacy_sqlite_helper_role": contract["legacy_domain_authority_refs_index_role"],
        "sqlite_persistence_allowed": False,
        "sqlite_persistence_parameter_exposed": False,
        "sqlite_payload_read": False,
        "sqlite_inspection_read": False,
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
        "live_takeover_required_before_physical_delete": True,
        "authority_boundary": _authority_boundary(),
    }


def _source_result(result: Mapping[str, Any]) -> dict[str, Any]:
    emitted = dict(result)
    emitted["surface_kind"] = SURFACE_KIND
    emitted["legacy_domain_authority_refs_surface_kind"] = result.get("surface_kind")
    emitted["status"] = SOURCE_ADAPTER_STATUS
    emitted["source_adapter_role"] = SOURCE_ADAPTER_ROLE
    emitted["replacement_owner_surface"] = REPLACEMENT_OWNER_SURFACE
    emitted["opl_state_index_kernel_required"] = True
    emitted["sqlite_persisted"] = False
    emitted["sqlite_persistence_allowed"] = False
    emitted["sqlite_persistence_parameter_exposed"] = False
    emitted["authority_boundary"] = _authority_boundary()
    return emitted


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
        "can_authorize_provider_admission": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "mas_state_index_authority": False,
        "state_index_owner": "one-person-lab",
    }


__all__ = [
    "REPLACEMENT_OWNER_SURFACE",
    "SCHEMA_VERSION",
    "SOURCE_ADAPTER_ROLE",
    "SOURCE_ADAPTER_STATUS",
    "SURFACE_KIND",
    "STATE_INDEX_SOURCE_ADAPTER_REF",
    "emit_archive_ref_source",
    "emit_dispatch_receipt_source",
    "emit_owner_route_receipt_source",
    "emit_paper_progress_transition_source",
    "emit_stage_artifact_delta_source",
    "quest_authority_refs_index_path",
    "source_adapter_contract",
    "source_adapter_manifest",
    "workspace_authority_refs_index_path",
]
