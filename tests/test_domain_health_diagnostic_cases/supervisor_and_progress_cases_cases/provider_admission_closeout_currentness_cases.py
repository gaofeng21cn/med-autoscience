from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_materialized_current_control_clears_candidate_after_stage_closeout_evidence_list(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "consumer_default_executor_dispatch",
        "next_executable_owner": "write",
        "required_output_surface": "canonical manuscript story-surface delta",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T05:50:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "stage_attempt_closeouts": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_attempt_id": "sat_0509b60217115954f91ac564",
                        "action_type": "run_quality_repair_batch",
                        "blocked_reason": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                        "typed_blocker": {
                            "blocker_id": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                            "action_fingerprint": fingerprint,
                        },
                        "owner_route_currentness": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                            "source_eval_id": "publication-eval::003::current-ai-reviewer",
                        },
                        "typed_blocker_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_0509b60217115954f91ac564.closeout.json"
                        ),
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "next_work_unit": None,
                    "typed_blocker": {
                        "blocker_id": "terminal_closeout_owner_answer_required",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                    "parked_state": None,
                    "source": "terminal_closeout_precedes_live_projection",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["active_stage_attempt_id"] == "sat_0509b60217115954f91ac564"
    assert decision["evidence_status"] == "blocked"


def test_materialized_current_control_retains_record_only_closeout_without_currentness(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "canonical manuscript story-surface delta",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "source_eval_id": "publication-eval::003::current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-13T01:15:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "stage_attempt_id": "sat_record_only_without_currentness",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                        "record_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                        "raw_closeout_work_unit_fingerprint_present": False,
                        "raw_closeout_action_fingerprint_present": False,
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert len(result["action_queue"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint


def test_materialized_current_control_prefers_terminal_closeout_over_stale_running_projection_from_evidence_list(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "canonical manuscript story-surface delta",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T05:50:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "running",
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat_0509b60217115954f91ac564",
                "active_workflow_id": "wf_cb79e18337ca2a02faf44a95",
                "opl_provider_attempt": {
                    "running_provider_attempt": True,
                    "active_stage_attempt_id": "sat_0509b60217115954f91ac564",
                    "active_workflow_id": "wf_cb79e18337ca2a02faf44a95",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "provider_status": "running",
                },
                "stage_attempt_closeouts": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_attempt_id": "sat_0509b60217115954f91ac564",
                        "action_type": "run_quality_repair_batch",
                        "typed_blocker": {
                            "blocker_id": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                            "action_fingerprint": fingerprint,
                        },
                        "owner_route_currentness": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "terminal_closeout_precedes_live_projection": 1,
    }
    study = result["studies"][0]
    assert study["running_provider_attempt"] is False
    assert study["current_execution_envelope"]["state_kind"] == "terminal_closeout_observed"
    assert study["current_execution_envelope"]["next_work_unit"] == work_unit_id


def test_report_current_control_clears_candidate_from_typed_blocker_closeout_without_current_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-11T05:50:00+00:00",
            "managed_study_opl_provider_admission_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "next_executable_owner": "write",
                    "required_output_surface": "canonical manuscript story-surface delta",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                }
            ],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "status": "typed_blocker",
                            "owner": "one-person-lab",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                        },
                        "current_execution_envelope": {
                            "state_kind": "typed_blocker",
                            "owner": "one-person-lab",
                            "typed_blocker": {
                                "blocker_id": "terminal_closeout_owner_answer_required",
                                "stage_attempt_id": "sat_0509b60217115954f91ac564",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                        },
                        "stage_attempt_closeouts": [
                            {
                                "surface_kind": "stage_attempt_closeout_packet",
                                "status": "blocked",
                                "stage_attempt_id": "sat_0509b60217115954f91ac564",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": work_unit_id,
                                "typed_blocker": {
                                    "blocker_id": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                                    "action_fingerprint": fingerprint,
                                },
                                "work_unit_fingerprint": fingerprint,
                                "owner_route_currentness": {
                                    "work_unit_id": work_unit_id,
                                    "work_unit_fingerprint": fingerprint,
                                    "truth_epoch": "truth-event-current",
                                    "runtime_health_epoch": "runtime-health-current",
                                },
                            }
                        ],
                    },
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }


def test_report_current_control_suppresses_dm003_repeat_suppressed_gate_replay_from_progress_terminal_stage(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
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

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-11T07:41:37+00:00",
            "managed_study_opl_provider_admission_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                }
            ],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "gate_clearing_batch",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "currentness_basis": {
                                "source_eval_id": source_eval_id,
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
                                "runtime_health_epoch": "runtime-health-event-006633-a8a0feb0a8750b82",
                            },
                        },
                        "current_executable_owner_action": {
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
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": work_unit_id,
                        },
                        "progress_first_monitoring_summary": {
                            "latest_terminal_stage": {
                                "stage_id": "domain_owner/default-executor-dispatch",
                                "action_type": "run_gate_clearing_batch",
                                "status": "repeat_suppressed",
                                "stage_name": work_unit_id,
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "action_fingerprint": fingerprint,
                                "outcome": "repeat_suppressed",
                                "progress_delta_classification": "typed_blocker",
                                "source_path": (
                                    "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                                    "artifacts/supervision/consumer/default_executor_execution/latest.json"
                                ),
                            },
                        },
                    }
                }
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["evidence_status"] == "repeat_suppressed"
    assert decision["no_progress_signal"] == "same_work_unit_repeat_suppressed_terminal_stage"
    assert decision["anti_loop_classification"] == "provider_admission_echo"
    assert decision["route_identity_key"] == f"provider-admission::{study_id}::{fingerprint}"
    assert decision["attempt_idempotency_key"] == f"provider-admission::{study_id}::{fingerprint}"


def test_report_current_control_retains_dm002_current_pending_over_stale_anti_loop_closeout_file(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
    closeout_ref = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_82a2b164657c9b4d0c312db9.closeout.json"
    )
    dump_json(
        closeout_ref,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "stage_attempt_id": "sat_82a2b164657c9b4d0c312db9",
            "stage_id": "domain_owner/default-executor-dispatch",
            "status": "closed_with_typed_blocker",
            "outcome": "repeat_suppressed_with_typed_blocker",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "schema_version": 1,
                "blocker_kind": "anti_loop_budget_exhausted",
                "reason": "anti_loop_budget_exhausted",
                "blocker_id": "opl_execution_authorization_required",
                "owner": "one-person-lab",
                "write_permitted": False,
                "anti_loop_budget": {
                    "status": "exhausted",
                    "study_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                    "work_unit_fingerprint": (
                        "owner-route::write::manuscript_story_surface_delta_missing::"
                        "run_quality_repair_batch"
                    ),
                    "blocker_reason": "opl_execution_authorization_required",
                },
            },
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "schema_version": 1,
                "status": "available",
                "stage_name": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "stage_work_done": [
                    "Observed MAS domain dispatch result execution_status=repeat_suppressed, "
                    "blocked_reason=anti_loop_budget_exhausted, and typed blocker "
                    "opl_execution_authorization_required."
                ],
                "paper_work_done": [
                    "No manuscript, paper package, current package, publication gate, controller decision, "
                    "medical result value, quality verdict, or submission-readiness surface was modified."
                ],
                "changed_stage_surfaces": [
                    "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
                    "default_executor_execution/sat_82a2b164657c9b4d0c312db9.closeout.json"
                ],
                "changed_paper_surfaces": [],
                "outcome": "typed_blocker_anti_loop_budget_exhausted",
                "remaining_blockers": [
                    "MAS domain dispatch suppressed another run_quality_repair_batch attempt for the same "
                    "action fingerprint after anti-loop budget exhaustion."
                ],
                "duration": {"status": "missing", "seconds": None},
                "token_usage": {
                    "status": "missing",
                    "total_tokens": None,
                },
                "cost": {"status": "missing", "usd": None},
                "progress_delta_classification": "typed_blocker",
                "next_forced_delta": {
                    "reason": "anti_loop_budget_exhausted_for_run_quality_repair_batch_same_action_fingerprint",
                },
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-11T21:28:34+00:00",
            "managed_study_opl_provider_admission_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "provider_admission_pending",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "next_executable_owner": "analysis-campaign",
                    "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                }
            ],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "analysis-campaign",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "currentness_basis": {
                                "source_eval_id": (
                                    "publication-eval::002-dm-china-us-mortality-attribution::"
                                    "stage-attempt-sat_a9b2ffcc8f97a24837d729bf"
                                ),
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
                                "runtime_health_epoch": "runtime-health-event-006868-be729a0387218e86",
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                            "next_owner": "analysis-campaign",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "action_type": "run_quality_repair_batch",
                            "allowed_actions": ["run_quality_repair_batch"],
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "analysis-campaign",
                            "next_work_unit": work_unit_id,
                        },
                    }
                }
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert len(result["action_queue"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint
