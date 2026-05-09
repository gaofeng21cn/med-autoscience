from __future__ import annotations

from pathlib import Path
from typing import Any


SURFACE_KIND = "mas_terminal_attach_gate"
BLOCKED_STATUS = "blocked_by_missing_terminal_input_owner"
FORBIDDEN_OWNER = "legacy_mds_daemon_websocket"


def blocked_by_missing_terminal_input_owner(
    *,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "status": BLOCKED_STATUS,
        "threat_model": {
            "scope": "interactive_terminal_attach",
            "risks": [
                "unauthorized_terminal_input",
                "stale_or_replayed_resize",
                "duplicate_or_out_of_order_input",
                "detached_session_continuing_without_audit",
                "legacy_daemon_regaining_runtime_ownership",
            ],
            "fail_closed_without_owner": True,
        },
        "required_owner_contract": {
            "token": "MAS-issued attach token with explicit study/run scope and expiry",
            "lease": "single active terminal input lease with renewal and stale lease rejection",
            "idempotency": "dedupe key for each input, resize, and detach request",
            "audit": "append-only receipt for attach, input, resize, detach, denial, and expiry",
            "input": "MAS-owned terminal input route with authorization and run-state checks",
            "resize": "MAS-owned resize route with lease and run-state checks",
            "detach": "MAS-owned detach route with audited lease release",
        },
        "forbidden_owner": FORBIDDEN_OWNER,
        "read_only_default": True,
        "attach_started": False,
        "profile_ref": str(Path(profile_ref).expanduser()) if profile_ref is not None else None,
        "study_id": study_id,
        "study_root": str(Path(study_root).expanduser()) if study_root is not None else None,
    }


__all__ = [
    "BLOCKED_STATUS",
    "FORBIDDEN_OWNER",
    "SURFACE_KIND",
    "blocked_by_missing_terminal_input_owner",
]
