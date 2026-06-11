from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any


REQUIRED_KEYS = {
    "surface_kind",
    "schema_version",
    "status",
    "study_id",
    "quest_id",
    "stage_id",
    "owner",
    "action_type",
    "work_unit_id",
    "work_unit_fingerprint",
    "action_fingerprint",
    "input_refs",
    "required_output_contract",
    "acceptance_refs",
    "state",
    "currentness_basis",
    "authority_boundary",
}


def _module():
    return importlib.import_module("med_autoscience.controllers.current_work_unit")


def _assert_contract_shape(work_unit: Mapping[str, Any]) -> None:
    assert set(work_unit) == REQUIRED_KEYS
    assert work_unit["surface_kind"] == "current_work_unit"
    assert work_unit["schema_version"] == 1
    assert work_unit["status"] in {
        "executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "blocked_current_work_unit",
    }
    assert work_unit["authority_boundary"]["top_level_truth"] == "status"
    assert work_unit["authority_boundary"]["mas_owner_authority_preserved"] is True
    assert work_unit["authority_boundary"]["stage_transition_authority"] == "OPL Stage Transition Authority"
    assert work_unit["authority_boundary"]["stage_authority_role"] == (
        "non_authoritative_observation_and_intent_producer"
    )
    assert work_unit["authority_boundary"]["can_write_stage_current_pointer"] is False
    assert work_unit["authority_boundary"]["can_write_current_owner_delta"] is False
    assert work_unit["authority_boundary"]["can_write_stage_terminal_state"] is False


def test_current_work_unit_rejects_running_attempt_for_superseded_work_unit() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "current_owner_action_or_typed_blocker",
                "reason": "publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "action_fingerprint": (
                    "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                ),
                "work_unit_fingerprint": (
                    "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                ),
                "authority": "observability_only",
            }
        ],
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat_ea47efca5f0e95fad738d584",
            "active_stage_attempt_id": "sat_ea47efca5f0e95fad738d584",
            "active_workflow_id": "wf_983dbdfb4062990f3f74d6a7",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::0915410f804b3697",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::0915410f804b3697",
            },
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["state_kind"] == "executable_owner_action"
    assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"


def test_current_work_unit_does_not_treat_unbound_running_attempt_as_guarded_apply_progress() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "paper_autonomy/guarded-apply",
            "current_owner_delta": {
                "surface_kind": "opl_current_owner_delta",
                "default_planning_root": "current_owner_delta",
                "stage_id": "paper_autonomy/guarded-apply",
                "lineage_ref": "sat_d1bbac5b1671e6afc08d743d",
                "current_owner": "med-autoscience",
                "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                "accepted_answer_shape": [
                    "domain_owner_receipt_ref",
                    "quality_gate_receipt_ref",
                    "typed_blocker_ref",
                    "human_gate_ref",
                    "route_back_evidence_ref",
                ],
                "latest_owner_answer_ref": None,
                "domain_ready_authorized": False,
                "owner_answer_missing": True,
                "owner_answer_still_required": True,
            },
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-stale-default",
            "active_stage_attempt_id": "sat-stale-default",
            "active_workflow_id": "wf-stale-default",
            "stage_id": "domain_owner/default-executor-dispatch",
            "work_unit_id": "run_quality_repair_batch",
            "action_type": "run_quality_repair_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert work_unit["state"]["owner_answer_missing"] is True
    assert work_unit["status"] != "running_provider_attempt"


def test_current_work_unit_projects_guarded_apply_owner_answer_missing_over_stale_default_executor() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "paper_autonomy/guarded-apply",
            "current_owner_delta": {
                "surface_kind": "stage_run_current_owner_delta",
                "stage_id": "paper_autonomy/guarded-apply",
                "lineage_ref": "sat_d1bbac5b1671e6afc08d743d",
                "owner": "med-autoscience",
                "action": "paper_autonomy/guarded-apply",
                "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                "accepted_answer_shape": [
                    "domain_owner_receipt_ref",
                    "quality_gate_receipt_ref",
                    "typed_blocker_ref",
                    "human_gate_ref",
                    "route_back_evidence_ref",
                ],
                "latest_owner_answer_ref": None,
                "domain_ready_authorized": False,
                "hard_gate": {
                    "state": "owner_answer_missing",
                    "owner_answer_missing": True,
                    "owner_answer_still_required": True,
                },
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_work_unit": "stale_default_executor_repair",
                "work_unit_id": "stale_default_executor_repair",
                "work_unit_fingerprint": "stale-default-executor-fingerprint",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["action_type"] == "paper_autonomy/guarded-apply"
    assert work_unit["work_unit_id"] == "domain_owner_receipt_quality_gate_or_typed_blocker_required"
    assert work_unit["stage_id"] == "paper_autonomy/guarded-apply"
    assert work_unit["state"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert work_unit["state"]["owner_answer_missing"] is True
    assert work_unit["currentness_basis"]["lineage_ref"] == "sat_d1bbac5b1671e6afc08d743d"
    assert work_unit["required_output_contract"]["accepted_return_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert work_unit["authority_boundary"]["can_write_current_owner_delta"] is False


def test_current_work_unit_projects_nested_guarded_apply_delta_over_stale_handoff() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "surface_kind": "opl_current_owner_delta",
                    "default_planning_root": "current_owner_delta",
                    "stage_id": "paper_autonomy/guarded-apply",
                    "lineage_ref": "sat_57ba2f698a97b2bc7f64d91f",
                    "current_owner": "med-autoscience",
                    "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                    "accepted_answer_shape": [
                        "domain_owner_receipt_ref",
                        "quality_gate_receipt_ref",
                        "typed_blocker_ref",
                        "human_gate_ref",
                        "route_back_evidence_ref",
                    ],
                    "latest_owner_answer_ref": None,
                    "domain_ready_authorized": False,
                    "owner_answer_missing": True,
                    "owner_answer_still_required": True,
                },
            },
        },
        current_execution_envelope={
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "return_to_ai_reviewer_workflow",
        },
        blocked_reason="quest_waiting_opl_runtime_owner_route",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["stage_id"] == "paper_autonomy/guarded-apply"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["work_unit_id"] == "domain_owner_receipt_quality_gate_or_typed_blocker_required"
    assert work_unit["work_unit_fingerprint"] == "sat_57ba2f698a97b2bc7f64d91f"
    assert work_unit["state"]["source"] == "stage_kernel_projection.current_owner_delta"
    assert work_unit["state"]["owner_answer_missing"] is True
