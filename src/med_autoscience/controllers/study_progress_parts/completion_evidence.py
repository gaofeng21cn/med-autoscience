from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REASON = "study_completion_contract_not_ready"
LANE_ID = "completion_evidence_required"
HANDLING_STATE = "completion_evidence_required"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def contract_from_status(status: Mapping[str, Any]) -> dict[str, Any]:
    return _mapping(status.get("study_completion_contract"))


def required(status: Mapping[str, Any]) -> bool:
    contract = contract_from_status(status)
    return _text(status.get("reason")) == REASON and _text(contract.get("status")) == "incomplete"


def missing_paths(status: Mapping[str, Any]) -> list[str]:
    contract = contract_from_status(status)
    return [text for item in contract.get("missing_evidence_paths") or [] if (text := _text(item)) is not None]


def summary(status: Mapping[str, Any]) -> str:
    paths = missing_paths(status)
    if paths:
        return "study-level 完成声明已存在，但 final submission 证据还未补齐：" + "、".join(paths)
    return "study-level 完成声明已存在，但 final submission 证据还未补齐，当前不能按完成态收口。"


def next_action(status: Mapping[str, Any]) -> str:
    del status
    return "先通过 MAS 交付/导出控制面补齐 completion evidence，再同步 completed quest；不要重开论文写作或 runtime repair。"


def intervention_lane(status: Mapping[str, Any]) -> dict[str, Any] | None:
    if not required(status):
        return None
    return {
        "lane_id": LANE_ID,
        "title": "补齐完成合同证据",
        "severity": "handoff",
        "summary": summary(status),
        "recommended_action_id": "sync_completion_evidence",
        "owner": "completion_evidence",
        "missing_evidence_paths": missing_paths(status),
    }


def completion_stage_summary(status: Mapping[str, Any]) -> str | None:
    return summary(status) if required(status) else None


def completion_next_action(status: Mapping[str, Any]) -> str | None:
    return next_action(status) if required(status) else None


def completion_blocker_summary(status: Mapping[str, Any]) -> str | None:
    return summary(status) if required(status) else None


def completion_intervention_lane(status: Mapping[str, Any]) -> dict[str, Any] | None:
    return intervention_lane(status)


def completion_progress_freshness_required(status: Mapping[str, Any]) -> bool:
    return not required(status)


def completion_stage_summary_or_reason(
    status: Mapping[str, Any],
    *,
    current_stage: str,
    reason_label,
) -> str | None:
    if current_stage != "runtime_blocked":
        return None
    return completion_stage_summary(status) or reason_label(status.get("reason"))


def completion_next_action_or_reason(
    status: Mapping[str, Any],
    *,
    decision: str | None,
    reason_label,
) -> str | None:
    if decision != "blocked":
        return None
    return completion_next_action(status) or reason_label(status.get("reason"))


def append_completion_blocker(blockers: list[str], status: Mapping[str, Any], append_unique) -> None:
    append_unique(blockers, completion_blocker_summary(status))
