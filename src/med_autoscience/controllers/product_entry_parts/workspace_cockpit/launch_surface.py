from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_progress, study_runtime_router
from med_autoscience.controllers.product_entry_parts.shared import (
    SCHEMA_VERSION,
    WorkspaceProfile,
    _append_human_status_lines,
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
    runtime_status = _serialize_runtime_status(
        study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=resolved_study_id,
            study_root=resolved_study_root,
            entry_mode=entry_mode,
            allow_stopped_relaunch=allow_stopped_relaunch,
            explicit_user_wakeup=explicit_user_wakeup,
            force=force,
            source="product_entry",
        )
    )
    progress_payload = study_progress.build_study_progress_projection(
        profile=profile,
        profile_ref=profile_ref,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        status_payload=runtime_status,
        entry_mode=entry_mode,
    )
    resolved_study_id = (
        _non_empty_text(progress_payload.get("study_id"))
        or _non_empty_text(runtime_status.get("study_id"))
        or resolved_study_id
    )
    commands = {
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "cockpit": f"{_command_prefix(profile_ref)} workspace-cockpit --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply-supervisor-platform-repair --apply"
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
