"""Generic OPL domain artifact CAS materialization & workspace index envelope helpers."""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import PurePosixPath
from typing import Any


CAS_MATERIALIZATION_SURFACE = "opl_domain_artifact_cas_materialization_request"
CAS_MATERIALIZATION_VERSION = "opl-domain-artifact-cas-materialization.v1"
WORKSPACE_INDEX_SURFACE = "opl_workspace_index"
WORKSPACE_INDEX_VERSION = "workspace-index.v1"


def strict_canonical_json_bytes(value: Any, *, ensure_ascii: bool = False) -> bytes:
    """Serialize strict canonical UTF-8 JSON bytes without NaN values."""

    return json.dumps(
        value,
        ensure_ascii=ensure_ascii,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _raw_bytes_sha256(data: bytes, *, sha256_prefix: bool = True) -> str:
    digest = hashlib.sha256(data).hexdigest()
    return f"sha256:{digest}" if sha256_prefix else digest


def strict_json_fingerprint(value: Any, *, ensure_ascii: bool = False) -> str:
    """Return canonical sha256:<hex> fingerprint of a strict JSON value."""

    return _raw_bytes_sha256(strict_canonical_json_bytes(value, ensure_ascii=ensure_ascii))


def _relative_workspace_path(value: str, field: str = "target_relative_path") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    raw = value.strip()
    if raw.startswith("/") or "\\" in raw or "//" in raw or raw.endswith("/"):
        raise ValueError(f"{field} must be a normalized workspace-relative path")
    posix = PurePosixPath(raw)
    if posix.is_absolute() or ".." in posix.parts or "." in posix.parts:
        raise ValueError(f"{field} must not escape workspace root")
    return posix.as_posix()


def _replacement_bytes(
    *,
    after_json: Mapping[str, Any] | None = None,
    after_bytes: bytes | None = None,
    ensure_ascii: bool = False,
) -> bytes:
    if (after_json is None) == (after_bytes is None):
        raise ValueError("Provide exactly one of after_json or after_bytes")
    if after_bytes is not None:
        return after_bytes
    return strict_canonical_json_bytes(after_json, ensure_ascii=ensure_ascii)


def build_cas_operation(
    target_relative_path: str,
    *,
    precondition: Mapping[str, Any],
    after_json: Mapping[str, Any] | None = None,
    after_bytes: bytes | None = None,
    ensure_ascii: bool = False,
    sha256_prefix: bool = True,
) -> dict[str, Any]:
    """Construct one CAS operation payload with base64 body, sha256, and byte size."""

    normalized_path = _relative_workspace_path(target_relative_path)
    replacement = _replacement_bytes(
        after_json=after_json,
        after_bytes=after_bytes,
        ensure_ascii=ensure_ascii,
    )
    return {
        "target_relative_path": normalized_path,
        "precondition": dict(precondition),
        "replacement_bytes_base64": base64.b64encode(replacement).decode("ascii"),
        "replacement_sha256": _raw_bytes_sha256(replacement, sha256_prefix=sha256_prefix),
        "replacement_byte_size": len(replacement),
    }


def build_cas_replace_operation(
    target_relative_path: str,
    *,
    current_sha256: str,
    current_byte_size: int,
    after_json: Mapping[str, Any] | None = None,
    after_bytes: bytes | None = None,
    ensure_ascii: bool = False,
    sha256_prefix: bool = True,
) -> dict[str, Any]:
    """Construct an existing_exact CAS replacement operation."""

    return build_cas_operation(
        target_relative_path,
        precondition={
            "kind": "existing_exact",
            "sha256": current_sha256,
            "byte_size": current_byte_size,
        },
        after_json=after_json,
        after_bytes=after_bytes,
        ensure_ascii=ensure_ascii,
        sha256_prefix=sha256_prefix,
    )


def build_cas_create_operation(
    target_relative_path: str,
    *,
    after_json: Mapping[str, Any] | None = None,
    after_bytes: bytes | None = None,
    ensure_ascii: bool = False,
    sha256_prefix: bool = True,
) -> dict[str, Any]:
    """Construct an absent-precondition CAS create operation."""

    return build_cas_operation(
        target_relative_path,
        precondition={"kind": "absent"},
        after_json=after_json,
        after_bytes=after_bytes,
        ensure_ascii=ensure_ascii,
        sha256_prefix=sha256_prefix,
    )


def collect_absent_precondition_paths(operations: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return sorted relative target paths whose precondition kind is `absent`."""

    return sorted(
        str(operation["target_relative_path"])
        for operation in operations
        if isinstance(operation.get("precondition"), Mapping)
        and operation["precondition"].get("kind") == "absent"
    )


def compute_cas_operation_digests(
    operations: Sequence[Mapping[str, Any]],
    *,
    absent_relative_path_preconditions: Sequence[str] = (),
    ensure_ascii: bool = False,
) -> tuple[str, str, list[str]]:
    """Compute operations_sha256, materialization_scope_sha256, and precondition paths."""

    ops = [dict(operation) for operation in operations]
    absent_paths = [str(item) for item in absent_relative_path_preconditions]
    operations_sha256 = strict_json_fingerprint(ops, ensure_ascii=ensure_ascii)
    materialization_scope_sha256 = strict_json_fingerprint(
        {
            "operations": ops,
            "absent_relative_path_preconditions": absent_paths,
        },
        ensure_ascii=ensure_ascii,
    )
    return operations_sha256, materialization_scope_sha256, absent_paths


def build_cas_materialization_request(
    *,
    capability_id: str,
    domain_id: str,
    request_id: str,
    authorization_ref: str,
    operations: Sequence[Mapping[str, Any]],
    operations_sha256: str,
    materialization_scope_sha256: str,
    absent_relative_path_preconditions: Sequence[str],
) -> dict[str, Any]:
    """Assemble an `opl_domain_artifact_cas_materialization_request` v1 envelope."""

    return {
        "surface_kind": CAS_MATERIALIZATION_SURFACE,
        "version": CAS_MATERIALIZATION_VERSION,
        "capability_id": capability_id,
        "request_id": request_id,
        "domain_id": domain_id,
        "authorization_ref": authorization_ref,
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": list(absent_relative_path_preconditions),
        "operations": [dict(operation) for operation in operations],
    }


def is_opl_workspace_index_envelope(
    record: Mapping[str, Any],
    *,
    require_absent_schema_version: bool = False,
) -> bool:
    """Return True when `record` carries the canonical `opl_workspace_index` header."""

    if (
        record.get("surface_kind") != WORKSPACE_INDEX_SURFACE
        or record.get("version") != WORKSPACE_INDEX_VERSION
    ):
        return False
    if require_absent_schema_version:
        return "schema_version" not in record
    return record.get("schema_version") is None


__all__ = [
    "CAS_MATERIALIZATION_SURFACE",
    "CAS_MATERIALIZATION_VERSION",
    "WORKSPACE_INDEX_SURFACE",
    "WORKSPACE_INDEX_VERSION",
    "build_cas_create_operation",
    "build_cas_materialization_request",
    "build_cas_operation",
    "build_cas_replace_operation",
    "collect_absent_precondition_paths",
    "compute_cas_operation_digests",
    "is_opl_workspace_index_envelope",
    "strict_canonical_json_bytes",
    "strict_json_fingerprint",
]
