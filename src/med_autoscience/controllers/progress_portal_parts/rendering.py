from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from .workspace_overview import dedupe_texts


def condition_badge(conditions: Mapping[str, Any]) -> str:
    labels = []
    for key in ("missing", "stale", "conflict"):
        values = _string_list(conditions.get(key))
        if values:
            labels.append(f"{key}:{len(values)}")
    return ", ".join(labels) if labels else "clear"


def gate_text(study: Mapping[str, Any]) -> str:
    if bool(study.get("needs_physician_decision")):
        return "需要医生/PI 确认后继续。"
    return "当前没有投影出的医生/PI gate。"


def runtime_continuity_section(runtime_continuity: Mapping[str, Any]) -> str:
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
    return list_section("Runtime Continuity", items, empty_text="当前没有 runtime session / recovery intent 投影。")


def section(title: str, paragraphs: list[str]) -> str:
    body = "".join(f"<p>{escape(text)}</p>" for text in dedupe_texts(paragraphs) if text)
    return f'<section class="panel"><h2>{escape(title)}</h2>{body}</section>'


def list_section(title: str, items: list[str], *, empty_text: str) -> str:
    return f'<section class="panel wide"><h2>{escape(title)}</h2>{list_html(items, empty_text=empty_text)}</section>'


def event_section(events: list[dict[str, str]]) -> str:
    if not events:
        return list_section("最近进展", [], empty_text="当前没有带时间戳的进展事件。")
    items = [f"{item.get('timestamp') or 'unknown'} - {item.get('summary') or ''}" for item in events]
    return list_section("最近进展", items, empty_text="当前没有带时间戳的进展事件。")


def condition_section(conditions: Mapping[str, Any]) -> str:
    items = []
    for key in ("missing", "stale", "conflict"):
        for value in _string_list(conditions.get(key)):
            items.append(f"{key}: {value}")
    return list_section("stale / missing / conflict", items, empty_text="No stale, missing, or conflict conditions.")


def list_html(items: list[str], *, empty_text: str) -> str:
    if not items:
        return f"<p>{escape(empty_text)}</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def portal_css() -> str:
    return """
:root { color-scheme: light; --ink:#172026; --muted:#5d6972; --line:#d8dee4; --accent:#0f766e; --warn:#b45309; --bad:#b91c1c; --bg:#f7f9fb; --panel:#ffffff; }
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }
.portal { max-width: 1160px; margin: 0 auto; padding: 28px; }
.masthead { border-bottom: 1px solid var(--line); padding: 8px 0 22px; }
.brand { color: var(--accent); font-weight: 700; letter-spacing: 0; }
h1 { margin: 8px 0 4px; font-size: 32px; line-height: 1.15; }
h2 { margin: 0 0 10px; font-size: 17px; }
p { margin: 0 0 10px; line-height: 1.5; }
.state { color: var(--muted); font-size: 18px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 18px 0 0; }
.meta div { border: 1px solid var(--line); background: var(--panel); padding: 10px 12px; border-radius: 8px; }
dt { color: var(--muted); font-size: 12px; text-transform: uppercase; }
dd { margin: 3px 0 0; font-weight: 600; overflow-wrap: anywhere; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 18px 0 14px; }
.panel, .refs { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; }
.wide { margin-top: 14px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
.study-row.selected td { background: #eef8f6; }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; overflow-wrap: anywhere; }
summary { cursor: pointer; font-weight: 700; }
.refs { margin-top: 14px; }
@media (max-width: 760px) { .portal { padding: 18px; } .grid { grid-template-columns: 1fr; } h1 { font-size: 26px; } }
""".strip()


def refresh_meta(value: object) -> str:
    if isinstance(value, int) and value > 0:
        return f'<meta http-equiv="refresh" content="{value}">'
    return ""


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
