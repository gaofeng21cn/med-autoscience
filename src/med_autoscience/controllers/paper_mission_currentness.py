from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def receipt_owner_consumption_superseded_by_consumption(
    *,
    receipt_owner_consumption_readback: Mapping[str, Any],
    consumption_ledger_readback: Mapping[str, Any] | None,
) -> bool:
    if consumption_ledger_readback is None:
        return False
    receipt_mtime = _path_mtime(
        _optional_text(receipt_owner_consumption_readback.get("source_ref"))
    )
    consume_mtime = _path_mtime(
        _optional_text(consumption_ledger_readback.get("source_ref"))
    )
    if receipt_mtime is None or consume_mtime is None or consume_mtime <= receipt_mtime:
        return False
    if (
        _optional_text(consumption_ledger_readback.get("route_handoff_status"))
        == "ready_for_opl_route_command"
    ):
        return True
    handoff = _mapping(consumption_ledger_readback.get("opl_route_handoff"))
    return (
        _optional_text(handoff.get("handoff_status")) == "ready_for_opl_route_command"
        and handoff.get("can_submit_to_opl_runtime") is True
    )


def _path_mtime(path_text: str | None) -> float | None:
    if path_text is None:
        return None
    try:
        return Path(path_text).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
