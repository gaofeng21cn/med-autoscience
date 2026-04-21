from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_latest import read_publication_eval_latest, stable_publication_eval_latest_path
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref

__all__ = [
    "STABLE_EVALUATION_SUMMARY_RELATIVE_PATH",
    "STABLE_PROMOTION_GATE_RELATIVE_PATH",
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
        _optional_text(route_repair_plan.get("route_key_question"))
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
    if reviewer_agenda["next_review_focus"]:
        next_review_focus = reviewer_agenda["next_review_focus"]
    else:
        next_review_focus = (
            _optional_text((route_repair_plan or {}).get("route_key_question"))
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
        summary_payload={
            "verdict_summary": _optional_text((publication_eval.get("verdict") or {}).get("summary")),
            "route_repair_plan": route_repair_plan,
            "quality_closure_truth": quality_closure_truth,
            "quality_review_agenda": derived_agenda,
        },
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
    current_required_action = _required_text(
        "promotion gate",
        "current_required_action",
        promotion_gate_payload.get("current_required_action"),
    )
    evidence_strength_status = str((quality_closure_basis.get("evidence_strength") or {}).get("status") or "").strip()
    if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"} and evidence_strength_status == "ready":
        return {
            "state": "bundle_only_remaining",
            "summary": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
            "current_required_action": current_required_action,
            "route_target": "finalize",
        }
    if current_required_action == "continue_write_stage" and evidence_strength_status == "ready":
        return {
            "state": "write_line_ready",
            "summary": "核心科学质量已经够稳；当前可以继续同一论文线的写作与有限补充收口。",
            "current_required_action": current_required_action,
            "route_target": "write",
        }
    route_target = str((route_repair_plan or {}).get("route_target") or "").strip()
    if route_target:
        summary = f"核心科学质量还没有闭环；当前应先回到 {route_target} 完成最窄补充修复。"
    else:
        summary = "核心科学质量还没有闭环；当前仍需先补齐论文质量缺口。"
    return {
        "state": "quality_repair_required",
        "summary": summary,
        "current_required_action": current_required_action,
        "route_target": route_target or None,
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
    return {
        "schema_version": 1,
        "summary_id": f"evaluation-summary::{publication_eval['study_id']}::{quest_id}::{publication_eval['emitted_at']}",
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
        "quality_closure_basis": quality_closure_basis,
        "quality_review_agenda": _quality_review_agenda(
            publication_eval=publication_eval,
            gaps=gaps,
            actions=actions,
            route_repair_plan=route_repair_plan,
            quality_closure_truth=quality_closure_truth,
        ),
        "requires_controller_decision": any(bool(action.get("requires_controller_decision")) for action in actions),
        "promotion_gate_status": {
            "status": promotion_gate_payload["status"],
            "allow_write": promotion_gate_payload["allow_write"],
            "current_required_action": promotion_gate_payload["current_required_action"],
            "blockers": list(promotion_gate_payload["blockers"]),
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
    }


def _normalized_evaluation_summary(payload: dict[str, Any]) -> dict[str, Any]:
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
        "quality_closure_basis": {
            key: _coerce_quality_basis_item(
                payload=_required_mapping("evaluation summary quality_closure_basis", key, quality_closure_basis.get(key)),
                fallback_status="underdefined",
                fallback_summary="unreachable",
                fallback_refs=["unreachable"],
            )
            for key in _QUALITY_CLOSURE_BASIS_KEYS
        },
        "quality_review_agenda": _normalized_quality_review_agenda(
            agenda_payload=quality_review_agenda,
            summary_payload=payload,
        ),
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
    return _normalized_evaluation_summary(payload)


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
        json.dumps(_normalized_evaluation_summary(evaluation_summary_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "evaluation_summary_ref": {
            "summary_id": str(evaluation_summary_payload["summary_id"]),
            "artifact_path": str(evaluation_summary_path),
        },
        "promotion_gate_ref": promotion_gate_ref,
    }
