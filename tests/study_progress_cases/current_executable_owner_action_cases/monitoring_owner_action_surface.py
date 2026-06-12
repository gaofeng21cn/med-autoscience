from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_exposes_actionable_gate_followthrough_repair_work_unit() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T122549Z::sat_64c5fb484e8ee7b3971786ee"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "finalize",
                "typed_blocker": {
                    "blocker_id": "publication_gate_replay_blocked",
                    "owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": (
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/gate_clearing_batch/latest.json"
                ),
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    assert monitoring["typed_blocker"] is None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["source_eval_id"] == source_eval_id


def test_current_owner_action_prefers_actionable_gate_followthrough_over_consumed_repair_followup() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    consumed_repair_fingerprint = "sha256:consumed-repair-delta"

    action = module.build_current_executable_owner_action(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": consumed_repair_fingerprint,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
            },
            "domain_transition": {
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": consumed_repair_fingerprint,
                }
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": (
                    "publication-eval::002-dm-china-us-mortality-attribution::"
                    "ai-reviewer-record::current"
                ),
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
            "next_forced_delta": {
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "analysis-campaign"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]


def test_current_owner_action_prefers_actionable_gate_followthrough_over_stale_readiness_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "medical_paper_readiness": {
                "overall_status": "blocked",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "authoring_runtime_authorization",
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_kind": "typed_blocker",
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::current"
                ),
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": (
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["medical_publication_surface_blocked"],
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]


def test_current_owner_action_prefers_terminal_gate_next_delta_over_stale_gate_followthrough() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "ai-reviewer-record::20260611T191558Z::sat_69f93a256b45113b077ab71a"
                ),
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": (
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["medical_publication_surface_blocked"],
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "blocked",
                    "action_type": "run_gate_clearing_batch",
                    "paper_stage_log": {
                        "stage_name": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                        "outcome": "blocked:{'blocker_id': 'opl_execution_authorization_required'}",
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                            "target_surface": {
                                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            },
                            "acceptance_refs": [
                                "owner_receipt_ref",
                                "typed_blocker_ref",
                                "changed_surface_ref",
                            ],
                            "owner_action": {
                                "next_owner": "gate_clearing_batch",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": (
                                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                                ),
                            },
                        },
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"


def test_current_owner_action_prefers_terminal_quality_repair_next_delta_over_stale_gate_followthrough() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
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
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_dm002_current_quality_repair",
                    "status": "blocked",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "source_path": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_dm002_current_quality_repair.closeout.json"
                    ),
                    "paper_stage_log": {
                        "stage_name": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                        "outcome": "typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "target_surface": {
                                "surface_ref": (
                                    "canonical manuscript story-surface delta or "
                                    "typed blocker:manuscript_story_surface_delta_missing"
                                ),
                            },
                            "acceptance_refs": [
                                "owner_receipt_ref",
                                "typed_blocker_ref",
                                "changed_surface_ref",
                            ],
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            },
                        },
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert action["target_surface"]["surface_ref"].startswith("canonical manuscript story-surface delta")
    assert action["terminal_stage_next_forced_delta"] is True


def test_current_owner_action_stop_loss_typed_blocker_blocks_stale_gate_followthrough() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_fingerprint": (
                    "owner-route::write::manuscript_story_surface_delta_missing::"
                    "run_quality_repair_batch"
                ),
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "blocker_type": "anti_loop_budget_exhausted",
                    "typed_blocker": {
                        "surface_kind": "mas_domain_typed_blocker",
                        "blocker_kind": "anti_loop_budget_exhausted",
                        "reason": "anti_loop_budget_exhausted",
                        "blocker_id": "opl_execution_authorization_required",
                        "blocked_reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                        "work_unit_fingerprint": (
                            "owner-route::write::manuscript_story_surface_delta_missing::"
                            "run_quality_repair_batch"
                        ),
                        "source_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_82a2b164657c9b4d0c312db9.closeout.json"
                        ),
                        "anti_loop_budget": {
                            "status": "exhausted",
                            "action_type": "run_quality_repair_batch",
                        },
                    },
                },
            },
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
        }
    )

    assert action is None


def test_progress_first_monitoring_prefers_repair_followup_over_stale_readiness_queue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "action_type": "return_to_ai_reviewer_workflow",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "owner_receipt_required": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-stale-readiness",
                "active_stage_attempt_id": "sat-stale-readiness",
                "active_workflow_id": "wf-stale-readiness",
                "runtime_health": {"runtime_liveness_status": "attempt_running"},
                "action_queue": [
                    {
                        "action_type": "complete_medical_paper_readiness_surface",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "fingerprint": "complete_medical_paper_readiness_surface::medical_paper_readiness_missing",
                        "consumption_status": "unconsumed",
                    }
                ],
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-stale-readiness"
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "ai_reviewer"
    assert monitoring["controller_action"] == "return_to_ai_reviewer_workflow"
    assert monitoring["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert monitoring["current_executable_owner_action"]["source"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    admission = monitoring["owner_action_admission"]
    assert admission["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_running_proven"] is False
    assert admission["provider_attempt_proof"] is None


def test_progress_first_monitoring_requires_running_provider_proof_for_current_write_action_without_queue_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "one-person-lab",
                "active_run_id": "opl-stage-attempt://sat-stale-gate",
                "active_stage_attempt_id": "sat-stale-gate",
                "active_workflow_id": "wf-stale-gate",
                "runtime_health": {"runtime_liveness_status": "live"},
                "action_queue": [],
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-stale-gate"
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    admission = monitoring["owner_action_admission"]
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_running_proven"] is False
    assert admission["provider_attempt_proof"] is None


def test_progress_first_monitoring_keeps_paper_line_owner_delta_and_platform_repair_accounting_separate() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    paper_line_monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "progress_first_sprint_state": {
                "classification": "deliverable_progress",
                "paper_progress_delta_counted": True,
                "platform_repair_delta_counted": False,
                "deliverable_progress_delta": {
                    "count": 1,
                    "owner_receipt_refs": [
                        "artifacts/controller/gate_clearing_batch/latest.json#owner_receipt"
                    ],
                },
                "platform_repair_delta": {"count": 0},
            },
        }
    )

    assert paper_line_monitoring["progress_delta_classification"] == "deliverable_progress"
    assert paper_line_monitoring["paper_progress_delta_counted"] is True
    assert paper_line_monitoring["platform_repair_delta_counted"] is False

    platform_repair_monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["produce_publication_eval"],
            },
            "progress_first_sprint_state": {
                "classification": "platform_repair",
                "paper_progress_delta_counted": False,
                "platform_repair_delta_counted": True,
                "deliverable_progress_delta": {"count": 0},
                "platform_repair_delta": {
                    "count": 1,
                    "refs": ["runtime/artifacts/supervision/opl_current_control_state/latest.json#read_model_hygiene"],
                },
            },
            "opl_current_control_state_handoff": {
                "stage_progress_log": {
                    "attempt_count": 1,
                    "missing_usage_telemetry_attempt_count": 1,
                    "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
                },
            },
        }
    )

    assert platform_repair_monitoring["progress_delta_classification"] == "platform_repair"
    assert platform_repair_monitoring["paper_progress_delta_counted"] is False
    assert platform_repair_monitoring["platform_repair_delta_counted"] is True
    assert platform_repair_monitoring["owner_action_admission"]["admission_requested"] is True
    assert platform_repair_monitoring["owner_action_admission"]["hard_gate_blocked"] is False
    assert platform_repair_monitoring["owner_action_admission"]["observability_diagnostics"] == [
        {
            "diagnostic": "missing_usage_telemetry",
            "authority": "observability_only",
            "attempt_count": 1,
            "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
        }
    ]

def test_progress_first_monitoring_treats_missing_telemetry_and_closeout_as_observability_diagnostics_not_admission_gates() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["produce_publication_eval"],
            },
            "opl_current_control_state_handoff": {
                "stage_progress_log": {
                    "attempt_count": 1,
                    "missing_usage_telemetry_attempt_count": 1,
                    "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
                },
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat-closeout-missing",
                    "status": "completed",
                    "missing_user_stage_log_fields": [
                        "stage_work_done",
                        "paper_work_done",
                        "changed_stage_surfaces",
                        "changed_paper_surfaces",
                        "progress_delta_classification",
                    ],
                    "missing_observability_fields": ["duration", "token_usage", "cost"],
                },
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_start_requested"] is True
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_blocked"] is False
    assert admission["hard_gate_reasons"] == []
    assert admission["observability_diagnostics"] == [
        {
            "diagnostic": "missing_usage_telemetry",
            "authority": "observability_only",
            "attempt_count": 1,
            "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
        },
        {
            "diagnostic": "terminal_closeout_observability_incomplete",
            "authority": "observability_only",
            "stage_attempt_id": "sat-closeout-missing",
            "missing_user_stage_log_fields": [
                "stage_work_done",
                "paper_work_done",
                "changed_stage_surfaces",
                "changed_paper_surfaces",
                "progress_delta_classification",
            ],
            "missing_observability_fields": ["duration", "token_usage", "cost"],
        },
    ]


def test_progress_first_monitoring_projects_canonical_current_work_unit_aliases() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "canonical_gate_replay_unit",
                "required_output_contract": {
                    "owner_receipt_required": True,
                    "typed_blocker_accepted": True,
                    "accepted_terminal_results": ["owner_receipt", "typed_blocker"],
                    "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
                    "target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "finalize",
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
                "acceptance_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
            "next_forced_delta": {
                "required_delta_kind": "stale_delta",
                "work_unit_id": "stale_delta_unit",
                "owner_action": {
                    "next_owner": "stale-owner",
                    "work_unit_id": "stale_delta_unit",
                    "allowed_actions": ["stale_action"],
                },
            },
        }
    )

    assert monitoring["current_work_unit"]["work_unit_id"] == "canonical_gate_replay_unit"
    assert monitoring["owner_action_current"] is True
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == "canonical_gate_replay_unit"
    assert monitoring["next_forced_delta"]["required_delta_kind"] == (
        "publication_gate_replay_delta_or_typed_blocker"
    )
    assert monitoring["next_forced_delta"]["work_unit_id"] == "canonical_gate_replay_unit"
    assert monitoring["next_forced_delta"]["owner_action"]["next_owner"] == "finalize"


def test_progress_first_monitoring_keeps_terminal_domain_blocker_over_artifact_and_repeat_gate_actions() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "artifact_os",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "display_surface_materialization_failed",
                        "blocked_reason": "display_surface_materialization_failed",
                        "owner": "artifact_os",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "terminal_closeout_status": "blocked",
                        "terminal_closeout_outcome": "blocked_with_domain_typed_blocker",
                    },
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": work_unit_id,
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": work_unit_id,
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
            },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "artifact_native_contract_ref": "mas-opl-stage-native-artifact-contract.v1",
                "stale_platform_repairs": ["sat_857dcf8b3164f75dfd037e22"],
                "next_owner_action": {
                    "next_owner": "08-publication_package_handoff",
                    "work_unit_id": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                    "allowed_actions": ["materialize_stage_artifact_delta"],
                    "required_delta_kind": "stage_artifact_delta",
                },
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "active_stage_attempt_id": "sat_857dcf8b3164f75dfd037e22",
                "action_queue": [],
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_857dcf8b3164f75dfd037e22",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "paper_stage_log": {
                        "stage_name": "run_gate_clearing_batch",
                        "outcome": "blocked_with_domain_typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [
                            "display_surface_materialization_failed",
                            "template_execution_mode_mismatch",
                        ],
                        "next_forced_delta": {
                            "required_delta_kind": "repair_display_surface_materialization_then_replay_gate",
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "artifact_os",
                                "action_type": "artifact_display_surface_materialization_required",
                            },
                        },
                    },
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["owner_action_current"] is False
    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["owner_action_admission"] is None
    assert monitoring["typed_blocker"]["blocker_type"] == "display_surface_materialization_failed"
    assert monitoring["next_owner"] == "artifact_os"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == work_unit_id


def test_progress_first_monitoring_prefers_canonical_typed_blocker_over_stale_terminal_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": (
                    "owner-route::write::manuscript_story_surface_delta_missing::"
                    "run_quality_repair_batch"
                ),
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "surface_kind": "mas_domain_typed_blocker",
                        "blocker_type": "anti_loop_budget_exhausted",
                        "blocker_kind": "anti_loop_budget_exhausted",
                        "reason": "anti_loop_budget_exhausted",
                        "blocker_id": "opl_execution_authorization_required",
                        "blocked_reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": (
                            "owner-route::write::manuscript_story_surface_delta_missing::"
                            "run_quality_repair_batch"
                        ),
                    },
                },
            },
            "current_blockers": [
                "quest marked running but no live session",
                "stale owner-route handoff residue",
            ],
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "action_queue": [],
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_stale_terminal",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "source_path": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_stale_terminal.closeout.json"
                    ),
                    "paper_stage_log": {
                        "stage_name": "run_quality_repair_batch",
                        "outcome": "blocked_with_domain_typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": ["opl_execution_authorization_required"],
                        "next_forced_delta": {
                            "required_delta_kind": "legacy_runtime_owner_route",
                            "work_unit_id": "stale_runtime_authorization",
                            "owner_action": {
                                "next_owner": "one-person-lab",
                                "action_type": "recover_runtime",
                            },
                        },
                    },
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["typed_blocker"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert monitoring["typed_blocker"]["work_unit_id"] == work_unit_id
    assert monitoring["next_owner"] == "one-person-lab"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == work_unit_id
    assert monitoring["current_blockers"] == ["anti_loop_budget_exhausted"]


__all__ = [name for name in globals() if name.startswith("test_")]
