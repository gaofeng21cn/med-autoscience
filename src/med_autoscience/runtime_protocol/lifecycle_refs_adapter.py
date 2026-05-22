from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .runtime_lifecycle_contract import (
    DEFAULT_DB_FILENAME,
    SCHEMA_VERSION,
    SURFACE_KIND,
)
from .lifecycle_refs_adapter_parts import (
    family_adoption,
    lineage_indexes,
    runtime_record_indexes,
    report_payloads,
    lifecycle_ref_indexes,
    sqlite_refs_index,
)

_connect = sqlite_refs_index.connect
_ensure_schema = sqlite_refs_index.ensure_schema
_index_result = sqlite_refs_index.index_result
_record_report_index_row = sqlite_refs_index.record_report_index_row
_resolve_db_path = sqlite_refs_index.resolve_db_path


def quest_lifecycle_store_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / "artifacts" / "runtime" / DEFAULT_DB_FILENAME


def workspace_lifecycle_store_path(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / "artifacts" / "runtime" / DEFAULT_DB_FILENAME


def record_domain_health_diagnostic_state(
    *,
    quest_root: Path,
    payload: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return runtime_record_indexes.record_watch_state(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path,
        index_result=_index_result,
        quest_root=quest_root,
        payload=payload,
        db_path=db_path,
    )


def record_runtime_report(
    *,
    quest_root: Path,
    report_group: str,
    timestamp: str,
    report: Mapping[str, Any],
    json_path: Path,
    md_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return runtime_record_indexes.record_runtime_report(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path,
        index_result=_index_result,
        record_report_index_row=_record_report_index_row,
        quest_root=quest_root,
        report_group=report_group,
        timestamp=timestamp,
        report=report,
        json_path=json_path,
        md_path=md_path,
        db_path=db_path,
    )


def record_workspace_storage_audit(
    *,
    workspace_root: Path,
    report: Mapping[str, Any],
    report_path: Path,
    latest_report_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return runtime_record_indexes.record_workspace_storage_audit(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        record_report_index_row=_record_report_index_row,
        workspace_root=workspace_root,
        report=report,
        report_path=report_path,
        latest_report_path=latest_report_path,
        db_path=db_path,
    )


def record_runtime_event(
    *,
    quest_root: Path,
    event: Mapping[str, Any],
    artifact_path: Path,
    latest_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return runtime_record_indexes.record_runtime_event(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path,
        index_result=_index_result,
        quest_root=quest_root,
        event=event,
        artifact_path=artifact_path,
        latest_path=latest_path,
        db_path=db_path,
    )


def record_archive_ref(
    *,
    quest_root: Path,
    archive_ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return runtime_record_indexes.record_archive_ref(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path,
        index_result=_index_result,
        quest_root=quest_root,
        archive_ref=archive_ref,
        db_path=db_path,
    )


def record_lineage_node(
    *,
    workspace_root: Path,
    node: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_lineage_node(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        node=node,
        db_path=db_path,
    )


def record_lineage_edge(
    *,
    workspace_root: Path,
    edge: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_lineage_edge(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        edge=edge,
        db_path=db_path,
    )


def record_workspace_allocation(
    *,
    workspace_root: Path,
    allocation: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_workspace_allocation(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        allocation=allocation,
        db_path=db_path,
    )


def record_runtime_snapshot(
    *,
    workspace_root: Path,
    snapshot: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_runtime_snapshot(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        snapshot=snapshot,
        db_path=db_path,
    )


def record_snapshot_file_ref(
    *,
    workspace_root: Path,
    ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_snapshot_file_ref(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        ref=ref,
        db_path=db_path,
    )


def record_revision_diff(
    *,
    workspace_root: Path,
    diff: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_revision_diff(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        diff=diff,
        db_path=db_path,
    )


def record_canvas_projection(
    *,
    workspace_root: Path,
    projection: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_canvas_projection(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        projection=projection,
        db_path=db_path,
    )


def record_study_macro_state_snapshot(
    *,
    study_root: Path,
    snapshot: Mapping[str, Any],
    snapshot_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lifecycle_ref_indexes.record_study_macro_state_snapshot(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        study_root=study_root,
        snapshot=snapshot,
        snapshot_path=snapshot_path,
        db_path=db_path,
    )


def record_owner_route_receipt(
    *,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lifecycle_ref_indexes.record_owner_route_receipt(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        study_root=study_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
    )


def record_dispatch_receipt(
    *,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lifecycle_ref_indexes.record_dispatch_receipt(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path,
        index_result=_index_result,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
    )


def record_turn_receipt(*, quest_root: Path, receipt: Mapping[str, Any], receipt_path: Path, db_path: Path | None = None) -> dict[str, Any]:
    return lifecycle_ref_indexes.record_turn_receipt(
        connect=_connect, ensure_schema=_ensure_schema, resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path, index_result=_index_result,
        quest_root=quest_root, receipt=receipt, receipt_path=receipt_path, db_path=db_path,
    )


def record_paper_work_unit_receipt(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lifecycle_ref_indexes.record_paper_work_unit_receipt(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
    )


def record_surface_ref(
    *,
    object_root: Path,
    object_scope: str,
    ref: Mapping[str, Any],
    ref_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lifecycle_ref_indexes.record_surface_ref(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        object_root=object_root,
        object_scope=object_scope,
        ref=ref,
        ref_path=ref_path,
        db_path=db_path,
    )


def build_opl_family_adoption_surface(
    *,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return family_adoption.build_opl_family_adoption_surface(
        connect=_connect,
        ensure_schema=_ensure_schema,
        inspect_lifecycle_store=inspect_lifecycle_store,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        workspace_root=workspace_root,
        db_path=db_path,
    )


def build_product_entry_adoption_projection(
    *,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return family_adoption.build_product_entry_adoption_projection(
        workspace_root=workspace_root,
        db_path=db_path,
    )


def build_family_stage_control_plane(*, family_action_catalog: Mapping[str, Any]) -> dict[str, Any]:
    return family_adoption.build_family_stage_control_plane(
        family_action_catalog=family_action_catalog,
    )


def build_domain_memory_descriptor() -> dict[str, Any]:
    return family_adoption.build_domain_memory_descriptor()


def inspect_lifecycle_store(db_path: Path) -> dict[str, Any]:
    return sqlite_refs_index.inspect_store(db_path)


def read_lifecycle_records(db_path: Path, table: str) -> list[dict[str, Any]]:
    return lineage_indexes.read_lifecycle_records(
        connect=_connect,
        ensure_schema=_ensure_schema,
        db_path=db_path,
        table=table,
    )


__all__ = [
    "DEFAULT_DB_FILENAME",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_domain_memory_descriptor",
    "build_opl_family_adoption_surface",
    "build_family_stage_control_plane",
    "build_product_entry_adoption_projection",
    "inspect_lifecycle_store",
    "quest_lifecycle_store_path",
    "record_archive_ref",
    "read_lifecycle_records",
    "record_canvas_projection",
    "record_dispatch_receipt",
    "record_lineage_edge",
    "record_lineage_node",
    "record_owner_route_receipt",
    "record_paper_work_unit_receipt",
    "record_revision_diff",
    "record_runtime_event",
    "record_runtime_report",
    "record_study_macro_state_snapshot",
    "record_turn_receipt",
    "record_runtime_snapshot",
    "record_snapshot_file_ref",
    "record_surface_ref",
    "record_domain_health_diagnostic_state",
    "record_workspace_allocation",
    "record_workspace_storage_audit",
    "workspace_lifecycle_store_path",
]
