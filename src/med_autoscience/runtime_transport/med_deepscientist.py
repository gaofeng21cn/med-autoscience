from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import shlex
import subprocess
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


def _write_yaml_dict(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _write_json_dict(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_config_env_value(*, path: Path, key: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"missing med-deepscientist launcher config: {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        lhs, rhs = stripped.split("=", 1)
        normalized_key = lhs.removeprefix("export ").strip()
        if normalized_key != key:
            continue
        value = rhs.strip()
        if not value:
            raise ValueError(f"{key} is empty in {path}")
        try:
            tokens = shlex.split(value, posix=True)
        except ValueError as exc:
            raise ValueError(f"invalid {key} assignment in {path}") from exc
        if len(tokens) != 1 or not tokens[0].strip():
            raise ValueError(f"{key} must resolve to one absolute path in {path}")
        return tokens[0].strip()
    raise ValueError(f"{key} is not configured in {path}")


def _resolve_launcher_path(*, runtime_root: Path) -> Path:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    launcher_value = _read_config_env_value(
        path=resolved_runtime_root.parent / "config.env",
        key="MED_DEEPSCIENTIST_LAUNCHER",
    )
    launcher_path = Path(launcher_value).expanduser()
    if not launcher_path.is_absolute():
        raise ValueError(f"MED_DEEPSCIENTIST_LAUNCHER must be an absolute path: {launcher_value}")
    resolved_launcher_path = launcher_path.resolve()
    if not resolved_launcher_path.exists():
        raise FileNotFoundError(f"med-deepscientist launcher does not exist: {resolved_launcher_path}")
    return resolved_launcher_path


def _launcher_command(*, runtime_root: Path, args: tuple[str, ...]) -> list[str]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    launcher_path = _resolve_launcher_path(runtime_root=resolved_runtime_root)
    return [str(launcher_path), "--home", str(resolved_runtime_root), *args]


def _run_launcher(
    *,
    runtime_root: Path,
    args: tuple[str, ...],
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _launcher_command(runtime_root=runtime_root, args=args),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def _parse_launcher_status(
    *,
    result: subprocess.CompletedProcess[str],
    runtime_root: Path,
) -> dict[str, Any]:
    stdout = str(result.stdout or "").strip()
    if not stdout:
        stderr = str(result.stderr or "").strip()
        raise RuntimeError(
            f"med-deepscientist launcher returned empty status for {Path(runtime_root).expanduser().resolve()}: {stderr or 'no output'}"
        )
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"med-deepscientist launcher returned non-JSON status for {Path(runtime_root).expanduser().resolve()}: {stdout}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError("med-deepscientist launcher status payload must be a JSON object")
    return payload


def ensure_managed_daemon(*, runtime_root: Path) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    try:
        status_result = _run_launcher(runtime_root=resolved_runtime_root, args=("--status",))
        status_payload = _parse_launcher_status(result=status_result, runtime_root=resolved_runtime_root)
        if (
            status_result.returncode == 0
            and bool(status_payload.get("healthy"))
            and bool(status_payload.get("identity_match"))
        ):
            return status_payload

        start_result = _run_launcher(
            runtime_root=resolved_runtime_root,
            args=("--daemon-only", "--no-browser", "--skip-update-check"),
        )
        if start_result.returncode != 0:
            stderr = str(start_result.stderr or "").strip()
            stdout = str(start_result.stdout or "").strip()
            raise RuntimeError(
                f"med-deepscientist launcher failed to start daemon for {resolved_runtime_root}: {stderr or stdout or f'exit {start_result.returncode}'}"
            )

        status_result = _run_launcher(runtime_root=resolved_runtime_root, args=("--status",))
        status_payload = _parse_launcher_status(result=status_result, runtime_root=resolved_runtime_root)
        if (
            status_result.returncode == 0
            and bool(status_payload.get("healthy"))
            and bool(status_payload.get("identity_match"))
        ):
            return status_payload

        raise RuntimeError(
            f"med-deepscientist daemon did not become healthy for {resolved_runtime_root}: {json.dumps(status_payload, ensure_ascii=False)}"
        )
    except (FileNotFoundError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError(
            f"med-deepscientist launcher contract failed for {resolved_runtime_root}: {exc}"
        ) from exc


def _ensure_managed_daemon_url(*, runtime_root: Path) -> str:
    daemon_status = ensure_managed_daemon(runtime_root=runtime_root)
    daemon_url = str(daemon_status.get("url") or "").strip().rstrip("/")
    if not daemon_url:
        raise RuntimeError("med-deepscientist launcher status is missing daemon url")
    return daemon_url


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


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
        sessions.append(item)
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
    return dict(payload)


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
        local_runtime_liveness = (
            _infer_local_runtime_liveness(runtime_root=runtime_root, quest_id=quest_id)
            if runtime_root is not None
            else None
        )
        if local_runtime_liveness is not None:
            payload = {
                "ok": True,
                "status": "none",
                "source": "local_runtime_state_contract",
                "active_run_id": local_runtime_liveness.get("active_run_id"),
                "runner_live": False,
                "bash_live": False,
                "runtime_audit": runtime_audit,
                "bash_session_audit": bash_session_audit,
                "local_runtime_state": local_runtime_liveness,
            }
            errors = [str(item) for item in [runtime_audit.get("error"), bash_session_audit.get("error")] if item]
            if errors:
                payload["probe_error"] = " | ".join(errors)
            return payload
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


def _infer_local_runtime_liveness(*, runtime_root: Path, quest_id: str) -> dict[str, Any] | None:
    quest_root = Path(runtime_root).expanduser().resolve() / "quests" / quest_id
    quest_yaml_path = quest_root / "quest.yaml"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    if not quest_yaml_path.exists():
        return None
    quest_data = _load_yaml_dict(quest_yaml_path)
    runtime_state = _load_json_dict(runtime_state_path)
    status = str(runtime_state.get("status") or quest_data.get("status") or "").strip()
    active_run_id = str(runtime_state.get("active_run_id") or quest_data.get("active_run_id") or "").strip() or None
    if active_run_id or status == "running":
        return None
    return {
        "status": status or None,
        "active_run_id": active_run_id,
        "continuation_policy": str(runtime_state.get("continuation_policy") or "").strip() or None,
        "continuation_anchor": str(runtime_state.get("continuation_anchor") or "").strip() or None,
    }


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = _ensure_managed_daemon_url(runtime_root=runtime_root)
    try:
        return _post_json(url=f"{base_url}/api/quests", payload=payload)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest create request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Quest create request failed: {exc}") from exc
    except (TimeoutError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Quest create request failed: {exc}") from exc


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
        if action == "resume":
            base_url = _ensure_managed_daemon_url(runtime_root=runtime_root)
        else:
            base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/control"
    try:
        return _post_json(url=url, payload={"action": action, "source": source})
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest control request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        if runtime_root is not None and action in {"pause", "stop"}:
            return _update_quest_control_locally(
                runtime_root=runtime_root,
                quest_id=quest_id,
                action=action,
                source=source,
            )
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
    try:
        return _patch_json(
            url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/startup-context",
            payload=payload,
        )
    except error.URLError:
        return _update_quest_startup_context_locally(
            runtime_root=runtime_root,
            quest_id=quest_id,
            startup_contract=startup_contract,
            requested_baseline_ref=requested_baseline_ref,
        )


def _update_quest_startup_context_locally(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None | object = _UNSET,
    requested_baseline_ref: dict[str, Any] | None | object = _UNSET,
) -> dict[str, Any]:
    quest_yaml_path = Path(runtime_root).expanduser().resolve() / "quests" / quest_id / "quest.yaml"
    if not quest_yaml_path.exists():
        raise FileNotFoundError(f"Unknown quest `{quest_id}`.")
    quest_data = _load_yaml_dict(quest_yaml_path)
    changed = False

    if requested_baseline_ref is not _UNSET:
        normalized_requested = dict(requested_baseline_ref) if isinstance(requested_baseline_ref, dict) else None
        if quest_data.get("requested_baseline_ref") != normalized_requested:
            quest_data["requested_baseline_ref"] = normalized_requested
            changed = True

    if startup_contract is not _UNSET:
        normalized_contract = dict(startup_contract) if isinstance(startup_contract, dict) else None
        if quest_data.get("startup_contract") != normalized_contract:
            quest_data["startup_contract"] = normalized_contract
            changed = True

    if changed:
        quest_data["updated_at"] = _utc_now()
        _write_yaml_dict(quest_yaml_path, quest_data)

    return {
        "ok": True,
        "sync_mode": "local_file",
        "snapshot": quest_data,
    }


def _update_quest_control_locally(
    *,
    runtime_root: Path,
    quest_id: str,
    action: str,
    source: str,
) -> dict[str, Any]:
    if action not in {"pause", "stop"}:
        raise ValueError(f"unsupported local quest control action `{action}`")
    quest_root = Path(runtime_root).expanduser().resolve() / "quests" / quest_id
    quest_yaml_path = quest_root / "quest.yaml"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    if not quest_yaml_path.exists():
        raise FileNotFoundError(f"Unknown quest `{quest_id}`.")

    quest_data = _load_yaml_dict(quest_yaml_path)
    runtime_state = _load_json_dict(runtime_state_path)
    active_run_id = str(runtime_state.get("active_run_id") or quest_data.get("active_run_id") or "").strip()
    if active_run_id:
        raise RuntimeError(
            "Quest control request failed and local fallback is unsafe while active_run_id is still set."
        )

    next_status = "paused" if action == "pause" else "stopped"
    now = _utc_now()
    if not runtime_state:
        runtime_state = {"quest_id": quest_id}
    runtime_state["quest_id"] = str(runtime_state.get("quest_id") or quest_id).strip() or quest_id
    runtime_state["status"] = next_status
    runtime_state["display_status"] = next_status
    runtime_state["active_run_id"] = None
    runtime_state["stop_reason"] = f"user_{action}"
    runtime_state["last_transition_at"] = now
    _write_json_dict(runtime_state_path, runtime_state)

    quest_data["status"] = next_status
    quest_data.pop("active_run_id", None)
    quest_data["updated_at"] = now
    _write_yaml_dict(quest_yaml_path, quest_data)

    snapshot = dict(quest_data)
    snapshot["status"] = runtime_state["status"]
    snapshot["active_run_id"] = runtime_state["active_run_id"]
    if "stop_reason" in runtime_state:
        snapshot["stop_reason"] = runtime_state["stop_reason"]
    return {
        "ok": True,
        "sync_mode": "local_file",
        "action": action,
        "source": source,
        "status": next_status,
        "snapshot": snapshot,
    }


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
