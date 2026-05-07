from __future__ import annotations

from pathlib import Path
from typing import Any

from .refs_and_validation import (
    _QUALITY_CLOSURE_BASIS_KEYS,
    _QUALITY_CLOSURE_STATES,
    _SAME_LINE_ROUTE_MODES,
    _SAME_LINE_ROUTE_STATES,
    _required_bool,
    _required_choice,
    _required_mapping,
    _required_string_list,
    _required_text,
    _optional_string_list,
)
from .quality_closure_truth import (
    _coerce_quality_basis_item,
    _normalized_quality_execution_lane_payload,
    _normalized_quality_review_loop,
    _normalized_same_line_route_surface_payload,
    _normalized_same_line_route_truth_payload,
    _study_quality_truth_from_summary_payload,
)
from .quality_revision_plan import (
    _normalized_quality_revision_plan,
)
from .refs_and_validation import (
    _normalized_quality_review_agenda,
)
from .study_quality_projection import normalized_study_quality_assessment_provenance
from med_autoscience.study_task_intake import read_latest_task_intake, summarize_task_intake


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
    study_quality_assessment_provenance = normalized_study_quality_assessment_provenance(
        normalized_study_quality_truth,
        study_root=study_root,
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
            **(
                {
                    "assessment_owner": _required_text(
                        "evaluation summary quality_closure_truth",
                        "assessment_owner",
                        quality_closure_truth.get("assessment_owner"),
                    )
                }
                if "assessment_owner" in quality_closure_truth
                else {}
            ),
            **(
                {
                    "ai_reviewer_required": _required_bool(
                        "evaluation summary quality_closure_truth",
                        "ai_reviewer_required",
                        quality_closure_truth.get("ai_reviewer_required"),
                    )
                }
                if "ai_reviewer_required" in quality_closure_truth
                else {}
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
            "assessment_owner": _required_choice(
                "evaluation summary study_quality_truth",
                "assessment_owner",
                normalized_study_quality_truth.get("assessment_owner")
                or study_quality_assessment_provenance.get("owner"),
                frozenset({"mechanical_projection", "ai_reviewer"}),
            ),
            "assessment_provenance": {
                "owner": _required_choice(
                    "evaluation summary study_quality_truth assessment_provenance",
                    "owner",
                    study_quality_assessment_provenance.get("owner"),
                    frozenset({"mechanical_projection", "ai_reviewer"}),
                ),
                "source_kind": _required_text(
                    "evaluation summary study_quality_truth assessment_provenance",
                    "source_kind",
                    study_quality_assessment_provenance.get("source_kind"),
                ),
                "policy_id": _required_text(
                    "evaluation summary study_quality_truth assessment_provenance",
                    "policy_id",
                    study_quality_assessment_provenance.get("policy_id"),
                ),
                "source_refs": _required_string_list(
                    "evaluation summary study_quality_truth assessment_provenance",
                    "source_refs",
                    study_quality_assessment_provenance.get("source_refs"),
                ),
                "ai_reviewer_required": _required_bool(
                    "evaluation summary study_quality_truth assessment_provenance",
                    "ai_reviewer_required",
                    study_quality_assessment_provenance.get("ai_reviewer_required"),
                ),
            },
            "ai_reviewer_required": _required_bool(
                "evaluation summary study_quality_truth",
                "ai_reviewer_required",
                normalized_study_quality_truth.get("ai_reviewer_required")
                if isinstance(normalized_study_quality_truth.get("ai_reviewer_required"), bool)
                else study_quality_assessment_provenance.get("ai_reviewer_required"),
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
