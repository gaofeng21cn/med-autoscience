from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import Any
from urllib import error
from urllib.parse import quote


ACTIVE_BASH_SESSION_STATUSES = frozenset({"running", "terminating"})

GetJson = Callable[..., Any]
ResolveDaemonUrl = Callable[..., str]
NormalizeQuestSession = Callable[..., dict[str, Any]]
NormalizeBashSessionEntry = Callable[..., dict[str, Any]]
ListQuestBashSessions = Callable[..., list[dict[str, Any]]]
GetQuestSession = Callable[..., dict[str, Any]]


def list_quest_bash_sessions(
    *,
    quest_id: str,
    get_json: GetJson,
    resolve_daemon_url: ResolveDaemonUrl,
    normalize_bash_session_entry: NormalizeBashSessionEntry,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int,
) -> list[dict[str, Any]]:
    base_url = str(daemon_url or "").strip().rstrip("/")
    if not base_url:
        if runtime_root is None:
            raise ValueError("runtime_root or daemon_url is required")
        base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/bash/sessions?limit=200"
    try:
        payload = get_json(url=url, timeout=timeout)
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
        sessions.append(normalize_bash_session_entry(payload=item))
    return sessions


def get_quest_session(
    *,
    quest_id: str,
    get_json: GetJson,
    resolve_daemon_url: ResolveDaemonUrl,
    normalize_quest_session: NormalizeQuestSession,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int,
) -> dict[str, Any]:
    base_url = str(daemon_url or "").strip().rstrip("/")
    if not base_url:
        if runtime_root is None:
            raise ValueError("runtime_root or daemon_url is required")
        base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/session"
    try:
        payload = get_json(url=url, timeout=timeout)
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
    return normalize_quest_session(payload=dict(payload))


def inspect_quest_live_bash_sessions(
    *,
    quest_id: str,
    list_quest_bash_sessions_fn: ListQuestBashSessions,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int,
) -> dict[str, Any]:
    try:
        sessions = list_quest_bash_sessions_fn(
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
