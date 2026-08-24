"""Shared exact-byte and digest validation primitives."""

from __future__ import annotations

from datetime import datetime, timezone
import base64
import binascii
import hashlib
import json
import math
import re
from typing import Any

from .._record_validation import RequestShapeError, integer, mapping, text


def _normalize_exact_json_object(
    *,
    encoded_value: Any,
    byte_size_value: Any,
    expected_sha256: str,
    supplied_record: Any,
    field: str,
) -> tuple[str, int, dict[str, Any]]:
    if not isinstance(encoded_value, str) or not encoded_value:
        raise RequestShapeError(f"{field} bytes_base64 must be a non-empty string")
    try:
        raw_bytes = base64.b64decode(encoded_value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise RequestShapeError(f"{field} bytes_base64 is malformed") from error
    if base64.b64encode(raw_bytes).decode("ascii") != encoded_value:
        raise RequestShapeError(f"{field} bytes_base64 must be canonical base64")

    byte_size = integer(byte_size_value, f"{field} byte_size")
    if byte_size < 1:
        raise RequestShapeError(f"{field} byte_size must be positive")
    if len(raw_bytes) != byte_size:
        raise RequestShapeError(f"{field} byte_size does not match decoded bytes")
    if hashlib.sha256(raw_bytes).hexdigest() != expected_sha256:
        raise RequestShapeError(f"{field} sha256 does not match decoded bytes")

    try:
        json_text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RequestShapeError(f"{field} bytes must be strict UTF-8") from error
    try:
        parsed = json.loads(
            json_text,
            object_pairs_hook=_json_object_without_duplicate_keys,
            parse_constant=_reject_json_constant,
            parse_float=_strict_json_float,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise RequestShapeError(
            f"{field} bytes must contain one strict JSON object: {error}"
        ) from error
    if not isinstance(parsed, dict):
        raise RequestShapeError(f"{field} bytes must contain a JSON object")

    record = mapping(supplied_record, f"{field}.record")
    if not _json_deep_equal(parsed, record):
        raise RequestShapeError(
            f"{field} decoded JSON must deep-equal the supplied record"
        )
    return encoded_value, byte_size, parsed


def _json_object_without_duplicate_keys(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _strict_json_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"non-finite JSON number {value!r}")
    return parsed


def _json_deep_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_deep_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_deep_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return bool(left == right)


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
