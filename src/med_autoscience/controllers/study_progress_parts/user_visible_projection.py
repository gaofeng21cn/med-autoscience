from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared import _mapping_copy, _non_empty_text, _status_narration_human_view

USER_VISIBLE_PROJECTION_SURFACE = "study_progress_user_visible_projection"
USER_VISIBLE_PROJECTION_READ_MODEL = "study_progress_user_visible_read_model"

_ANSWER_FOCUS = ("current_stage", "current_blockers", "next_step", "evidence")
_EVIDENCE_REF_KEYS = (
    "publication_eval_path",
    "controller_decision_path",
    "controller_confirmation_summary_path",
    "runtime_supervision_path",
    "runtime_watch_report_path",
    "runtime_status_summary_path",
    "evaluation_summary_path",
    "medical_paper_readiness_path",
    "study_truth_snapshot_path",
    "runtime_health_snapshot_path",
    "bash_summary_path",
    "details_projection_path",
)


def build_user_visible_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    human_view = _status_narration_human_view(payload)
    current_stage = _non_empty_text(human_view.get("current_stage")) or _non_empty_text(payload.get("current_stage"))
    current_stage_summary = (
        _non_empty_text(payload.get("current_stage_summary"))
        or _non_empty_text(human_view.get("latest_update"))
        or _non_empty_text(human_view.get("status_summary"))
    )
    next_system_action = _non_empty_text(payload.get("next_system_action")) or _non_empty_text(
        human_view.get("next_step")
    )
    current_blockers = _normalized_texts(payload.get("current_blockers") or human_view.get("current_blockers"))
    evidence = _evidence_projection(payload)
    return {
        "surface": USER_VISIBLE_PROJECTION_SURFACE,
        "read_model": USER_VISIBLE_PROJECTION_READ_MODEL,
        "schema_version": 1,
        "authority": "truth_projection",
        "projection_only": True,
        "answer_focus": list(_ANSWER_FOCUS),
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "current_stage": current_stage,
        "current_stage_label": _non_empty_text(human_view.get("current_stage_label")),
        "current_stage_summary": current_stage_summary,
        "status_summary": _non_empty_text(human_view.get("status_summary")),
        "paper_stage": _non_empty_text(payload.get("paper_stage")),
        "paper_stage_summary": _non_empty_text(payload.get("paper_stage_summary")),
        "current_blockers": current_blockers,
        "next_system_action": next_system_action,
        "next_step": next_system_action,
        "needs_user_decision": bool(payload.get("needs_user_decision")),
        "needs_physician_decision": bool(payload.get("needs_physician_decision")),
        "supervision": _supervision_projection(payload),
        "evidence": evidence,
        "conditions": _projection_conditions(
            current_stage=current_stage,
            current_stage_summary=current_stage_summary,
            current_blockers=current_blockers,
            next_system_action=next_system_action,
            needs_user_decision=bool(payload.get("needs_user_decision")),
            supervision=_mapping_copy(payload.get("supervision")),
            evidence=evidence,
        ),
    }


def _normalized_texts(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in items:
            items.append(text)
    return items


def _evidence_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping_copy(payload.get("refs"))
    return {
        "latest_events": [
            dict(item)
            for item in payload.get("latest_events") or []
            if isinstance(item, dict)
        ],
        "refs": {key: refs.get(key) for key in _EVIDENCE_REF_KEYS if refs.get(key) is not None},
    }


def _supervision_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    supervision = _mapping_copy(payload.get("supervision"))
    return {
        "browser_url": _non_empty_text(supervision.get("browser_url")),
        "quest_session_api_url": _non_empty_text(supervision.get("quest_session_api_url")),
        "active_run_id": _non_empty_text(supervision.get("active_run_id")),
        "health_status": _non_empty_text(supervision.get("health_status")),
        "supervisor_tick_status": _non_empty_text(supervision.get("supervisor_tick_status")),
    }


def _projection_conditions(
    *,
    current_stage: str | None,
    current_stage_summary: str | None,
    current_blockers: list[str],
    next_system_action: str | None,
    needs_user_decision: bool,
    supervision: dict[str, Any],
    evidence: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        _condition(
            "stage_known",
            bool(current_stage),
            "stage_present" if current_stage else "stage_missing",
            current_stage_summary or current_stage,
        ),
        _condition(
            "blocked",
            bool(current_blockers),
            "blockers_present" if current_blockers else "no_current_blockers",
            current_blockers[0] if current_blockers else "当前没有新的卡点。",
        ),
        _condition(
            "next_action_known",
            bool(next_system_action),
            "next_action_present" if next_system_action else "next_action_missing",
            next_system_action,
        ),
        _condition(
            "evidence_available",
            bool(evidence.get("latest_events") or evidence.get("refs")),
            "evidence_refs_present" if evidence.get("latest_events") or evidence.get("refs") else "evidence_missing",
            "关键证据引用可用。" if evidence.get("latest_events") or evidence.get("refs") else "缺少关键证据引用。",
        ),
        _condition(
            "human_decision_required",
            needs_user_decision,
            "user_gate_present" if needs_user_decision else "user_gate_absent",
            "当前需要用户判断。" if needs_user_decision else "当前不需要用户判断。",
        ),
        _condition(
            "runtime_supervised",
            bool(
                _non_empty_text(supervision.get("active_run_id"))
                or _non_empty_text(supervision.get("health_status"))
                or _non_empty_text(supervision.get("supervisor_tick_status"))
            ),
            "supervision_signal_present",
            _non_empty_text(supervision.get("health_status")) or _non_empty_text(supervision.get("active_run_id")),
        ),
    ]


def _condition(condition_type: str, status: bool, reason: str, message: str | None) -> dict[str, str]:
    return {
        "type": condition_type,
        "status": "true" if status else "false",
        "reason": reason,
        "message": message or "",
    }
