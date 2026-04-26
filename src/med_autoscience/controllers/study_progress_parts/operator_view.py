from __future__ import annotations

from . import shared as _shared
from . import publication_runtime as _publication_runtime
from . import progression as _progression

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_publication_runtime)
_module_reexport(_progression)

def _recovery_step(
    *,
    step_id: str,
    title: str,
    surface_kind: str,
    command: str,
) -> dict[str, str]:
    return {
        "step_id": step_id,
        "title": title,
        "surface_kind": surface_kind,
        "command": command,
    }


def _study_command_surfaces(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    profile_ref: str | Path | None,
) -> dict[str, str]:
    prefix = _command_prefix(profile_ref)
    profile_arg = _profile_arg(profile_ref)
    selector = _study_selector(study_id=study_id)
    return {
        "workspace_cockpit": f"{prefix} workspace cockpit --profile {profile_arg}",
        "study_progress": f"{prefix} study progress --profile {profile_arg} {selector}",
        "study_runtime_status": f"{prefix} study-runtime-status --profile {profile_arg} {selector}",
        "quality_repair_batch": f"{prefix} study quality-repair-batch --profile {profile_arg} {selector}",
        "launch_study": f"{prefix} study launch --profile {profile_arg} {selector}",
        "refresh_supervision": (
            f"{prefix} runtime watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {profile_arg} --ensure-study-runtimes --apply"
        ),
    }


def _recovery_contract(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    profile_ref: str | Path | None,
    intervention_lane: dict[str, Any],
    current_stage_summary: str,
    next_system_action: str,
    current_blockers: list[str],
) -> tuple[str | None, list[dict[str, str]], dict[str, Any]]:
    commands = _study_command_surfaces(profile=profile, study_id=study_id, profile_ref=profile_ref)
    lane_id = _non_empty_text(intervention_lane.get("lane_id")) or "monitor_only"
    summary = (
        _non_empty_text(intervention_lane.get("summary"))
        or _non_empty_text(current_blockers[0] if current_blockers else None)
        or current_stage_summary
        or next_system_action
        or "当前 study 没有新的接管动作。"
    )

    if lane_id == "workspace_supervision_gap":
        steps = [
            _recovery_step(
                step_id="refresh_supervision",
                title="刷新 Hermes-hosted supervision tick",
                surface_kind="runtime_watch_refresh",
                command=commands["refresh_supervision"],
            ),
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
        ]
        action_mode = "refresh_supervision"
    elif lane_id in {"runtime_recovery_required", "runtime_blocker"}:
        steps = [
            _recovery_step(
                step_id="continue_or_relaunch",
                title="继续或重新拉起当前 study",
                surface_kind="launch_study",
                command=commands["launch_study"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
        ]
        action_mode = "continue_or_relaunch"
    elif lane_id == "human_decision_gate":
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="open_workspace_cockpit",
                title="返回 workspace cockpit",
                surface_kind="workspace_cockpit",
                command=commands["workspace_cockpit"],
            ),
        ]
        action_mode = "human_decision_review"
    elif lane_id == "manual_finishing":
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="open_workspace_cockpit",
                title="返回 workspace cockpit",
                surface_kind="workspace_cockpit",
                command=commands["workspace_cockpit"],
            ),
        ]
        action_mode = "maintain_compatibility_guard"
    elif lane_id in {"quality_floor_blocker", "study_progress_gap"}:
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
            _recovery_step(
                step_id="open_workspace_cockpit",
                title="返回 workspace cockpit",
                surface_kind="workspace_cockpit",
                command=commands["workspace_cockpit"],
            ),
        ]
        action_mode = "inspect_progress"
    else:
        steps = [
            _recovery_step(
                step_id="inspect_study_progress",
                title="读取当前研究进度",
                surface_kind="study_progress",
                command=commands["study_progress"],
            ),
            _recovery_step(
                step_id="inspect_runtime_status",
                title="读取结构化运行真相",
                surface_kind="study_runtime_status",
                command=commands["study_runtime_status"],
            ),
        ]
        action_mode = "monitor_only"

    recovery_contract = {
        "contract_kind": "study_recovery_contract",
        "lane_id": lane_id,
        "action_mode": action_mode,
        "summary": summary,
        "recommended_step_id": steps[0]["step_id"] if steps else None,
        "steps": steps,
    }
    recommended_command = steps[0]["command"] if steps else None
    return recommended_command, steps, recovery_contract


def _restore_point(
    *,
    continuation_state: dict[str, Any],
    family_checkpoint_lineage: dict[str, Any],
    needs_physician_decision: bool,
) -> dict[str, Any]:
    resume_contract_payload = family_checkpoint_lineage.get("resume_contract")
    resume_contract = dict(resume_contract_payload) if isinstance(resume_contract_payload, dict) else {}
    resume_mode = _non_empty_text(resume_contract.get("resume_mode"))
    continuation_policy = _non_empty_text(continuation_state.get("continuation_policy"))
    continuation_reason = (
        _continuation_reason_label(continuation_state.get("continuation_reason"))
        or _non_empty_text(continuation_state.get("continuation_reason"))
    )
    if isinstance(resume_contract.get("human_gate_required"), bool):
        human_gate_required = bool(resume_contract.get("human_gate_required"))
    else:
        human_gate_required = needs_physician_decision
    if resume_mode is not None or continuation_policy is not None or continuation_reason is not None:
        summary_parts: list[str] = []
        if resume_mode is not None:
            summary_parts.append(f"当前恢复点采用 {resume_mode}")
        else:
            summary_parts.append("当前恢复点已冻结")
        if continuation_policy is not None:
            summary_parts.append(f"continuation policy 为 {continuation_policy}")
        if continuation_reason is not None:
            summary_parts.append(f"最近一次续跑原因是{continuation_reason}")
        if human_gate_required:
            summary_parts.append("恢复前仍需人工确认")
        summary = "；".join(summary_parts) + "。"
    elif human_gate_required:
        summary = "当前还没有额外 checkpoint resume contract；恢复前仍需人工确认。"
    else:
        summary = "当前还没有额外 checkpoint resume contract；可以直接回到 MAS 主线继续恢复或重启当前 study。"
    return {
        "resume_mode": resume_mode,
        "continuation_policy": continuation_policy,
        "continuation_reason": continuation_reason,
        "human_gate_required": human_gate_required,
        "summary": summary,
    }


def _latest_outer_loop_dispatch(
    *,
    study_id: str,
    runtime_watch_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    dispatch_block = (
        dict((runtime_watch_payload or {}).get("managed_study_outer_loop_dispatch") or {})
        if isinstance((runtime_watch_payload or {}).get("managed_study_outer_loop_dispatch"), dict)
        else {}
    )
    if dispatch_block and _non_empty_text(dispatch_block.get("study_id")) == study_id:
        dispatches: list[dict[str, Any]] = [dispatch_block]
    else:
        dispatches = [
            dict(item)
            for item in ((runtime_watch_payload or {}).get("managed_study_outer_loop_dispatches") or [])
            if isinstance(item, dict)
        ]
    for item in reversed(dispatches):
        if _non_empty_text(item.get("study_id")) != study_id:
            continue
        route_target = _non_empty_text(item.get("route_target"))
        if route_target is None:
            continue
        route_target_label = _paper_stage_label(route_target) or route_target
        route_key_question = _display_text(item.get("route_key_question")) or _non_empty_text(item.get("route_key_question"))
        decision_type = _non_empty_text(item.get("decision_type"))
        verb = "进入" if decision_type == "bounded_analysis" else "转到"
        if route_key_question is not None:
            summary = f"最近一次自治外环已{verb}“{route_target_label}”，当前关键问题是“{route_key_question}”。"
        else:
            summary = f"最近一次自治外环已{verb}“{route_target_label}”。"
        return {
            "decision_type": decision_type,
            "route_target": route_target,
            "route_target_label": route_target_label,
            "route_key_question": route_key_question,
            "dispatch_status": _non_empty_text(item.get("dispatch_status")),
            "summary": summary,
        }
    return None


def _autonomy_contract(
    *,
    study_id: str,
    intervention_lane: dict[str, Any],
    recovery_contract: dict[str, Any],
    recommended_command: str | None,
    current_stage_summary: str,
    next_system_action: str,
    continuation_state: dict[str, Any],
    family_checkpoint_lineage: dict[str, Any],
    runtime_watch_payload: dict[str, Any] | None,
    needs_physician_decision: bool,
    manual_finish_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    restore_point = _restore_point(
        continuation_state=continuation_state,
        family_checkpoint_lineage=family_checkpoint_lineage,
        needs_physician_decision=needs_physician_decision,
    )
    latest_outer_loop_dispatch = _latest_outer_loop_dispatch(
        study_id=study_id,
        runtime_watch_payload=runtime_watch_payload,
    )
    lane_id = _non_empty_text(intervention_lane.get("lane_id")) or "monitor_only"
    if _manual_finish_active(manual_finish_contract):
        autonomy_state = "compatibility_guard"
    elif needs_physician_decision:
        autonomy_state = "human_gate"
    elif lane_id in {"workspace_supervision_gap", "runtime_recovery_required", "runtime_blocker"}:
        autonomy_state = "runtime_recovery"
    else:
        autonomy_state = "autonomous_progress"
    if autonomy_state == "autonomous_progress" and latest_outer_loop_dispatch is not None:
        summary = str(latest_outer_loop_dispatch.get("summary") or "").strip()
    elif autonomy_state == "autonomous_progress" and restore_point.get("resume_mode"):
        summary = f"恢复点已冻结；当前停在 {restore_point.get('resume_mode')}，下一次确认看恢复信号。"
    else:
        summary = (
            _non_empty_text(intervention_lane.get("summary"))
            or _non_empty_text(recovery_contract.get("summary"))
            or current_stage_summary
            or next_system_action
            or str(restore_point.get("summary") or "").strip()
        )
    return {
        "contract_kind": "study_autonomy_contract",
        "autonomy_state": autonomy_state,
        "summary": summary,
        "recommended_command": recommended_command,
        "next_signal": next_system_action or str(restore_point.get("summary") or "").strip(),
        "restore_point": restore_point,
        "latest_outer_loop_dispatch": latest_outer_loop_dispatch,
    }


def _autonomy_soak_status(
    *,
    autonomy_contract: dict[str, Any],
    progress_freshness: dict[str, Any],
    runtime_watch_path: Path | None,
    controller_decision_path: Path,
) -> dict[str, Any] | None:
    latest_outer_loop_dispatch = dict(autonomy_contract.get("latest_outer_loop_dispatch") or {})
    if not latest_outer_loop_dispatch:
        return None
    return {
        "surface_kind": "study_autonomy_soak_status",
        "status": "autonomous_dispatch_visible",
        "summary": str(latest_outer_loop_dispatch.get("summary") or "").strip(),
        "autonomy_state": _non_empty_text(autonomy_contract.get("autonomy_state")),
        "dispatch_status": _non_empty_text(latest_outer_loop_dispatch.get("dispatch_status")),
        "route_target": _non_empty_text(latest_outer_loop_dispatch.get("route_target")),
        "route_target_label": _non_empty_text(latest_outer_loop_dispatch.get("route_target_label")),
        "route_key_question": _non_empty_text(latest_outer_loop_dispatch.get("route_key_question")),
        "progress_freshness_status": _non_empty_text(progress_freshness.get("status")),
        "next_confirmation_signal": _non_empty_text(autonomy_contract.get("next_signal")),
        "proof_refs": [
            ref
            for ref in (
                str(runtime_watch_path) if runtime_watch_path is not None else None,
                str(controller_decision_path),
            )
            if ref is not None
        ],
    }


def _research_runtime_control_projection(
    *,
    study_commands: Mapping[str, str],
    autonomy_contract: Mapping[str, Any],
    operator_status_card: Mapping[str, Any],
    continuation_state: Mapping[str, Any],
    family_checkpoint_lineage: Mapping[str, Any],
    intervention_lane: Mapping[str, Any],
    needs_physician_decision: bool,
    evaluation_summary_ref: str | None,
    publication_eval_ref: str,
    controller_decision_ref: str,
    runtime_supervision_ref: str | None,
    runtime_watch_ref: str | None,
) -> dict[str, Any]:
    restore_point = _mapping_copy(autonomy_contract.get("restore_point"))
    interrupt_policy = _non_empty_text(intervention_lane.get("recommended_action_id"))
    pickup_refs = _runtime_control_pickup_refs(
        evaluation_summary_ref=evaluation_summary_ref,
        publication_eval_ref=publication_eval_ref,
        controller_decision_ref=controller_decision_ref,
        runtime_supervision_ref=runtime_supervision_ref,
        runtime_watch_ref=runtime_watch_ref,
    )
    return {
        "surface_kind": "research_runtime_control_projection",
        "study_session_owner": {
            "runtime_owner": "upstream_hermes_agent",
            "study_owner": "med-autoscience",
            "executor_owner": "med_deepscientist",
        },
        "session_lineage_surface": {
            "surface_kind": "study_progress",
            "field_path": "family_checkpoint_lineage",
            "resume_contract_field": "family_checkpoint_lineage.resume_contract",
            "continuation_state_field": "continuation_state",
            "active_run_id_field": "supervision.active_run_id",
            "lineage_version": _non_empty_text(family_checkpoint_lineage.get("version")),
            "continuation_anchor": _non_empty_text(continuation_state.get("continuation_anchor")),
        },
        "restore_point_surface": {
            "surface_kind": "study_progress",
            "field_path": "autonomy_contract.restore_point",
            "lineage_anchor_field": "family_checkpoint_lineage.resume_contract",
            "summary": _non_empty_text(restore_point.get("summary")),
        },
        "progress_cursor_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
        },
        "progress_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
            "fallback_field_path": "next_system_action",
            "workspace_cockpit_command": _non_empty_text(study_commands.get("workspace_cockpit")),
            "current_focus": _non_empty_text(operator_status_card.get("current_focus")),
        },
        "artifact_inventory_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs",
            "refs": {
                "evaluation_summary_path": evaluation_summary_ref,
                "publication_eval_path": publication_eval_ref,
                "controller_decision_path": controller_decision_ref,
                "runtime_supervision_path": runtime_supervision_ref,
                "runtime_watch_report_path": runtime_watch_ref,
            },
        },
        "artifact_pickup_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs.evaluation_summary_path",
            "fallback_fields": [
                "refs.publication_eval_path",
                "refs.controller_decision_path",
                "refs.runtime_supervision_path",
                "refs.runtime_watch_report_path",
            ],
            "pickup_refs": pickup_refs,
        },
        "command_templates": {
            "resume": _non_empty_text(study_commands.get("launch_study")),
            "check_progress": _non_empty_text(study_commands.get("study_progress")),
            "check_runtime_status": _non_empty_text(study_commands.get("study_runtime_status")),
        },
        "research_gate_surface": {
            "surface_kind": "study_progress",
            "approval_gate_field": "needs_physician_decision",
            "approval_gate_owner": "mas_controller",
            "approval_gate_required": bool(needs_physician_decision),
            "interrupt_policy_field": "intervention_lane.recommended_action_id",
            "interrupt_policy": interrupt_policy,
            "gate_lane_field": "intervention_lane.lane_id",
            "gate_lane": _non_empty_text(intervention_lane.get("lane_id")),
            "gate_summary_field": "intervention_lane.summary",
            "gate_summary": _non_empty_text(intervention_lane.get("summary")),
        },
    }


def _operator_verdict(
    *,
    study_id: str,
    intervention_lane: dict[str, Any],
    recovery_contract: dict[str, Any],
    recommended_command: str | None,
    current_stage_summary: str,
    next_system_action: str,
    current_blockers: list[str],
) -> dict[str, Any]:
    lane_id = _non_empty_text(intervention_lane.get("lane_id")) or "monitor_only"
    severity = _non_empty_text(intervention_lane.get("severity")) or "observe"
    summary = (
        _non_empty_text(intervention_lane.get("summary"))
        or _non_empty_text(current_blockers[0] if current_blockers else None)
        or current_stage_summary
        or next_system_action
        or "当前 study 没有新的接管动作。"
    )
    primary_step_id = _non_empty_text((recovery_contract or {}).get("recommended_step_id"))
    primary_surface_kind = None
    for step in (recovery_contract or {}).get("steps") or []:
        if not isinstance(step, dict):
            continue
        if _non_empty_text(step.get("step_id")) == primary_step_id:
            primary_surface_kind = _non_empty_text(step.get("surface_kind"))
            break

    if lane_id in {"workspace_supervision_gap", "runtime_recovery_required", "runtime_blocker"}:
        decision_mode = "intervene_now"
    elif lane_id == "human_decision_gate":
        decision_mode = "human_decision_required"
    elif lane_id == "manual_finishing":
        decision_mode = "compatibility_guard_only"
    else:
        decision_mode = "monitor_only"

    payload = {
        "surface_kind": "study_operator_verdict",
        "verdict_id": f"study_operator_verdict::{study_id}::{lane_id}",
        "study_id": study_id,
        "lane_id": lane_id,
        "severity": severity,
        "decision_mode": decision_mode,
        "needs_intervention": decision_mode in {"intervene_now", "human_decision_required"},
        "focus_scope": "workspace" if lane_id == "workspace_supervision_gap" else "study",
        "summary": summary,
        "reason_summary": summary,
        "primary_step_id": primary_step_id,
        "primary_surface_kind": primary_surface_kind,
        "primary_command": recommended_command,
    }
    for field_name in (
        "repair_mode",
        "repair_mode_label",
        "route_target",
        "route_target_label",
        "route_key_question",
        "route_rationale",
        "route_summary",
    ):
        value = _non_empty_text(intervention_lane.get(field_name))
        if value is not None:
            payload[field_name] = value
    return payload


def _operator_status_handling_state(
    *,
    current_stage: str,
    intervention_lane: dict[str, Any],
    needs_physician_decision: bool,
    current_blockers: list[str],
    manual_finish_contract: dict[str, Any] | None,
) -> str:
    lane_id = _non_empty_text((intervention_lane or {}).get("lane_id")) or "monitor_only"
    if _manual_finish_active(manual_finish_contract):
        return "manual_finishing"
    if lane_id == "workspace_supervision_gap":
        return "runtime_supervision_recovering"
    if lane_id in {"runtime_recovery_required", "runtime_blocker"} or current_stage in {
        "managed_runtime_recovering",
        "managed_runtime_degraded",
        "managed_runtime_escalated",
        "runtime_blocked",
    }:
        return "runtime_recovering"
    if needs_physician_decision or lane_id == "human_decision_gate":
        return "waiting_human_decision"
    if any(str(item or "").strip() in _HUMAN_SURFACE_REFRESH_BLOCKER_LABELS for item in current_blockers):
        return "paper_surface_refresh_in_progress"
    if lane_id == "quality_floor_blocker":
        return "scientific_or_quality_repair_in_progress"
    return "monitor_only"


def _latest_event_snapshot(latest_events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for item in latest_events:
        if not isinstance(item, dict):
            continue
        timestamp = _non_empty_text(item.get("timestamp"))
        if timestamp is None:
            continue
        source = _non_empty_text(item.get("source")) or _non_empty_text(item.get("category")) or "latest_event"
        return "latest_event", timestamp if source is None else timestamp
    return None, None


def _operator_status_truth_snapshot(
    *,
    handling_state: str,
    latest_events: list[dict[str, Any]],
    publication_eval_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
) -> tuple[str | None, str | None]:
    latest_event_source, latest_event_time = _latest_event_snapshot(latest_events)
    candidates_by_state = {
        "runtime_supervision_recovering": (
            ("supervisor_tick_audit", _non_empty_text((supervisor_tick_audit or {}).get("latest_recorded_at"))),
            ("runtime_supervision", _non_empty_text((runtime_supervision_payload or {}).get("recorded_at"))),
            (latest_event_source, latest_event_time),
        ),
        "runtime_recovering": (
            ("runtime_supervision", _non_empty_text((runtime_supervision_payload or {}).get("recorded_at"))),
            ("supervisor_tick_audit", _non_empty_text((supervisor_tick_audit or {}).get("latest_recorded_at"))),
            (latest_event_source, latest_event_time),
        ),
        "paper_surface_refresh_in_progress": (
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
            (latest_event_source, latest_event_time),
        ),
        "scientific_or_quality_repair_in_progress": (
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
            (latest_event_source, latest_event_time),
        ),
        "waiting_human_decision": (
            ("controller_confirmation", _non_empty_text((controller_confirmation_summary or {}).get("requested_at"))),
            ("controller_decision", _non_empty_text((controller_decision_payload or {}).get("emitted_at"))),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            (latest_event_source, latest_event_time),
        ),
        "manual_finishing": (
            (latest_event_source, latest_event_time),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
        ),
        "monitor_only": (
            (latest_event_source, latest_event_time),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
        ),
    }
    for source, timestamp in candidates_by_state.get(handling_state, ((latest_event_source, latest_event_time),)):
        if source is not None and timestamp is not None:
            return source, timestamp
    return None, None


def _operator_status_human_surface_summary(handling_state: str) -> tuple[str, str]:
    if handling_state == "paper_surface_refresh_in_progress":
        return "stale", "给人看的投稿包镜像仍落后于当前论文真相。"
    if handling_state == "waiting_human_decision":
        return "pending_decision", "当前主要等待人工判断，给人看的稿件状态以论文门控为准。"
    if handling_state in {"runtime_supervision_recovering", "runtime_recovering"}:
        return "monitoring_runtime", "当前优先看结构化监管真相，给人看的稿件表面还不是主判断面。"
    return "current", "给人看的稿件表面当前没有额外刷新告警。"


def _operator_status_verdict(handling_state: str) -> str:
    if handling_state == "runtime_supervision_recovering":
        return "MAS 正在恢复外环监管，当前 study 仍处在受管修复中。"
    if handling_state == "runtime_recovering":
        return "MAS 正在处理 runtime recovery，当前 study 仍处在受管修复中。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在处理论文可发表性硬阻塞，给人看的稿件还没到放行状态。"
    if handling_state == "waiting_human_decision":
        return "MAS 已经把自动侧能做的部分推进完成，当前在等医生或 PI 判断。"
    if handling_state == "manual_finishing":
        return "MAS 当前保持人工收尾兼容保护，并继续提供监督入口。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_owner_summary(handling_state: str) -> str:
    if handling_state == "runtime_supervision_recovering":
        return "MAS 正在恢复 workspace 级监管心跳，托管执行仍由 runtime 持有。"
    if handling_state == "runtime_recovering":
        return "MAS 正在根据 runtime supervision 真相继续处理恢复。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "MAS 正在根据 publication gate 真相刷新给人看的投稿包镜像。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在收口论文可发表性与质量硬阻塞。"
    if handling_state == "waiting_human_decision":
        return "MAS 已把下一步提升到医生或 PI 决策面，并继续保持监管。"
    if handling_state == "manual_finishing":
        return "MAS 当前只保持人工收尾兼容保护和监督入口。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_focus_summary(
    *,
    handling_state: str,
    intervention_lane: dict[str, Any],
    next_system_action: str,
    current_stage_summary: str,
) -> str:
    if handling_state == "paper_surface_refresh_in_progress":
        return "优先把人类查看面同步到当前论文真相，再继续盯论文门控。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        route_summary = _non_empty_text((intervention_lane or {}).get("route_summary"))
        if route_summary is not None:
            return route_summary
    return (
        _non_empty_text(next_system_action)
        or _non_empty_text((intervention_lane or {}).get("summary"))
        or _non_empty_text(current_stage_summary)
        or "继续按当前 study 的结构化真相推进。"
    )


def _operator_status_next_confirmation_signal(handling_state: str, intervention_lane: dict[str, Any]) -> str:
    if handling_state == "runtime_supervision_recovering":
        return "看 supervisor tick 是否回到 fresh，并确认监管缺口告警从 attention queue 消失。"
    if handling_state == "runtime_recovering":
        return "看 runtime_supervision/latest.json 的 health_status 回到 live，或最近明确推进时间刷新。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "看 manuscript/delivery_manifest.json、current_package，或 submission_minimal 是否被刷新到最新真相。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        route_label = _non_empty_text((intervention_lane or {}).get("route_target_label"))
        key_question = _non_empty_text((intervention_lane or {}).get("route_key_question"))
        if route_label is not None and key_question is not None:
            return (
                f"看 publication_eval/latest.json 是否把“{route_label}”这条修复线继续收窄，"
                f"以及“{key_question}”是否已经被关闭。"
            )
        return "看 publication_eval/latest.json 或 runtime_watch 里的 blocker 是否减少。"
    if handling_state == "waiting_human_decision":
        return "看 controller_confirmation_summary 是否清空或变化，或 controller_decisions/latest.json 是否写出人工确认后的下一步。"
    if handling_state == "manual_finishing":
        return "看人工收尾是否写出新的明确结论，或兼容保护是否仍然保持 active。"
    return "看下一条 runtime progress / publication_eval 更新。"


def _operator_status_card(
    *,
    study_id: str,
    current_stage: str,
    current_stage_summary: str,
    intervention_lane: dict[str, Any],
    needs_physician_decision: bool,
    current_blockers: list[str],
    next_system_action: str,
    latest_events: list[dict[str, Any]],
    publication_eval_payload: dict[str, Any] | None,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_decision_payload: dict[str, Any] | None,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_supervision_payload: dict[str, Any] | None,
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
) -> dict[str, Any]:
    handling_state = _operator_status_handling_state(
        current_stage=current_stage,
        intervention_lane=intervention_lane,
        needs_physician_decision=needs_physician_decision,
        current_blockers=current_blockers,
        manual_finish_contract=manual_finish_contract,
    )
    latest_truth_source, latest_truth_time = _operator_status_truth_snapshot(
        handling_state=handling_state,
        latest_events=latest_events,
        publication_eval_payload=publication_eval_payload,
        controller_confirmation_summary=controller_confirmation_summary,
        controller_decision_payload=controller_decision_payload,
        runtime_watch_payload=runtime_watch_payload,
        runtime_supervision_payload=runtime_supervision_payload,
        supervisor_tick_audit=supervisor_tick_audit,
    )
    human_surface_freshness, human_surface_summary = _operator_status_human_surface_summary(handling_state)
    return {
        "surface_kind": "study_operator_status_card",
        "study_id": study_id,
        "handling_state": handling_state,
        "handling_state_label": _OPERATOR_STATUS_HANDLING_LABELS.get(handling_state),
        "owner_summary": _operator_status_owner_summary(handling_state),
        "current_focus": _operator_status_focus_summary(
            handling_state=handling_state,
            intervention_lane=intervention_lane,
            next_system_action=next_system_action,
            current_stage_summary=current_stage_summary,
        ),
        "latest_truth_time": latest_truth_time,
        "latest_truth_source": latest_truth_source,
        "latest_truth_source_label": (
            _OPERATOR_STATUS_TRUTH_SOURCE_LABELS.get(latest_truth_source)
            if latest_truth_source is not None
            else None
        ),
        "human_surface_freshness": human_surface_freshness,
        "human_surface_summary": human_surface_summary,
        "next_confirmation_signal": _operator_status_next_confirmation_signal(handling_state, intervention_lane),
        "user_visible_verdict": _operator_status_verdict(handling_state),
    }


def _task_intake_override_event_summary(task_intake_progress_override: dict[str, Any] | None) -> str | None:
    if not isinstance(task_intake_progress_override, dict) or not task_intake_progress_override:
        return None
    quality_closure_truth = _mapping_copy(task_intake_progress_override.get("quality_closure_truth"))
    for value in (
        quality_closure_truth.get("summary"),
        task_intake_progress_override.get("current_stage_summary"),
        task_intake_progress_override.get("next_system_action"),
    ):
        summary = _display_text(value) or _non_empty_text(value)
        if summary is not None:
            return summary
    return None


def _latest_events(
    *,
    launch_report_payload: dict[str, Any] | None,
    launch_report_path: Path,
    runtime_supervision_payload: dict[str, Any] | None,
    runtime_supervision_path: Path | None,
    runtime_escalation_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    publication_eval_payload: dict[str, Any] | None,
    publication_eval_path: Path,
    controller_decision_payload: dict[str, Any] | None,
    controller_decision_path: Path,
    runtime_watch_payload: dict[str, Any] | None,
    runtime_watch_path: Path | None,
    details_projection_payload: dict[str, Any] | None,
    details_projection_path: Path | None,
    bash_summary_payload: dict[str, Any] | None,
    bash_summary_path: Path | None,
    publication_supervisor_state: dict[str, Any] | None = None,
    task_intake_progress_override: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    task_override_summary = _task_intake_override_event_summary(task_intake_progress_override)
    if runtime_supervision_payload is not None:
        runtime_health_status = _non_empty_text(runtime_supervision_payload.get("health_status")) or "runtime"
        runtime_summary = (
            _non_empty_text(runtime_supervision_payload.get("summary"))
            or _non_empty_text(runtime_supervision_payload.get("clinician_update"))
            or "运行健康状态已刷新。"
        )
        item = _event(
            timestamp=_non_empty_text(runtime_supervision_payload.get("recorded_at")),
            category="runtime_supervision",
            title=f"托管运行监管状态更新（{runtime_health_status}）",
            summary=runtime_summary,
            source="runtime_supervision",
            artifact_path=runtime_supervision_path,
        )
        if item is not None:
            events.append(item)
    latest_session = (bash_summary_payload or {}).get("latest_session")
    if isinstance(latest_session, dict):
        last_progress = latest_session.get("last_progress")
        if isinstance(last_progress, dict):
            summary = _non_empty_text(last_progress.get("message")) or _non_empty_text(last_progress.get("step"))
            if summary is not None:
                item = _event(
                    timestamp=_non_empty_text(last_progress.get("ts")) or _non_empty_text(latest_session.get("updated_at")),
                    category="runtime_progress",
                    title="托管运行时完成一段推进",
                    summary=summary,
                    source="bash_summary",
                    artifact_path=bash_summary_path,
                )
                if item is not None:
                    events.append(item)
    if details_projection_payload is not None:
        status_line = _non_empty_text(((details_projection_payload.get("summary") or {}).get("status_line")))
        if status_line is not None:
            item = _event(
                timestamp=_non_empty_text(((details_projection_payload.get("summary") or {}).get("updated_at")))
                or _non_empty_text((details_projection_payload or {}).get("generated_at")),
                category="paper_projection",
                title="论文进度投影刷新",
                summary=status_line,
                source="details_projection",
                artifact_path=details_projection_path,
            )
            if item is not None:
                events.append(item)
    if controller_decision_payload is not None:
        decision_type = _decision_type_label(controller_decision_payload.get("decision_type")) or "形成控制面决定"
        reason = _non_empty_text(controller_decision_payload.get("reason"))
        summary = f"控制面正式决定：{decision_type}。"
        if reason is not None:
            summary += f" 原因：{reason}"
        item = _event(
            timestamp=_non_empty_text(controller_decision_payload.get("emitted_at")),
            category="controller_decision",
            title="控制面写入下一步决定",
            summary=summary,
            source="controller_decision",
            artifact_path=controller_decision_path,
        )
        if item is not None:
            events.append(item)
    if publication_eval_payload is not None:
        verdict = (publication_eval_payload.get("verdict") or {}) if isinstance(publication_eval_payload, dict) else {}
        verdict_summary = (
            task_override_summary
            or _display_text(_non_empty_text(verdict.get("summary")))
            or _non_empty_text(verdict.get("summary"))
            or "发表评估已更新。"
        )
        item = _event(
            timestamp=_non_empty_text(publication_eval_payload.get("emitted_at")),
            category="publication_eval",
            title="发表可行性评估更新",
            summary=verdict_summary,
            source="publication_eval",
            artifact_path=publication_eval_path,
        )
        if item is not None:
            events.append(item)
    if runtime_watch_payload is not None:
        publication_gate = ((runtime_watch_payload.get("controllers") or {}).get("publication_gate"))
        if not _publication_supervisor_state_conflicts(
            current=publication_supervisor_state,
            candidate=publication_gate if isinstance(publication_gate, dict) else None,
        ):
            watch_summary = "系统完成一次研究运行巡检。"
            if isinstance(publication_gate, dict):
                controller_note = _non_empty_text(publication_gate.get("controller_stage_note"))
                if task_override_summary is not None:
                    watch_summary = task_override_summary
                elif controller_note is not None:
                    watch_summary = _display_text(controller_note) or controller_note
                else:
                    blockers = [
                        _watch_blocker_label(item)
                        for item in (publication_gate.get("blockers") or [])
                    ]
                    blockers = [item for item in blockers if item]
                    if blockers:
                        watch_summary = blockers[0]
            item = _event(
                timestamp=_non_empty_text(runtime_watch_payload.get("scanned_at")),
                category="runtime_watch",
                title="运行时巡检完成",
                summary=watch_summary,
                source="runtime_watch",
                artifact_path=runtime_watch_path,
            )
            if item is not None:
                events.append(item)
    if runtime_escalation_payload is not None:
        summary = _reason_label(runtime_escalation_payload.get("reason")) or "运行时已把问题升级回控制面。"
        item = _event(
            timestamp=_non_empty_text(runtime_escalation_payload.get("emitted_at")),
            category="runtime_escalation",
            title="运行时发出升级信号",
            summary=summary,
            source="runtime_escalation",
            artifact_path=runtime_escalation_path,
        )
        if item is not None:
            events.append(item)
    if launch_report_payload is not None:
        decision = (
            _runtime_decision_label(launch_report_payload.get("decision"))
            or _humanize_token(launch_report_payload.get("decision"))
            or "状态回写"
        )
        reason = _reason_label(launch_report_payload.get("reason"))
        summary = f"最近一次运行状态回写结论：{decision}。"
        if reason is not None:
            summary += f" {reason}"
        if not _publication_supervisor_state_conflicts(
            current=publication_supervisor_state,
            candidate=(
                launch_report_payload.get("publication_supervisor_state")
                if isinstance(launch_report_payload.get("publication_supervisor_state"), dict)
                else None
            ),
        ):
            item = _event(
                timestamp=_non_empty_text(launch_report_payload.get("recorded_at")),
                category="launch_report",
                title="研究运行状态回写",
                summary=summary,
                source="launch_report",
                artifact_path=launch_report_path,
            )
            if item is not None:
                events.append(item)
    events.sort(key=lambda item: item["timestamp"], reverse=True)
    # “最近进展”优先展示具体推进，再展示轮询/状态回写类摘要。
    events.sort(key=lambda item: _latest_event_display_tier(item.get("category")))
    return events[:_DEFAULT_EVENT_LIMIT]
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
