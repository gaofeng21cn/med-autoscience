from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_latest import stable_publication_eval_latest_path
from med_autoscience.quality.study_quality import build_study_quality_truth
from med_autoscience.study_charter import resolve_study_charter_ref

from .refs_and_validation import (
    _gap_counts,
    _recommended_action_types,
    _required_mapping,
    _required_text,
    _route_repair_plan,
)
from .quality_closure_truth import (
    _load_review_ledger_context,
    _quality_closure_basis,
    _quality_closure_truth,
    _quality_execution_lane,
    _quality_review_agenda,
    _same_line_route_surface_from_summary_payload,
    _normalized_quality_execution_lane_payload,
    _normalized_quality_review_loop,
    _normalized_same_line_route_surface_payload,
    _normalized_same_line_route_truth_payload,
    _study_quality_truth_from_summary_payload,
    build_same_line_route_truth,
)
from .quality_revision_plan import (
    _quality_revision_plan,
    _quality_review_loop_from_summary_payload,
)

_OBJECTIVE_PUNCTUATION = ("，", ",", "；", ";", "。", ".", "：", ":", "、", "？", "?", "！", "!")




def _objective_compare_text(value: str) -> str:
    text = " ".join(value.split())
    for mark in _OBJECTIVE_PUNCTUATION:
        text = text.replace(f" {mark}", mark).replace(f"{mark} ", mark)
    return text



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
    eval_publication_objective = _required_text(
        "publication eval charter context ref",
        "publication_objective",
        charter_context_ref.get("publication_objective"),
    )
    if _objective_compare_text(eval_publication_objective) != _objective_compare_text(publication_objective):
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
        publication_eval=publication_eval,
        promotion_gate_payload={
            **promotion_gate_payload,
            "assessment_provenance": dict(publication_eval.get("assessment_provenance") or {}),
        },
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
