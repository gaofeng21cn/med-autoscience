from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_terminal_next_forced_write_without_strong_fingerprint_is_not_executable() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "status": "completed",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "source_path": (
                        "studies/003/artifacts/supervision/consumer/"
                        "default_executor_execution/sat.closeout.json"
                    ),
                    "paper_stage_log": {
                        "next_forced_delta": {
                            "required_delta_kind": (
                                "same_line_write_repair_or_typed_blocker_consumption"
                            ),
                            "owner_action": {
                                "action_type": "return_to_write",
                                "next_owner": "write",
                                "work_unit_id": "medical_prose_write_repair",
                                "allowed_actions": ["run_quality_repair_batch"],
                            },
                        }
                    },
                }
            },
        }
    )

    assert action is None


def test_progress_first_monitoring_prefers_handoff_typed_blocker_readiness_followup_over_terminal_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {
                "overall_status": "blocked",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "literature_provider_runtime",
                    "summary": "运行联网 literature provider runtime 并写入可审计来源后再继续。",
                },
            },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "artifact_delta_present",
                    "next_missing_surface": None,
                },
                "next_owner_action": {
                    "owner": "08-publication_package_handoff",
                    "next_owner": "publication_gate_owner",
                    "action_type": "publication_handoff_owner_gate",
                    "allowed_actions": ["publication_handoff_owner_gate"],
                    "required_delta_kind": "publication_handoff_owner_receipt_or_typed_blocker",
                    "work_unit_id": "publication_handoff_owner_gate",
                    "terminal_publication_handoff": True,
                    "artifact_first_authority": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_not_ready",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                }
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["controller_action"] == "complete_medical_paper_readiness_surface"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert action["source"] == "stage_kernel_projection.current_owner_delta"
    assert action["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert action["blocked_surface"] == "publication_handoff_owner_gate"
    assert action["surface_key"] == "literature_provider_runtime"
    assert action["next_action"]["surface_key"] == "literature_provider_runtime"
    assert action["target_surface"]["surface_key"] == "literature_provider_runtime"
    assert action["artifact_first_precedence"]["typed_blocker_followup_takes_precedence"] is True


def test_progress_first_monitoring_accepts_current_stage_run_typed_blocker_answer() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "typed_blocked",
                    "stage_progress_status": "typed_blocked",
                    "manifest_present": True,
                    "typed_blocker_ref": typed_blocker_ref,
                },
                "next_owner_action": {},
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"
    assert monitoring["typed_blocker"]["source_ref"] == typed_blocker_ref


def test_progress_first_monitoring_prefers_consumed_repair_followup_over_same_publication_eval_repair() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    fingerprint = "publication-blockers::0915410f804b3697"
    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    "next_work_unit": "medical_prose_write_repair",
                },
            },
            "publication_eval": {
                "eval_id": "publication-eval::003::current",
                "verdict": {"overall_verdict": "blocked"},
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "action_id": "publication-eval-action::route-back-write",
                        "route_target": "write",
                        "work_unit_fingerprint": fingerprint,
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": "Repair structured medical reporting.",
                        },
                        "evidence_refs": ["runtime/quests/003/artifacts/reports/publishability_gate/latest.json"],
                    }
                ],
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:old-repair-progress-followup",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                "ai_reviewer_recheck_done": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "action_queue": [
                    {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "next_owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "allowed_actions": ["run_quality_repair_batch"],
                    }
                ],
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    admission = monitoring["owner_action_admission"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["owner_action_current"] is True
    assert monitoring["next_owner"] == "gate_clearing_batch"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == "publication_gate_replay"
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["work_unit_fingerprint"] == "sha256:old-repair-progress-followup"
    assert action["repair_progress_precedence"]["source_work_unit_id"] == "medical_prose_write_repair"
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is True
    assert admission["next_owner"] == "gate_clearing_batch"
    assert admission["work_unit_id"] == "publication_gate_replay"
    assert admission["provider_attempt_owner"] == "gate_clearing_batch"


def test_current_action_does_not_reopen_write_repair_after_consumed_gate_replay_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "state": {
                    "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                },
            },
            "publication_eval": {
                "eval_id": "publication-eval::003::new-blocked-eval",
                "verdict": {"overall_verdict": "blocked"},
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "route_target": "write",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": "Repair structured medical reporting.",
                        },
                    }
                ],
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:repair-progress-evidence",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                "ai_reviewer_recheck_done": True,
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": "publication_gate_replay",
                    "outcome": "blocked:opl_execution_authorization_required",
                    "paper_stage_log": {
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "work_unit_id": "publication_gate_replay",
                            "target_surface": {
                                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                            },
                            "owner_action": {
                                "next_owner": "gate_clearing_batch",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": "publication_gate_replay",
                            },
                        }
                    },
                    "source_path": "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    "evidence_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                }
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "closed_with_domain_owner_refs",
                    "paper_stage_log": {
                        "next_forced_delta": {
                            "required_delta_kind": "same_line_write_repair_or_gate_replay_route",
                            "owner_action": {
                                "next_owner": "write",
                                "action_type": "return_to_write",
                                "work_unit_id": "medical_prose_write_repair",
                            },
                        }
                    },
                }
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["terminal_stage_next_forced_delta"] is True


def test_current_action_routes_consumed_write_repair_closeout_to_ai_reviewer_successor() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    fingerprint = "publication-blockers::0915410f804b3697"

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "med-autoscience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "provider_completion_is_not_domain_ready",
                        "owner": "med-autoscience",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "typed_blocker_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat_f8e1cfe49a3aa3cf95d0584d.closeout.json"
                        ),
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "med-autoscience",
                "source": "accepted_closeout_consumed_pending",
                "typed_blocker": {
                    "blocker_type": "provider_completion_is_not_domain_ready",
                    "owner": "med-autoscience",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": fingerprint,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
                "ai_reviewer_recheck_done": True,
                "paper_delta_refs": [
                    "paper/draft.md",
                    "paper/build/review_manuscript.md",
                    "paper/evidence_ledger.json",
                ],
            },
            "publication_eval": {
                "eval_id": "publication-eval::003::still-recommends-write",
                "verdict": {"overall_verdict": "blocked"},
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "route_target": "write",
                        "work_unit_fingerprint": fingerprint,
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": "Repair structured medical reporting.",
                        },
                    }
                ],
            },
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "eval_id": "publication-eval::003::post-write-repair",
                    "action_fingerprint": fingerprint,
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "domain_transition"
    assert action["next_owner"] == "ai_reviewer"
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert action["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert action["work_unit_fingerprint"] == (
        "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
    )
    assert action["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "review",
        "surface_ref": "artifacts/publication_eval/latest.json",
    }


def test_progress_first_monitoring_derives_repair_action_from_stable_readiness_blocker_publication_eval() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "publication_eval": {
                "eval_id": "publication-eval::003::blocked::current",
                "verdict": {"overall_verdict": "blocked"},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::route_back_same_line::publication-blockers",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "medical publication surface is blocked",
                        "evidence_refs": [
                            "runtime/quests/003/artifacts/reports/publishability_gate/latest.json",
                            "runtime/quests/003/artifacts/results/main_result.json",
                        ],
                        "route_target": "write",
                        "route_key_question": "What is the narrowest same-line manuscript repair?",
                        "route_rationale": "Close reviewer-first publication-surface concerns.",
                        "work_unit_fingerprint": "publication-blockers::current",
                        "blocking_work_units": [
                            {
                                "unit_id": "medical_prose_write_repair",
                                "lane": "write",
                                "summary": "Repair structured medical reporting.",
                            }
                        ],
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": "Repair structured medical reporting.",
                        },
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "gap-001",
                        "gap_type": "reporting",
                        "severity": "must_fix",
                        "summary": "medical_publication_surface_blocked",
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    assert action["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["work_unit_fingerprint"] == "publication-blockers::current"
    assert action["target_surface_specificity"] == "publication_eval_readiness_blocker_derived_repair"
    assert action["stage_typed_blocker_ref"] == typed_blocker_ref
    assert action["publication_eval_id"] == "publication-eval::003::blocked::current"
    assert action["gap_ids"] == ["gap-001"]
    assert action["required_output_contract"]["accepted_outputs_any"] == [
        "canonical_manuscript_story_surface_delta",
        "claim_evidence_semantic_delta",
        "review_ledger_delta",
        "publication_gate_delta",
        "stage_owner_receipt_ref",
        "stable_typed_blocker_for_the_specific_repair_work_unit",
    ]
    assert action["target_surface"]["stage_typed_blocker_ref"] == typed_blocker_ref
    assert action["target_surface"]["publication_eval_id"] == "publication-eval::003::blocked::current"
    assert action["target_surface"]["gap_ids"] == ["gap-001"]
    assert action["readiness_blocker_precedence"]["superseded_readiness_action"] == (
        "complete_medical_paper_readiness_surface"
    )
    assert action["target_surface"]["gaps"][0]["summary"] == "medical_publication_surface_blocked"


def test_progress_first_monitoring_derives_repair_action_from_cutover_source_publication_eval() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "publication_eval": {
                "schema_version": 1,
                "surface_kind": "paper_authority_cutover_projection",
                "assessment_provenance": {
                    "owner": "paper_authority_cutover",
                    "source_kind": "clean_migration_receipt",
                    "ai_reviewer_required": True,
                    "mechanical_projection_used_as_quality_authority": False,
                },
                "gaps": [],
                "recommended_actions": [],
                "source_publication_eval": {
                    "eval_id": "publication-eval::003::ai-reviewer-record::current",
                    "verdict": {"overall_verdict": "blocked"},
                    "recommended_actions": [
                        {
                            "action_id": "publication-eval-action::route-back::medical-prose",
                            "action_type": "route_back_same_line",
                            "priority": "required",
                            "evidence_refs": [
                                "studies/003/artifacts/publication_eval/latest.json"
                            ],
                            "route_target": "write",
                            "route_key_question": "Which same-line prose repair closes the current gate?",
                            "route_rationale": "The current AI-reviewer eval already names the prose repair.",
                            "work_unit_fingerprint": "medical-prose-write-repair::current",
                            "next_work_unit": {
                                "unit_id": "medical_prose_write_repair",
                                "lane": "write",
                                "summary": "Repair medical prose against the current publication eval gaps.",
                            },
                        }
                    ],
                    "gaps": [
                        {
                            "gap_id": "gap-medical-prose",
                            "gap_type": "medical_prose",
                            "severity": "must_fix",
                            "summary": "medical prose still needs current same-line repair",
                        }
                    ],
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    assert action["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert action["publication_eval_id"] == "publication-eval::003::ai-reviewer-record::current"
    assert action["gap_ids"] == ["gap-medical-prose"]
    assert action["target_surface"]["gaps"][0]["gap_id"] == "gap-medical-prose"


def test_progress_first_monitoring_keeps_stage_native_repair_action_with_current_readiness_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_native_current_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "stage_native_workspace_next_action",
                "status": "ready",
                "next_owner": "write",
                "work_unit_id": "run_quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "required_delta_kind": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
                "source_ref": (
                    "studies/002-dm-china-us-mortality-attribution/control/"
                    "next_action.json"
                ),
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "run_quality_repair_batch"
    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "stage_native_workspace_next_action"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["source_ref"].endswith("control/next_action.json")
    assert monitoring["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"


def test_progress_first_monitoring_routes_repair_delta_to_ai_reviewer_over_stale_stage_native_write_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )
    repair_evidence_ref = (
        "artifacts/controller/repair_execution_evidence/latest.json"
    )
    repair_receipt_ref = (
        "artifacts/controller/repair_execution_receipts/latest.json"
    )
    ai_reviewer_request_ref = (
        "artifacts/supervision/requests/ai_reviewer/latest.json"
    )
    gate_replay_request_ref = (
        "artifacts/controller/gate_replay_requests/latest.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_progress_delta": {
                "count": 1,
                "sources": ["repair_progress_projection.mas_owner_repair_execution_evidence"],
                "refs": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                    repair_evidence_ref,
                    repair_receipt_ref,
                    ai_reviewer_request_ref,
                    gate_replay_request_ref,
                ],
            },
            "progress_first_sprint_state": {
                "paper_progress_delta_counted": True,
                "classification": "deliverable_progress",
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "progress_delta_candidate": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "repair-source-current",
                "repair_execution_evidence_ref": repair_evidence_ref,
                "owner_receipt_ref": repair_receipt_ref,
                "ai_reviewer_recheck_request_ref": ai_reviewer_request_ref,
                "gate_replay_refs": [gate_replay_request_ref],
                "changed_artifact_refs": [
                    {
                        "path": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                            "paper/draft.md"
                        ),
                        "artifact_role": "canonical_manuscript_story_surface",
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_native_current_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "stage_native_workspace_next_action",
                "status": "ready",
                "next_owner": "write",
                "work_unit_id": "run_quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "required_delta_kind": "canonical manuscript story-surface delta",
                    "source_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/control/"
                        "next_action.json"
                    ),
                },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "typed_blocked",
                    "stage_progress_status": "typed_blocked",
                    "manifest_present": True,
                    "typed_blocker_ref": typed_blocker_ref,
                },
                "next_owner_action": {
                    "owner": "08-publication_package_handoff",
                    "next_owner": "08-publication_package_handoff",
                    "action_type": "materialize_stage_artifact_delta",
                    "allowed_actions": ["materialize_stage_artifact_delta"],
                    "work_unit_id": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                    "required_delta_kind": "stage_artifact_delta",
                },
                "stages": [
                    {
                        "stage_id": "08-publication_package_handoff",
                        "stage_progress_status": "typed_blocked",
                        "manifest_present": True,
                        "typed_blocker_ref": typed_blocker_ref,
                    }
                ],
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "ai_reviewer"
    assert monitoring["controller_action"] == "return_to_ai_reviewer_workflow"
    assert monitoring["next_work_unit"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert action["work_unit_fingerprint"] == "repair-source-current"
    assert action["action_fingerprint"] == "repair-source-current"
    assert action["source_ref"] == repair_evidence_ref
    assert action["target_surface"]["surface_ref"] == "artifacts/publication_eval/latest.json"
    assert action["target_surface"]["request_ref"] == ai_reviewer_request_ref
    assert action["target_surface"]["gate_replay_request_ref"] == gate_replay_request_ref
