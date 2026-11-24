"""MAS domain status narration checklists and localized progress labels."""

from __future__ import annotations

PAPER_MILESTONE_ANSWER_CHECKLIST = (
    "milestone_status",
    "review_readiness",
    "submission_readiness",
    "remaining_scope",
)

MAS_STATUS_NARRATION_CODE_LABELS: dict[str, str] = {
    "study_completed": "研究已进入交付收尾",
    "waiting_physician_decision": "等待医生或 PI 判断",
    "publication_supervision": "论文可发表性监管",
    "runtime_preflight": "研究预检与准备阶段",
    "scientific_anchor_missing": "科学锚点仍待补齐",
    "write_stage_ready": "论文写作就绪",
    "publishability_gate_blocked": "论文可发表性门控阻塞",
    "bundle_stage_blocked": "投稿打包存在硬阻塞",
    "bundle_stage_ready": "投稿打包就绪",
    "missing_submission_minimal": "缺少最小投稿包导出。",
    "medical_publication_surface_blocked": "论文叙事或方法/结果书写面仍有硬阻塞。",
    "forbidden_manuscript_terminology": "当前稿件仍含不允许的术语表达，需要清理。",
    "forbidden_manuscript_terms_present": "当前稿件仍含不允许的术语表达，需要清理。",
    "submission_checklist_contains_unclassified_blocking_items": "投稿检查清单里仍有未归类的硬阻塞。",
    "claim_evidence_map_missing_or_incomplete": "关键 claim-to-evidence 对照仍不完整。",
    "figure_catalog_missing_or_incomplete": "关键图表目录仍不完整。",
    "ama_pdf_defaults_missing": "AMA 稿件导出默认配置仍未补齐。",
}

__all__ = [
    "MAS_STATUS_NARRATION_CODE_LABELS",
    "PAPER_MILESTONE_ANSWER_CHECKLIST",
]
