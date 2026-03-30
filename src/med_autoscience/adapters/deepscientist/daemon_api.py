from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import request

import yaml


DEFAULT_DAEMON_TIMEOUT_SECONDS = 10


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing DeepScientist runtime config: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _normalize_local_host(host: str) -> str:
    normalized = host.strip() or "127.0.0.1"
    if normalized in {"0.0.0.0", "localhost"}:
        return "127.0.0.1"
    return normalized


def resolve_daemon_url(*, runtime_root: Path) -> str:
    config = _load_yaml_dict(Path(runtime_root).expanduser().resolve() / "config" / "config.yaml")
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
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
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


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return _post_json(
        url=f"{base_url}/api/quests/{quest_id}/control",
        payload={"action": "resume", "source": source},
    )
