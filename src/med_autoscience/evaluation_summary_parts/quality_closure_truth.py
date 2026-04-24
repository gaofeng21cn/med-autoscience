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

from .refs_and_validation import (
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
from .refs_and_validation import (
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
from .refs_and_validation import (
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
from .refs_and_validation import (
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
from .refs_and_validation import (
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
from .refs_and_validation import (
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
from .quality_revision_plan import (
    _task_intake_scoped_quality_agenda,
    _quality_revision_plan_id,
    _quality_review_loop_id,
    _top_quality_revision_dimension,
    _quality_revision_action_type,
    _quality_revision_route_target,
    _default_quality_revision_action,
    _quality_revision_done_criteria,
    _quality_revision_item_priority,
    _quality_revision_item,
    _quality_revision_plan_from_summary_payload,
    _quality_revision_candidates,
)
from .quality_revision_plan import (
    _quality_revision_plan,
    _normalized_weight_contract,
    _normalized_text_list,
    _normalized_quality_revision_item,
    _normalized_quality_revision_plan,
    _quality_review_loop_phase,
    _quality_review_loop_blocking_issues,
    _quality_review_loop_summary,
    _quality_review_loop_recommended_next_action,
    _quality_review_loop_from_summary_payload,
)



def _quality_execution_lane_from_summary_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    route_repair_plan = (
        dict(summary_payload.get("route_repair_plan") or {})
        if isinstance(summary_payload.get("route_repair_plan"), dict)
        else {}
    )
    current_required_action = _optional_text(quality_closure_truth.get("current_required_action")) or "return_to_publishability_gate"
    closure_state = _optional_text(quality_closure_truth.get("state")) or "quality_repair_required"
    route_target = _optional_text(route_repair_plan.get("route_target")) or _optional_text(quality_closure_truth.get("route_target"))
    route_key_question = _optional_text(route_repair_plan.get("route_key_question"))
    route_rationale = (
        _optional_text(route_repair_plan.get("route_rationale"))
        or _optional_text(quality_closure_truth.get("summary"))
        or _optional_text(summary_payload.get("verdict_summary"))
        or "当前应先收口现有论文质量缺口。"
    )
    action_type = _optional_text(route_repair_plan.get("action_type"))

    if action_type == "bounded_analysis" or route_target == "analysis-campaign":
        lane_id = "claim_evidence"
    elif closure_state == "bundle_only_remaining" or current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}:
        lane_id = "submission_hardening"
    elif current_required_action == "continue_write_stage" or route_target == "write":
        lane_id = "write_ready"
    else:
        lane_id = "general_quality_repair"

    lane_label = _QUALITY_EXECUTION_LANE_LABELS[lane_id]
    repair_mode = (
        "bounded_analysis"
        if action_type == "bounded_analysis"
        else "same_line_route_back"
        if route_target is not None
        else None
    )

    if lane_id == "submission_hardening":
        route_target = "finalize"
        route_key_question = "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
        repair_mode = "same_line_route_back"

    if lane_id == "submission_hardening":
        summary = f"当前质量执行线聚焦{lane_label}；先回到定稿与投稿收尾，回答“{route_key_question}”。"
    elif route_target and route_key_question:
        verb = "进入" if repair_mode == "bounded_analysis" else "回到"
        summary = f"当前质量执行线聚焦 {lane_label}；先{verb} {route_target}，回答“{route_key_question}”。"
    elif route_target:
        verb = "进入" if repair_mode == "bounded_analysis" else "回到"
        summary = f"当前质量执行线聚焦 {lane_label}；先{verb} {route_target} 收口当前缺口。"
    elif current_required_action == "continue_write_stage":
        summary = "当前质量执行线已经进入同线写作推进；核心科学面允许继续往写作收口。"
    else:
        summary = f"当前质量执行线聚焦 {lane_label}；应先收口当前质量缺口。"

    return {
        "lane_id": lane_id,
        "lane_label": lane_label,
        "repair_mode": repair_mode,
        "route_target": route_target or None,
        "route_key_question": route_key_question or None,
        "summary": summary,
        "why_now": route_rationale,
    }


def _normalized_quality_execution_lane_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    raw_lane = summary_payload.get("quality_execution_lane")
    if isinstance(raw_lane, dict):
        return dict(raw_lane)
    try:
        return _quality_execution_lane_from_summary_payload(summary_payload)
    except (TypeError, ValueError):
        return {}


def _same_line_route_surface_from_summary_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    quality_execution_lane = _normalized_quality_execution_lane_payload(summary_payload)
    repair_mode = _optional_text(quality_execution_lane.get("repair_mode"))
    route_target = _optional_text(quality_execution_lane.get("route_target"))
    if repair_mode != "same_line_route_back" or route_target not in _SAME_LINE_ROUTE_TARGET_LABELS:
        return {}
    route_key_question = _optional_text(quality_execution_lane.get("route_key_question"))
    if route_key_question is None:
        return {}
    return {
        "surface_kind": "same_line_route_surface",
        "lane_id": _optional_text(quality_execution_lane.get("lane_id")) or "general_quality_repair",
        "repair_mode": repair_mode,
        "route_target": route_target,
        "route_target_label": _SAME_LINE_ROUTE_TARGET_LABELS[route_target],
        "route_key_question": route_key_question,
        "summary": _optional_text(quality_execution_lane.get("summary"))
        or f"当前已经收窄到同线 {route_target} 收口。",
        "why_now": _optional_text(quality_execution_lane.get("why_now"))
        or _optional_text(quality_closure_truth.get("summary"))
        or "当前应沿同一论文线继续收口。",
        "current_required_action": _optional_text(quality_closure_truth.get("current_required_action"))
        or "return_to_publishability_gate",
        "closure_state": _optional_text(quality_closure_truth.get("state")) or "quality_repair_required",
    }


def _normalized_same_line_route_surface_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    raw_surface = summary_payload.get("same_line_route_surface")
    if isinstance(raw_surface, dict):
        return dict(raw_surface)
    return _same_line_route_surface_from_summary_payload(summary_payload)


def _normalized_same_line_route_truth_payload(summary_payload: dict[str, Any]) -> dict[str, Any]:
    raw_truth = summary_payload.get("same_line_route_truth")
    if isinstance(raw_truth, dict):
        return dict(raw_truth)
    return build_same_line_route_truth(
        quality_closure_truth=(
            dict(summary_payload.get("quality_closure_truth") or {})
            if isinstance(summary_payload.get("quality_closure_truth"), dict)
            else {}
        ),
        quality_execution_lane=_normalized_quality_execution_lane_payload(summary_payload),
    )


def _normalized_quality_review_loop(
    *,
    loop_payload: dict[str, Any] | None,
    summary_payload: dict[str, Any],
) -> dict[str, Any]:
    fallback = _quality_review_loop_from_summary_payload(summary_payload)
    scoped_agenda = _task_intake_scoped_quality_agenda(summary_payload)
    if scoped_agenda is not None:
        if not isinstance(loop_payload, dict):
            return fallback
        return {
            "policy_id": _optional_text(loop_payload.get("policy_id")) or fallback["policy_id"],
            "loop_id": _optional_text(loop_payload.get("loop_id")) or fallback["loop_id"],
            "closure_state": fallback["closure_state"],
            "lane_id": fallback["lane_id"],
            "current_phase": fallback["current_phase"],
            "current_phase_label": fallback["current_phase_label"],
            "recommended_next_phase": fallback["recommended_next_phase"],
            "recommended_next_phase_label": fallback["recommended_next_phase_label"],
            "active_plan_id": _optional_text(loop_payload.get("active_plan_id")) or fallback["active_plan_id"],
            "active_plan_execution_status": fallback["active_plan_execution_status"],
            "blocking_issue_count": fallback["blocking_issue_count"],
            "blocking_issues": list(fallback["blocking_issues"]),
            "next_review_focus": list(fallback["next_review_focus"]),
            "re_review_ready": fallback["re_review_ready"],
            "summary": fallback["summary"],
            "recommended_next_action": fallback["recommended_next_action"],
        }
    if not isinstance(loop_payload, dict):
        return fallback
    current_phase = _optional_text(loop_payload.get("current_phase")) or fallback["current_phase"]
    if current_phase not in _QUALITY_REVIEW_LOOP_PHASES:
        allowed = ", ".join(sorted(_QUALITY_REVIEW_LOOP_PHASES))
        raise ValueError(f"quality review loop current_phase must be one of: {allowed}")
    recommended_next_phase = (
        _optional_text(loop_payload.get("recommended_next_phase")) or fallback["recommended_next_phase"]
    )
    if recommended_next_phase not in _QUALITY_REVIEW_LOOP_NEXT_PHASES:
        allowed = ", ".join(sorted(_QUALITY_REVIEW_LOOP_NEXT_PHASES))
        raise ValueError(f"quality review loop recommended_next_phase must be one of: {allowed}")
    closure_state = _optional_text(loop_payload.get("closure_state")) or fallback["closure_state"]
    if closure_state not in _QUALITY_CLOSURE_STATES:
        allowed = ", ".join(sorted(_QUALITY_CLOSURE_STATES))
        raise ValueError(f"quality review loop closure_state must be one of: {allowed}")
    active_plan_execution_status = (
        _optional_text(loop_payload.get("active_plan_execution_status")) or fallback["active_plan_execution_status"]
    )
    if active_plan_execution_status not in _QUALITY_REVISION_PLAN_STATUSES:
        allowed = ", ".join(sorted(_QUALITY_REVISION_PLAN_STATUSES))
        raise ValueError(f"quality review loop active_plan_execution_status must be one of: {allowed}")
    blocking_issues = _normalized_text_list(loop_payload.get("blocking_issues"))
    if not blocking_issues:
        blocking_issues = list(fallback["blocking_issues"])
    blocking_issue_count = loop_payload.get("blocking_issue_count")
    if not isinstance(blocking_issue_count, int) or blocking_issue_count < 0:
        blocking_issue_count = len(blocking_issues)
    return {
        "policy_id": _optional_text(loop_payload.get("policy_id")) or fallback["policy_id"],
        "loop_id": _optional_text(loop_payload.get("loop_id")) or fallback["loop_id"],
        "closure_state": closure_state,
        "lane_id": _optional_text(loop_payload.get("lane_id")) or fallback["lane_id"],
        "current_phase": current_phase,
        "current_phase_label": (
            _optional_text(loop_payload.get("current_phase_label")) or _QUALITY_REVIEW_LOOP_PHASE_LABELS[current_phase]
        ),
        "recommended_next_phase": recommended_next_phase,
        "recommended_next_phase_label": (
            _optional_text(loop_payload.get("recommended_next_phase_label"))
            or _QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS[recommended_next_phase]
        ),
        "active_plan_id": _optional_text(loop_payload.get("active_plan_id")) or fallback["active_plan_id"],
        "active_plan_execution_status": active_plan_execution_status,
        "blocking_issue_count": blocking_issue_count,
        "blocking_issues": blocking_issues,
        "next_review_focus": (
            _normalized_text_list(loop_payload.get("next_review_focus"))
            or list(fallback["next_review_focus"])
        ),
        "re_review_ready": (
            loop_payload.get("re_review_ready")
            if isinstance(loop_payload.get("re_review_ready"), bool)
            else fallback["re_review_ready"]
        ),
        "summary": _optional_text(loop_payload.get("summary")) or fallback["summary"],
        "recommended_next_action": (
            _optional_text(loop_payload.get("recommended_next_action")) or fallback["recommended_next_action"]
        ),
    }


def _quality_review_agenda(
    *,
    publication_eval: dict[str, Any],
    gaps: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    route_repair_plan: dict[str, str] | None,
    quality_closure_truth: dict[str, Any],
) -> dict[str, str]:
    declared_agenda = (
        dict(publication_eval.get("quality_review_agenda") or {})
        if isinstance(publication_eval.get("quality_review_agenda"), dict)
        else None
    )
    reviewer_agenda = _reviewer_agenda_from_quality_assessment(publication_eval)
    priority_gap = _highest_priority_gap(gaps)
    if reviewer_agenda["top_priority_issue"]:
        top_priority_issue = reviewer_agenda["top_priority_issue"]
    elif priority_gap is not None:
        severity = priority_gap["severity"]
        severity_label = _GAP_SEVERITY_LABELS.get(severity, severity)
        top_priority_issue = f"{severity_label}：{priority_gap['summary']}"
    else:
        top_priority_issue = (
            _optional_text(quality_closure_truth.get("summary"))
            or _optional_text((publication_eval.get("verdict") or {}).get("summary"))
            or "当前论文线仍有质量修订任务待完成。"
        )
    priority_action = _highest_priority_action(actions)
    route_target = _optional_text((route_repair_plan or {}).get("route_target"))
    route_rationale = _optional_text((route_repair_plan or {}).get("route_rationale"))
    if reviewer_agenda["suggested_revision"]:
        suggested_revision = reviewer_agenda["suggested_revision"]
    elif priority_action is not None:
        action_route_target = _optional_text(priority_action.get("route_target"))
        action_reason = _optional_text(priority_action.get("reason"))
        if action_route_target and action_reason:
            suggested_revision = f"先在 {action_route_target} 修订：{action_reason}"
        elif action_reason:
            suggested_revision = action_reason
        elif action_route_target:
            suggested_revision = f"先在 {action_route_target} 推进当前最窄修订。"
        else:
            suggested_revision = f"优先执行 {priority_action['action_type']} 修订动作。"
    elif route_target and route_rationale:
        suggested_revision = f"先在 {route_target} 修订：{route_rationale}"
    elif route_target:
        suggested_revision = f"先在 {route_target} 推进当前最窄修订。"
    elif route_rationale:
        suggested_revision = route_rationale
    else:
        current_required_action = _optional_text(quality_closure_truth.get("current_required_action"))
        suggested_revision = (
            f"按 {current_required_action} 指令继续质量修订。"
            if current_required_action is not None
            else "继续按当前评估结论收窄修订。"
        )
    agenda_summary_payload = {
        "verdict_summary": _optional_text((publication_eval.get("verdict") or {}).get("summary")),
        "route_repair_plan": route_repair_plan,
        "quality_closure_truth": quality_closure_truth,
    }
    quality_execution_lane = _quality_execution_lane_from_summary_payload(agenda_summary_payload)
    if reviewer_agenda["next_review_focus"]:
        next_review_focus = reviewer_agenda["next_review_focus"]
    else:
        next_review_focus = (
            _optional_text(quality_execution_lane.get("route_key_question"))
            or _optional_text((route_repair_plan or {}).get("route_key_question"))
            or (
                f"复评时确认“{priority_gap['summary']}”是否已闭环，并补齐对应证据引用。"
                if priority_gap is not None
                else f"复评时确认“{top_priority_issue}”是否已经形成可复核证据闭环。"
            )
        )
    derived_agenda = {
        "top_priority_issue": top_priority_issue,
        "suggested_revision": suggested_revision,
        "next_review_focus": next_review_focus,
    }
    return _normalized_quality_review_agenda(
        agenda_payload=declared_agenda if declared_agenda is not None else derived_agenda,
        summary_payload={**agenda_summary_payload, "quality_review_agenda": derived_agenda},
    )


def _fallback_refs(*values: object) -> list[str]:
    refs: list[str] = []
    for value in values:
        text = str(value or "").strip()
        if text:
            refs.append(text)
    if not refs:
        raise ValueError("quality closure basis requires at least one evidence ref")
    return refs


def _coerce_quality_basis_item(
    *,
    payload: dict[str, Any] | None,
    fallback_status: str,
    fallback_summary: str,
    fallback_refs: list[str],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {
            "status": fallback_status,
            "summary": fallback_summary,
            "evidence_refs": list(fallback_refs),
        }
    evidence_refs = _required_string_list("quality closure basis item", "evidence_refs", payload.get("evidence_refs"))
    if not evidence_refs:
        raise ValueError("quality closure basis item evidence_refs must not be empty")
    return {
        "status": _required_choice(
            "quality closure basis item",
            "status",
            payload.get("status"),
            _QUALITY_DIMENSION_STATUSES,
        ),
        "summary": _required_text("quality closure basis item", "summary", payload.get("summary")),
        "evidence_refs": evidence_refs,
    }


def _publication_gate_quality_basis(
    *,
    promotion_gate_payload: dict[str, Any],
    promotion_gate_ref: dict[str, str],
    route_repair_plan: dict[str, str] | None,
    evidence_strength_status: str,
) -> dict[str, Any]:
    gate_ref = str(promotion_gate_ref.get("artifact_path") or "").strip()
    current_required_action = _required_text(
        "promotion gate",
        "current_required_action",
        promotion_gate_payload.get("current_required_action"),
    )
    if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"} and evidence_strength_status == "ready":
        return {
            "status": "partial",
            "summary": "核心科学面已经闭环；剩余阻塞只落在当前论文线的 finalize / bundle 收口。",
            "evidence_refs": _fallback_refs(gate_ref),
        }
    if current_required_action == "continue_write_stage" and evidence_strength_status == "ready":
        return {
            "status": "ready",
            "summary": "发表门控已经放行写作；当前论文线可以继续同线写作推进。",
            "evidence_refs": _fallback_refs(gate_ref),
        }
    route_target = str((route_repair_plan or {}).get("route_target") or "").strip()
    if route_target:
        summary = f"发表门控仍未放行当前论文线；系统应先沿 {route_target} 修复质量缺口。"
    else:
        summary = "发表门控仍未放行当前论文线；系统应先修复当前质量缺口。"
    return {
        "status": "blocked",
        "summary": summary,
        "evidence_refs": _fallback_refs(gate_ref),
    }


def _quality_closure_basis(
    *,
    study_root: Path,
    publication_eval: dict[str, Any],
    promotion_gate_ref: dict[str, str],
    promotion_gate_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
) -> dict[str, Any]:
    quality_assessment = dict(publication_eval.get("quality_assessment") or {})
    runtime_context_refs = dict(publication_eval.get("runtime_context_refs") or {})
    charter_context_ref = dict(publication_eval.get("charter_context_ref") or {})
    main_result_ref = str(runtime_context_refs.get("main_result_ref") or "").strip()
    charter_ref = str(resolve_study_charter_ref(study_root=study_root, ref=charter_context_ref.get("ref")))
    gate_ref = str(promotion_gate_ref.get("artifact_path") or "").strip()
    basis = {
        "clinical_significance": _coerce_quality_basis_item(
            payload=quality_assessment.get("clinical_significance"),
            fallback_status="underdefined",
            fallback_summary="当前 publication eval 还没有给出稳定的临床意义判断。",
            fallback_refs=_fallback_refs(charter_ref, gate_ref),
        ),
        "evidence_strength": _coerce_quality_basis_item(
            payload=quality_assessment.get("evidence_strength"),
            fallback_status="underdefined",
            fallback_summary="当前 publication eval 还没有给出稳定的证据强度判断。",
            fallback_refs=_fallback_refs(main_result_ref, gate_ref),
        ),
        "novelty_positioning": _coerce_quality_basis_item(
            payload=quality_assessment.get("novelty_positioning"),
            fallback_status="underdefined",
            fallback_summary="当前 publication eval 还没有给出稳定的创新性定位判断。",
            fallback_refs=_fallback_refs(charter_ref),
        ),
        "human_review_readiness": _coerce_quality_basis_item(
            payload=quality_assessment.get("human_review_readiness"),
            fallback_status="underdefined",
            fallback_summary="当前 publication eval 还没有给出稳定的人工审阅准备度判断。",
            fallback_refs=_fallback_refs(gate_ref),
        ),
    }
    basis["publication_gate"] = _publication_gate_quality_basis(
        promotion_gate_payload=promotion_gate_payload,
        promotion_gate_ref=promotion_gate_ref,
        route_repair_plan=route_repair_plan,
        evidence_strength_status=str(basis["evidence_strength"]["status"]),
    )
    return basis


def _quality_closure_truth(
    *,
    promotion_gate_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
    quality_closure_basis: dict[str, Any],
) -> dict[str, Any]:
    return derive_quality_closure_truth(
        promotion_gate_payload=promotion_gate_payload,
        route_repair_plan=route_repair_plan,
        quality_closure_basis=quality_closure_basis,
    )


def _quality_execution_lane(
    *,
    promotion_gate_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
) -> dict[str, Any]:
    return derive_quality_execution_lane(
        promotion_gate_payload=promotion_gate_payload,
        route_repair_plan=route_repair_plan,
    )


def _load_review_ledger_context(
    publication_eval: dict[str, Any],
) -> tuple[dict[str, Any] | None, str | None]:
    delivery_context_refs = (
        dict(publication_eval.get("delivery_context_refs") or {})
        if isinstance(publication_eval.get("delivery_context_refs"), dict)
        else {}
    )
    paper_root_ref = _optional_text(delivery_context_refs.get("paper_root_ref"))
    if paper_root_ref is None:
        return None, None
    review_ledger_path = Path(paper_root_ref).expanduser().resolve() / "review" / "review_ledger.json"
    if not review_ledger_path.exists():
        return None, str(review_ledger_path)
    return _read_json_object(review_ledger_path, label="review ledger"), str(review_ledger_path)


def _study_quality_truth_from_summary_payload(
    *,
    study_root: Path,
    summary_payload: dict[str, Any],
    quality_closure_truth: dict[str, Any],
    quality_closure_basis: dict[str, Any],
    quality_execution_lane: dict[str, Any],
) -> dict[str, Any]:
    publication_eval = read_publication_eval_latest(study_root=study_root)
    charter_payload = read_study_charter(study_root=study_root)
    review_ledger_payload, review_ledger_path = _load_review_ledger_context(publication_eval)
    route_repair_plan = (
        dict(summary_payload.get("route_repair_plan") or {})
        if isinstance(summary_payload.get("route_repair_plan"), dict)
        else None
    )
    return build_study_quality_truth(
        study_id=_required_text("evaluation summary", "study_id", summary_payload.get("study_id")),
        charter_payload=charter_payload,
        publication_eval=publication_eval,
        promotion_gate_payload=dict(summary_payload.get("promotion_gate_status") or {}),
        route_repair_plan=route_repair_plan,
        quality_closure_truth=quality_closure_truth,
        quality_closure_basis=quality_closure_basis,
        quality_execution_lane=quality_execution_lane,
        review_ledger_payload=review_ledger_payload,
        review_ledger_path=review_ledger_path,
    )


def build_same_line_route_truth(
    *,
    quality_closure_truth: dict[str, Any] | None,
    quality_execution_lane: dict[str, Any] | None,
) -> dict[str, Any]:
    closure_truth = dict(quality_closure_truth or {})
    execution_lane = dict(quality_execution_lane or {})
    if not closure_truth and not execution_lane:
        return {}

    closure_state = _optional_text(closure_truth.get("state"))
    lane_id = _optional_text(execution_lane.get("lane_id"))
    repair_mode = _optional_text(execution_lane.get("repair_mode"))
    route_target = _optional_text(execution_lane.get("route_target")) or _optional_text(closure_truth.get("route_target"))
    route_key_question = _optional_text(execution_lane.get("route_key_question"))
    lane_summary = _optional_text(execution_lane.get("summary"))

    if lane_id == "submission_hardening" or closure_state == "bundle_only_remaining":
        same_line_state = "finalize_only_remaining"
        route_mode = "return"
        route_target = "finalize"
        summary = "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。"
    elif lane_id == "write_ready" or closure_state == "write_line_ready" or route_target == "write":
        same_line_state = "write_continuation"
        route_mode = "continue"
        route_target = "write"
        summary = "当前同线路由已经进入写作收口；可以沿当前论文线继续推进写作与有限补充。"
    elif repair_mode == "bounded_analysis" or route_target == "analysis-campaign":
        same_line_state = "bounded_analysis"
        route_mode = "enter"
        summary = (
            f"当前论文线仍在同线质量修复；先进入 {route_target or 'analysis-campaign'} 收口当前最窄缺口。"
        )
    elif route_target is not None:
        same_line_state = "same_line_route_back"
        route_mode = "return"
        summary = f"当前论文线仍在同线质量修复；先回到 {route_target} 收口当前最窄缺口。"
    else:
        same_line_state = "quality_repair_pending"
        route_mode = None
        summary = lane_summary or _optional_text(closure_truth.get("summary")) or "当前论文线仍有待收口的质量修复。"

    current_focus = route_key_question or lane_summary or _optional_text(closure_truth.get("summary")) or summary
    return {
        "surface_kind": "same_line_route_truth",
        "same_line_state": same_line_state,
        "same_line_state_label": _SAME_LINE_ROUTE_STATE_LABELS[same_line_state],
        "route_mode": route_mode,
        "route_target": route_target or None,
        "route_target_label": _same_line_route_target_label(route_target),
        "summary": summary,
        "current_focus": current_focus,
    }
