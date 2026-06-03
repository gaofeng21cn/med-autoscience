from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


ALLOWED_PAYLOAD_ROLES = {
    "ref",
    "locator",
    "cursor",
    "checksum",
    "content_hash",
    "source_fingerprint",
    "idempotency_key",
    "receipt_ref",
    "typed_blocker_ref",
    "restore_proof_ref",
    "bounded_preview_hash",
}

FORBIDDEN_PAYLOAD_ROLES = {
    "study_truth_body",
    "publication_eval_body",
    "controller_decision_body",
    "manuscript_body",
    "paper_package_body",
    "evidence_ledger_body",
    "review_ledger_body",
    "memory_body",
    "artifact_body",
    "publication_quality_verdict_body",
    "artifact_authority_verdict_body",
    "owner_receipt_authority",
}


def build_state_index_kernel_rows(
    *,
    stage_artifact_index: Mapping[str, Any],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for stage in _mapping_items(stage_artifact_index.get("stages")):
        rows.extend(_rows_for_stage(stage))
    violations = [
        row
        for row in rows
        if row["payload_role"] not in ALLOWED_PAYLOAD_ROLES
        or row["payload_role"] in FORBIDDEN_PAYLOAD_ROLES
        or row.get("body_included") is True
    ]
    return {
        "surface_kind": "opl_state_index_kernel_rows_projection",
        "schema_version": 1,
        "index_authority": "derived_refs_only_rebuildable_read_model",
        "source_of_truth": "physical_stage_folder_files_mas_owned_truth_files_and_domain_owner_receipts",
        "row_count": len(rows),
        "rows": rows,
        "payload_policy": {
            "allowed_payload_roles": sorted(ALLOWED_PAYLOAD_ROLES),
            "forbidden_payload_roles": sorted(FORBIDDEN_PAYLOAD_ROLES),
            "body_included": False,
            "sqlite_record_counts_as_stage_complete": False,
        },
        "violations": violations,
        "status": "ready_for_opl_sidecar_ingest" if not violations else "blocked_by_forbidden_payload",
        "authority_boundary": _authority_boundary(),
    }


def rebuild_state_index_kernel_report(
    *,
    stage_artifact_index: Mapping[str, Any],
    previous_rows: Iterable[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    current = build_state_index_kernel_rows(stage_artifact_index=stage_artifact_index)
    previous_keys = {_row_key(row) for row in (previous_rows or [])}
    current_keys = {_row_key(row) for row in current["rows"]}
    return {
        "surface_kind": "opl_state_index_kernel_rebuild_report",
        "schema_version": 1,
        "status": current["status"],
        "derived_index_rebuildable": True,
        "row_count": current["row_count"],
        "added_row_keys": sorted(current_keys - previous_keys),
        "removed_row_keys": sorted(previous_keys - current_keys),
        "unchanged_row_keys": sorted(previous_keys & current_keys),
        "rows_projection": current,
        "authority_boundary": _authority_boundary(),
    }


def _rows_for_stage(stage: Mapping[str, Any]) -> list[dict[str, Any]]:
    stage_id = _text(stage.get("stage_id")) or "unknown-stage"
    rows: list[dict[str, Any]] = []
    stage_folder = _mapping(stage.get("stage_folder_contract"))
    artifact_classification = _mapping(stage.get("artifact_classification"))
    physical_kernel = _mapping(stage.get("physical_stage_folder_kernel"))
    rows.extend(
        _row(stage_id=stage_id, family="stage_folder", role="ref", key=key, value=value)
        for key, value in (
            ("stage_folder_ref", stage_folder.get("stage_folder_ref")),
            ("stage_json_ref", physical_kernel.get("stage_json_ref")),
            ("attempt_json_ref", physical_kernel.get("attempt_json_ref")),
            ("manifest_ref", stage_folder.get("manifest_ref")),
            ("receipt_ref", stage_folder.get("receipt_ref")),
            ("current_pointer_ref", stage_folder.get("current_pointer_ref")),
        )
        if _text(value) is not None
    )
    rows.extend(
        _row(stage_id=stage_id, family="artifact", role="ref", key="current_output", value=value)
        for value in artifact_classification.get("current") or []
        if _text(value) is not None
    )
    for family, role, values in (
        ("artifact_hash", "content_hash", artifact_classification.get("manifest_hash_refs")),
        ("receipt_hash", "checksum", artifact_classification.get("receipt_hash_refs")),
        ("owner_receipt", "receipt_ref", artifact_classification.get("owner_receipt_refs")),
        ("typed_blocker", "typed_blocker_ref", artifact_classification.get("typed_blocker_refs")),
        ("decision_receipt", "receipt_ref", artifact_classification.get("decision_receipt_refs")),
        ("restore", "restore_proof_ref", _mapping(artifact_classification.get("retention")).get("restore_refs")),
    ):
        rows.extend(_rows_from_values(stage_id=stage_id, family=family, role=role, values=values))
    return rows


def _rows_from_values(
    *,
    stage_id: str,
    family: str,
    role: str,
    values: object,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, item in enumerate(values if isinstance(values, list | tuple | set) else []):
        if isinstance(item, Mapping):
            value = _text(item.get("path")) or _text(item.get("ref")) or _text(item.get("sha256"))
            metadata = {
                key: str(val)
                for key, val in item.items()
                if isinstance(val, str) and key in {"path", "sha256", "kind", "ref"}
            }
        else:
            value = _text(item)
            metadata = {}
        if value is not None:
            result.append(
                _row(
                    stage_id=stage_id,
                    family=family,
                    role=role,
                    key=f"{family}:{index}",
                    value=value,
                    metadata=metadata,
                )
            )
    return result


def _row(
    *,
    stage_id: str,
    family: str,
    role: str,
    key: str,
    value: object,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "stage_id": stage_id,
        "row_family": family,
        "row_key": key,
        "payload_role": role,
        "ref": str(value),
        "metadata": dict(metadata or {}),
        "body_included": False,
    }


def _row_key(row: Mapping[str, Any]) -> str:
    return "|".join(
        [
            str(row.get("stage_id") or ""),
            str(row.get("row_family") or ""),
            str(row.get("row_key") or ""),
            str(row.get("ref") or ""),
        ]
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_items(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _authority_boundary() -> dict[str, bool]:
    return {
        "mas_can_write_opl_state_index_kernel": False,
        "mas_can_own_generic_sqlite_sidecar": False,
        "sqlite_record_counts_as_stage_complete": False,
        "opl_can_write_mas_truth": False,
        "opl_can_authorize_publication_quality": False,
        "opl_can_authorize_artifact_mutation": False,
    }


__all__ = [
    "ALLOWED_PAYLOAD_ROLES",
    "FORBIDDEN_PAYLOAD_ROLES",
    "build_state_index_kernel_rows",
    "rebuild_state_index_kernel_report",
]
