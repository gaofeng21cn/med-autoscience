from __future__ import annotations

from typing import Any, Iterable

MANUSCRIPT_FAST_LANE_ENTRY_MODES = frozenset({"manuscript_fast_lane"})
MANUSCRIPT_FAST_LANE_MARKERS = (
    "manuscript fast lane",
    "fast lane",
    "text-only manuscript revision",
    "text-only revision",
    "foreground fast lane",
    "manual finishing",
    "manual_finishing",
    "论文快修",
    "文本快修",
    "前台快修",
    "人工收尾",
)
MANUSCRIPT_FAST_LANE_GUARDRAIL_MARKERS = (
    "existing evidence only",
    "existing evidence",
    "canonical paper",
    "controller-authorized canonical paper",
    "paper/",
    "no new analysis",
    "既有 evidence",
    "既有证据",
    "现有证据",
    "不新增分析",
    "不做新分析",
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


def _contains_any(payload: dict[str, Any] | None, markers: tuple[str, ...]) -> bool:
    corpus = _task_intake_text_corpus(payload)
    if not corpus:
        return False
    return any(marker.lower() in text.lower() for text in corpus for marker in markers)


def task_intake_requests_manuscript_fast_lane(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    entry_mode = _non_empty_text(payload.get("entry_mode"))
    if entry_mode in MANUSCRIPT_FAST_LANE_ENTRY_MODES:
        return True
    return _contains_any(payload, MANUSCRIPT_FAST_LANE_MARKERS) and _contains_any(
        payload,
        MANUSCRIPT_FAST_LANE_GUARDRAIL_MARKERS,
    )


def build_manuscript_fast_lane_contract(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_requests_manuscript_fast_lane(payload):
        return None
    return {
        "surface_kind": "manuscript_fast_lane_contract",
        "status": "requested",
        "execution_owner": "codex_foreground_under_mas_controller",
        "canonical_write_surface": "paper/",
        "human_projection_surface": "manuscript/current_package/",
        "required_conditions": [
            "manual_finishing_or_bundle_stage_ready",
            "runtime_inactive_or_takeover_allowed",
            "canonical_paper_authority_resolved",
            "existing_evidence_only",
            "claim_guardrails_preserved",
        ],
        "allowed_change_scope": [
            "canonical paper text and structure",
            "review matrix or durable handoff",
            "evidence repackaging from existing results",
            "export/sync of human-facing package after canonical writeback",
        ],
        "forbidden_change_scope": [
            "new analysis or new result claims",
            "runtime-owned roots without explicit takeover",
            "direct-only manuscript/current_package completion claims",
        ],
        "required_validation": [
            "MAS export/sync from canonical paper authority",
            "publication/reporting QC",
            "forbidden terminology or internal-jargon scan",
            "package consistency check",
        ],
        "handoff_required": True,
    }


def build_manuscript_fast_lane_progress_override(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not task_intake_requests_manuscript_fast_lane(payload):
        return None
    first_cycle_outputs = _normalized_strings((payload or {}).get("first_cycle_outputs") or [])
    current_focus = (
        first_cycle_outputs[0]
        if first_cycle_outputs
        else "controller-visible intake/handoff, canonical paper patch, export/sync, QC and package consistency checks"
    )
    manuscript_fast_lane = build_manuscript_fast_lane_contract(payload) or {}
    blocker_summary = (
        "最新 task intake 已明确要求走 manuscript fast lane；执行前必须确认 manual_finishing、"
        "runtime inactive 或 foreground takeover allowed，并且改动只限 canonical paper 文本/结构与既有证据重包装。"
    )
    route_summary = (
        "最新 task intake 已进入 controller-visible manuscript fast lane；先在 canonical paper/ 完成"
        f"“{current_focus}”，再通过 MAS export/sync 与 QC 刷新 human-facing package。"
    )
    execution_summary = (
        "按 manuscript fast lane 执行：Codex 前台只改 controller-authorized canonical paper surface，"
        "保留 handoff，随后运行 export/sync 与包一致性验证。"
    )
    return {
        "blocker_summary": blocker_summary,
        "current_stage_summary": blocker_summary,
        "next_system_action": route_summary,
        "current_required_action": "run_manuscript_fast_lane",
        "paper_stage": "write",
        "paper_stage_summary": route_summary,
        "manuscript_fast_lane": {
            **manuscript_fast_lane,
            "enabled": True,
        },
        "quality_closure_truth": {
            "state": "manuscript_fast_lane_requested",
            "summary": blocker_summary,
            "current_required_action": "run_manuscript_fast_lane",
            "route_target": "write",
        },
        "quality_execution_lane": {
            "lane_id": "manuscript_fast_lane",
            "lane_label": "论文快修通道",
            "repair_mode": "same_line_route_back",
            "route_target": "write",
            "route_key_question": current_focus,
            "summary": execution_summary,
            "why_now": blocker_summary,
        },
        "same_line_route_truth": {
            "surface_kind": "same_line_route_truth",
            "same_line_state": "same_line_route_back",
            "same_line_state_label": "同线质量修复",
            "route_mode": "return",
            "route_target": "write",
            "route_target_label": "论文写作与结果收紧",
            "summary": route_summary,
            "current_focus": current_focus,
        },
        "same_line_route_surface": {
            "surface_kind": "same_line_route_surface",
            "lane_id": "manuscript_fast_lane",
            "repair_mode": "same_line_route_back",
            "route_target": "write",
            "route_target_label": "论文写作与结果收紧",
            "route_key_question": current_focus,
            "summary": execution_summary,
            "why_now": blocker_summary,
            "current_required_action": "run_manuscript_fast_lane",
            "closure_state": "manuscript_fast_lane_requested",
        },
    }


def render_manuscript_fast_lane_markdown_lines(payload: dict[str, Any]) -> list[str]:
    if build_manuscript_fast_lane_contract(payload) is None:
        return []
    return [
        "",
        "## Manuscript Fast Lane",
        "",
        "- 状态: requested",
        "- 执行 owner: Codex foreground under MAS controller",
        "- 写入面: controller-authorized `paper/` canonical source",
        "- 投影面: `manuscript/current_package/` 只能由 export/sync 刷新",
        "- 前置条件: manual_finishing 或 bundle_stage_ready；runtime inactive 或已允许 foreground takeover；所有结果来自既有 evidence。",
        "- 验证: MAS export/sync、publication/reporting QC、禁词/内部术语扫描、package consistency check。",
    ]


def render_manuscript_fast_lane_runtime_context_lines(payload: dict[str, Any]) -> list[str]:
    if build_manuscript_fast_lane_contract(payload) is None:
        return []
    return [
        "Manuscript fast lane: requested",
        "Execution owner: Codex foreground under MAS controller",
        "Write only controller-authorized canonical paper/ sources.",
        "Use existing evidence only; do not create new analysis or new result claims.",
        "After writeback, run MAS export/sync, QC, terminology scan, and package consistency checks.",
    ]
