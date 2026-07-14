from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from typing import Any


def provider_receipts_from_host_payloads(
    *sources: Mapping[str, Any],
) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source in sources:
        nested_sources = (
            source,
            _mapping(source.get("prompt_contract")),
            _mapping(source.get("handoff_packet")),
            _mapping(source.get("operator_payload")),
        )
        for payload in nested_sources:
            raw_receipts = payload.get("provider_receipts")
            candidates = (
                raw_receipts
                if isinstance(raw_receipts, Sequence)
                and not isinstance(raw_receipts, (str, bytes, bytearray))
                else (raw_receipts,)
            )
            for candidate in candidates:
                if isinstance(candidate, Mapping):
                    _append_unique_receipt(receipts, seen=seen, receipt=candidate)
            connect_payload = _mapping(payload.get("opl_connect_reference_verification"))
            if connect_payload:
                _append_unique_receipt(
                    receipts,
                    seen=seen,
                    receipt={
                        "receipt_ref": _text(
                            payload.get("provider_receipt_ref") or payload.get("receipt_ref")
                        ),
                        "opl_connect_reference_verification": connect_payload,
                    },
                )
    return receipts


def _append_unique_receipt(
    receipts: list[dict[str, Any]],
    *,
    seen: set[str],
    receipt: Mapping[str, Any],
) -> None:
    normalized = dict(receipt)
    key = json.dumps(normalized, ensure_ascii=False, sort_keys=True)
    if key not in seen:
        receipts.append(normalized)
        seen.add(key)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["provider_receipts_from_host_payloads"]
