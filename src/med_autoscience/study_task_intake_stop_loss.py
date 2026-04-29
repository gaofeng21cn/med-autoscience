from __future__ import annotations

from typing import Any


PUBLISHABILITY_STOP_LOSS_MARKERS = (
    "publishability stop-loss",
    "publishability stop loss",
    "stop-loss",
    "stop loss",
    "early stop",
    "terminate the paper",
    "terminate this paper",
    "stop the paper",
    "not publishable",
    "cannot publish",
    "paper is not viable",
    "no clinical significance",
    "no clinical meaning",
    "no new conclusion",
    "no meaningful novelty",
    "及时终止",
    "早期止损",
    "主动止损",
    "止损机制",
    "止损停题",
    "发不了论文",
    "不能发表",
    "无法发表",
    "没有临床意义",
    "没有什么临床意义",
    "没有新结论",
    "论文不成立",
    "稿件不成立",
    "不是可投稿论文",
    "不建议继续投稿",
    "不值得继续写",
    "继续包装",
    "浪费token",
    "knosp本来就是看侵袭性",
    "knosp 本来就是看侵袭性",
    "knosp分型的目的就是看侵袭性",
    "knosp 分型的目的就是看侵袭性",
)


def _task_intake_text_corpus(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    texts: list[str] = []
    for key in ("task_intent", "journal_target"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            texts.append(value.strip())
    for key in ("constraints", "evidence_boundary", "trusted_inputs", "reference_papers", "first_cycle_outputs"):
        value = payload.get(key)
        if isinstance(value, list):
            texts.extend(str(item).strip() for item in value if str(item).strip())
    return tuple(texts)


def task_intake_requests_publishability_stop_loss(payload: dict[str, Any] | None) -> bool:
    corpus = _task_intake_text_corpus(payload)
    if not corpus:
        return False
    haystack = "\n".join(corpus).lower()
    return any(marker in haystack for marker in PUBLISHABILITY_STOP_LOSS_MARKERS)


def build_publishability_stop_loss_intake(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_requests_publishability_stop_loss(payload):
        return None
    return {
        "kind": "publishability_stop_loss",
        "status": "active",
        "route": "stop_loss",
        "handoff_required": True,
        "reviewer_revision_allowed": False,
        "decision_policy": {
            "required_verdict": "stop",
            "canonical_action": "stop_loss",
            "controller_action": "stop_runtime",
            "reason": "The latest intake asserts that the paper line lacks an independent publishable clinical claim.",
        },
        "minimum_evidence": [
            "why the core clinical question no longer supports a publishable paper",
            "which result or prior clinical definition collapses the novelty/value claim",
            "whether a new study question is required before any future relaunch",
        ],
    }


def build_publishability_stop_loss_progress_override(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_requests_publishability_stop_loss(payload):
        return None
    blocker_summary = (
        "最新 task intake 明确触发 publishability stop-loss；当前论文线缺少可发表的独立临床结论，"
        "不得继续按 reviewer_revision 或投稿包收口推进。"
    )
    route_key_question = "当前论文线是否还有独立临床意义和强论文路径？"
    route_summary = "停止当前 manuscript line；除非未来重新定义独立研究问题并形成新的 study charter，否则不再继续打磨投稿包。"
    return {
        "blocker_summary": blocker_summary,
        "current_stage_summary": blocker_summary,
        "next_system_action": route_summary,
        "current_required_action": "stop_runtime",
        "paper_stage": "stop",
        "paper_stage_summary": route_summary,
        "quality_closure_truth": {
            "state": "stop_loss_recommended",
            "summary": blocker_summary,
            "current_required_action": "stop_runtime",
            "route_target": "stop",
        },
        "quality_execution_lane": {
            "lane_id": "stop_loss",
            "lane_label": "主动止损",
            "repair_mode": "stop_loss",
            "route_target": "stop",
            "route_key_question": route_key_question,
            "summary": route_summary,
            "why_now": blocker_summary,
        },
        "same_line_route_truth": {
            "surface_kind": "same_line_route_truth",
            "same_line_state": "stop_loss",
            "same_line_state_label": "主动止损停题",
            "route_mode": "return",
            "route_target": "stop",
            "route_target_label": "止损停题",
            "summary": route_summary,
            "current_focus": route_key_question,
        },
        "same_line_route_surface": {
            "surface_kind": "same_line_route_surface",
            "lane_id": "stop_loss",
            "repair_mode": "stop_loss",
            "route_target": "stop",
            "route_target_label": "止损停题",
            "route_key_question": route_key_question,
            "summary": route_summary,
            "why_now": blocker_summary,
            "current_required_action": "stop_runtime",
            "closure_state": "stop_loss_recommended",
        },
    }


def render_publishability_stop_loss_markdown_lines(payload: dict[str, Any]) -> list[str]:
    if not task_intake_requests_publishability_stop_loss(payload):
        return []
    return [
        "",
        "## Publishability Stop-Loss Intake",
        "",
        "- 当前任务不是稿件返修；应停止当前论文线并记录 stop-loss decision。",
        "- 不得继续把该反馈路由为 reviewer_revision、submission bundle cleanup 或前台 current_package patch。",
        "- 未来如需重启，必须先重新定义独立研究问题、study charter 与可发表性证据边界。",
    ]


def render_publishability_stop_loss_runtime_context_lines(payload: dict[str, Any]) -> list[str]:
    if not task_intake_requests_publishability_stop_loss(payload):
        return []
    return [
        "Publishability stop-loss intake: active",
        "Route: stop_loss",
        "Controller action: stop_runtime",
        "Do not route this intake as reviewer_revision or submission bundle cleanup.",
        "Future relaunch requires a new independent research question and study charter.",
    ]
