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
from .quality_closure_truth import (
    _quality_execution_lane_from_summary_payload,
    _normalized_quality_execution_lane_payload,
    _same_line_route_surface_from_summary_payload,
    _normalized_same_line_route_surface_payload,
    _normalized_same_line_route_truth_payload,
    _normalized_quality_review_loop,
    _quality_review_agenda,
    _fallback_refs,
    _coerce_quality_basis_item,
    _publication_gate_quality_basis,
    _quality_closure_basis,
    _quality_closure_truth,
)
from .quality_closure_truth import (
    _quality_execution_lane,
    _load_review_ledger_context,
    _study_quality_truth_from_summary_payload,
    build_same_line_route_truth,
)



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
    summary_payload = {
        **payload,
        "task_intake": summarize_task_intake(read_latest_task_intake(study_root=study_root)),
    }
    quality_execution_lane = _normalized_quality_execution_lane_payload(payload)
    same_line_route_truth = _normalized_same_line_route_truth_payload(payload)
    same_line_route_surface = _normalized_same_line_route_surface_payload(payload)
    normalized_quality_review_agenda = _normalized_quality_review_agenda(
        agenda_payload=quality_review_agenda,
        summary_payload=summary_payload,
    )
    normalized_quality_revision_plan = _normalized_quality_revision_plan(
        plan_payload=quality_revision_plan,
        summary_payload={**summary_payload, "quality_review_agenda": normalized_quality_review_agenda},
    )
    normalized_quality_review_loop = _normalized_quality_review_loop(
        loop_payload=quality_review_loop,
        summary_payload={
            **summary_payload,
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
