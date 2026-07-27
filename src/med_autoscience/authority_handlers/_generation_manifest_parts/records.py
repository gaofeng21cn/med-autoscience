"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)



def _manifest_artifact_ref(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
    expected_role: str,
) -> dict[str, Any]:
    normalized = _exact_ref(value, field, "mas_artifact")
    matches = [
        item
        for item in artifacts
        if item["role"] == expected_role
        and item["ref"] == normalized["ref"]
        and item["size_bytes"] == normalized["size_bytes"]
        and item["sha256"] == normalized["sha256"]
    ]
    if len(matches) != 1:
        raise RequestShapeError(
            f"{field} must match exactly one current {expected_role} artifact"
        )
    return normalized


def _normalize_artifact(
    value: Any,
    field: str,
    *,
    allowed_roles: frozenset[str],
    schema_version: int = 1,
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {"role", "ref", "size_bytes", "sha256"}
    if schema_version == 2:
        keys.add("member_id")
    exact_keys(payload, keys, field)
    normalized = {
        "role": enum_text(payload.get("role"), f"{field}.role", set(allowed_roles)),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    if schema_version == 2:
        normalized["member_id"] = text(payload.get("member_id"), f"{field}.member_id")
    return normalized


def _require_unique_member_ids(
    members: list[dict[str, Any]],
    field: str,
) -> None:
    member_ids = [
        text(item.get("member_id"), f"{field}[{index}].member_id")
        for index, item in enumerate(members)
    ]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(f"{field} contains duplicate member_id values")
