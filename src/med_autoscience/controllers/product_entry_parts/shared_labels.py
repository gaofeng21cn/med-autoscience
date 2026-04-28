from __future__ import annotations


_OPERATOR_VERDICT_LABELS = {
    "attention_required": "需要处理",
    "preflight_blocked": "前置检查未通过",
    "ready_for_task": "可直接开始",
    "auto_runtime_parked": "自动运行已停驻",
    "monitor_only": "持续观察",
}

_WORKSPACE_STATUS_LABELS = {
    "ready": "已就绪",
    "attention_required": "需要处理",
    "blocked": "前置检查未通过",
}

_START_MODE_LABELS = {
    "open_frontdesk": "打开 MAS 前台",
    "submit_task": "给 study 下 durable 任务",
    "continue_study": "启动或续跑 study",
}

_DIRECT_ENTRY_MODE_LABELS = {
    "direct": "直接进入",
    "opl-handoff": "OPL handoff",
}

_RUNTIME_DECISION_LABELS = {
    "resume": "恢复当前运行",
    "launch": "启动新运行",
    "reroute": "改走其他运行路径",
}

_SURFACE_KIND_LABELS = {
    "product_frontdesk": "MAS 前台",
    "workspace_cockpit": "workspace cockpit",
    "study_task_intake": "study 任务入口",
    "launch_study": "启动或续跑 study",
    "study_progress": "study 进度",
}

_CHECK_STATUS_LABELS = {
    "pass": "通过",
    "fail": "未通过",
    "warning": "需关注",
}

_PHASE5_SEQUENCE_SCOPE_LABELS = {
    "monorepo_landing_readiness": "monorepo 落地就绪度（monorepo_landing_readiness）",
}

_PHASE5_MONOREPO_STATUS_LABELS = {
    "post_gate_target": "post-gate 目标态（post_gate_target）",
}

_USER_INTERACTION_MODE_LABELS = {
    "natural_language_frontdoor": "自然语言前台（natural_language_frontdoor）",
}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _operator_verdict_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _OPERATOR_VERDICT_LABELS.get(text, text)


def _workspace_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _WORKSPACE_STATUS_LABELS.get(text, text)


def _start_mode_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _START_MODE_LABELS.get(text, text.replace("_", " "))


def _direct_entry_mode_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _DIRECT_ENTRY_MODE_LABELS.get(text, text)


def _runtime_decision_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _RUNTIME_DECISION_LABELS.get(text, text)


def _surface_kind_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _SURFACE_KIND_LABELS.get(text, text.replace("_", " "))


def _bool_label(value: object) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return text


def _check_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _CHECK_STATUS_LABELS.get(text, text)


def _phase5_sequence_scope_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _PHASE5_SEQUENCE_SCOPE_LABELS.get(text, text)


def _phase5_monorepo_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _PHASE5_MONOREPO_STATUS_LABELS.get(text, text)


def _user_interaction_mode_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _USER_INTERACTION_MODE_LABELS.get(text, text)
