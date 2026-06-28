from __future__ import annotations

from tests.study_progress_cases import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_uses_specificity_targets_for_publication_repair_owner() -> None:
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
                "eval_id": "publication-eval::003::blocked::specific-targets",
                "verdict": {"overall_verdict": "blocked"},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::route_back_same_line::publication-blockers",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "publication gate names concrete current targets",
                        "evidence_refs": [
                            "runtime/quests/003/artifacts/reports/publishability_gate/latest.json",
                            "runtime/quests/003/artifacts/results/main_result.json",
                        ],
                        "route_target": "write",
                        "route_key_question": "Which current target blocks publication?",
                        "route_rationale": "Use specificity targets before repeating prose repair.",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "blocking_work_units": [
                            {
                                "unit_id": "medical_prose_write_repair",
                                "lane": "write",
                            },
                            {
                                "unit_id": "submission_minimal_refresh",
                                "lane": "finalize",
                            },
                        ],
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                        },
                        "specificity_targets": [
                            {
                                "target_kind": "table",
                                "target_id": "submission_minimal_authority",
                                "source_path": "paper/submission_minimal/audit/submission_manifest.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                            {
                                "target_kind": "claim",
                                "target_id": "review_ledger",
                                "source_path": "paper/review/review_ledger.json",
                                "blocking_reason": "reviewer_first_concerns_unresolved",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "paper/figures/figure_catalog.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                            {
                                "target_kind": "metric",
                                "target_id": "main_result_metrics",
                                "source_path": "runtime/quests/003/artifacts/results/main_result.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                            {
                                "target_kind": "source_path",
                                "target_id": "publication_gate_source_path",
                                "source_path": (
                                    "runtime/quests/003/artifacts/reports/"
                                    "medical_publication_surface/latest.json"
                                ),
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                        ],
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "reviewer_first_concerns_unresolved",
                        "gap_type": "review",
                        "severity": "must_fix",
                    },
                    {
                        "gap_id": "stale_submission_minimal_authority",
                        "gap_type": "submission",
                        "severity": "must_fix",
                    },
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
    assert monitoring["next_owner"] == "analysis-campaign"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "analysis_claim_evidence_repair"
    assert action["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert action["next_owner"] == "analysis-campaign"
    assert action["target_surface"]["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert [unit["unit_id"] for unit in action["target_surface"]["blocking_work_units"]] == [
        "analysis_claim_evidence_repair",
        "manuscript_story_repair",
        "submission_minimal_refresh",
    ]
    assert {ref["target_id"] for ref in action["target_surface"]["specificity_targets"]} == {
        "figure_catalog",
        "main_result_metrics",
        "publication_gate_source_path",
        "review_ledger",
        "submission_minimal_authority",
    }


def test_current_ai_reviewer_finalize_route_projects_gate_replay_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "current-ai-reviewer-record::sha256-a05623df"
    )
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "publication_eval": {
                "eval_id": eval_id,
                "verdict": {"overall_verdict": "promising", "primary_claim_status": "supported"},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::consume-current-ai-reviewer-record",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "reason": "Consume current AI reviewer record and replay publication gate.",
                        "evidence_refs": [
                            "artifacts/publication_eval/ai_reviewer_responses/current.json",
                            "artifacts/publication_eval/latest.json",
                        ],
                        "requires_controller_decision": True,
                        "route_target": "finalize",
                        "route_key_question": (
                            "Can MAS consume the current AI reviewer record and replay the gate?"
                        ),
                        "route_rationale": (
                            "Authoritative latest/gate surfaces must be updated only through "
                            "MAS owner consumption and gate replay."
                        ),
                        "work_unit_fingerprint": fingerprint,
                        "next_work_unit": {
                            "unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
                            "lane": "finalize",
                            "summary": "Materialize record-only AI reviewer archive, then gate replay.",
                        },
                    }
                ],
            },
        }
    )

    assert action is not None
    assert action["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert action["next_owner"] == "finalize"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["work_unit_id"] == "consume_current_ai_reviewer_publication_eval_record_and_replay_gate"
    assert action["work_unit_fingerprint"] == fingerprint
    assert action["publication_eval_id"] == eval_id
    assert action["required_delta_kind"] == "publication_eval_gate_replay_delta_or_typed_blocker"
    assert action["target_surface"]["route_target"] == "finalize"
    assert action["target_surface"]["surface_ref"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert action["owner_route_currentness_basis"]["source_eval_id"] == eval_id
    assert action["authority_boundary"]["can_write_runtime_owned_surfaces"] is False
    assert "publication_eval_latest_manual_write" in action["required_output_contract"]["forbidden_outputs"]
    assert "runtime_queue_or_provider_manual_write" in action["required_output_contract"]["forbidden_outputs"]


def test_current_ai_reviewer_finalize_route_supersedes_stale_repair_progress_followup() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    current_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "current-ai-reviewer-record::sha256-a05623df"
    )
    stale_repair_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "2026-06-21T10:29:56+00:00"
    )
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "dm002_same_line_publication_paper_repair",
                "source_fingerprint": "sha256:old-repair-progress",
                "source_eval_id": stale_repair_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "runtime/quests/002/artifacts/reports/publishability_gate/old.json",
                    "artifacts/controller/gate_clearing_batch/latest.json",
                ],
            },
            "publication_eval": {
                "eval_id": current_eval_id,
                "verdict": {"overall_verdict": "mixed", "primary_claim_status": "partial"},
                "recommended_actions": [
                    {
                        "action_id": "publication-eval-action::consume-current-ai-reviewer-record",
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "evidence_refs": [
                            "artifacts/publication_eval/ai_reviewer_responses/current.json",
                            "artifacts/publication_eval/latest.json",
                        ],
                        "route_target": "finalize",
                        "route_key_question": (
                            "Can MAS consume the current AI reviewer record and replay the gate?"
                        ),
                        "route_rationale": (
                            "Authoritative latest/gate surfaces must be updated only through "
                            "MAS owner consumption and gate replay."
                        ),
                        "work_unit_fingerprint": fingerprint,
                        "next_work_unit": {
                            "unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
                            "lane": "finalize",
                            "summary": "Materialize record-only AI reviewer archive, then gate replay.",
                        },
                    }
                ],
            },
        }
    )

    assert action is not None
    assert action["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert action["next_owner"] == "finalize"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "consume_current_ai_reviewer_publication_eval_record_and_replay_gate"
    assert action["publication_eval_id"] == current_eval_id
    assert action["owner_route_currentness_basis"]["source_eval_id"] == current_eval_id


def test_gate_followthrough_specificity_targets_supersede_stale_terminal_prose_ticket() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260616T042403Z::sat_07183cd27fc9f913b03dfcee"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "publication_eval": {
                "source_publication_eval": {
                    "eval_id": "publication-eval::003::source-current",
                    "verdict": {"overall_verdict": "blocked"},
                    "gaps": [
                        {"gap_id": "gap-001", "summary": "stale_submission_minimal_authority"},
                        {"gap_id": "gap-003", "summary": "reviewer_first_concerns_unresolved"},
                    ],
                    "recommended_actions": [
                        {
                            "action_id": "publication-eval-action::route-back::specific-targets",
                            "action_type": "route_back_same_line",
                            "priority": "now",
                            "route_target": "write",
                            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                            "next_work_unit": {
                                "unit_id": "medical_prose_write_repair",
                                "lane": "write",
                            },
                            "specificity_targets": [
                                {
                                    "target_kind": "table",
                                    "target_id": "submission_minimal_authority",
                                    "source_path": "paper/submission_minimal/audit/submission_manifest.json",
                                    "blocking_reason": "stale_submission_minimal_authority",
                                },
                                {
                                    "target_kind": "claim",
                                    "target_id": "review_ledger",
                                    "source_path": "paper/review/review_ledger.json",
                                    "blocking_reason": "reviewer_first_concerns_unresolved",
                                },
                                {
                                    "target_kind": "figure",
                                    "target_id": "figure_catalog",
                                    "source_path": "paper/figures/figure_catalog.json",
                                    "blocking_reason": "stale_submission_minimal_authority",
                                },
                                {
                                    "target_kind": "metric",
                                    "target_id": "main_result_metrics",
                                    "source_path": "runtime/quests/003/artifacts/results/main_result.json",
                                    "blocking_reason": "stale_submission_minimal_authority",
                                },
                                {
                                    "target_kind": "source_path",
                                    "target_id": "publication_gate_source_path",
                                    "source_path": "runtime/quests/003/artifacts/reports/medical_publication_surface/latest.json",
                                    "blocking_reason": "stale_submission_minimal_authority",
                                },
                            ],
                        }
                    ],
                }
            },
            "repair_progress_projection": {
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "source_eval_id": "publication-eval::003::newer-prose-repair",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
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
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "status": "completed",
                    "action_type": "run_quality_repair_batch",
                    "source_path": "artifacts/supervision/consumer/default_executor_execution/sat.closeout.json",
                    "paper_stage_log": {
                        "next_forced_delta": {
                            "required_delta_kind": "review_current_paper_delta",
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

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "analysis-campaign"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert action["target_surface"]["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"


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
