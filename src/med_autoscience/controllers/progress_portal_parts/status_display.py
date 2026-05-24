from __future__ import annotations

from html import escape


STATUS_LABELS = {
    "active": "活跃",
    "analysis-campaign": "分析推进",
    "attention_required": "需要关注",
    "available": "可读取",
    "await_explicit_resume": "等待显式恢复",
    "awaiting_explicit_resume": "等待显式恢复",
    "blocked": "阻塞",
    "blocked_reason": "阻塞原因",
    "completed": "已完成",
    "conflict": "冲突",
    "escalated": "已升级",
    "execution_failed": "执行失败",
    "fresh": "新鲜",
    "invalid": "无效",
    "loaded": "已注册",
    "manual_hold": "手动暂停",
    "live_worker_meaningful_artifact_delta_timeout": "live worker 产物增量超时",
    "missing": "缺失",
    "no_live_run": "无运行编号",
    "none": "无",
    "not_required": "无需自动推进",
    "not_installed": "未注册",
    "not_loaded": "未加载",
    "parked": "停驻",
    "projected": "投影",
    "recover_runtime": "恢复 runtime",
    "recovering": "恢复中",
    "run_id_without_worker": "有 run_id 但 worker 未确认",
    "run_projection_without_worker": "有 run 投影但 worker 未确认",
    "running": "运行中",
    "runtime_handoff_required": "需要 OPL runtime handoff",
    "stale": "陈旧",
    "same_fingerprint_loop": "同 fingerprint 循环",
    "workspace-overview": "工作区总览",
    "write": "写作",
    "external_supervisor_required": "需要外层 supervisor",
    "runtime_recovery_retry_budget_exhausted": "runtime 恢复重试预算耗尽",
    "quest_marked_running_but_no_live_session": "标记运行但没有 live session",
    "unknown": "未知",
}

EMPTY_VALUE_LABELS = {
    "",
    "none",
    "null",
    "unknown",
    "unknown-study",
}


def status_label(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "未提供"
    label = STATUS_LABELS.get(text)
    return label or text


def display_text(value: object, *, empty_text: str = "未提供", preserve_known_token: bool = True) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in EMPTY_VALUE_LABELS:
        return empty_text
    if preserve_known_token:
        return status_label(text)
    return STATUS_LABELS.get(text, text)


def status_chip(value: object) -> str:
    text = str(value or "").strip() or "unknown"
    label = status_label(text)
    tone = "neutral"
    lowered = text.lower()
    if lowered in {"fresh", "loaded", "running", "active", "completed", "available"}:
        tone = "ok"
    elif lowered in {
        "stale",
        "recovering",
        "attention_required",
        "manual_hold",
        "parked",
        "awaiting_explicit_resume",
        "await_explicit_resume",
        "not_required",
        "projected",
        "no_live_run",
    }:
        tone = "warn"
    elif lowered in {
        "missing",
        "blocked",
        "escalated",
        "execution_failed",
        "invalid",
        "not_installed",
        "not_loaded",
        "external_supervisor_required",
        "runtime_recovery_retry_budget_exhausted",
        "quest_marked_running_but_no_live_session",
    }:
        tone = "bad"
    return f'<span class="status-chip status-{tone}">{escape(label)}</span>'


__all__ = ["STATUS_LABELS", "display_text", "status_chip", "status_label"]
