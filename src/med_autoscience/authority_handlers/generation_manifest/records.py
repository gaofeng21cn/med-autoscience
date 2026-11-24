"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from typing import Any

from .._record_validation import (
    NonEmptyStr,
    NonNegativeInt,
    RequestShapeError,
    Sha256Text,
    StrictRecordModel,
    enum_text,
    text,
    validate_record_dict,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)


class _ArtifactRecordV1Model(StrictRecordModel):
    role: NonEmptyStr
    ref: NonEmptyStr
    size_bytes: NonNegativeInt
    sha256: Sha256Text


class _ArtifactRecordV2Model(_ArtifactRecordV1Model):
    member_id: NonEmptyStr


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
    model_cls = _ArtifactRecordV2Model if schema_version == 2 else _ArtifactRecordV1Model
    normalized = validate_record_dict(model_cls, value, field)
    normalized["role"] = enum_text(
        normalized["role"],
        f"{field}.role",
        set(allowed_roles),
    )
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
