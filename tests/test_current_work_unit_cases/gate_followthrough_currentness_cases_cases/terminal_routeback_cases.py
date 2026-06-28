from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_terminal_gate_routeback_action_supersedes_same_closeout_gate_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    closeout_ref = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapter_receipt/sat_e4dbaf4c7df74333010d29ae.closeout.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_e4dbaf4c7df74333010d29ae",
                    "stage_id": "stage_outcome/opl-handoff",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "status": "blocked",
                    "outcome": "blocked:publication_gate_replay_blocked",
                    "progress_delta_classification": "typed_blocker",
                    "paper_stage_log": {
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "publication_gate_replay",
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "return_to_write",
                                "work_unit_id": "reviewer_first_publication_surface_repair",
                            },
                        },
                    },
                    "source_path": closeout_ref,
                    "closeout_refs": [closeout_ref],
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": "reviewer_first_publication_surface_repair",
            "work_unit_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "terminal_stage_next_forced_delta": True,
            "acceptance_refs": [closeout_ref],
        },
        typed_blocker={
            "surface_kind": "mas_typed_blocker",
            "blocker_id": "publication_gate_replay_blocked",
            "blocker_type": "publication_gate_replay_blocked",
            "blocked_reason": "publication_gate_replay_blocked",
            "owner": "write",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "reviewer_first_publication_surface_repair",
            "source_ref": closeout_ref,
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "reviewer_first_publication_surface_repair"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"


def test_current_work_unit_terminal_gate_routeback_action_supersedes_prior_readiness_answer() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    closeout_ref = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapter_receipt/sat_e4dbaf4c7df74333010d29ae.closeout.json"
    )
    readiness_ref = (
        f"/workspace/studies/{study_id}/artifacts/stage_outputs/"
        "08-publication_package_handoff/receipts/typed_blocker.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "current_owner_delta": {
                        "owner": "MedAutoScience",
                        "action": "complete_medical_paper_readiness_surface",
                        "reason": "medical_paper_readiness_missing",
                        "required_input": "complete_medical_paper_readiness_surface",
                        "source_ref": readiness_ref,
                        "source_kind": "typed_blocker",
                    },
                },
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_ref": readiness_ref,
                    "source_kind": "typed_blocker",
                },
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_e4dbaf4c7df74333010d29ae",
                    "stage_id": "stage_outcome/opl-handoff",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "status": "blocked",
                    "outcome": "blocked:publication_gate_replay_blocked",
                    "progress_delta_classification": "typed_blocker",
                    "paper_stage_log": {
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "publication_gate_replay",
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "return_to_write",
                                "work_unit_id": "reviewer_first_publication_surface_repair",
                            },
                        },
                    },
                    "source_path": closeout_ref,
                    "closeout_refs": [closeout_ref],
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": "reviewer_first_publication_surface_repair",
            "work_unit_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "terminal_stage_next_forced_delta": True,
            "acceptance_refs": [closeout_ref],
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "reviewer_first_publication_surface_repair"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"


def test_current_work_unit_terminal_gate_routeback_action_accepts_live_closeout_without_terminal_work_unit() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    closeout_ref = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapter_receipt/sat_e4dbaf4c7df74333010d29ae.closeout.json"
    )
    relative_closeout_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/owner_callable_adapter_receipt/"
        "sat_e4dbaf4c7df74333010d29ae.closeout.json"
    )
    readiness_ref = (
        f"/workspace/studies/{study_id}/artifacts/stage_outputs/"
        "08-publication_package_handoff/receipts/typed_blocker.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "stage_kernel_projection": {
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "current_owner_delta": {
                        "owner": "MedAutoScience",
                        "action": "complete_medical_paper_readiness_surface",
                        "reason": "medical_paper_readiness_missing",
                        "required_input": "complete_medical_paper_readiness_surface",
                        "source_ref": readiness_ref,
                        "source_kind": "typed_blocker",
                    },
                },
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_ref": readiness_ref,
                    "source_kind": "typed_blocker",
                },
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_e4dbaf4c7df74333010d29ae",
                    "stage_id": "stage_outcome/opl-handoff",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "outcome": "blocked:publication_gate_replay_blocked",
                    "progress_delta_classification": "typed_blocker",
                    "source_path": closeout_ref,
                    "closeout_refs": [relative_closeout_ref],
                    "next_forced_delta": {
                        "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                        "work_unit_id": "publication_gate_replay",
                        "owner_action": {
                            "next_owner": "write",
                            "action_type": "return_to_write",
                            "work_unit_id": "reviewer_first_publication_surface_repair",
                        },
                    },
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": "reviewer_first_publication_surface_repair",
            "work_unit_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_fingerprint": "route-currentness::003-dpcc-primary-care-phenotype-treatment-gap::fresh",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "terminal_stage_next_forced_delta": True,
            "acceptance_refs": [closeout_ref, "owner_receipt_ref", "typed_blocker_ref"],
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "reviewer_first_publication_surface_repair"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"


def test_current_work_unit_prefers_raw_terminal_handoff_over_flattened_monitoring_summary() -> None:
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
    terminal_summary = {
        "stage_attempt_id": "sat_58099ea2494e3ed8eb6f978a",
        "stage_id": "stage_outcome/opl-handoff",
        "action_type": "run_gate_clearing_batch",
        "status": "blocked",
        "stage_name": "run_gate_clearing_batch",
        "outcome": "blocked_with_domain_typed_blocker",
        "progress_delta_classification": "typed_blocker",
        "remaining_blockers": [
            "stage_outcome_authority_zero_selected_dispatch",
            "display_surface_materialization_failed",
        ],
        "source_path": (
            "/workspace/studies/002-dm-china-us-mortality-attribution/"
            "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
            "sat_58099ea2494e3ed8eb6f978a.closeout.json"
        ),
    }
    raw_terminal_handoff = {
        **terminal_summary,
        "paper_stage_log": {
            "stage_name": "run_gate_clearing_batch",
            "outcome": "blocked_with_domain_typed_blocker",
            "progress_delta_classification": "typed_blocker",
            "remaining_blockers": [
                "stage_outcome_authority_zero_selected_dispatch",
                "display_surface_materialization_failed",
                "template_execution_mode_mismatch",
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
                "latest_terminal_stage": terminal_summary,
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": raw_terminal_handoff,
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
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["blocker_type"] == "display_surface_materialization_failed"
