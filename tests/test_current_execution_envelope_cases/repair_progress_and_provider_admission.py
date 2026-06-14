from __future__ import annotations

import importlib


def test_envelope_preserves_manifest_backed_stage_typed_blocker_over_handoff_queue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                },
            },
            "paper_progress_delta": {"count": 0},
            "progress_first_sprint_state": {
                "paper_progress_delta_counted": False,
            },
        },
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "source_surface": "action_queue",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"
    assert envelope["typed_blocker"]["source_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )


def test_envelope_accepts_current_provider_admission_repair_action_over_stage_readiness_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                },
            },
            "paper_progress_delta": {"count": 0},
            "progress_first_sprint_state": {
                "paper_progress_delta_counted": False,
            },
        },
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "allowed_actions": ["run_quality_repair_batch"],
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                "action_fingerprint": "sha256:dm002-current-provider-admission",
                "work_unit_fingerprint": "sha256:dm002-current-provider-admission",
            }
        ],
        blocked_reason="medical_paper_readiness_missing",
        next_owner="write",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "write"
    assert envelope["next_work_unit"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert envelope["typed_blocker"] is None


def test_envelope_accepts_materialized_provider_admission_action_over_admission_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "paper_progress_delta": {"count": 0},
            "progress_first_sprint_state": {
                "paper_progress_delta_counted": False,
            },
        },
        actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_owner": "gate_clearing_batch",
                "next_work_unit": "current_package_freshness_required",
                "work_unit_id": "current_package_freshness_required",
                "allowed_actions": ["run_gate_clearing_batch"],
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::003-dpcc::run_gate_clearing_batch",
                "action_fingerprint": "sha256:dpcc-current-provider-admission",
                "work_unit_fingerprint": "sha256:dpcc-current-provider-admission",
            }
        ],
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="one-person-lab",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "gate_clearing_batch"
    assert envelope["next_work_unit"] == "current_package_freshness_required"
    assert envelope["typed_blocker"] is None


def test_envelope_prefers_running_provider_attempt_over_owner_route_reason() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "ai_reviewer_medical_prose_quality_review",
            }
        ],
        blocked_reason="domain_transition_ai_reviewer_re_eval",
        next_owner="ai_reviewer",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "work_unit_id": "ai_reviewer_medical_prose_quality_review",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == "ai_reviewer_medical_prose_quality_review"
    assert envelope["typed_blocker"] is None


def test_envelope_preserves_non_superseded_blocker_over_running_provider_attempt() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        blocked_reason="typed_closeout_packet_required",
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "action_type": "complete_medical_paper_readiness_surface",
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
        },
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"


def test_envelope_actions_prefer_current_domain_transition_over_stale_readiness_handoff_queue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_action_projection_reconcile"
    )

    actions = module.current_execution_envelope_actions(
        handoff={
            "running_provider_attempt": False,
            "action_queue": [
                {
                    "action_type": "complete_medical_paper_readiness_surface",
                    "owner": "MedAutoScience",
                    "recommended_owner": "MedAutoScience",
                    "next_work_unit": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "fingerprint": "complete_medical_paper_readiness_surface::medical_paper_readiness_missing",
                }
            ],
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "source": "domain_transition",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["request_opl_stage_attempt"],
        },
    )

    assert actions == [
        {
            "action_type": "request_opl_stage_attempt",
            "owner": "finalize",
            "recommended_owner": "finalize",
            "next_owner": "finalize",
            "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["request_opl_stage_attempt"],
            "source_surface": "domain_transition",
            "source_ref": None,
        }
    ]


def test_envelope_actions_prefer_repair_progress_current_action_over_stale_gate_handoff_queue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_action_projection_reconcile"
    )

    actions = module.current_execution_envelope_actions(
        handoff={
            "running_provider_attempt": False,
            "action_queue": [
                {
                    "action_type": "run_gate_clearing_batch",
                    "owner": "gate_clearing_batch",
                    "recommended_owner": "gate_clearing_batch",
                    "next_work_unit": "ai_reviewer_record_gate_consumption",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
                    ),
                }
            ],
            "latest_terminal_stage_log": {
                "action_type": "run_gate_clearing_batch",
                "status": "blocked",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "blocked_reason": "opl_execution_authorization_required",
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
            "action_fingerprint": "sha256:current-ai-reviewer-record",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": ["artifacts/supervision/requests/ai_reviewer/latest.json"],
        },
    )

    assert actions == [
        {
            "action_type": "return_to_ai_reviewer_workflow",
            "owner": "ai_reviewer",
            "recommended_owner": "ai_reviewer",
            "next_owner": "ai_reviewer",
            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
            "action_fingerprint": "sha256:current-ai-reviewer-record",
            "acceptance_refs": ["artifacts/supervision/requests/ai_reviewer/latest.json"],
        }
    ]


def test_current_action_alignment_keeps_repair_progress_action_over_authorization_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )

    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        "action_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        "repair_progress_precedence": {
            "paper_delta_observed": True,
            "accepted_owner_receipt": True,
            "source_work_unit_id": "medical_prose_write_repair",
            "source_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        },
    }

    aligned = module.current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "typed_blocker": {
                "blocker_type": "opl_execution_authorization_required",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
            },
        },
    )

    assert aligned == action


def test_execution_surface_refresh_keeps_repair_progress_action_over_consumed_authorization_handoff() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )

    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "next_owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        "action_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        "repair_progress_precedence": {
            "paper_delta_observed": True,
            "accepted_owner_receipt": True,
            "source_work_unit_id": "medical_prose_write_repair",
            "source_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
        },
    }

    refreshed = module.refresh_current_execution_surfaces(
        payload={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": action,
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        },
        status={"study_id": "003-dpcc-primary-care-phenotype-treatment-gap"},
        handoff={
            "running_provider_attempt": False,
            "blocked_reason": "opl_execution_authorization_required",
            "next_owner": "one-person-lab",
            "latest_typed_default_executor_closeout": {
                "status": "blocked",
                "terminal_closeout_status": "blocked",
                "terminal_closeout_outcome": "typed_blocker",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "owner": "gate_clearing_batch",
                },
                "receipt_ref": "artifacts/supervision/consumer/default_executor_execution/sat.closeout.json",
            },
        },
        runtime_health_snapshot={},
    )

    assert refreshed["current_executable_owner_action"] == action
    assert refreshed["current_work_unit"]["status"] == "executable_owner_action"
    assert refreshed["current_work_unit"]["owner"] == "gate_clearing_batch"
    assert refreshed["current_execution_envelope"]["state_kind"] == "executable_owner_action"


def test_execution_surface_refresh_uses_paper_recovery_successor_over_gate_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    blocker_fingerprint = (
        "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    )
    successor_fingerprint = "publication-blockers::0915410f804b3697"

    refreshed = module.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "publication_eval": {"eval_id": source_eval_id},
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {"owner": "write", "authority": "med-autoscience"},
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": successor_fingerprint,
                        "source_surface": (
                            "gate_clearing_batch_followthrough.actionable_current_work_unit"
                        ),
                        "source_ref": (
                            f"/workspace/studies/{study_id}/artifacts/controller/"
                            "gate_clearing_batch/latest.json"
                        ),
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "next_owner": "write",
                    "paper_autonomy_obligation_ref": (
                        f"paper-autonomy::{study_id}::publication_supervision::"
                        f"run_gate_clearing_batch::publication_gate_replay::{blocker_fingerprint}"
                    ),
                },
            },
        },
        status={"study_id": study_id},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "blocked_reason": "publication_gate_replay_blocked",
            "next_owner": "publication_gate",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": blocker_fingerprint,
                "action_fingerprint": blocker_fingerprint,
                "state": {
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": blocker_fingerprint,
                    }
                },
            },
        },
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006847-d96308022f0a2c05"
        },
    )

    action = refreshed["current_executable_owner_action"]
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "write"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert refreshed["current_work_unit"]["status"] == "executable_owner_action"
    assert refreshed["current_work_unit"]["owner"] == "write"
    assert refreshed["current_work_unit"]["action_type"] == "run_quality_repair_batch"
    assert refreshed["current_work_unit"]["work_unit_id"] == "medical_prose_write_repair"
    assert refreshed["current_work_unit"]["work_unit_fingerprint"] == successor_fingerprint
    assert refreshed["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert refreshed["current_execution_envelope"]["owner"] == "write"
    assert refreshed["current_execution_envelope"]["typed_blocker"] is None


def test_envelope_actions_drop_stale_readiness_handoff_queue_after_paper_delta_without_current_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_action_projection_reconcile"
    )

    actions = module.current_execution_envelope_actions(
        handoff={
            "running_provider_attempt": False,
            "action_queue": [
                {
                    "action_type": "complete_medical_paper_readiness_surface",
                    "owner": "MedAutoScience",
                    "recommended_owner": "MedAutoScience",
                    "next_work_unit": "complete_medical_paper_readiness_surface",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "fingerprint": "complete_medical_paper_readiness_surface::medical_paper_readiness_missing",
                }
            ],
        },
        current_executable_owner_action={},
        paper_progress_delta_counted=True,
    )

    assert actions == []


def test_envelope_accepts_repair_progress_ai_reviewer_action_over_stage_readiness_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "paper_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "ai_reviewer_recheck_request_ref": (
                    "artifacts/supervision/requests/ai_reviewer/latest.json"
                ),
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "next_work_unit": (
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                ),
                "work_unit_id": (
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                ),
                "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                "action_fingerprint": "sha256:current-ai-reviewer-record",
            }
        ],
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert envelope["typed_blocker"] is None


def test_envelope_does_not_borrow_next_work_unit_from_stale_action_queue_for_running_attempt() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            }
        ],
        blocked_reason=None,
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
        },
        runtime_health={
            "runtime_liveness_status": "live",
            "provider_status": "running",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "sat-live"


def test_envelope_prefers_running_provider_attempt_over_stale_parked_projection() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "waiting_user_decision",
                "parked_owner": "user",
                "source_reason": "quest_waiting_for_user",
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "runtime_liveness_status": "live",
            },
        },
        progress={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "waiting_user_decision",
                "parked_owner": "user",
            },
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
        },
        actions=[
            {
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
            }
        ],
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
        runtime_health={
            "canonical_runtime_action": "continue_supervising_runtime",
            "runtime_liveness_status": "live",
        },
    )

    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "sat-live"
    assert envelope["parked_state"] is None


def test_envelope_ignores_stale_running_attempt_when_owner_action_supersedes_user_park() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "opl_runtime_refs": {
                "strict_live": False,
                "active_run_id": None,
                "runtime_liveness_status": "unknown",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
                "source_reason": "quest_waiting_for_user",
            },
        },
        actions=[
            {
                "action_type": "materialize_stage_artifact_delta",
                "owner": "08-publication_package_handoff",
                "next_work_unit": "materialize_stage_artifact_delta",
                "work_unit_fingerprint": "sha256:materialize-stage-artifact-delta",
                "action_fingerprint": "sha256:materialize-stage-artifact-delta",
            }
        ],
        next_owner="08-publication_package_handoff",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_stage_attempt_id": "sat-terminal-stale",
            "active_workflow_id": "wf-terminal-stale",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
        runtime_health={
            "canonical_runtime_action": "continue_supervising_runtime",
            "runtime_liveness_status": "unknown",
        },
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "08-publication_package_handoff"
    assert envelope["next_work_unit"] == "materialize_stage_artifact_delta"
    assert envelope["typed_blocker"] is None


def test_envelope_does_not_report_closed_stage_attempt_as_running_provider() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                "action_fingerprint": "sha256:current-ai-reviewer-record",
            }
        ],
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-closed",
            "active_stage_attempt_id": "sat-closed",
            "active_workflow_id": "wf-closed",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-closed",
                "status": "closed_with_domain_owner_refs",
                "source_path": "artifacts/supervision/consumer/default_executor_execution/sat-closed.closeout.json",
            },
        },
        runtime_health={
            "canonical_runtime_action": "continue_supervising_runtime",
            "runtime_liveness_status": "live",
        },
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"


def test_envelope_does_not_report_record_only_archive_closeout_as_running_provider() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "source": "domain_transition",
                "action_type": "run_gate_clearing_batch",
                "owner": "finalize",
                "next_owner": "finalize",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_fingerprint": "sha256:dpcc-gate-replay-current",
                "action_fingerprint": "sha256:dpcc-gate-replay-current",
            }
        ],
        next_owner="MedAutoScience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-record-only",
            "active_stage_attempt_id": "sat-record-only",
            "active_workflow_id": "wf-record-only",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-record-only",
                "status": "executed_record_only_archive_materialized",
                "source_path": (
                    "artifacts/supervision/consumer/default_executor_execution/"
                    "sat-record-only.closeout.json"
                ),
            },
        },
        runtime_health={
            "canonical_runtime_action": "continue_supervising_runtime",
            "runtime_liveness_status": "live",
        },
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "finalize"
    assert envelope["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"


def test_envelope_prefers_repair_progress_followup_over_runtime_recovery_blocker() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        progress={
            "paper_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                "action_fingerprint": "sha256:current-ai-reviewer-record",
            }
        ],
        blocked_reason="runtime_recovery_not_authorized",
        next_owner="one-person-lab",
        runtime_health={
            "canonical_runtime_action": "continue_supervising_runtime",
            "runtime_liveness_status": "unknown",
        },
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert envelope["typed_blocker"] is None


def test_envelope_preserves_explicit_typed_blocker_over_action_queue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_work_unit": "manuscript_story_repair",
            }
        ],
        blocked_reason="typed_closeout_packet_required",
        next_owner="one-person-lab",
        typed_blocker={
            "blocker_type": "typed_closeout_packet_required",
            "owner": "one-person-lab",
        },
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "one-person-lab"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "typed_closeout_packet_required"
