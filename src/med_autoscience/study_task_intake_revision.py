from __future__ import annotations

from typing import Any, Iterable

from med_autoscience.study_task_intake_stop_loss import (
    build_publishability_stop_loss_intake,
    task_intake_requests_publishability_stop_loss,
)

DIRECT_FINALIZE_DOWNGRADE_MARKERS = (
    "不能按已达投稿包里程碑直接收口",
    "不得直接按外投收口",
    "submission-ready/finalize 判断降回",
    "降回待修订后再评估",
    "downgrade the current submission-ready/finalize judgment",
)
REVIEWER_REVISION_MARKERS = (
    "reviewer feedback",
    "reviewer comment",
    "review comments",
    "reviewer revision",
    "reviewer-first revision",
    "reviewer first revision",
    "manuscript revision",
    "manuscript-change",
    "paper revision",
    "revise manuscript",
    "revision checklist",
    "explicit user feedback",
    "user feedback",
    "review matrix",
    "action matrix",
    "导师反馈",
    "专家反馈",
    "审稿意见",
    "审稿人意见",
    "审稿式反馈",
    "论文修改",
    "稿件修改",
    "修改意见",
    "显式重新激活同一论文线",
    "重新激活同一论文线",
    "结构性返修",
    "revision/rebuttal",
    "投稿前必须修正",
    "补分析",
    "改表",
    "改图",
    "introduction feedback",
    "methods feedback",
    "results feedback",
    "figure feedback",
    "table feedback",
    "scientific revision feedback",
    "table/figure legends",
    "tripod",
    "probast",
)
REVISION_INTAKE_CHECKLIST: tuple[tuple[str, str, str], ...] = (
    ("text_revisions", "text revisions", "Introduction/Methods/Results/Discussion 等文字修订点已逐条定位。"),
    ("methods_completeness", "methods completeness", "方法学补充、数据来源、纳排、变量和流程说明已补齐或记录为缺口。"),
    ("statistical_analysis", "statistical analysis", "新增或修订统计分析、敏感性/亚组/稳健性需求已绑定证据来源。"),
    ("tables_figures", "tables/figures", "表格、图片、图注和补充材料改动范围已列明。"),
    ("follow_up_evidence", "follow-up evidence", "后续证据、补充结果和不可完成项有明确状态。"),
    ("discussion_claim_guardrails", "discussion/claim guardrails", "讨论、结论和 claim 边界没有越过当前证据包。"),
    ("handoff_evidence_surface", "handoff/evidence surface", "durable handoff 写明数据源、脚本入口、输出表图、改动范围、claim guardrails 与 canonical source 回灌状态。"),
)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalized_strings(values: Iterable[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            normalized.append(text)
    return normalized


def _task_intake_text_corpus(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    values: list[object] = [
        payload.get("task_intent"),
        *(payload.get("constraints") or []),
        *(payload.get("evidence_boundary") or []),
        *(payload.get("trusted_inputs") or []),
        *(payload.get("reference_papers") or []),
        *(payload.get("first_cycle_outputs") or []),
    ]
    return tuple(_normalized_strings(values))


def _task_intake_contains_any(payload: dict[str, Any] | None, markers: tuple[str, ...]) -> bool:
    corpus = _task_intake_text_corpus(payload)
    if not corpus:
        return False
    for text in corpus:
        lowered = text.lower()
        if any(marker.lower() in lowered for marker in markers):
            return True
    return False


def task_intake_is_reviewer_revision(payload: dict[str, Any] | None) -> bool:
    if task_intake_requests_publishability_stop_loss(payload):
        return False
    return _task_intake_contains_any(payload, REVIEWER_REVISION_MARKERS)


def task_intake_requests_submission_package_refresh(payload: dict[str, Any] | None) -> bool:
    return _task_intake_contains_any(payload, DIRECT_FINALIZE_DOWNGRADE_MARKERS)


def submission_revision_operating_state(payload: dict[str, Any] | None) -> str | None:
    if task_intake_requests_publishability_stop_loss(payload):
        return None
    if task_intake_is_reviewer_revision(payload):
        return "reviewer_revision"
    if task_intake_requests_submission_package_refresh(payload):
        return "submission_package_refresh"
    return None
