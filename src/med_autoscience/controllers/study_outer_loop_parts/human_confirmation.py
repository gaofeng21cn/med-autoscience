from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_runtime_family_orchestration as family_orchestration
from med_autoscience.controller_confirmation_summary import (
    read_controller_confirmation_summary,
    stable_controller_confirmation_summary_path,
)
from med_autoscience.runtime_escalation_record import RuntimeEscalationRecordRef
from med_autoscience.study_decision_record import (
    StudyDecisionCharterRef,
    StudyDecisionControllerAction,
    StudyDecisionPublicationEvalRef,
    StudyDecisionRecord,
)


def _build_family_human_gates_for_decision_record(
    *,
    requires_human_confirmation: bool,
    emitted_at: str,
    study_id: str,
    evidence_refs: list[dict[str, str]],
    controller_actions: tuple[StudyDecisionControllerAction, ...],
) -> list[dict[str, Any]]:
    if not requires_human_confirmation:
        return []
    return [
        family_orchestration.build_family_human_gate(
            gate_id=f"controller-human-confirmation-{study_id}",
            gate_kind="controller_human_confirmation",
            requested_at=emitted_at,
            request_surface_kind="controller_decisions",
            request_surface_id="controller_decisions/latest.json",
            evidence_refs=evidence_refs,
            decision_options=["approve", "request_changes", "reject"],
        )
    ]


def _build_human_confirmation_request(
    *,
    study_id: str,
    summary: str,
    runtime_status: dict[str, str],
    runtime_escalation_ref: RuntimeEscalationRecordRef,
    publication_eval_payload: dict[str, Any],
    controller_actions: tuple[StudyDecisionControllerAction, ...],
) -> dict[str, Any]:
    verdict = publication_eval_payload.get("verdict")
    gaps = publication_eval_payload.get("gaps")
    publication_blockers: list[dict[str, Any]] = []
    if isinstance(verdict, dict):
        publication_blockers.append(
            {
                "overall_verdict": str(verdict.get("overall_verdict") or "").strip(),
                "primary_claim_status": str(verdict.get("primary_claim_status") or "").strip(),
                "summary": str(verdict.get("summary") or "").strip(),
                "gap_summaries": [
                    str(item.get("summary") or "").strip()
                    for item in gaps
                    if isinstance(item, dict) and str(item.get("summary") or "").strip()
                ]
                if isinstance(gaps, list)
                else [],
            }
        )
    first_action = controller_actions[0].action_type.value if controller_actions else "controller_review"
    return {
        "category": "controller_decision_confirmation",
        "summary": summary,
        "runtime_blockers": [
            {
                "decision": str(runtime_status.get("decision") or "").strip(),
                "reason": str(runtime_status.get("reason") or "").strip(),
                "record_id": runtime_escalation_ref.record_id,
                "summary_ref": runtime_escalation_ref.summary_ref,
            }
        ],
        "publication_blockers": publication_blockers,
        "current_required_action": "human_confirmation_required",
        "controller_actions": [action.to_dict() for action in controller_actions],
        "question_for_user": f"Approve controller action `{first_action}` for study `{study_id}`?",
    }


def _controller_confirmation_pending(*, study_root: Path) -> bool:
    summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    if not summary_path.exists():
        return False
    summary = read_controller_confirmation_summary(
        study_root=study_root,
        ref=summary_path,
    )
    return str(summary.get("status") or "").strip() == "pending"


def _latest_controller_decision_requires_human_confirmation(*, study_root: Path) -> bool:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    if not decision_path.exists():
        return False
    payload = json.loads(decision_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("controller decision latest artifact must contain a mapping payload")
    return StudyDecisionRecord.from_payload(payload).requires_human_confirmation


def _latest_controller_decision_matches_spec(
    *,
    study_root: Path,
    decision_type: str,
    requires_human_confirmation: bool,
    reason: str,
    charter_ref: StudyDecisionCharterRef | dict[str, Any],
    publication_eval_ref: StudyDecisionPublicationEvalRef | dict[str, Any],
    controller_actions: tuple[StudyDecisionControllerAction, ...] | list[dict[str, Any]],
    runtime_escalation_ref: RuntimeEscalationRecordRef | dict[str, Any] | None,
    route_target: str | None = None,
    route_key_question: str | None = None,
    route_rationale: str | None = None,
) -> bool:
    latest_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    if not latest_path.exists():
        return False
    payload = json.loads(latest_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("controller decision latest artifact must contain a mapping payload")
    record = StudyDecisionRecord.from_payload(payload)
    desired_charter_ref = (
        charter_ref if isinstance(charter_ref, StudyDecisionCharterRef) else StudyDecisionCharterRef.from_payload(charter_ref)
    )
    desired_publication_eval_ref = (
        publication_eval_ref
        if isinstance(publication_eval_ref, StudyDecisionPublicationEvalRef)
        else StudyDecisionPublicationEvalRef.from_payload(publication_eval_ref)
    )
    desired_controller_actions = tuple(
        action if isinstance(action, StudyDecisionControllerAction) else StudyDecisionControllerAction.from_payload(action)
        for action in controller_actions
    )
    desired_runtime_escalation_ref = (
        runtime_escalation_ref
        if isinstance(runtime_escalation_ref, RuntimeEscalationRecordRef)
        else RuntimeEscalationRecordRef.from_payload(runtime_escalation_ref)
        if isinstance(runtime_escalation_ref, dict)
        else None
    )
    if record.decision_type.value != decision_type:
        return False
    if record.requires_human_confirmation is not requires_human_confirmation:
        return False
    if record.reason != reason:
        return False
    if record.route_target != route_target:
        return False
    if record.route_key_question != route_key_question:
        return False
    if record.route_rationale != route_rationale:
        return False
    if record.charter_ref.to_dict() != desired_charter_ref.to_dict():
        return False
    if record.publication_eval_ref.to_dict() != desired_publication_eval_ref.to_dict():
        return False
    if tuple(action.to_dict() for action in record.controller_actions) != tuple(
        action.to_dict() for action in desired_controller_actions
    ):
        return False
    if desired_runtime_escalation_ref is None:
        return True
    return record.runtime_escalation_ref.to_dict() == desired_runtime_escalation_ref.to_dict()

