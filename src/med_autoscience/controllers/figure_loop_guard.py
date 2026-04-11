from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.figure_routes import (
    FIGURE_ROUTE_ILLUSTRATION_PROGRAM,
    FIGURE_ROUTE_SCRIPT_FIX,
    normalize_figure_token,
    normalize_required_routes,
    partition_required_routes,
    supported_required_route_help,
)
from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.runtime_protocol import quest_state, user_message
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store
from med_autoscience.runtime_protocol.layout import resolve_runtime_root_from_quest_root


managed_runtime_backend = runtime_backend_contract.get_managed_runtime_backend(
    runtime_backend_contract.DEFAULT_MANAGED_RUNTIME_BACKEND_ID
)
med_deepscientist_transport = managed_runtime_backend


RESOLVED_PATTERNS = [
    r"已收住",
    r"收住了",
    r"已解决",
    r"resolved",
    r"closed",
    r"不再继续",
    r"不再回头",
]

@dataclass
class GuardState:
    quest_root: Path
    quest_id: str
    runtime_state: dict[str, Any]
    outbox_path: Path
    recent_outbox_rows: list[dict[str, Any]]
    figure_counts: dict[str, int]
    dominant_figure_id: str | None
    dominant_figure_mentions: int
    reopen_detected: bool
    reference_count: int
    accepted_figures: dict[str, str]
    figure_tickets: dict[str, str]
    required_routes: list[str]
    min_figure_mentions: int
    min_reference_count: int
    recent_window: int


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_timestamp(value: object) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def parse_key_value_pairs(values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in values:
        item = str(raw).strip()
        if not item:
            continue
        if "=" in item:
            key, note = item.split("=", 1)
        else:
            key, note = item, ""
        parsed[key.strip().upper()] = note.strip()
    return parsed


def resolve_outbox_path(quest_root: Path) -> Path:
    runtime_root = resolve_runtime_root_from_quest_root(quest_root)
    return runtime_root / "logs" / "connectors" / "local" / "outbox.jsonl"


def _normalize_optional_path(value: object) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    return str(Path(raw).expanduser().resolve())

def extract_figures(message: str) -> list[str]:
    found: set[str] = set()
    for raw_id, panel in re.findall(r"(?i)\bfigure\s+(s?\d+)\s*([A-Z])?\b", message):
        token = normalize_figure_token(raw_id, panel)
        if token:
            found.add(token)
    for raw_id, panel in re.findall(r"(?i)\bF(S?\d+)([A-Z])?\b", message):
        token = normalize_figure_token(raw_id, panel)
        if token:
            found.add(token)
    return sorted(found)


def resolve_active_run_window_start(quest_root: Path, runtime_state: dict[str, Any]) -> datetime | None:
    active_run_id = str(runtime_state.get("active_run_id") or "").strip()
    if not active_run_id:
        return None
    stdout_path = quest_state.resolve_active_stdout_path(
        quest_root=quest_root,
        runtime_state=runtime_state,
    )
    if stdout_path is not None and stdout_path.exists():
        for raw in stdout_path.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            timestamp = parse_timestamp(payload.get("timestamp"))
            if timestamp is not None:
                return timestamp
    return parse_timestamp(runtime_state.get("last_resume_at"))


def read_recent_outbox_rows(
    outbox_path: Path,
    quest_root: Path,
    limit: int,
    *,
    not_before: datetime | None = None,
) -> list[dict[str, Any]]:
    if not outbox_path.exists():
        return []
    resolved_quest_root = str(Path(quest_root).expanduser().resolve())
    rows: list[dict[str, Any]] = []
    for raw in outbox_path.read_text(encoding="utf-8").splitlines():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if str(payload.get("quest_id") or "").strip() != quest_root.name:
            continue
        payload_quest_root = _normalize_optional_path(payload.get("quest_root"))
        if payload_quest_root is not None and payload_quest_root != resolved_quest_root:
            continue
        if not_before is not None:
            sent_at = parse_timestamp(payload.get("sent_at") or payload.get("created_at"))
            if sent_at is None or sent_at < not_before:
                continue
        rows.append(payload)
    return rows[-max(limit, 0):]


def count_figures(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        for token in extract_figures(str(row.get("message") or "")):
            counts[token] = counts.get(token, 0) + 1
    return counts


def choose_dominant_figure(rows: list[dict[str, Any]], counts: dict[str, int]) -> tuple[str | None, int]:
    if not counts:
        return None, 0
    best_key = ""
    best_count = -1
    last_seen_index = -1
    for key, count in counts.items():
        current_last_seen = -1
        for index, row in enumerate(rows):
            if key in extract_figures(str(row.get("message") or "")):
                current_last_seen = index
        if count > best_count or (count == best_count and current_last_seen > last_seen_index):
            best_key = key
            best_count = count
            last_seen_index = current_last_seen
    return best_key or None, max(best_count, 0)


def detect_reopen(rows: list[dict[str, Any]], figure_id: str | None) -> bool:
    if not figure_id:
        return False
    resolved_seen = False
    for row in rows:
        message = str(row.get("message") or "")
        if figure_id not in extract_figures(message):
            continue
        if any(re.search(pattern, message, flags=re.IGNORECASE) for pattern in RESOLVED_PATTERNS):
            resolved_seen = True
            continue
        if resolved_seen:
            return True
    return False


def resolve_references_path(quest_root: Path) -> Path | None:
    candidates = list(quest_root.glob(".ds/worktrees/*/paper/references.bib"))
    candidates.extend(list(quest_root.glob("paper/references.bib")))
    return quest_state.find_latest(candidates)


def count_references(quest_root: Path) -> int:
    references_path = resolve_references_path(quest_root)
    if references_path is None or not references_path.exists():
        return 0
    return sum(1 for line in references_path.read_text(encoding="utf-8").splitlines() if line.lstrip().startswith("@"))


def build_guard_state(
    quest_root: Path,
    *,
    outbox_path: Path | None = None,
    accepted_figures: dict[str, str] | None = None,
    figure_tickets: dict[str, str] | None = None,
    required_routes: list[str] | None = None,
    min_figure_mentions: int = 12,
    min_reference_count: int = 12,
    recent_window: int = 120,
) -> GuardState:
    runtime_state = quest_state.load_runtime_state(quest_root)
    resolved_outbox_path = outbox_path or resolve_outbox_path(quest_root)
    active_run_window_start = resolve_active_run_window_start(quest_root, runtime_state)
    active_run_id = str(runtime_state.get("active_run_id") or "").strip()
    rows = (
        read_recent_outbox_rows(
            resolved_outbox_path,
            quest_root,
            recent_window,
            not_before=active_run_window_start,
        )
        if active_run_id and active_run_window_start is not None
        else []
    )
    counts = count_figures(rows)
    dominant_figure_id, dominant_figure_mentions = choose_dominant_figure(rows, counts)
    return GuardState(
        quest_root=quest_root,
        quest_id=quest_root.name,
        runtime_state=runtime_state,
        outbox_path=resolved_outbox_path,
        recent_outbox_rows=rows,
        figure_counts=counts,
        dominant_figure_id=dominant_figure_id,
        dominant_figure_mentions=dominant_figure_mentions,
        reopen_detected=detect_reopen(rows, dominant_figure_id),
        reference_count=count_references(quest_root),
        accepted_figures=dict(accepted_figures or {}),
        figure_tickets=dict(figure_tickets or {}),
        required_routes=normalize_required_routes(list(required_routes or [])),
        min_figure_mentions=min_figure_mentions,
        min_reference_count=min_reference_count,
        recent_window=recent_window,
    )


def build_guard_report(state: GuardState) -> dict[str, Any]:
    loop_detected = bool(state.dominant_figure_id and state.dominant_figure_mentions >= state.min_figure_mentions)
    blockers: list[str] = []
    if loop_detected:
        blockers.append("figure_loop_budget_exceeded")
    if state.reopen_detected:
        blockers.append("figure_reopened_after_resolution")
    if state.reopen_detected and state.dominant_figure_id in state.accepted_figures:
        blockers.append("accepted_figure_reopened")
    if loop_detected and state.reference_count < state.min_reference_count:
        blockers.append("references_below_floor_during_figure_loop")

    recommended_action = "stop_current_run_and_route_mainline" if blockers else "continue_current_run"
    status = "blocked" if blockers else "clear"
    return {
        "schema_version": 1,
        "guard_kind": "figure_loop_guard",
        "generated_at": utc_now(),
        "quest_id": state.quest_id,
        "status": status,
        "recommended_action": recommended_action,
        "blockers": blockers,
        "recent_window": state.recent_window,
        "outbox_path": str(state.outbox_path),
        "dominant_figure_id": state.dominant_figure_id,
        "dominant_figure_mentions": state.dominant_figure_mentions,
        "figure_counts": state.figure_counts,
        "reopen_detected": state.reopen_detected,
        "reference_count": state.reference_count,
        "reference_floor": state.min_reference_count,
        "accepted_figures": state.accepted_figures,
        "figure_tickets": state.figure_tickets,
        "required_routes": state.required_routes,
        "active_run_id": state.runtime_state.get("active_run_id"),
        "active_interaction_id": state.runtime_state.get("active_interaction_id"),
        "runtime_status": state.runtime_state.get("status"),
        "controller_note": (
            "This controller is an outer orchestration guard. It does not edit prompts or runtime internals; "
            "it stops runaway figure polishing, records durable decisions, and routes the quest back to the main line."
        ),
    }


def render_guard_markdown(report: dict[str, Any]) -> str:
    blockers = report.get("blockers") or []
    lines = [
        "# Figure Loop Guard Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- quest_id: `{report['quest_id']}`",
        f"- status: `{report['status']}`",
        f"- recommended_action: `{report['recommended_action']}`",
        f"- dominant_figure_id: `{report.get('dominant_figure_id') or 'none'}`",
        f"- dominant_figure_mentions: `{report.get('dominant_figure_mentions')}`",
        f"- reopen_detected: `{str(bool(report.get('reopen_detected'))).lower()}`",
        f"- reference_count: `{report.get('reference_count')}`",
        f"- reference_floor: `{report.get('reference_floor')}`",
        "",
        "## Blockers" if blockers else "## Status",
        "",
    ]
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- No controller-level blocker detected.")
    lines.extend(["", "## Accepted Figures", ""])
    accepted_figures = report.get("accepted_figures") or {}
    if accepted_figures:
        lines.extend(f"- `{figure_id}`: {note or 'accepted'}" for figure_id, note in accepted_figures.items())
    else:
        lines.append("- None")
    lines.extend(["", "## Figure Tickets", ""])
    figure_tickets = report.get("figure_tickets") or {}
    if figure_tickets:
        lines.extend(f"- `{figure_id}`: {note}" for figure_id, note in figure_tickets.items())
    else:
        lines.append("- None")
    lines.extend(["", "## Required Routes", ""])
    required_routes = report.get("required_routes") or []
    if required_routes:
        lines.extend(f"- `{item}`" for item in required_routes)
    else:
        lines.append("- None")
    lines.extend(["", "## Controller Scope", "", f"- {report.get('controller_note')}", ""])
    return "\n".join(lines)


def build_intervention_message(report: dict[str, Any]) -> str:
    dominant = report.get("dominant_figure_id") or "unknown"
    blockers = ", ".join(report.get("blockers") or []) or "none"
    accepted = "; ".join(
        f"{figure_id}={note or 'accepted'}" for figure_id, note in (report.get("accepted_figures") or {}).items()
    ) or "none"
    tickets = "; ".join(f"{figure_id}={note}" for figure_id, note in (report.get("figure_tickets") or {}).items()) or "none"
    required_routes = list(report.get("required_routes") or [])
    mainline_routes, script_fix_routes, program_routes = partition_required_routes(required_routes)
    routes = ", ".join(required_routes) or "none"
    message = (
        "Hard control message from MedAutoScience orchestration layer: stop the current figure-polish loop now. "
        f"The dominant runaway figure is `{dominant}` with `{report.get('dominant_figure_mentions')}` recent mentions. "
        f"Controller blockers: {blockers}. "
        f"Current reference count is `{report.get('reference_count')}` below the floor `{report.get('reference_floor')}`. "
        f"Accepted figures that must not be reopened in this run: {accepted}. "
        "For accepted figures, record the final state and defer any residual visual concern to the final human paper check. "
        f"Open figure tickets that may only be handled as bounded sidecar items: {tickets}. "
        f"Required next routes: {routes}. "
    )
    if mainline_routes:
        message += (
            "Mainline research routes to execute next: "
            + ", ".join(mainline_routes)
            + ". "
        )
    if script_fix_routes:
        message += (
            "For the script/data repair route, only use bounded regeneration from the frozen data/script path for "
            + ", ".join(f"`{figure_id}` via `{FIGURE_ROUTE_SCRIPT_FIX}:{figure_id}`" for figure_id in script_fix_routes)
            + ". This route is for evidence-bearing result figures and must not call any sidecar or illustration-only tooling. "
        )
    if program_routes:
        message += (
            "For the programmatic illustration route, only use bounded non-evidence figure generation for "
            + ", ".join(
                f"`{figure_id}` via `{FIGURE_ROUTE_ILLUSTRATION_PROGRAM}:{figure_id}`" for figure_id in program_routes
            )
            + ". This route is for manuscript-safe explanatory figures generated directly by MedAutoScience-controlled code and must not be used for evidence-bearing result plots. "
        )
    message += (
        "Do not keep `figure-polish` on the main line. If any figure ticket cannot be closed in one bounded corrective run, "
        "register it as a blocker and return to literature expansion plus manuscript body revision."
    )
    return message


def write_guard_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="figure_loop_guard",
        timestamp=report["generated_at"],
        report=report,
        markdown=render_guard_markdown(report),
    )


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    outbox_path: Path | None = None,
    daemon_url: str | None = None,
    accepted_figures: dict[str, str] | None = None,
    figure_tickets: dict[str, str] | None = None,
    required_routes: list[str] | None = None,
    min_figure_mentions: int = 12,
    min_reference_count: int = 12,
    recent_window: int = 120,
    source: str = "medautosci-figure-loop-guard",
) -> dict[str, Any]:
    state = build_guard_state(
        quest_root,
        outbox_path=outbox_path,
        accepted_figures=accepted_figures,
        figure_tickets=figure_tickets,
        required_routes=required_routes,
        min_figure_mentions=min_figure_mentions,
        min_reference_count=min_reference_count,
        recent_window=recent_window,
    )
    report = build_guard_report(state)
    json_path, md_path = write_guard_files(quest_root, report)

    stop_result = None
    intervention = None
    if apply and report["blockers"]:
        runtime_status = str(state.runtime_state.get("status") or "").strip().lower()
        if runtime_status in {"running", "active"}:
            stop_result = managed_runtime_backend.stop_quest(
                daemon_url=daemon_url,
                runtime_root=None if daemon_url else resolve_runtime_root_from_quest_root(state.quest_root),
                quest_id=state.quest_id,
                source=source,
            )
        intervention = user_message.enqueue_user_message(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=build_intervention_message(report),
            source=source,
        )

    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "blockers": report["blockers"],
        "dominant_figure_id": report["dominant_figure_id"],
        "dominant_figure_mentions": report["dominant_figure_mentions"],
        "reference_count": report["reference_count"],
        "intervention_enqueued": bool(intervention),
        "message_id": intervention.get("message_id") if intervention else None,
        "quest_stop_applied": bool(stop_result),
        "quest_stop_status": stop_result.get("status") if isinstance(stop_result, dict) else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--outbox-path", type=Path)
    parser.add_argument("--daemon-url")
    parser.add_argument("--accepted-figure", action="append", default=[])
    parser.add_argument("--figure-ticket", action="append", default=[])
    parser.add_argument("--required-route", action="append", default=[], help=supported_required_route_help())
    parser.add_argument("--min-figure-mentions", type=int, default=12)
    parser.add_argument("--min-reference-count", type=int, default=12)
    parser.add_argument("--recent-window", type=int, default=120)
    parser.add_argument("--source", default="medautosci-figure-loop-guard")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = run_controller(
        quest_root=args.quest_root,
        apply=args.apply,
        outbox_path=args.outbox_path,
        daemon_url=args.daemon_url,
        accepted_figures=parse_key_value_pairs(args.accepted_figure),
        figure_tickets=parse_key_value_pairs(args.figure_ticket),
        required_routes=list(args.required_route or []),
        min_figure_mentions=max(1, int(args.min_figure_mentions)),
        min_reference_count=max(0, int(args.min_reference_count)),
        recent_window=max(1, int(args.recent_window)),
        source=str(args.source),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
