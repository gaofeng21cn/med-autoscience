from __future__ import annotations

from . import shared as _shared

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)

def _publication_eval_route_repair(publication_eval_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    actions = (publication_eval_payload or {}).get("recommended_actions") or []
    candidates: list[tuple[int, int, dict[str, Any]]] = []
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        action_type = _non_empty_text(action.get("action_type"))
        if action_type not in _ROUTE_REPAIR_ACTION_TYPES:
            continue
        route_target = _non_empty_text(action.get("route_target"))
        route_key_question = _non_empty_text(action.get("route_key_question"))
        route_rationale = _non_empty_text(action.get("route_rationale"))
        if route_target is None or route_key_question is None or route_rationale is None:
            continue
        route_label = _paper_stage_label(route_target) or route_target
        repair_mode = _route_repair_mode(action_type)
        priority = _non_empty_text(action.get("priority")) or "next"
        candidate = {
            "action_id": _non_empty_text(action.get("action_id")),
            "action_type": action_type,
            "priority": priority,
            "repair_mode": repair_mode,
            "repair_mode_label": _ROUTE_REPAIR_MODE_LABELS.get(repair_mode),
            "route_target": route_target,
            "route_target_label": route_label,
            "route_key_question": route_key_question,
            "route_rationale": route_rationale,
        }
        route_summary = _route_repair_summary(candidate)
        if route_summary is not None:
            candidate["route_summary"] = route_summary
        candidates.append((0 if priority == "now" else 1, index, candidate))
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def _decision_type_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _DECISION_TYPE_LABELS.get(text, _humanize_token(text))


def _controller_action_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _CONTROLLER_ACTION_LABELS.get(text, _humanize_token(text))


def _reason_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _REASON_LABELS.get(text, _humanize_token(text))


def _runtime_decision_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _RUNTIME_DECISION_LABELS.get(text, _humanize_token(text))


def _manual_finish_active(manual_finish_contract: dict[str, Any] | None) -> bool:
    return bool((manual_finish_contract or {}).get("compatibility_guard_only"))


def _manual_finish_runtime_decision_summary(manual_finish_contract: dict[str, Any] | None) -> str:
    del manual_finish_contract
    return "兼容性监督中"


def _manual_finish_runtime_reason_summary(manual_finish_contract: dict[str, Any] | None) -> str:
    summary = _non_empty_text((manual_finish_contract or {}).get("summary"))
    if summary is not None:
        return _display_text(summary) or summary
    return "当前 study 已转入人工收尾；MAS 只保持兼容性与监督入口。"


def _runtime_health_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _RUNTIME_HEALTH_LABELS.get(text, _humanize_token(text))


def _supervisor_tick_status_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _SUPERVISOR_TICK_STATUS_LABELS.get(text, _humanize_token(text))


def _continuation_reason_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.startswith("decision:"):
        return "运行停在待处理的决策节点"
    if text.startswith("latest_user_requirement:"):
        return "最新用户要求已接管当前优先级"
    return _CONTINUATION_REASON_LABELS.get(text, _humanize_token(text))


def _action_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _ACTION_LABELS.get(text, _humanize_token(text))


def _watch_blocker_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return _WATCH_BLOCKER_LABELS.get(text, _humanize_token(text))


def _blocker_label(value: object) -> str | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    normalized = text.replace(" ", "_")
    direct_label = _BLOCKER_LABELS.get(text) or _BLOCKER_LABELS.get(normalized)
    if direct_label is not None:
        return direct_label
    watch_label = _WATCH_BLOCKER_LABELS.get(text) or _WATCH_BLOCKER_LABELS.get(normalized)
    if watch_label is not None:
        return watch_label
    reason_label = _REASON_LABELS.get(text) or _REASON_LABELS.get(normalized)
    if reason_label is not None:
        return reason_label
    return _display_text(text) or _humanize_token(text)


def _humanized_blockers(items: list[str]) -> list[str]:
    blockers: list[str] = []
    for item in items:
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    return blockers


def _append_unique(items: list[str], message: str | None) -> None:
    if not message:
        return
    if message not in items:
        items.append(message)


def _publication_eval_gap_is_blocking(gap: dict[str, Any]) -> bool:
    summary = _non_empty_text(gap.get("summary"))
    if summary is None:
        return False
    severity = _non_empty_text(gap.get("severity"))
    if severity in {"optional", "advisory", "watch", "info", "informational"}:
        return False
    return True


def _publication_supervisor_state_marker(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    supervisor_phase = _non_empty_text(payload.get("supervisor_phase"))
    if supervisor_phase is None:
        return None
    return {
        "supervisor_phase": supervisor_phase,
        "bundle_tasks_downstream_only": bool(payload.get("bundle_tasks_downstream_only")),
        "current_required_action": _non_empty_text(payload.get("current_required_action")),
    }


def _publication_supervisor_state_conflicts(
    *,
    current: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> bool:
    current_marker = _publication_supervisor_state_marker(current)
    candidate_marker = _publication_supervisor_state_marker(candidate)
    if current_marker is None or candidate_marker is None:
        return False
    return any(candidate_marker[key] != current_marker[key] for key in current_marker)


def _latest_runtime_watch_report(quest_root: Path | None) -> Path | None:
    if quest_root is None:
        return None
    report_root = quest_root / "artifacts" / "reports" / "runtime_watch"
    if not report_root.exists():
        return None
    latest_path = report_root / "latest.json"
    if latest_path.exists():
        return latest_path
    candidates = [
        path
        for path in report_root.glob("*.json")
        if path.name not in {"state.json", "latest.json"}
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.stat().st_mtime)


def _details_projection_payload(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    wrapper = _read_json_object(path)
    if wrapper is None:
        return None
    payload = wrapper.get("payload")
    if not isinstance(payload, dict):
        return None
    return payload


def _runtime_module_surface(
    *,
    generated_at: str,
    study_id: str,
    quest_id: str | None,
    study_root: Path,
    launch_report_path: Path,
    runtime_supervision_path: Path,
    runtime_supervision_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    runtime_watch_path: Path | None,
    recovery_contract: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    publication_supervisor_state: dict[str, Any],
    current_stage: str,
    current_stage_summary: str,
    next_system_action: str,
    needs_physician_decision: bool,
    status: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    auto_runtime_parked: dict[str, Any] | None,
) -> dict[str, Any]:
    manual_finish_active = _manual_finish_active(manual_finish_contract)
    runtime_parked = bool((auto_runtime_parked or {}).get("parked"))
    runtime_health_status = (
        _non_empty_text(status.get("runtime_liveness_status")) or "none"
        if manual_finish_active or runtime_parked
        else _non_empty_text((runtime_supervision_payload or {}).get("health_status")) or "unknown"
    )
    current_required_action = (
        _non_empty_text(publication_supervisor_state.get("current_required_action"))
        if manual_finish_active or runtime_parked
        else (
            _non_empty_text(execution_owner_guard.get("current_required_action"))
            or _non_empty_text((runtime_supervision_payload or {}).get("next_action"))
        )
    )
    status_summary = (
        current_stage_summary
        if manual_finish_active or runtime_parked
        else (
            _display_text((runtime_supervision_payload or {}).get("summary"))
            or current_stage_summary
            or next_system_action
        )
    )
    next_action_summary = (
        next_system_action
        if manual_finish_active or runtime_parked
        else (
            _display_text((runtime_supervision_payload or {}).get("next_action_summary"))
            or next_system_action
            or current_stage_summary
        )
    )
    summary = build_runtime_status_summary(
        study_id=study_id,
        quest_id=quest_id,
        generated_at=generated_at,
        runtime_status_ref=(
            str(runtime_supervision_path.resolve())
            if runtime_supervision_payload is not None
            else str(launch_report_path.resolve())
        ),
        runtime_artifact_ref=str(launch_report_path.resolve()),
        runtime_escalation_record_ref=(
            str(runtime_escalation_path.resolve()) if runtime_escalation_path is not None else None
        ),
        runtime_watch_ref=str(runtime_watch_path.resolve()) if runtime_watch_path is not None else None,
        health_status=runtime_health_status,
        runtime_decision=_non_empty_text(status.get("decision")) or "noop",
        runtime_reason=_non_empty_text(status.get("reason")),
        recovery_action_mode=_non_empty_text(recovery_contract.get("action_mode")) or "monitor_only",
        supervisor_tick_status=_non_empty_text(supervisor_tick_audit.get("status")),
        current_required_action=current_required_action,
        controller_stage_note=(
            _non_empty_text(execution_owner_guard.get("controller_stage_note"))
            or _non_empty_text(publication_supervisor_state.get("controller_stage_note"))
        ),
        status_summary=status_summary,
        next_action_summary=next_action_summary,
        needs_human_intervention=(
            bool((runtime_supervision_payload or {}).get("needs_human_intervention")) or needs_physician_decision
        ),
    )
    summary_ref = materialize_runtime_status_summary(study_root=study_root, summary=summary)
    return {
        "module": "runtime",
        "surface_kind": "runtime_module_surface",
        "summary_id": summary_ref["summary_id"],
        "summary_ref": summary_ref["artifact_path"],
        "runtime_status_ref": summary["runtime_status_ref"],
        "runtime_artifact_ref": summary["runtime_artifact_ref"],
        "runtime_escalation_record_ref": summary["runtime_escalation_record_ref"],
        "runtime_watch_ref": summary["runtime_watch_ref"],
        "health_status": summary["health_status"],
        "runtime_decision": summary["runtime_decision"],
        "runtime_reason": summary["runtime_reason"],
        "recovery_action_mode": summary["recovery_action_mode"],
        "status_summary": summary["status_summary"],
        "next_action_summary": summary["next_action_summary"],
        "needs_human_intervention": summary["needs_human_intervention"],
        "auto_runtime_parked": dict(auto_runtime_parked or {}) or None,
    }


def _publishability_gate_report_path(
    *,
    runtime_watch_payload: dict[str, Any] | None,
    quest_root: Path | None,
) -> Path | None:
    publication_gate = (
        dict((((runtime_watch_payload or {}).get("controllers") or {}).get("publication_gate") or {}))
        if isinstance(((runtime_watch_payload or {}).get("controllers") or {}).get("publication_gate"), dict)
        else {}
    )
    report_json = _non_empty_text(publication_gate.get("report_json"))
    runtime_watch_candidate: Path | None = None
    if report_json is not None:
        candidate = Path(report_json).expanduser()
        if candidate.is_absolute():
            runtime_watch_candidate = candidate.resolve()
        elif quest_root is not None:
            runtime_watch_candidate = (quest_root / candidate).resolve()
    latest_candidate = None
    if quest_root is not None:
        candidate = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        if candidate.exists():
            latest_candidate = candidate.resolve()
    if runtime_watch_candidate is None:
        return latest_candidate
    if latest_candidate is None:
        return runtime_watch_candidate
    if not runtime_watch_candidate.exists():
        return latest_candidate
    if latest_candidate.stat().st_mtime >= runtime_watch_candidate.stat().st_mtime:
        return latest_candidate
    return runtime_watch_candidate


def _refresh_publication_surfaces_from_gate_report(
    *,
    study_root: Path,
    study_id: str,
    quest_root: Path | None,
    quest_id: str | None,
    publication_eval_path: Path,
    runtime_escalation_path: Path | None,
    runtime_watch_payload: dict[str, Any] | None,
) -> tuple[dict[str, Any] | None, Path | None, dict[str, Any] | None]:
    publishability_gate_path = _publishability_gate_report_path(
        runtime_watch_payload=runtime_watch_payload,
        quest_root=quest_root,
    )
    publishability_gate_payload = (
        _read_json_object(publishability_gate_path)
        if publishability_gate_path is not None
        else None
    )
    publication_eval_payload = _read_json_object(publication_eval_path)
    gate_generated_at = _non_empty_text((publishability_gate_payload or {}).get("generated_at"))
    eval_emitted_at = _non_empty_text((publication_eval_payload or {}).get("emitted_at"))
    if (
        publishability_gate_path is not None
        and publishability_gate_payload is not None
        and quest_root is not None
        and _non_empty_text(publishability_gate_payload.get("gate_kind")) == "publishability_control"
        and (
            _timestamp_is_newer(gate_generated_at, eval_emitted_at)
            or _publication_eval_semantically_stale_against_gate(
                publication_eval_payload=publication_eval_payload,
                publishability_gate_payload=publishability_gate_payload,
            )
        )
    ):
        try:
            decision_module = import_module("med_autoscience.controllers.study_runtime_decision")
            decision_module._materialize_publication_eval_from_gate_report(
                study_root=study_root,
                study_id=study_id,
                quest_root=quest_root,
                quest_id=quest_id,
                publication_gate_report=publishability_gate_payload,
            )
            publication_eval_payload = _read_json_object(publication_eval_path)
        except (AttributeError, ImportError, OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    refreshed_eval_emitted_at = _non_empty_text((publication_eval_payload or {}).get("emitted_at"))
    evaluation_summary_path = stable_evaluation_summary_path(study_root=study_root)
    evaluation_summary_payload = _read_json_object(evaluation_summary_path)
    evaluation_summary_emitted_at = _non_empty_text((evaluation_summary_payload or {}).get("emitted_at"))
    if (
        publication_eval_payload is not None
        and publishability_gate_path is not None
        and runtime_escalation_path is not None
        and runtime_escalation_path.exists()
        and refreshed_eval_emitted_at is not None
        and refreshed_eval_emitted_at != evaluation_summary_emitted_at
    ):
        try:
            materialize_evaluation_summary_artifacts(
                study_root=study_root,
                runtime_escalation_ref=runtime_escalation_path,
                publishability_gate_report_ref=publishability_gate_path,
            )
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return publication_eval_payload, publishability_gate_path, publishability_gate_payload


def _controller_module_surface(*, study_root: Path) -> dict[str, Any] | None:
    summary_path = stable_controller_summary_path(study_root=study_root)
    if not summary_path.exists():
        return None
    summary = read_controller_summary(study_root=study_root, ref=summary_path)
    confirmation_summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    confirmation_summary = (
        read_controller_confirmation_summary(study_root=study_root, ref=confirmation_summary_path)
        if confirmation_summary_path.exists()
        else None
    )
    controller_policy = dict(summary.get("controller_policy") or {})
    route_trigger_authority = dict(summary.get("route_trigger_authority") or {})
    decision_policy = _non_empty_text(route_trigger_authority.get("decision_policy")) or "unknown"
    launch_profile = _non_empty_text(route_trigger_authority.get("launch_profile")) or "unknown"
    required_first_anchor = _non_empty_text(controller_policy.get("required_first_anchor"))
    human_confirmation_surface = (
        {
            "gate_id": confirmation_summary["gate_id"],
            "status": confirmation_summary["status"],
            "requested_at": confirmation_summary["requested_at"],
            "question_for_user": confirmation_summary["question_for_user"],
            "allowed_responses": list(confirmation_summary.get("allowed_responses") or []),
            "next_action_if_approved": confirmation_summary["next_action_if_approved"],
            "summary_ref": str(confirmation_summary_path),
        }
        if confirmation_summary is not None
        else None
    )
    status_summary = (
        "研究合同已冻结；当前控制面决策等待用户确认。"
        if human_confirmation_surface is not None
        else f"研究合同已冻结；决策策略 {decision_policy}，启动入口 {launch_profile}。"
    )
    next_action_summary = (
        f"{human_confirmation_surface['question_for_user']} 确认后系统将{human_confirmation_surface['next_action_if_approved']}。"
        if human_confirmation_surface is not None
        else (
            f"从 {required_first_anchor} 锚点继续推进当前研究。"
            if required_first_anchor
            else "沿 controller contract 继续推进当前研究。"
        )
    )
    return {
        "module": "controller_charter",
        "surface_kind": "controller_module_surface",
        "summary_id": summary["summary_id"],
        "summary_ref": str(summary_path),
        "study_charter_ref": dict(summary.get("study_charter_ref") or {}),
        "decision_policy": decision_policy,
        "launch_profile": launch_profile,
        "status_summary": status_summary,
        "next_action_summary": next_action_summary,
        "human_confirmation": human_confirmation_surface,
    }


def _evaluation_module_surface(
    *,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    runtime_watch_payload: dict[str, Any] | None,
    quest_root: Path | None,
) -> dict[str, Any] | None:
    evaluation_summary_path = stable_evaluation_summary_path(study_root=study_root)
    promotion_gate_path = stable_promotion_gate_path(study_root=study_root)
    if not evaluation_summary_path.exists():
        gate_report_path = _publishability_gate_report_path(
            runtime_watch_payload=runtime_watch_payload,
            quest_root=quest_root,
        )
        charter_path = stable_study_charter_path(study_root=study_root)
        if (
            publication_eval_payload is None
            or runtime_escalation_path is None
            or not runtime_escalation_path.exists()
            or gate_report_path is None
            or not gate_report_path.exists()
            or not charter_path.exists()
        ):
            return None
        materialize_evaluation_summary_artifacts(
            study_root=study_root,
            runtime_escalation_ref=runtime_escalation_path,
            publishability_gate_report_ref=gate_report_path,
        )
    if not evaluation_summary_path.exists():
        return None
    read_evaluation_summary_fn = _controller_override("read_evaluation_summary", read_evaluation_summary)
    summary = read_evaluation_summary_fn(study_root=study_root, ref=evaluation_summary_path)
    promotion_gate_status = _mapping_copy(summary.get("promotion_gate_status"))
    quality_closure_truth = _mapping_copy(summary.get("quality_closure_truth"))
    quality_execution_lane = _mapping_copy(summary.get("quality_execution_lane"))
    same_line_route_truth = _mapping_copy(summary.get("same_line_route_truth"))
    same_line_route_surface = _mapping_copy(summary.get("same_line_route_surface"))
    quality_closure_basis = _mapping_copy(summary.get("quality_closure_basis"))
    quality_review_agenda = _mapping_copy(summary.get("quality_review_agenda"))
    quality_revision_plan = _mapping_copy(summary.get("quality_revision_plan"))
    quality_review_loop = _mapping_copy(summary.get("quality_review_loop"))
    current_required_action = _non_empty_text(promotion_gate_status.get("current_required_action"))
    plan_items = [
        dict(item)
        for item in (quality_revision_plan.get("items") or [])
        if isinstance(item, dict)
    ]
    plan_next_action = (
        _display_text((plan_items[0] or {}).get("action")) if plan_items else None
    ) or (_non_empty_text((plan_items[0] or {}).get("action")) if plan_items else None)
    review_loop_next_action = _display_text(quality_review_loop.get("recommended_next_action")) or _non_empty_text(
        quality_review_loop.get("recommended_next_action")
    )
    next_action_summary = (
        review_loop_next_action
        or plan_next_action
        or (
        _display_text(quality_review_agenda.get("suggested_revision"))
        or _non_empty_text(quality_review_agenda.get("suggested_revision"))
        or _ACTION_LABELS.get(current_required_action or "", "")
        or current_required_action
        or "按当前 eval hygiene 结论继续推进。"
        )
    )
    return {
        "module": "eval_hygiene",
        "surface_kind": "evaluation_module_surface",
        "summary_id": summary["summary_id"],
        "summary_ref": str(evaluation_summary_path),
        "promotion_gate_ref": str(promotion_gate_path) if promotion_gate_path.exists() else None,
        "overall_verdict": summary["overall_verdict"],
        "primary_claim_status": summary["primary_claim_status"],
        "stop_loss_pressure": summary["stop_loss_pressure"],
        "requires_controller_decision": bool(summary.get("requires_controller_decision")),
        "status_summary": summary["verdict_summary"],
        "next_action_summary": next_action_summary,
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_closure_basis": quality_closure_basis or None,
        "quality_review_agenda": quality_review_agenda or None,
        "quality_revision_plan": quality_revision_plan or None,
        "quality_review_loop": quality_review_loop or None,
    }


def _quality_review_followthrough_projection(
    *,
    quality_review_loop: Mapping[str, Any],
    needs_physician_decision: bool,
    interaction_arbitration: Mapping[str, Any],
    runtime_decision: str | None,
    quest_status: str | None,
    current_blockers: list[str],
    next_system_action: str,
) -> dict[str, Any] | None:
    if not quality_review_loop:
        return None
    waiting_auto_re_review = bool(quality_review_loop.get("re_review_ready")) or _non_empty_text(
        quality_review_loop.get("current_phase")
    ) == "re_review_required"
    if not waiting_auto_re_review:
        return {
            "surface_kind": "quality_review_followthrough",
            "state": "not_in_re_review_waiting",
            "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["not_in_re_review_waiting"],
            "waiting_auto_re_review": False,
            "auto_continue_expected": False,
            "summary": "当前质量闭环不在自动复评等待态，系统会按现有修订线继续推进。",
            "blocking_reason": None,
            "next_confirmation_signal": "看下一次质量评审结论是否继续收窄当前修订线。",
            "user_intervention_required_now": False,
        }

    requires_user_input = needs_physician_decision or bool(interaction_arbitration.get("requires_user_input"))
    runtime_active = quest_status in {"running", "active", "waiting_for_user"}
    runtime_recovery_requested = runtime_decision in {"create_and_start", "resume", "relaunch_stopped"}
    runtime_blocks_auto = runtime_decision in {"blocked", "completed", "create_only"}
    auto_continue_expected = (runtime_active or runtime_recovery_requested) and not runtime_blocks_auto and not requires_user_input
    if auto_continue_expected:
        return {
            "surface_kind": "quality_review_followthrough",
            "state": "auto_re_review_pending",
            "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["auto_re_review_pending"],
            "waiting_auto_re_review": True,
            "auto_continue_expected": True,
            "summary": "当前在等系统自动发起下一轮复评，主线会自动继续。",
            "blocking_reason": None,
            "next_confirmation_signal": "看 publication_eval/latest.json 是否出现新的复评结论，或 blocking issues 是否继续收窄。",
            "user_intervention_required_now": False,
        }

    if requires_user_input:
        blocking_reason = "当前需要用户先确认下一步，系统不会直接自动复评。"
    elif runtime_decision == "blocked":
        blocking_reason = "当前运行被控制面阻断，需先解除阻断后才会继续复评。"
    elif quest_status in {"stopped", "failed", "completed"}:
        blocking_reason = "当前运行不在自动推进状态，需要先恢复运行后才会继续复评。"
    else:
        blocking_reason = _non_empty_text(current_blockers[0] if current_blockers else None) or next_system_action
    return {
        "surface_kind": "quality_review_followthrough",
        "state": "auto_re_review_blocked",
        "state_label": _QUALITY_REVIEW_FOLLOWTHROUGH_STATE_LABELS["auto_re_review_blocked"],
        "waiting_auto_re_review": True,
        "auto_continue_expected": False,
        "summary": "当前停在等待复评，系统暂时不会自动继续。",
        "blocking_reason": blocking_reason,
        "next_confirmation_signal": "先解除当前卡点，再看 publication_eval/latest.json 是否出现新的复评结论。",
        "user_intervention_required_now": True,
    }


def _apply_quality_review_followthrough_to_operator_status(
    *,
    operator_status_card: Mapping[str, Any],
    followthrough: Mapping[str, Any] | None,
) -> dict[str, Any]:
    card = dict(operator_status_card or {})
    follow = dict(followthrough or {})
    if not card or not follow or not bool(follow.get("waiting_auto_re_review")):
        return card
    card["quality_review_followthrough"] = follow
    card["current_focus"] = _non_empty_text(follow.get("summary")) or card.get("current_focus")
    next_signal = _non_empty_text(follow.get("next_confirmation_signal"))
    if next_signal is not None:
        card["next_confirmation_signal"] = next_signal
    intervention_required = bool(follow.get("user_intervention_required_now"))
    card["user_intervention_required_now"] = intervention_required
    if intervention_required:
        card["user_visible_verdict"] = "当前停在等待复评，系统不会自动继续；你现在需要先处理卡点。"
    else:
        card["user_visible_verdict"] = "当前在等系统自动复评；你现在不用介入，先等待复评回写。"
    return card


def _gate_clearing_batch_followthrough(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    record_path = gate_clearing_batch.stable_gate_clearing_batch_path(study_root=study_root)
    record = _read_json_object(record_path)
    if record is None:
        return None
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    source_eval_id = _non_empty_text(record.get("source_eval_id"))
    if current_eval_id is None or source_eval_id is None or current_eval_id != source_eval_id:
        return None
    unit_results = [
        dict(item)
        for item in (record.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    failed_units = [item for item in unit_results if _non_empty_text(item.get("status")) == "failed"]
    gate_replay = dict(record.get("gate_replay") or {})
    gate_replay_status = _non_empty_text(gate_replay.get("status")) or "unknown"
    if failed_units:
        summary = "最近一轮 gate-clearing batch 已执行，但仍有修复单元失败，当前不能继续自动前推。"
        next_confirmation_signal = "先修掉失败 repair unit，再看 publication_eval/latest.json 是否进入新的复评或放行结论。"
        user_intervention_required_now = True
    elif gate_replay_status == "clear":
        summary = "最近一轮 gate-clearing batch 已执行，并已把发表门控回放到放行状态。"
        next_confirmation_signal = "看 publication_eval/latest.json 是否刷新为新的放行结论，并确认当前 study 已进入下一阶段。"
        user_intervention_required_now = False
    else:
        blockers = [
            _non_empty_text(item)
            for item in (gate_replay.get("blockers") or [])
            if _non_empty_text(item) is not None
        ]
        blocker_summary = f"当前仍剩 {len(blockers)} 个 gate blocker。" if blockers else "当前 gate replay 仍未完全收口。"
        summary = f"最近一轮 gate-clearing batch 已执行；{blocker_summary}"
        next_confirmation_signal = "看 publication_eval/latest.json 或最新 gate replay 是否继续收窄 blocker。"
        user_intervention_required_now = False
    return {
        "surface_kind": "gate_clearing_batch_followthrough",
        "status": _non_empty_text(record.get("status")) or "executed",
        "summary": summary,
        "gate_replay_status": gate_replay_status,
        "blocking_issue_count": len(gate_replay.get("blockers") or []),
        "failed_unit_count": len(failed_units),
        "next_confirmation_signal": next_confirmation_signal,
        "user_intervention_required_now": user_intervention_required_now,
        "latest_record_path": str(record_path),
    }


def _quality_repair_batch_followthrough(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any] | None,
    recommended_command: str | None,
) -> dict[str, Any] | None:
    record_path = quality_repair_batch.stable_quality_repair_batch_path(study_root=study_root)
    record = _read_json_object(record_path)
    if record is None:
        return None
    current_eval_id = _non_empty_text((publication_eval_payload or {}).get("eval_id"))
    source_eval_id = _non_empty_text(record.get("source_eval_id"))
    if current_eval_id is None or source_eval_id is None or current_eval_id != source_eval_id:
        return None
    gate_batch = dict(record.get("gate_clearing_batch") or {})
    unit_results = [
        dict(item)
        for item in (gate_batch.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    failed_units = [item for item in unit_results if _non_empty_text(item.get("status")) == "failed"]
    gate_replay = dict(gate_batch.get("gate_replay") or {})
    gate_replay_status = _non_empty_text(gate_replay.get("status")) or "unknown"
    if failed_units:
        summary = "最近一轮 quality-repair batch 已执行，但仍有修复单元失败，当前不能继续自动前推。"
        next_confirmation_signal = "先修掉失败 repair unit，再看 publication_eval/latest.json 是否进入新的复评或放行结论。"
        user_intervention_required_now = True
    elif gate_replay_status == "clear":
        summary = "最近一轮 quality-repair batch 已执行，并已把 quality gate replay 到放行状态。"
        next_confirmation_signal = "看 publication_eval/latest.json 是否刷新为新的放行结论，并确认当前 study 已进入下一阶段。"
        user_intervention_required_now = False
    else:
        blockers = [
            _non_empty_text(item)
            for item in (gate_replay.get("blockers") or [])
            if _non_empty_text(item) is not None
        ]
        blocker_summary = f"当前 gate replay 仍剩 {len(blockers)} 个 blocker。" if blockers else "当前 quality gate replay 仍未完全收口。"
        summary = f"最近一轮 quality-repair batch 已执行；{blocker_summary}"
        next_confirmation_signal = "看 publication_eval/latest.json 或最新 quality gate replay 是否继续收窄 blocker。"
        user_intervention_required_now = False
    payload = {
        "surface_kind": "quality_repair_batch_followthrough",
        "status": _non_empty_text(record.get("status")) or "executed",
        "quality_closure_state": _non_empty_text(record.get("quality_closure_state")),
        "quality_execution_lane_id": _non_empty_text(record.get("quality_execution_lane_id")),
        "summary": summary,
        "gate_replay_status": gate_replay_status,
        "blocking_issue_count": len(gate_replay.get("blockers") or []),
        "failed_unit_count": len(failed_units),
        "next_confirmation_signal": next_confirmation_signal,
        "user_intervention_required_now": user_intervention_required_now,
        "latest_record_path": str(record_path),
    }
    if recommended_command is not None:
        payload["recommended_step_id"] = "run_quality_repair_batch"
        payload["recommended_command"] = recommended_command
    return payload
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
