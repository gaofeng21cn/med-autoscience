from __future__ import annotations

from collections.abc import Iterable, Mapping
from html import escape
from typing import Any

from .local_time import local_time_projection
from .status_display import STATUS_LABELS, display_text, status_chip, status_label
from .workspace_overview import dedupe_texts


def condition_badge(conditions: Mapping[str, Any]) -> str:
    labels = []
    display_keys = {"missing": "缺失", "stale": "陈旧", "conflict": "冲突"}
    for key in ("missing", "stale", "conflict"):
        values = _string_list(conditions.get(key))
        if values:
            labels.append(f"{display_keys[key]}:{len(values)}")
    return ", ".join(labels) if labels else "无"


def gate_text(study: Mapping[str, Any]) -> str:
    if bool(study.get("needs_physician_decision")):
        return "需要医生/PI 确认后继续。"
    return "当前没有投影出的医生/PI gate。"


def runtime_continuity_section(runtime_continuity: Mapping[str, Any]) -> str:
    session = _mapping(runtime_continuity.get("runtime_session"))
    intent = _mapping(runtime_continuity.get("recovery_intent"))
    items = []
    if session:
        items.append(f"worker：{display_text(session.get('worker_state'), fallback='未提供')}")
        if session.get("active_run_id"):
            items.append(f"active run：{session.get('active_run_id')}")
        elif session.get("last_known_run_id"):
            items.append(f"last known run：{session.get('last_known_run_id')}")
        if session.get("last_seen_at"):
            items.append(f"last seen：{local_time_label(session.get('last_seen_at'))}")
        if session.get("freshness_state"):
            items.append(f"freshness：{display_text(session.get('freshness_state'), fallback='未提供')}")
    if intent:
        items.append(f"recovery action：{display_text(intent.get('current_action'), fallback='未提供')}")
        if intent.get("next_owner"):
            items.append(f"next owner：{intent.get('next_owner')}")
        if intent.get("next_eligible_tick"):
            items.append(f"next eligible tick：{local_time_label(intent.get('next_eligible_tick'))}")
    return list_section("运行连续性", items, empty_text="当前没有 runtime session / recovery intent 投影。")


def section(title: str, paragraphs: list[str]) -> str:
    body = "".join(f"<p>{escape(text)}</p>" for text in dedupe_texts(paragraphs) if text)
    return f'<section class="panel"><h2>{escape(title)}</h2>{body}</section>'


def list_section(title: str, items: list[str], *, empty_text: str) -> str:
    return f'<section class="panel wide"><h2>{escape(title)}</h2>{list_html(items, empty_text=empty_text)}</section>'


def event_section(events: list[dict[str, str]]) -> str:
    if not events:
        return list_section("最近进展", [], empty_text="当前没有带时间戳的进展事件。")
    items = [f"{local_time_label(item.get('timestamp'))} - {item.get('summary') or ''}" for item in events]
    return list_section("最近进展", items, empty_text="当前没有带时间戳的进展事件。")


def condition_section(conditions: Mapping[str, Any]) -> str:
    items = []
    for key in ("missing", "stale", "conflict"):
        for value in _string_list(conditions.get(key)):
            items.append(f"{STATUS_LABELS.get(key, key)}：{value}")
    return list_section("陈旧 / 缺失 / 冲突", items, empty_text="当前没有陈旧、缺失或冲突条件。")


def list_html(items: list[str], *, empty_text: str) -> str:
    if not items:
        return f"<p>{escape(empty_text)}</p>"
    return "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"


def local_time_label(value: object) -> str:
    text = str(value or "").strip()
    if not text or text == "unknown":
        return "时间未提供"
    projection = local_time_projection(text, timezone_name=None)
    label = str(projection.get("label") or text)
    if label == text:
        return label
    return f"{label} / 原始 {text}"


def portal_css() -> str:
    return """
:root { color-scheme: light; --ink:#172026; --muted:#5d6972; --line:#d8dee4; --accent:#0f766e; --warn:#8a5a00; --bad:#b91c1c; --ok:#047857; --bg:#f6f8fb; --panel:#ffffff; --soft:#eef8f6; --panel-alt:#fbfcfd; --code:#111827; }
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); font-size: 15px; line-height: 1.5; }
.portal { max-width: 1280px; margin: 0 auto; padding: 24px; }
.masthead { border: 1px solid var(--line); border-radius: 8px; background: var(--panel); padding: 22px; box-shadow: 0 1px 2px rgba(20, 32, 51, .04); }
.brand { color: var(--muted); font-weight: 700; letter-spacing: 0; }
h1 { margin: 8px 0 4px; font-size: 32px; line-height: 1.15; }
h2 { margin: 0 0 10px; font-size: 17px; }
p { margin: 0 0 10px; line-height: 1.5; }
.state { color: var(--muted); font-size: 18px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 18px 0 0; }
.meta div { border: 1px solid var(--line); background: var(--panel-alt); padding: 10px 12px; border-radius: 8px; min-width: 0; }
dt { color: var(--muted); font-size: 12px; }
dd { margin: 3px 0 0; font-weight: 600; overflow-wrap: anywhere; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 18px 0 14px; }
.panel, .refs { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(20, 32, 51, .03); }
.wide { margin-top: 14px; }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { color: var(--muted); font-size: 12px; }
tbody tr:hover td { background: #f7fafc; }
.study-row.selected td { background: #eef8f6; }
.status-chip { display: inline-flex; align-items: center; min-height: 24px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--line); font-size: 12px; font-weight: 650; line-height: 1.35; white-space: nowrap; }
.status-ok { color: var(--ok); background: #edf9f1; border-color: #b7e4c7; }
.status-warn { color: var(--warn); background: #fff7e6; border-color: #f0d18a; }
.status-bad { color: var(--bad); background: #fff1f1; border-color: #f0b9b9; }
.status-neutral { color: var(--muted); background: #f3f6f9; border-color: var(--line); }
.live-console-link { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-top: 16px; }
.live-console-link a, .live-console-link strong { color: var(--accent); font-weight: 750; }
.live-console-link span { color: var(--muted); overflow-wrap: anywhere; }
code { background: #eef2f6; border: 1px solid var(--line); border-radius: 5px; padding: 1px 5px; color: var(--code); }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; overflow-wrap: anywhere; }
summary { cursor: pointer; font-weight: 700; }
.refs { margin-top: 14px; }
@media (max-width: 760px) {
  .portal { padding: 18px; }
  .grid { grid-template-columns: 1fr; }
  h1 { font-size: 26px; }
  .table-wrap { overflow-x: visible; }
  table.responsive-table,
  table.responsive-table thead,
  table.responsive-table tbody,
  table.responsive-table tr,
  table.responsive-table th,
  table.responsive-table td { display: block; width: 100%; }
  table.responsive-table thead { display: none; }
  table.responsive-table tr {
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--panel-alt);
    margin: 0 0 10px;
    padding: 10px 12px;
  }
  table.responsive-table td {
    border-bottom: 0;
    padding: 6px 0;
    display: grid;
    grid-template-columns: minmax(96px, 38%) minmax(0, 1fr);
    gap: 10px;
  }
  table.responsive-table td::before {
    content: attr(data-label);
    color: var(--muted);
    font-size: 12px;
    font-weight: 700;
  }
}
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
