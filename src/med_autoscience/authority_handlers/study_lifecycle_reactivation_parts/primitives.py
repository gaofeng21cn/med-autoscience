"""Shared exact-byte and digest validation primitives."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any

from opl_framework.exact_refs import (
    json_deep_equal as _json_deep_equal,
    normalize_exact_json_object,
)

from .._record_validation import RequestShapeError, text


def _normalize_exact_json_object(
    *,
    encoded_value: Any,
    byte_size_value: Any,
    expected_sha256: str,
    supplied_record: Any,
    field: str,
) -> tuple[str, int, dict[str, Any]]:
    return normalize_exact_json_object(
        encoded_value=encoded_value,
        byte_size_value=byte_size_value,
        expected_sha256=expected_sha256,
        supplied_record=supplied_record,
        field=field,
        error_type=RequestShapeError,
    )


def _timestamp(value: Any, field: str) -> str:
    raw = text(value, field)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise RequestShapeError(f"{field} must be an RFC3339 timestamp") from error
    if parsed.tzinfo is None:
        raise RequestShapeError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _timestamp_instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _relative_path(value: Any, field: str) -> str:
    path = text(value, field)
    parts = path.split("/")
    if path.startswith("/") or any(part in {"", ".", ".."} for part in parts):
        raise RequestShapeError(f"{field} must be a safe workspace-relative path")
    return path


def _file_ref(value: Any, field: str) -> str:
    ref = text(value, field)
    if not ref.startswith("file:///"):
        raise RequestShapeError(f"{field} must be an exact file URL")
    return ref


def _digest_text(value: Any, field: str) -> str:
    digest = text(value, field).lower().removeprefix("sha256:")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise RequestShapeError(f"{field} must be a SHA-256 digest")
    return digest


def _required_false(value: Any, field: str) -> bool:
    if value is not False:
        raise RequestShapeError(f"{field} must be false")
    return False


def _normalized_instruction_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestShapeError(f"{field} must be non-empty normalized text")
    normalized = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if value != normalized:
        raise RequestShapeError(
            f"{field} must use LF newlines and have no surrounding whitespace"
        )
    return normalized


def _history_stamp(value: str) -> str:
    return value.replace("-", "").replace(":", "").replace("+", "").replace(".", "")


def _json_fingerprint(value: Any) -> str:
    return _strict_fingerprint(value)


def _strict_canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RequestShapeError(
            "authority JSON contains an unsupported or non-finite value"
        ) from error


def _strict_fingerprint(value: Any) -> str:
    return _bytes_sha256(_strict_canonical_json_bytes(value))


def _bytes_sha256(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _raw_bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
