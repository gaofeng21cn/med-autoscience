from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_truth_kernel
from med_autoscience.controllers.product_entry_parts.shared import (
    SCHEMA_VERSION,
    SUPPORTED_DIRECT_ENTRY_MODES,
    WorkspaceProfile,
    _append_human_status_lines,
    _command,
    _command_prefix,
    _non_empty_text,
    _profile_arg,
    _quote_cli_arg,
    _recovery_action_mode_label,
    _resolve_study,
    _runtime_decision_label,
    _serialize_runtime_status,
    _study_selector,
    _utc_now,
    domain_status_projection,
    study_progress,
)


def launch_study(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    allow_stopped_relaunch: bool = False,
    explicit_user_wakeup: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, _study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    selected_entry_mode = _require_launch_entry_mode(entry_mode)
    runtime_status = _serialize_runtime_status(
        domain_status_projection.progress_projection(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            entry_mode=None,
        )
    )
    explicit_wakeup_receipt = _record_explicit_user_wakeup(
        study_root=resolved_study_root,
        study_id=resolved_study_id,
        runtime_status=runtime_status,
        profile_ref=profile_ref,
        explicit_user_wakeup=explicit_user_wakeup,
    )
    if explicit_wakeup_receipt is not None:
        runtime_status = _serialize_runtime_status(
            domain_status_projection.progress_projection(
                profile=profile,
                study_id=resolved_study_id,
                study_root=resolved_study_root,
                entry_mode=None,
            )
        )
        runtime_status["study_truth_snapshot"] = explicit_wakeup_receipt["snapshot"]
    runtime_status["product_entry_launch_policy"] = {
        "status": "opl_attempt_admission_required",
        "entry_mode": selected_entry_mode,
        "supported_entry_modes": list(SUPPORTED_DIRECT_ENTRY_MODES),
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_executes_runtime_attempt": False,
        "allow_stopped_relaunch_requested": bool(allow_stopped_relaunch),
        "explicit_user_wakeup_requested": bool(explicit_user_wakeup),
        "explicit_user_wakeup_recorded": explicit_wakeup_receipt is not None,
        "explicit_user_wakeup_ref": (explicit_wakeup_receipt or {}).get("event_id"),
        "study_truth_snapshot_ref": (explicit_wakeup_receipt or {}).get("snapshot_path"),
        "owner_handoff_hydration_required": explicit_wakeup_receipt is not None,
        "owner_handoff_hydration_action": (
            "hydrate_opl_owner_route_from_explicit_resume" if explicit_wakeup_receipt is not None else None
        ),
        "owner_handoff_hydration_owner": "one-person-lab" if explicit_wakeup_receipt is not None else None,
        "force_requested": bool(force),
    }
    progress_payload = study_progress.build_study_progress_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status_payload=runtime_status,
        entry_mode=selected_entry_mode,
    )
    resolved_study_id = (
        _non_empty_text(progress_payload.get("study_id"))
        or _non_empty_text(runtime_status.get("study_id"))
        or resolved_study_id
    )
    commands = {
        "progress": (
            f"{_command(profile_ref, 'study-progress', '--profile', _profile_arg(profile_ref))} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)} --format json"
        ),
        "cockpit": _command(profile_ref, "workspace-cockpit", "--profile", _profile_arg(profile_ref)),
        "owner_route_handoff": (
            f"{_command_prefix(profile_ref)} owner-route-reconcile "
            f"--profile {_profile_arg(profile_ref)} {_study_selector(study_id=resolved_study_id)} "
            "--developer-supervisor-mode external_observe"
        ),
        "diagnostic_tick": (
            f"{_command_prefix(profile_ref)} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)}"
        ),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "study_id": resolved_study_id,
        "runtime_status": runtime_status,
        "progress": progress_payload,
        "commands": commands,
    }


def _require_launch_entry_mode(value: str | None) -> str:
    mode = _non_empty_text(value) or "opl-handoff"
    if mode not in SUPPORTED_DIRECT_ENTRY_MODES:
        supported = ", ".join(SUPPORTED_DIRECT_ENTRY_MODES)
        raise ValueError(f"study launch entry mode 不支持: {mode}; supported_entry_modes={supported}")
    return mode


def _record_explicit_user_wakeup(
    *,
    study_root: Path,
    study_id: str,
    runtime_status: dict[str, Any],
    profile_ref: str | Path | None,
    explicit_user_wakeup: bool,
) -> dict[str, Any] | None:
    if not explicit_user_wakeup:
        return None
    recorded_at = _utc_now()
    event = study_truth_kernel.append_truth_event(
        study_root=study_root,
        study_id=study_id,
        event_type="explicit_resume",
        payload={
            "current_required_action": "resume_same_study_line",
            "summary": "User explicitly requested MAS study resume through launch-study.",
            "resume_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "quest_id": _non_empty_text(runtime_status.get("quest_id")),
            "quest_status": _non_empty_text(runtime_status.get("quest_status")),
            "previous_reason": _non_empty_text(runtime_status.get("reason")),
            "previous_decision": _non_empty_text(runtime_status.get("decision")),
            "profile_ref": str(profile_ref) if profile_ref is not None else None,
        },
        recorded_at=recorded_at,
    )
    snapshot_path = study_truth_kernel.materialize_truth_snapshot(study_root=study_root, study_id=study_id)
    snapshot = study_truth_kernel.rebuild_truth_snapshot(study_root=study_root, study_id=study_id)
    return {
        "event_id": event["event_id"],
        "snapshot_path": str(snapshot_path),
        "snapshot": snapshot,
    }


def render_launch_study_markdown(payload: dict[str, Any]) -> str:
    progress_payload = dict(payload.get("progress") or {})
    supervision = dict(progress_payload.get("supervision") or {})
    blockers = list(progress_payload.get("current_blockers") or [])
    task_intake = dict(progress_payload.get("task_intake") or {})
    progress_freshness = dict(progress_payload.get("progress_freshness") or {})
    recovery_contract = dict(progress_payload.get("recovery_contract") or {})
    recommended_commands = [
        dict(item)
        for item in (progress_payload.get("recommended_commands") or [])
        if isinstance(item, dict)
    ]
    lines = [
        "# Launch Study",
        "",
        f"- 当前 study: `{payload.get('study_id')}`",
        f"- 当前运行判断: {_runtime_decision_label((payload.get('runtime_status') or {}).get('decision'))}",
        f"- 浏览器入口: `{supervision.get('browser_url') or 'none'}`",
        f"- 当前运行批次: `{supervision.get('active_run_id') or 'none'}`",
    ]
    _append_human_status_lines(lines, progress_payload)
    if task_intake:
        lines.extend(
            [
                f"- 当前任务意图: {task_intake.get('task_intent') or '未提供'}",
                f"- 当前投稿目标: {task_intake.get('journal_target') or 'none'}",
            ]
        )
    if progress_freshness.get("summary"):
        lines.append(f"- 进度信号: {progress_freshness.get('summary')}")
    lines.extend(["", "## Blockers", ""])
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 当前没有新的硬阻塞。")
    if recovery_contract:
        lines.extend(["", "## 恢复建议", ""])
        if recovery_contract.get("contract_kind"):
            lines.append(f"- 恢复合同类型: `{recovery_contract.get('contract_kind')}`")
        recovery_action_mode_label = _recovery_action_mode_label(recovery_contract)
        if recovery_action_mode_label:
            lines.append(f"- 当前恢复模式: {recovery_action_mode_label}")
        if recovery_contract.get("summary"):
            lines.append(f"- 当前恢复判断: {recovery_contract.get('summary')}")
        for item in recommended_commands:
            title = _non_empty_text(item.get("title")) or _non_empty_text(item.get("step_id")) or "unnamed"
            lines.append(f"- {title}: `{item.get('command') or 'none'}`")
    lines.extend(["", "## Commands", ""])
    for name, command in (payload.get("commands") or {}).items():
        lines.append(f"- `{name}`: `{command}`")
    lines.append("")
    return "\n".join(lines)
