from __future__ import annotations

from collections.abc import Mapping
from html import escape
from typing import Any


LIVE_CONSOLE_HTML_REF = "ops/mas/live-console/index.html"
LIVE_CONSOLE_SESSION_READ_MODEL_REF = "artifacts/runtime/live_console/session_read_model/latest.json"
LIVE_CONSOLE_SERVE_COMMAND = "medautosci runtime live-console --profile <profile> --serve"


def live_console_projection(*, disabled_reason: str | None = None) -> dict[str, object]:
    reason = disabled_reason.strip() if isinstance(disabled_reason, str) and disabled_reason.strip() else None
    return {
        "available": reason is None,
        "label": "Live Console",
        "html_ref": LIVE_CONSOLE_HTML_REF,
        "session_read_model_ref": LIVE_CONSOLE_SESSION_READ_MODEL_REF,
        "serve_command": LIVE_CONSOLE_SERVE_COMMAND,
        "authority": "read_only_runtime_observation",
        "disabled_reason": reason,
    }


def render_live_console_portal_link(live_console: Mapping[str, Any]) -> str:
    if not live_console:
        return ""
    label = _non_empty_text(live_console.get("label")) or "Live Console"
    serve_command = _non_empty_text(live_console.get("serve_command")) or LIVE_CONSOLE_SERVE_COMMAND
    if bool(live_console.get("available")):
        return (
            '<div class="live-console-link">'
            '<a href="../live-console/index.html">Live Console</a>'
            f"<span>{escape(serve_command)}</span>"
            "</div>"
        )
    reason = _non_empty_text(live_console.get("disabled_reason")) or "Live Console is not available."
    return (
        '<div class="live-console-link disabled">'
        f"<strong>{escape(label)} unavailable</strong>"
        f"<span>{escape(reason)}</span>"
        "</div>"
    )


def render_live_console_static_shell() -> str:
    model_ref = LIVE_CONSOLE_SESSION_READ_MODEL_REF
    model_fetch_ref = "../../../" + model_ref
    serve_command = escape(LIVE_CONSOLE_SERVE_COMMAND)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MAS Live Console</title>
<style>
:root {{ color-scheme: light; --ink:#172026; --muted:#5b6770; --line:#d9e0e6; --panel:#ffffff; --bg:#f5f7f9; --accent:#0f766e; --soft:#e9f5f3; --warn:#8a5a00; --code:#101820; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
.shell {{ min-height: 100vh; display: grid; grid-template-rows: auto 1fr; }}
header {{ display: grid; grid-template-columns: 1fr auto; gap: 16px; align-items: end; padding: 22px 28px; border-bottom: 1px solid var(--line); background: var(--panel); }}
.brand {{ color: var(--accent); font-weight: 700; letter-spacing: 0; }}
h1 {{ margin: 5px 0 6px; font-size: 30px; line-height: 1.15; letter-spacing: 0; }}
.subtle {{ color: var(--muted); margin: 0; line-height: 1.45; }}
.badge {{ display: inline-flex; align-items: center; min-height: 28px; padding: 3px 9px; border: 1px solid var(--accent); border-radius: 999px; color: var(--accent); font-weight: 700; background: var(--soft); }}
.top-actions {{ display: flex; flex-wrap: wrap; gap: 10px; justify-content: flex-end; align-items: center; }}
a {{ color: var(--accent); font-weight: 700; text-decoration: none; }}
main {{ display: grid; grid-template-columns: minmax(240px, 300px) minmax(0, 1fr) minmax(280px, 380px); gap: 14px; padding: 16px; }}
section {{ background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px; min-width: 0; }}
h2 {{ margin: 0 0 10px; font-size: 16px; letter-spacing: 0; }}
.stack {{ display: grid; gap: 12px; align-content: start; }}
.item {{ border: 1px solid var(--line); border-radius: 8px; padding: 10px; background: #fbfcfd; }}
.item strong, dt {{ display: block; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0; }}
.item span, dd {{ display: block; margin: 4px 0 0; overflow-wrap: anywhere; font-weight: 650; }}
.timeline {{ display: grid; gap: 9px; }}
.event {{ display: grid; grid-template-columns: 118px 1fr; gap: 10px; border-left: 3px solid var(--accent); padding: 8px 10px; background: #fbfcfd; }}
.event time {{ color: var(--muted); font-size: 12px; overflow-wrap: anywhere; }}
.stream {{ min-height: 360px; background: var(--code); color: #d6f7ee; border-radius: 8px; padding: 12px; font: 12px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; overflow: auto; white-space: pre-wrap; }}
dl {{ margin: 0; display: grid; gap: 8px; }}
dd {{ margin-left: 0; }}
code {{ background: #eef2f6; border: 1px solid var(--line); border-radius: 5px; padding: 1px 5px; overflow-wrap: anywhere; }}
.intent {{ border-left: 3px solid var(--warn); padding-left: 10px; }}
ul {{ margin: 0; padding-left: 20px; }}
li {{ margin: 6px 0; overflow-wrap: anywhere; }}
@media (max-width: 980px) {{ main {{ grid-template-columns: 1fr; }} header {{ grid-template-columns: 1fr; }} .top-actions {{ justify-content: flex-start; }} }}
</style>
</head>
<body>
<div class="shell">
<header>
  <div>
    <div class="brand">Med Auto Science</div>
    <h1>MAS Live Console</h1>
    <p class="subtle">MAS-authored read-only view for workspace, study, run, terminal, log, and artifact observation.</p>
  </div>
  <div class="top-actions">
    <span class="badge">Read-only</span>
    <a href="../progress/index.html">Progress Portal</a>
  </div>
</header>
<main>
  <section class="stack" aria-labelledby="workspace-study-run-heading">
    <h2 id="workspace-study-run-heading">Workspace / Study / Run</h2>
    <div class="item"><strong>progress portal</strong><span>ops/mas/progress/index.html</span></div>
    <div class="item"><strong>read model</strong><span>{escape(model_ref)}</span></div>
    <div class="item"><strong>serve command</strong><span><code>{serve_command}</code></span></div>
    <div id="run-list" class="stack"></div>
  </section>
  <section class="stack" aria-labelledby="timeline-heading">
    <h2 id="timeline-heading">Timeline</h2>
    <div id="timeline" class="timeline"></div>
    <h2>Artifact Refs</h2>
    <ul id="artifact-refs"></ul>
  </section>
  <section class="stack" aria-labelledby="stream-heading">
    <h2 id="stream-heading">Terminal / Log Stream</h2>
    <div id="stream" class="stream">Waiting for {escape(model_ref)}.
Start the read-only local service with:
{serve_command}</div>
    <div class="intent">
      <h2>Controller Action Intent</h2>
      <p class="subtle">This shell shows intent only. Runtime changes still require MAS controller-owned commands.</p>
      <dl>
        <div><dt>inspect progress</dt><dd><code>medautosci workspace progress-portal --profile &lt;profile&gt;</code></dd></div>
        <div><dt>open runtime console</dt><dd><code>{serve_command}</code></dd></div>
        <div><dt>request reconcile</dt><dd><code>controller-required runtime reconcile intent</code></dd></div>
      </dl>
    </div>
  </section>
</main>
</div>
<script>
const MODEL_REF = "{model_fetch_ref}";
const MODEL_LABEL = "{model_ref}";
const text = (value, fallback = "unknown") => {{
  if (value === null || value === undefined || value === "") return fallback;
  return String(value);
}};
const list = (value) => Array.isArray(value) ? value : [];
const runItems = (payload) => {{
  if (Array.isArray(payload?.runs)) return payload.runs;
  if (Array.isArray(payload?.studies)) return payload.studies;
  return [];
}};
const clearChildren = (node) => {{
  while (node.firstChild) node.removeChild(node.firstChild);
}};
const appendText = (parent, tagName, value, className = "") => {{
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text(value);
  parent.appendChild(element);
  return element;
}};
const renderList = (id, values, emptyText) => {{
  const node = document.getElementById(id);
  const items = values.filter(Boolean);
  clearChildren(node);
  const visibleItems = items.length ? items : [emptyText];
  visibleItems.forEach((item) => {{
    appendText(node, "li", typeof item === "string" ? item : item.source_ref || item.ref || JSON.stringify(item));
  }});
}};
const appendRunItem = (parent, item, payload) => {{
  const wrapper = document.createElement("div");
  wrapper.className = "item";
  appendText(wrapper, "strong", item.study_id || payload.study_id || "workspace");
  appendText(wrapper, "span", `run: ${{text(item.active_run_id || item.run_id || payload.active_run_id, "none")}}`);
  appendText(wrapper, "span", `worker: ${{text(item.worker_running ?? payload.worker_running)}}`);
  appendText(wrapper, "span", `health: ${{text(item.runtime_health_status || payload.runtime_health_status || item.status)}}`);
  appendText(wrapper, "span", `supervisor: ${{text(item.supervisor_tick_status || payload.supervisor_tick_status)}}`);
  parent.appendChild(wrapper);
}};
const appendEventItem = (parent, event, payload) => {{
  const wrapper = document.createElement("div");
  wrapper.className = "event";
  appendText(wrapper, "time", event.observed_at || event.timestamp || event.local_time || payload.last_event_at);
  appendText(wrapper, "div", event.summary || event.message || event.topic || event.source_ref);
  parent.appendChild(wrapper);
}};
const render = (payload) => {{
  const runs = runItems(payload);
  const runList = document.getElementById("run-list");
  clearChildren(runList);
  if (runs.length) {{
    runs.forEach((item) => appendRunItem(runList, item, payload));
  }} else {{
    const wrapper = document.createElement("div");
    wrapper.className = "item";
    appendText(wrapper, "strong", "status");
    appendText(wrapper, "span", "No live console session read model has been generated yet.");
    runList.appendChild(wrapper);
  }}
  const events = list(payload?.timeline || payload?.latest_events || payload?.events);
  const timeline = document.getElementById("timeline");
  clearChildren(timeline);
  if (events.length) {{
    events.forEach((event) => appendEventItem(timeline, event, payload));
  }} else {{
    appendEventItem(timeline, {{ summary: "No timeline events loaded." }}, payload);
  }}
  renderList("artifact-refs", list(payload?.source_refs), "No artifact refs loaded.");
  const terminalSources = list(payload?.stream_sources).filter((item) => item.topic === "terminal.tail");
  const logSources = list(payload?.stream_sources).filter((item) => item.topic === "log.tail");
  const streamLines = [
    `read_model: ${{MODEL_LABEL}}`,
    `workspace: ${{text(payload?.workspace?.workspace_root || payload?.workspace_root)}}`,
    `selected_study_id: ${{text(payload?.selected_study_id, "none")}}`,
    "",
    "terminal sources:",
    ...(terminalSources.length ? terminalSources.map((item) => `  - ${{text(item.source_ref || item.ref || item)}}`) : ["  - none"]),
    "",
    "log sources:",
    ...(logSources.length ? logSources.map((item) => `  - ${{text(item.source_ref || item.ref || item)}}`) : ["  - none"]),
  ];
  document.getElementById("stream").textContent = streamLines.join("\\n");
}};
fetch(MODEL_REF, {{ cache: "no-store" }})
  .then((response) => response.ok ? response.json() : Promise.reject(new Error(`${{response.status}} ${{response.statusText}}`)))
  .then(render)
  .catch(() => render({{}}));
</script>
</body>
</html>
"""


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "LIVE_CONSOLE_HTML_REF",
    "LIVE_CONSOLE_SERVE_COMMAND",
    "LIVE_CONSOLE_SESSION_READ_MODEL_REF",
    "live_console_projection",
    "render_live_console_portal_link",
    "render_live_console_static_shell",
]
