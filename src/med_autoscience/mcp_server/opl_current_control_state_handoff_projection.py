from __future__ import annotations

from typing import Any


def _compact_record(value: Any, keys: tuple[str, ...]) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact: dict[str, Any] = {}
    for key in keys:
        if key in value:
            compact[key] = value[key]
    return compact or None


def _compact_string_list(value: Any, *, limit: int = 12) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
        if len(items) >= limit:
            break
    return items


def _compact_terminal_stage_log(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface_kind",
            "read_model",
            "authority",
            "source_path",
            "generated_at",
            "study_id",
            "stage_attempt_id",
            "stage_id",
            "action_type",
            "status",
            "observability_status",
            "duration",
            "token_usage",
            "cost",
            "usage_refs",
            "cost_refs",
            "missing_observability_fields",
            "paper_stage_log",
            "stage_log_workbench_summary",
            "closeout_refs",
            "authority_boundary",
        ),
    )
    if compact is None:
        return None
    paper_stage_log = compact.get("paper_stage_log")
    if isinstance(paper_stage_log, dict):
        for key in (
            "stage_work_done",
            "paper_work_done",
            "changed_stage_surfaces",
            "changed_paper_surfaces",
            "remaining_blockers",
            "usage_refs",
            "cost_refs",
            "evidence_refs",
        ):
            if isinstance(paper_stage_log.get(key), list):
                paper_stage_log[key] = _compact_string_list(paper_stage_log.get(key), limit=6)
    for ref_key in ("usage_refs", "cost_refs"):
        if isinstance(compact.get(ref_key), list):
            compact[ref_key] = _compact_string_list(compact.get(ref_key), limit=6)
    if isinstance(compact.get("closeout_refs"), list):
        compact["closeout_refs"] = _compact_string_list(compact.get("closeout_refs"), limit=6)
    workbench_summary = compact.get("stage_log_workbench_summary")
    if isinstance(workbench_summary, dict):
        for ref_key in ("evidence_refs", "usage_refs", "cost_refs", "source_refs"):
            if isinstance(workbench_summary.get(ref_key), list):
                workbench_summary[ref_key] = _compact_string_list(workbench_summary.get(ref_key), limit=6)
    return compact


def compact_opl_current_control_state_handoff(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    compact = _compact_record(
        value,
        (
            "surface_kind",
            "read_model",
            "authority",
            "source_path",
            "generated_at",
            "study_id",
            "mode",
            "mode_label",
            "scheduler_owner",
            "codex_app_heartbeat_required",
            "safe_actions_enabled",
            "repo_level_repair_authority",
            "github_user_gate",
            "quest_status",
            "active_run_id",
            "runtime_health",
            "artifact_delta",
            "gate_specificity",
            "ai_reviewer_status",
            "stage_progress_log",
            "latest_terminal_stage_log",
            "queue_slo",
            "owner_pickup_overdue",
            "developer_supervisor_attention_required",
            "blocked_reason",
            "next_owner",
            "external_supervisor_required",
        ),
    )
    if compact is None:
        return None
    stage_progress_log = compact.get("stage_progress_log")
    if isinstance(stage_progress_log, dict):
        attempt_refs = stage_progress_log.get("attempt_refs")
        if isinstance(attempt_refs, list):
            stage_progress_log["attempt_refs"] = _compact_string_list(attempt_refs, limit=6)
        temporal_refs = stage_progress_log.get("temporal_webui_refs")
        if isinstance(temporal_refs, list):
            stage_progress_log["temporal_webui_refs"] = _compact_string_list(temporal_refs, limit=6)
    latest_terminal_stage_log = _compact_terminal_stage_log(compact.get("latest_terminal_stage_log"))
    if latest_terminal_stage_log is not None:
        compact["latest_terminal_stage_log"] = latest_terminal_stage_log
    else:
        compact.pop("latest_terminal_stage_log", None)
    action_queue = value.get("action_queue")
    if isinstance(action_queue, list):
        compact["action_queue"] = [
            {
                key: item[key]
                for key in (
                    "action_type",
                    "summary",
                    "status",
                    "owner",
                    "surface",
                    "source",
                    "action_id",
                    "fingerprint",
                    "queue_age_hours",
                    "queued_first_seen_at",
                    "repeat_fingerprint",
                    "owner_pickup",
                    "consumption",
                )
                if key in item
            }
            for item in action_queue
            if isinstance(item, dict)
        ][:6]
    why_not_applied = _compact_string_list(value.get("why_not_applied"), limit=8)
    if why_not_applied:
        compact["why_not_applied"] = why_not_applied
    return compact


def render_mcp_progress_opl_current_control_state_handoff(compact: dict[str, Any]) -> list[str]:
    dashboard = compact.get("opl_current_control_state_handoff")
    if not isinstance(dashboard, dict):
        return []
    runtime_health = dashboard.get("runtime_health") if isinstance(dashboard.get("runtime_health"), dict) else {}
    artifact_delta = dashboard.get("artifact_delta") if isinstance(dashboard.get("artifact_delta"), dict) else {}
    gate_specificity = dashboard.get("gate_specificity") if isinstance(dashboard.get("gate_specificity"), dict) else {}
    ai_reviewer = dashboard.get("ai_reviewer_status") if isinstance(dashboard.get("ai_reviewer_status"), dict) else {}
    lines = [
        "",
        "## OPL Current Control State Handoff",
        (
            f"- developer supervisor mode: `{dashboard.get('mode') or 'unknown'}`"
            f" ({dashboard.get('mode_label') or 'unlabeled'})；"
            f"scheduler_owner: `{dashboard.get('scheduler_owner') or 'unknown'}`；"
            f"Codex App heartbeat required: `{dashboard.get('codex_app_heartbeat_required')}`"
        ),
        (
            f"- developer supervisor authority: safe_actions_enabled "
            f"`{dashboard.get('safe_actions_enabled')}`；"
            f"repo_level_repair_authority `{dashboard.get('repo_level_repair_authority') or 'unknown'}`；"
            f"authority_gate `{dashboard.get('authority_gate') or dashboard.get('github_user_gate') or 'unknown'}`"
        ),
        (
            f"- quest: `{dashboard.get('quest_status') or 'unknown'}`；"
            f"run: `{dashboard.get('active_run_id') or 'none'}`；"
            f"health: `{runtime_health.get('health_status') or 'unknown'}`"
        ),
        (
            f"- artifact_delta: `{artifact_delta.get('status') or 'unknown'}`；"
            f"gate_specificity: `{gate_specificity.get('status') or 'unknown'}`；"
            f"ai_reviewer: `{ai_reviewer.get('status') or 'unknown'}`"
        ),
    ]
    blocked_reason = str(dashboard.get("blocked_reason") or gate_specificity.get("blocked_reason") or "").strip()
    if blocked_reason:
        lines.append(f"- blocked_reason: `{blocked_reason}`")
    stage_progress_log = dashboard.get("stage_progress_log")
    if isinstance(stage_progress_log, dict):
        lines.append(
            f"- stage_progress_log: attempts `{stage_progress_log.get('attempt_count') or 0}`；"
            f"completed `{stage_progress_log.get('completed_attempt_count') or 0}`；"
            f"blocked `{stage_progress_log.get('blocked_attempt_count') or 0}`"
        )
        if stage_progress_log.get("missing_usage_telemetry_attempt_count") is not None:
            lines.append(
                "- missing_usage_telemetry_attempt_count: "
                f"`{stage_progress_log.get('missing_usage_telemetry_attempt_count')}`"
            )
    latest_terminal_stage_log = dashboard.get("latest_terminal_stage_log")
    if isinstance(latest_terminal_stage_log, dict):
        workbench_summary = (
            latest_terminal_stage_log.get("stage_log_workbench_summary")
            if isinstance(latest_terminal_stage_log.get("stage_log_workbench_summary"), dict)
            else {}
        )
        paper_stage_log = (
            latest_terminal_stage_log.get("paper_stage_log")
            if isinstance(latest_terminal_stage_log.get("paper_stage_log"), dict)
            else {}
        )
        lines.append(
            f"- latest_terminal_stage_log: action `{latest_terminal_stage_log.get('action_type') or 'unknown'}`；"
            f"status `{latest_terminal_stage_log.get('status') or 'unknown'}`；"
            f"attempt `{latest_terminal_stage_log.get('stage_attempt_id') or 'unknown'}`"
        )
        outcome = str(paper_stage_log.get("outcome") or "").strip()
        if outcome:
            lines.append(f"- latest_terminal_stage_outcome: `{outcome}`")
        if workbench_summary:
            paper_delta = (
                workbench_summary.get("paper_delta")
                if isinstance(workbench_summary.get("paper_delta"), dict)
                else {}
            )
            platform_delta = (
                workbench_summary.get("platform_delta")
                if isinstance(workbench_summary.get("platform_delta"), dict)
                else {}
            )
            lines.append(
                "- latest_terminal_stage_workbench_summary: "
                f"paper_delta `{paper_delta.get('status') or 'missing'}`；"
                f"platform_delta `{platform_delta.get('status') or 'missing'}`；"
                f"body_free `{workbench_summary.get('body_policy') == 'refs_only_body_free'}`"
            )
        duration = (
            latest_terminal_stage_log.get("duration")
            if isinstance(latest_terminal_stage_log.get("duration"), dict)
            else {}
        )
        token_usage = (
            latest_terminal_stage_log.get("token_usage")
            if isinstance(latest_terminal_stage_log.get("token_usage"), dict)
            else {}
        )
        cost = (
            latest_terminal_stage_log.get("cost")
            if isinstance(latest_terminal_stage_log.get("cost"), dict)
            else {}
        )
        duration_seconds = duration.get("seconds")
        if duration_seconds is not None:
            lines.append(f"- latest_terminal_stage_duration_seconds: `{duration_seconds}`")
        token_total = token_usage.get("total_tokens") or token_usage.get("total")
        if token_total is not None:
            lines.append(f"- latest_terminal_stage_token_usage_total: `{token_total}`")
        cost_usd = cost.get("usd") or cost.get("cost_usd")
        if cost_usd is not None:
            lines.append(f"- latest_terminal_stage_cost_usd: `{cost_usd}`")
        missing = _compact_string_list(latest_terminal_stage_log.get("missing_observability_fields"), limit=6)
        if missing:
            lines.append(
                "- latest_terminal_stage_missing_observability: "
                + "；".join(f"`{item}`" for item in missing)
            )
        blockers = _compact_string_list(paper_stage_log.get("remaining_blockers"), limit=6)
        if blockers:
            lines.append("- latest_terminal_stage_blockers: " + "；".join(f"`{item}`" for item in blockers))
        evidence_refs = _compact_string_list(paper_stage_log.get("evidence_refs"), limit=4)
        if evidence_refs:
            lines.append("- latest_terminal_stage_evidence_refs: " + "；".join(f"`{item}`" for item in evidence_refs))
    for action in dashboard.get("action_queue") or []:
        if not isinstance(action, dict):
            continue
        lines.append(
            f"- OPL action ref: `{action.get('action_type') or action.get('action_id') or 'unknown_action'}` "
            f"{action.get('summary') or ''}".rstrip()
        )
        owner_pickup = action.get("owner_pickup") if isinstance(action.get("owner_pickup"), dict) else {}
        if owner_pickup:
            lines.append(f"  owner_pickup: `{owner_pickup.get('state') or 'unknown'}`")
        consumption = action.get("consumption") if isinstance(action.get("consumption"), dict) else {}
        if consumption:
            lines.append(
                "  developer_supervisor_attention_required: "
                f"`{consumption.get('developer_supervisor_attention_required')}`"
            )
    why_not_applied = _compact_string_list(dashboard.get("why_not_applied"), limit=8)
    if why_not_applied:
        lines.append("- why_not_applied: " + "；".join(f"`{item}`" for item in why_not_applied))
    next_owner = str(dashboard.get("next_owner") or "").strip()
    if next_owner or dashboard.get("external_supervisor_required") is not None:
        lines.append(
            f"- next_owner: `{next_owner or 'unknown'}`；"
            f"external_supervisor_required: `{dashboard.get('external_supervisor_required')}`"
        )
    return lines
