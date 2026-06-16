from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_suppresses_gate_replay_receipt_consumed_owner_action() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_3961f4c4b2e9335879a17891"
    )
    current_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "consumption_status": "receipt_consumed",
                    "receipt_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    "receipt_kind": "gate_clearing_batch",
                    "execution_status": "executed",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "canonical_work_unit_identity": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                        ),
                        "source_eval_id": source_eval_id,
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": current_fingerprint,
            "action_fingerprint": current_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["action_type"] is None
    assert work_unit["work_unit_id"] is None
    assert work_unit["state"]["blocker_type"] == "current_work_unit_unresolved"


def test_current_work_unit_treats_repeat_suppressed_gate_replay_terminal_stage_as_typed_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_3961f4c4b2e9335879a17891"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "repeat_suppressed",
                    "stage_name": work_unit_id,
                    "outcome": "repeat_suppressed",
                    "progress_delta_classification": "typed_blocker",
                    "source_path": (
                        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/supervision/consumer/default_executor_execution/latest.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert work_unit["state"]["stale_queue_or_handoff_can_override"] is False


def test_current_work_unit_does_not_turn_handoff_ready_terminal_log_into_typed_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "handoff_ready",
                    "stage_name": work_unit_id,
                    "outcome": "handoff_ready",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": [],
                    "source_path": (
                        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                        "default_executor_execution/latest.json"
                    ),
                    "paper_stage_log": {
                        "outcome": "handoff_ready",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [],
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "reason": "no_deliverable_delta_observed",
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": work_unit_id,
                            },
                        },
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "owner_receipt_required": True,
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": True,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            },
            "owner_route_currentness_basis": {
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_uses_write_repair_after_executed_ai_reviewer_receipt_over_stale_gate_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "auto_runtime_parked",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_fdeabae35e46694c6f8dacd2",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "executed",
                    "outcome": "owner_receipt",
                    "progress_delta_classification": "deliverable_progress",
                    "changed_paper_surfaces": [
                        "studies/003/artifacts/publication_eval/ai_reviewer_responses/"
                        "20260612T100912Z_publication_eval_record.json"
                    ],
                    "source_path": (
                        "studies/003/artifacts/supervision/consumer/default_executor_execution/"
                        "sat_fdeabae35e46694c6f8dacd2.closeout.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "target_surface": {
                "ref_kind": "publication_eval_recommended_action",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_kind": "current_typed_blocker_precedes_provider_admission",
            "blocker_type": "current_typed_blocker_precedes_provider_admission",
            "blocked_reason": "current_typed_blocker_precedes_provider_admission",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "source_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_b2652a75945b6ed8fb16148e.closeout.json"
            ),
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["state"]["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"


def test_current_work_unit_uses_remaining_blocker_for_executed_typed_closeout() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T122549Z::sat_64c5fb484e8ee7b3971786ee"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "stage_attempt_id": "sat_c0348bcfa41849926ebb46f9",
                    "action_type": "run_gate_clearing_batch",
                    "status": "executed",
                    "stage_name": work_unit_id,
                    "outcome": "typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": [
                        "publication_gate_replay_blocked",
                        "medical_publication_surface_blocked",
                    ],
                    "source_path": (
                        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_c0348bcfa41849926ebb46f9.closeout.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "finalize",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="finalize",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "publication_gate"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["blocker_type"] == "publication_gate_replay_blocked"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_status"] == "executed"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_outcome"] == "typed_blocker"


def test_current_work_unit_gate_replay_executed_log_uses_gate_blocked_reason() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "publication_gate_replay"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "surface_kind": "mas_latest_terminal_stage_log_projection",
                    "action_type": "run_gate_clearing_batch",
                    "status": "executed",
                    "stage_name": work_unit_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "source_eval_id": source_eval_id,
                    "outcome": "executed",
                    "progress_delta_classification": "typed_blocker",
                    "gate_replay_status": "blocked",
                    "gate_replay_blockers": [
                        "medical_publication_surface_blocked",
                        "reviewer_first_concerns_unresolved",
                    ],
                    "paper_stage_log": {
                        "outcome": "executed",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [],
                    },
                    "source_path": (
                        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                        "default_executor_execution/latest.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "publication_gate"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["blocker_type"] == "publication_gate_replay_blocked"
    assert work_unit["state"]["typed_blocker"]["gate_replay_status"] == "blocked"
    assert work_unit["state"]["typed_blocker"]["gate_replay_blockers"] == [
        "medical_publication_surface_blocked",
        "reviewer_first_concerns_unresolved",
    ]
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_outcome"] == "executed"


def test_current_work_unit_preserves_same_identity_gate_replay_typed_closeout_over_admission() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_execution/sat_eb4ae953c9b1fd3ada29360f.closeout.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "stage_attempt_id": "sat_eb4ae953c9b1fd3ada29360f",
                    "action_type": "run_gate_clearing_batch",
                    "status": "closed_with_domain_owner_refs",
                    "stage_name": work_unit_id,
                    "outcome": "typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": ["publication_gate_replay_blocked"],
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "source_path": closeout_ref,
                    "typed_blocker": {
                        "surface_kind": "mas_domain_typed_blocker",
                        "owner": "gate_clearing_batch",
                        "blocker_type": "publication_gate_replay_blocked",
                        "reason": "publication_gate_replay_blocked",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "owner_receipt_ref": f"{closeout_ref}#owner_receipt",
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": (
                "publication-eval::002-dm-china-us-mortality-attribution::"
                "002-dm-china-us-mortality-attribution::stage-attempt-sat_a9b2ffcc8f97a24837d729bf::"
                "2026-06-11T12:41:21+00:00"
            ),
        },
        provider_admission={
            "provider_admission_pending_count": 1,
            "provider_attempt_or_lease_required": True,
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "publication_gate"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["blocker_type"] == "publication_gate_replay_blocked"
    assert work_unit["state"]["typed_blocker"]["owner_receipt_ref"] == f"{closeout_ref}#owner_receipt"


def test_current_work_unit_terminal_quality_repair_next_delta_blocks_stale_gate_followthrough_identity() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    fingerprint = "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch"
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_execution/sat_quality_repair.closeout.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "paper_autonomy/guarded-apply",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "stage_id": "paper_autonomy/guarded-apply",
                    "owner": "MedAutoScience",
                    "current_owner": "MedAutoScience",
                    "action": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                    "desired_delta": "domain_owner_receipt_quality_gate_or_typed_blocker_required",
                    "owner_answer_missing": True,
                    "owner_answer_still_required": True,
                    "domain_ready_authorized": True,
                    "accepted_answer_shape": [
                        "domain_owner_receipt_ref",
                        "quality_gate_receipt_ref",
                        "typed_blocker_ref",
                    ],
                    "hard_gate": {"state": "owner_answer_missing"},
                },
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "stage_attempt_id": "sat_quality_repair",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "stage_name": work_unit_id,
                    "outcome": "typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": ["manuscript_story_surface_delta_missing"],
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "source_path": closeout_ref,
                    "paper_stage_log": {
                        "stage_name": "run_quality_repair_batch",
                        "outcome": "typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": ["manuscript_story_surface_delta_missing"],
                        "next_forced_delta": {
                            "required_delta_kind": "review_current_paper_delta",
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "allowed_actions": ["run_quality_repair_batch"],
                                "owner_receipt_required": True,
                            },
                        },
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "terminal_stage_next_forced_delta": True,
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["blocker_type"] == "manuscript_story_surface_delta_missing"


def test_current_work_unit_projects_gate_action_over_matching_currentness_blocker_from_live_handoff() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_current::2026-06-11T11:30:58+00:00"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::002-dm-china-us-mortality-attribution::"
        f"{work_unit_id}::{source_eval_id}"
    )
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "study_progress.next_forced_delta.owner_action",
        "next_owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "review_current_paper_delta",
    }
    blocker = {
        "blocker_id": "gate_clearing_batch_source_eval_currentness_mismatch",
        "blocker_type": "gate_clearing_batch_source_eval_currentness_mismatch",
        "owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "currentness_basis": {
            "source": "study_progress.next_forced_delta.owner_action",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": work_unit_id,
                "work_unit_id": work_unit_id,
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_surface": "study_progress.next_forced_delta.owner_action",
            }
        ],
        current_executable_owner_action=current_action,
        live_provider_attempt={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat_live_without_identity",
            "active_stage_attempt_id": "sat_live_without_identity",
            "active_workflow_id": "wf_live_without_identity",
            "blocked_reason": "gate_clearing_batch_source_eval_currentness_mismatch",
            "next_owner": "gate_clearing_batch",
            "typed_blocker": blocker,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
        typed_blocker=blocker,
        blocked_reason="gate_clearing_batch_source_eval_currentness_mismatch",
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_next_forced_delta_over_stale_owner_route_closeout() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_current::2026-06-11T12:41:21+00:00"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::002-dm-china-us-mortality-attribution::"
        f"{work_unit_id}::{source_eval_id}"
    )
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "study_progress.next_forced_delta.owner_action",
        "next_owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "review_current_paper_delta",
    }
    stale_blocker = {
        "blocker_id": "owner_route_stale",
        "blocker_type": "owner_route_stale",
        "owner": "write",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": "sha256:stale-publication-gate-replay",
        "source_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat_0f1a9f5d24d067c53e89b342.closeout.json"
        ),
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "stage_attempt_id": "sat_0f1a9f5d24d067c53e89b342",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": "publication_gate_replay",
                    "outcome": "typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": ["owner_route_stale"],
                    "source_path": (
                        "/workspace/studies/002-dm-china-us-mortality-attribution/"
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_0f1a9f5d24d067c53e89b342.closeout.json"
                    ),
                },
            },
        },
        current_executable_owner_action=current_action,
        typed_blocker=stale_blocker,
        blocked_reason="owner_route_stale",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_uses_latest_terminal_handoff_domain_blocker_over_repeat_gate_replay_action() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_current::2026-06-11T12:41:21+00:00"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::002-dm-china-us-mortality-attribution::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_857dcf8b3164f75dfd037e22",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "typed_blocker_ref": (
                        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                        "consumer/default_executor_execution/sat_857dcf8b3164f75dfd037e22.closeout.json"
                        "#typed_blocker"
                    ),
                    "paper_stage_log": {
                        "stage_name": "run_gate_clearing_batch",
                        "outcome": "blocked_with_domain_typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [
                            "display_surface_materialization_failed",
                            "template_execution_mode_mismatch",
                            "publication_gate_replay_blocked",
                        ],
                        "next_forced_delta": {
                            "required_delta_kind": "repair_display_surface_materialization_then_replay_gate",
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "artifact_os",
                                "action_type": "artifact_display_surface_materialization_required",
                                "reason": "display_surface_materialization_failed",
                            },
                        },
                    },
                    "source_path": (
                        "/workspace/studies/002-dm-china-us-mortality-attribution/"
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_857dcf8b3164f75dfd037e22.closeout.json"
                    ),
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "review_current_paper_delta",
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "artifact_os"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["blocker_type"] == "display_surface_materialization_failed"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_status"] == "blocked"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_outcome"] == (
        "blocked_with_domain_typed_blocker"
    )


def test_current_work_unit_reports_consumed_gate_replay_blocker_after_fresh_gate_receipt() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_current::2026-06-11T12:41:21+00:00"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::002-dm-china-us-mortality-attribution::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": "sha256:fresh-gate-receipt",
                "gate_replay_status": "blocked",
                "blocking_issue_count": 2,
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "claim_evidence_consistency_failed",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_58099ea2494e3ed8eb6f978a",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": work_unit_id,
                    "outcome": "blocked_with_domain_typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": [
                        "domain_owner_action_dispatch_zero_selected_dispatch",
                        "display_surface_materialization_failed",
                    ],
                    "source_path": (
                        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                        "default_executor_execution/sat_58099ea2494e3ed8eb6f978a.closeout.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "publication_gate"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["blocker_type"] == "publication_gate_replay_blocked"
    assert work_unit["state"]["typed_blocker"]["gate_replay_status"] == "blocked"
    assert work_unit["state"]["typed_blocker"]["gate_replay_blockers"] == [
        "medical_publication_surface_blocked",
        "claim_evidence_consistency_failed",
    ]
    assert work_unit["state"]["typed_blocker"]["source_ref"].endswith(
        "/artifacts/controller/gate_clearing_batch/latest.json"
    )
