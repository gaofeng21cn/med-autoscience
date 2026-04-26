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
_TASK_INTAKE_REPORTING_SCOPE_HINTS = frozenset(
    {
        "reporting/display contract mismatch",
        "delivery/reporting contract mismatch",
        "display contract",
        "display registry",
        "registry_contract_mismatch",
        "medical_reporting_audit",
        "稿面契约",
        "显示契约",
    }
)
_TASK_INTAKE_NO_CLAIM_REOPEN_HINTS = frozenset(
    {
        "do not change scientific claims",
        "do not reopen scientific claims",
        "不要改变科学结论",
        "不要改 scientific claims",
        "不改变科学主张",
    }
)
_TASK_INTAKE_NO_EVIDENCE_REOPEN_HINTS = frozenset(
    {
        "do not reopen manuscript evidence adequacy",
        "not manuscript evidence failure",
        "不要重开 manuscript evidence adequacy",
        "不得重开证据充分性",
        "只使用现有证据",
        "只基于当前数据",
    }
)
_TASK_INTAKE_NO_PUBLIC_DATA_EXPANSION_HINTS = frozenset(
    {
        "do not expand public data",
        "不要扩 public data",
        "不扩 public data",
    }
)
_TASK_INTAKE_STATUS_RECHECK_HINTS = frozenset(
    {
        "medical_reporting_audit",
        "runtime_watch",
        "publication-gate",
        "publication gate",
    }
)
_TASK_INTAKE_DISPLAY_REGISTRY_HINTS = frozenset({"display registry", "registry_contract_mismatch"})
_TASK_INTAKE_SHELL_INPUT_HINTS = frozenset({"shell/input", "input surfaces"})


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
    scoped_agenda = _task_intake_scoped_quality_agenda(summary_payload)
    if scoped_agenda is not None:
        return scoped_agenda
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
    provenance = (
        dict(publication_eval.get("assessment_provenance") or {})
        if isinstance(publication_eval.get("assessment_provenance"), dict)
        else {}
    )
    if provenance.get("owner") != "ai_reviewer" or provenance.get("ai_reviewer_required") is not False:
        return {
            "top_priority_issue": "",
            "suggested_revision": "",
            "next_review_focus": "",
        }
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
    scoped_agenda = _task_intake_scoped_quality_agenda(summary_payload)
    if scoped_agenda is not None:
        return scoped_agenda
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


def _task_intake_scope_texts(task_intake: dict[str, Any] | None) -> list[str]:
    if not isinstance(task_intake, dict):
        return []
    return _unique_non_empty_texts(
        list(task_intake.get("trusted_inputs") or []),
        list(task_intake.get("constraints") or []),
        task_intake.get("task_intent"),
        list(task_intake.get("evidence_boundary") or []),
        list(task_intake.get("first_cycle_outputs") or []),
    )


def _task_intake_contains_hint(texts: list[str], hints: frozenset[str]) -> bool:
    lowered_texts = [text.casefold() for text in texts]
    return any(hint in text for text in lowered_texts for hint in hints)


def _format_revision_scope_targets(targets: list[str]) -> str:
    unique_targets = _unique_non_empty_texts(targets)
    if not unique_targets:
        return "reporting contract"
    if len(unique_targets) == 1:
        return unique_targets[0]
    if len(unique_targets) == 2:
        return f"{unique_targets[0]} 与 {unique_targets[1]}"
    return f"{'、'.join(unique_targets[:-1])} 与{unique_targets[-1]}"
