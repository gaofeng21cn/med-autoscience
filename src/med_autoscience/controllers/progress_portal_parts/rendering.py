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
    items = _runtime_session_continuity_items(session)
    items.extend(_recovery_intent_continuity_items(intent))
    return list_section("运行连续性", items, empty_text="当前没有 runtime session / recovery intent 投影。")


def _runtime_session_continuity_items(session: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    if session:
        items.append(f"worker：{display_text(session.get('worker_state'), fallback='未提供')}")
        if session.get("active_run_id"):
            items.append(f"active run：{session.get('active_run_id')}")
        elif session.get("last_known_run_id"):
            items.append(f"last known run：{session.get('last_known_run_id')}")
        if session.get("last_seen_at"):
            items.append(f"last seen：{local_time_label(session.get('last_seen_at'))}")
        if session.get("heartbeat_age_seconds") is not None:
            items.append(f"last worker heartbeat：{session.get('heartbeat_age_seconds')}s ago")
        if session.get("last_output_at"):
            items.append(f"last output：{local_time_label(session.get('last_output_at'))}")
        if session.get("monitor_kind") or session.get("monitor_state"):
            items.append(
                "monitor owner："
                + display_text(session.get("monitor_kind"), fallback="未提供")
                + " / "
                + display_text(session.get("monitor_state"), fallback="未提供")
            )
        if session.get("stale_reason"):
            items.append(f"why waiting：{display_text(session.get('stale_reason'), fallback='未提供')}")
        if session.get("will_start_llm") is not None:
            items.append(f"will start LLM：{'yes' if session.get('will_start_llm') else 'no'}")
        if session.get("freshness_state"):
            items.append(f"freshness：{display_text(session.get('freshness_state'), fallback='未提供')}")
    return items


def _recovery_intent_continuity_items(intent: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    if intent:
        items.append(f"recovery action：{display_text(intent.get('current_action'), fallback='未提供')}")
        if intent.get("next_owner"):
            items.append(f"next owner：{intent.get('next_owner')}")
        if intent.get("next_eligible_tick"):
            items.append(f"next eligible tick：{local_time_label(intent.get('next_eligible_tick'))}")
    return items


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
:root { color-scheme: light; --ink:#172026; --muted:#5d6972; --line:#d8dee4; --line-strong:#c9d2dc; --accent:#0f766e; --accent-ink:#0f4f49; --warn:#8a5a00; --bad:#b91c1c; --ok:#047857; --info:#2563eb; --bg:#f4f7fa; --panel:#ffffff; --soft:#eef8f6; --panel-alt:#fbfcfd; --code:#111827; --shadow:0 10px 30px rgba(20, 32, 51, .08); }
* { box-sizing: border-box; }
body { margin: 0; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); font-size: 15px; line-height: 1.5; }
.portal { max-width: 1280px; margin: 0 auto; padding: 24px; }
.masthead { border: 1px solid var(--line); border-radius: 8px; background: var(--panel); padding: 22px; box-shadow: 0 1px 2px rgba(20, 32, 51, .04); }
.brand { color: var(--accent); font-weight: 750; letter-spacing: 0; }
h1 { margin: 8px 0 4px; font-size: 32px; line-height: 1.15; letter-spacing: 0; }
h2 { margin: 0 0 10px; font-size: 17px; letter-spacing: 0; }
h3 { margin: 0; font-size: 16px; line-height: 1.3; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.5; }
.state { color: var(--muted); font-size: 18px; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 18px 0 0; }
.meta div { border: 1px solid var(--line); background: var(--panel-alt); padding: 10px 12px; border-radius: 8px; min-width: 0; }
dt { color: var(--muted); font-size: 12px; }
dd { margin: 3px 0 0; font-weight: 600; overflow-wrap: anywhere; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 18px 0 14px; }
.panel, .refs { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; box-shadow: 0 1px 2px rgba(20, 32, 51, .03); }
.wide { margin-top: 14px; }
.muted { color: var(--muted); }
.workspace-dashboard { margin-top: 18px; }
.attention-band { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(300px, .9fr); gap: 16px; align-items: stretch; margin-bottom: 18px; }
.attention-summary { background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--accent); border-radius: 8px; padding: 18px 20px; box-shadow: var(--shadow); }
.attention-summary p { font-size: 15px; color: var(--ink); }
.eyebrow { display: block; color: var(--muted); font-size: 12px; font-weight: 750; text-transform: uppercase; margin-bottom: 4px; }
.attention-detail { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.attention-detail span { color: var(--muted); background: var(--panel-alt); border: 1px solid var(--line); border-radius: 999px; padding: 3px 9px; font-size: 12px; font-weight: 650; }
.attention-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.metric-tile { min-height: 78px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 13px 14px; display: flex; flex-direction: column; justify-content: space-between; }
.metric-label { color: var(--muted); font-size: 12px; font-weight: 700; }
.metric-tile strong { font-size: 22px; line-height: 1; overflow-wrap: anywhere; }
.metric-tile--ok { border-color: #b7e4c7; background: #f2fbf5; }
.metric-tile--warn { border-color: #f0d18a; background: #fffaf0; }
.metric-tile--bad { border-color: #f0b9b9; background: #fff5f5; }
.metric-tile--info { border-color: #bfdbfe; background: #f2f7ff; }
.attention-alert { grid-column: 1 / -1; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; }
.attention-alert--active { border-color: #f0d18a; background: #fffbeb; }
.command-code { display: block; background: #111827; color: #f9fafb; border-color: #111827; border-radius: 6px; padding: 10px 12px; overflow-wrap: anywhere; }
.study-card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 14px; }
.study-card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; min-height: 250px; box-shadow: 0 1px 2px rgba(20, 32, 51, .03); }
.study-card--selected { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(15, 118, 110, .12); }
.study-card--attention { border-left: 4px solid var(--warn); }
.study-card__header { display: flex; gap: 12px; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.study-card__header a { color: var(--accent); text-decoration: none; overflow-wrap: anywhere; }
.study-card__header a:hover { text-decoration: underline; }
.study-card__meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 0 0 14px; }
.study-card__meta div { background: var(--panel-alt); border: 1px solid var(--line); border-radius: 8px; padding: 9px 10px; min-width: 0; }
.study-card__action { border-left: 3px solid var(--accent); background: var(--soft); border-radius: 0 8px 8px 0; padding: 12px 14px; margin-top: auto; }
.study-card__action span { display: block; color: var(--accent-ink); font-size: 12px; font-weight: 750; margin-bottom: 4px; }
.study-card__action p { margin: 0; font-weight: 650; }
.study-card__footer { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
.study-card__console a { color: var(--accent); border: 1px solid var(--accent); border-radius: 6px; padding: 5px 9px; text-decoration: none; font-weight: 750; }
.study-card__console a:hover { background: var(--soft); }
.run-id { color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; font-size: 12px; overflow-wrap: anywhere; }
.field-details summary { cursor: pointer; font-weight: 750; }
.field-details-body { margin-top: 12px; }
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
.live-console-link .capability-badge { color: var(--accent); border: 1px solid var(--accent); border-radius: 999px; padding: 2px 8px; font-size: 12px; font-weight: 750; background: #e9f5f3; }
code { background: #eef2f6; border: 1px solid var(--line); border-radius: 5px; padding: 1px 5px; color: var(--code); }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; overflow-wrap: anywhere; }
summary { cursor: pointer; font-weight: 700; }
.refs { margin-top: 14px; }
@media (max-width: 760px) {
  .portal { padding: 18px; }
  .grid { grid-template-columns: 1fr; }
  .attention-band { grid-template-columns: 1fr; }
  .attention-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .study-card-grid { grid-template-columns: 1fr; }
  .study-card__meta { grid-template-columns: 1fr; }
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
