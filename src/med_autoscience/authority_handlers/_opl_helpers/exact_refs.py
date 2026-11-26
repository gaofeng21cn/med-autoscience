"""Versioned Python JSON identity bytes and exact-reference validation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import base64
import binascii
import hashlib
import json
import math
from typing import Any


PYTHON_EXACT_REF_CODEC_VERSION = "opl-python-exact-ref.v1"


class ExactRefValidationError(ValueError):
    """An exact reference or digest has an invalid shape."""


def _fail(error_type: type[ValueError], message: str) -> None:
    raise error_type(message)


def _mapping(
    value: Any,
    field: str,
    error_type: type[ValueError],
) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail(error_type, f"{field} must be an object")
    return dict(value)


def _sequence(value: Any, field: str, error_type: type[ValueError]) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        _fail(error_type, f"{field} must be an array")
    return list(value)


def _text(value: Any, field: str, error_type: type[ValueError]) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(error_type, f"{field} must be a non-empty string")
    return value.strip()


def _exact_keys(
    payload: Mapping[str, Any],
    allowed: set[str],
    field: str,
    error_type: type[ValueError],
) -> None:
    missing = sorted(allowed - set(payload))
    unknown = sorted(set(payload) - allowed)
    if missing:
        _fail(error_type, f"{field} missing fields: {', '.join(missing)}")
    if unknown:
        _fail(
            error_type,
            f"{field} contains unsupported fields: {', '.join(unknown)}",
        )


def _integer(value: Any, field: str, error_type: type[ValueError]) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        _fail(error_type, f"{field} must be a non-negative integer")
    return value


def normalize_sha256(
    value: Any,
    field: str,
    *,
    error_type: type[ValueError] = ExactRefValidationError,
) -> str:
    normalized = _text(value, field, error_type).lower()
    digest = normalized.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        _fail(error_type, f"{field} must be a SHA-256 digest")
    return f"sha256:{digest}"


def normalize_typed_ref(
    value: Any,
    field: str,
    expected_kind: str,
    *,
    error_type: type[ValueError] = ExactRefValidationError,
) -> dict[str, str]:
    payload = _mapping(value, field, error_type)
    _exact_keys(payload, {"kind", "ref", "sha256"}, field, error_type)
    kind = _text(payload.get("kind"), f"{field}.kind", error_type)
    if kind != expected_kind:
        _fail(error_type, f"{field}.kind must be {expected_kind}")
    return {
        "kind": kind,
        "ref": _text(payload.get("ref"), f"{field}.ref", error_type),
        "sha256": normalize_sha256(
            payload.get("sha256"),
            f"{field}.sha256",
            error_type=error_type,
        ),
    }


def normalize_exact_ref(
    value: Any,
    field: str,
    expected_kind: str,
    *,
    error_type: type[ValueError] = ExactRefValidationError,
) -> dict[str, Any]:
    payload = _mapping(value, field, error_type)
    _exact_keys(payload, {"kind", "ref", "size_bytes", "sha256"}, field, error_type)
    kind = _text(payload.get("kind"), f"{field}.kind", error_type)
    if kind != expected_kind:
        _fail(error_type, f"{field}.kind must be {expected_kind}")
    return {
        "kind": kind,
        "ref": _text(payload.get("ref"), f"{field}.ref", error_type),
        "size_bytes": _integer(
            payload.get("size_bytes"),
            f"{field}.size_bytes",
            error_type,
        ),
        "sha256": normalize_sha256(
            payload.get("sha256"),
            f"{field}.sha256",
            error_type=error_type,
        ),
    }


def normalize_typed_ref_list(
    value: Any,
    field: str,
    expected_kind: str,
    *,
    error_type: type[ValueError] = ExactRefValidationError,
) -> list[dict[str, str]]:
    refs = [
        normalize_typed_ref(
            item,
            f"{field}[{index}]",
            expected_kind,
            error_type=error_type,
        )
        for index, item in enumerate(_sequence(value, field, error_type))
    ]
    if len(refs) != len({(item["ref"], item["sha256"]) for item in refs}):
        _fail(error_type, f"{field} contains duplicate refs")
    return refs


def normalize_exact_ref_list(
    value: Any,
    field: str,
    expected_kind: str,
    *,
    dedupe_size: bool = True,
    error_type: type[ValueError] = ExactRefValidationError,
) -> list[dict[str, Any]]:
    refs = [
        normalize_exact_ref(
            item,
            f"{field}[{index}]",
            expected_kind,
            error_type=error_type,
        )
        for index, item in enumerate(_sequence(value, field, error_type))
    ]
    identities = {
        (
            item["ref"],
            *((item["size_bytes"],) if dedupe_size else ()),
            item["sha256"],
        )
        for item in refs
    }
    if len(refs) != len(identities):
        _fail(error_type, f"{field} contains duplicate refs")
    return refs


def canonical_json_bytes_v1(payload: Mapping[str, Any]) -> bytes:
    """Freeze Python json identity bytes; this is not RFC 8785/JCS."""

    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint_v1(payload: Mapping[str, Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes_v1(payload)).hexdigest()}"


def normalize_exact_json_object(
    *,
    encoded_value: Any,
    byte_size_value: Any,
    expected_sha256: str,
    supplied_record: Any,
    field: str,
    error_type: type[ValueError] = ExactRefValidationError,
) -> tuple[str, int, dict[str, Any]]:
    """Validate original JSON bytes without reserializing their identity."""

    if not isinstance(encoded_value, str) or not encoded_value:
        _fail(error_type, f"{field} bytes_base64 must be a non-empty string")
    try:
        raw_bytes = base64.b64decode(encoded_value, validate=True)
    except (binascii.Error, ValueError) as error:
        raise error_type(f"{field} bytes_base64 is malformed") from error
    if base64.b64encode(raw_bytes).decode("ascii") != encoded_value:
        _fail(error_type, f"{field} bytes_base64 must be canonical base64")
    byte_size = _integer(byte_size_value, f"{field} byte_size", error_type)
    if byte_size < 1:
        _fail(error_type, f"{field} byte_size must be positive")
    if len(raw_bytes) != byte_size:
        _fail(error_type, f"{field} byte_size does not match decoded bytes")
    if hashlib.sha256(raw_bytes).hexdigest() != expected_sha256:
        _fail(error_type, f"{field} sha256 does not match decoded bytes")
    try:
        json_text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise error_type(f"{field} bytes must be strict UTF-8") from error
    try:
        parsed = json.loads(
            json_text,
            object_pairs_hook=_json_object_without_duplicate_keys,
            parse_constant=_reject_json_constant,
            parse_float=_strict_json_float,
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise error_type(f"{field} bytes must contain one strict JSON object: {error}") from error
    if not isinstance(parsed, dict):
        _fail(error_type, f"{field} bytes must contain a JSON object")
    record = _mapping(supplied_record, f"{field}.record", error_type)
    if not json_deep_equal(parsed, record):
        _fail(error_type, f"{field} decoded JSON must deep-equal the supplied record")
    return encoded_value, byte_size, parsed


def _json_object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
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


def json_deep_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without conflating booleans, integers and floats."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_deep_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_deep_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return bool(left == right)


__all__ = [
    "ExactRefValidationError",
    "PYTHON_EXACT_REF_CODEC_VERSION",
    "canonical_json_bytes_v1",
    "fingerprint_v1",
    "json_deep_equal",
    "normalize_exact_ref",
    "normalize_exact_ref_list",
    "normalize_exact_json_object",
    "normalize_sha256",
    "normalize_typed_ref",
    "normalize_typed_ref_list",
]
