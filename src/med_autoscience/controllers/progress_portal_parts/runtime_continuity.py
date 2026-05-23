from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any


def render_runtime_continuity_section(runtime_continuity: Mapping[str, Any]) -> str:
    handoff = _mapping(runtime_continuity.get("domain_authority_handoff"))
    items = _domain_authority_items(handoff)
    return _list_section("OPL 控制面交接", items, empty_text="当前没有 MAS domain authority handoff 投影。")


def _domain_authority_items(handoff: Mapping[str, Any]) -> list[str]:
    if not handoff:
        return []
    owner_route = _mapping(handoff.get("owner_route"))
    typed_blocker = _mapping(handoff.get("typed_blocker"))
    items = [
        f"handoff status: {handoff.get('status') or 'unknown'}",
    ]
    if owner_route.get("next_owner"):
        items.append(f"next owner: {owner_route.get('next_owner')}")
    if owner_route.get("idempotency_key"):
        items.append(f"route idempotency key: {owner_route.get('idempotency_key')}")
    if typed_blocker.get("reason"):
        items.append(f"typed blocker: {typed_blocker.get('reason')}")
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
