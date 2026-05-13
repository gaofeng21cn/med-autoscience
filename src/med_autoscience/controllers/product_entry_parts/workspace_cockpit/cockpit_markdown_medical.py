from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.delivery_visibility_projection import (
    render_delivery_inspection_markdown_lines,
)
from med_autoscience.controllers.medical_paper_research_loop import research_loop_markdown_lines
from med_autoscience.controllers.product_entry_parts.workspace_cockpit.cockpit_markdown_common import (
    readiness_action_card_label,
)


def append_medical_paper_readiness_state(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## 自动医学论文能力闭环 / Medical Paper Readiness", ""])
    readiness_state = dict(payload.get("medical_paper_readiness_state") or {})
    if readiness_state:
        counts = dict(readiness_state.get("counts") or {})
        lines.append(f"- 当前 readiness 摘要: {readiness_state.get('summary') or 'none'}")
        lines.append(
            "- 当前计数: "
            f"已接入 {counts.get('projected_count', 0)}；"
            f"ready {counts.get('ready', 0)}；"
            f"需要关注 {counts.get('attention_required', 0)}；"
            f"missing {counts.get('missing', 0)}"
        )
        for study in readiness_state.get("studies") or []:
            if isinstance(study, Mapping):
                _append_readiness_study(lines, study)
    else:
        lines.append("- 当前还没有 Medical Paper Readiness projection。")


def _append_readiness_study(lines: list[str], study: Mapping[str, Any]) -> None:
    next_action = dict(study.get("next_action") or {})
    lines.append(
        f"- `{study.get('study_id') or 'unknown-study'}` overall_status: "
        f"`{study.get('overall_status') or 'unknown'}` "
        f"({study.get('ready_count', 0)}/{study.get('required_count', 0)})"
    )
    if next_action.get("summary"):
        lines.append(f"  下一步: {next_action.get('summary')}")
    readiness_actions = [
        item
        for item in study.get("workflow_steps") or study.get("action_cards") or []
        if isinstance(item, Mapping)
    ]
    if readiness_actions:
        labels = "；".join(
            readiness_action_card_label(item)
            for item in readiness_actions
            if item.get("label") or item.get("title")
        )
        if labels:
            lines.append(f"  动作卡: {labels}")
    lines.append("  quality authorization: projection-only")


def append_medical_paper_v4_operations_state(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## v4 生产运行面 / Medical Paper Operations", ""])
    v4_operations_state = dict(payload.get("medical_paper_v4_operations_state") or {})
    if v4_operations_state:
        counts = dict(v4_operations_state.get("counts") or {})
        lines.append(f"- 当前 v4 operations 摘要: {v4_operations_state.get('summary') or 'none'}")
        lines.append(
            "- 当前计数: "
            f"study {counts.get('study_count', 0)}；"
            f"ready {counts.get('ready', 0)}；"
            f"partial {counts.get('partial', 0)}；"
            f"blocked {counts.get('blocked', 0)}"
        )
        _append_v4_operation_studies(lines, v4_operations_state)
    else:
        lines.append("- 当前还没有 v4 operations projection。")


def _append_v4_operation_studies(lines: list[str], state: Mapping[str, Any]) -> None:
    for study in state.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        next_action = dict(study.get("next_action") or {})
        lines.append(
            f"- `{study.get('study_id') or 'unknown-study'}` v4 operations: "
            f"`{study.get('overall_status') or 'unknown'}`；"
            f"下一步 `{next_action.get('summary') or 'none'}`"
        )


def append_medical_paper_ops_health_state(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(["", "## v5 运营健康闭环 / Medical Paper Ops Health", ""])
    ops_health_state = dict(payload.get("medical_paper_ops_health_state") or {})
    if ops_health_state:
        counts = dict(ops_health_state.get("counts") or {})
        lines.append(f"- 当前 ops health 摘要: {ops_health_state.get('summary') or 'none'}")
        lines.append(f"- last-green: `{ops_health_state.get('last_green_at') or 'none'}`")
        lines.append(
            "- 当前计数: "
            f"study {counts.get('study_count', 0)}；"
            f"ready {counts.get('ready', 0)}；"
            f"partial {counts.get('partial', 0)}；"
            f"blocked {counts.get('blocked', 0)}"
        )
        _append_ops_health_studies(lines, ops_health_state)
    else:
        lines.append("- 当前还没有 v5 ops health projection。")


def _append_ops_health_studies(lines: list[str], state: Mapping[str, Any]) -> None:
    for study in state.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        next_action = dict(study.get("next_operator_action") or {})
        lines.append(
            f"- `{study.get('study_id') or 'unknown-study'}` ops health: "
            f"`{study.get('overall_status') or 'unknown'}`；"
            f"下一步 `{next_action.get('summary') or 'none'}`"
        )


def append_medical_paper_research_loop_state(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(_medical_paper_research_loop_cockpit_lines(payload.get("medical_paper_research_loop_state")))


def append_delivery_inspection_state(lines: list[str], payload: Mapping[str, Any]) -> None:
    lines.extend(_workspace_delivery_inspection_lines(payload.get("delivery_inspection_state")))


def _workspace_delivery_inspection_lines(state: object) -> list[str]:
    delivery_state = dict(state or {}) if isinstance(state, Mapping) else {}
    if not delivery_state:
        return []
    counts = dict(delivery_state.get("counts") or {})
    lines = [
        "",
        "## Delivery Inspection",
        "",
        "- submission_minimal = controller-authorized source",
        "- current_package = human-facing mirror",
        "- layout migration: layout migration 会在下一次 authorized sync 升级",
        f"- 当前摘要: {delivery_state.get('summary') or 'none'}",
        (
            "- 当前计数: "
            f"已接入 {counts.get('projected_count', 0)}；"
            f"需要关注 {counts.get('attention_required', 0)}；"
            f"layout migration {counts.get('layout_migration_pending_sync', 0)}"
        ),
    ]
    for study in delivery_state.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        lines.append(
            f"- `{study.get('study_id') or 'unknown-study'}` delivery: "
            f"`{study.get('status') or 'unknown'}`；{study.get('summary') or 'none'}"
        )
    return lines


def _medical_paper_research_loop_cockpit_lines(state: object) -> list[str]:
    research_loop_state = dict(state or {}) if isinstance(state, Mapping) else {}
    if not research_loop_state:
        return [
            "",
            "## 自动论文科研闭环 / Medical Paper Research Loop",
            "",
            "- 当前还没有 Medical Paper Research Loop projection。",
        ]
    lines = research_loop_markdown_lines(research_loop_state)
    for study in research_loop_state.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        lines.append(
            f"- `{study.get('study_id') or 'unknown-study'}` research loop: "
            f"`{study.get('overall_status') or 'unknown'}`"
        )
        lines.extend(research_loop_markdown_lines(study, heading=False))
    return lines


def active_item_research_loop_lines(state: object) -> list[str]:
    research_loop = dict(state or {}) if isinstance(state, Mapping) else {}
    if not research_loop:
        return []
    return [
        "- Medical Paper Research Loop: "
        f"overall_status `{research_loop.get('overall_status') or 'unknown'}`；"
        f"下一步: {dict(research_loop.get('next_action') or {}).get('summary') or 'none'}；"
        "authority contract: projection-only"
    ]


def active_item_delivery_inspection_lines(state: object) -> list[str]:
    return render_delivery_inspection_markdown_lines(
        state,
        heading="#### Delivery Inspection",
    )
