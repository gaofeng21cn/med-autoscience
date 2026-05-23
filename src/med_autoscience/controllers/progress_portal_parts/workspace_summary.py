from __future__ import annotations

from typing import Any


def workspace_status_paragraphs(studies: list[dict[str, Any]]) -> list[str]:
    if not studies:
        return ["当前 workspace 尚未发现论文线。"]
    live = sum(1 for item in studies if bool(item.get("active_run_id")))
    needs_supervisor = sum(1 for item in studies if str(item.get("runtime_health_status") or "") == "escalated")
    parked = sum(
        1
        for item in studies
        if str(item.get("runtime_health_status") or "") in {"parked", "awaiting_explicit_resume", "await_explicit_resume"}
    )
    return [
        f"当前 workspace 共 {len(studies)} 条论文线：{live} 条有 OPL 运行投影，{needs_supervisor} 条需要外层 supervisor，{parked} 条等待显式恢复或停驻。",
        "以论文线概览表为当前主状态；单篇详情需进入具体 study 视图查看。",
    ]


def workspace_next_step_paragraphs(studies: list[dict[str, Any]]) -> list[str]:
    if not studies:
        return ["先确认 workspace profile 和 studies root。"]
    focus = [
        f"{item.get('study_id')}: {item.get('operator_focus') or item.get('next_system_action')}"
        for item in studies
        if item.get("operator_focus") or item.get("next_system_action")
    ]
    return focus[:4] or ["当前没有 workspace 级下一步投影。"]


def workspace_quality_paragraphs(studies: list[dict[str, Any]]) -> list[str]:
    total = len(studies)
    if total == 0:
        return ["当前 workspace 尚未发现论文线。"]
    blocked = sum(
        1
        for item in studies
        if str(item.get("runtime_health_status") or "") in {"blocked", "recovering", "escalated", "attention_required"}
    )
    stale = sum(1 for item in studies if str(item.get("progress_freshness_status") or "") == "stale")
    return [
        f"当前显示 workspace 级质量/论文状态：共 {total} 条论文线，{blocked} 条需要运行或质量侧关注，{stale} 条进度新鲜度陈旧。",
        "单篇发表门禁、AI 复审和当前投稿包结论需进入具体 study 视图查看。",
    ]


def workspace_delivery_paragraphs(studies: list[dict[str, Any]]) -> list[str]:
    total = len(studies)
    live_like = sum(
        1
        for item in studies
        if str(item.get("current_stage") or "") in {"live", "write", "analysis-campaign"}
    )
    return [
        f"当前为 workspace 总览，不直接判断单篇交付包 ready；{live_like}/{total} 条论文线仍处于写作、分析或运行相关阶段。",
        "交付文件位置和当前投稿包状态由各 study 的交付/package surface 持有。",
    ]


__all__ = [
    "workspace_delivery_paragraphs",
    "workspace_next_step_paragraphs",
    "workspace_quality_paragraphs",
    "workspace_status_paragraphs",
]
