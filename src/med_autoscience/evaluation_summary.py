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

__all__ = [
    "STABLE_EVALUATION_SUMMARY_RELATIVE_PATH",
    "STABLE_PROMOTION_GATE_RELATIVE_PATH",
    "build_same_line_route_truth",
    "materialize_evaluation_summary_artifacts",
    "read_evaluation_summary",
    "read_promotion_gate",
    "resolve_evaluation_summary_ref",
    "resolve_promotion_gate_ref",
    "stable_evaluation_summary_path",
    "stable_promotion_gate_path",
]


STABLE_EVALUATION_SUMMARY_RELATIVE_PATH = Path("artifacts/eval_hygiene/evaluation_summary/latest.json")
STABLE_PROMOTION_GATE_RELATIVE_PATH = Path("artifacts/eval_hygiene/promotion_gate/latest.json")
_GAP_SEVERITIES = ("must_fix", "important", "optional")
_GAP_SEVERITY_RANK = {severity: index for index, severity in enumerate(_GAP_SEVERITIES)}
_GAP_SEVERITY_LABELS = {
    "must_fix": "必须优先修复",
    "important": "重要修订项",
    "optional": "可选优化项",
}
_ACTION_PRIORITY_RANK = {"now": 0, "next": 1}
_ROUTE_REPAIR_ACTION_TYPES = {"continue_same_line", "route_back_same_line", "bounded_analysis"}
_QUALITY_DIMENSION_STATUSES = frozenset({"ready", "partial", "blocked", "underdefined"})
_QUALITY_CLOSURE_STATES = frozenset({"quality_repair_required", "write_line_ready", "bundle_only_remaining"})
_QUALITY_CLOSURE_BASIS_KEYS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "human_review_readiness",
    "publication_gate",
)
_QUALITY_REVIEW_STATUS_RANK = {"blocked": 0, "underdefined": 1, "partial": 2, "ready": 3}
_QUALITY_ASSESSMENT_REVIEW_ORDER = (
    "evidence_strength",
    "human_review_readiness",
    "clinical_significance",
    "novelty_positioning",
)
_QUALITY_EXECUTION_LANE_LABELS = {
    "reviewer_first": "reviewer-first 收口",
    "claim_evidence": "claim-evidence 修复",
    "submission_hardening": "投稿包硬化收口",
    "write_ready": "同线写作推进",
    "general_quality_repair": "质量修复",
}
_SAME_LINE_ROUTE_STATES = frozenset(
    {
        "quality_repair_pending",
        "same_line_route_back",
        "bounded_analysis",
        "write_continuation",
        "finalize_only_remaining",
    }
)
_SAME_LINE_ROUTE_STATE_LABELS = {
    "quality_repair_pending": "同线质量修复待定",
    "same_line_route_back": "同线质量修复",
    "bounded_analysis": "有限补充分析",
    "write_continuation": "同线写作推进",
    "finalize_only_remaining": "同线定稿与投稿包收尾",
}
_SAME_LINE_ROUTE_MODES = frozenset({"return", "enter", "continue"})
_SAME_LINE_ROUTE_TARGET_LABELS = {
    "analysis-campaign": "补充分析与稳健性验证",
    "write": "论文写作与结果收紧",
    "finalize": "定稿与投稿收尾",
}
_PUBLICATION_CRITIQUE_WEIGHT_CONTRACT = build_publication_critique_weight_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
_PUBLICATION_CRITIQUE_ACTION_CONTRACT = frozenset(build_revision_action_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY))
_QUALITY_REVISION_PLAN_STATUSES = frozenset({"planned", "in_progress", "completed"})
_QUALITY_REVISION_ITEM_PRIORITIES = frozenset({"p0", "p1", "p2"})
_QUALITY_REVISION_PRIORITY_BY_STATUS = {
    "blocked": "p0",
    "underdefined": "p1",
    "partial": "p2",
}
_QUALITY_REVISION_DIMENSIONS = frozenset((*_QUALITY_ASSESSMENT_REVIEW_ORDER, "publication_gate"))
_QUALITY_REVISION_ACTION_BY_DIMENSION = {
    "clinical_significance": "tighten_clinical_framing",
    "evidence_strength": "close_evidence_gap",
    "novelty_positioning": "tighten_novelty_framing",
    "human_review_readiness": "refresh_review_surface",
    "publication_gate": "refresh_review_surface",
}
_QUALITY_REVISION_DEFAULT_ACTIONS = {
    "tighten_clinical_framing": "收紧临床 framing，让研究问题、结论边界和临床落点保持一致。",
    "close_evidence_gap": "补齐当前主结论对应的证据缺口，并把证据闭环写回稿件主面。",
    "tighten_novelty_framing": "收紧创新点和贡献边界，避免把解释层写成过度主张。",
    "refresh_review_surface": "清理稿面与 figure/table surface，让稿件达到医学论文可审阅状态。",
    "stabilize_submission_bundle": "刷新 docx/pdf 与最小投稿包，保证给人看的投稿面和源稿一致。",
}
_QUALITY_REVISION_DEFAULT_DONE_CRITERIA = {
    "tighten_clinical_framing": "临床问题、结论边界和适用场景表述一致，并能被稿件证据直接支撑。",
    "close_evidence_gap": "主结论对应的 claim-to-evidence 缺口补齐，且关键证据可逐条复核。",
    "tighten_novelty_framing": "创新点、贡献边界和已有工作差异表述清楚，且不会越出当前证据面。",
    "refresh_review_surface": "给人看的稿面、figure 和 table 不再暴露系统/分析流程痕迹。",
    "stabilize_submission_bundle": "docx/pdf 与当前 markdown 源稿同步，且最小投稿包达到可人工审核状态。",
}
_QUALITY_REVIEW_LOOP_PHASES = frozenset(
    {"revision_required", "revision_in_progress", "re_review_required", "write_continuation", "bundle_hardening"}
)
_QUALITY_REVIEW_LOOP_PHASE_LABELS = {
    "revision_required": "修订待执行",
    "revision_in_progress": "修订进行中",
    "re_review_required": "等待复评",
    "write_continuation": "继续写作收口",
    "bundle_hardening": "投稿包收口",
}
_QUALITY_REVIEW_LOOP_NEXT_PHASES = frozenset({"revision", "re_review", "write", "finalize"})
_QUALITY_REVIEW_LOOP_NEXT_PHASE_LABELS = {
    "revision": "执行修订",
    "re_review": "发起复评",
    "write": "继续写作",
    "finalize": "定稿与投稿收尾",
}


def stable_evaluation_summary_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_EVALUATION_SUMMARY_RELATIVE_PATH).resolve()


def stable_promotion_gate_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_PROMOTION_GATE_RELATIVE_PATH).resolve()


def _resolve_stable_ref(*, study_root: Path, stable_path: Path, ref: str | Path | None, label: str) -> Path:
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError(f"{label} only accepts the eval hygiene-owned promotion gate artifact" if "promotion gate" in label else f"{label} only accepts the eval hygiene-owned latest artifact")
    return stable_path


def resolve_evaluation_summary_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    return _resolve_stable_ref(
        study_root=study_root,
        stable_path=stable_evaluation_summary_path(study_root=study_root),
        ref=ref,
        label="evaluation summary reader",
    )


def resolve_promotion_gate_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    return _resolve_stable_ref(
        study_root=study_root,
        stable_path=stable_promotion_gate_path(study_root=study_root),
        ref=ref,
        label="promotion gate reader",
    )


def _required_text(label: str, field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _required_bool(label: str, field_name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be bool")
    return value


def _optional_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _required_choice(label: str, field_name: str, value: object, allowed_values: frozenset[str]) -> str:
    normalized = _required_text(label, field_name, value)
    if normalized not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{label} {field_name} must be one of: {allowed}")
    return normalized


def _required_mapping(label: str, field_name: str, value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    return dict(value)


def _required_string_list(label: str, field_name: str, value: object) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{label} {field_name} must be a list")
    normalized: list[str] = []
    for item in value:
        normalized.append(_required_text(label, field_name, item))
    return normalized


def _optional_string_list(label: str, field_name: str, value: object) -> list[str]:
    if value is None:
        return []
    return _required_string_list(label, field_name, value)


def _same_line_route_target_label(route_target: str | None) -> str | None:
    if route_target is None:
        return None
    return _SAME_LINE_ROUTE_TARGET_LABELS.get(route_target, route_target)


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{label} payload must be a JSON object: {path}")
    return payload


def _normalize_runtime_escalation_ref(
    *,
    study_root: Path,
    runtime_escalation_ref: str | Path | dict[str, Any],
) -> dict[str, str]:
    if isinstance(runtime_escalation_ref, dict):
        raw_ref = dict(runtime_escalation_ref)
        artifact_path = Path(_required_text("runtime escalation ref", "artifact_path", raw_ref.get("artifact_path"))).expanduser()
    else:
        raw_ref = {}
        artifact_path = Path(runtime_escalation_ref).expanduser()
    if not artifact_path.is_absolute():
        artifact_path = (Path(study_root).expanduser().resolve() / artifact_path).resolve()
    else:
        artifact_path = artifact_path.resolve()
    payload = _read_json_object(artifact_path, label="runtime escalation")
    record_id = _required_text("runtime escalation", "record_id", payload.get("record_id"))
    payload_artifact_path = Path(
        _required_text("runtime escalation", "artifact_path", payload.get("artifact_path"))
    ).expanduser().resolve()
    summary_ref = Path(_required_text("runtime escalation", "summary_ref", payload.get("summary_ref"))).expanduser().resolve()
    if payload_artifact_path != artifact_path:
        raise ValueError("runtime escalation artifact_path mismatch")
    if raw_ref:
        provided_record_id = _required_text("runtime escalation ref", "record_id", raw_ref.get("record_id"))
        provided_summary_ref = Path(
            _required_text("runtime escalation ref", "summary_ref", raw_ref.get("summary_ref"))
        ).expanduser().resolve()
        if provided_record_id != record_id or provided_summary_ref != summary_ref:
            raise ValueError("runtime escalation ref mismatch")
    return {
        "record_id": record_id,
        "artifact_path": str(payload_artifact_path),
        "summary_ref": str(summary_ref),
    }


def _normalize_gate_report(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path, label="promotion gate source report")
    blockers = _required_string_list("promotion gate source report", "blockers", payload.get("blockers"))
    return {
        "generated_at": _required_text("promotion gate source report", "generated_at", payload.get("generated_at")),
        "status": _required_text("promotion gate source report", "status", payload.get("status")),
        "allow_write": _required_bool("promotion gate source report", "allow_write", payload.get("allow_write")),
        "recommended_action": _required_text(
            "promotion gate source report",
            "recommended_action",
            payload.get("recommended_action"),
        ),
        "current_required_action": _required_text(
            "promotion gate source report",
            "current_required_action",
            payload.get("current_required_action"),
        ),
        "supervisor_phase": _required_text(
            "promotion gate source report",
            "supervisor_phase",
            payload.get("supervisor_phase"),
        ),
        "controller_stage_note": _required_text(
            "promotion gate source report",
            "controller_stage_note",
            payload.get("controller_stage_note"),
        ),
        "blockers": blockers,
        "medical_publication_surface_named_blockers": _optional_string_list(
            "promotion gate source report",
            "medical_publication_surface_named_blockers",
            payload.get("medical_publication_surface_named_blockers"),
        ),
        "medical_publication_surface_route_back_recommendation": (
            None
            if payload.get("medical_publication_surface_route_back_recommendation") is None
            else _required_text(
                "promotion gate source report",
                "medical_publication_surface_route_back_recommendation",
                payload.get("medical_publication_surface_route_back_recommendation"),
            )
        ),
        "source_gate_report_ref": str(path.resolve()),
    }


def _build_promotion_gate_payload(
    *,
    study_root: Path,
    publication_eval: dict[str, Any],
    runtime_escalation_ref: dict[str, str],
    gate_report: dict[str, Any],
) -> dict[str, Any]:
    quest_id = publication_eval.get("quest_id")
    quest_scope = _required_text("publication eval", "quest_id", quest_id)
    verdict = _required_mapping("publication eval", "verdict", publication_eval.get("verdict"))
    eval_id = _required_text("publication eval", "eval_id", publication_eval.get("eval_id"))
    return {
        "schema_version": 1,
        "gate_id": f"promotion-gate::{publication_eval['study_id']}::{quest_scope}::{gate_report['generated_at']}",
        "study_id": _required_text("publication eval", "study_id", publication_eval.get("study_id")),
        "quest_id": quest_scope,
        "emitted_at": gate_report["generated_at"],
        "source_gate_report_ref": gate_report["source_gate_report_ref"],
        "publication_eval_ref": {
            "eval_id": eval_id,
            "artifact_path": str(stable_publication_eval_latest_path(study_root=study_root)),
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "overall_verdict": _required_text("publication eval verdict", "overall_verdict", verdict.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "publication eval verdict",
            "primary_claim_status",
            verdict.get("primary_claim_status"),
        ),
        "stop_loss_pressure": _required_text(
            "publication eval verdict",
            "stop_loss_pressure",
            verdict.get("stop_loss_pressure"),
        ),
        "status": gate_report["status"],
        "allow_write": gate_report["allow_write"],
        "recommended_action": gate_report["recommended_action"],
        "current_required_action": gate_report["current_required_action"],
        "supervisor_phase": gate_report["supervisor_phase"],
        "controller_stage_note": gate_report["controller_stage_note"],
        "blockers": gate_report["blockers"],
        "medical_publication_surface_named_blockers": list(
            gate_report.get("medical_publication_surface_named_blockers") or []
        ),
        "medical_publication_surface_route_back_recommendation": (
            str(gate_report.get("medical_publication_surface_route_back_recommendation") or "").strip() or None
        ),
    }


def _gap_counts(gaps: list[dict[str, Any]]) -> dict[str, int]:
    counts = {severity: 0 for severity in _GAP_SEVERITIES}
    for gap in gaps:
        severity = _required_text("publication eval gap", "severity", gap.get("severity"))
        if severity in counts:
            counts[severity] += 1
    counts["total"] = len(gaps)
    return counts


def _recommended_action_types(actions: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for action in actions:
        action_type = _required_text("publication eval recommended action", "action_type", action.get("action_type"))
        if action_type not in seen:
            ordered.append(action_type)
            seen.add(action_type)
    return ordered


def _route_repair_plan(actions: list[dict[str, Any]]) -> dict[str, str] | None:
    prioritized_actions = sorted(
        enumerate(actions),
        key=lambda item: (0 if item[1].get("priority") == "now" else 1, item[0]),
    )
    for _, action in prioritized_actions:
        action_type = _required_text("publication eval recommended action", "action_type", action.get("action_type"))
        if action_type not in _ROUTE_REPAIR_ACTION_TYPES:
            continue
        return {
            "action_id": _required_text("publication eval recommended action", "action_id", action.get("action_id")),
            "action_type": action_type,
            "priority": _required_text("publication eval recommended action", "priority", action.get("priority")),
            "route_target": _required_text(
                "publication eval recommended action",
                "route_target",
                action.get("route_target"),
            ),
            "route_key_question": _required_text(
                "publication eval recommended action",
                "route_key_question",
                action.get("route_key_question"),
            ),
            "route_rationale": _required_text(
                "publication eval recommended action",
                "route_rationale",
                action.get("route_rationale"),
            ),
        }
    return None


def _highest_priority_gap(gaps: list[dict[str, Any]]) -> dict[str, str] | None:
    selected: tuple[tuple[int, int], dict[str, str]] | None = None
    for index, gap in enumerate(gaps):
        if not isinstance(gap, dict):
            continue
        summary = _optional_text(gap.get("summary"))
        if summary is None:
            continue
        severity = _optional_text(gap.get("severity")) or "important"
        marker = (_GAP_SEVERITY_RANK.get(severity, len(_GAP_SEVERITIES)), index)
        candidate = {
            "severity": severity,
            "summary": summary,
        }
        if selected is None or marker < selected[0]:
            selected = (marker, candidate)
    return None if selected is None else selected[1]


def _highest_priority_action(actions: list[dict[str, Any]]) -> dict[str, str] | None:
    selected: tuple[tuple[int, int], dict[str, str]] | None = None
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        action_type = _optional_text(action.get("action_type"))
        reason = _optional_text(action.get("reason"))
        if action_type is None and reason is None:
            continue
        priority = _optional_text(action.get("priority")) or "next"
        marker = (_ACTION_PRIORITY_RANK.get(priority, 1), index)
        candidate = {
            "action_type": action_type or "unknown",
            "priority": priority,
            "reason": reason or "",
            "route_target": _optional_text(action.get("route_target")) or "",
        }
        if selected is None or marker < selected[0]:
            selected = (marker, candidate)
    return None if selected is None else selected[1]


def _agenda_field(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = _optional_text(payload.get(key))
        if value is not None:
            return value
    return None


def _agenda_summary(
    *,
    top_priority_issue: str,
    suggested_revision: str,
    next_review_focus: str,
) -> str:
    return (
        f"优先修复：{top_priority_issue}；"
        f"建议修订：{suggested_revision}；"
        f"下一轮复评重点：{next_review_focus}"
    )


def _quality_review_agenda_from_summary_payload(summary_payload: dict[str, Any]) -> dict[str, str]:
    route_repair_plan = (
        dict(summary_payload.get("route_repair_plan") or {})
        if isinstance(summary_payload.get("route_repair_plan"), dict)
        else {}
    )
    quality_execution_lane = _quality_execution_lane_from_summary_payload(summary_payload)
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), dict)
        else {}
    )
    top_priority_issue = (
        _optional_text(quality_closure_truth.get("summary"))
        or _optional_text(summary_payload.get("verdict_summary"))
        or "当前论文线仍有质量修订任务待完成。"
    )
    route_target = _optional_text(route_repair_plan.get("route_target"))
    route_rationale = _optional_text(route_repair_plan.get("route_rationale"))
    current_required_action = _optional_text(quality_closure_truth.get("current_required_action"))
    if route_target and route_rationale:
        suggested_revision = f"先在 {route_target} 修订：{route_rationale}"
    elif route_target:
        suggested_revision = f"先在 {route_target} 推进当前最窄修订。"
    elif route_rationale:
        suggested_revision = route_rationale
    elif current_required_action:
        suggested_revision = f"按 {current_required_action} 指令继续质量修订。"
    else:
        suggested_revision = _optional_text(summary_payload.get("verdict_summary")) or "继续按当前评估结论收窄修订。"
    next_review_focus = (
        _optional_text(quality_execution_lane.get("route_key_question"))
        or _optional_text(route_repair_plan.get("route_key_question"))
        or f"复评时确认“{top_priority_issue}”是否已经形成可复核证据闭环。"
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


def _reviewer_agenda_from_quality_assessment(publication_eval: dict[str, Any]) -> dict[str, str]:
    quality_assessment = (
        dict(publication_eval.get("quality_assessment") or {})
        if isinstance(publication_eval.get("quality_assessment"), dict)
        else {}
    )
    candidates: list[tuple[tuple[int, int], dict[str, str]]] = []
    for order_index, dimension in enumerate(_QUALITY_ASSESSMENT_REVIEW_ORDER):
        payload = quality_assessment.get(dimension)
        if not isinstance(payload, dict):
            continue
        reason = _optional_text(payload.get("reviewer_reason"))
        advice = _optional_text(payload.get("reviewer_revision_advice"))
        next_focus = _optional_text(payload.get("reviewer_next_round_focus"))
        if reason is None and advice is None and next_focus is None:
            continue
        status = _optional_text(payload.get("status")) or "partial"
        marker = (_QUALITY_REVIEW_STATUS_RANK.get(status, len(_QUALITY_REVIEW_STATUS_RANK)), order_index)
        candidates.append(
            (
                marker,
                {
                    "top_priority_issue": reason or "",
                    "suggested_revision": advice or "",
                    "next_review_focus": next_focus or "",
                },
            )
        )
    candidates.sort(key=lambda item: item[0])
    top_priority_issue: str | None = None
    suggested_revision: str | None = None
    next_review_focus: str | None = None
    for _, candidate in candidates:
        if top_priority_issue is None and candidate["top_priority_issue"]:
            top_priority_issue = candidate["top_priority_issue"]
        if suggested_revision is None and candidate["suggested_revision"]:
            suggested_revision = candidate["suggested_revision"]
        if next_review_focus is None and candidate["next_review_focus"]:
            next_review_focus = candidate["next_review_focus"]
    return {
        "top_priority_issue": top_priority_issue or "",
        "suggested_revision": suggested_revision or "",
        "next_review_focus": next_review_focus or "",
    }


def _normalized_quality_review_agenda(
    *,
    agenda_payload: dict[str, Any] | None,
    summary_payload: dict[str, Any],
) -> dict[str, str]:
    fallback = _quality_review_agenda_from_summary_payload(summary_payload)
    if not isinstance(agenda_payload, dict):
        return fallback
    top_priority_issue = (
        _agenda_field(
            agenda_payload,
            "top_priority_issue",
            "priority_issue",
            "current_top_issue",
            "reviewer_reason",
        )
        or fallback["top_priority_issue"]
    )
    suggested_revision = (
        _agenda_field(
            agenda_payload,
            "suggested_revision",
            "revision_action",
            "suggested_fix",
            "reviewer_revision_advice",
        )
        or fallback["suggested_revision"]
    )
    next_review_focus = (
        _agenda_field(
            agenda_payload,
            "next_review_focus",
            "review_focus",
            "next_review_checkpoint",
            "reviewer_next_round_focus",
        )
        or fallback["next_review_focus"]
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


def _unique_non_empty_texts(*values: object) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if isinstance(value, list):
            nested_values = value
        else:
            nested_values = [value]
        for item in nested_values:
            text = _optional_text(item)
            if text is None or text in seen:
                continue
            ordered.append(text)
            seen.add(text)
    return ordered


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


def _build_evaluation_summary_payload(
    *,
    study_root: Path,
    publication_eval: dict[str, Any],
    charter_payload: dict[str, Any],
    runtime_escalation_ref: dict[str, str],
    promotion_gate_ref: dict[str, str],
    promotion_gate_payload: dict[str, Any],
) -> dict[str, Any]:
    charter_context_ref = _required_mapping(
        "publication eval",
        "charter_context_ref",
        publication_eval.get("charter_context_ref"),
    )
    charter_id = _required_text("study charter", "charter_id", charter_payload.get("charter_id"))
    publication_objective = _required_text(
        "study charter",
        "publication_objective",
        charter_payload.get("publication_objective"),
    )
    if _required_text("publication eval charter context ref", "charter_id", charter_context_ref.get("charter_id")) != charter_id:
        raise ValueError("evaluation summary charter_id mismatch")
    if _required_text(
        "publication eval charter context ref",
        "publication_objective",
        charter_context_ref.get("publication_objective"),
    ) != publication_objective:
        raise ValueError("evaluation summary publication objective mismatch")
    verdict = _required_mapping("publication eval", "verdict", publication_eval.get("verdict"))
    gaps = list(publication_eval.get("gaps") or [])
    actions = list(publication_eval.get("recommended_actions") or [])
    quest_id = _required_text("publication eval", "quest_id", publication_eval.get("quest_id"))
    route_repair_plan = _route_repair_plan(actions)
    summary_id = f"evaluation-summary::{publication_eval['study_id']}::{quest_id}::{publication_eval['emitted_at']}"
    quality_closure_basis = _quality_closure_basis(
        study_root=study_root,
        publication_eval=publication_eval,
        promotion_gate_ref=promotion_gate_ref,
        promotion_gate_payload=promotion_gate_payload,
        route_repair_plan=route_repair_plan,
    )
    quality_closure_truth = _quality_closure_truth(
        promotion_gate_payload=promotion_gate_payload,
        route_repair_plan=route_repair_plan,
        quality_closure_basis=quality_closure_basis,
    )
    quality_execution_lane = _quality_execution_lane(
        promotion_gate_payload=promotion_gate_payload,
        route_repair_plan=route_repair_plan,
    )
    review_ledger_payload, review_ledger_path = _load_review_ledger_context(publication_eval)
    study_quality_truth = build_study_quality_truth(
        study_id=_required_text("publication eval", "study_id", publication_eval.get("study_id")),
        charter_payload=charter_payload,
        publication_eval=publication_eval,
        promotion_gate_payload=promotion_gate_payload,
        route_repair_plan=route_repair_plan,
        quality_closure_truth=quality_closure_truth,
        quality_closure_basis=quality_closure_basis,
        quality_execution_lane=quality_execution_lane,
        review_ledger_payload=review_ledger_payload,
        review_ledger_path=review_ledger_path,
    )
    same_line_route_truth = build_same_line_route_truth(
        quality_closure_truth=quality_closure_truth,
        quality_execution_lane=quality_execution_lane,
    )
    same_line_route_surface = _same_line_route_surface_from_summary_payload(
        {
            "quality_closure_truth": quality_closure_truth,
            "quality_execution_lane": quality_execution_lane,
        }
    )
    quality_review_agenda = _quality_review_agenda(
        publication_eval=publication_eval,
        gaps=gaps,
        actions=actions,
        route_repair_plan=route_repair_plan,
        quality_closure_truth=quality_closure_truth,
    )
    quality_revision_plan = _quality_revision_plan(
        publication_eval=publication_eval,
        summary_payload={
            "summary_id": summary_id,
            "study_id": publication_eval["study_id"],
            "verdict_summary": verdict.get("summary"),
            "route_repair_plan": route_repair_plan,
            "quality_closure_truth": quality_closure_truth,
            "quality_execution_lane": quality_execution_lane,
            "same_line_route_truth": same_line_route_truth or None,
            "same_line_route_surface": same_line_route_surface or None,
            "quality_closure_basis": quality_closure_basis,
            "quality_review_agenda": quality_review_agenda,
        },
    )
    quality_review_loop = _quality_review_loop_from_summary_payload(
        {
            "summary_id": summary_id,
            "study_id": publication_eval["study_id"],
            "quality_closure_truth": quality_closure_truth,
            "quality_execution_lane": quality_execution_lane,
            "same_line_route_truth": same_line_route_truth or None,
            "same_line_route_surface": same_line_route_surface or None,
            "quality_review_agenda": quality_review_agenda,
            "quality_revision_plan": quality_revision_plan,
        }
    )
    return {
        "schema_version": 1,
        "summary_id": summary_id,
        "study_id": _required_text("publication eval", "study_id", publication_eval.get("study_id")),
        "quest_id": quest_id,
        "emitted_at": _required_text("publication eval", "emitted_at", publication_eval.get("emitted_at")),
        "charter_ref": {
            "charter_id": charter_id,
            "artifact_path": str(resolve_study_charter_ref(study_root=study_root, ref=charter_context_ref.get("ref"))),
            "publication_objective": publication_objective,
        },
        "publication_eval_ref": {
            "eval_id": _required_text("publication eval", "eval_id", publication_eval.get("eval_id")),
            "artifact_path": str(stable_publication_eval_latest_path(study_root=study_root)),
        },
        "runtime_escalation_ref": runtime_escalation_ref,
        "promotion_gate_ref": dict(promotion_gate_ref),
        "evaluation_scope": _required_text(
            "publication eval",
            "evaluation_scope",
            publication_eval.get("evaluation_scope"),
        ),
        "overall_verdict": _required_text("publication eval verdict", "overall_verdict", verdict.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "publication eval verdict",
            "primary_claim_status",
            verdict.get("primary_claim_status"),
        ),
        "verdict_summary": _required_text("publication eval verdict", "summary", verdict.get("summary")),
        "stop_loss_pressure": _required_text(
            "publication eval verdict",
            "stop_loss_pressure",
            verdict.get("stop_loss_pressure"),
        ),
        "publication_objective": publication_objective,
        "gap_counts": _gap_counts(gaps),
        "recommended_action_types": _recommended_action_types(actions),
        "route_repair_plan": route_repair_plan,
        "quality_closure_truth": quality_closure_truth,
        "quality_execution_lane": quality_execution_lane,
        "study_quality_truth": study_quality_truth,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_closure_basis": quality_closure_basis,
        "quality_review_agenda": quality_review_agenda,
        "quality_revision_plan": quality_revision_plan,
        "quality_review_loop": quality_review_loop,
        "requires_controller_decision": any(bool(action.get("requires_controller_decision")) for action in actions),
        "promotion_gate_status": {
            "status": promotion_gate_payload["status"],
            "allow_write": promotion_gate_payload["allow_write"],
            "current_required_action": promotion_gate_payload["current_required_action"],
            "blockers": list(promotion_gate_payload["blockers"]),
            "medical_publication_surface_named_blockers": list(
                promotion_gate_payload.get("medical_publication_surface_named_blockers") or []
            ),
            "medical_publication_surface_route_back_recommendation": (
                str(promotion_gate_payload.get("medical_publication_surface_route_back_recommendation") or "").strip()
                or None
            ),
        },
    }


def _normalized_promotion_gate(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("promotion gate payload must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("promotion gate schema_version must be 1")
    return {
        "schema_version": 1,
        "gate_id": _required_text("promotion gate", "gate_id", payload.get("gate_id")),
        "study_id": _required_text("promotion gate", "study_id", payload.get("study_id")),
        "quest_id": _required_text("promotion gate", "quest_id", payload.get("quest_id")),
        "emitted_at": _required_text("promotion gate", "emitted_at", payload.get("emitted_at")),
        "source_gate_report_ref": _required_text(
            "promotion gate",
            "source_gate_report_ref",
            payload.get("source_gate_report_ref"),
        ),
        "publication_eval_ref": _required_mapping(
            "promotion gate",
            "publication_eval_ref",
            payload.get("publication_eval_ref"),
        ),
        "runtime_escalation_ref": _required_mapping(
            "promotion gate",
            "runtime_escalation_ref",
            payload.get("runtime_escalation_ref"),
        ),
        "overall_verdict": _required_text("promotion gate", "overall_verdict", payload.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "promotion gate",
            "primary_claim_status",
            payload.get("primary_claim_status"),
        ),
        "stop_loss_pressure": _required_text(
            "promotion gate",
            "stop_loss_pressure",
            payload.get("stop_loss_pressure"),
        ),
        "status": _required_text("promotion gate", "status", payload.get("status")),
        "allow_write": _required_bool("promotion gate", "allow_write", payload.get("allow_write")),
        "recommended_action": _required_text(
            "promotion gate",
            "recommended_action",
            payload.get("recommended_action"),
        ),
        "current_required_action": _required_text(
            "promotion gate",
            "current_required_action",
            payload.get("current_required_action"),
        ),
        "supervisor_phase": _required_text(
            "promotion gate",
            "supervisor_phase",
            payload.get("supervisor_phase"),
        ),
        "controller_stage_note": _required_text(
            "promotion gate",
            "controller_stage_note",
            payload.get("controller_stage_note"),
        ),
        "blockers": _required_string_list("promotion gate", "blockers", payload.get("blockers")),
        "medical_publication_surface_named_blockers": _optional_string_list(
            "promotion gate",
            "medical_publication_surface_named_blockers",
            payload.get("medical_publication_surface_named_blockers"),
        ),
        "medical_publication_surface_route_back_recommendation": (
            None
            if payload.get("medical_publication_surface_route_back_recommendation") is None
            else _required_text(
                "promotion gate",
                "medical_publication_surface_route_back_recommendation",
                payload.get("medical_publication_surface_route_back_recommendation"),
            )
        ),
    }


def _normalized_evaluation_summary(payload: dict[str, Any], *, study_root: Path) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("evaluation summary payload must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("evaluation summary schema_version must be 1")
    quality_closure_truth = _required_mapping(
        "evaluation summary",
        "quality_closure_truth",
        payload.get("quality_closure_truth"),
    )
    quality_closure_basis = _required_mapping(
        "evaluation summary",
        "quality_closure_basis",
        payload.get("quality_closure_basis"),
    )
    quality_review_agenda = (
        dict(payload.get("quality_review_agenda") or {})
        if isinstance(payload.get("quality_review_agenda"), dict)
        else None
    )
    quality_revision_plan = (
        dict(payload.get("quality_revision_plan") or {})
        if isinstance(payload.get("quality_revision_plan"), dict)
        else None
    )
    quality_review_loop = (
        dict(payload.get("quality_review_loop") or {})
        if isinstance(payload.get("quality_review_loop"), dict)
        else None
    )
    quality_execution_lane = _normalized_quality_execution_lane_payload(payload)
    same_line_route_truth = _normalized_same_line_route_truth_payload(payload)
    same_line_route_surface = _normalized_same_line_route_surface_payload(payload)
    normalized_quality_review_agenda = _normalized_quality_review_agenda(
        agenda_payload=quality_review_agenda,
        summary_payload=payload,
    )
    normalized_quality_revision_plan = _normalized_quality_revision_plan(
        plan_payload=quality_revision_plan,
        summary_payload={**payload, "quality_review_agenda": normalized_quality_review_agenda},
    )
    normalized_quality_review_loop = _normalized_quality_review_loop(
        loop_payload=quality_review_loop,
        summary_payload={
            **payload,
            "quality_review_agenda": normalized_quality_review_agenda,
            "quality_revision_plan": normalized_quality_revision_plan,
        },
    )
    raw_study_quality_truth = (
        dict(payload.get("study_quality_truth") or {})
        if isinstance(payload.get("study_quality_truth"), dict)
        else None
    )
    normalized_study_quality_truth = raw_study_quality_truth or _study_quality_truth_from_summary_payload(
        study_root=study_root,
        summary_payload=payload,
        quality_closure_truth=quality_closure_truth,
        quality_closure_basis=quality_closure_basis,
        quality_execution_lane=quality_execution_lane,
    )
    return {
        "schema_version": 1,
        "summary_id": _required_text("evaluation summary", "summary_id", payload.get("summary_id")),
        "study_id": _required_text("evaluation summary", "study_id", payload.get("study_id")),
        "quest_id": _required_text("evaluation summary", "quest_id", payload.get("quest_id")),
        "emitted_at": _required_text("evaluation summary", "emitted_at", payload.get("emitted_at")),
        "charter_ref": _required_mapping("evaluation summary", "charter_ref", payload.get("charter_ref")),
        "publication_eval_ref": _required_mapping(
            "evaluation summary",
            "publication_eval_ref",
            payload.get("publication_eval_ref"),
        ),
        "runtime_escalation_ref": _required_mapping(
            "evaluation summary",
            "runtime_escalation_ref",
            payload.get("runtime_escalation_ref"),
        ),
        "promotion_gate_ref": _required_mapping(
            "evaluation summary",
            "promotion_gate_ref",
            payload.get("promotion_gate_ref"),
        ),
        "evaluation_scope": _required_text(
            "evaluation summary",
            "evaluation_scope",
            payload.get("evaluation_scope"),
        ),
        "overall_verdict": _required_text("evaluation summary", "overall_verdict", payload.get("overall_verdict")),
        "primary_claim_status": _required_text(
            "evaluation summary",
            "primary_claim_status",
            payload.get("primary_claim_status"),
        ),
        "verdict_summary": _required_text(
            "evaluation summary",
            "verdict_summary",
            payload.get("verdict_summary"),
        ),
        "stop_loss_pressure": _required_text(
            "evaluation summary",
            "stop_loss_pressure",
            payload.get("stop_loss_pressure"),
        ),
        "publication_objective": _required_text(
            "evaluation summary",
            "publication_objective",
            payload.get("publication_objective"),
        ),
        "gap_counts": _required_mapping("evaluation summary", "gap_counts", payload.get("gap_counts")),
        "recommended_action_types": _required_string_list(
            "evaluation summary",
            "recommended_action_types",
            payload.get("recommended_action_types"),
        ),
        "route_repair_plan": (
            None
            if payload.get("route_repair_plan") is None
            else _required_mapping("evaluation summary", "route_repair_plan", payload.get("route_repair_plan"))
        ),
        "quality_closure_truth": {
            "state": _required_choice(
                "evaluation summary quality_closure_truth",
                "state",
                quality_closure_truth.get("state"),
                _QUALITY_CLOSURE_STATES,
            ),
            "summary": _required_text(
                "evaluation summary quality_closure_truth",
                "summary",
                quality_closure_truth.get("summary"),
            ),
            "current_required_action": _required_text(
                "evaluation summary quality_closure_truth",
                "current_required_action",
                quality_closure_truth.get("current_required_action"),
            ),
            "route_target": (
                None
                if quality_closure_truth.get("route_target") is None
                else _required_text(
                    "evaluation summary quality_closure_truth",
                    "route_target",
                    quality_closure_truth.get("route_target"),
                )
            ),
        },
        "quality_execution_lane": {
            "lane_id": _required_text(
                "evaluation summary quality_execution_lane",
                "lane_id",
                quality_execution_lane.get("lane_id"),
            ),
            "lane_label": _required_text(
                "evaluation summary quality_execution_lane",
                "lane_label",
                quality_execution_lane.get("lane_label"),
            ),
            "repair_mode": (
                None
                if quality_execution_lane.get("repair_mode") is None
                else _required_text(
                    "evaluation summary quality_execution_lane",
                    "repair_mode",
                    quality_execution_lane.get("repair_mode"),
                )
            ),
            "route_target": (
                None
                if quality_execution_lane.get("route_target") is None
                else _required_text(
                    "evaluation summary quality_execution_lane",
                    "route_target",
                    quality_execution_lane.get("route_target"),
                )
            ),
            "route_key_question": (
                None
                if quality_execution_lane.get("route_key_question") is None
                else _required_text(
                    "evaluation summary quality_execution_lane",
                    "route_key_question",
                    quality_execution_lane.get("route_key_question"),
                )
            ),
            "summary": _required_text(
                "evaluation summary quality_execution_lane",
                "summary",
                quality_execution_lane.get("summary"),
            ),
            "why_now": _required_text(
                "evaluation summary quality_execution_lane",
                "why_now",
                quality_execution_lane.get("why_now"),
            ),
        },
        "study_quality_truth": {
            "study_id": _required_text(
                "evaluation summary study_quality_truth",
                "study_id",
                normalized_study_quality_truth.get("study_id"),
            ),
            "contract_state": _required_choice(
                "evaluation summary study_quality_truth",
                "contract_state",
                normalized_study_quality_truth.get("contract_state"),
                _QUALITY_CLOSURE_STATES,
            ),
            "contract_closed": _required_bool(
                "evaluation summary study_quality_truth",
                "contract_closed",
                normalized_study_quality_truth.get("contract_closed"),
            ),
            "summary": _required_text(
                "evaluation summary study_quality_truth",
                "summary",
                normalized_study_quality_truth.get("summary"),
            ),
            "narrowest_scientific_gap": _required_mapping(
                "evaluation summary study_quality_truth",
                "narrowest_scientific_gap",
                normalized_study_quality_truth.get("narrowest_scientific_gap"),
            ),
            "reviewer_first": _required_mapping(
                "evaluation summary study_quality_truth",
                "reviewer_first",
                normalized_study_quality_truth.get("reviewer_first"),
            ),
            "bounded_analysis": _required_mapping(
                "evaluation summary study_quality_truth",
                "bounded_analysis",
                normalized_study_quality_truth.get("bounded_analysis"),
            ),
            "finalize_bundle_readiness": _required_mapping(
                "evaluation summary study_quality_truth",
                "finalize_bundle_readiness",
                normalized_study_quality_truth.get("finalize_bundle_readiness"),
            ),
            "publication_gate_required_action": (
                None
                if normalized_study_quality_truth.get("publication_gate_required_action") is None
                else _required_text(
                    "evaluation summary study_quality_truth",
                    "publication_gate_required_action",
                    normalized_study_quality_truth.get("publication_gate_required_action"),
                )
            ),
        },
        "same_line_route_truth": {
            "surface_kind": _required_text(
                "evaluation summary same_line_route_truth",
                "surface_kind",
                same_line_route_truth.get("surface_kind"),
            ),
            "same_line_state": _required_choice(
                "evaluation summary same_line_route_truth",
                "same_line_state",
                same_line_route_truth.get("same_line_state"),
                _SAME_LINE_ROUTE_STATES,
            ),
            "same_line_state_label": _required_text(
                "evaluation summary same_line_route_truth",
                "same_line_state_label",
                same_line_route_truth.get("same_line_state_label"),
            ),
            "route_mode": (
                None
                if same_line_route_truth.get("route_mode") is None
                else _required_choice(
                    "evaluation summary same_line_route_truth",
                    "route_mode",
                    same_line_route_truth.get("route_mode"),
                    _SAME_LINE_ROUTE_MODES,
                )
            ),
            "route_target": (
                None
                if same_line_route_truth.get("route_target") is None
                else _required_text(
                    "evaluation summary same_line_route_truth",
                    "route_target",
                    same_line_route_truth.get("route_target"),
                )
            ),
            "route_target_label": (
                None
                if same_line_route_truth.get("route_target_label") is None
                else _required_text(
                    "evaluation summary same_line_route_truth",
                    "route_target_label",
                    same_line_route_truth.get("route_target_label"),
                )
            ),
            "summary": _required_text(
                "evaluation summary same_line_route_truth",
                "summary",
                same_line_route_truth.get("summary"),
            ),
            "current_focus": _required_text(
                "evaluation summary same_line_route_truth",
                "current_focus",
                same_line_route_truth.get("current_focus"),
            ),
        },
        "same_line_route_surface": (
            None
            if not same_line_route_surface
            else {
                "surface_kind": _required_text(
                    "evaluation summary same_line_route_surface",
                    "surface_kind",
                    same_line_route_surface.get("surface_kind"),
                ),
                "lane_id": _required_text(
                    "evaluation summary same_line_route_surface",
                    "lane_id",
                    same_line_route_surface.get("lane_id"),
                ),
                "repair_mode": _required_text(
                    "evaluation summary same_line_route_surface",
                    "repair_mode",
                    same_line_route_surface.get("repair_mode"),
                ),
                "route_target": _required_text(
                    "evaluation summary same_line_route_surface",
                    "route_target",
                    same_line_route_surface.get("route_target"),
                ),
                "route_target_label": _required_text(
                    "evaluation summary same_line_route_surface",
                    "route_target_label",
                    same_line_route_surface.get("route_target_label"),
                ),
                "route_key_question": _required_text(
                    "evaluation summary same_line_route_surface",
                    "route_key_question",
                    same_line_route_surface.get("route_key_question"),
                ),
                "summary": _required_text(
                    "evaluation summary same_line_route_surface",
                    "summary",
                    same_line_route_surface.get("summary"),
                ),
                "why_now": _required_text(
                    "evaluation summary same_line_route_surface",
                    "why_now",
                    same_line_route_surface.get("why_now"),
                ),
                "current_required_action": _required_text(
                    "evaluation summary same_line_route_surface",
                    "current_required_action",
                    same_line_route_surface.get("current_required_action"),
                ),
                "closure_state": _required_choice(
                    "evaluation summary same_line_route_surface",
                    "closure_state",
                    same_line_route_surface.get("closure_state"),
                    _QUALITY_CLOSURE_STATES,
                ),
            }
        ),
        "quality_closure_basis": {
            key: _coerce_quality_basis_item(
                payload=_required_mapping("evaluation summary quality_closure_basis", key, quality_closure_basis.get(key)),
                fallback_status="underdefined",
                fallback_summary="unreachable",
                fallback_refs=["unreachable"],
            )
            for key in _QUALITY_CLOSURE_BASIS_KEYS
        },
        "quality_review_agenda": normalized_quality_review_agenda,
        "quality_revision_plan": normalized_quality_revision_plan,
        "quality_review_loop": normalized_quality_review_loop,
        "requires_controller_decision": _required_bool(
            "evaluation summary",
            "requires_controller_decision",
            payload.get("requires_controller_decision"),
        ),
        "promotion_gate_status": _required_mapping(
            "evaluation summary",
            "promotion_gate_status",
            payload.get("promotion_gate_status"),
        ),
    }


def read_promotion_gate(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    gate_path = resolve_promotion_gate_ref(study_root=study_root, ref=ref)
    payload = _read_json_object(gate_path, label="promotion gate")
    return _normalized_promotion_gate(payload)


def read_evaluation_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    summary_path = resolve_evaluation_summary_ref(study_root=study_root, ref=ref)
    payload = _read_json_object(summary_path, label="evaluation summary")
    return _normalized_evaluation_summary(payload, study_root=study_root)


def materialize_evaluation_summary_artifacts(
    *,
    study_root: Path,
    runtime_escalation_ref: str | Path | dict[str, Any],
    publishability_gate_report_ref: str | Path,
) -> dict[str, dict[str, str]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    publication_eval = read_publication_eval_latest(study_root=resolved_study_root)
    charter_context_ref = _required_mapping(
        "publication eval",
        "charter_context_ref",
        publication_eval.get("charter_context_ref"),
    )
    charter_payload = read_study_charter(
        study_root=resolved_study_root,
        ref=charter_context_ref.get("ref"),
    )
    normalized_runtime_escalation_ref = _normalize_runtime_escalation_ref(
        study_root=resolved_study_root,
        runtime_escalation_ref=runtime_escalation_ref,
    )
    gate_report_path = Path(publishability_gate_report_ref).expanduser()
    if gate_report_path.is_absolute():
        gate_report_path = gate_report_path.resolve()
    else:
        gate_report_path = (resolved_study_root / gate_report_path).resolve()
    gate_report = _normalize_gate_report(gate_report_path)
    promotion_gate_payload = _build_promotion_gate_payload(
        study_root=resolved_study_root,
        publication_eval=publication_eval,
        runtime_escalation_ref=normalized_runtime_escalation_ref,
        gate_report=gate_report,
    )
    promotion_gate_path = stable_promotion_gate_path(study_root=resolved_study_root)
    promotion_gate_path.parent.mkdir(parents=True, exist_ok=True)
    promotion_gate_path.write_text(
        json.dumps(_normalized_promotion_gate(promotion_gate_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    promotion_gate_ref = {
        "gate_id": str(promotion_gate_payload["gate_id"]),
        "artifact_path": str(promotion_gate_path),
    }
    evaluation_summary_payload = _build_evaluation_summary_payload(
        study_root=resolved_study_root,
        publication_eval=publication_eval,
        charter_payload=charter_payload,
        runtime_escalation_ref=normalized_runtime_escalation_ref,
        promotion_gate_ref=promotion_gate_ref,
        promotion_gate_payload=promotion_gate_payload,
    )
    evaluation_summary_path = stable_evaluation_summary_path(study_root=resolved_study_root)
    evaluation_summary_path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_summary_path.write_text(
        json.dumps(
            _normalized_evaluation_summary(evaluation_summary_payload, study_root=resolved_study_root),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "evaluation_summary_ref": {
            "summary_id": str(evaluation_summary_payload["summary_id"]),
            "artifact_path": str(evaluation_summary_path),
        },
        "promotion_gate_ref": promotion_gate_ref,
    }
