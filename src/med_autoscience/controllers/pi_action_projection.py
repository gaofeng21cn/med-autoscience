from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SCHEMA_VERSION = 1
SURFACE = "pi_action_projection"
READ_MODEL = "L2_pi_action_projection_read_model"
AUTHORITY = "projection_only"

ACTION_ORDER = (
    "补文献",
    "改统计",
    "降级 claim",
    "重开同一论文线",
    "换线",
    "进入 AI reviewer",
    "进入 submission package rebuild",
)

AUTHORITY_CONTRACT = {
    "projection_only": True,
    "can_set_canonical_next_action": False,
    "can_authorize_publication_readiness": False,
    "can_authorize_submission": False,
    "can_mutate_runtime": False,
    "canonical_next_action_authority": (
        "StudyTruthKernel, RuntimeHealthKernel, AI reviewer-backed publication_eval/latest.json, "
        "controller_decisions/latest.json, and canonical artifact proof"
    ),
}

_CATEGORY_SUMMARIES = {
    "补文献": "补齐可审计文献、检索日期、anchor/guideline/近邻文献，再回到论文质量判断。",
    "改统计": "补齐统计纪律、敏感性分析、报告规范或临床效用分析，再回到质量复核。",
    "降级 claim": "把当前过强或证据不足的 claim 收紧到已有证据能支撑的范围。",
    "重开同一论文线": "同一 study line 仍可救，重新进入同线修复、返修或有限补充分析。",
    "换线": "当前主线触发止损或路线切换压力，需要进入新路线选择或换线判断。",
    "进入 AI reviewer": "进入 AI reviewer-backed 质量、写作或返修闭环，补齐 reviewer provenance。",
    "进入 submission package rebuild": "质量与授权面已足够接近交付，下一步从 canonical source 重建投稿包。",
}

_CATEGORY_STEP_IDS = {
    "补文献": "complete_literature_evidence",
    "改统计": "resolve_statistical_blockers",
    "降级 claim": "downgrade_claim_scope",
    "重开同一论文线": "reopen_same_paper_line",
    "换线": "switch_study_line",
    "进入 AI reviewer": "enter_ai_reviewer",
    "进入 submission package rebuild": "rebuild_submission_package",
}

_LITERATURE_TOKENS = (
    "literature",
    "reference",
    "citation",
    "guideline",
    "anchor",
    "scout",
    "文献",
    "参考文献",
    "指南",
)
_STAT_TOKENS = (
    "statistical",
    "statistics",
    "sensitivity",
    "subgroup",
    "baseline_balance",
    "decision_curve",
    "time_to_event",
    "competing_risk",
    "prediction_performance",
    "missingness",
    "统计",
    "亚组",
    "敏感性",
    "校准",
    "外部验证",
)
_CLAIM_TOKENS = (
    "claim",
    "claim_evidence",
    "primary_claim",
    "overclaim",
    "evidence_strength",
    "证据链",
    "结论",
    "主结论",
    "降级",
)
_AI_REVIEWER_TOKENS = (
    "ai_reviewer",
    "reviewer",
    "human_review",
    "medical_journal_prose",
    "target_journal",
    "revision",
    "rebuttal",
    "审稿",
    "返修",
    "写作",
)
_REBUILD_TOKENS = (
    "submission",
    "package",
    "bundle",
    "current_package",
    "artifact_proof",
    "delivery",
    "finalize",
    "投稿包",
    "交付",
    "定稿",
    "重建",
)
_SWITCH_TOKENS = (
    "switch",
    "switch_line",
    "stop_loss",
    "reroute",
    "route change",
    "换线",
    "止损",
    "改换",
)
_REOPEN_TOKENS = (
    "same_line",
    "same-line",
    "route_back",
    "bounded_analysis",
    "reopen",
    "continue_same_line",
    "同线",
    "重开",
    "补充分析",
)


def build_pi_action_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    categories = _infer_categories(payload)
    primary = categories[0] if categories else _fallback_category(payload)
    evidence = _evidence_refs(payload)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "authority": AUTHORITY,
        "projection_only": True,
        "study_id": _text(payload.get("study_id")),
        "primary_category": primary,
        "categories": [
            _category_payload(category=category, payload=payload, evidence_refs=evidence)
            for category in categories
        ],
        "summary": _summary(primary, categories),
        "source_surfaces": _source_surfaces(payload),
        "authority_contract": dict(AUTHORITY_CONTRACT),
    }


def compact_pi_action_projection(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    compact = {
        "surface": value.get("surface") or SURFACE,
        "schema_version": value.get("schema_version") or SCHEMA_VERSION,
        "read_model": value.get("read_model") or READ_MODEL,
        "authority": value.get("authority") or AUTHORITY,
        "projection_only": bool(value.get("projection_only", True)),
        "study_id": _text(value.get("study_id")),
        "primary_category": _text(value.get("primary_category")),
        "summary": _text(value.get("summary")),
    }
    categories = []
    for item in value.get("categories") or []:
        if not isinstance(item, Mapping):
            continue
        categories.append(
            {
                key: item[key]
                for key in (
                    "category",
                    "label",
                    "recommended_step_id",
                    "summary",
                    "projection_only",
                    "can_authorize_publication_readiness",
                    "can_authorize_submission",
                    "can_set_canonical_next_action",
                )
                if key in item
            }
        )
    compact["categories"] = categories
    contract = value.get("authority_contract")
    if isinstance(contract, Mapping):
        compact["authority_contract"] = {
            key: contract[key]
            for key in (
                "projection_only",
                "can_set_canonical_next_action",
                "can_authorize_publication_readiness",
                "can_authorize_submission",
                "can_mutate_runtime",
            )
            if key in contract
        }
    return compact


def _category_payload(
    *,
    category: str,
    payload: Mapping[str, Any],
    evidence_refs: list[str],
) -> dict[str, Any]:
    return {
        "category": category,
        "label": category,
        "summary": _CATEGORY_SUMMARIES[category],
        "recommended_step_id": _CATEGORY_STEP_IDS[category],
        "recommended_command": _text(payload.get("recommended_command")),
        "evidence_refs": evidence_refs[:8],
        "projection_only": True,
        "can_set_canonical_next_action": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission": False,
    }


def _infer_categories(payload: Mapping[str, Any]) -> list[str]:
    categories: list[str] = []
    _append_readiness_categories(categories, _mapping(payload.get("medical_paper_readiness")))
    _append_quality_categories(categories, payload)
    _append_runtime_categories(categories, payload)
    _append_ai_first_categories(categories, payload)
    return [category for category in ACTION_ORDER if category in categories]


def _append_readiness_categories(categories: list[str], readiness: Mapping[str, Any]) -> None:
    if not readiness:
        return
    surfaces = [
        item
        for item in readiness.get("capability_surfaces") or []
        if isinstance(item, Mapping)
        and bool(item.get("required_for_ready"))
        and _text(item.get("status")) != "present"
    ]
    action_cards = [item for item in readiness.get("action_cards") or [] if isinstance(item, Mapping)]
    texts = _joined_text(readiness, *surfaces, *action_cards, _mapping(readiness.get("next_action")))
    if _has_any(texts, _LITERATURE_TOKENS):
        _add(categories, "补文献")
    if _has_any(texts, _STAT_TOKENS):
        _add(categories, "改统计")
    if _has_any(texts, _CLAIM_TOKENS):
        _add(categories, "降级 claim")
    if _has_any(texts, _REOPEN_TOKENS):
        _add(categories, "重开同一论文线")
    if _has_any(texts, _SWITCH_TOKENS):
        _add(categories, "换线")
    if _has_any(texts, _AI_REVIEWER_TOKENS):
        _add(categories, "进入 AI reviewer")
    if _has_any(texts, _REBUILD_TOKENS):
        _add(categories, "进入 submission package rebuild")


def _append_quality_categories(categories: list[str], payload: Mapping[str, Any]) -> None:
    quality_lane = _mapping(payload.get("quality_execution_lane"))
    same_line_truth = _mapping(payload.get("same_line_route_truth"))
    same_line_surface = _mapping(payload.get("same_line_route_surface"))
    review_loop = _mapping(payload.get("quality_review_loop"))
    blockers = payload.get("current_blockers") if isinstance(payload.get("current_blockers"), list) else []
    texts = _joined_text(quality_lane, same_line_truth, same_line_surface, review_loop, *blockers)
    if _has_any(texts, _STAT_TOKENS):
        _add(categories, "改统计")
    if _has_any(texts, _CLAIM_TOKENS):
        _add(categories, "降级 claim")
    if _has_any(texts, _REOPEN_TOKENS):
        _add(categories, "重开同一论文线")
    if _has_any(texts, _SWITCH_TOKENS):
        _add(categories, "换线")
    if _has_any(texts, _AI_REVIEWER_TOKENS):
        _add(categories, "进入 AI reviewer")


def _append_runtime_categories(categories: list[str], payload: Mapping[str, Any]) -> None:
    intervention_lane = _mapping(payload.get("intervention_lane"))
    task_intake = _mapping(payload.get("task_intake"))
    controller = _mapping(payload.get("authority_snapshot"))
    texts = _joined_text(
        intervention_lane,
        task_intake,
        controller,
        payload.get("next_system_action"),
        payload.get("current_stage_summary"),
    )
    lane_id = _text(intervention_lane.get("lane_id"))
    if lane_id == "manual_finishing" or _has_any(texts, _REBUILD_TOKENS):
        _add(categories, "进入 submission package rebuild")
    if _has_any(texts, _REOPEN_TOKENS):
        _add(categories, "重开同一论文线")
    if _has_any(texts, _SWITCH_TOKENS):
        _add(categories, "换线")


def _append_ai_first_categories(categories: list[str], payload: Mapping[str, Any]) -> None:
    default_state = _mapping(payload.get("ai_first_default_entry_state"))
    feedback_state = _mapping(payload.get("ai_first_feedback_state"))
    lifecycle = _mapping(payload.get("ai_first_action_dispatch_lifecycle"))
    request_lifecycle = _mapping(payload.get("ai_reviewer_request_lifecycle"))
    texts = _joined_text(default_state, feedback_state, lifecycle, request_lifecycle)
    if _has_any(texts, _AI_REVIEWER_TOKENS):
        _add(categories, "进入 AI reviewer")
    if _has_any(texts, _REBUILD_TOKENS):
        _add(categories, "进入 submission package rebuild")


def _fallback_category(payload: Mapping[str, Any]) -> str:
    next_action = _text(payload.get("next_system_action")) or ""
    if _has_any(next_action, _REBUILD_TOKENS):
        return "进入 submission package rebuild"
    if _has_any(next_action, _AI_REVIEWER_TOKENS):
        return "进入 AI reviewer"
    if _has_any(next_action, _SWITCH_TOKENS):
        return "换线"
    if _has_any(next_action, _REOPEN_TOKENS):
        return "重开同一论文线"
    if _has_any(next_action, _STAT_TOKENS):
        return "改统计"
    if _has_any(next_action, _CLAIM_TOKENS):
        return "降级 claim"
    if _has_any(next_action, _LITERATURE_TOKENS):
        return "补文献"
    return "进入 AI reviewer"


def _source_surfaces(payload: Mapping[str, Any]) -> list[str]:
    surfaces = ["study_progress"]
    for key in (
        "study_truth_snapshot",
        "runtime_health_snapshot",
        "authority_snapshot",
        "medical_paper_readiness",
        "quality_execution_lane",
        "same_line_route_truth",
        "ai_reviewer_request_lifecycle",
        "artifact_runtime_proof",
        "submission_hygiene_truth",
    ):
        if isinstance(payload.get(key), Mapping):
            surfaces.append(key)
    return surfaces


def _evidence_refs(payload: Mapping[str, Any]) -> list[str]:
    refs = _mapping(payload.get("refs"))
    values = []
    for key in (
        "study_truth_snapshot_path",
        "runtime_health_snapshot_path",
        "publication_eval_path",
        "controller_decision_path",
        "medical_paper_readiness_path",
        "artifact_runtime_proof_delivery_manifest_path",
        "submission_hygiene_submission_manifest_path",
    ):
        text = _text(refs.get(key))
        if text:
            values.append(text)
    return values


def _summary(primary: str, categories: list[str]) -> str:
    if not categories:
        return _CATEGORY_SUMMARIES[primary]
    if len(categories) == 1:
        return _CATEGORY_SUMMARIES[categories[0]]
    return f"PI action projection 建议先处理「{primary}」，并同步关注：" + "、".join(categories[1:])


def _add(categories: list[str], category: str) -> None:
    if category not in categories:
        categories.append(category)


def _has_any(text: str, tokens: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def _joined_text(*values: object) -> str:
    return " ".join(_walk_text(value) for value in values)


def _walk_text(value: object) -> str:
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_walk_text(item)}" for key, item in value.items())
    if isinstance(value, list | tuple | set):
        return " ".join(_walk_text(item) for item in value)
    return str(value or "")


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
