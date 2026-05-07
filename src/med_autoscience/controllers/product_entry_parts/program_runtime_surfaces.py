from __future__ import annotations

from typing import Any

from .shared_base import CONTROLLED_BACKEND_EXECUTOR_OWNER, TARGET_DOMAIN_ID


def _build_research_runtime_control_projection(
    *,
    resume_command: str,
    check_progress_command: str,
    check_runtime_status_command: str,
    surface_kind: str,
) -> dict[str, Any]:
    return {
        "surface_kind": surface_kind,
        "study_session_owner": {
            "runtime_owner": "upstream_hermes_agent",
            "study_owner": TARGET_DOMAIN_ID,
            "executor_owner": CONTROLLED_BACKEND_EXECUTOR_OWNER,
        },
        "session_lineage_surface": {
            "surface_kind": "study_progress",
            "field_path": "family_checkpoint_lineage",
            "resume_contract_field": "family_checkpoint_lineage.resume_contract",
            "continuation_state_field": "continuation_state",
            "active_run_id_field": "supervision.active_run_id",
        },
        "restore_point_surface": {
            "surface_kind": "study_progress",
            "field_path": "autonomy_contract.restore_point",
            "lineage_anchor_field": "family_checkpoint_lineage.resume_contract",
            "summary_field": "autonomy_contract.restore_point.summary",
        },
        "progress_cursor_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
        },
        "progress_surface": {
            "surface_kind": "study_progress",
            "field_path": "operator_status_card.current_focus",
            "fallback_field_path": "next_system_action",
        },
        "artifact_inventory_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs",
        },
        "artifact_runtime_proof_surface": {
            "surface_kind": "study_progress",
            "field_path": "artifact_runtime_proof",
            "delivery_manifest_field": "refs.artifact_runtime_proof_delivery_manifest_path",
        },
        "submission_hygiene_truth_surface": {
            "surface_kind": "study_progress",
            "field_path": "submission_hygiene_truth",
            "recommended_flow_field": "product_recommended_flow",
            "blocking_gate_keys_field": "submission_hygiene_truth.blocking_gate_keys",
        },
        "artifact_pickup_surface": {
            "surface_kind": "study_progress",
            "field_path": "refs.evaluation_summary_path",
            "fallback_fields": [
                "refs.publication_eval_path",
                "refs.medical_manuscript_blueprint_path",
                "refs.medical_journal_style_corpus_path",
                "refs.medical_prose_review_request_path",
                "refs.medical_prose_review_path",
                "refs.retrospective_medical_prose_audit_path",
                "refs.controller_decision_path",
                "refs.runtime_supervision_path",
                "refs.runtime_watch_report_path",
            ],
            "pickup_refs_field": "research_runtime_control_projection.artifact_pickup_surface.pickup_refs",
        },
        "medical_writing_quality_surface": {
            "surface_kind": "study_progress",
            "field_path": "medical_writing_quality_surfaces",
            "blueprint_field": "medical_writing_quality_surfaces.blueprint",
            "style_corpus_field": "medical_writing_quality_surfaces.style_corpus",
            "prose_review_request_field": "medical_writing_quality_surfaces.prose_review_request",
            "prose_review_field": "medical_writing_quality_surfaces.prose_review",
            "retrospective_audit_field": "medical_writing_quality_surfaces.retrospective_audit",
            "subjective_quality_owner": "ai_reviewer",
            "mechanical_flags_role": "evidence_snippets_only",
        },
        "recommended_flow_surface": {
            "surface_kind": "study_progress",
            "field_path": "product_recommended_flow",
            "default_step_field": "product_recommended_flow.recommended_step_id",
        },
        "command_templates": {
            "resume": resume_command,
            "check_progress": check_progress_command,
            "check_runtime_status": check_runtime_status_command,
        },
        "research_gate_surface": {
            "surface_kind": "study_progress",
            "approval_gate_field": "needs_user_decision",
            "approval_gate_required_field": "needs_user_decision",
            "legacy_approval_gate_field": "needs_physician_decision",
            "approval_gate_owner": "mas_controller",
            "interrupt_policy_field": "intervention_lane.recommended_action_id",
            "interrupt_policy_value_field": "intervention_lane.recommended_action_id",
            "gate_lane_field": "intervention_lane.lane_id",
            "gate_summary_field": "intervention_lane.summary",
            "human_gate_required_field": "autonomy_contract.restore_point.human_gate_required",
        },
    }
