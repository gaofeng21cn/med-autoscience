from __future__ import annotations


def live_console_css() -> str:
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
  --bad: #b91c1c;
  --ok: #047857;
  --code: #101827;
  --panel-alt: #fbfcfd;
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
  box-shadow: 0 1px 2px rgba(20, 32, 51, .04);
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
button {
  border: 1px solid var(--accent);
  border-radius: 6px;
  background: var(--accent);
  color: #fff;
  min-height: 34px;
  padding: 5px 10px;
  font-weight: 750;
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
}
dd {
  margin: 2px 0 0;
  overflow-wrap: anywhere;
}
.panel {
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 1px 2px rgba(20, 32, 51, .03);
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
  overflow-wrap: anywhere;
}
th {
  color: var(--muted);
  font-size: 12px;
}
td code {
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}
tbody tr:hover td { background: #f7fafc; }
.status-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid var(--line);
  font-size: 12px;
  font-weight: 650;
  line-height: 1.35;
  white-space: nowrap;
}
.status-ok { color: var(--ok); background: #edf9f1; border-color: #b7e4c7; }
.status-warn { color: var(--warn); background: #fff7e6; border-color: #f0d18a; }
.status-bad { color: var(--bad); background: #fff1f1; border-color: #f0b9b9; }
.status-neutral { color: var(--muted); background: #f3f6f9; border-color: var(--line); }
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
  background: #f8fafc;
  border: 1px solid var(--line);
  color: var(--ink);
  font: 13px/1.45 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  white-space: pre-wrap;
}
.terminal-actions, .terminal-resize {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin: 10px 0;
}
.terminal-input-label {
  display: block;
  color: var(--muted);
  font-weight: 700;
  margin-bottom: 6px;
}
textarea, input[type="number"] {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 7px 9px;
  font: inherit;
}
textarea {
  width: 100%;
  resize: vertical;
}
input[type="number"] {
  width: 90px;
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
  .table-wrap {
    overflow-x: visible;
  }
  table.responsive-table,
  table.responsive-table thead,
  table.responsive-table tbody,
  table.responsive-table tr,
  table.responsive-table th,
  table.responsive-table td {
    display: block;
    width: 100%;
  }
  table.responsive-table thead {
    display: none;
  }
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


__all__ = ["live_console_css"]
