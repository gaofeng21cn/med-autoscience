from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any


def render_runtime_continuity_section(runtime_continuity: Mapping[str, Any]) -> str:
    session = _mapping(runtime_continuity.get("runtime_session"))
    intent = _mapping(runtime_continuity.get("recovery_intent"))
    items = _runtime_session_items(session) + _recovery_intent_items(intent)
    return _list_section("Runtime Continuity", items, empty_text="当前没有 runtime session / recovery intent 投影。")


def _runtime_session_items(session: Mapping[str, Any]) -> list[str]:
    if not session:
        return []
    items = [
        f"worker: {session.get('worker_state') or 'unknown'}",
    ]
    items.extend(_run_identity_items(session))
    items.extend(_worker_observation_items(session))
    items.extend(_monitor_items(session))
    return items


def _run_identity_items(session: Mapping[str, Any]) -> list[str]:
    if session.get("active_run_id"):
        return [f"active run: {session.get('active_run_id')}"]
    if session.get("last_known_run_id"):
        return [f"last known run: {session.get('last_known_run_id')}"]
    return []


def _worker_observation_items(session: Mapping[str, Any]) -> list[str]:
    items = []
    if session.get("last_seen_at"):
        items.append(f"last seen: {session.get('last_seen_at')}")
    if session.get("heartbeat_age_seconds") is not None:
        items.append(f"last worker heartbeat: {session.get('heartbeat_age_seconds')}s ago")
    if session.get("last_output_at"):
        items.append(f"last output: {session.get('last_output_at')}")
    return items


def _monitor_items(session: Mapping[str, Any]) -> list[str]:
    items = []
    if session.get("monitor_kind") or session.get("monitor_state"):
        items.append(f"monitor owner: {session.get('monitor_kind') or 'unknown'} / {session.get('monitor_state') or 'unknown'}")
    if session.get("stale_reason"):
        items.append(f"why waiting: {session.get('stale_reason')}")
    if session.get("will_start_llm") is not None:
        items.append(f"will start LLM: {'yes' if session.get('will_start_llm') else 'no'}")
    if session.get("freshness_state"):
        items.append(f"freshness: {session.get('freshness_state')}")
    return items


def _recovery_intent_items(intent: Mapping[str, Any]) -> list[str]:
    if not intent:
        return []
    items = [f"recovery action: {intent.get('current_action') or 'unknown'}"]
    if intent.get("next_owner"):
        items.append(f"next owner: {intent.get('next_owner')}")
    if intent.get("next_eligible_tick"):
        items.append(f"next eligible tick: {intent.get('next_eligible_tick')}")
    return items


def _list_section(title: str, items: list[str], *, empty_text: str) -> str:
    return f'<section class="panel wide"><h2>{escape(title)}</h2>{_list_html(items, empty_text=empty_text)}</section>'


def _list_html(items: list[str], *, empty_text: str) -> str:
    if not items:
        return f"<p>{escape(empty_text)}</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["render_runtime_continuity_section"]
