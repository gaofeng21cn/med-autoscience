from __future__ import annotations

from datetime import datetime, timezone
import json
import re
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience import runtime_backend as runtime_backend_contract


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
    quest_id: str | None = None,
    idempotency_key: str,
    requested_at: str | None = None,
    apply: bool = False,
    runtime_backend: Any | None = None,
) -> dict[str, Any]:
    normalized_action = _normalize_action(action)
    normalized_key = _normalize_idempotency_key(idempotency_key)
    receipt_path = _receipt_path(profile=profile, idempotency_key=normalized_key)
    if receipt_path.exists():
        return _load_receipt(receipt_path)

    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    requested_quest_id = _text(quest_id) or _text(study_id)
    dry_run = normalized_action in DRY_RUN_ACTIONS
    should_apply = bool(apply) and not dry_run
    mode = "dry_run" if dry_run else ("runtime_control_apply" if should_apply else "action_request")
    receipt = {
        "schema_version": 1,
        "surface_kind": "mas_progress_portal_action_receipt",
        "action": normalized_action,
        "study_id": _text(study_id),
        "quest_id": requested_quest_id,
        "requested_at": requested_at or _utc_now(),
        "idempotency_key": normalized_key,
        "mode": mode,
        "dry_run": dry_run,
        "apply": should_apply,
        "apply_status": "not_applicable" if dry_run or not should_apply else "pending",
        "controller_owned": True,
        "status": "accepted_for_controller_dispatch" if not should_apply else "accepted_for_runtime_control_apply",
        "audit_ref": _workspace_relative(receipt_path, profile.workspace_root),
        "forbidden_writes": list(FORBIDDEN_WRITES),
    }
    if should_apply:
        if requested_quest_id is None:
            raise PortalActionError(status_code=400, reason="missing_quest_id")
        receipt.update(
            _apply_runtime_control(
                profile=profile,
                action=normalized_action,
                quest_id=requested_quest_id,
                backend=runtime_backend or default_runtime_backend(),
            )
        )
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return receipt


def default_runtime_backend() -> Any:
    return runtime_backend_contract.get_managed_runtime_backend(runtime_backend_contract.DEFAULT_MANAGED_RUNTIME_BACKEND_ID)


def _apply_runtime_control(
    *,
    profile: WorkspaceProfile,
    action: str,
    quest_id: str,
    backend: Any,
) -> dict[str, Any]:
    operation_name = _runtime_control_operation(action)
    source = f"progress_portal:{action}"
    try:
        if operation_name == "pause_quest":
            result = backend.pause_quest(runtime_root=profile.runtime_root, quest_id=quest_id, source=source)
        elif operation_name == "resume_quest":
            result = backend.resume_quest(runtime_root=profile.runtime_root, quest_id=quest_id, source=source)
        elif operation_name == "stop_quest":
            result = backend.stop_quest(runtime_root=profile.runtime_root, quest_id=quest_id, source=source, daemon_url=None)
        else:
            raise PortalActionError(status_code=400, reason="action_not_runtime_control")
    except PortalActionError:
        raise
    except Exception as exc:  # pragma: no cover - exercised by endpoint integration tests with real backend failures.
        return {
            "apply_status": "failed",
            "runtime_control_operation": operation_name,
            "runtime_control_error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "apply_status": "applied",
        "runtime_control_operation": operation_name,
        "runtime_control_result": _jsonable(result),
    }


def _runtime_control_operation(action: str) -> str:
    if action == "pause":
        return "pause_quest"
    if action == "resume":
        return "resume_quest"
    if action == "stop":
        return "stop_quest"
    raise PortalActionError(status_code=400, reason="action_not_runtime_control")


def _jsonable(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    return value


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
