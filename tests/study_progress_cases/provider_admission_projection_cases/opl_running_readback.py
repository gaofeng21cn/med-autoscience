from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.study_progress_cases.provider_admission_projection import _opl_transition_result


def test_provider_admission_projection_consumes_current_identity_running_proof(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "owner_route_currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "truth_epoch": "truth::current",
                "runtime_health_epoch": "runtime::current",
            },
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "provider_admission_pending": True,
            },
        },
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": True,
        "active_run_id": "opl-stage-attempt://sat-current-running",
        "active_stage_attempt_id": "sat-current-running",
        "active_workflow_id": "wf-current-running",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "owner_route_currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth::current",
            "runtime_health_epoch": "runtime::current",
        },
        "runtime_health": {
            "runtime_liveness_status": "live",
            "health_status": "running",
        },
        "action_queue": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "owner_route": {
                    "next_owner": "write",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "source_refs": {
                        "owner_route_currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth::current",
                            "runtime_health_epoch": "runtime::current",
                        },
                    },
                },
            }
        ],
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "study_id": study_id,
                "quest_id": study_id,
                "status": "provider_admission_pending",
                "next_executable_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "opl_domain_progress_transition_runtime_live_readback": _opl_transition_result(
                    study_id=study_id,
                    work_unit_id=work_unit_id,
                    fingerprint=fingerprint,
                ),
            }
        ],
    }

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    consumed = fields["provider_admission_running_proof_consumed"]
    assert consumed["status"] == "running_provider_attempt"
    assert consumed["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-current-running"
    assert consumed["action_type"] == "run_quality_repair_batch"
    assert consumed["work_unit_id"] == work_unit_id
    assert consumed["work_unit_fingerprint"] == fingerprint
    assert consumed["authority_boundary"]["can_start_provider_attempt"] is False
    assert consumed["authority_boundary"]["provider_running_is_paper_progress"] is False


def test_provider_admission_projection_rejects_unbound_running_proof(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": True,
        "active_run_id": "opl-stage-attempt://sat-unbound",
        "active_stage_attempt_id": "sat-unbound",
        "active_workflow_id": "wf-unbound",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "runtime_health": {
            "runtime_liveness_status": "live",
            "health_status": "running",
        },
        "action_queue": [],
    }

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
    )

    assert "provider_admission_running_proof_consumed" not in fields
    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []


def test_provider_admission_projection_consumes_terminal_closeout_after_owner_receipt(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    stage_attempt_id = "sat_f73bda556baf30ed6a9d5bdf"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = _opl_transition_result(
        study_id=study_id,
        work_unit_id=work_unit_id,
        fingerprint=fingerprint,
    )
    typed_blocker = {
        "surface_kind": "domain_stage_typed_blocker",
        "blocker_id": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
        "blocker_type": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
        "blocked_reason": "domain_owner_action_dispatch_apply_selected_zero_dispatch",
        "owner": "MedAutoScience",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "stage_attempt_id": stage_attempt_id,
        "typed_blocker_ref": (
            f"studies/{study_id}/artifacts/supervision/consumer/"
            f"default_executor_execution/{stage_attempt_id}.closeout.json"
        ),
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "active_stage_attempt_id": stage_attempt_id,
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "source": "opl_current_control_state.provider_admission_candidates",
                "study_id": study_id,
                "quest_id": study_id,
                "status": "provider_admission_pending",
                "next_executable_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "provider_attempt_or_lease_required": True,
                "opl_domain_progress_transition_runtime_live_readback": readback,
            }
        ],
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "owner_receipt_recorded",
                "typed_blocker": typed_blocker,
            },
        },
        "latest_terminal_stage_log": {
            "surface_kind": "mas_latest_terminal_stage_log_projection",
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "blocked",
            "outcome": "typed_blocker",
            "typed_blocker_ref": typed_blocker["typed_blocker_ref"],
        },
        "action_queue": [],
    }
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "owner_receipt_recorded",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "owner_receipt_recorded",
                "provider_admission_pending": False,
            },
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": True,
                "successor_owner_action": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
    }

    fields = module.provider_admission_projection_fields(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 0
    assert fields["provider_admission_candidates"] == []
    assert fields["transition_request_pending_count"] == 0
    assert fields["transition_request_candidates"] == []
    consumed = fields["provider_admission_terminal_closeout_consumed"]
    assert consumed["stage_attempt_id"] == stage_attempt_id
    assert consumed["blocker_type"] == "domain_owner_action_dispatch_apply_selected_zero_dispatch"
    assert consumed["typed_blocker"]["work_unit_id"] == work_unit_id
    assert consumed["authority_boundary"]["can_authorize_provider_admission"] is False
    assert consumed["authority_boundary"]["provider_completion_is_domain_completion"] is False
