from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import error, request

from med_autoscience.runtime_transport.med_deepscientist_parts.storage import _load_json_dict, _load_yaml_dict


def _get_json(*, url: str, timeout: int) -> Any:
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
    timeout: int,
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


def resolve_daemon_url(*, runtime_root: Path, timeout: int) -> str:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    daemon_state = _load_json_dict(resolved_runtime_root / "runtime" / "daemon.json")
    daemon_url = str(daemon_state.get("url") or "").strip()
    if daemon_url and _daemon_url_matches_runtime_home(
        daemon_url=daemon_url,
        expected_home=resolved_runtime_root,
        timeout=timeout,
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
    timeout: int,
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


def _post_json(*, url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    return _request_json(url=url, payload=payload, method="POST", timeout=timeout)


def _patch_json(*, url: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    return _request_json(url=url, payload=payload, method="PATCH", timeout=timeout)
