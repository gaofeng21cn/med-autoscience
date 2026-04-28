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
    if bool((auto_runtime_parked or {}).get("parked")):
        return _non_empty_text((auto_runtime_parked or {}).get("parked_state")) or "auto_runtime_parked"
    if _manual_finish_active(manual_finish_contract):
        return "manual_finishing"
    if lane_id == "manual_finishing":
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
    if needs_physician_decision or is_user_decision_lane(lane_id):
        return "waiting_user_decision"
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
        "waiting_user_decision": (
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
        return "stale", "给人看的投稿包镜像仍落后于当前论文真相。"
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
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在处理论文可发表性硬阻塞，给人看的稿件还没到放行状态。"
    if handling_state == "waiting_user_decision":
        return "MAS 已经把自动侧能做的部分推进完成，当前在等用户判断。"
    if handling_state == "manual_finishing":
        return "MAS 当前保持人工收尾兼容保护，并继续提供监督入口。"
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
    if handling_state == "scientific_or_quality_repair_in_progress":
        return "MAS 正在收口论文可发表性与质量硬阻塞。"
    if handling_state == "waiting_user_decision":
        return "MAS 已把下一步提升到用户决策面，并继续保持监管。"
    if handling_state == "manual_finishing":
        return "MAS 当前只保持人工收尾兼容保护和监督入口。"
    return "MAS 正在持续监管当前 study。"


def _operator_status_focus_summary(
    *,
    handling_state: str,
    intervention_lane: dict[str, Any],
    next_system_action: str,
    current_stage_summary: str,
    no_op_suppression: dict[str, Any] | None,
) -> str:
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


def _runtime_efficiency_summary(runtime_efficiency: dict[str, Any] | None) -> tuple[str | None, dict[str, Any] | None]:
    if not runtime_efficiency:
        return None, None
    evidence_packet_count = int(runtime_efficiency.get("evidence_packet_count") or 0)
    gate_cache_surfaces = [
        dict(item)
        for item in (runtime_efficiency.get("gate_cache_surfaces") or [])
        if isinstance(item, dict)
    ]
    summary = (
        f"runtime efficiency: {evidence_packet_count} evidence packet sidecar item(s); "
        f"{len(gate_cache_surfaces)} gate cache surface(s)."
    )
    refs = {
        "telemetry_path": _non_empty_text(runtime_efficiency.get("telemetry_path")),
        "evidence_packet_index_path": _non_empty_text(runtime_efficiency.get("evidence_packet_index_path")),
        "gate_cache_surfaces": [
            {
                "surface_id": _non_empty_text(item.get("surface_id")),
                "path": _non_empty_text(item.get("path")),
                "input_fingerprint": _non_empty_text(item.get("input_fingerprint")),
            }
            for item in gate_cache_surfaces[:8]
        ],
    }
    return summary, refs


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
    runtime_efficiency_summary, runtime_efficiency_refs = _runtime_efficiency_summary(runtime_efficiency)
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
