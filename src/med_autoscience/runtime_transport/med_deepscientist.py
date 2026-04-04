from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote

import yaml


DEFAULT_DAEMON_TIMEOUT_SECONDS = 10
ACTIVE_BASH_SESSION_STATUSES = frozenset({"running", "terminating"})
_UNSET = object()


def _load_json_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing med-deepscientist runtime config: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _get_json(*, url: str, timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> Any:
    http_request = request.Request(
        url,
        headers={"Accept": "application/json"},
        method="GET",
    )
    with request.urlopen(http_request, timeout=timeout) as response:
        raw = response.read()
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def _normalize_local_host(host: str) -> str:
    normalized = host.strip() or "127.0.0.1"
    if normalized in {"0.0.0.0", "localhost"}:
        return "127.0.0.1"
    return normalized


def _daemon_url_matches_runtime_home(
    *,
    daemon_url: str,
    expected_home: Path,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> bool:
    normalized_url = daemon_url.rstrip("/")
    health_request = request.Request(
        f"{normalized_url}/api/health",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with request.urlopen(health_request, timeout=timeout) as response:
            raw = response.read()
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        return False
    if not raw:
        return False
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(decoded, dict):
        return False
    resolved_home = str(decoded.get("home") or "").strip()
    if not resolved_home:
        return False
    try:
        return Path(resolved_home).expanduser().resolve() == expected_home.expanduser().resolve()
    except OSError:
        return False


def resolve_daemon_url(*, runtime_root: Path) -> str:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    daemon_state = _load_json_dict(resolved_runtime_root / "runtime" / "daemon.json")
    daemon_url = str(daemon_state.get("url") or "").strip()
    if daemon_url and _daemon_url_matches_runtime_home(
        daemon_url=daemon_url,
        expected_home=resolved_runtime_root,
    ):
        return daemon_url.rstrip("/")
    config = _load_yaml_dict(resolved_runtime_root / "config" / "config.yaml")
    ui = config.get("ui")
    if not isinstance(ui, dict):
        raise ValueError("runtime config is missing ui section")
    host = _normalize_local_host(str(ui.get("host") or "127.0.0.1"))
    port = ui.get("port", 20999)
    if not isinstance(port, int):
        raise ValueError("runtime config ui.port must be an integer")
    return f"http://{host}:{port}"


def _request_json(
    *,
    url: str,
    payload: dict[str, Any],
    method: str,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    http_request.headers["Content-Type"] = "application/json"
    with request.urlopen(http_request, timeout=timeout) as response:
        raw = response.read()
    if not raw:
        return {}
    decoded = json.loads(raw.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError(f"daemon response must be a JSON object: {url}")
    return decoded


def _post_json(*, url: str, payload: dict[str, Any], timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> dict[str, Any]:
    return _request_json(url=url, payload=payload, method="POST", timeout=timeout)


def _patch_json(*, url: str, payload: dict[str, Any], timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> dict[str, Any]:
    return _request_json(url=url, payload=payload, method="PATCH", timeout=timeout)


def _normalize_stable_bash_session_entry(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    bash_id = str(payload.get("bash_id") or "").strip()
    status = str(payload.get("status") or "").strip()
    if not bash_id or not status:
        raise RuntimeError("stable bash session contract requires `bash_id` and `status`")
    return dict(payload)


def _normalize_stable_quest_session(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    quest_id = str(payload.get("quest_id") or "").strip()
    snapshot = payload.get("snapshot")
    runtime_audit = payload.get("runtime_audit")
    if not quest_id or not isinstance(snapshot, dict) or not isinstance(runtime_audit, dict):
        raise RuntimeError("missing stable quest session contract")
    required_runtime_audit_keys = {
        "ok",
        "status",
        "source",
        "active_run_id",
        "worker_running",
        "worker_pending",
        "stop_requested",
    }
    if not required_runtime_audit_keys.issubset(runtime_audit):
        raise RuntimeError("missing stable quest session contract")
    return dict(payload)


def _normalize_stable_quest_create_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot = payload.get("snapshot")
    if payload.get("ok") is not True or not isinstance(snapshot, dict) or not str(snapshot.get("quest_id") or "").strip():
        raise RuntimeError("missing stable quest create contract")
    return dict(payload)


def _normalize_stable_startup_context_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot = payload.get("snapshot")
    quest_id = str(payload.get("quest_id") or "").strip()
    if payload.get("ok") is not True or not isinstance(snapshot, dict):
        raise RuntimeError("missing stable startup-context contract")
    if not quest_id:
        quest_id = str(snapshot.get("quest_id") or "").strip()
    if not quest_id:
        raise RuntimeError("missing stable startup-context contract")
    return dict(payload)


def _normalize_stable_quest_control_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    quest_id = str(payload.get("quest_id") or "").strip()
    action = str(payload.get("action") or "").strip()
    snapshot = payload.get("snapshot")
    status = str(payload.get("status") or (snapshot.get("status") if isinstance(snapshot, dict) else "") or "").strip()
    if payload.get("ok") is not True or not quest_id or not action or not isinstance(snapshot, dict) or not status:
        raise RuntimeError("missing stable quest control contract")
    return dict(payload)


def _normalize_stable_artifact_completion_result(
    *,
    payload: dict[str, Any],
) -> dict[str, Any]:
    snapshot = payload.get("snapshot")
    summary_refresh = payload.get("summary_refresh")
    status = str(payload.get("status") or "").strip()
    if payload.get("ok") is not True or not isinstance(snapshot, dict) or not isinstance(summary_refresh, dict) or not status:
        raise RuntimeError("missing stable artifact completion contract")
    return dict(payload)


def list_quest_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> list[dict[str, Any]]:
    base_url = str(daemon_url or "").strip().rstrip("/")
    if not base_url:
        if runtime_root is None:
            raise ValueError("runtime_root or daemon_url is required")
        base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/bash/sessions?limit=200"
    try:
        payload = _get_json(url=url, timeout=timeout)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Bash session probe failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Bash session probe failed: {exc}") from exc
    except (TimeoutError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Bash session probe failed: {exc}") from exc
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise RuntimeError(f"Bash session probe returned non-list payload: {url}")
    sessions: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            raise RuntimeError(f"Bash session probe returned non-object entry: {url}")
        sessions.append(_normalize_stable_bash_session_entry(payload=item))
    return sessions


def get_quest_session(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    base_url = str(daemon_url or "").strip().rstrip("/")
    if not base_url:
        if runtime_root is None:
            raise ValueError("runtime_root or daemon_url is required")
        base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/session"
    try:
        payload = _get_json(url=url, timeout=timeout)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest session probe failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Quest session probe failed: {exc}") from exc
    except (TimeoutError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Quest session probe failed: {exc}") from exc
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        raise RuntimeError(f"Quest session probe returned non-object payload: {url}")
    return _normalize_stable_quest_session(payload=dict(payload))


def inspect_quest_live_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    try:
        sessions = list_quest_bash_sessions(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    except RuntimeError as exc:
        return {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": str(exc),
        }
    live_session_ids = [
        str(session.get("bash_id") or "").strip()
        for session in sessions
        if str(session.get("status") or "").strip().lower() in ACTIVE_BASH_SESSION_STATUSES
        and str(session.get("bash_id") or "").strip()
    ]
    return {
        "ok": True,
        "status": "live" if live_session_ids else "none",
        "session_count": len(sessions),
        "live_session_count": len(live_session_ids),
        "live_session_ids": live_session_ids,
    }


def inspect_quest_live_runtime(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    try:
        payload = get_quest_session(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    except RuntimeError as exc:
        return {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": str(exc),
        }

    runtime_audit = payload.get("runtime_audit") if isinstance(payload.get("runtime_audit"), dict) else None
    snapshot = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else {}
    active_run_id = str((runtime_audit or {}).get("active_run_id") or snapshot.get("active_run_id") or "").strip() or None
    if runtime_audit is None:
        return {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": active_run_id,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "Quest session probe returned no runtime_audit payload.",
        }

    status = str(runtime_audit.get("status") or "").strip().lower()
    if status not in {"live", "none"}:
        return {
            "ok": False,
            "status": "unknown",
            "source": str(runtime_audit.get("source") or "quest_session_runtime_audit"),
            "active_run_id": active_run_id,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": f"Unsupported runtime audit status: {status or 'empty'}",
        }

    return {
        "ok": bool(runtime_audit.get("ok", True)),
        "status": status,
        "source": str(runtime_audit.get("source") or "quest_session_runtime_audit"),
        "active_run_id": active_run_id,
        "worker_running": bool(runtime_audit.get("worker_running")) if "worker_running" in runtime_audit else None,
        "worker_pending": bool(runtime_audit.get("worker_pending")) if "worker_pending" in runtime_audit else None,
        "stop_requested": bool(runtime_audit.get("stop_requested")) if "stop_requested" in runtime_audit else None,
    }


def inspect_quest_live_execution(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    runtime_audit = inspect_quest_live_runtime(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )
    bash_session_audit = inspect_quest_live_bash_sessions(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )
    runtime_live = str(runtime_audit.get("status") or "").strip() == "live"
    bash_live = str(bash_session_audit.get("status") or "").strip() == "live"
    runtime_known = str(runtime_audit.get("status") or "").strip() in {"live", "none"}
    bash_known = str(bash_session_audit.get("status") or "").strip() in {"live", "none"}
    if runtime_live or bash_live:
        status = "live"
        ok = True
    elif runtime_known and bash_known:
        status = "none"
        ok = True
    else:
        status = "unknown"
        ok = False
    payload = {
        "ok": ok,
        "status": status,
        "source": "combined_runner_or_bash_session",
        "active_run_id": runtime_audit.get("active_run_id"),
        "runner_live": runtime_live,
        "bash_live": bash_live,
        "runtime_audit": runtime_audit,
        "bash_session_audit": bash_session_audit,
    }
    errors = [str(item) for item in [runtime_audit.get("error"), bash_session_audit.get("error")] if item]
    if errors:
        payload["error"] = " | ".join(errors)
    return payload


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return _normalize_stable_quest_create_result(
        payload=_post_json(url=f"{base_url}/api/quests", payload=payload)
    )


def chat_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    text: str,
    source: str,
    reply_to_interaction_id: str | None = None,
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    payload: dict[str, Any] = {"text": text, "source": source}
    if reply_to_interaction_id:
        payload["reply_to_interaction_id"] = reply_to_interaction_id
    return _post_json(url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/chat", payload=payload)


def artifact_interact(
    *,
    runtime_root: Path,
    quest_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return _post_json(
        url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/artifact/interact",
        payload=payload,
    )


def artifact_complete_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    summary: str,
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return _post_json(
        url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/artifact/complete",
        payload={"summary": summary},
    )


def sync_completion_with_approval(
    *,
    runtime_root: Path,
    quest_id: str,
    decision_request_payload: dict[str, Any],
    approval_text: str,
    summary: str,
    source: str,
) -> dict[str, Any]:
    request_result = artifact_interact(
        runtime_root=runtime_root,
        quest_id=quest_id,
        payload=decision_request_payload,
    )
    interaction_id = str(request_result.get("interaction_id") or "").strip()
    if str(request_result.get("status") or "").strip() != "ok" or not interaction_id:
        raise RuntimeError("failed to create quest completion approval request")
    approval_message = chat_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        text=approval_text,
        source=source,
        reply_to_interaction_id=interaction_id,
    )
    if approval_message.get("ok") is not True:
        raise RuntimeError("failed to bind study-level approval into managed quest")
    completion_result = artifact_complete_quest(
        runtime_root=runtime_root,
        quest_id=quest_id,
        summary=summary,
    )
    completion_result = _normalize_stable_artifact_completion_result(payload=completion_result)
    if str(completion_result.get("status") or "").strip() not in {"completed", "already_completed"}:
        raise RuntimeError("managed quest completion did not reach completed state")
    return {
        "completion_request": request_result,
        "approval_message": approval_message,
        "completion": completion_result,
    }


def post_quest_control(
    *,
    quest_id: str,
    action: str,
    source: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    base_url = str(daemon_url or "").strip().rstrip("/")
    if not base_url:
        if runtime_root is None:
            raise ValueError("runtime_root or daemon_url is required")
        base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/control"
    try:
        return _normalize_stable_quest_control_result(
            payload=_post_json(url=url, payload={"action": action, "source": source})
        )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest control request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Quest control request failed: {exc}") from exc


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return post_quest_control(
        runtime_root=runtime_root,
        quest_id=quest_id,
        action="resume",
        source=source,
    )


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None | object = _UNSET,
    requested_baseline_ref: dict[str, Any] | None | object = _UNSET,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if startup_contract is not _UNSET:
        payload["startup_contract"] = startup_contract
    if requested_baseline_ref is not _UNSET:
        payload["requested_baseline_ref"] = requested_baseline_ref
    if not payload:
        raise ValueError("at least one startup-context field is required")
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return _normalize_stable_startup_context_result(
        payload=_patch_json(
            url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/startup-context",
            payload=payload,
        )
    )


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return post_quest_control(
        runtime_root=runtime_root,
        quest_id=quest_id,
        action="pause",
        source=source,
    )


def stop_quest(
    *,
    quest_id: str,
    source: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "quest_id": quest_id,
        "action": "stop",
        "source": source,
    }
    if daemon_url is not None:
        kwargs["daemon_url"] = daemon_url
    if runtime_root is not None:
        kwargs["runtime_root"] = runtime_root
    return post_quest_control(**kwargs)
