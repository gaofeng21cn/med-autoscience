from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


SURFACE_KIND = "mas_terminal_attach_gate"
CONTRACT_SURFACE_KIND = "mas_terminal_attach_contract"
OWNER_SURFACE_KIND = "mas_terminal_attach_owner"
BLOCKED_STATUS = "blocked_by_missing_terminal_input_owner"
AVAILABLE_STATUS = "available"
FORBIDDEN_OWNER = "legacy_mds_daemon_websocket"
DEFAULT_LEASE_TTL_SECONDS = 900
REQUIRED_CAPABILITIES = ("attach", "input", "resize", "detach")
REQUIRED_OWNER_CONTRACT_KEYS = ("token", "lease", "idempotency", "audit", "input", "resize", "detach")


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


def terminal_attach_status(
    *,
    owner_contract: Mapping[str, Any] | None = None,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
) -> dict[str, Any]:
    if not _owner_available(owner_contract):
        return blocked_by_missing_terminal_input_owner(
            profile_ref=profile_ref,
            study_id=study_id,
            study_root=study_root,
        )
    contract = dict(owner_contract or {})
    endpoints = _mapping(contract.get("endpoints"))
    return {
        "surface_kind": SURFACE_KIND,
        "status": AVAILABLE_STATUS,
        "owner_surface_kind": OWNER_SURFACE_KIND,
        "owner": str(contract.get("owner") or "mas_terminal_attach_owner"),
        "capabilities": list(REQUIRED_CAPABILITIES),
        "required_owner_contract": {
            key: str(_mapping(contract.get("required_owner_contract")).get(key) or contract.get(key) or "available")
            for key in REQUIRED_OWNER_CONTRACT_KEYS
        },
        "endpoints": {
            key: str(endpoints.get(key) or "")
            for key in REQUIRED_CAPABILITIES
            if str(endpoints.get(key) or "").strip()
        },
        "forbidden_owner": FORBIDDEN_OWNER,
        "read_only_default": False,
        "attach_started": False,
        "profile_ref": str(Path(profile_ref).expanduser()) if profile_ref is not None else None,
        "study_id": study_id,
        "study_root": str(Path(study_root).expanduser()) if study_root is not None else None,
    }


def inspect_terminal_attach(
    *,
    runtime_root: str | Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str | None = None,
    source: str,
) -> dict[str, Any]:
    del source
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    read_model = _read_json(_read_model_path(quest_root))
    if not read_model:
        return _base_read_model(
            runtime_root=_runtime_root(runtime_root),
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=run_id,
            study_id=study_id,
            status="idle",
            latest_receipt=None,
            lease=None,
            token=token,
        )
    if token and _token_sha(read_model.get("lease")) != _sha256(token):
        return {
            **read_model,
            "authorized": False,
            "authorization_status": "invalid_token",
        }
    return read_model


def attach_terminal(
    *,
    runtime_root: str | Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    idempotency_key: str,
    source: str,
    lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
) -> dict[str, Any]:
    context = _operation_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        run_id=run_id,
        study_id=study_id,
        idempotency_key=idempotency_key,
    )
    if replay := _receipt_for_key(context["quest_root"], context["idempotency_key"]):
        return replay
    denial = _validate_owner_context(context)
    if denial is not None:
        return _record_receipt(context=context, operation="attach_terminal", status="denied", source=source, reason=denial)
    now = _utc_now()
    expires_at = _format_time(_parse_time(now) + timedelta(seconds=max(1, int(lease_ttl_seconds))))
    lease_id = _stable_id("lease", context["quest_root"], context["run_id"], context["idempotency_key"], now)
    token = _stable_id("mas-term", context["quest_root"], context["run_id"], lease_id, now)
    lease = {
        "lease_id": lease_id,
        "status": "active",
        "quest_id": context["quest_id"],
        "run_id": context["run_id"],
        "study_id": context["study_id"],
        "issued_at": now,
        "expires_at": expires_at,
        "token_sha256": _sha256(token),
    }
    return _record_receipt(
        context=context,
        operation="attach_terminal",
        status="attached",
        source=source,
        lease=lease,
        attach_token=token,
    )


def terminal_input(
    *,
    runtime_root: str | Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str,
    lease_id: str,
    text: str,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    context = _operation_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        run_id=run_id,
        study_id=study_id,
        idempotency_key=idempotency_key,
    )
    if replay := _receipt_for_key(context["quest_root"], context["idempotency_key"]):
        return replay
    reason = _validate_active_lease(context=context, token=token, lease_id=lease_id)
    extra: dict[str, Any] = {"input": {"byte_count": len(str(text).encode("utf-8"))}}
    if reason is not None:
        return _record_receipt(
            context=context,
            operation="terminal_input",
            status="denied",
            source=source,
            reason=reason,
            **extra,
        )
    command = _append_terminal_command(
        context=context,
        operation="terminal_input",
        lease_id=lease_id,
        payload={"text": text},
    )
    return _record_receipt(
        context=context,
        operation="terminal_input",
        status="accepted",
        source=source,
        command=command,
        **extra,
    )


def resize_terminal(
    *,
    runtime_root: str | Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str,
    lease_id: str,
    rows: int,
    cols: int,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    context = _operation_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        run_id=run_id,
        study_id=study_id,
        idempotency_key=idempotency_key,
    )
    if replay := _receipt_for_key(context["quest_root"], context["idempotency_key"]):
        return replay
    reason = _validate_active_lease(context=context, token=token, lease_id=lease_id)
    terminal_size = {"rows": _positive_int("rows", rows), "cols": _positive_int("cols", cols)}
    if reason is not None:
        return _record_receipt(
            context=context,
            operation="resize_terminal",
            status="denied",
            source=source,
            reason=reason,
            terminal_size=terminal_size,
        )
    command = _append_terminal_command(
        context=context,
        operation="resize_terminal",
        lease_id=lease_id,
        payload=terminal_size,
    )
    return _record_receipt(
        context=context,
        operation="resize_terminal",
        status="accepted",
        source=source,
        command=command,
        terminal_size=terminal_size,
    )


def detach_terminal(
    *,
    runtime_root: str | Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    token: str,
    lease_id: str,
    idempotency_key: str,
    source: str,
) -> dict[str, Any]:
    context = _operation_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        run_id=run_id,
        study_id=study_id,
        idempotency_key=idempotency_key,
    )
    if replay := _receipt_for_key(context["quest_root"], context["idempotency_key"]):
        return replay
    reason = _validate_active_lease(context=context, token=token, lease_id=lease_id)
    if reason is not None:
        return _record_receipt(
            context=context,
            operation="detach_terminal",
            status="denied",
            source=source,
            reason=reason,
        )
    command = _append_terminal_command(
        context=context,
        operation="detach_terminal",
        lease_id=lease_id,
        payload={},
    )
    return _record_receipt(
        context=context,
        operation="detach_terminal",
        status="detached",
        source=source,
        command=command,
    )


def _operation_context(
    *,
    runtime_root: str | Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    idempotency_key: str,
) -> dict[str, Any]:
    normalized_idempotency_key = _required_text("idempotency_key", idempotency_key)
    root = _runtime_root(runtime_root)
    quest_root = _quest_root(runtime_root=root, quest_id=quest_id)
    return {
        "runtime_root": root,
        "quest_root": quest_root,
        "quest_id": _required_path_segment("quest_id", quest_id),
        "run_id": _required_text("run_id", run_id),
        "study_id": _required_text("study_id", study_id),
        "idempotency_key": normalized_idempotency_key,
    }


def _validate_owner_context(context: dict[str, Any]) -> str | None:
    quest_root = context["quest_root"]
    if not (quest_root / "quest.yaml").is_file():
        return "quest_missing"
    runtime_state = _read_json(quest_root / ".ds" / "runtime_state.json")
    active_run_id = _text(runtime_state.get("active_run_id"))
    if active_run_id != context["run_id"]:
        return "run_id_mismatch"
    state_study_id = _text(runtime_state.get("study_id"))
    if state_study_id and state_study_id != context["study_id"]:
        return "study_id_mismatch"
    if _text(runtime_state.get("runtime_backend_id")) != "mas_runtime_core":
        return "invalid_runtime_owner"
    if _text(runtime_state.get("status")) != "running":
        return "run_not_active"
    lease = _read_json(_worker_lease_path(context["quest_root"], context["run_id"]))
    if lease.get("terminal_attach_capable") is not True:
        return "run_not_terminal_attach_capable"
    return None


def _validate_active_lease(*, context: dict[str, Any], token: str, lease_id: str) -> str | None:
    owner_reason = _validate_owner_context(context)
    if owner_reason is not None:
        return owner_reason
    read_model = _read_json(_read_model_path(context["quest_root"]))
    lease = read_model.get("lease")
    if not isinstance(lease, dict) or lease.get("status") != "active":
        return "missing_active_lease"
    if _text(lease.get("lease_id")) != _required_text("lease_id", lease_id):
        return "lease_mismatch"
    if _text(lease.get("run_id")) != context["run_id"] or _text(lease.get("study_id")) != context["study_id"]:
        return "lease_scope_mismatch"
    if _text(lease.get("token_sha256")) != _sha256(_required_text("token", token)):
        return "invalid_token"
    expires_at = _parse_time(_text(lease.get("expires_at")))
    if expires_at is None or expires_at <= datetime.now(UTC):
        return "lease_expired"
    return None


def _record_receipt(
    *,
    context: dict[str, Any],
    operation: str,
    status: str,
    source: str,
    reason: str | None = None,
    lease: dict[str, Any] | None = None,
    attach_token: str | None = None,
    **extra: Any,
) -> dict[str, Any]:
    now = _utc_now()
    current_model = _read_json(_read_model_path(context["quest_root"]))
    active_lease = lease if lease is not None else (_mapping(current_model.get("lease")) or None)
    if operation == "detach_terminal" and status == "detached" and active_lease:
        active_lease = {**active_lease, "status": "detached", "detached_at": now}
    if status == "denied" and lease is None:
        active_lease = _mapping(current_model.get("lease")) or None
    receipt = {
        "surface_kind": CONTRACT_SURFACE_KIND,
        "ok": status not in {"denied", "expired"},
        "operation": operation,
        "status": status,
        "reason": reason,
        "runtime_root": str(context["runtime_root"]),
        "quest_id": context["quest_id"],
        "run_id": context["run_id"],
        "study_id": context["study_id"],
        "source": _required_text("source", source),
        "idempotency_key": context["idempotency_key"],
        "recorded_at": now,
        "lease": active_lease,
        **extra,
    }
    if attach_token is not None:
        receipt["attach_token"] = attach_token
    _append_receipt(context["quest_root"], receipt)
    _write_receipt_index(context["quest_root"], context["idempotency_key"], receipt)
    _write_read_model(context=context, receipt=receipt, lease=active_lease)
    return receipt


def _write_read_model(*, context: dict[str, Any], receipt: dict[str, Any], lease: dict[str, Any] | None) -> None:
    status = receipt["status"]
    if receipt["operation"] in {"terminal_input", "resize_terminal"} and receipt["ok"]:
        status = "attached"
    model = _base_read_model(
        runtime_root=context["runtime_root"],
        quest_root=context["quest_root"],
        quest_id=context["quest_id"],
        run_id=context["run_id"],
        study_id=context["study_id"],
        status=status,
        latest_receipt={key: value for key, value in receipt.items() if key != "attach_token"},
        lease=lease,
        token=None,
    )
    path = _read_model_path(context["quest_root"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(model, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_read_model(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    study_id: str,
    status: str,
    latest_receipt: dict[str, Any] | None,
    lease: dict[str, Any] | None,
    token: str | None,
) -> dict[str, Any]:
    authorized = token is None or _token_sha(lease) == _sha256(token)
    return {
        "surface_kind": CONTRACT_SURFACE_KIND,
        "status": status,
        "authorized": authorized,
        "authorization_status": "authorized" if authorized else "invalid_token",
        "runtime_root": str(runtime_root),
        "quest_root": str(quest_root),
        "quest_id": quest_id,
        "run_id": run_id,
        "study_id": study_id,
        "lease": lease,
        "latest_receipt": latest_receipt,
        "receipt_log_path": str(_receipt_log_path(quest_root)),
        "read_model_path": str(_read_model_path(quest_root)),
        "command_queue_path": str(_command_queue_path(quest_root, run_id)),
    }


def _append_terminal_command(
    *,
    context: dict[str, Any],
    operation: str,
    lease_id: str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    now = _utc_now()
    command = {
        "schema_version": 1,
        "command_id": _stable_id(
            "terminal-command",
            context["quest_root"],
            context["run_id"],
            context["idempotency_key"],
            now,
        ),
        "operation": operation,
        "quest_id": context["quest_id"],
        "run_id": context["run_id"],
        "study_id": context["study_id"],
        "lease_id": _required_text("lease_id", lease_id),
        "idempotency_key": context["idempotency_key"],
        "status": "pending",
        "recorded_at": now,
        "payload": dict(payload),
    }
    path = _command_queue_path(context["quest_root"], context["run_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(command, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "command_id": command["command_id"],
        "operation": operation,
        "queue_path": str(path),
        "status": "pending",
    }


def _owner_available(owner_contract: Mapping[str, Any] | None) -> bool:
    contract = dict(owner_contract or {})
    if contract.get("surface_kind") != OWNER_SURFACE_KIND:
        return False
    if contract.get("status") != AVAILABLE_STATUS:
        return False
    if contract.get("forbidden_owner") == FORBIDDEN_OWNER or contract.get("owner") == FORBIDDEN_OWNER:
        return False
    capabilities = set(_string_list(contract.get("capabilities")))
    if not set(REQUIRED_CAPABILITIES).issubset(capabilities):
        return False
    endpoints = _mapping(contract.get("endpoints"))
    if any(not str(endpoints.get(key) or "").strip() for key in REQUIRED_CAPABILITIES):
        return False
    owner_keys = set(_string_list(contract.get("owner_contract")))
    nested_contract = _mapping(contract.get("required_owner_contract"))
    if not set(REQUIRED_OWNER_CONTRACT_KEYS).issubset(owner_keys | set(nested_contract)):
        return False
    return True


def _token_sha(lease: object) -> str | None:
    if not isinstance(lease, Mapping):
        return None
    return _text(lease.get("token_sha256"))


def _append_receipt(quest_root: Path, receipt: dict[str, Any]) -> None:
    path = _receipt_log_path(quest_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(receipt, ensure_ascii=False, sort_keys=True) + "\n")


def _write_receipt_index(quest_root: Path, idempotency_key: str, receipt: dict[str, Any]) -> None:
    path = _receipt_index_path(quest_root, idempotency_key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _receipt_for_key(quest_root: Path, idempotency_key: str) -> dict[str, Any] | None:
    payload = _read_json(_receipt_index_path(quest_root, idempotency_key))
    return payload or None


def _store_root(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "terminal_attach"


def _receipt_log_path(quest_root: Path) -> Path:
    return _store_root(quest_root) / "receipts.jsonl"


def _receipt_index_path(quest_root: Path, idempotency_key: str) -> Path:
    return _store_root(quest_root) / "receipts" / f"{_safe_filename(idempotency_key)}.json"


def _read_model_path(quest_root: Path) -> Path:
    return _store_root(quest_root) / "read_model" / "latest.json"


def _worker_lease_path(quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "runs" / run_id / "worker_lease.json"


def _command_queue_path(quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "runs" / run_id / "terminal_commands.jsonl"


def _runtime_root(runtime_root: str | Path) -> Path:
    return Path(runtime_root).expanduser().resolve()


def _quest_root(*, runtime_root: str | Path, quest_id: str) -> Path:
    return _runtime_root(runtime_root) / "quests" / _required_path_segment("quest_id", quest_id)


def _required_path_segment(name: str, value: object) -> str:
    text = _required_text(name, value)
    path = Path(text)
    if path.is_absolute() or ".." in path.parts or len(path.parts) != 1:
        raise ValueError(f"{name} must be a single relative path segment")
    return text


def _required_text(name: str, value: object) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{name} is required")
    return text


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if isinstance(value, (str, bytes)) or not hasattr(value, "__iter__"):
        return []
    return [str(item) for item in value if isinstance(item, str) and item.strip()]


def _positive_int(name: str, value: object) -> int:
    if not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _parse_time(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat()


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}-{_sha256('|'.join(str(part) for part in parts))[:24]}"


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_filename(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


__all__ = [
    "AVAILABLE_STATUS",
    "BLOCKED_STATUS",
    "CONTRACT_SURFACE_KIND",
    "DEFAULT_LEASE_TTL_SECONDS",
    "FORBIDDEN_OWNER",
    "OWNER_SURFACE_KIND",
    "REQUIRED_CAPABILITIES",
    "REQUIRED_OWNER_CONTRACT_KEYS",
    "SURFACE_KIND",
    "attach_terminal",
    "blocked_by_missing_terminal_input_owner",
    "detach_terminal",
    "inspect_terminal_attach",
    "resize_terminal",
    "terminal_attach_status",
    "terminal_input",
]
