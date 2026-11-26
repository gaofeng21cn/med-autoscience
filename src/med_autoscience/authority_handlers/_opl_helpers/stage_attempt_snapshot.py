"""Generic Stage Attempt reviewer-input snapshot materialization request helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import os
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .artifact_inspection import (
    ContainedFileReadError,
    fingerprint_contained_regular_file,
)
from .epistemic_review_scope import project_review_scope_members
from .exact_refs import normalize_sha256


SNAPSHOT_MATERIALIZATION_SURFACE = "opl_reviewer_input_snapshot_materialization_request"
SNAPSHOT_MATERIALIZATION_SCHEMA_VERSION = 2
ATTEMPT_BINDING_ENV_KEYS = (
    "OPL_STAGE_ATTEMPT_REF",
    "OPL_EXECUTION_CONTENT_BINDING_SHA256",
    "OPL_PACKAGE_USE_BOUNDARY_ID",
    "OPL_ROOT_PACKAGE_ID",
    "OPL_ROOT_PACKAGE_CONTENT_DIGEST",
)


class StageAttemptSnapshotError(ValueError):
    """Raised when Stage Attempt bindings, source paths, or snapshot requests are invalid."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageAttemptSnapshotError(f"{field} must be a non-empty string")
    return value.strip()


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise StageAttemptSnapshotError(f"{field} must be an object")
    return dict(value)


def _sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise StageAttemptSnapshotError(f"{field} must be an array")
    return list(value)


def read_stage_attempt_environment(
    *,
    expected_stage_id: str,
    agent_id: str,
    domain_id: str,
    environ: Mapping[str, str] | None = None,
) -> tuple[Path, dict[str, str]]:
    """Parse and validate host-injected OPL Stage Attempt bindings for snapshot requests."""

    source = os.environ if environ is None else environ
    stage_id = _text(source.get("OPL_STAGE_ID"), "environment.OPL_STAGE_ID")
    if stage_id != expected_stage_id:
        raise StageAttemptSnapshotError(
            f"environment.OPL_STAGE_ID must be {expected_stage_id}"
        )
    try:
        workspace_root = Path(
            _text(source.get("OPL_WORKSPACE_ROOT"), "environment.OPL_WORKSPACE_ROOT")
        ).resolve(strict=True)
    except OSError as error:
        raise StageAttemptSnapshotError(
            "environment.OPL_WORKSPACE_ROOT must be readable"
        ) from error
    if not workspace_root.is_dir():
        raise StageAttemptSnapshotError("environment.OPL_WORKSPACE_ROOT must be a directory")

    values = {
        key: _text(source.get(key), f"environment.{key}")
        for key in ATTEMPT_BINDING_ENV_KEYS
    }
    attempt_ref = values["OPL_STAGE_ATTEMPT_REF"]
    if not attempt_ref.startswith("opl://stage_attempts/") or not attempt_ref.removeprefix(
        "opl://stage_attempts/"
    ):
        raise StageAttemptSnapshotError(
            "environment.OPL_STAGE_ATTEMPT_REF must reference one OPL Stage Attempt"
        )
    attempt_id = source.get("OPL_STAGE_ATTEMPT_ID")
    if attempt_id is not None and _text(
        attempt_id, "environment.OPL_STAGE_ATTEMPT_ID"
    ) != attempt_ref.removeprefix("opl://stage_attempts/"):
        raise StageAttemptSnapshotError("OPL Stage Attempt id/ref bindings do not match")

    authority_issuer = {
        "agent_id": agent_id,
        "domain_id": domain_id,
        "package_id": values["OPL_ROOT_PACKAGE_ID"],
        "stage_attempt_ref": attempt_ref,
        "execution_content_binding_sha256": values["OPL_EXECUTION_CONTENT_BINDING_SHA256"],
        "package_use_boundary_id": values["OPL_PACKAGE_USE_BOUNDARY_ID"],
        "root_package_content_digest": values["OPL_ROOT_PACKAGE_CONTENT_DIGEST"],
    }
    return workspace_root, authority_issuer


def normalize_snapshot_authority_issuer(
    value: Any,
    *,
    expected_agent_id: str,
    expected_domain_id: str,
    expected_package_id: str,
    field: str = "authority_issuer",
) -> dict[str, Any]:
    """Validate an authority_issuer record against exact agent, domain, and package IDs."""

    payload = _mapping(value, field)
    keys = {
        "agent_id",
        "domain_id",
        "package_id",
        "stage_attempt_ref",
        "execution_content_binding_sha256",
        "package_use_boundary_id",
        "root_package_content_digest",
    }
    missing = sorted(keys - set(payload))
    unknown = sorted(set(payload) - keys)
    if missing:
        raise StageAttemptSnapshotError(f"{field} missing fields: {', '.join(missing)}")
    if unknown:
        raise StageAttemptSnapshotError(
            f"{field} contains unsupported fields: {', '.join(unknown)}"
        )
    if payload.get("agent_id") != expected_agent_id:
        raise StageAttemptSnapshotError(f"{field}.agent_id must be {expected_agent_id}")
    if payload.get("domain_id") != expected_domain_id:
        raise StageAttemptSnapshotError(f"{field}.domain_id must be {expected_domain_id}")
    if payload.get("package_id") != expected_package_id:
        raise StageAttemptSnapshotError(f"{field}.package_id must be {expected_package_id}")
    stage_attempt_ref = _text(payload.get("stage_attempt_ref"), f"{field}.stage_attempt_ref")
    if not stage_attempt_ref.startswith("opl://stage_attempts/"):
        raise StageAttemptSnapshotError(
            f"{field}.stage_attempt_ref must reference one OPL Stage Attempt"
        )
    return {
        "agent_id": expected_agent_id,
        "domain_id": expected_domain_id,
        "package_id": expected_package_id,
        "stage_attempt_ref": stage_attempt_ref,
        "execution_content_binding_sha256": normalize_sha256(
            payload.get("execution_content_binding_sha256"),
            f"{field}.execution_content_binding_sha256",
            error_type=StageAttemptSnapshotError,
        ),
        "package_use_boundary_id": _text(
            payload.get("package_use_boundary_id"),
            f"{field}.package_use_boundary_id",
        ),
        "root_package_content_digest": normalize_sha256(
            payload.get("root_package_content_digest"),
            f"{field}.root_package_content_digest",
            error_type=StageAttemptSnapshotError,
        ),
    }


def resolve_workspace_source_path(
    workspace_root: Path,
    source_ref: str,
    field: str,
) -> Path:
    """Resolve one workspace relative path or local `file://` URI inside `workspace_root`."""

    normalized_ref = _text(source_ref, field)
    parsed = urlparse(normalized_ref)
    if parsed.scheme == "file":
        if parsed.netloc not in {"", "localhost"} or parsed.query or parsed.fragment:
            raise StageAttemptSnapshotError(f"{field} must use a local file URI")
        candidate = Path(unquote(parsed.path))
    elif parsed.scheme:
        raise StageAttemptSnapshotError(f"{field} must be a workspace path or file URI")
    else:
        candidate = Path(normalized_ref)
        if not candidate.is_absolute():
            candidate = workspace_root / candidate

    absolute_candidate = Path(os.path.abspath(candidate))
    if not absolute_candidate.is_relative_to(workspace_root):
        raise StageAttemptSnapshotError(f"{field} escapes OPL_WORKSPACE_ROOT")
    return absolute_candidate


def fingerprint_workspace_source_file(
    workspace_root: Path,
    path: Path,
    field: str,
) -> tuple[int, str]:
    """Read file size and sha256 safely through `fingerprint_contained_regular_file`."""

    try:
        relative = path.relative_to(workspace_root)
    except ValueError as error:
        raise StageAttemptSnapshotError(f"{field} escapes OPL_WORKSPACE_ROOT") from error
    try:
        return fingerprint_contained_regular_file(workspace_root, relative)
    except ContainedFileReadError as error:
        detail = {
            "safe_open_unsupported": "cannot be inspected without no-follow support",
            "ref_not_contained": "must use a normalized workspace path",
            "ref_symlink": "must not reference a symlink",
            "ref_not_directory": "must reference a regular file",
            "not_regular_file": "must reference a regular file",
            "root_not_directory": "OPL_WORKSPACE_ROOT must be a physical directory",
        }.get(error.code, "changed while its bytes were inspected")
        raise StageAttemptSnapshotError(f"{field} {detail}") from error


def normalize_member_source_refs(
    source_refs_by_member_id: Mapping[str, str],
    expected_member_ids: set[str],
    *,
    scope_label: str = "review scope",
) -> dict[str, str]:
    """Validate an exact 1-to-1 member_id -> source_ref map without omissions or extras."""

    supplied = _mapping(source_refs_by_member_id, "source_refs_by_member_id")
    normalized: dict[str, str] = {}
    for index, (member_id_value, source_ref_value) in enumerate(supplied.items()):
        member_id = _text(member_id_value, f"source_refs_by_member_id key[{index}]")
        if member_id in normalized:
            raise StageAttemptSnapshotError(
                "source_refs_by_member_id contains duplicate normalized member_id values"
            )
        normalized[member_id] = _text(
            source_ref_value,
            f"source_refs_by_member_id.{member_id}",
        )

    supplied_ids = set(normalized)
    missing = sorted(expected_member_ids - supplied_ids)
    extra = sorted(supplied_ids - expected_member_ids)
    if missing or extra:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise StageAttemptSnapshotError(
            f"source_refs_by_member_id must exactly match the {scope_label}; "
            + "; ".join(details)
        )
    return normalized


def verify_workspace_member_source_refs(
    *,
    expected_members: Sequence[Mapping[str, Any]],
    workspace_root: Path,
    source_refs_by_member_id: Mapping[str, str],
    scope_label: str = "review scope",
    artifact_owner_label: str = "domain",
) -> dict[str, str]:
    """Verify every workspace file referenced in `source_refs_by_member_id` matches frozen digests."""

    by_id = {str(item["member_id"]): item for item in expected_members}
    normalized = normalize_member_source_refs(
        source_refs_by_member_id,
        set(by_id),
        scope_label=scope_label,
    )
    for member_id, member in by_id.items():
        field = f"source_refs_by_member_id.{member_id}"
        path = resolve_workspace_source_path(workspace_root, normalized[member_id], field)
        observed_size, observed_sha256 = fingerprint_workspace_source_file(
            workspace_root, path, field
        )
        if observed_size != member["size_bytes"] or observed_sha256 != member["sha256"]:
            raise StageAttemptSnapshotError(
                f"{field} bytes do not match the frozen {artifact_owner_label} artifact identity"
            )
    return normalized


def build_reviewer_input_snapshot_materialization_request(
    *,
    review_lane: str,
    owner_authority_ref: Mapping[str, Any],
    authority_issuer: Mapping[str, Any],
    workspace_root: str,
    reviewed_members: Sequence[Mapping[str, Any]],
    source_refs_by_member_id: Mapping[str, str],
    scope_label: str = "review scope",
) -> dict[str, Any]:
    """Construct an immutable `opl_reviewer_input_snapshot_materialization_request` v2 payload."""

    projected = project_review_scope_members(reviewed_members)
    normalized_refs = normalize_member_source_refs(
        source_refs_by_member_id,
        {item["member_id"] for item in projected},
        scope_label=scope_label,
    )
    members = [
        {
            "member_id": item["member_id"],
            "source_ref": normalized_refs[item["member_id"]],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in projected
    ]
    return {
        "surface_kind": SNAPSHOT_MATERIALIZATION_SURFACE,
        "schema_version": SNAPSHOT_MATERIALIZATION_SCHEMA_VERSION,
        "review_lane": review_lane,
        "owner_authority_ref": dict(owner_authority_ref),
        "producer_attempt_ref": authority_issuer["stage_attempt_ref"],
        "execution_content_binding_sha256": authority_issuer["execution_content_binding_sha256"],
        "workspace_root": _text(workspace_root, "workspace_root"),
        "members": members,
    }


def inject_snapshot_materialization_into_closeout(
    closeout_packet: Mapping[str, Any],
    *,
    request: Mapping[str, Any],
    owner_authority_ref: Mapping[str, Any],
    producer_attempt_ref: str,
) -> dict[str, Any]:
    """Inject one snapshot request into a producer closeout packet while blocking hard stops."""

    closeout = deepcopy(_mapping(closeout_packet, "closeout_packet"))
    if closeout.get("surface_kind") != "stage_attempt_closeout_packet":
        raise StageAttemptSnapshotError(
            "closeout_packet.surface_kind must be stage_attempt_closeout_packet"
        )
    attempt_id = producer_attempt_ref.removeprefix("opl://stage_attempts/")
    if _text(closeout.get("stage_attempt_id"), "closeout_packet.stage_attempt_id") != attempt_id:
        raise StageAttemptSnapshotError(
            "closeout_packet.stage_attempt_id must match OPL_STAGE_ATTEMPT_REF"
        )

    route_impact = _mapping(
        closeout.get("route_impact", {}),
        "closeout_packet.route_impact",
    )
    quality_cycle = _mapping(
        route_impact.get("stage_quality_cycle", {}),
        "closeout_packet.route_impact.stage_quality_cycle",
    )
    for field, value in (
        ("hard_stop_class", route_impact.get("hard_stop_class")),
        ("blocked_reason", route_impact.get("blocked_reason")),
        ("typed_blocker_refs", route_impact.get("typed_blocker_refs")),
        ("human_gate_refs", route_impact.get("human_gate_refs")),
        ("stage_quality_cycle.hard_stop_class", quality_cycle.get("hard_stop_class")),
        ("stage_quality_cycle.blocked_reason", quality_cycle.get("blocked_reason")),
        ("stage_quality_cycle.typed_blocker_refs", quality_cycle.get("typed_blocker_refs")),
        ("stage_quality_cycle.human_gate_refs", quality_cycle.get("human_gate_refs")),
    ):
        if value not in (None, "", [], {}):
            raise StageAttemptSnapshotError(
                "hard-stop closeout cannot carry a review input snapshot "
                f"materialization request ({field})"
            )
    outcome = quality_cycle.get("outcome")
    if outcome in {"blocked", "human_gate"}:
        raise StageAttemptSnapshotError(
            "hard-stop closeout cannot carry a review input snapshot "
            f"materialization request (stage_quality_cycle.outcome={outcome})"
        )

    existing_request = quality_cycle.get("review_input_snapshot_materialization_request")
    request_copy = dict(request)
    if existing_request is not None and existing_request != request_copy:
        raise StageAttemptSnapshotError(
            "closeout_packet contains a conflicting snapshot materialization request"
        )
    quality_cycle["review_input_snapshot_materialization_request"] = request_copy
    route_impact["stage_quality_cycle"] = quality_cycle
    closeout["route_impact"] = route_impact

    metadata = _sequence(
        closeout.get("closeout_ref_metadata", []),
        "closeout_packet.closeout_ref_metadata",
    )
    owner_ref_copy = dict(owner_authority_ref)
    for value in metadata:
        item = _mapping(value, "closeout_packet.closeout_ref_metadata[]")
        if item.get("ref") != owner_ref_copy["ref"]:
            continue
        if item != owner_ref_copy:
            raise StageAttemptSnapshotError(
                "closeout_packet contains conflicting owner authority metadata"
            )
        break
    else:
        metadata.append(owner_ref_copy)
    closeout["closeout_ref_metadata"] = metadata
    return closeout


__all__ = [
    "ATTEMPT_BINDING_ENV_KEYS",
    "SNAPSHOT_MATERIALIZATION_SCHEMA_VERSION",
    "SNAPSHOT_MATERIALIZATION_SURFACE",
    "StageAttemptSnapshotError",
    "build_reviewer_input_snapshot_materialization_request",
    "fingerprint_workspace_source_file",
    "inject_snapshot_materialization_into_closeout",
    "normalize_member_source_refs",
    "normalize_snapshot_authority_issuer",
    "read_stage_attempt_environment",
    "resolve_workspace_source_path",
    "verify_workspace_member_source_refs",
]
