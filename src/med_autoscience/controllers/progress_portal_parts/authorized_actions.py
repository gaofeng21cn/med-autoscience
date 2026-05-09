from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


ALLOWED_ACTIONS = frozenset({"inspect", "reconcile-dry-run", "pause", "resume", "stop"})
DRY_RUN_ACTIONS = frozenset({"inspect", "reconcile-dry-run"})
FORBIDDEN_WRITES = [
    "paper",
    "package",
    "publication_gate",
    "controller_decision",
    "runtime_sqlite_authority",
]
_IDEMPOTENCY_KEY_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}")


class PortalActionError(ValueError):
    def __init__(self, *, status_code: int, reason: str) -> None:
        super().__init__(reason)
        self.status_code = status_code
        self.reason = reason


def write_action_receipt(
    *,
    profile: WorkspaceProfile,
    action: str,
    study_id: str | None,
    idempotency_key: str,
    requested_at: str | None = None,
) -> dict[str, Any]:
    normalized_action = _normalize_action(action)
    normalized_key = _normalize_idempotency_key(idempotency_key)
    receipt_path = _receipt_path(profile=profile, idempotency_key=normalized_key)
    if receipt_path.exists():
        return _load_receipt(receipt_path)

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "dry_run" if normalized_action in DRY_RUN_ACTIONS else "action_request"
    receipt = {
        "schema_version": 1,
        "surface_kind": "mas_progress_portal_action_receipt",
        "action": normalized_action,
        "study_id": _text(study_id),
        "requested_at": requested_at or _utc_now(),
        "idempotency_key": normalized_key,
        "mode": mode,
        "dry_run": mode == "dry_run",
        "apply": False,
        "controller_owned": True,
        "status": "accepted_for_controller_dispatch",
        "audit_ref": _workspace_relative(receipt_path, profile.workspace_root),
        "forbidden_writes": list(FORBIDDEN_WRITES),
    }
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def _normalize_action(action: str) -> str:
    normalized = str(action or "").strip()
    if normalized not in ALLOWED_ACTIONS:
        raise PortalActionError(status_code=400, reason="action_not_allowed")
    return normalized


def _normalize_idempotency_key(idempotency_key: str) -> str:
    normalized = str(idempotency_key or "").strip()
    if not _IDEMPOTENCY_KEY_PATTERN.fullmatch(normalized):
        raise PortalActionError(status_code=400, reason="invalid_idempotency_key")
    return normalized


def _receipt_path(*, profile: WorkspaceProfile, idempotency_key: str) -> Path:
    return (
        profile.workspace_root
        / "artifacts"
        / "runtime"
        / "progress_portal"
        / "action_receipts"
        / f"{idempotency_key}.json"
    )


def _load_receipt(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PortalActionError(status_code=500, reason="receipt_not_object")
    return dict(payload)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _workspace_relative(path: Path, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)
