from __future__ import annotations

from typing import Any, Mapping

from .shared import _non_empty_text


def specificity_stage_summary() -> str:
    return (
        "论文门控需要先具体化当前 blocker：要求 publication gate 写出具体 claim、figure、table、metric "
        "或 source path 后，系统才能选择对应修复 worker。"
    )


def specificity_next_system_action() -> str:
    return (
        "先要求 publication gate 输出具体 claim/figure/table/metric/source path；"
        "没有具体对象前不再启动普通分析或写作 worker。"
    )


def specificity_intervention_lane(specificity_request: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "lane_id": "publication_gate_specificity_required",
        "title": "先让发表门控具体化 blocker",
        "severity": "critical",
        "summary": (
            _non_empty_text(specificity_request.get("summary"))
            or "Publication gate must identify concrete blocker targets before any repair worker can run."
        ),
        "recommended_action_id": "request_gate_specificity",
        "repair_mode": "gate_needs_specificity",
        "route_target": "controller",
        "route_target_label": "发表门控具体化",
        "route_key_question": "publication gate 必须写出具体 claim/figure/table/metric/source path。",
        "work_unit_id": _non_empty_text(specificity_request.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(specificity_request.get("work_unit_fingerprint")),
    }
    questions = list(specificity_request.get("specificity_questions") or [])
    if questions:
        payload["specificity_questions"] = questions
    return payload


__all__ = [
    "specificity_intervention_lane",
    "specificity_next_system_action",
    "specificity_stage_summary",
]
