"""Shared validation primitives for zero-I/O MAS authority records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


class RequestShapeError(ValueError):
    """Raised when a host-injected authority request is not exact and typed."""


def mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise RequestShapeError(f"{field} must be an object")
    return dict(value)


def sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise RequestShapeError(f"{field} must be an array")
    return list(value)


def exact_keys(payload: Mapping[str, Any], allowed: set[str], field: str) -> None:
    missing = sorted(allowed - set(payload))
    unknown = sorted(set(payload) - allowed)
    if missing:
        raise RequestShapeError(f"{field} missing fields: {', '.join(missing)}")
    if unknown:
        raise RequestShapeError(
            f"{field} contains unsupported fields: {', '.join(unknown)}"
        )


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RequestShapeError(f"{field} must be a non-empty string")
    return value.strip()


def optional_text(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return text(value, field)


def text_list(value: Any, field: str) -> list[str]:
    values = [
        text(item, f"{field}[{index}]")
        for index, item in enumerate(sequence(value, field))
    ]
    if len(values) != len(set(values)):
        raise RequestShapeError(f"{field} contains duplicates")
    return values


def enum_text(value: Any, field: str, allowed: set[str]) -> str:
    normalized = text(value, field)
    if normalized not in allowed:
        raise RequestShapeError(f"{field} must be one of: {', '.join(sorted(allowed))}")
    return normalized


def integer(value: Any, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise RequestShapeError(f"{field} must be a non-negative integer")
    return value


def sha256(value: Any, field: str) -> str:
    normalized = text(value, field).lower()
    digest = normalized.removeprefix("sha256:")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RequestShapeError(f"{field} must be a SHA-256 digest")
    return f"sha256:{digest}"


def optional_sha256(value: Any, field: str) -> str | None:
    if value is None:
        return None
    return sha256(value, field)


def dedupe(values: Sequence[str]) -> list[str]:
    return list(dict.fromkeys(values))


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def fingerprint(payload: Mapping[str, Any]) -> str:
    return f"sha256:{hashlib.sha256(canonical_json_bytes(payload)).hexdigest()}"


__all__ = [
    "RequestShapeError",
    "canonical_json_bytes",
    "dedupe",
    "enum_text",
    "exact_keys",
    "fingerprint",
    "integer",
    "mapping",
    "optional_sha256",
    "optional_text",
    "sequence",
    "sha256",
    "text",
    "text_list",
]
