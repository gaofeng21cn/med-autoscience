from __future__ import annotations


_PHASE_STATUS_LABELS = {
    "in_progress": "进行中",
    "completed": "已完成",
    "pending": "待开始",
    "blocked": "阻塞中",
    "blocked_post_gate": "等待前置门后进入",
}

_ENTRY_POINT_LABELS = {
    "mainline_status": "查看主线状态",
    "workspace_cockpit": "打开 workspace cockpit",
    "study_progress": "查看 study 进度",
    "submit_study_task": "提交 study 任务",
    "launch_study": "启动或续跑 study",
    "doctor": "运行 doctor",
    "hermes_runtime_check": "检查 Hermes runtime",
    "watch": "刷新监管与恢复",
}

_SEQUENCE_SCOPE_LABELS = {
    "monorepo_landing_readiness": "monorepo 落地就绪度",
}

_MONOREPO_STATUS_LABELS = {
    "post_gate_target": "post-gate 目标态",
}


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _phase_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _PHASE_STATUS_LABELS.get(text, text)


def _bool_label(value: object) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return text


def _entry_point_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未命名入口"
    return _ENTRY_POINT_LABELS.get(text, text.replace("_", " "))


def _sequence_scope_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _SEQUENCE_SCOPE_LABELS.get(text, text)


def _monorepo_status_label(value: object) -> str:
    text = _non_empty_text(value)
    if text is None:
        return "未知"
    return _MONOREPO_STATUS_LABELS.get(text, text)
