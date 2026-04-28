from __future__ import annotations

from collections.abc import Mapping
from typing import Any

PARKED_HANDLING_STATES = frozenset(
    {
        "package_ready_handoff",
        "external_metadata_pending",
        "waiting_user_decision",
        "external_input_pending",
        "external_upstream_pending",
        "explicit_resume_pending",
        "platform_repair_pending",
        "preflight_contract_pending",
    }
)
USER_DECISION_LANE_IDS = frozenset({"user_decision_gate", "human_decision_gate"})


def is_parked_handling_state(handling_state: str) -> bool:
    return handling_state in PARKED_HANDLING_STATES


def is_user_decision_lane(lane_id: str) -> bool:
    return lane_id in USER_DECISION_LANE_IDS


def parked_recovery_steps(commands: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {
            "step_id": "inspect_study_progress",
            "title": "读取当前停驻投影",
            "surface_kind": "study_progress",
            "command": commands["study_progress"],
        },
        {
            "step_id": "open_workspace_cockpit",
            "title": "返回 workspace cockpit",
            "surface_kind": "workspace_cockpit",
            "command": commands["workspace_cockpit"],
        },
    ]


def parked_truth_candidates(
    handling_state: str,
    *,
    controller_decision_payload: Mapping[str, Any] | None,
    publication_eval_payload: Mapping[str, Any] | None,
    latest_event_source: str | None,
    latest_event_time: str | None,
) -> tuple[tuple[str | None, str | None], ...] | None:
    if not is_parked_handling_state(handling_state):
        return None
    return (
        ("controller_decision", _text((controller_decision_payload or {}).get("emitted_at"))),
        ("publication_eval", _text((publication_eval_payload or {}).get("emitted_at"))),
        (latest_event_source, latest_event_time),
    )


def parked_human_surface_summary(handling_state: str) -> tuple[str, str] | None:
    if not is_parked_handling_state(handling_state):
        return None
    return "parked", "自动运行已停驻并释放资源；给人看的稿件状态以当前投影和最新用户反馈为准。"


def parked_status_verdict(handling_state: str) -> str | None:
    return {
        "package_ready_handoff": "MAS/MDS 已到投稿包/人审包交付节点，当前停驻等待用户审阅或显式恢复。",
        "external_metadata_pending": "MAS/MDS 已释放自动运行资源，当前等待外部投稿元数据。",
        "waiting_user_decision": "MAS/MDS 已停在需要用户判断的节点，用户反馈会优先重新打开修订线。",
        "external_input_pending": "MAS/MDS 正在等待外部输入，不会用本机自动运行空转替代。",
        "external_upstream_pending": "当前阻塞属于上游 API/provider/account 问题，MAS/MDS 已停止空转。",
        "explicit_resume_pending": "当前运行已停驻，等待显式 resume、rerun 或 relaunch。",
        "platform_repair_pending": "当前阻塞属于 MAS/MDS 平台问题，需要工程修复后再恢复。",
        "preflight_contract_pending": "当前运行前置合同未满足，自动运行已停驻等待合同修复。",
    }.get(handling_state)


def parked_owner_summary(handling_state: str) -> str | None:
    if not is_parked_handling_state(handling_state):
        return None
    return "MAS/MDS 已释放自动运行资源；下一步由 parked_state 指定的 owner 或显式唤醒条件决定。"


def parked_focus_summary(
    handling_state: str,
    *,
    intervention_lane: Mapping[str, Any],
    current_stage_summary: str,
) -> str | None:
    if not is_parked_handling_state(handling_state):
        return None
    return _text(intervention_lane.get("summary")) or current_stage_summary or "当前聚焦是保持停驻投影清晰，等待显式恢复或新的用户输入。"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
