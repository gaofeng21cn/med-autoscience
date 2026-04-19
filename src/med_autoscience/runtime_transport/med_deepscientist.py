from __future__ import annotations

from datetime import UTC, datetime
import json
import os
from pathlib import Path
import shlex
import subprocess
from typing import Any
from urllib import error, request
from urllib.parse import quote

import yaml

from med_autoscience.native_runtime_event import NativeRuntimeEventRecord
from med_autoscience.runtime_event_record import RuntimeEventRecordRef
from med_autoscience.startup_contract import stable_startup_contract


BACKEND_ID = "med_deepscientist"
ENGINE_ID = "med-deepscientist"
DEFAULT_DAEMON_TIMEOUT_SECONDS = 10
ACTIVE_BASH_SESSION_STATUSES = frozenset({"running", "terminating"})
_UNSET = object()


def _read_optional_config_env_value(*, path: Path, key: str) -> str | None:
    if not path.exists():
        return None
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
    return None


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
    value = _read_optional_config_env_value(path=path, key=key)
    if value is not None:
        return value
    if not path.exists():
        raise FileNotFoundError(f"missing med-deepscientist launcher config: {path}")
    raise ValueError(f"{key} is not configured in {path}")


def _read_launcher_text(*, launcher_path: Path) -> str | None:
    try:
        return launcher_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _launcher_looks_like_python_console_script(*, launcher_path: Path) -> bool:
    launcher_text = _read_launcher_text(launcher_path=launcher_path)
    if not launcher_text:
        return False
    return "from deepscientist.cli import main" in launcher_text


def _repo_root_from_repo_local_venv_path(*, path: Path) -> Path | None:
    resolved_path = Path(path).expanduser().resolve()
    if resolved_path.parent.name != "bin":
        return None
    venv_root = resolved_path.parent.parent
    if venv_root.name != ".venv":
        return None
    return venv_root.parent


def _companion_js_launcher_path(*, launcher_path: Path) -> Path | None:
    repo_root = _repo_root_from_repo_local_venv_path(path=launcher_path)
    if repo_root is None:
        return None
    candidate = repo_root / "bin" / "ds.js"
    if not candidate.exists():
        return None
    return candidate.resolve()


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
    if _launcher_looks_like_python_console_script(launcher_path=resolved_launcher_path):
        companion_launcher_path = _companion_js_launcher_path(launcher_path=resolved_launcher_path)
        if companion_launcher_path is None:
            raise ValueError(
                "MED_DEEPSCIENTIST_LAUNCHER points to a Python DeepScientist console script, "
                "but no compatible repo-local bin/ds.js launcher was found"
            )
        return companion_launcher_path
    return resolved_launcher_path


def _launcher_requires_node(*, launcher_path: Path) -> bool:
    launcher_text = _read_launcher_text(launcher_path=launcher_path)
    if not launcher_text:
        return False
    first_line = launcher_text.splitlines()[0] if launcher_text.splitlines() else ""
    if not first_line.startswith("#!"):
        return False
    return "node" in first_line


def _resolve_launcher_node_binary(*, runtime_root: Path) -> str | None:
    configured_node = str(os.environ.get("MED_AUTOSCIENCE_NODE_BIN") or "").strip()
    if not configured_node:
        workspace_root = Path(runtime_root).expanduser().resolve().parents[2]
        configured_value = _read_optional_config_env_value(
            path=workspace_root / "ops" / "medautoscience" / "config.env",
            key="MED_AUTOSCIENCE_NODE_BIN",
        )
        configured_node = str(configured_value or "").strip()
    if not configured_node:
        return None
    if not os.path.isabs(configured_node):
        raise ValueError(f"MED_AUTOSCIENCE_NODE_BIN must be an absolute path: {configured_node}")
    if not os.access(configured_node, os.X_OK):
        raise ValueError(f"MED_AUTOSCIENCE_NODE_BIN is not executable: {configured_node}")
    return configured_node


def _launcher_command(*, runtime_root: Path, args: tuple[str, ...]) -> list[str]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    launcher_path = _resolve_launcher_path(runtime_root=resolved_runtime_root)
    if _launcher_requires_node(launcher_path=launcher_path):
        node_binary = _resolve_launcher_node_binary(runtime_root=resolved_runtime_root)
        if node_binary:
            return [node_binary, str(launcher_path), "--home", str(resolved_runtime_root), *args]
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


def _daemon_state_path(runtime_root: Path) -> Path:
    return Path(runtime_root).expanduser().resolve() / "runtime" / "daemon.json"


def _normalize_health_home(health: dict[str, Any]) -> Path | None:
    raw_home = str(health.get("home") or "").strip()
    if not raw_home:
        return None
    try:
        return Path(raw_home).expanduser().resolve()
    except OSError:
        return None


def _health_matches_runtime_state(
    *,
    runtime_root: Path,
    state: dict[str, Any],
    health: dict[str, Any] | None,
) -> bool:
    if not isinstance(health, dict):
        return False
    if str(health.get("status") or "").strip().lower() != "ok":
        return False
    if _normalize_health_home(health) != Path(runtime_root).expanduser().resolve():
        return False
    state_daemon_id = str(state.get("daemon_id") or "").strip()
    health_daemon_id = str(health.get("daemon_id") or "").strip()
    if state_daemon_id and health_daemon_id:
        return state_daemon_id == health_daemon_id
    return not state_daemon_id and not health_daemon_id


def _recover_launcher_status_from_runtime_state(*, runtime_root: Path) -> dict[str, Any] | None:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    state = _load_json_dict(_daemon_state_path(resolved_runtime_root))
    if not state:
        return None
    url = str(state.get("url") or "").strip().rstrip("/")
    if not url:
        return None
    try:
        health = _get_json(url=f"{url}/api/health")
    except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        health = None
    if health is not None and not isinstance(health, dict):
        health = None
    healthy = isinstance(health, dict) and str(health.get("status") or "").strip().lower() == "ok"
    identity_match = _health_matches_runtime_state(
        runtime_root=resolved_runtime_root,
        state=state,
        health=health if isinstance(health, dict) else None,
    )
    return {
        "healthy": healthy,
        "identity_match": identity_match,
        "managed": True,
        "home": str(resolved_runtime_root),
        "url": url,
        "daemon": state,
        "health": health,
    }


def ensure_managed_daemon(*, runtime_root: Path) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    try:
        status_result = _run_launcher(runtime_root=resolved_runtime_root, args=("--status",))
        try:
            status_payload = _parse_launcher_status(result=status_result, runtime_root=resolved_runtime_root)
        except RuntimeError:
            recovered_status_payload = _recover_launcher_status_from_runtime_state(runtime_root=resolved_runtime_root)
            if recovered_status_payload is None:
                raise
            status_payload = recovered_status_payload
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
    normalized_payload = dict(payload)
    runtime_event_ref_payload = payload.get("runtime_event_ref")
    runtime_event_payload = payload.get("runtime_event")
    normalized_runtime_event_ref: dict[str, str] | None = None
    normalized_runtime_event: dict[str, Any] | None = None
    runtime_event_contract_errors: dict[str, str] = {}
    if runtime_event_ref_payload is not None:
        try:
            normalized_runtime_event_ref = RuntimeEventRecordRef.from_payload(runtime_event_ref_payload).to_dict()
        except (TypeError, ValueError) as exc:
            runtime_event_contract_errors["runtime_event_ref_contract_error"] = str(exc)
    if runtime_event_payload is not None:
        try:
            native_runtime_event = NativeRuntimeEventRecord.from_payload(runtime_event_payload)
            if native_runtime_event.quest_id != quest_id:
                raise ValueError("stable quest session runtime_event quest_id mismatch")
        except (TypeError, ValueError) as exc:
            runtime_event_contract_errors["runtime_event_contract_error"] = str(exc)
            normalized_runtime_event_ref = None
        else:
            normalized_runtime_event = native_runtime_event.to_dict()
            native_runtime_event_ref: dict[str, str] | None = None
            try:
                native_runtime_event_ref = native_runtime_event.ref().to_dict()
            except ValueError:
                native_runtime_event_ref = None
            if (
                normalized_runtime_event_ref is not None
                and native_runtime_event_ref is not None
                and native_runtime_event_ref != normalized_runtime_event_ref
            ):
                runtime_event_contract_errors["runtime_event_ref_contract_error"] = (
                    "stable quest session runtime_event_ref mismatch against runtime_event"
                )
            if native_runtime_event_ref is not None:
                normalized_runtime_event_ref = native_runtime_event_ref
    if normalized_runtime_event_ref is not None:
        normalized_payload["runtime_event_ref"] = normalized_runtime_event_ref
    else:
        normalized_payload.pop("runtime_event_ref", None)
    if normalized_runtime_event is not None:
        normalized_payload["runtime_event"] = normalized_runtime_event
    else:
        normalized_payload.pop("runtime_event", None)
    normalized_payload.update(runtime_event_contract_errors)
    return normalized_payload


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
    try:
        startup_contract = _normalize_startup_contract_for_stable_transport(
            startup_contract=snapshot.get("startup_contract")
        )
    except ValueError as exc:
        raise RuntimeError(str(exc)) from exc
    if not isinstance(startup_contract, dict):
        raise RuntimeError("missing stable startup-context contract")
    normalized_snapshot = dict(snapshot)
    normalized_snapshot["startup_contract"] = startup_contract
    normalized_payload = dict(payload)
    normalized_payload["snapshot"] = normalized_snapshot
    return normalized_payload


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


def _interaction_watchdog_payload(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    payload = snapshot.get("interaction_watchdog")
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _stale_progress_watchdog(interaction_watchdog: dict[str, Any] | None) -> bool:
    if not isinstance(interaction_watchdog, dict):
        return False
    if "stale_visibility_gap" in interaction_watchdog:
        return bool(interaction_watchdog.get("stale_visibility_gap"))
    silence_seconds = interaction_watchdog.get("seconds_since_last_artifact_interact")
    try:
        resolved_silence_seconds = int(silence_seconds)
    except (TypeError, ValueError):
        return False
    return bool(interaction_watchdog.get("inspection_due")) and resolved_silence_seconds >= 30 * 60


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

    interaction_watchdog = _interaction_watchdog_payload(snapshot)
    stale_progress = status == "live" and _stale_progress_watchdog(interaction_watchdog)
    result = {
        "ok": bool(runtime_audit.get("ok", True)),
        "status": status,
        "source": str(runtime_audit.get("source") or "quest_session_runtime_audit"),
        "active_run_id": active_run_id,
        "worker_running": bool(runtime_audit.get("worker_running")) if "worker_running" in runtime_audit else None,
        "worker_pending": bool(runtime_audit.get("worker_pending")) if "worker_pending" in runtime_audit else None,
        "stop_requested": bool(runtime_audit.get("stop_requested")) if "stop_requested" in runtime_audit else None,
    }
    runtime_event_contract_error = str(payload.get("runtime_event_contract_error") or "").strip() or None
    if runtime_event_contract_error is not None:
        result["runtime_event_contract_error"] = runtime_event_contract_error
    runtime_event_ref_contract_error = str(payload.get("runtime_event_ref_contract_error") or "").strip() or None
    if runtime_event_ref_contract_error is not None:
        result["runtime_event_ref_contract_error"] = runtime_event_ref_contract_error
    runtime_event_ref_payload = payload.get("runtime_event_ref")
    if isinstance(runtime_event_ref_payload, dict):
        result["runtime_event_ref"] = dict(runtime_event_ref_payload)
    runtime_event_payload = payload.get("runtime_event")
    if isinstance(runtime_event_payload, dict):
        result["runtime_event"] = dict(runtime_event_payload)
    if interaction_watchdog is not None:
        result["interaction_watchdog"] = interaction_watchdog
    if stale_progress:
        result["stale_progress"] = True
        result["liveness_guard_reason"] = "stale_progress_watchdog"
    return result


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
    stale_progress = bool(runtime_audit.get("stale_progress"))
    liveness_guard_reason = str(runtime_audit.get("liveness_guard_reason") or "").strip() or None
    if stale_progress:
        status = "unknown"
        ok = False
    elif runtime_live or bash_live:
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
    if isinstance(runtime_audit.get("runtime_event_ref"), dict):
        payload["runtime_event_ref"] = dict(runtime_audit.get("runtime_event_ref") or {})
    if isinstance(runtime_audit.get("runtime_event"), dict):
        payload["runtime_event"] = dict(runtime_audit.get("runtime_event") or {})
    if stale_progress:
        payload["stale_progress"] = True
    if liveness_guard_reason is not None:
        payload["liveness_guard_reason"] = liveness_guard_reason
    errors: list[str] = []
    if stale_progress:
        errors.append("Live managed runtime exceeded the artifact interaction silence threshold.")
    errors.extend(str(item) for item in [runtime_audit.get("error"), bash_session_audit.get("error")] if item)
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
        "continuation_reason": str(runtime_state.get("continuation_reason") or "").strip() or None,
    }


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = _ensure_managed_daemon_url(runtime_root=runtime_root)
    try:
        return _normalize_stable_quest_create_result(
            payload=_post_json(url=f"{base_url}/api/quests", payload=payload)
        )
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
    decision_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    payload: dict[str, Any] = {"text": text, "source": source}
    if reply_to_interaction_id:
        payload["reply_to_interaction_id"] = reply_to_interaction_id
    if isinstance(decision_response, dict):
        payload["decision_response"] = decision_response
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


def _normalize_startup_contract_for_stable_transport(
    *,
    startup_contract: dict[str, Any] | None | object,
) -> dict[str, Any] | None | object:
    if startup_contract is _UNSET or startup_contract is None:
        return startup_contract
    if not isinstance(startup_contract, dict):
        raise ValueError("startup_contract must be a mapping or null")
    return stable_startup_contract(startup_contract)


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None | object = _UNSET,
    requested_baseline_ref: dict[str, Any] | None | object = _UNSET,
) -> dict[str, Any]:
    normalized_startup_contract = _normalize_startup_contract_for_stable_transport(startup_contract=startup_contract)
    payload: dict[str, Any] = {}
    if normalized_startup_contract is not _UNSET:
        payload["startup_contract"] = normalized_startup_contract
    if requested_baseline_ref is not _UNSET:
        payload["requested_baseline_ref"] = requested_baseline_ref
    if not payload:
        raise ValueError("at least one startup-context field is required")
    base_url = _ensure_managed_daemon_url(runtime_root=runtime_root)
    try:
        result = _normalize_stable_startup_context_result(
            payload=_patch_json(
                url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/startup-context",
                payload=payload,
            )
        )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest startup-context request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Quest startup-context request failed: {exc}") from exc
    except (TimeoutError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Quest startup-context request failed: {exc}") from exc
    snapshot = result.get("snapshot") if isinstance(result.get("snapshot"), dict) else {}
    if normalized_startup_contract is not _UNSET and snapshot.get("startup_contract") != normalized_startup_contract:
        raise RuntimeError("missing stable startup-context startup_contract roundtrip")
    if requested_baseline_ref is not _UNSET and snapshot.get("requested_baseline_ref") != requested_baseline_ref:
        raise RuntimeError("missing stable startup-context requested_baseline_ref roundtrip")
    return result


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
