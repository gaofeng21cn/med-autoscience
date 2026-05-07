from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
import subprocess
from typing import Any
from urllib import error

from med_autoscience.runtime_transport.med_deepscientist_parts.storage import _load_json_dict


RunLauncher = Callable[..., subprocess.CompletedProcess[str]]
GetJson = Callable[..., Any]
ParseLauncherStatus = Callable[..., dict[str, Any]]


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


def _recover_launcher_status_from_runtime_state(*, runtime_root: Path, get_json: GetJson) -> dict[str, Any] | None:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    state = _load_json_dict(_daemon_state_path(resolved_runtime_root))
    if not state:
        return None
    url = str(state.get("url") or "").strip().rstrip("/")
    if not url:
        return None
    try:
        health = get_json(url=f"{url}/api/health")
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


def ensure_managed_daemon(
    *,
    runtime_root: Path,
    run_launcher: RunLauncher,
    parse_launcher_status: ParseLauncherStatus,
    get_json: GetJson,
) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    try:
        status_result = run_launcher(runtime_root=resolved_runtime_root, args=("--status",))
        try:
            status_payload = parse_launcher_status(result=status_result, runtime_root=resolved_runtime_root)
        except RuntimeError:
            recovered_status_payload = _recover_launcher_status_from_runtime_state(
                runtime_root=resolved_runtime_root,
                get_json=get_json,
            )
            if recovered_status_payload is None:
                raise
            status_payload = recovered_status_payload
        if (
            status_result.returncode == 0
            and bool(status_payload.get("healthy"))
            and bool(status_payload.get("identity_match"))
        ):
            return status_payload

        start_result = run_launcher(
            runtime_root=resolved_runtime_root,
            args=("--daemon-only", "--no-browser", "--skip-update-check"),
        )
        if start_result.returncode != 0:
            stderr = str(start_result.stderr or "").strip()
            stdout = str(start_result.stdout or "").strip()
            raise RuntimeError(
                f"med-deepscientist launcher failed to start daemon for {resolved_runtime_root}: {stderr or stdout or f'exit {start_result.returncode}'}"
            )

        status_result = run_launcher(runtime_root=resolved_runtime_root, args=("--status",))
        status_payload = parse_launcher_status(result=status_result, runtime_root=resolved_runtime_root)
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
