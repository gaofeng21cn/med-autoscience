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
    handoff = _mapping(runtime_continuity.get("domain_authority_handoff"))
    items = _domain_authority_handoff_items(handoff)
    return list_section("OPL 控制面交接", items, empty_text="当前没有 MAS domain authority handoff 投影。")


def _domain_authority_handoff_items(handoff: Mapping[str, Any]) -> list[str]:
    items: list[str] = []
    if handoff:
        owner_route = _mapping(handoff.get("owner_route"))
        typed_blocker = _mapping(handoff.get("typed_blocker"))
        items.append(f"handoff status：{display_text(handoff.get('status'), empty_text='未提供')}")
        if owner_route.get("next_owner"):
            items.append(f"next owner：{owner_route.get('next_owner')}")
        if owner_route.get("idempotency_key"):
            items.append(f"route idempotency key：{owner_route.get('idempotency_key')}")
        if typed_blocker.get("reason"):
            items.append(f"typed blocker：{typed_blocker.get('reason')}")
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
:root { color-scheme: light; --ink:#16211c; --muted:#62706a; --faint:#87928d; --line:#dbe4de; --line-strong:#c5d2cb; --accent:#0b6b5c; --accent-ink:#06463d; --accent-soft:#e6f4ef; --warn:#8a5a00; --warn-soft:#fff3cf; --bad:#b42318; --bad-soft:#ffe7e4; --ok:#087443; --ok-soft:#e8f6ed; --info:#285ea8; --info-soft:#e8f0fb; --bg:#f6f9f6; --bg-band:#edf5ef; --panel:#ffffff; --panel-alt:#f9fbf7; --code:#151b23; --shadow:0 18px 42px rgba(30, 54, 44, .10); --shadow-soft:0 1px 2px rgba(30, 54, 44, .06); --focus:0 0 0 3px rgba(11, 107, 92, .22); }
* { box-sizing: border-box; }
body { margin: 0; font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; color: var(--ink); background: var(--bg); font-size: 15px; line-height: 1.56; }
body::before { content: ""; position: fixed; inset: 0; z-index: -1; pointer-events: none; background: linear-gradient(180deg, var(--bg-band) 0, var(--bg) 290px, #f8faf7 100%); }
a { color: var(--accent); text-underline-offset: 3px; }
a:hover { color: var(--accent-ink); }
a:focus-visible, button:focus-visible, summary:focus-visible, .btn:focus-visible { outline: none; box-shadow: var(--focus); border-radius: 8px; }
.portal { max-width: 1280px; margin: 0 auto; padding: 28px; }
.masthead, .page-header { position: relative; border: 1px solid var(--line); border-radius: 8px; background: rgba(255, 255, 255, .96); padding: 24px; box-shadow: var(--shadow); overflow: hidden; }
.masthead::before, .page-header::before { content: ""; position: absolute; inset: 0 0 auto; height: 5px; background: linear-gradient(90deg, var(--accent), #d98032 48%, var(--ok)); }
.brand { color: var(--accent-ink); font-size: 13px; font-weight: 800; letter-spacing: 0; }
h1 { margin: 8px 0 4px; font-size: 34px; line-height: 1.12; letter-spacing: 0; }
h2 { margin: 0 0 12px; font-size: 17px; line-height: 1.28; letter-spacing: 0; }
h3 { margin: 0; font-size: 16px; line-height: 1.35; letter-spacing: 0; }
p { margin: 0 0 10px; line-height: 1.56; }
.state { color: var(--muted); font-size: 18px; max-width: 78ch; }
.header-actions { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 16px; }
.snapshot-meta { margin-top: 18px; }
.snapshot-meta summary { display: inline-flex; min-height: 32px; align-items: center; cursor: pointer; color: var(--muted); font-size: 13px; font-weight: 800; }
.meta { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 10px; margin: 16px 0 0; }
.meta div { border: 1px solid var(--line); background: var(--panel-alt); padding: 10px 12px; border-radius: 8px; min-width: 0; box-shadow: var(--shadow-soft); }
dt { color: var(--muted); font-size: 12px; font-weight: 700; }
dd { margin: 3px 0 0; font-weight: 650; overflow-wrap: anywhere; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; margin: 18px 0 14px; }
.panel, .refs { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; box-shadow: var(--shadow-soft); }
.panel:hover, .refs:hover { border-color: var(--line-strong); }
.wide { margin-top: 14px; }
.muted { color: var(--muted); }
.workspace-dashboard { margin-top: 18px; }
.attention-band { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(300px, .9fr); gap: 16px; align-items: stretch; margin-bottom: 20px; }
.attention-summary { background: var(--panel); border: 1px solid var(--line); border-left: 5px solid var(--accent); border-radius: 8px; padding: 18px 20px; box-shadow: var(--shadow); }
.attention-summary p { font-size: 15px; color: var(--ink); }
.eyebrow { display: block; color: var(--muted); font-size: 12px; font-weight: 800; text-transform: uppercase; margin-bottom: 4px; }
.attention-detail { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.attention-detail span { color: var(--muted); background: var(--panel-alt); border: 1px solid var(--line); border-radius: 999px; padding: 4px 10px; font-size: 12px; font-weight: 700; }
.attention-metrics { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.metric-tile { min-height: 86px; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; box-shadow: var(--shadow-soft); }
.metric-label { color: var(--muted); font-size: 12px; font-weight: 800; }
.metric-tile strong { font-size: 24px; line-height: 1; overflow-wrap: anywhere; font-variant-numeric: tabular-nums; }
.metric-tile--ok { border-color: #a9d9b7; background: var(--ok-soft); }
.metric-tile--warn { border-color: #e6c267; background: var(--warn-soft); }
.metric-tile--bad { border-color: #f0ada8; background: var(--bad-soft); }
.metric-tile--info { border-color: #b9cceb; background: var(--info-soft); }
.attention-alert { grid-column: 1 / -1; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; box-shadow: var(--shadow-soft); }
.attention-alert--active { border-color: #e0ba58; background: var(--warn-soft); }
.command-code { display: block; background: var(--code); color: #f7faf9; border: 1px solid var(--code); border-radius: 8px; padding: 10px 12px; overflow-wrap: anywhere; font-size: 13px; line-height: 1.55; }
.study-card-grid, .study-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(330px, 1fr)); gap: 14px; }
.study-card, .study-item { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; min-height: 250px; box-shadow: var(--shadow-soft); }
.study-card--selected, .study-item--selected { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(11, 107, 92, .15), var(--shadow-soft); }
.study-card--attention, .study-item--attention { border-left: 5px solid var(--warn); }
.study-card__header { display: flex; gap: 12px; justify-content: space-between; align-items: flex-start; margin-bottom: 14px; }
.study-card__header a { color: var(--accent-ink); text-decoration: none; overflow-wrap: anywhere; }
.study-card__header a:hover { text-decoration: underline; }
.study-card__meta, .study-meta { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin: 0 0 14px; }
.study-card__meta div, .study-meta div { background: var(--panel-alt); border: 1px solid var(--line); border-radius: 8px; padding: 9px 10px; min-width: 0; }
.study-info { min-width: 0; }
.study-status { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.study-card__action, .study-action { border-left: 4px solid var(--accent); background: var(--accent-soft); border-radius: 0 8px 8px 0; padding: 12px 14px; margin-top: auto; }
.study-card__action span, .study-action-label { display: block; color: var(--accent-ink); font-size: 12px; font-weight: 800; margin-bottom: 4px; }
.study-card__action p, .study-action-desc { margin: 0; font-weight: 650; color: var(--ink); }
.study-card__footer, .study-actions { display: flex; flex-wrap: wrap; gap: 10px; justify-content: space-between; align-items: center; margin-top: 14px; padding-top: 12px; border-top: 1px solid var(--line); }
.study-card__console a { color: var(--accent-ink); border: 1px solid var(--accent); border-radius: 8px; padding: 6px 10px; text-decoration: none; font-weight: 800; min-height: 32px; display: inline-flex; align-items: center; }
.study-card__console a:hover { background: var(--accent-soft); }
.run-id { color: var(--muted); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; font-size: 12px; overflow-wrap: anywhere; }
.field-details summary { cursor: pointer; font-weight: 800; min-height: 34px; display: flex; align-items: center; }
.field-details-body { margin-top: 12px; }
.diagnostics-stack { display: grid; gap: 12px; margin-top: 12px; }
.diagnostics-section { background: var(--panel); border: 1px solid var(--line); border-left: 4px solid var(--info); border-radius: 8px; padding: 14px; box-shadow: var(--shadow-soft); }
.diagnostics-section[open] { border-left-color: var(--warn); background: #fffdf6; }
.diagnostics-section summary { cursor: pointer; font-weight: 800; color: var(--ink); }
.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 8px; text-align: left; vertical-align: top; overflow-wrap: anywhere; }
th { color: var(--muted); font-size: 12px; font-weight: 800; background: #f8faf7; }
tbody tr:hover td { background: #f7fbf8; }
.study-row.selected td { background: var(--accent-soft); }
.status-chip { display: inline-flex; align-items: center; min-height: 24px; padding: 2px 8px; border-radius: 999px; border: 1px solid var(--line); font-size: 12px; font-weight: 650; line-height: 1.35; white-space: nowrap; }
.status-ok { color: var(--ok); background: var(--ok-soft); border-color: #a9d9b7; }
.status-warn { color: var(--warn); background: var(--warn-soft); border-color: #e6c267; }
.status-bad { color: var(--bad); background: var(--bad-soft); border-color: #f0ada8; }
.status-neutral { color: var(--muted); background: #f4f7f5; border-color: var(--line); }
.route-map-panel { overflow: hidden; }
.route-map-shell { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: linear-gradient(180deg, #fbfdfb, var(--panel-alt)); padding: 10px; }
.route-map-svg { display: block; min-width: 720px; width: 100%; height: auto; }
.route-edge { fill: none; stroke: var(--line-strong); stroke-width: 2.5; marker-end: url(#route-arrow); }
.route-edge--blocked { stroke: var(--warn); stroke-dasharray: 7 5; }
.route-edge--artifact-generated, .route-edge--artifact_generated, .route-edge--evidence_to_artifact { stroke: var(--info); }
.route-edge--alternative, .route-edge--reroute { stroke: var(--warn); stroke-dasharray: 3 5; }
#route-arrow path { fill: var(--line-strong); }
.route-node rect { fill: var(--panel); stroke: var(--line-strong); stroke-width: 1.5; filter: drop-shadow(0 2px 3px rgba(30, 54, 44, .08)); }
.route-node text { fill: var(--ink); font-size: 12px; font-weight: 800; pointer-events: none; }
.route-node .route-node-meta { fill: var(--muted); font-size: 11px; font-weight: 700; }
.route-node-link:focus .route-node rect, .route-node-link:hover .route-node rect { stroke: var(--accent); stroke-width: 2.5; }
.route-node-status--active rect, .route-node-status--winning rect { fill: var(--accent-soft); stroke: var(--accent); stroke-width: 2; }
.route-node-status--blocked rect { fill: var(--warn-soft); stroke: var(--warn); stroke-width: 2; }
.route-node--blocker rect { fill: var(--bad-soft); stroke: var(--bad); }
.route-node--artifact rect { fill: var(--info-soft); stroke: var(--info); }
.route-map-legend { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-top: 12px; color: var(--muted); font-size: 13px; }
.route-map-legend span { font-weight: 800; color: var(--ink); }
.route-map-legend ul { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; padding: 0; margin: 0; }
.route-map-legend li { margin: 0; border: 1px solid var(--line); border-radius: 999px; padding: 3px 9px; background: var(--panel-alt); font-weight: 700; }
.route-map-details { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; padding: 0; margin: 14px 0 0; list-style: none; }
.route-map-details li { margin: 0; border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; background: var(--panel-alt); scroll-margin-top: 18px; }
.route-map-details li:target { border-color: var(--accent); box-shadow: var(--focus); background: var(--panel); }
.route-map-details strong, .route-map-details span { display: block; }
.route-map-details span { color: var(--muted); font-size: 12px; font-weight: 800; margin-top: 2px; }
.route-map-details p { margin: 6px 0 0; font-size: 13px; }
.route-node-refs { display: grid; gap: 4px; margin-top: 8px; color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }
.route-node-refs a { color: var(--accent-ink); font-weight: 800; }
.conversation-timeline { position: relative; list-style: none; margin: 12px 0 14px; padding: 0; display: grid; gap: 10px; }
.conversation-timeline::before { content: ""; position: absolute; left: 11px; top: 12px; bottom: 12px; width: 2px; background: var(--line); }
.conversation-item { position: relative; display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 10px; margin: 0; }
.conversation-item__marker { width: 24px; height: 24px; border-radius: 999px; border: 2px solid var(--accent); background: var(--panel); z-index: 1; margin-top: 2px; }
.conversation-item--user_message .conversation-item__marker { background: var(--accent); border-color: var(--accent); }
.conversation-item--turn_receipt .conversation-item__marker, .conversation-item--latest_turn_receipt_ref .conversation-item__marker { background: var(--ok-soft); border-color: var(--ok); }
.conversation-item--runtime_lifecycle_event .conversation-item__marker { background: var(--panel-alt); border-color: var(--line-strong); }
.conversation-item__body { border: 1px solid var(--line); border-radius: 8px; background: var(--panel-alt); padding: 10px 12px; min-width: 0; }
.conversation-item__body strong { display: inline-block; margin-right: 8px; }
.conversation-item__body span { color: var(--muted); font-size: 12px; font-weight: 700; overflow-wrap: anywhere; }
.conversation-item__body p { margin: 5px 0 0; font-size: 13px; overflow-wrap: anywhere; }
.portal-nav-links { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin-top: 16px; }
.portal-nav-links a, .portal-nav-links strong { color: var(--accent-ink); font-weight: 800; }
.portal-nav-links span { color: var(--muted); overflow-wrap: anywhere; }
.btn, a.btn, button.btn { min-height: 38px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid var(--accent); border-radius: 8px; padding: 8px 12px; background: var(--accent); color: #fff; font: inherit; font-size: 14px; font-weight: 800; text-decoration: none; cursor: pointer; box-shadow: var(--shadow-soft); }
.btn:hover, a.btn:hover, button.btn:hover { background: var(--accent-ink); color: #fff; }
.btn-outline, a.btn-outline, button.btn-outline { background: var(--panel); color: var(--accent-ink); border-color: var(--line-strong); }
.btn-outline:hover, a.btn-outline:hover, button.btn-outline:hover { background: var(--accent-soft); color: var(--accent-ink); border-color: var(--accent); }
code { background: #edf2ef; border: 1px solid var(--line); border-radius: 6px; padding: 1px 5px; color: var(--code); }
ul { margin: 0; padding-left: 20px; }
li { margin: 6px 0; overflow-wrap: anywhere; }
summary { cursor: pointer; font-weight: 800; }
.refs { margin-top: 14px; }
@media (max-width: 760px) {
  .portal { padding: 18px; }
  .grid { grid-template-columns: 1fr; }
  .attention-band { grid-template-columns: 1fr; }
  .attention-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .study-card-grid, .study-list { grid-template-columns: 1fr; }
  .study-card__meta, .study-meta { grid-template-columns: 1fr; }
  .study-card, .study-item { min-height: 0; }
  .study-card__header { flex-direction: column; align-items: flex-start; }
  .header-actions, .study-actions, .study-card__footer { align-items: stretch; }
  .btn, a.btn, button.btn { width: 100%; }
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
