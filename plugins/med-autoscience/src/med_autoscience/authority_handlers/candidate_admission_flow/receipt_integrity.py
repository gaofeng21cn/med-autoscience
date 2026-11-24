"""Canonical identity checks shared by MAS receipt normalizers."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    fingerprint,
    integer,
    sha256,
    text,
)


def _validate_embedded_receipt(
    payload: Mapping[str, Any],
    core: dict[str, Any],
    *,
    field: str,
    id_prefix: str,
) -> dict[str, Any]:
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = f"{id_prefix}:{expected_fingerprint.removeprefix('sha256:')}"
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if (
        sha256(payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint")
        != expected_fingerprint
    ):
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }
