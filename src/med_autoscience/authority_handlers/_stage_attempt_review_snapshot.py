"""Attempt-local immutable review snapshot closeout helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from opl_framework.stage_attempt_snapshot import (
    ATTEMPT_BINDING_ENV_KEYS as _ATTEMPT_BINDING_ENV_KEYS,
    StageAttemptSnapshotError,
    fingerprint_workspace_source_file,
    inject_snapshot_materialization_into_closeout,
    read_stage_attempt_environment,
    resolve_workspace_source_path,
    verify_workspace_member_source_refs,
)

from ._generation_manifest import (
    build_generation_manifest_v2,
    build_stage_review_input_snapshot_bundle,
)
from ._record_validation import (
    RequestShapeError,
)


BOUNDED_ANALYSIS_STAGE_ID = "bounded_analysis_campaign"
BOUNDED_ANALYSIS_REVIEW_LANE = "statistical"


def _attempt_environment(
    environ: Mapping[str, str] | None,
) -> tuple[Path, dict[str, str]]:
    try:
        return read_stage_attempt_environment(
            expected_stage_id=BOUNDED_ANALYSIS_STAGE_ID,
            agent_id="mas",
            domain_id="medautoscience",
            environ=environ,
        )
    except StageAttemptSnapshotError as error:
        raise RequestShapeError(str(error)) from error


def _workspace_source_path(
    workspace_root: Path,
    source_ref: str,
    field: str,
) -> Path:
    try:
        return resolve_workspace_source_path(workspace_root, source_ref, field)
    except StageAttemptSnapshotError as error:
        raise RequestShapeError(str(error)) from error


def _file_identity(
    workspace_root: Path,
    path: Path,
    field: str,
) -> tuple[int, str]:
    try:
        return fingerprint_workspace_source_file(workspace_root, path, field)
    except StageAttemptSnapshotError as error:
        raise RequestShapeError(str(error)) from error


def _statistical_source_refs(
    *,
    generation_manifest: dict[str, Any],
    workspace_root: Path,
    source_refs_by_member_id: Mapping[str, str],
) -> dict[str, str]:
    scope = next(
        item
        for item in generation_manifest["review_scopes"]
        if item["review_lane"] == BOUNDED_ANALYSIS_REVIEW_LANE
    )
    try:
        return verify_workspace_member_source_refs(
            expected_members=scope["reviewed_members"],
            workspace_root=workspace_root,
            source_refs_by_member_id=source_refs_by_member_id,
            scope_label="statistical review scope",
            artifact_owner_label="MAS",
        )
    except StageAttemptSnapshotError as error:
        raise RequestShapeError(str(error)) from error


def _inject_snapshot_bundle(
    closeout_packet: Mapping[str, Any],
    bundle: dict[str, Any],
    *,
    producer_attempt_ref: str,
) -> dict[str, Any]:
    try:
        return inject_snapshot_materialization_into_closeout(
            closeout_packet,
            request=bundle["review_input_snapshot_materialization_request"],
            owner_authority_ref=bundle["required_closeout_ref_metadata"][0],
            producer_attempt_ref=producer_attempt_ref,
        )
    except StageAttemptSnapshotError as error:
        raise RequestShapeError(str(error)) from error


def finalize_bounded_analysis_producer_snapshot_closeout(
    *,
    closeout_packet: Mapping[str, Any],
    artifacts: list[dict[str, Any]],
    generation_id: str,
    generation_ref: str,
    source_refs_by_member_id: Mapping[str, str],
    clinical_analysis_identity_admission: Mapping[str, Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build and inject one statistical snapshot request for a producer Attempt."""

    workspace_root, authority_issuer = _attempt_environment(environ)
    generation_manifest = build_generation_manifest_v2(
        artifacts=artifacts,
        generation_id=generation_id,
        manifest_scope="analysis_generation",
        clinical_analysis_identity_admission=(
            dict(clinical_analysis_identity_admission)
            if clinical_analysis_identity_admission is not None
            else None
        ),
    )
    statistical_source_refs = _statistical_source_refs(
        generation_manifest=generation_manifest,
        workspace_root=workspace_root,
        source_refs_by_member_id=source_refs_by_member_id,
    )
    bundle = build_stage_review_input_snapshot_bundle(
        stage_id=BOUNDED_ANALYSIS_STAGE_ID,
        artifacts=generation_manifest["artifacts"],
        generation_id=generation_manifest["generation_id"],
        generation_ref=generation_ref,
        workspace_root=str(workspace_root),
        source_refs_by_member_id=statistical_source_refs,
        authority_issuer=authority_issuer,
        clinical_analysis_identity_admission=(
            dict(clinical_analysis_identity_admission)
            if clinical_analysis_identity_admission is not None
            else None
        ),
    )
    if bundle["generation_manifest"] != generation_manifest:
        raise RequestShapeError(
            "stage snapshot bundle changed the frozen generation manifest"
        )
    finalized_closeout = _inject_snapshot_bundle(
        closeout_packet,
        bundle,
        producer_attempt_ref=authority_issuer["stage_attempt_ref"],
    )
    return {
        "surface_kind": "mas_bounded_analysis_producer_snapshot_finalization",
        "schema_version": 1,
        "stage_id": BOUNDED_ANALYSIS_STAGE_ID,
        "review_lane": BOUNDED_ANALYSIS_REVIEW_LANE,
        "snapshot_bundle": bundle,
        "closeout_packet": finalized_closeout,
    }


__all__ = [
    "BOUNDED_ANALYSIS_REVIEW_LANE",
    "BOUNDED_ANALYSIS_STAGE_ID",
    "finalize_bounded_analysis_producer_snapshot_closeout",
]
