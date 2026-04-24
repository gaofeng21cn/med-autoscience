from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_publication_critique_weight_contract,
    build_revision_action_contract,
)
from med_autoscience.publication_eval_latest import read_publication_eval_latest, stable_publication_eval_latest_path
from med_autoscience.quality.publication_gate import (
    derive_quality_closure_truth,
    derive_quality_execution_lane,
)
from med_autoscience.quality.study_quality import build_study_quality_truth
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.study_task_intake import read_latest_task_intake, summarize_task_intake

from .chunk_01 import (
    __all__,
    STABLE_EVALUATION_SUMMARY_RELATIVE_PATH,
    STABLE_PROMOTION_GATE_RELATIVE_PATH,
    _GAP_SEVERITIES,
    _GAP_SEVERITY_RANK,
    _GAP_SEVERITY_LABELS,
    _ACTION_PRIORITY_RANK,
    _ROUTE_REPAIR_ACTION_TYPES,
    _QUALITY_DIMENSION_STATUSES,
    _QUALITY_CLOSURE_STATES,
    _QUALITY_CLOSURE_BASIS_KEYS,
    _QUALITY_REVIEW_STATUS_RANK,
)
from .chunk_01 import (
    _QUALITY_ASSESSMENT_REVIEW_ORDER,
    _QUALITY_EXECUTION_LANE_LABELS,
    _SAME_LINE_ROUTE_STATES,
    _SAME_LINE_ROUTE_STATE_LABELS,
    _SAME_LINE_ROUTE_MODES,
    _SAME_LINE_ROUTE_TARGET_LABELS,
    _PUBLICATION_CRITIQUE_WEIGHT_CONTRACT,
    _PUBLICATION_CRITIQUE_ACTION_CONTRACT,
    _QUALITY_REVISION_PLAN_STATUSES,
    _QUALITY_REVISION_ITEM_PRIORITIES,
    _QUALITY_REVISION_PRIORITY_BY_STATUS,
    _QUALITY_REVISION_DIMENSIONS,
)
from .chunk_01 import (
    _QUALITY_REVISION_ACTION_BY_DIMENSION,
    _QUALITY_REVISION_DEFAULT_ACTIONS,
    _QUALITY_REVISION_DEFAULT_DONE_CRITERIA,
    _QUALITY_REVIEW_LOOP_PHASES,
    _QUALITY_REVIEW_LOOP_PHASE_LABELS,
    _QUALITY_REVIEW_LOOP_NEXT_PHASES,
    _QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS,
    _TASK_INTAKE_REPORTING_SCOPE_HINTS,
    _TASK_INTAKE_NO_CLAIM_REOPEN_HINTS,
    _TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS,
    _TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS,
    _TASK_INTAKE_STATUS_RECHECK_HINTS,
)
from .chunk_01 import (
    _TASK_INTAKE_DISPLAY_REGISTRY_HINTS,
    _TASK_INTAKE_SHELL_INPUT_HINTS,
    stable_evaluation_summary_path,
    stable_promotion_gate_path,
    _resolve_stable_ref,
    resolve_evaluation_summary_ref,
    resolve_promotion_gate_ref,
    _required_text,
    _required_bool,
    _optional_text,
    _required_choice,
    _required_mapping,
)
from .chunk_01 import (
    _required_string_list,
    _optional_string_list,
    _same_line_route_target_label,
    _read_json_object,
    _normalize_runtime_escalation_ref,
    _normalize_gate_report,
    _build_promotion_gate_payload,
    _gap_counts,
    _recommended_action_types,
    _route_repair_plan,
    _highest_priority_gap,
    _highest_priority_action,
)
from .chunk_01 import (
    _agenda_field,
    _agenda_summary,
    _quality_review_agenda_from_summary_payload,
    _reviewer_agenda_from_quality_assessment,
    _normalized_quality_review_agenda,
    _unique_non_empty_texts,
    _task_intake_scope_texts,
    _task_intake_contains_hint,
    _format_revision_scope_targets,
)



def _task_intake_scoped_quality_agenda(summary_payload: dict[str, Any]) -> dict[str, str] | None:
    task_intake = (
        dict(summary_payload.get("task_intake") or {})
        if isinstance(summary_payload.get("task_intake"), dict)
        else None
    )
    if not isinstance(task_intake, dict):
        return None
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    if _optional_text(quality_closure_truth.get("state")) != "bundle_only_remaining" and _optional_text(
        quality_execution_lane.get("lane_id")
    ) != "submission_hardening":
        return None
    texts = _task_intake_scope_texts(task_intake)
    if not texts:
        return None
    if not _task_intake_contains_hint(texts, _TASK_INTAKE_REPORTING_SCOPE_HINTS):
        return None
    if not (
        _task_intake_contains_hint(texts, _TASK_INTAKE_NO_CLAIM_REOPEN_HINTS)
        or _task_intake_contains_hint(texts, _TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS)
        or _task_intake_contains_hint(texts, _TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS)
    ):
        return None
    revision_targets = ["reporting contract"]
    if _task_intake_contains_hint(texts, _TASK_INTAKE_DISPLAY_REGISTRY_HINTS):
        revision_targets.append("display registry")
    if _task_intake_contains_hint(texts, _TASK_INTAKE_SHELL_INPUT_HINTS):
        revision_targets.append("必需 shell/input surfaces")
    top_priority_issue = "当前任务范围已收窄到 reporting/display contract mismatch；现阶段不要重开 manuscript evidence adequacy 或 scientific claims。"
    suggested_revision = (
        f"对齐 {_format_revision_scope_targets(revision_targets)}，"
        "让 current package 与已接受展示包保持一致。"
    )
    next_review_focus = (
        "复核 medical_reporting_audit、runtime_watch 与 publication gate 状态是否已清掉 stale reporting blockers。"
        if _task_intake_contains_hint(texts, _TASK_INTAKE_STATUS_RECHECK_HINTS)
        else "复核 reporting/display contract mismatch 是否已经清零，且 current package 与 submission surfaces 保持事实一致。"
    )
    return {
        "top_priority_issue": top_priority_issue,
        "suggested_revision": suggested_revision,
        "next_review_focus": next_review_focus,
        "agenda_summary": _agenda_summary(
            top_priority_issue=top_priority_issue,
            suggested_revision=suggested_revision,
            next_review_focus=next_review_focus,
        ),
    }


def _quality_revision_plan_id(summary_payload: dict[str, Any]) -> str:
    summary_id = _optional_text(summary_payload.get("summary_id"))
    if summary_id is not None:
        return f"quality-revision-plan::{summary_id}"
    study_id = _optional_text(summary_payload.get("study_id")) or "unknown-study"
    return f"quality-revision-plan::{study_id}"


def _quality_review_loop_id(summary_payload: dict[str, Any]) -> str:
    summary_id = _optional_text(summary_payload.get("summary_id"))
    if summary_id is not None:
        return f"quality-review-loop::{summary_id}"
    study_id = _optional_text(summary_payload.get("study_id")) or "unknown-study"
    return f"quality-review-loop::{study_id}"


def _top_quality_revision_dimension(summary_payload: dict[str, Any]) -> str:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    if _optional_text(quality_closure_truth.get("state")) == "bundle_only_remaining" or _optional_text(
        quality_execution_lane.get("lane_id")
    ) == "submission_hardening":
        return "human_review_readiness"
    quality_closure_basis = (
        dict(summary_payload.get("quality_closure_basis") or {})
        if isinstance(summary_payload.get("quality_closure_basis"), dict)
        else {}
    )
    selected: tuple[tuple[int, int], str] | None = None
    for order_index, dimension in enumerate(_QUALITY_ASSESSMENT_REVIEW_ORDER):
        basis_item = quality_closure_basis.get(dimension)
        if not isinstance(basis_item, dict):
            continue
        status = _optional_text(basis_item.get("status")) or "ready"
        if status == "ready":
            continue
        marker = (_QUALITY_REVIEW_STATUS_RANK.get(status, len(_QUALITY_REVIEW_STATUS_RANK)), order_index)
        if selected is None or marker < selected[0]:
            selected = (marker, dimension)
    if selected is not None:
        return selected[1]
    return "publication_gate"


def _quality_revision_action_type(*, dimension: str, summary_payload: dict[str, Any]) -> str:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    if _optional_text(quality_closure_truth.get("state")) == "bundle_only_remaining" or _optional_text(
        quality_execution_lane.get("lane_id")
    ) == "submission_hardening":
        return "stabilize_submission_bundle"
    return _QUALITY_REVISION_ACTION_BY_DIMENSION.get(dimension, "close_evidence_gap")


def _quality_revision_route_target(summary_payload: dict[str, Any]) -> str | None:
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    route_repair_plan = (
        dict(summary_payload.get("route_repair_plan") or {})
        if isinstance(summary_payload.get("route_repair_plan"), dict)
        else {}
    )
    return _optional_text(quality_execution_lane.get("route_target")) or _optional_text(route_repair_plan.get("route_target"))


def _default_quality_revision_action(*, action_type: str, route_target: str | None) -> str:
    base_action = _QUALITY_REVISION_DEFAULT_ACTIONS.get(action_type, "继续按当前质量评估结论推进修订。")
    if route_target is None:
        return base_action
    return f"先在 {route_target} 推进：{base_action}"


def _quality_revision_done_criteria(*, next_review_focus: str | None, action_type: str) -> str:
    if next_review_focus is not None:
        return f"下一轮复评能够明确确认：{next_review_focus}"
    return _QUALITY_REVISION_DEFAULT_DONE_CRITERIA.get(action_type, "当前质量缺口形成可复核闭环。")


def _quality_revision_item_priority(*, status: str | None, is_top_priority: bool) -> str:
    if is_top_priority:
        return "p0"
    if status is None:
        return "p1"
    return _QUALITY_REVISION_PRIORITY_BY_STATUS.get(status, "p1")


def _quality_revision_item(
    *,
    item_id: str,
    dimension: str,
    action_type: str,
    action: str,
    rationale: str,
    done_criteria: str,
    priority: str,
    route_target: str | None,
) -> dict[str, Any]:
    item = {
        "item_id": item_id,
        "priority": priority,
        "dimension": dimension,
        "action_type": action_type,
        "action": action,
        "rationale": rationale,
        "done_criteria": done_criteria,
    }
    if route_target is not None:
        item["route_target"] = route_target
    return item


def _quality_revision_plan_from_summary_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    agenda = _normalized_quality_review_agenda(
        agenda_payload=(
            dict(summary_payload.get("quality_review_agenda") or {})
            if isinstance(summary_payload.get("quality_review_agenda"), dict)
            else None
        ),
        summary_payload=summary_payload,
    )
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_closure_basis = (
        dict(summary_payload.get("quality_closure_basis") or {})
        if isinstance(summary_payload.get("quality_closure_basis"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    lane_id = _optional_text(quality_execution_lane.get("lane_id"))
    dimension = _top_quality_revision_dimension(summary_payload)
    basis_item = dict(quality_closure_basis.get(dimension) or {})
    status = _optional_text(basis_item.get("status"))
    action_type = _quality_revision_action_type(dimension=dimension, summary_payload=summary_payload)
    route_target = _quality_revision_route_target(summary_payload)
    lane_specific_action = (
        f"先在 {route_target} 修订，完成当前最小投稿包收口。"
        if route_target is not None
        and (_optional_text(quality_closure_truth.get("state")) == "bundle_only_remaining" or lane_id == "submission_hardening")
        else None
    )
    next_review_focus = (
        _optional_text(quality_execution_lane.get("route_key_question"))
        if _optional_text(quality_closure_truth.get("state")) == "bundle_only_remaining" or lane_id == "submission_hardening"
        else _optional_text(agenda.get("next_review_focus"))
    ) or _optional_text(agenda.get("next_review_focus"))
    rationale = (
        _optional_text(quality_closure_truth.get("summary"))
        if _optional_text(quality_closure_truth.get("state")) == "bundle_only_remaining" or lane_id == "submission_hardening"
        else None
    ) or _optional_text(agenda.get("top_priority_issue")) or _optional_text(basis_item.get("summary")) or _optional_text(
        quality_closure_truth.get("summary")
    )
    return {
        "policy_id": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
        "plan_id": _quality_revision_plan_id(summary_payload),
        "execution_status": "planned",
        "overall_diagnosis": (
            _optional_text(quality_closure_truth.get("summary"))
            or _optional_text(summary_payload.get("verdict_summary"))
            or "当前论文线仍有质量修订任务待完成。"
        ),
        "weight_contract": dict(_PUBLICATION_CRITIQUE_WEIGHT_CONTRACT),
        "items": [
            _quality_revision_item(
                item_id="quality-revision-item-1",
                priority=_quality_revision_item_priority(status=status, is_top_priority=True),
                dimension=dimension,
                action_type=action_type,
                route_target=route_target,
                action=lane_specific_action
                or _optional_text(agenda.get("suggested_revision"))
                or _default_quality_revision_action(action_type=action_type, route_target=route_target),
                rationale=rationale or "当前质量缺口仍未闭环。",
                done_criteria=_quality_revision_done_criteria(
                    next_review_focus=next_review_focus,
                    action_type=action_type,
                ),
            )
        ],
        "next_review_focus": _unique_non_empty_texts(
            next_review_focus,
            quality_execution_lane.get("route_key_question"),
        ),
    }


def _quality_revision_candidates(
    *,
    publication_eval: dict[str, Any],
    summary_payload: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    quality_assessment = (
        dict(publication_eval.get("quality_assessment") or {})
        if isinstance(publication_eval.get("quality_assessment"), dict)
        else {}
    )
    agenda = _normalized_quality_review_agenda(
        agenda_payload=(
            dict(summary_payload.get("quality_review_agenda") or {})
            if isinstance(summary_payload.get("quality_review_agenda"), dict)
            else None
        ),
        summary_payload=summary_payload,
    )
    top_dimension = _top_quality_revision_dimension(summary_payload)
    route_target = _quality_revision_route_target(summary_payload)
    candidates: list[tuple[tuple[int, int, int], dict[str, Any], str | None]] = []
    for order_index, dimension in enumerate(_QUALITY_ASSESSMENT_REVIEW_ORDER):
        payload = quality_assessment.get(dimension)
        if not isinstance(payload, dict):
            continue
        status = _optional_text(payload.get("status")) or "partial"
        if status == "ready":
            continue
        reviewer_reason = _optional_text(payload.get("reviewer_reason"))
        reviewer_advice = _optional_text(payload.get("reviewer_revision_advice"))
        reviewer_focus = _optional_text(payload.get("reviewer_next_round_focus"))
        if reviewer_reason is None and reviewer_advice is None and reviewer_focus is None:
            continue
        is_top_priority = dimension == top_dimension
        action_type = _quality_revision_action_type(dimension=dimension, summary_payload=summary_payload)
        focus = reviewer_focus or (_optional_text(agenda.get("next_review_focus")) if is_top_priority else None)
        candidates.append(
            (
                (
                    0 if is_top_priority else 1,
                    _QUALITY_REVIEW_STATUS_RANK.get(status, len(_QUALITY_REVIEW_STATUS_RANK)),
                    order_index,
                ),
                _quality_revision_item(
                    item_id="",
                    priority=_quality_revision_item_priority(status=status, is_top_priority=is_top_priority),
                    dimension=dimension,
                    action_type=action_type,
                    route_target=route_target,
                    action=reviewer_advice
                    or (_optional_text(agenda.get("suggested_revision")) if is_top_priority else None)
                    or _default_quality_revision_action(action_type=action_type, route_target=route_target),
                    rationale=reviewer_reason
                    or (_optional_text(agenda.get("top_priority_issue")) if is_top_priority else None)
                    or _optional_text(payload.get("summary"))
                    or "当前质量缺口仍未闭环。",
                    done_criteria=_quality_revision_done_criteria(
                        next_review_focus=focus,
                        action_type=action_type,
                    ),
                ),
                focus,
            )
        )
    candidates.sort(key=lambda item: item[0])
    normalized: list[dict[str, Any]] = []
    focuses: list[str] = []
    for index, (_, item, focus) in enumerate(candidates, start=1):
        candidate = dict(item)
        candidate["item_id"] = f"quality-revision-item-{index}"
        normalized.append(candidate)
        if focus is not None:
            focuses.append(focus)
    return normalized, focuses


def _quality_revision_plan(
    *,
    publication_eval: dict[str, Any],
    summary_payload: dict[str, Any],
) -> dict[str, Any]:
    declared_plan = (
        dict(publication_eval.get("quality_revision_plan") or {})
        if isinstance(publication_eval.get("quality_revision_plan"), dict)
        else None
    )
    derived_plan = _quality_revision_plan_from_summary_payload(summary_payload)
    reviewer_candidates, reviewer_focuses = _quality_revision_candidates(
        publication_eval=publication_eval,
        summary_payload=summary_payload,
    )
    if reviewer_candidates:
        derived_plan = {
            **derived_plan,
            "items": reviewer_candidates,
            "next_review_focus": _unique_non_empty_texts(reviewer_focuses),
        }
    return _normalized_quality_revision_plan(
        plan_payload=declared_plan if declared_plan is not None else derived_plan,
        summary_payload={**summary_payload, "quality_revision_plan": derived_plan},
    )


def _normalized_weight_contract(payload: object) -> dict[str, int]:
    if not isinstance(payload, dict):
        return dict(_PUBLICATION_CRITIQUE_WEIGHT_CONTRACT)
    contract: dict[str, int] = {}
    for field, weight in payload.items():
        if not isinstance(field, str) or not field.strip() or not isinstance(weight, int):
            raise ValueError("quality revision plan weight_contract must map non-empty strings to integers")
        contract[field.strip()] = weight
    return contract or dict(_PUBLICATION_CRITIQUE_WEIGHT_CONTRACT)


def _normalized_text_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return _unique_non_empty_texts(value)
    text = _optional_text(value)
    return [] if text is None else [text]


def _normalized_quality_revision_item(
    *,
    item_payload: dict[str, Any] | None,
    fallback_item: dict[str, Any],
    item_index: int,
) -> dict[str, Any]:
    if not isinstance(item_payload, dict):
        return dict(fallback_item)
    item_id = _optional_text(item_payload.get("item_id")) or fallback_item["item_id"] or f"quality-revision-item-{item_index}"
    priority = _optional_text(item_payload.get("priority")) or fallback_item["priority"]
    if priority not in _QUALITY_REVISION_ITEM_PRIORITIES:
        allowed = ", ".join(sorted(_QUALITY_REVISION_ITEM_PRIORITIES))
        raise ValueError(f"quality revision plan item priority must be one of: {allowed}")
    dimension = (
        _optional_text(item_payload.get("dimension"))
        or _optional_text(item_payload.get("quality_dimension"))
        or fallback_item["dimension"]
    )
    if dimension not in _QUALITY_REVISION_DIMENSIONS:
        allowed = ", ".join(sorted(_QUALITY_REVISION_DIMENSIONS))
        raise ValueError(f"quality revision plan item dimension must be one of: {allowed}")
    action_type = _optional_text(item_payload.get("action_type")) or fallback_item["action_type"]
    if action_type not in _PUBLICATION_CRITIQUE_ACTION_CONTRACT:
        allowed = ", ".join(sorted(_PUBLICATION_CRITIQUE_ACTION_CONTRACT))
        raise ValueError(f"quality revision plan item action_type must be one of: {allowed}")
    action = (
        _optional_text(item_payload.get("action"))
        or _optional_text(item_payload.get("suggested_revision"))
        or fallback_item["action"]
    )
    rationale = _optional_text(item_payload.get("rationale")) or _optional_text(item_payload.get("reason")) or fallback_item["rationale"]
    done_criteria = _optional_text(item_payload.get("done_criteria")) or fallback_item["done_criteria"]
    route_target = _optional_text(item_payload.get("route_target")) or _optional_text(fallback_item.get("route_target"))
    return _quality_revision_item(
        item_id=item_id,
        priority=priority,
        dimension=dimension,
        action_type=action_type,
        route_target=route_target,
        action=action,
        rationale=rationale,
        done_criteria=done_criteria,
    )


def _normalized_quality_revision_plan(
    *,
    plan_payload: dict[str, Any] | None,
    summary_payload: dict[str, Any],
) -> dict[str, Any]:
    fallback = _quality_revision_plan_from_summary_payload(summary_payload)
    scoped_agenda = _task_intake_scoped_quality_agenda(summary_payload)
    if scoped_agenda is not None:
        scoped_items = [dict(item) for item in fallback["items"]]
        if scoped_items:
            scoped_items[0] = {
                **scoped_items[0],
                "action": scoped_agenda["suggested_revision"],
                "rationale": scoped_agenda["top_priority_issue"],
                "done_criteria": f"下一轮复评能够明确确认：{scoped_agenda['next_review_focus']}",
            }
        if not isinstance(plan_payload, dict):
            return {
                **fallback,
                "items": scoped_items,
                "next_review_focus": [scoped_agenda["next_review_focus"]],
            }
        execution_status = _optional_text(plan_payload.get("execution_status")) or fallback["execution_status"]
        if execution_status not in _QUALITY_REVISION_PLAN_STATUSES:
            allowed = ", ".join(sorted(_QUALITY_REVISION_PLAN_STATUSES))
            raise ValueError(f"quality revision plan execution_status must be one of: {allowed}")
        return {
            "policy_id": _optional_text(plan_payload.get("policy_id")) or fallback["policy_id"],
            "plan_id": (
                _optional_text(plan_payload.get("plan_id"))
                or _optional_text(plan_payload.get("revision_plan_id"))
                or fallback["plan_id"]
            ),
            "execution_status": execution_status,
            "overall_diagnosis": fallback["overall_diagnosis"],
            "weight_contract": _normalized_weight_contract(plan_payload.get("weight_contract")),
            "items": scoped_items,
            "next_review_focus": [scoped_agenda["next_review_focus"]],
        }
    if not isinstance(plan_payload, dict):
        return fallback
    execution_status = _optional_text(plan_payload.get("execution_status")) or fallback["execution_status"]
    if execution_status not in _QUALITY_REVISION_PLAN_STATUSES:
        allowed = ", ".join(sorted(_QUALITY_REVISION_PLAN_STATUSES))
        raise ValueError(f"quality revision plan execution_status must be one of: {allowed}")
    fallback_items = [dict(item) for item in fallback["items"]]
    raw_items = plan_payload.get("items")
    if raw_items is None:
        normalized_items = fallback_items
    else:
        if not isinstance(raw_items, list):
            raise ValueError("quality revision plan items must be a list")
        if not raw_items:
            normalized_items = fallback_items
        else:
            normalized_items = []
            for index, item in enumerate(raw_items, start=1):
                fallback_item = fallback_items[min(index - 1, len(fallback_items) - 1)]
                normalized_items.append(
                    _normalized_quality_revision_item(
                        item_payload=item if isinstance(item, dict) else None,
                        fallback_item=fallback_item,
                        item_index=index,
                    )
                )
    return {
        "policy_id": _optional_text(plan_payload.get("policy_id")) or fallback["policy_id"],
        "plan_id": _optional_text(plan_payload.get("plan_id")) or _optional_text(plan_payload.get("revision_plan_id")) or fallback["plan_id"],
        "execution_status": execution_status,
        "overall_diagnosis": _optional_text(plan_payload.get("overall_diagnosis")) or fallback["overall_diagnosis"],
        "weight_contract": _normalized_weight_contract(plan_payload.get("weight_contract")),
        "items": normalized_items,
        "next_review_focus": (
            _unique_non_empty_texts(_normalized_text_list(plan_payload.get("next_review_focus")))
            if _normalized_text_list(plan_payload.get("next_review_focus"))
            else list(fallback["next_review_focus"])
        ),
    }


def _quality_review_loop_phase(*, summary_payload: dict[str, Any]) -> tuple[str, str]:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_revision_plan = (
        dict(summary_payload.get("quality_revision_plan") or {})
        if isinstance(summary_payload.get("quality_revision_plan"), dict)
        else {}
    )
    closure_state = _optional_text(quality_closure_truth.get("state")) or "quality_repair_required"
    execution_status = _optional_text(quality_revision_plan.get("execution_status")) or "planned"
    if closure_state == "write_line_ready":
        return "write_continuation", "write"
    if closure_state == "bundle_only_remaining":
        if execution_status == "completed":
            return "re_review_required", "re_review"
        return "bundle_hardening", "finalize"
    if execution_status == "completed":
        return "re_review_required", "re_review"
    if execution_status == "in_progress":
        return "revision_in_progress", "revision"
    return "revision_required", "revision"


def _quality_review_loop_blocking_issues(summary_payload: dict[str, Any]) -> list[str]:
    quality_revision_plan = (
        dict(summary_payload.get("quality_revision_plan") or {})
        if isinstance(summary_payload.get("quality_revision_plan"), dict)
        else {}
    )
    issues = _unique_non_empty_texts(
        [dict(item).get("rationale") for item in (quality_revision_plan.get("items") or []) if isinstance(item, dict)],
    )
    if issues:
        return issues
    quality_review_agenda = (
        dict(summary_payload.get("quality_review_agenda") or {})
        if isinstance(summary_payload.get("quality_review_agenda"), dict)
        else {}
    )
    fallback = _optional_text(quality_review_agenda.get("top_priority_issue"))
    return [] if fallback is None else [fallback]


def _quality_review_loop_summary(*, current_phase: str) -> str:
    if current_phase == "revision_required":
        return "当前已经形成结构化质量修订计划，下一步应先执行修订，再回到 MAS 做复评。"
    if current_phase == "revision_in_progress":
        return "当前质量修订正在推进，完成后应由 MAS 发起下一轮复评。"
    if current_phase == "re_review_required":
        return "当前修订计划已完成，下一步应由 MAS 发起 re-review，重新判断 blocking issues 是否真正闭环。"
    if current_phase == "write_continuation":
        return "核心科学质量已经到可继续写作收口的状态，当前应继续同线写作推进。"
    return "核心科学质量已经闭环，当前只剩投稿包与人工审阅面的收口修订。"


def _quality_review_loop_recommended_next_action(*, current_phase: str, summary_payload: dict[str, Any]) -> str:
    if current_phase == "re_review_required":
        return "发起下一轮 MAS quality re-review，确认当前 blocking issues 是否已真正闭环。"
    quality_revision_plan = (
        dict(summary_payload.get("quality_revision_plan") or {})
        if isinstance(summary_payload.get("quality_revision_plan"), dict)
        else {}
    )
    plan_items = [dict(item) for item in (quality_revision_plan.get("items") or []) if isinstance(item, dict)]
    first_action = _optional_text((plan_items[0] or {}).get("action")) if plan_items else None
    if first_action is not None:
        return first_action
    quality_review_agenda = (
        dict(summary_payload.get("quality_review_agenda") or {})
        if isinstance(summary_payload.get("quality_review_agenda"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    return (
        _optional_text(quality_review_agenda.get("suggested_revision"))
        or _optional_text(quality_execution_lane.get("summary"))
        or "继续按当前质量评估结论推进。"
    )


def _quality_review_loop_from_summary_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    quality_revision_plan = _normalized_quality_revision_plan(
        plan_payload=(
            dict(summary_payload.get("quality_revision_plan") or {})
            if isinstance(summary_payload.get("quality_revision_plan"), dict)
            else None
        ),
        summary_payload=summary_payload,
    )
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), dict)
        else {}
    )
    current_phase, recommended_next_phase = _quality_review_loop_phase(
        summary_payload={**summary_payload, "quality_revision_plan": quality_revision_plan}
    )
    blocking_issues = _quality_review_loop_blocking_issues(
        {**summary_payload, "quality_revision_plan": quality_revision_plan}
    )
    return {
        "policy_id": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
        "loop_id": _quality_review_loop_id(summary_payload),
        "closure_state": _optional_text(quality_closure_truth.get("state")) or "quality_repair_required",
        "lane_id": _optional_text(quality_execution_lane.get("lane_id")) or "general_quality_repair",
        "current_phase": current_phase,
        "current_phase_label": _QUALITY_REVIEW_LOOP_PHASE_LABELS[current_phase],
        "recommended_next_phase": recommended_next_phase,
        "recommended_next_phase_label": _QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS[recommended_next_phase],
        "active_plan_id": _optional_text(quality_revision_plan.get("plan_id"))
        or _quality_revision_plan_id(summary_payload),
        "active_plan_execution_status": _optional_text(quality_revision_plan.get("execution_status")) or "planned",
        "blocking_issue_count": len(blocking_issues),
        "blocking_issues": blocking_issues,
        "next_review_focus": list(quality_revision_plan.get("next_review_focus") or []),
        "re_review_ready": current_phase == "re_review_required",
        "summary": _quality_review_loop_summary(current_phase=current_phase),
        "recommended_next_action": _quality_review_loop_recommended_next_action(
            current_phase=current_phase,
            summary_payload={**summary_payload, "quality_revision_plan": quality_revision_plan},
        ),
    }
