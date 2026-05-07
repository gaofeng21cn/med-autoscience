from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path
from typing import Any
from urllib import error
from urllib.parse import quote


EnsureManagedDaemonUrl = Callable[..., str]
ResolveDaemonUrl = Callable[..., str]
PostJson = Callable[..., dict[str, Any]]
PatchJson = Callable[..., dict[str, Any]]
NormalizePayload = Callable[..., dict[str, Any]]
NormalizeStartupContract = Callable[..., dict[str, Any] | None | object]
PostQuestControl = Callable[..., dict[str, Any]]


def create_quest(
    *,
    runtime_root: Path,
    payload: dict[str, Any],
    ensure_managed_daemon_url: EnsureManagedDaemonUrl,
    post_json: PostJson,
    normalize_quest_create_result: NormalizePayload,
) -> dict[str, Any]:
    base_url = ensure_managed_daemon_url(runtime_root=runtime_root)
    try:
        return normalize_quest_create_result(
            payload=post_json(url=f"{base_url}/api/quests", payload=payload)
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
    resolve_daemon_url: ResolveDaemonUrl,
    post_json: PostJson,
    reply_to_interaction_id: str | None = None,
    decision_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    payload: dict[str, Any] = {"text": text, "source": source}
    if reply_to_interaction_id:
        payload["reply_to_interaction_id"] = reply_to_interaction_id
    if isinstance(decision_response, dict):
        payload["decision_response"] = decision_response
    return post_json(url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/chat", payload=payload)


def artifact_interact(
    *,
    runtime_root: Path,
    quest_id: str,
    payload: dict[str, Any],
    resolve_daemon_url: ResolveDaemonUrl,
    post_json: PostJson,
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return post_json(
        url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/artifact/interact",
        payload=payload,
    )


def artifact_complete_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    summary: str,
    resolve_daemon_url: ResolveDaemonUrl,
    post_json: PostJson,
) -> dict[str, Any]:
    base_url = resolve_daemon_url(runtime_root=runtime_root)
    return post_json(
        url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/artifact/complete",
        payload={"summary": summary},
    )


def post_quest_control(
    *,
    quest_id: str,
    action: str,
    source: str,
    resolve_daemon_url: ResolveDaemonUrl,
    ensure_managed_daemon_url: EnsureManagedDaemonUrl,
    post_json: PostJson,
    normalize_quest_control_result: NormalizePayload,
    daemon_control_timeout_seconds: int,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    base_url = str(daemon_url or "").strip().rstrip("/")
    if not base_url:
        if runtime_root is None:
            raise ValueError("runtime_root or daemon_url is required")
        if action == "resume":
            base_url = ensure_managed_daemon_url(runtime_root=runtime_root)
        else:
            base_url = resolve_daemon_url(runtime_root=runtime_root)
    url = f"{base_url}/api/quests/{quote(quest_id, safe='')}/control"
    try:
        return normalize_quest_control_result(
            payload=post_json(
                url=url,
                payload={"action": action, "source": source},
                timeout=daemon_control_timeout_seconds,
            )
        )
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Quest control request failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Quest control request failed: {exc}") from exc
    except (TimeoutError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Quest control request failed: {exc}") from exc


def resume_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    source: str,
    post_quest_control_fn: PostQuestControl,
) -> dict[str, Any]:
    return post_quest_control_fn(
        runtime_root=runtime_root,
        quest_id=quest_id,
        action="resume",
        source=source,
    )


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    normalize_startup_contract: NormalizeStartupContract,
    ensure_managed_daemon_url: EnsureManagedDaemonUrl,
    patch_json: PatchJson,
    normalize_startup_context_result: NormalizePayload,
    daemon_control_timeout_seconds: int,
    unset: object,
    startup_contract: dict[str, Any] | None | object,
    requested_baseline_ref: dict[str, Any] | None | object,
) -> dict[str, Any]:
    normalized_startup_contract = normalize_startup_contract(startup_contract=startup_contract)
    payload: dict[str, Any] = {}
    if normalized_startup_contract is not unset:
        payload["startup_contract"] = normalized_startup_contract
    if requested_baseline_ref is not unset:
        payload["requested_baseline_ref"] = requested_baseline_ref
    if not payload:
        raise ValueError("at least one startup-context field is required")
    base_url = ensure_managed_daemon_url(runtime_root=runtime_root)
    try:
        result = normalize_startup_context_result(
            payload=patch_json(
                url=f"{base_url}/api/quests/{quote(quest_id, safe='')}/startup-context",
                payload=payload,
                timeout=daemon_control_timeout_seconds,
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
    if normalized_startup_contract is not unset and snapshot.get("startup_contract") != normalized_startup_contract:
        raise RuntimeError("missing stable startup-context startup_contract roundtrip")
    if requested_baseline_ref is not unset and snapshot.get("requested_baseline_ref") != requested_baseline_ref:
        raise RuntimeError("missing stable startup-context requested_baseline_ref roundtrip")
    return result


def pause_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    source: str,
    post_quest_control_fn: PostQuestControl,
) -> dict[str, Any]:
    return post_quest_control_fn(
        runtime_root=runtime_root,
        quest_id=quest_id,
        action="pause",
        source=source,
    )


def stop_quest(
    *,
    quest_id: str,
    source: str,
    post_quest_control_fn: PostQuestControl,
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
    return post_quest_control_fn(**kwargs)
