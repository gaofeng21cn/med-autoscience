from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_handoff_action_keeps_scalar_remaining_blocker_text() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    action = module.current_owner_handoff_action(
        {
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "handoff_ready",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "paper_stage_log": {
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": "ai_reviewer_record_stale_after_current_inputs",
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["blocked_reason"] == "ai_reviewer_record_stale_after_current_inputs"


def test_current_owner_handoff_action_ignores_structured_remaining_blocker_payload() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    action = module.current_owner_handoff_action(
        {
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "handoff_ready",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "paper_stage_log": {
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": {
                            "reason": "ai_reviewer_record_stale_after_current_inputs"
                        },
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["blocked_reason"] is None


def test_terminal_stage_log_missing_user_progress_fields_projects_typed_blocker(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-001.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": "001-risk",
            "stage_attempt_id": "sat-001",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "completed",
            "generated_at": "2026-05-31T01:00:00+00:00",
            "closeout_refs": ["artifacts/supervision/consumer/default_executor_execution/sat-001.json"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "current_story_surface_repair",
                "problem_summary": "Story-surface repair attempt reached provider completion.",
                "stage_goal": "Produce a user-readable repair delta or stable blocker.",
                "outcome": "completed",
                "remaining_blockers": [],
                "duration": {"seconds": 42},
                "token_usage": {"total_tokens": 1200},
                "cost": {"usd": 0.04},
                "usage_refs": ["usage://sat-001"],
                "cost_refs": ["cost://sat-001"],
                "evidence_refs": [
                    "artifacts/supervision/consumer/default_executor_execution/sat-001.json"
                ],
            },
        },
    )

    handoff = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id="001-risk",
    )

    assert handoff is not None
    terminal_log = handoff["latest_terminal_stage_log"]
    assert terminal_log["status"] == "typed_blocker"
    assert terminal_log["typed_blocker_reason"] == "typed_closeout_packet_required"
    assert terminal_log["diagnostic"] == "user_stage_log_missing_required_progress_fields"
    assert terminal_log["missing_user_stage_log_fields"] == [
        "stage_work_done",
        "paper_work_done",
        "changed_stage_surfaces",
        "changed_paper_surfaces",
        "progress_delta_classification",
    ]
    assert terminal_log["missing_domain_fields"] == terminal_log["missing_user_stage_log_fields"]
    assert terminal_log["semantic_gap"] == {
        "reason": "domain_closeout_provided_incomplete_user_stage_log",
        "missing_domain_fields": [
            "stage_work_done",
            "paper_work_done",
            "changed_stage_surfaces",
            "changed_paper_surfaces",
            "progress_delta_classification",
        ],
        "source": "paper_stage_log",
        "owner": "MedAutoScience",
    }
    assert terminal_log["paper_stage_log"]["outcome"] == "typed_blocker"
    assert terminal_log["paper_stage_log"]["remaining_blockers"] == [
        "typed_closeout_packet_required"
    ]


def test_terminal_stage_log_infers_missing_delta_classification_from_paper_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.opl_current_control_state_handoff"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat-002.closeout.json"
    )
    _write_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": "001-risk",
            "stage_attempt_id": "sat-002",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "completed",
            "generated_at": "2026-05-31T01:00:00+00:00",
            "closeout_refs": ["artifacts/supervision/consumer/default_executor_execution/sat-002.json"],
            "paper_stage_log": {
                "surface_kind": "mas_paper_facing_stage_log_summary",
                "stage_name": "current_story_surface_repair",
                "problem_summary": "Story-surface repair produced manuscript-facing changes.",
                "stage_goal": "Produce a user-readable repair delta or stable blocker.",
                "stage_work_done": ["Updated manuscript-facing surfaces."],
                "paper_work_done": ["Updated manuscript-facing surfaces."],
                "changed_stage_surfaces": [
                    "studies/001-risk/paper/draft.md",
                ],
                "changed_paper_surfaces": [
                    "studies/001-risk/paper/draft.md",
                ],
                "outcome": "completed",
                "remaining_blockers": [],
                "duration": {"seconds": 42},
                "token_usage": {"total_tokens": 1200},
                "cost": {"usd": 0.04},
                "usage_refs": ["usage://sat-002"],
                "cost_refs": ["cost://sat-002"],
                "evidence_refs": [
                    "artifacts/supervision/consumer/default_executor_execution/sat-002.json"
                ],
            },
        },
    )

    handoff = module.opl_current_control_state_study_handoff_projection(
        profile=profile,
        study_id="001-risk",
    )

    assert handoff is not None
    terminal_log = handoff["latest_terminal_stage_log"]
    assert terminal_log["status"] == "completed"
    assert "typed_blocker_reason" not in terminal_log
    assert terminal_log["missing_user_stage_log_fields"] == ["progress_delta_classification"]
    assert terminal_log["paper_stage_log"]["progress_delta_classification"] == "deliverable_progress"
    assert (
        terminal_log["paper_stage_log"]["progress_delta_classification_source"]
        == "inferred_from_changed_paper_surfaces"
    )


def test_progress_first_monitoring_projects_terminal_closeout_semantic_completeness() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "001-risk",
            "progress_delta_classification": "platform_repair",
            "next_forced_delta": {
                "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                "work_unit_id": "publishability_repair_sprint",
                "target_surface": {"surface_ref": "canonical_manuscript"},
                "owner_action": {
                    "next_owner": "runtime_mechanism_repair",
                    "work_unit_id": "publishability_repair_sprint",
                },
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat-001",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "typed_blocker",
                    "typed_blocker_reason": "typed_closeout_packet_required",
                    "diagnostic": "user_stage_log_missing_required_progress_fields",
                    "missing_user_stage_log_fields": [
                        "paper_work_done",
                        "progress_delta_classification",
                    ],
                    "observability_status": "missing",
                    "missing_observability_fields": ["token_usage", "cost"],
                    "duration": {"seconds": 42},
                    "token_usage": {},
                    "cost": {},
                    "closeout_refs": [
                        "artifacts/supervision/consumer/default_executor_execution/sat-001.json"
                    ],
                    "paper_stage_log": {
                        "outcome": "typed_blocker",
                        "stage_work_done": ["Checked the provider closeout."],
                        "changed_stage_surfaces": ["artifacts/supervision/current_control_state/latest.json"],
                        "changed_paper_surfaces": [],
                        "remaining_blockers": ["typed_closeout_packet_required"],
                        "evidence_refs": [
                            "artifacts/supervision/consumer/default_executor_execution/sat-001.json"
                        ],
                    },
                },
            },
        }
    )

    terminal = monitoring["latest_terminal_stage"]
    assert terminal["changed_stage_surfaces"] == [
        "artifacts/supervision/current_control_state/latest.json"
    ]
    assert terminal["progress_delta_classification"] is None
    assert terminal["missing_user_stage_log_fields"] == [
        "paper_work_done",
        "progress_delta_classification",
    ]
    assert terminal["missing_domain_fields"] == [
        "paper_work_done",
        "progress_delta_classification",
    ]
    assert terminal["semantic_gap"] == {
        "reason": "domain_closeout_provided_incomplete_user_stage_log",
        "missing_domain_fields": [
            "paper_work_done",
            "progress_delta_classification",
        ],
        "source": "paper_stage_log",
        "owner": "MedAutoScience",
    }
    assert terminal["missing_observability_fields"] == ["token_usage", "cost"]
    completeness = terminal["terminal_closeout_semantic_completeness"]
    assert completeness == {
        "status": "typed_blocker",
        "required_user_stage_log_fields": "missing",
        "missing_user_stage_log_fields": [
            "paper_work_done",
            "progress_delta_classification",
        ],
        "changed_surfaces": "present",
        "changed_stage_surfaces": "present",
        "changed_paper_surfaces": "present_empty",
        "progress_delta_classification": "missing",
        "telemetry": "missing",
        "missing_telemetry_fields": ["token_usage", "cost"],
        "typed_blocker": "typed_closeout_packet_required",
        "typed_blocker_diagnostic": "user_stage_log_missing_required_progress_fields",
        "semantic_gap": {
            "reason": "domain_closeout_provided_incomplete_user_stage_log",
            "missing_domain_fields": [
                "paper_work_done",
                "progress_delta_classification",
            ],
            "source": "paper_stage_log",
            "owner": "MedAutoScience",
        },
        "next_forced_delta": {
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "work_unit_id": "publishability_repair_sprint",
            "target_surface": {"surface_ref": "canonical_manuscript"},
            "owner_action": {
                "next_owner": "runtime_mechanism_repair",
                "work_unit_id": "publishability_repair_sprint",
            },
        },
    }


def test_progress_first_monitoring_treats_current_work_unit_typed_blocker_as_not_running() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "MedAutoScience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::0915410f804b3697",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::0915410f804b3697",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_selected_by_domain_owner_action_dispatch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::0915410f804b3697",
                },
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat_stale_or_superseded",
                "active_stage_attempt_id": "sat_stale_or_superseded",
                "active_workflow_id": "wf_stale_or_superseded",
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat_stale_or_superseded"
    )
    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["typed_blocker"]["blocker_type"] == (
        "stage_packet_not_selected_by_domain_owner_action_dispatch"
    )


def test_progress_first_monitoring_counts_paper_delta_despite_missing_closeout_observability() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_forced_delta": {
                "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "owner_action": {
                    "next_owner": "ai_reviewer",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                },
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat-003",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "executed",
                    "missing_user_stage_log_fields": ["progress_delta_classification"],
                    "observability_status": "missing",
                    "missing_observability_fields": ["duration", "token_usage", "cost"],
                    "duration": {},
                    "token_usage": {},
                    "cost": {},
                    "paper_stage_log": {
                        "stage_name": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                        "problem_summary": "Repair produced paper-facing artifact changes.",
                        "stage_goal": "Produce manuscript-facing deltas or a stable blocker.",
                        "outcome": "executed",
                        "stage_work_done": ["Recorded paper-facing artifact changes."],
                        "paper_work_done": ["Recorded paper-facing artifact changes."],
                        "changed_stage_surfaces": [
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                        ],
                        "changed_paper_surfaces": [
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                        ],
                        "remaining_blockers": [],
                        "evidence_refs": [
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                        ],
                    },
                },
            },
        }
    )

    assert monitoring["typed_blocker"] is None
    assert monitoring["progress_delta_classification"] == "deliverable_progress"
    terminal = monitoring["latest_terminal_stage"]
    assert terminal["progress_delta_classification"] == "deliverable_progress"
    completeness = terminal["terminal_closeout_semantic_completeness"]
    assert completeness["status"] == "complete"
    assert completeness["typed_blocker"] is None
    assert completeness["telemetry"] == "missing"
    assert completeness["missing_telemetry_fields"] == ["duration", "token_usage", "cost"]
    assert (
        completeness["progress_delta_classification_source"]
        == "inferred_from_changed_paper_surfaces"
    )


def test_progress_first_monitoring_counts_stage_delta_despite_missing_closeout_observability() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "next_forced_delta": {
                "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                "work_unit_id": "unit_harmonized_external_validation_rerun",
                "owner_action": {
                    "next_owner": "analysis_harmonization_owner",
                    "work_unit_id": "unit_harmonized_external_validation_rerun",
                },
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat-002",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "executed",
                    "typed_blocker_reason": "typed_closeout_packet_required",
                    "diagnostic": "missing_usage_telemetry",
                    "missing_user_stage_log_fields": ["progress_delta_classification"],
                    "observability_status": "missing",
                    "missing_observability_fields": ["duration", "token_usage", "cost"],
                    "duration": {},
                    "token_usage": {},
                    "cost": {},
                    "paper_stage_log": {
                        "stage_name": "unit_harmonized_external_validation_rerun",
                        "problem_summary": "Repair advanced the runtime-stage surface.",
                        "stage_goal": "Produce a stage-level repair delta or a stable blocker.",
                        "outcome": "executed",
                        "stage_work_done": ["Recorded stage-facing runtime repair changes."],
                        "paper_work_done": [],
                        "changed_stage_surfaces": [
                            "artifacts/supervision/current_control_state/latest.json",
                        ],
                        "changed_paper_surfaces": [],
                        "remaining_blockers": [],
                        "evidence_refs": [
                            "artifacts/supervision/current_control_state/latest.json",
                        ],
                    },
                },
            },
        }
    )

    assert monitoring["typed_blocker"] is None
    assert monitoring["progress_delta_classification"] == "platform_repair"
    terminal = monitoring["latest_terminal_stage"]
    assert terminal["progress_delta_classification"] == "platform_repair"
    completeness = terminal["terminal_closeout_semantic_completeness"]
    assert completeness["status"] == "complete"
    assert completeness["typed_blocker"] is None
    assert completeness["telemetry"] == "missing"
    assert completeness["missing_telemetry_fields"] == ["duration", "token_usage", "cost"]
    assert (
        completeness["progress_delta_classification_source"]
        == "inferred_from_changed_stage_surfaces"
    )


def test_progress_first_monitoring_marks_complete_terminal_closeout_semantics() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "001-risk",
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat-002",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "executed",
                    "observability_status": "observed",
                    "missing_observability_fields": [],
                    "duration": {"seconds": 0},
                    "token_usage": {"total_tokens": 0},
                    "cost": {"usd": 0},
                    "paper_stage_log": {
                        "stage_name": "run_quality_repair_batch",
                        "problem_summary": "Recorded a no-op owner receipt.",
                        "stage_goal": "Record a typed closeout packet for the owner action.",
                        "outcome": "executed",
                        "stage_work_done": ["Recorded a no-op owner receipt."],
                        "paper_work_done": ["Recorded a no-op owner receipt."],
                        "changed_stage_surfaces": [],
                        "changed_paper_surfaces": [],
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [],
                        "evidence_refs": ["artifacts/controller/quality_repair_batch/latest.json"],
                    },
                },
            },
        }
    )

    completeness = monitoring["latest_terminal_stage"]["terminal_closeout_semantic_completeness"]
    assert monitoring["latest_terminal_stage"]["semantic_completeness"] == {
        "status": "complete",
        "required_fields": [
            "stage_name",
            "problem_summary",
            "stage_goal",
            "stage_work_done",
            "changed_stage_surfaces",
            "outcome",
            "remaining_blockers",
            "evidence_refs",
        ],
        "missing_fields": [],
    }
    assert completeness["status"] == "complete"
    assert completeness["required_user_stage_log_fields"] == "complete"
    assert completeness["missing_user_stage_log_fields"] == []
    assert completeness["changed_surfaces"] == "present"
    assert completeness["changed_stage_surfaces"] == "present_empty"
    assert completeness["changed_paper_surfaces"] == "present_empty"
    assert completeness["progress_delta_classification"] == "typed_blocker"
    assert completeness["telemetry"] == "complete"
    assert completeness["missing_telemetry_fields"] == []
    assert completeness["typed_blocker"] is None
    assert completeness["next_forced_delta"] is None


def test_progress_first_monitoring_prefers_consumed_transition_owner_action_over_stale_execution_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "ai_reviewer",
                "typed_blocker": {
                    "blocker_type": "ai_reviewer_assessment_required",
                    "owner": "ai_reviewer",
                },
            },
            "current_blockers": ["ai_reviewer_assessment_required"],
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "publication_gate",
                    "summary": "MAS publication-gate/currentness replay after current AI reviewer archive.",
                },
                "typed_blocker": None,
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    "next_action": "honor_ai_reviewer_publication_eval_authority",
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["route_target"] == "write"
    assert monitoring["controller_action"] == "request_opl_stage_attempt"
    assert monitoring["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["dispatch_consumption"]["consumption_status"] == "consumed"


def test_progress_first_monitoring_prefers_current_handoff_action_over_stale_transition() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "typed_closeout_packet_required",
                    "owner": "one-person-lab",
                },
            },
            "current_blockers": ["typed_closeout_packet_required"],
            "next_forced_delta": {
                "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                "work_unit_id": "unit_harmonized_external_validation_rerun",
            },
            "opl_current_control_state_handoff": {
                "action_queue": [
                    {
                        "action_type": "unit_harmonized_external_validation_rerun",
                        "owner": "analysis_harmonization_owner",
                        "controller_work_unit_id": "unit_harmonized_external_validation_rerun",
                    }
                ],
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                    "lane": "publication_gate",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/old.json",
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "analysis_harmonization_owner"
    assert monitoring["controller_action"] == "unit_harmonized_external_validation_rerun"
    assert monitoring["next_work_unit"] == "unit_harmonized_external_validation_rerun"
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []


def test_existing_progress_projection_refreshes_stale_opl_handoff_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_adapter = importlib.import_module("med_autoscience.mcp_server_parts.projection_adapters")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量复评待推进。",
            "paper_stage_summary": "待 AI reviewer 复评。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T06:50:18+00:00",
                    "category": "controller_decision",
                    "source": "controller_decision",
                },
                {
                    "timestamp": "2026-05-30T06:50:08+00:00",
                    "category": "publication_eval",
                    "source": "publication_eval",
                },
            ],
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "summary": (
                        "Produce a current AI reviewer publication-eval record before dispatching "
                        "the publication-eval workflow."
                    ),
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "generated_at": "2026-05-30T03:44:25+00:00",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
            },
            "ai_repair_lifecycle": {
                "surface": "ai_repair_lifecycle",
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "last_apply_attempt_at": "2026-05-30T05:57:59+00:00",
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "operator_verdict": {
                "summary": stale_next_step,
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
            "refs": {
                "ai_repair_lifecycle_path": "/tmp/repair_lifecycle/latest.json",
                "opl_current_control_state_handoff_path": "/tmp/opl_current_control_state/latest.json",
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert "request_opl_handoff_hydration" not in result["next_system_action"]
    assert result["opl_current_control_state_handoff"] is None
    assert result["ai_repair_lifecycle"] is None
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"
    assert result["user_visible_projection"]["paper_progress_state"]["next_owner"] == "ai_reviewer"
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"].get("handoff_source") is None
    assert result["refs"]["ai_repair_lifecycle_path"] is None
    assert result["refs"]["opl_current_control_state_handoff_path"] is None
    mcp_result = mcp_adapter.render_study_progress_result(result)
    mcp_structured = mcp_result["structuredContent"]
    mcp_markdown = mcp_result["content"][0]["text"]
    assert mcp_structured.get("ai_repair_lifecycle") is None
    assert mcp_structured["next_owner"] == "ai_reviewer"
    assert mcp_structured["user_visible_projection"]["next_owner"] == "ai_reviewer"
    assert "request_opl_handoff_hydration" not in mcp_markdown
    assert "external_supervisor" not in mcp_markdown


def test_existing_projection_refreshes_stale_lane_after_handoff_surface_removed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量复评待推进。",
            "paper_stage_summary": "待 AI reviewer 复评。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T06:50:18+00:00",
                    "category": "controller_decision",
                    "source": "controller_decision",
                },
                {
                    "timestamp": "2026-05-30T06:50:08+00:00",
                    "category": "publication_eval",
                    "source": "publication_eval",
                },
                {
                    "timestamp": "2026-05-30T03:44:25+00:00",
                    "category": "opl_runtime_owner_handoff",
                    "source": "opl_runtime_owner_handoff",
                },
            ],
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
            "opl_current_control_state_handoff": None,
            "ai_repair_lifecycle": None,
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"].get("handoff_source") is None
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"


def test_current_owner_receipt_consumption_suppresses_fresh_opl_owner_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量复评待推进。",
            "paper_stage_summary": "待 AI reviewer 复评。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T07:09:29+00:00",
                    "category": "opl_runtime_owner_handoff",
                    "source": "opl_runtime_owner_handoff",
                },
            ],
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/latest.json",
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "generated_at": "2026-05-30T07:09:29+00:00",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
                "owner_route": {
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    "source_refs": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    },
                },
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert result["opl_current_control_state_handoff"] is None
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"


def test_stale_opl_handoff_refresh_uses_route_target_when_owner_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量修复待推进。",
            "paper_stage_summary": "待 write owner 完成当前性复核。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T10:15:14+00:00",
                    "category": "controller_decision",
                    "source": "controller_decision",
                },
            ],
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": "medical_prose_currentness_recheck",
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "generated_at": "2026-05-30T09:33:57+00:00",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "medical_prose_currentness_recheck" in result["next_system_action"]
    assert result["opl_current_control_state_handoff"] is None
    assert result["intervention_lane"]["route_target"] == "write"
    assert result["intervention_lane"].get("handoff_source") is None
    assert result["user_visible_projection"]["next_owner"] == "write"
    assert result["user_visible_projection"]["paper_progress_state"]["next_owner"] == "write"
