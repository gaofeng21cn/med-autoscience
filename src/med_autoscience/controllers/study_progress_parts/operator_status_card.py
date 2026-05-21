from __future__ import annotations

from typing import Any

from .parked_operator import (
    is_parked_handling_state,
    is_user_decision_lane,
    parked_focus_summary,
    parked_human_surface_summary,
    parked_owner_summary,
    parked_status_verdict,
    parked_truth_candidates,
)
from .shared import *  # noqa: F403
from .publication_runtime import *  # noqa: F403

def _operator_status_handling_state(
    *,
    current_stage: str,
    intervention_lane: dict[str, Any],
    needs_physician_decision: bool,
    current_blockers: list[str],
    manual_finish_contract: dict[str, Any] | None,
    auto_runtime_parked: dict[str, Any] | None,
) -> str:
    lane_id = _non_empty_text((intervention_lane or {}).get("lane_id")) or "monitor_only"
    activity_timeout = (intervention_lane or {}).get("activity_timeout")
    runtime_unhealthy_stage = current_stage in {
        "managed_runtime_recovering",
        "managed_runtime_degraded",
        "managed_runtime_escalated",
        "runtime_blocked",
    }
    if lane_id == "runtime_recovery_required" and isinstance(activity_timeout, dict):
        if _non_empty_text(activity_timeout.get("state")) == "timed_out":
            return "runtime_recovering"
    if bool((auto_runtime_parked or {}).get("parked")):
        return _non_empty_text((auto_runtime_parked or {}).get("parked_state")) or "auto_runtime_parked"
    if lane_id == "workspace_supervision_gap":
        return "runtime_supervision_recovering"
    if lane_id == "publication_gate_specificity_required":
        return "publication_gate_specificity_required"
    if lane_id == "completion_evidence_required":
        return "completion_evidence_required"
    if needs_physician_decision or is_user_decision_lane(lane_id):
        return "waiting_user_decision"
    if any(str(item or "").strip() in _HUMAN_SURFACE_REFRESH_BLOCKER_LABELS for item in current_blockers):
        return "paper_surface_refresh_in_progress"
    if current_stage == "managed_runtime_escalated":
        return "runtime_recovering"
    if lane_id == "quality_floor_blocker":
        return "scientific_or_quality_repair_in_progress"
    if current_stage in {"managed_runtime_recovering", "managed_runtime_degraded", "managed_runtime_escalated"}:
        return "runtime_recovering"
    if _manual_finish_active(manual_finish_contract):
        return "package_ready_handoff"
    if lane_id == "manual_finishing":
        return "package_ready_handoff"
    if lane_id in {"runtime_recovery_required", "runtime_blocker"} or runtime_unhealthy_stage:
        return "runtime_recovering"
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
        "publication_gate_specificity_required": (
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
            (latest_event_source, latest_event_time),
        ),
        "scientific_or_quality_repair_in_progress": (
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
            (latest_event_source, latest_event_time),
        ),
        "waiting_user_decision": (
            ("controller_confirmation", _non_empty_text((controller_confirmation_summary or {}).get("requested_at"))),
            ("controller_decision", _non_empty_text((controller_decision_payload or {}).get("emitted_at"))),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            (latest_event_source, latest_event_time),
        ),
        "monitor_only": (
            (latest_event_source, latest_event_time),
            ("publication_eval", _non_empty_text((publication_eval_payload or {}).get("emitted_at"))),
            ("runtime_watch", _non_empty_text((runtime_watch_payload or {}).get("scanned_at"))),
        ),
    }
    parked_candidates = parked_truth_candidates(
        handling_state,
        controller_decision_payload=controller_decision_payload,
        publication_eval_payload=publication_eval_payload,
        latest_event_source=latest_event_source,
        latest_event_time=latest_event_time,
    )
    if parked_candidates is not None:
        candidates_by_state[handling_state] = parked_candidates
    for source, timestamp in candidates_by_state.get(handling_state, ((latest_event_source, latest_event_time),)):
        if source is not None and timestamp is not None:
            return source, timestamp
    return None, None


def _operator_status_human_surface_summary(handling_state: str) -> tuple[str, str]:
    parked_summary = parked_human_surface_summary(handling_state)
    if parked_summary is not None:
        return parked_summary
    if handling_state == "paper_surface_refresh_in_progress":
        return "stale", "给人看的投稿包镜像仍落后于当前论文真相；没有 freshness proof 前不得视为投稿包可用。"
    if handling_state == "publication_gate_specificity_required":
        return "stale", "publication gate 还没有给出具体 blocker 对象；current_package 不能作为投稿可用包判断。"
    if handling_state == "completion_evidence_required":
        return "stale", "completed study 的 completion evidence 合同还未闭环；不能重开写作或 runtime repair。"
    if handling_state == "waiting_user_decision":
        return "pending_decision", "当前主要等待人工判断，给人看的稿件状态以论文门控为准。"
    if handling_state in {"runtime_supervision_recovering", "runtime_recovering"}:
        return "monitoring_runtime", "当前优先看结构化监管真相，给人看的稿件表面还不是主判断面。"
    return "current", "给人看的稿件表面当前没有额外刷新告警。"


def _operator_status_verdict(handling_state: str) -> str:
    parked_verdict = parked_status_verdict(handling_state)
    if parked_verdict is not None:
        return parked_verdict
    if handling_state == "runtime_supervision_recovering":
        return "MAS 正在恢复外环监管，当前 study 仍处在受管修复中。"
    if handling_state == "runtime_recovering":
        return "MAS 正在处理 runtime recovery，当前 study 仍处在受管修复中。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "MAS 正在刷新给人看的投稿包镜像，科学真相已经先行一步。"
    if handling_state == "publication_gate_specificity_required":
        return "MAS 已阻止普通分析/写作重跑，当前等待 publication gate 给出具体 blocker 对象。"
    if handling_state == "completion_evidence_required":
        return "MAS 已把 completed study 停在 completion evidence 补齐面，当前不应恢复自动写入。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在处理论文可发表性硬阻塞，给人看的稿件还没到放行状态。"
    if handling_state == "waiting_user_decision":
        return "MAS 已经把自动侧能做的部分推进完成，当前在等用户判断。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_owner_summary(handling_state: str) -> str:
    parked_summary = parked_owner_summary(handling_state)
    if parked_summary is not None:
        return parked_summary
    if handling_state == "runtime_supervision_recovering":
        return "MAS 正在恢复 workspace 级监管心跳，托管执行仍由 runtime 持有。"
    if handling_state == "runtime_recovering":
        return "MAS 正在根据 runtime supervision 真相继续处理恢复。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "MAS 正在根据 publication gate 真相刷新给人看的投稿包镜像。"
    if handling_state == "publication_gate_specificity_required":
        return "MAS 正在要求 publication gate 产出具体 claim、figure、table、metric 或 source path 后再派发修复。"
    if handling_state == "completion_evidence_required":
        return "MAS 正在等待交付/导出控制面补齐 study completion evidence。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在收口论文可发表性与质量硬阻塞。"
    if handling_state == "waiting_user_decision":
        return "MAS 已把下一步提升到用户决策面，并继续保持监管。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_focus_summary(
    *,
    handling_state: str,
    intervention_lane: dict[str, Any],
    next_system_action: str,
    current_stage_summary: str,
    no_op_suppression: dict[str, Any] | None,
) -> str:
    activity_timeout = (intervention_lane or {}).get("activity_timeout")
    if handling_state == "runtime_recovering" and isinstance(activity_timeout, dict):
        return (
            _non_empty_text(activity_timeout.get("summary"))
            or _non_empty_text((intervention_lane or {}).get("summary"))
            or "live worker 已超过 meaningful artifact delta 活动窗口，当前必须先恢复产物增量。"
        )
    if no_op_suppression is not None:
        return (
            _non_empty_text(no_op_suppression.get("operator_summary"))
            or "同一 blocker fingerprint 未变化；当前不建议继续空转。"
        )
    parked_summary = parked_focus_summary(
        handling_state,
        intervention_lane=intervention_lane,
        current_stage_summary=current_stage_summary,
    )
    if parked_summary is not None:
        return parked_summary
    if handling_state == "paper_surface_refresh_in_progress":
        return "优先把人类查看面同步到当前论文真相，再继续盯论文门控。"
    if handling_state == "publication_gate_specificity_required":
        return (
            _non_empty_text((intervention_lane or {}).get("summary"))
            or "等待 publication gate 写出具体 claim/figure/table/metric/source path；没有具体对象前不派普通 repair worker。"
        )
    if handling_state == "completion_evidence_required":
        return (
            _non_empty_text((intervention_lane or {}).get("summary"))
            or "study-level 完成声明已存在，但 final submission 证据还未补齐。"
        )
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
    if is_parked_handling_state(handling_state):
        return "看是否出现新的用户反馈、外部条件解除或显式 resume/rerun/relaunch。"
    if handling_state == "runtime_supervision_recovering":
        return "看 supervisor tick 是否回到 fresh，并确认监管缺口告警从 attention queue 消失。"
    if handling_state == "runtime_recovering":
        return "看 runtime_supervision/latest.json 的 health_status 回到 live，并确认 meaningful artifact delta 刷新。"
    if handling_state == "paper_surface_refresh_in_progress":
        return "看 artifacts/controller/current_package_freshness/latest.json 是否写出 fresh proof，再看 current_package 和 submission_minimal 是否同步到同一 authority signature。"
    if handling_state == "publication_gate_specificity_required":
        return "看 publication_eval/latest.json 是否写出具体 claim/figure/table/metric/source path；同时确认 current_package_freshness/latest.json 存在 fresh proof 后再判断投稿包可用。"
    if handling_state == "completion_evidence_required":
        return "看 study_completion.missing_evidence_paths 是否清空，并确认 quest 同步到 completed。"
    if handling_state == "scientific_or_quality_repair_in_progress":
        route_label = _non_empty_text((intervention_lane or {}).get("route_target_label"))
        key_question = _non_empty_text((intervention_lane or {}).get("route_key_question"))
        if route_label is not None and key_question is not None:
            return (
                f"看 publication_eval/latest.json 是否把“{route_label}”这条修复线继续收窄，"
                f"以及“{key_question}”是否已经被关闭。"
            )
        return "看 publication_eval/latest.json 或 runtime_watch 里的 blocker 是否减少。"
    if handling_state == "waiting_user_decision":
        return "看 controller_confirmation_summary 是否清空或变化，或 controller_decisions/latest.json 是否写出人工确认后的下一步。"
    if handling_state == "manual_finishing":
        return "看人工收尾是否写出新的明确结论，或兼容保护是否仍然保持 active。"
    return "看下一条 runtime progress / publication_eval 更新。"


def _latest_no_op_suppression(
    *,
    study_id: str,
    runtime_watch_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    candidates = [
        dict(item)
        for item in ((runtime_watch_payload or {}).get("managed_study_no_op_suppressions") or [])
        if isinstance(item, dict)
    ]
    for item in reversed(candidates):
        item_study_id = _non_empty_text(item.get("study_id"))
        if item_study_id is None or item_study_id == study_id:
            return item
    return None


def _runtime_efficiency_summary(
    runtime_efficiency: dict[str, Any] | None,
) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
    if not runtime_efficiency:
        return None, None, None
    evidence_packet_count = int(runtime_efficiency.get("evidence_packet_count") or 0)
    gate_cache_surfaces = [
        dict(item)
        for item in (runtime_efficiency.get("gate_cache_surfaces") or [])
        if isinstance(item, dict)
    ]
    metrics = {
        "tool_result_bytes_saved_total": int(runtime_efficiency.get("tool_result_bytes_saved_total") or 0),
        "unique_command_count": int(runtime_efficiency.get("unique_command_count") or 0),
        "read_tool_call_count": int(runtime_efficiency.get("read_tool_call_count") or 0),
        "repeated_read_result_count": int(runtime_efficiency.get("repeated_read_result_count") or 0),
        "repeated_read_ratio": float(runtime_efficiency.get("repeated_read_ratio") or 0.0),
        "gate_replay_hit_count": int(runtime_efficiency.get("gate_replay_hit_count") or 0),
        "latest_gate_replay_at": _non_empty_text(runtime_efficiency.get("latest_gate_replay_at")),
    }
    summary = (
        f"runtime efficiency: {evidence_packet_count} evidence packet sidecar item(s); "
        f"{len(gate_cache_surfaces)} gate cache surface(s); "
        f"unique commands {metrics['unique_command_count']}; "
        f"repeated reads {metrics['repeated_read_result_count']}/{metrics['read_tool_call_count']}; "
        f"saved bytes {metrics['tool_result_bytes_saved_total']}; "
        f"gate replay hits {metrics['gate_replay_hit_count']}."
    )
    refs = {
        "telemetry_path": _non_empty_text(runtime_efficiency.get("telemetry_path")),
        "evidence_packet_index_path": _non_empty_text(runtime_efficiency.get("evidence_packet_index_path")),
        "gate_replay_ref": _non_empty_text(runtime_efficiency.get("gate_replay_ref")),
        "gate_cache_surfaces": [
            {
                "surface_id": _non_empty_text(item.get("surface_id")),
                "path": _non_empty_text(item.get("path")),
                "input_fingerprint": _non_empty_text(item.get("input_fingerprint")),
            }
            for item in gate_cache_surfaces[:8]
        ],
    }
    return summary, refs, metrics


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
    auto_runtime_parked: dict[str, Any] | None,
    runtime_efficiency: dict[str, Any] | None = None,
) -> dict[str, Any]:
    handling_state = _operator_status_handling_state(
        current_stage=current_stage,
        intervention_lane=intervention_lane,
        needs_physician_decision=needs_physician_decision,
        current_blockers=current_blockers,
        manual_finish_contract=manual_finish_contract,
        auto_runtime_parked=auto_runtime_parked,
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
    no_op_suppression = _latest_no_op_suppression(
        study_id=study_id,
        runtime_watch_payload=runtime_watch_payload,
    )
    runtime_efficiency_summary, runtime_efficiency_refs, runtime_efficiency_metrics = _runtime_efficiency_summary(
        runtime_efficiency
    )
    payload = {
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
            no_op_suppression=no_op_suppression,
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
    if no_op_suppression is not None:
        payload["no_op_suppression"] = no_op_suppression
    if runtime_efficiency_summary is not None:
        payload["runtime_efficiency_summary"] = runtime_efficiency_summary
        payload["runtime_efficiency_refs"] = runtime_efficiency_refs
        payload["runtime_efficiency_metrics"] = runtime_efficiency_metrics
    if bool((auto_runtime_parked or {}).get("parked")):
        payload["auto_runtime_parked"] = dict(auto_runtime_parked or {})
        payload["parked_state"] = _non_empty_text((auto_runtime_parked or {}).get("parked_state"))
        payload["resource_release_expected"] = bool(
            (auto_runtime_parked or {}).get("resource_release_expected")
        )
        payload["awaiting_explicit_wakeup"] = bool(
            (auto_runtime_parked or {}).get("awaiting_explicit_wakeup")
        )
        payload["auto_execution_complete"] = bool((auto_runtime_parked or {}).get("auto_execution_complete"))
        payload["reopen_policy"] = _non_empty_text((auto_runtime_parked or {}).get("reopen_policy"))
    return payload


__all__ = ["_operator_status_card"]
