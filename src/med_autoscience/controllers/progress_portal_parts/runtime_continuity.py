from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any


def render_runtime_continuity_section(runtime_continuity: Mapping[str, Any]) -> str:
    session = _mapping(runtime_continuity.get("runtime_session"))
    intent = _mapping(runtime_continuity.get("recovery_intent"))
    items = []
    if session:
        items.append(f"worker: {session.get('worker_state') or 'unknown'}")
        if session.get("active_run_id"):
            items.append(f"active run: {session.get('active_run_id')}")
        elif session.get("last_known_run_id"):
            items.append(f"last known run: {session.get('last_known_run_id')}")
        if session.get("last_seen_at"):
            items.append(f"last seen: {session.get('last_seen_at')}")
        if session.get("freshness_state"):
            items.append(f"freshness: {session.get('freshness_state')}")
    if intent:
        items.append(f"recovery action: {intent.get('current_action') or 'unknown'}")
        if intent.get("next_owner"):
            items.append(f"next owner: {intent.get('next_owner')}")
        if intent.get("next_eligible_tick"):
            items.append(f"next eligible tick: {intent.get('next_eligible_tick')}")
    return _list_section("Runtime Continuity", items, empty_text="当前没有 runtime session / recovery intent 投影。")


def _list_section(title: str, items: list[str], *, empty_text: str) -> str:
    return f'<section class="panel wide"><h2>{escape(title)}</h2>{_list_html(items, empty_text=empty_text)}</section>'


def _list_html(items: list[str], *, empty_text: str) -> str:
    if not items:
        return f"<p>{escape(empty_text)}</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["render_runtime_continuity_section"]
