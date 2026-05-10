from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


PROGRESS_PORTAL_PAYLOAD_REF = "artifacts/runtime/progress_portal/latest.json"
PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE = "artifacts/runtime/progress_portal/studies/{study_id}/latest.json"


def build_runtime_workbench_projection(
    *,
    workspace_root: Path,
    profile_ref: str | Path | None,
    profile_name: str,
    generated_at: str,
    study_id: str,
    workspace_overview_mode: bool,
    page_scope: str,
    workspace_study_rows: list[dict[str, Any]],
    user_visible: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    freshness: Mapping[str, Any],
    source_refs: list[str],
    conditions: Mapping[str, Any],
    study_workbench: Mapping[str, Any],
    live_console: Mapping[str, Any],
) -> dict[str, Any]:
    studies = [
        _workbench_study_row(
            row,
            fallback_freshness=freshness,
            fallback_source_refs=source_refs,
            selected_study_id=study_id,
        )
        for row in workspace_study_rows
        if _non_empty_text(row.get("study_id")) is not None
    ]
    if not workspace_overview_mode and not any(item["study_id"] == study_id for item in studies):
        studies.append(
            _selected_workbench_study(
                study_id=study_id,
                user_visible=user_visible,
                progress=progress,
                runtime=runtime,
                freshness=freshness,
                source_refs=source_refs,
                study_workbench=study_workbench,
            )
        )
    return {
        "surface_kind": "mas_opl_runtime_workbench_projection",
        "schema_version": 1,
        "generated_at": generated_at,
        "workspace": {
            "workspace_root": str(workspace_root),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
            "profile_name": profile_name,
        },
        "studies": studies,
        "terminal": _workbench_terminal_projection(
            study_id=study_id,
            active_run_id=(
                _non_empty_text(_mapping(study_workbench.get("runtime")).get("active_run_id"))
                or _non_empty_text(_mapping(progress.get("supervision")).get("active_run_id"))
                or _non_empty_text(runtime.get("active_run_id"))
            ),
            live_console=live_console,
        ),
        "authority": {
            "opl_role": "projection_consumer_and_action_transport_only",
            "mas_truth_owner": True,
            "page_scope": page_scope,
            "forbidden_writes": [
                "study_truth",
                "publication_judgment",
                "quality_verdict",
                "runtime_authority",
                "artifact_authority",
                "runtime_state",
                "runtime_sqlite",
                "terminal_commands",
                "current_package",
                "evidence_ledger",
                "review_ledger",
            ],
        },
        "conditions": {
            "missing": _string_list(conditions.get("missing")),
            "stale": _string_list(conditions.get("stale")),
            "conflict": _string_list(conditions.get("conflict")),
        },
    }


def _workbench_study_row(
    row: Mapping[str, Any],
    *,
    fallback_freshness: Mapping[str, Any],
    fallback_source_refs: list[str],
    selected_study_id: str,
) -> dict[str, Any]:
    study_id = _non_empty_text(row.get("study_id")) or "unknown-study"
    freshness = {
        "status": _non_empty_text(row.get("progress_freshness_status")) or _non_empty_text(fallback_freshness.get("status")),
        "summary": _non_empty_text(row.get("progress_freshness_summary")) or _non_empty_text(fallback_freshness.get("summary")),
        "latest_event_at": _non_empty_text(row.get("latest_event_at")) or _non_empty_text(fallback_freshness.get("latest_event_at")),
    }
    active_run_id = _non_empty_text(row.get("active_run_id"))
    worker_state = _first_non_empty_text(
        row.get("worker_state"),
        row.get("runtime_health_status"),
        row.get("supervisor_tick_status"),
    )
    return {
        "study_id": study_id,
        "display_title": _non_empty_text(row.get("display_title")) or _non_empty_text(row.get("title")) or study_id,
        "macro_state": _first_non_empty_text(
            row.get("macro_state"),
            row.get("state_label"),
            row.get("current_stage"),
            row.get("paper_stage"),
        ) or "unknown",
        "user_next": _first_non_empty_text(row.get("user_next"), row.get("next_system_action"), row.get("operator_focus")),
        "current_stage": _non_empty_text(row.get("current_stage")),
        "active_run_id": active_run_id,
        "worker_state": worker_state,
        "last_seen_at": _first_non_empty_text(row.get("last_seen_at"), freshness["latest_event_at"]),
        "freshness": freshness,
        "blocker_summary": _first_non_empty_text(row.get("blocker_summary"), row.get("progress_freshness_summary")),
        "next_action_summary": _first_non_empty_text(row.get("next_action_summary"), row.get("next_system_action"), row.get("operator_focus")),
        "source_refs": fallback_source_refs[:12],
        "links": _workbench_links(study_id, selected=study_id == selected_study_id),
        "actions": _workbench_actions(),
    }


def _selected_workbench_study(
    *,
    study_id: str,
    user_visible: Mapping[str, Any],
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any],
    freshness: Mapping[str, Any],
    source_refs: list[str],
    study_workbench: Mapping[str, Any],
) -> dict[str, Any]:
    runtime_projection = _mapping(study_workbench.get("runtime"))
    continuity = _mapping(progress.get("runtime_continuity"))
    runtime_session = _mapping(continuity.get("runtime_session"))
    active_run_id = (
        _non_empty_text(runtime_projection.get("active_run_id"))
        or _non_empty_text(_mapping(progress.get("supervision")).get("active_run_id"))
        or _non_empty_text(runtime.get("active_run_id"))
    )
    return {
        "study_id": study_id,
        "display_title": study_id,
        "macro_state": _first_non_empty_text(user_visible.get("state_label"), user_visible.get("writer_state")) or "unknown",
        "user_next": _non_empty_text(user_visible.get("user_next")) or _non_empty_text(user_visible.get("next_system_action")),
        "current_stage": _non_empty_text(user_visible.get("current_stage")),
        "active_run_id": active_run_id,
        "worker_state": _first_non_empty_text(
            runtime_session.get("worker_state"),
            runtime_projection.get("health_status"),
            runtime.get("health_status"),
        ),
        "last_seen_at": _first_non_empty_text(runtime_session.get("last_seen_at"), freshness.get("latest_event_at")),
        "freshness": dict(freshness),
        "blocker_summary": "; ".join(_string_list(user_visible.get("current_blockers"))) or None,
        "next_action_summary": _non_empty_text(user_visible.get("next_system_action")),
        "source_refs": source_refs[:12],
        "links": _workbench_links(study_id, selected=True),
        "actions": _workbench_actions(),
        "workbench": dict(study_workbench),
    }


def _workbench_links(study_id: str, *, selected: bool) -> dict[str, Any]:
    return {
        "progress_payload_ref": (
            PROGRESS_PORTAL_PAYLOAD_REF
            if selected
            else PROGRESS_PORTAL_STUDY_PAYLOAD_REF_TEMPLATE.format(study_id=study_id)
        ),
        "conversation_read_model_ref": "artifacts/runtime/conversation_read_model/latest.json",
        "live_console_read_model_ref": "artifacts/runtime/live_console/session_read_model/latest.json",
        "terminal_attach_status_ref": "artifacts/runtime/terminal_attach/read_model/latest.json",
        "artifact_refs": [],
    }


def _workbench_actions() -> dict[str, dict[str, Any]]:
    return {
        action: {
            "allowed": False,
            "owner": "mas_runtime_owner",
            "endpoint_ref": None,
            "idempotency_required": True,
            "confirmation_required": action in {"stop", "reconcile_apply"},
        }
        for action in ("pause", "resume", "stop", "reconcile_dry_run", "reconcile_apply")
    }


def _workbench_terminal_projection(
    *,
    study_id: str,
    active_run_id: str | None,
    live_console: Mapping[str, Any],
) -> dict[str, Any]:
    available = bool(active_run_id and live_console.get("available"))
    return {
        "mode": "read_only_tail" if available else "unavailable",
        "reason": None if available else "no_attach_capable_live_run",
        "study_id": study_id,
        "active_run_id": active_run_id,
        "endpoints": None,
        "token_required": True,
        "lease_required": True,
        "audit_ref": "artifacts/runtime/terminal_attach/receipts.jsonl",
    }


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _first_non_empty_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result
