"""Attempt-local immutable review snapshot closeout helpers."""

from __future__ import annotations

import hashlib
import os
from collections.abc import Mapping
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from ._generation_manifest import (
    build_generation_manifest_v2,
    build_stage_review_input_snapshot_bundle,
)
from ._record_validation import (
    RequestShapeError,
    mapping,
    sequence,
    text,
)


BOUNDED_ANALYSIS_STAGE_ID = "bounded_analysis_campaign"
BOUNDED_ANALYSIS_REVIEW_LANE = "statistical"
_ATTEMPT_BINDING_ENV_KEYS = (
    "OPL_STAGE_ATTEMPT_REF",
    "OPL_EXECUTION_CONTENT_BINDING_SHA256",
    "OPL_PACKAGE_USE_BOUNDARY_ID",
    "OPL_ROOT_PACKAGE_ID",
    "OPL_ROOT_PACKAGE_CONTENT_DIGEST",
)


def _attempt_environment(
    environ: Mapping[str, str] | None,
) -> tuple[Path, dict[str, str]]:
    source = os.environ if environ is None else environ
    stage_id = text(source.get("OPL_STAGE_ID"), "environment.OPL_STAGE_ID")
    if stage_id != BOUNDED_ANALYSIS_STAGE_ID:
        raise RequestShapeError(
            "environment.OPL_STAGE_ID must be bounded_analysis_campaign"
        )
    try:
        workspace_root = Path(
            text(source.get("OPL_WORKSPACE_ROOT"), "environment.OPL_WORKSPACE_ROOT")
        ).resolve(strict=True)
    except OSError as error:
        raise RequestShapeError(
            "environment.OPL_WORKSPACE_ROOT must be readable"
        ) from error
    if not workspace_root.is_dir():
        raise RequestShapeError("environment.OPL_WORKSPACE_ROOT must be a directory")

    values = {
        key: text(source.get(key), f"environment.{key}")
        for key in _ATTEMPT_BINDING_ENV_KEYS
    }
    attempt_ref = values["OPL_STAGE_ATTEMPT_REF"]
    if not attempt_ref.startswith("opl://stage_attempts/") or not attempt_ref.removeprefix(
        "opl://stage_attempts/"
    ):
        raise RequestShapeError(
            "environment.OPL_STAGE_ATTEMPT_REF must reference one OPL Stage Attempt"
        )
    attempt_id = source.get("OPL_STAGE_ATTEMPT_ID")
    if attempt_id is not None and text(
        attempt_id, "environment.OPL_STAGE_ATTEMPT_ID"
    ) != attempt_ref.removeprefix("opl://stage_attempts/"):
        raise RequestShapeError("OPL Stage Attempt id/ref bindings do not match")

    authority_issuer = {
        "agent_id": "mas",
        "domain_id": "medautoscience",
        "package_id": values["OPL_ROOT_PACKAGE_ID"],
        "stage_attempt_ref": attempt_ref,
        "execution_content_binding_sha256": values[
            "OPL_EXECUTION_CONTENT_BINDING_SHA256"
        ],
        "package_use_boundary_id": values["OPL_PACKAGE_USE_BOUNDARY_ID"],
        "root_package_content_digest": values[
            "OPL_ROOT_PACKAGE_CONTENT_DIGEST"
        ],
    }
    return workspace_root, authority_issuer


def _workspace_source_path(
    workspace_root: Path,
    source_ref: str,
    field: str,
) -> Path:
    normalized_ref = text(source_ref, field)
    parsed = urlparse(normalized_ref)
    if parsed.scheme == "file":
        if parsed.netloc not in {"", "localhost"} or parsed.query or parsed.fragment:
            raise RequestShapeError(f"{field} must use a local file URI")
        candidate = Path(unquote(parsed.path))
    elif parsed.scheme:
        raise RequestShapeError(f"{field} must be a workspace path or file URI")
    else:
        candidate = Path(normalized_ref)
        if not candidate.is_absolute():
            candidate = workspace_root / candidate

    try:
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise RequestShapeError(f"{field} must reference a readable file") from error
    if not resolved.is_relative_to(workspace_root):
        raise RequestShapeError(f"{field} escapes OPL_WORKSPACE_ROOT")
    if not resolved.is_file():
        raise RequestShapeError(f"{field} must reference a regular file")
    return resolved


def _file_identity(path: Path, field: str) -> tuple[int, str]:
    before = path.stat()
    digest = hashlib.sha256()
    size_bytes = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
            size_bytes += len(chunk)
    after = path.stat()
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity or size_bytes != after.st_size:
        raise RequestShapeError(f"{field} changed while its bytes were inspected")
    return size_bytes, f"sha256:{digest.hexdigest()}"


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
    supplied = mapping(source_refs_by_member_id, "source_refs_by_member_id")
    normalized: dict[str, str] = {}
    for index, (member_id_value, source_ref_value) in enumerate(supplied.items()):
        member_id = text(member_id_value, f"source_refs_by_member_id key[{index}]")
        if member_id in normalized:
            raise RequestShapeError(
                "source_refs_by_member_id contains duplicate normalized member_id values"
            )
        normalized[member_id] = text(
            source_ref_value,
            f"source_refs_by_member_id.{member_id}",
        )

    expected_members = {
        item["member_id"]: item for item in scope["reviewed_members"]
    }
    if set(normalized) != set(expected_members):
        missing = sorted(set(expected_members) - set(normalized))
        extra = sorted(set(normalized) - set(expected_members))
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise RequestShapeError(
            "source_refs_by_member_id must exactly match the statistical review scope; "
            + "; ".join(details)
        )

    for member_id, member in expected_members.items():
        field = f"source_refs_by_member_id.{member_id}"
        path = _workspace_source_path(workspace_root, normalized[member_id], field)
        observed_size, observed_sha256 = _file_identity(path, field)
        if (
            observed_size != member["size_bytes"]
            or observed_sha256 != member["sha256"]
        ):
            raise RequestShapeError(
                f"{field} bytes do not match the frozen MAS artifact identity"
            )
    return normalized


def _inject_snapshot_bundle(
    closeout_packet: Mapping[str, Any],
    bundle: dict[str, Any],
    *,
    producer_attempt_ref: str,
) -> dict[str, Any]:
    closeout = deepcopy(mapping(closeout_packet, "closeout_packet"))
    if closeout.get("surface_kind") != "stage_attempt_closeout_packet":
        raise RequestShapeError(
            "closeout_packet.surface_kind must be stage_attempt_closeout_packet"
        )
    attempt_id = producer_attempt_ref.removeprefix("opl://stage_attempts/")
    if text(
        closeout.get("stage_attempt_id"), "closeout_packet.stage_attempt_id"
    ) != attempt_id:
        raise RequestShapeError(
            "closeout_packet.stage_attempt_id must match OPL_STAGE_ATTEMPT_REF"
        )

    route_impact = mapping(
        closeout.get("route_impact", {}),
        "closeout_packet.route_impact",
    )
    quality_cycle = mapping(
        route_impact.get("stage_quality_cycle", {}),
        "closeout_packet.route_impact.stage_quality_cycle",
    )
    request = bundle["review_input_snapshot_materialization_request"]
    existing_request = quality_cycle.get(
        "review_input_snapshot_materialization_request"
    )
    if existing_request is not None and existing_request != request:
        raise RequestShapeError(
            "closeout_packet contains a conflicting snapshot materialization request"
        )
    quality_cycle["review_input_snapshot_materialization_request"] = request
    route_impact["stage_quality_cycle"] = quality_cycle
    closeout["route_impact"] = route_impact

    metadata = sequence(
        closeout.get("closeout_ref_metadata", []),
        "closeout_packet.closeout_ref_metadata",
    )
    owner_authority_ref = bundle["required_closeout_ref_metadata"][0]
    for index, value in enumerate(metadata):
        item = mapping(value, f"closeout_packet.closeout_ref_metadata[{index}]")
        if item.get("ref") != owner_authority_ref["ref"]:
            continue
        if item != owner_authority_ref:
            raise RequestShapeError(
                "closeout_packet contains conflicting owner authority metadata"
            )
        break
    else:
        metadata.append(dict(owner_authority_ref))
    closeout["closeout_ref_metadata"] = metadata
    return closeout


def finalize_bounded_analysis_producer_snapshot_closeout(
    *,
    closeout_packet: Mapping[str, Any],
    artifacts: list[dict[str, Any]],
    generation_id: str,
    generation_ref: str,
    source_refs_by_member_id: Mapping[str, str],
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build and inject one statistical snapshot request for a producer Attempt."""

    workspace_root, authority_issuer = _attempt_environment(environ)
    generation_manifest = build_generation_manifest_v2(
        artifacts=artifacts,
        generation_id=generation_id,
        manifest_scope="analysis_generation",
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
