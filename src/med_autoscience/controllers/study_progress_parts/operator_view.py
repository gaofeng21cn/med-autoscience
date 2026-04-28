from __future__ import annotations

from .operator_status_card import _operator_status_card
from .parked_operator import is_user_decision_lane, parked_recovery_steps
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
    elif is_user_decision_lane(lane_id):
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
    elif lane_id == "auto_runtime_parked":
        steps = parked_recovery_steps(commands)
        action_mode = "auto_runtime_parked"
    elif lane_id in {"manual_finishing", "manual_finishing_fast_lane"}:
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
        action_mode = (
            "run_manuscript_fast_lane"
            if lane_id == "manual_finishing_fast_lane"
            else "maintain_compatibility_guard"
        )
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
    auto_runtime_parked: dict[str, Any] | None,
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
    if bool((auto_runtime_parked or {}).get("parked")):
        autonomy_state = "auto_runtime_parked"
    elif _manual_finish_active(manual_finish_contract):
        autonomy_state = "compatibility_guard"
    elif needs_physician_decision:
        autonomy_state = "human_gate"
    elif lane_id in {"workspace_supervision_gap", "runtime_recovery_required", "runtime_blocker"}:
        autonomy_state = "runtime_recovery"
    else:
        autonomy_state = "autonomous_progress"
    if autonomy_state == "auto_runtime_parked":
        summary = _non_empty_text((auto_runtime_parked or {}).get("summary")) or current_stage_summary
    elif autonomy_state == "autonomous_progress" and latest_outer_loop_dispatch is not None:
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
    parked_projection = dict(auto_runtime_parked or {}) if isinstance(auto_runtime_parked, dict) else {}
    surfaced_parked_projection = (
        parked_projection
        if bool(parked_projection.get("parked")) or bool(parked_projection.get("superseded_by_task_intake"))
        else None
    )
    payload = {
        "contract_kind": "study_autonomy_contract",
        "autonomy_state": autonomy_state,
        "summary": summary,
        "recommended_command": recommended_command,
        "next_signal": next_system_action or str(restore_point.get("summary") or "").strip(),
        "restore_point": restore_point,
        "latest_outer_loop_dispatch": latest_outer_loop_dispatch,
    }
    if surfaced_parked_projection is not None:
        payload["auto_runtime_parked"] = surfaced_parked_projection
    return payload


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
            "approval_gate_field": "needs_user_decision",
            "legacy_approval_gate_field": "needs_physician_decision",
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
    elif is_user_decision_lane(lane_id):
        decision_mode = "human_decision_required"
    elif lane_id == "auto_runtime_parked":
        decision_mode = "auto_runtime_parked"
    elif lane_id in {"manual_finishing", "manual_finishing_fast_lane"}:
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
