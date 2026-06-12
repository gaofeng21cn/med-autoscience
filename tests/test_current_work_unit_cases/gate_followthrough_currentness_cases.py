from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_does_not_terminally_block_actionable_gate_followthrough() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    replay_work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    actionable_work_unit_id = "medical_prose_write_repair"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T122549Z::sat_64c5fb484e8ee7b3971786ee"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{replay_work_unit_id}::{source_eval_id}"
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
                "work_unit_id": replay_work_unit_id,
                "work_unit_fingerprint": "sha256:fresh-gate-receipt",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": replay_work_unit_id,
                    "current_publication_work_unit_id": actionable_work_unit_id,
                    "explicit_work_unit_fingerprint_matches_current": False,
                    "lacks_specific_blocker_object": False,
                    "current_actionability_status": "actionable",
                },
                "current_publication_work_unit": {
                    "unit_id": actionable_work_unit_id,
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "blocking_issue_count": 3,
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "finalize",
            "work_unit_id": replay_work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
        },
        next_owner="finalize",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "finalize"
    assert work_unit["work_unit_id"] == replay_work_unit_id
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"


def test_current_work_unit_actionable_gate_followthrough_supersedes_stale_readiness_blocker() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::002::current",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["claim_evidence_consistency_failed"],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "source_eval_id": "publication-eval::002::current",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "analysis-campaign",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "analysis_claim_evidence_repair"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_actionable_gate_followthrough_supersedes_stale_zero_dispatch_closeout() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_a9b2ffcc8f97a24837d729bf::"
        "2026-06-11T12:41:21+00:00"
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
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "claim_evidence_consistency_failed",
                    "submission_hardening_incomplete",
                    "submission_surface_qc_failure_present",
                    "forbidden_manuscript_terminology",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "analysis-campaign",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "analysis-campaign",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_id": "domain_owner_action_dispatch_zero_selected_dispatch",
            "status": "blocked",
            "reason": "domain_owner_action_dispatch_zero_selected_dispatch",
            "owner": "gate_clearing_batch",
            "next_owner": "med-autoscience",
            "requested_action_type": "run_gate_clearing_batch",
            "blocker_type": "domain_owner_action_dispatch_zero_selected_dispatch",
            "blocked_reason": "domain_owner_action_dispatch_zero_selected_dispatch",
            "action_type": "run_gate_clearing_batch",
            "source_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_8365e11154b896e37d7a5344.closeout.json"
            ),
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "analysis_claim_evidence_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::497d1260db522f01"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_actionable_gate_followthrough_supersedes_consumed_typed_closeout_packet() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
    )
    gate_work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    gate_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{gate_work_unit_id}::{source_eval_id}"
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
                "work_unit_id": gate_work_unit_id,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": gate_work_unit_id,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair medical prose blockers before package readiness.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "action_fingerprint": "publication-blockers::0915410f804b3697",
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_id": "current_work_unit_already_typed_closeout_packet_required",
            "blocker_type": "current_work_unit_already_typed_closeout_packet_required",
            "blocked_reason": "current_work_unit_already_typed_closeout_packet_required",
            "reason": "current_work_unit_already_typed_closeout_packet_required",
            "owner": "one-person-lab",
            "next_owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": gate_work_unit_id,
            "work_unit_fingerprint": gate_fingerprint,
            "source_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_cbe7d09ebd4ca572b544c073.closeout.json"
            ),
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_terminal_quality_repair_next_delta_blocks_stale_gate_followthrough_identity() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    stale_work_unit_id = "analysis_claim_evidence_repair"
    canonical_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": (
                    "publication-eval::002-dm-china-us-mortality-attribution::"
                    "002-dm-china-us-mortality-attribution::stage-attempt-sat_a9b2ffcc8f97a24837d729bf::"
                    "2026-06-11T12:41:21+00:00"
                ),
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": stale_work_unit_id,
                    "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": stale_work_unit_id,
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["claim_evidence_consistency_failed"],
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_8fb0009e8384954d24ab28cf",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "work_unit_id": stale_work_unit_id,
                    "typed_blocker": {
                        "blocker_id": "opl_execution_authorization_required",
                        "owner": "one-person-lab",
                    },
                    "paper_stage_log": {
                        "stage_name": canonical_work_unit_id,
                        "outcome": "typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [
                            "opl_execution_authorization_required",
                            "opl_work_unit_binding_mismatch",
                        ],
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": canonical_work_unit_id,
                            "target_surface": {
                                "surface_ref": (
                                    "canonical manuscript story-surface delta or "
                                    "typed blocker:manuscript_story_surface_delta_missing"
                                ),
                            },
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": canonical_work_unit_id,
                            },
                        },
                    },
                    "source_path": (
                        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
                        "default_executor_execution/sat_8fb0009e8384954d24ab28cf.closeout.json"
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
            "work_unit_id": canonical_work_unit_id,
            "work_unit_fingerprint": (
                "owner-route::write::manuscript_story_surface_delta_missing::"
                "run_quality_repair_batch"
            ),
            "action_fingerprint": (
                "owner-route::write::manuscript_story_surface_delta_missing::"
                "run_quality_repair_batch"
            ),
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "terminal_stage_next_forced_delta": True,
        },
        next_owner="analysis-campaign",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == canonical_work_unit_id
    assert work_unit["state"]["blocker_type"] == "opl_execution_authorization_required"
    assert work_unit["state"]["source"] == "typed_blocker"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_status"] == "blocked"
    assert work_unit["state"]["typed_blocker"]["terminal_closeout_outcome"] == "typed_blocker"


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
        "stage_id": "domain_owner/default-executor-dispatch",
        "action_type": "run_gate_clearing_batch",
        "status": "blocked",
        "stage_name": "run_gate_clearing_batch",
        "outcome": "blocked_with_domain_typed_blocker",
        "progress_delta_classification": "typed_blocker",
        "remaining_blockers": [
            "domain_owner_action_dispatch_zero_selected_dispatch",
            "display_surface_materialization_failed",
        ],
        "source_path": (
            "/workspace/studies/002-dm-china-us-mortality-attribution/"
            "artifacts/supervision/consumer/default_executor_execution/"
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
                "domain_owner_action_dispatch_zero_selected_dispatch",
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
