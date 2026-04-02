from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import quote

import yaml


DEFAULT_DAEMON_TIMEOUT_SECONDS = 10


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


def _post_json(*, url: str, payload: dict[str, Any], timeout: int = DEFAULT_DAEMON_TIMEOUT_SECONDS) -> dict[str, Any]:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/json"},
        method="POST",
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


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return _post_json(url=f"{base_url}/api/quests", payload=payload)


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
        return _post_json(url=url, payload={"action": action, "source": source})
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


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    return post_quest_control(
        runtime_root=runtime_root,
        quest_id=quest_id,
        action="pause",
        source=source,
    )
