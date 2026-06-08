from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_platform_only_repair_projects_next_forced_paper_delta_without_counting_paper_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-29T00:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "escalated"},
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "next_owner": "runtime_mechanism_repair",
                    "owner_route": {
                        "next_owner": "runtime_mechanism_repair",
                        "route_target": "write",
                        "allowed_actions": ["paper_autonomy/repair-recheck"],
                        "target_surface": {
                            "ref_kind": "route_obligation",
                            "route_target": "write",
                            "surface_ref": "canonical_manuscript",
                        },
                        "acceptance_refs": [
                            "canonical_manuscript_delta",
                            "ai_reviewer_gate_replay_request",
                        ],
                        "source_refs": {
                            "work_unit_id": "publishability_repair_sprint",
                            "source_eval_id": "eval-current",
                        },
                        "source_fingerprint": "source-current",
                    },
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "execution_owner_guard": {"supervisor_only": True},
            "runtime_health_snapshot": {"attempt_state": "escalated"},
            "authority_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["deliverable_progress_delta"] == result["paper_progress_delta"]
    assert result["paper_progress_delta"]["count"] == 0
    assert result["platform_repair_delta"]["count"] == 1
    assert result["progress_delta_classification"] == "platform_repair"
    assert result["progress_first_sprint_state"]["deliverable_progress_delta"] == result["paper_progress_delta"]
    assert result["progress_first_sprint_state"]["classification"] == "platform_repair"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is False
    assert result["next_forced_delta"]["required_delta_kind"] == "paper_progress_delta_or_typed_blocker"
    assert result["next_forced_delta"]["work_unit_id"] == "publishability_repair_sprint"
    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "canonical_manuscript",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "owner_route.target_surface",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "runtime_mechanism_repair",
        "work_unit_id": "publishability_repair_sprint",
        "allowed_actions": ["paper_autonomy/repair-recheck"],
        "owner_receipt_required": True,
    }
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["authority"] == "refs_only_observability"
    assert monitoring["active_run_id"] == "run-001"
    assert monitoring["worker_liveness"]["health_status"] == "escalated"
    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "runtime_mechanism_repair"
    assert monitoring["next_work_unit"] == "publishability_repair_sprint"
    assert monitoring["typed_blocker"]["blocker_type"] == "runtime_recovery_retry_budget_exhausted"
    assert monitoring["progress_delta_classification"] == "platform_repair"
    assert monitoring["paper_progress_delta_counted"] is False
    assert monitoring["platform_repair_delta_counted"] is True
    assert monitoring["next_forced_delta"]["target_surface"]["surface_ref"] == "canonical_manuscript"
    assert monitoring["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert monitoring["next_forced_delta"]["target_surface_diagnostic"]["source"] == "owner_route.target_surface"
    assert monitoring["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert monitoring["next_forced_delta"]["owner_action"]["next_owner"] == "runtime_mechanism_repair"
    assert monitoring["foreground_write_policy"] == {
        "supervisor_only": True,
        "foreground_can_write_runtime_owned_surfaces": False,
        "rule": "supervisor_only_no_runtime_owned_writes",
    }
    assert monitoring["authority_boundary"]["can_write_paper_or_package"] is False
    assert monitoring["authority_boundary"]["can_authorize_quality_verdict"] is False
    compact = mcp_projection.compact_study_progress_projection(result)
    markdown = mcp_projection.render_mcp_study_progress_markdown(result)
    assert compact["next_forced_delta"]["target_surface"]["surface_ref"] == "canonical_manuscript"
    assert compact["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert compact["next_forced_delta"]["owner_action"]["work_unit_id"] == "publishability_repair_sprint"
    assert compact["progress_first_monitoring_summary"]["active_run_id"] == "run-001"
    assert compact["progress_first_monitoring_summary"]["next_work_unit"] == "publishability_repair_sprint"
    assert compact["progress_first_monitoring_summary"]["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert "## Progress-First Monitoring" in markdown
    assert "platform_delta_counted: `True`" in markdown


def test_next_forced_delta_marks_next_forced_target_surface_as_precise() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 1},
            "current_execution_envelope": {
                "owner_route": {
                    "next_owner": "paper_author",
                    "route_target": "write",
                    "next_forced_target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "write",
                        "surface_ref": "canonical_manuscript#discussion",
                    },
                    "source_refs": {"work_unit_id": "publishability_repair_sprint"},
                }
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "canonical_manuscript#discussion",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "owner_route.next_forced_target_surface",
        "missing_explicit_target_surface": False,
    }


def test_next_forced_delta_uses_domain_transition_required_owner_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 0},
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "lane": "review",
                },
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "eval_id": "eval-current",
                    "action_fingerprint": "domain-transition::ai_reviewer_re_eval",
                },
            },
        }
    )

    assert result["next_forced_delta"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "review",
        "surface_ref": "artifacts/publication_eval/latest.json",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "domain_transition.guard_boundary.required_owner_surface",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "ai_reviewer",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "owner_receipt_required": True,
    }


def test_next_forced_delta_prefers_domain_transition_when_handoff_route_lacks_target_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 0},
            "opl_current_control_state_handoff": {
                "owner_route": {
                    "next_owner": "ai_reviewer",
                    "route_target": "review",
                    "source_refs": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                    },
                },
            },
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "lane": "review",
                },
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "review",
        "surface_ref": "artifacts/publication_eval/latest.json",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False


def test_next_forced_delta_prefers_current_handoff_action_queue_over_stale_transition() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 0},
            "opl_current_control_state_handoff": {
                "owner_route": {
                    "next_owner": "analysis_harmonization_owner",
                    "owner_reason": "unit_harmonized_rerun_required",
                    "allowed_actions": ["unit_harmonized_external_validation_rerun"],
                    "source_refs": {"work_unit_id": "unit_harmonized_external_validation_rerun"},
                },
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
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "eval_id": "eval-stale",
                    "action_fingerprint": "domain-transition::stale-write-replay",
                },
            },
        }
    )

    assert result["progress_first_sprint_state"]["next_owner"] == "analysis_harmonization_owner"
    assert result["next_forced_delta"]["work_unit_id"] == "unit_harmonized_external_validation_rerun"
    assert result["next_forced_delta"]["target_surface"] == {
        "surface": "analysis_harmonization_owner_target_surface",
        "schema_version": 1,
        "body_free": True,
        "owner": "analysis_harmonization_owner",
        "work_unit": "unit_harmonized_external_validation_rerun",
        "accepted_outputs": [
            "unit_harmonized_external_validation_rerun_evidence",
            "feature_order_and_coefficient_provenance",
            "calibration_or_recalibration_evidence",
            "claim_evidence_map_update_ref",
            "stable_typed_blocker:unit_harmonized_rerun_required",
        ],
        "output_refs": {
            "owner_result": "artifacts/controller/analysis_harmonization/latest.json",
            "rerun_evidence": (
                "artifacts/controller/analysis_harmonization/"
                "unit_harmonized_external_validation_rerun.json"
            ),
            "claim_evidence_map": "paper/claim_evidence_map.json",
            "request_packet": "artifacts/supervision/requests/analysis_harmonization/latest.json",
        },
        "publication_ready_authorized": False,
        "current_package_write_allowed": False,
        "paper_body_write_allowed": False,
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "default_executor_action_policy.request_output_surface_for_action_type",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "analysis_harmonization_owner",
        "work_unit_id": "unit_harmonized_external_validation_rerun",
        "allowed_actions": ["unit_harmonized_external_validation_rerun"],
        "owner_receipt_required": True,
    }


def test_next_forced_delta_does_not_redrive_readiness_queue_after_paper_delta_with_current_transition() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 1},
            "platform_repair_delta": {"count": 0},
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "owner_route": {
                    "next_owner": "MedAutoScience",
                    "allowed_actions": ["complete_medical_paper_readiness_surface"],
                    "source_refs": {
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "source_fingerprint": (
                            "stage-current-owner-delta::complete_medical_paper_readiness_surface"
                        ),
                    },
                },
                "action_queue": [
                    {
                        "action_type": "complete_medical_paper_readiness_surface",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "fingerprint": "complete_medical_paper_readiness_surface::medical_paper_readiness_missing",
                        "consumption": {"state": "unconsumed"},
                    }
                ],
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "finalize",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "publication_gate",
                },
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
            },
        }
    )

    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"
    assert result["next_forced_delta"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
    }
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "finalize",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
    }


def test_next_forced_delta_drops_readiness_queue_after_paper_delta_without_current_route() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 1},
            "platform_repair_delta": {"count": 0},
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "owner_route": {
                    "next_owner": "MedAutoScience",
                    "allowed_actions": ["complete_medical_paper_readiness_surface"],
                    "source_refs": {
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                    },
                },
                "action_queue": [
                    {
                        "action_type": "complete_medical_paper_readiness_surface",
                        "owner": "MedAutoScience",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "fingerprint": "complete_medical_paper_readiness_surface::medical_paper_readiness_missing",
                    }
                ],
            },
        }
    )

    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"
    assert result["next_forced_delta"]["reason"] == "paper_progress_delta_observed"
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": None,
        "work_unit_id": None,
        "allowed_actions": [],
        "owner_receipt_required": True,
    }
    assert result["current_owner_ticket"]["allowed_action"] is None
    assert result["current_owner_ticket"]["work_unit"] == {}


def test_next_forced_delta_maps_publication_gate_replay_family_to_gate_clearing_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 0},
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "finalize",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "publication_gate",
                },
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "default_executor_action_policy.request_output_surface_for_action_type",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "finalize",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
    }


def test_next_forced_delta_maps_current_ai_reviewer_consumption_write_route_to_quality_repair_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 1},
            "platform_repair_delta": {"count": 0},
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                    "lane": "review",
                },
                "guard_boundary": {
                    "required_owner_surface": "artifacts/publication_eval/latest.json",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "eval_id": "publication-eval::002::current-inputs",
                    "action_fingerprint": "domain-transition::route_back_same_line::consume-current-record",
                },
            },
        }
    )

    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"
    assert result["next_forced_delta"]["work_unit_id"] == (
        "consume_current_ai_reviewer_record_then_prose_gate_package_replay"
    )
    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "default_executor_action_policy.request_output_surface_for_action_type",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "write",
        "work_unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
    }


def test_next_forced_delta_maps_current_handoff_owner_route_action_to_quality_repair_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 1},
            "platform_repair_delta": {"count": 0},
            "opl_current_control_state_handoff": {
                "owner_route": {
                    "next_owner": "write",
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    "source_fingerprint": "truth-snapshot::current",
                    "source_refs": {
                        "work_unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                        "source_eval_id": "publication-eval::current-inputs",
                    },
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
        }
    )

    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"
    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is False
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "precise",
        "source": "default_executor_action_policy.request_output_surface_for_action_type",
        "missing_explicit_target_surface": False,
    }
    assert result["next_forced_delta"]["owner_action"] == {
        "next_owner": "write",
        "work_unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
    }


def test_next_forced_delta_reads_current_execution_evidence_owner_route() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 1},
            "platform_repair_delta": {"count": 0},
            "current_execution_evidence": {
                "opl_current_control_state_handoff": {
                    "owner_route": {
                        "next_owner": "write",
                        "source_refs": {
                            "work_unit_id": "consume_current_ai_reviewer_record_then_prose_gate_package_replay",
                            "source_eval_id": "publication-eval::current-inputs",
                        },
                        "allowed_actions": ["run_quality_repair_batch"],
                    },
                },
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": (
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "explicit_owner_route_target"
    assert result["next_forced_delta"]["owner_action"]["allowed_actions"] == ["run_quality_repair_batch"]


def test_next_forced_delta_reports_generic_target_surface_fallback_when_owner_route_lacks_precise_surface() -> None:
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )

    result = projection.build_progress_first_projection(
        {
            "deliverable_progress_delta": {"count": 0},
            "platform_repair_delta": {"count": 1},
            "current_execution_envelope": {
                "owner_route": {
                    "next_owner": "paper_author",
                    "route_target": "write",
                    "source_refs": {"work_unit_id": "publishability_repair_sprint"},
                }
            },
        }
    )

    assert result["next_forced_delta"]["target_surface"] == {
        "ref_kind": "route_obligation",
        "route_target": "write",
        "surface_ref": "study_progress.next_forced_delta",
    }
    assert result["next_forced_delta"]["target_surface_specificity"] == "generic_route_obligation_fallback"
    assert result["next_forced_delta"]["missing_explicit_target_surface"] is True
    assert result["next_forced_delta"]["target_surface_fallback_reason"] == (
        "owner_route_missing_explicit_target_surface"
    )
    assert result["next_forced_delta"]["target_surface_diagnostic"] == {
        "specificity": "generic_fallback",
        "source": "study_progress.next_forced_delta",
        "missing_explicit_target_surface": True,
        "fallback_reason": "owner_route_missing_explicit_target_surface",
    }


def test_terminal_stage_paper_delta_counts_in_top_level_progress_first_projection() -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )
    handoff = {
        "latest_terminal_stage_log": {
            "stage_attempt_id": "sat-003",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "executed",
            "missing_user_stage_log_fields": ["progress_delta_classification"],
            "missing_observability_fields": ["duration", "token_usage", "cost"],
            "paper_stage_log": {
                "stage_work_done": ["Recorded paper-facing artifact changes."],
                "paper_work_done": ["Recorded paper-facing artifact changes."],
                "changed_stage_surfaces": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                ],
                "changed_paper_surfaces": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                ],
                "semantic_delta_refs": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md#semantic-delta",
                ],
                "remaining_blockers": [],
            },
        },
    }

    progress_delta = assembly._progress_delta_metrics(
        quality_repair_batch_followthrough={},
        gate_clearing_batch_followthrough={},
        opl_current_control_state_handoff=handoff,
        runtime_efficiency={"token_usage": {"total_tokens": 1200}},
    )
    result = projection.build_progress_first_projection(
        {
            **progress_delta,
            "opl_current_control_state_handoff": handoff,
        }
    )

    assert progress_delta["deliverable_progress_delta"] == {
        "count": 1,
        "token_usage_total": 1200,
        "sources": ["opl_current_control_state.latest_terminal_stage_log.paper_stage_log"],
    }
    assert progress_delta["paper_progress_delta"] == progress_delta["deliverable_progress_delta"]
    assert progress_delta["platform_repair_delta"]["count"] == 0
    assert progress_delta["progress_delta_classification"] == "deliverable_progress"
    assert result["progress_first_sprint_state"]["classification"] == "deliverable_progress"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is True
    assert result["next_forced_delta"]["required_delta_kind"] == "review_current_paper_delta"


def test_terminal_stage_log_without_backing_refs_is_observability_not_paper_delta() -> None:
    assembly = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_projection"
    )
    handoff = {
        "latest_terminal_stage_log": {
            "stage_attempt_id": "sat-003",
            "stage_id": "domain_owner/default-executor-dispatch",
            "action_type": "run_quality_repair_batch",
            "status": "executed",
            "missing_user_stage_log_fields": ["progress_delta_classification"],
            "paper_stage_log": {
                "stage_work_done": ["Observed paper-facing artifact paths."],
                "paper_work_done": ["Observed paper-facing artifact paths."],
                "changed_paper_surfaces": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/claim_evidence_map.json",
                ],
                "remaining_blockers": [],
            },
        },
    }

    progress_delta = assembly._progress_delta_metrics(
        quality_repair_batch_followthrough={},
        gate_clearing_batch_followthrough={},
        opl_current_control_state_handoff=handoff,
        runtime_efficiency={"token_usage": {"total_tokens": 1200}},
    )
    result = projection.build_progress_first_projection(
        {
            **progress_delta,
            "opl_current_control_state_handoff": handoff,
        }
    )

    assert progress_delta["deliverable_progress_delta"] == {
        "count": 0,
        "token_usage_total": 0,
        "sources": [],
    }
    assert progress_delta["paper_progress_delta"] == progress_delta["deliverable_progress_delta"]
    assert progress_delta["progress_delta_classification"] == "typed_blocker"
    assert result["progress_first_sprint_state"]["classification"] == "typed_blocker"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is False
