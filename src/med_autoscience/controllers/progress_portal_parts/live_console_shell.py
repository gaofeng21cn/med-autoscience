from __future__ import annotations

from collections.abc import Mapping
from html import escape
from urllib.parse import quote
from typing import Any


LIVE_CONSOLE_HTML_REF = "ops/mas/live-console/index.html"
LIVE_CONSOLE_SESSION_READ_MODEL_REF = "artifacts/runtime/live_console/session_read_model/latest.json"
LIVE_CONSOLE_SERVE_COMMAND = "medautosci runtime live-console --profile <profile> --serve"


def live_console_projection(
    *,
    disabled_reason: str | None = None,
    study_id: str | None = None,
    page_scope: str = "workspace",
) -> dict[str, object]:
    reason = disabled_reason.strip() if isinstance(disabled_reason, str) and disabled_reason.strip() else None
    scoped_study_id = study_id.strip() if isinstance(study_id, str) and study_id.strip() else None
    href = "../live-console/index.html"
    if page_scope == "study" and scoped_study_id:
        href = f"../../../live-console/index.html?study_id={quote(scoped_study_id, safe='')}"
    elif scoped_study_id:
        href = f"../live-console/index.html?study_id={quote(scoped_study_id, safe='')}"
    return {
        "available": reason is None,
        "label": "运行控制台",
        "html_ref": LIVE_CONSOLE_HTML_REF,
        "href": href,
        "scope": "study" if scoped_study_id else "profile",
        "study_id": scoped_study_id,
        "capability_badge": "单篇运行控制台" if scoped_study_id else "工作区运行控制台",
        "session_read_model_ref": LIVE_CONSOLE_SESSION_READ_MODEL_REF,
        "serve_command": LIVE_CONSOLE_SERVE_COMMAND,
        "authority": "read_only_runtime_observation",
        "disabled_reason": reason,
    }


def render_live_console_portal_link(live_console: Mapping[str, Any]) -> str:
    if not live_console:
        return ""
    label = _non_empty_text(live_console.get("label")) or "运行控制台"
    href = _non_empty_text(live_console.get("href")) or "../live-console/index.html"
    scope = _non_empty_text(live_console.get("scope")) or "profile"
    badge = _non_empty_text(live_console.get("capability_badge")) or (
        "单篇运行控制台" if scope == "study" else "工作区运行控制台"
    )
    scope_label = "单篇" if scope == "study" else "工作区"
    if bool(live_console.get("available")):
        return (
            '<div class="live-console-link">'
            f'<a href="{escape(href, quote=True)}">运行控制台</a>'
            f'<span class="capability-badge">{escape(badge)}</span>'
            f"<span>范围：{escape(scope_label)}</span>"
            "</div>"
        )
    reason = _non_empty_text(live_console.get("disabled_reason")) or "运行控制台不可用。"
    return (
        '<div class="live-console-link disabled">'
        f"<strong>{escape(label)}不可用</strong>"
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
<title>MAS 运行控制台</title>
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
.terminal-actions {{ display: flex; flex-wrap: wrap; gap: 8px; }}
button {{ border: 1px solid var(--accent); border-radius: 6px; background: var(--accent); color: #fff; min-height: 32px; padding: 4px 10px; font-weight: 750; }}
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
    <h1>MAS 运行控制台</h1>
    <p class="subtle">只读查看 workspace、study、run、终端尾部、日志尾部和产物引用；运行变更必须回到 MAS controller。</p>
  </div>
  <div class="top-actions">
    <span class="badge">只读</span>
    <a href="../progress/index.html">返回进度入口</a>
  </div>
</header>
<main>
  <section class="stack" aria-labelledby="workspace-study-run-heading">
    <h2 id="workspace-study-run-heading">工作区 / 论文线 / 运行</h2>
    <div class="item"><strong>进度入口</strong><span>ops/mas/progress/index.html</span></div>
    <div class="item"><strong>读取模型</strong><span>{escape(model_ref)}</span></div>
    <div class="item"><strong>刷新命令</strong><span><code>{serve_command}</code></span></div>
    <div id="run-list" class="stack"></div>
  </section>
  <section class="stack" aria-labelledby="timeline-heading">
    <h2 id="timeline-heading">运行时间线</h2>
    <div id="timeline" class="timeline"></div>
    <h2>产物来源</h2>
    <ul id="artifact-refs"></ul>
  </section>
  <section class="stack" aria-labelledby="stream-heading">
    <h2 id="stream-heading">终端 / 日志来源</h2>
    <div id="stream" class="stream">等待读取 {escape(model_ref)}。
启动只读本地服务：
{serve_command}</div>
    <div class="intent">
      <h2>控制器动作意图</h2>
      <p class="subtle">这里只展示动作意图；暂停、恢复、重启或 reconcile 仍必须由 MAS controller-owned 命令执行。</p>
      <dl>
        <div><dt>查看进度</dt><dd><code>medautosci workspace progress-portal --profile &lt;profile&gt;</code></dd></div>
        <div><dt>刷新控制台</dt><dd><code>{serve_command}</code></dd></div>
        <div><dt>请求 reconcile</dt><dd><code>controller-required runtime reconcile intent</code></dd></div>
      </dl>
    </div>
    <section class="terminal-attach" aria-labelledby="terminal-attach-heading">
      <h2 id="terminal-attach-heading">Terminal Attach</h2>
      <p class="subtle">默认 fail closed；只有 MAS terminal attach owner 提供 token、lease、idempotency、audit 与 attach/input/resize/detach endpoints 时才可用。</p>
      <div class="terminal-actions">
        <button type="button">Attach</button>
        <button type="button">Input</button>
        <button type="button">Resize</button>
        <button type="button">Detach</button>
      </div>
    </section>
  </section>
</main>
</div>
<script>
const MODEL_REF = "{model_fetch_ref}";
const MODEL_LABEL = "{model_ref}";
const text = (value, emptyText = "unknown") => {{
  if (value === null || value === undefined || value === "") return emptyText;
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
    appendText(wrapper, "span", "尚未生成 live-console session read model。");
    runList.appendChild(wrapper);
  }}
  const events = list(payload?.timeline || payload?.latest_events || payload?.events);
  const timeline = document.getElementById("timeline");
  clearChildren(timeline);
  if (events.length) {{
    events.forEach((event) => appendEventItem(timeline, event, payload));
  }} else {{
    appendEventItem(timeline, {{ summary: "尚未加载运行时间线事件。" }}, payload);
  }}
  renderList("artifact-refs", list(payload?.source_refs), "尚未加载产物来源。");
  const terminalSources = list(payload?.stream_sources).filter((item) => item.topic === "terminal.tail");
  const logSources = list(payload?.stream_sources).filter((item) => item.topic === "log.tail");
  const streamLines = [
    `读取模型: ${{MODEL_LABEL}}`,
    `工作区: ${{text(payload?.workspace?.workspace_root || payload?.workspace_root)}}`,
    `当前论文线: ${{text(payload?.selected_study_id, "none")}}`,
    "",
    "终端来源:",
    ...(terminalSources.length ? terminalSources.map((item) => `  - ${{text(item.source_ref || item.ref || item)}}`) : ["  - none"]),
    "",
    "日志来源:",
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
