from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from html import escape
from typing import Any

from med_autoscience.controllers.progress_portal_parts import local_time_projection


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_live_console_ui"
BRAND = "Med Auto Science"
LIVE_CONSOLE_HTML_REF = "ops/mas/live-console/index.html"
LIVE_CONSOLE_PAYLOAD_REF = "artifacts/runtime/live_console/ui_payload/latest.json"


def build_live_console_ui_payload(
    *,
    live_console_snapshot: Mapping[str, Any],
    generated_at: str | None = None,
    progress_portal_href: str = "../progress/index.html",
    stream_href: str | None = None,
) -> dict[str, Any]:
    workspace = _mapping(live_console_snapshot.get("workspace"))
    studies = _studies(live_console_snapshot.get("studies"))
    source_refs = _source_refs(studies)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "brand": BRAND,
        "generated_at": generated_at or _utc_now(),
        "generated_at_local": local_time_projection(generated_at or _utc_now(), timezone_name=None),
        "payload_ref": LIVE_CONSOLE_PAYLOAD_REF,
        "html_ref": LIVE_CONSOLE_HTML_REF,
        "authority": {
            "kind": "read_only_live_observation_shell",
            "read_only": True,
            "writes_authority_surface": False,
            "state_interpretation_owner": "runtime_session_read_model",
            "authority_note": (
                "Live Console renders MAS live observation payloads and does not own runtime, "
                "publication, controller, package, or study truth."
            ),
        },
        "portal_handoff": {
            "progress_portal_href": progress_portal_href,
            "relationship": "navigation_return_link",
            "portal_owns_live_console_state_interpretation": False,
        },
        "stream": {
            "href": stream_href,
            "mode": "read_only_observation",
            "writes_authority_surface": False,
        },
        "workspace": {
            "profile_name": _text(workspace.get("profile_name")) or "unknown",
            "workspace_root": _text(workspace.get("workspace_root")) or "",
            "workspace_status": _text(workspace.get("workspace_status")) or "unknown",
        },
        "studies": studies,
        "source_refs": source_refs,
    }


def render_live_console_html(payload: Mapping[str, Any]) -> str:
    workspace = _mapping(payload.get("workspace"))
    studies = [dict(item) for item in payload.get("studies") or [] if isinstance(item, Mapping)]
    portal_handoff = _mapping(payload.get("portal_handoff"))
    stream = _mapping(payload.get("stream"))
    generated_at = str(payload.get("generated_at") or "unknown")
    generated_at_local = _mapping(payload.get("generated_at_local"))
    generated_at_local_label = str(generated_at_local.get("label") or generated_at)
    brand = str(payload.get("brand") or BRAND)
    progress_href = str(portal_handoff.get("progress_portal_href") or "../progress/index.html")
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{escape(brand)} Live Console</title>",
            "<style>",
            _css(),
            "</style>",
            "</head>",
            "<body>",
            '<main class="console">',
            '<header class="masthead">',
            '<div class="topline">',
            f'<span class="brand">{escape(brand)}</span>',
            '<span class="badge">READ ONLY</span>',
            f'<a class="portal-link" href="{escape(progress_href, quote=True)}">返回 Progress Portal</a>',
            "</div>",
            f"<h1>{escape(str(workspace.get('profile_name') or 'unknown workspace'))}</h1>",
            '<dl class="meta">',
            f"<div><dt>workspace root</dt><dd>{escape(str(workspace.get('workspace_root') or ''))}</dd></div>",
            f"<div><dt>workspace status</dt><dd>{escape(str(workspace.get('workspace_status') or 'unknown'))}</dd></div>",
            f"<div><dt>generated_at local</dt><dd>{escape(generated_at_local_label)}</dd></div>",
            f"<div><dt>generated_at UTC</dt><dd>{escape(generated_at)}</dd></div>",
            f"<div><dt>stream</dt><dd>{escape(str(stream.get('href') or 'static snapshot'))}</dd></div>",
            "</dl>",
            "</header>",
            _study_run_section(studies),
            '<section class="layout">',
            _timeline_section(studies),
            _stream_section("Terminal stream", studies, key="terminal_sources"),
            _stream_section("Log stream", studies, key="log_sources"),
            "</section>",
            _refs_section("Artifact refs", studies, key="artifact_refs"),
            _refs_section("Event refs", studies, key="event_refs"),
            "</main>",
            "</body>",
            "</html>",
        ]
    )


def _studies(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    studies: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        study_id = _text(item.get("study_id"))
        if study_id is None:
            continue
        studies.append(
            {
                "study_id": study_id,
                "state_label": _text(item.get("state_label")),
                "current_stage": _text(item.get("current_stage")),
                "active_run_id": _text(item.get("active_run_id")),
                "runtime_health_status": _text(item.get("runtime_health_status")),
                "supervisor_tick_status": _text(item.get("supervisor_tick_status")),
                "worker_running": item.get("worker_running") if isinstance(item.get("worker_running"), bool) else None,
                "runs": _runs(item.get("runs")),
                "timeline": _timeline(item.get("timeline")),
                "terminal_sources": _stream_sources(item.get("terminal_sources")),
                "log_sources": _stream_sources(item.get("log_sources")),
                "artifact_refs": _string_list(item.get("artifact_refs")),
                "event_refs": _string_list(item.get("event_refs")),
            }
        )
    return studies


def _runs(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    runs: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        run_id = _text(item.get("run_id"))
        if run_id is None:
            continue
        runs.append(
            {
                "run_id": run_id,
                "status": _text(item.get("status")),
                "started_at": _text(item.get("started_at")),
                "last_seen_at": _text(item.get("last_seen_at")),
            }
        )
    return runs


def _timeline(value: object) -> list[dict[str, str | None]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    events: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        summary = _text(item.get("summary"))
        if summary is None:
            continue
        events.append(
            {
                "observed_at": _text(item.get("observed_at")),
                "topic": _text(item.get("topic")),
                "summary": summary,
                "source_ref": _text(item.get("source_ref")),
            }
        )
    return events


def _stream_sources(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    sources: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        source_ref = _text(item.get("source_ref"))
        tail = _string_list(item.get("tail"))
        if source_ref is None and not tail:
            continue
        sources.append(
            {
                "label": _text(item.get("label")) or "source",
                "source_ref": source_ref,
                "tail": tail,
            }
        )
    return sources


def _source_refs(studies: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for study in studies:
        for event in study.get("timeline") or []:
            if isinstance(event, Mapping):
                refs.append(str(event.get("source_ref") or ""))
        for key in ("terminal_sources", "log_sources"):
            for source in study.get(key) or []:
                if isinstance(source, Mapping):
                    refs.append(str(source.get("source_ref") or ""))
        refs.extend(_string_list(study.get("artifact_refs")))
        refs.extend(_string_list(study.get("event_refs")))
    return _dedupe(refs)


def _study_run_section(studies: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for study in studies:
        runs = [dict(item) for item in study.get("runs") or [] if isinstance(item, Mapping)]
        if not runs:
            rows.append(_study_run_row(study, {}))
            continue
        for run in runs:
            rows.append(_study_run_row(study, run))
    return (
        '<section class="panel wide">'
        "<h2>workspace/study/run</h2>"
        '<div class="table-wrap"><table>'
        "<thead><tr><th>study_id</th><th>run_id</th><th>state</th><th>stage</th>"
        "<th>runtime</th><th>supervisor</th><th>worker</th><th>last_seen_at</th></tr></thead>"
        "<tbody>"
        + "".join(rows)
        + "</tbody></table></div></section>"
    )


def _study_run_row(study: Mapping[str, Any], run: Mapping[str, Any]) -> str:
    worker = _worker_label(study.get("worker_running"))
    return (
        "<tr>"
        f"<td>{escape(str(study.get('study_id') or 'unknown-study'))}</td>"
        f"<td>{escape(str(run.get('run_id') or study.get('active_run_id') or 'none'))}</td>"
        f"<td>{escape(str(study.get('state_label') or run.get('status') or 'unknown'))}</td>"
        f"<td>{escape(str(study.get('current_stage') or 'unknown'))}</td>"
        f"<td>{escape(str(study.get('runtime_health_status') or 'unknown'))}</td>"
        f"<td>{escape(str(study.get('supervisor_tick_status') or 'unknown'))}</td>"
        f"<td>{escape(worker)}</td>"
        f"<td>{escape(str(run.get('last_seen_at') or 'unknown'))}</td>"
        "</tr>"
    )


def _timeline_section(studies: list[dict[str, Any]]) -> str:
    items: list[str] = []
    for study in studies:
        study_id = str(study.get("study_id") or "unknown-study")
        for event in study.get("timeline") or []:
            if not isinstance(event, Mapping):
                continue
            prefix = " | ".join(
                _dedupe(
                    [
                        study_id,
                        str(event.get("observed_at") or ""),
                        str(event.get("topic") or ""),
                    ]
                )
            )
            label = f"{prefix}: {event.get('summary')}" if prefix else str(event.get("summary") or "")
            items.append(label)
    return _list_panel("状态 timeline", items, empty_text="No status events supplied.")


def _stream_section(title: str, studies: list[dict[str, Any]], *, key: str) -> str:
    blocks: list[str] = []
    for study in studies:
        study_id = str(study.get("study_id") or "unknown-study")
        for source in study.get(key) or []:
            if not isinstance(source, Mapping):
                continue
            tail = "\n".join(_string_list(source.get("tail")))
            label = str(source.get("label") or "source")
            source_ref = str(source.get("source_ref") or "")
            blocks.append(
                '<article class="stream-block">'
                f"<h3>{escape(study_id)} / {escape(label)}</h3>"
                f'<p class="source-ref">{escape(source_ref)}</p>'
                f"<pre>{escape(tail)}</pre>"
                "</article>"
            )
    if not blocks:
        blocks.append('<p class="empty">No stream tail supplied.</p>')
    return f'<section class="panel stream"><h2>{escape(title)}</h2>{"".join(blocks)}</section>'


def _refs_section(title: str, studies: list[dict[str, Any]], *, key: str) -> str:
    refs: list[str] = []
    for study in studies:
        refs.extend(_string_list(study.get(key)))
    return _list_panel(title, _dedupe(refs), empty_text="No refs supplied.")


def _list_panel(title: str, items: list[str], *, empty_text: str) -> str:
    if not items:
        body = f'<p class="empty">{escape(empty_text)}</p>'
    else:
        body = "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"
    return f'<section class="panel"><h2>{escape(title)}</h2>{body}</section>'


def _worker_label(value: object) -> str:
    if value is True:
        return "running"
    if value is False:
        return "not running"
    return "unknown"


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            result.append(text)
    return result


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = " ".join(str(value).strip().split())
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _css() -> str:
    return """
:root {
  color-scheme: light;
  --bg: #f6f8fb;
  --ink: #142033;
  --muted: #56657a;
  --line: #d9e1ec;
  --panel: #ffffff;
  --accent: #0f766e;
  --warn: #8a4b00;
  --code: #101827;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  font-size: 15px;
  line-height: 1.5;
}
.console {
  width: min(1280px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 24px 0 40px;
}
.masthead, .panel {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.masthead {
  padding: 22px;
  margin-bottom: 16px;
}
.topline {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
}
.brand {
  color: var(--muted);
  font-weight: 700;
  letter-spacing: 0;
}
.badge {
  color: var(--warn);
  border: 1px solid rgba(138, 75, 0, .35);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 800;
}
.portal-link {
  color: var(--accent);
  font-weight: 700;
  text-decoration: none;
}
h1 {
  margin: 14px 0 12px;
  font-size: 30px;
  line-height: 1.2;
  letter-spacing: 0;
}
h2 {
  margin: 0 0 12px;
  font-size: 18px;
  line-height: 1.3;
  letter-spacing: 0;
}
h3 {
  margin: 0 0 6px;
  font-size: 14px;
  letter-spacing: 0;
}
.meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin: 0;
}
.meta div {
  min-width: 0;
}
dt {
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
}
dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
}
.panel {
  padding: 16px;
  margin-bottom: 16px;
}
.wide {
  grid-column: 1 / -1;
}
.layout {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.stream {
  min-width: 0;
}
.table-wrap {
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border-bottom: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}
th {
  color: var(--muted);
  font-size: 12px;
  text-transform: uppercase;
}
ul {
  margin: 0;
  padding-left: 20px;
}
li {
  margin: 4px 0;
  overflow-wrap: anywhere;
}
.stream-block {
  border-top: 1px solid var(--line);
  padding-top: 12px;
  margin-top: 12px;
}
.stream-block:first-of-type {
  border-top: 0;
  padding-top: 0;
  margin-top: 0;
}
.source-ref {
  color: var(--muted);
  margin: 0 0 8px;
  overflow-wrap: anywhere;
}
pre {
  margin: 0;
  min-height: 88px;
  overflow: auto;
  border-radius: 6px;
  padding: 12px;
  background: var(--code);
  color: #e6eef8;
  font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  white-space: pre-wrap;
}
.empty {
  color: var(--muted);
  margin: 0;
}
@media (max-width: 820px) {
  .console {
    width: min(100vw - 20px, 1280px);
    padding-top: 10px;
  }
  .layout {
    grid-template-columns: 1fr;
  }
  h1 {
    font-size: 24px;
  }
}
""".strip()


__all__ = [
    "LIVE_CONSOLE_HTML_REF",
    "LIVE_CONSOLE_PAYLOAD_REF",
    "build_live_console_ui_payload",
    "render_live_console_html",
]
