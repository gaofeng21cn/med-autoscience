from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_redrive_projection_keeps_mas_domain_transition_over_opl_handoff_queue() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {
                "decision_owner": "ai_reviewer",
                "route_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "conditions": [
                {
                    "type": "DomainTransitionRedrive",
                    "status": "true",
                    "summary": "current domain transition names an owner work unit",
                }
            ],
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "next_owner": "write",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "action_queue": [
                {
                    "action_type": "run_quality_repair_batch",
                    "status": "queued",
                    "owner": "write",
                    "summary": "The current AI reviewer-backed write route requires manuscript story-surface repair.",
                }
            ],
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_target_label": "独立审阅与质控",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "operator_verdict": {
            "surface_kind": "study_operator_verdict",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "reason_summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "recovery_contract": {
            "contract_kind": "study_recovery_contract",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "autonomy_contract": {
            "contract_kind": "study_autonomy_contract",
            "next_signal": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "ai_reviewer owner" in result["next_system_action"]
    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert "write owner" not in result["next_system_action"]
    assert "run_quality_repair_batch" not in result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"
    assert result["user_visible_projection"]["next_step"] == result["next_system_action"]
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"]["route_key_question"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert result["operator_verdict"]["summary"] != result["next_system_action"]
    assert result["operator_verdict"]["route_target"] == "review"
    assert result["recovery_contract"]["summary"] != result["next_system_action"]
    assert result["recovery_contract"]["route_target"] == "review"
    assert result["autonomy_contract"]["next_signal"] != result["next_system_action"]


def test_redrive_projection_uses_structured_typed_blocker_route_back_owner() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "write",
            "owner": "write",
            "next_work_unit": {
                "unit_id": "medical_prose_currentness_recheck",
                "summary": "Repair stale medical prose against the current manuscript.",
                "required_output_surface": "paper/build/review_manuscript.md",
            },
            "evidence_refs": {
                "publication_eval": "artifacts/publication_eval/latest.json",
                "reviewer_record": "artifacts/publication_eval/ai_reviewer_responses/current_record.json",
            },
            "expected_repair_result": (
                "current manuscript story-surface delta plus AI reviewer recheck request, "
                "or a stable typed blocker"
            ),
        },
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {
                "route_owner": "write",
                "route_target": "write",
                "next_work_unit": "medical_prose_currentness_recheck",
            },
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "generated_at": "2026-05-30T10:00:00+00:00",
            "latest_terminal_stage_log": {
                "status": "handoff_ready",
                "action_type": "run_quality_repair_batch",
                "paper_stage_log": {
                    "current_owner": "write",
                    "progress_delta_classification": "platform_repair",
                    "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
                    "paper_progress_delta": {"count": 0, "token_usage_total": 0},
                    "platform_repair_delta": {"count": 1, "token_usage_total": 2400},
                    "changed_paper_surfaces": [],
                    "changed_stage_surfaces": ["runtime/typed_closeout.json"],
                    "evidence_refs": ["artifacts/controller/quality_repair_batch/latest.json"],
                    "remaining_blockers": {
                        "reason": "manuscript_story_surface_delta_missing",
                        "typed_blocker": "manuscript_story_surface_delta_missing",
                    },
                },
            },
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_key_question": "stale_review_route",
            "summary": "旧审阅 route。",
        },
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "write owner" in result["next_system_action"]
    assert "medical_prose_currentness_recheck" in result["next_system_action"]
    assert "run_quality_repair_batch" not in result["next_system_action"]
    assert "manuscript_story_surface_delta_missing" not in result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "write"
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"]["route_key_question"] == "stale_review_route"
    checklist = result["route_back_checklist"]
    assert checklist["blockers"] == ["manuscript_story_surface_delta_missing"]
    assert checklist["route_target"] == "write"
    assert checklist["owner"] == "write"
    assert checklist["next_work_units"] == [
        {
            "unit_id": "medical_prose_currentness_recheck",
            "summary": "Repair stale medical prose against the current manuscript.",
            "required_output_surface": "paper/build/review_manuscript.md",
        }
    ]
    assert checklist["evidence_refs"] == [
        "artifacts/controller/quality_repair_batch/latest.json",
        "artifacts/publication_eval/latest.json",
        "artifacts/publication_eval/ai_reviewer_responses/current_record.json",
    ]
    assert checklist["expected_repair_result"].startswith("current manuscript story-surface delta")
    assert checklist["progress_delta_classification"] == "platform_repair"
    assert checklist["deliverable_progress_delta"] == {"count": 0, "token_usage_total": 0}
    assert checklist["platform_repair_delta"] == {"count": 1, "token_usage_total": 2400}
    assert checklist["changed_paper_surfaces"] == []
    assert checklist["changed_stage_surfaces"] == ["runtime/typed_closeout.json"]
    assert result["user_visible_projection"]["route_back_checklist"] == checklist
    assert "route_back_checklist" not in result["intervention_lane"]


def test_user_visible_projection_uses_current_domain_transition_owner_when_handoff_shell_is_stale() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "latest_events": [
            {
                "timestamp": "2026-05-30T10:20:17+00:00",
                "category": "controller_decision",
                "source": "controller_decision",
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
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {
                "route_owner": "ai_reviewer",
                "route_target": "review",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "generated_at": "2026-05-30T09:33:57+00:00",
            "next_owner": None,
            "blocked_reason": None,
            "latest_terminal_stage_log": {
                "generated_at": "2026-05-30T10:26:13+00:00",
                "status": "handoff_ready",
                "action_type": "return_to_ai_reviewer_workflow",
                "paper_stage_log": {
                    "current_owner": "ai_reviewer",
                    "remaining_blockers": [],
                },
            },
        },
    }

    projection = module.build_user_visible_projection(payload)

    assert projection["next_owner"] == "ai_reviewer"
    assert projection["paper_progress_state"]["next_owner"] == "ai_reviewer"


def test_progress_first_monitoring_does_not_redrive_same_consumed_ai_reviewer_record() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.progress_first_monitoring")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "lane": "review",
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": "publication-eval::003-dpcc::current",
                "next_action": "honor_ai_reviewer_publication_eval_authority",
            },
        },
    }

    projection = module.build_progress_first_monitoring_summary(payload)

    assert projection["execution_state_kind"] == "receipt_consumed"
    assert projection["next_owner"] == "ai_reviewer"
    assert projection["controller_action"] == "return_to_ai_reviewer_workflow"
    assert projection["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert projection["dispatch_consumption"]["consumption_status"] == "consumed"


def test_progress_first_monitoring_uses_canonical_next_action_over_legacy_current_work_unit() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.progress_first_monitoring")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "next_action": {
            "surface_kind": "mas_next_action_envelope",
            "action_id": "next-action::003::runtime-route",
            "action_family": "runtime.opl_route",
            "action_kind": "submit_to_opl_runtime",
            "action_type": "request_opl_stage_attempt",
            "owner": "one-person-lab",
            "executor_target": "opl_domain_progress_transition_runtime",
            "work_unit_id": "canonical-runtime-route",
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": "legacy-writer",
            "action_type": "legacy_writer_repair",
            "work_unit_id": "legacy-writer-work-unit",
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "legacy-writer",
            "action_type": "legacy_writer_repair",
            "work_unit_id": "legacy-writer-work-unit",
        },
    }

    projection = module.build_progress_first_monitoring_summary(payload)

    assert projection["next_owner"] == "one-person-lab"
    assert projection["controller_action"] == "request_opl_stage_attempt"
    assert projection["next_work_unit"] == "canonical-runtime-route"
    assert projection["current_work_unit"]["owner"] == "legacy-writer"


def test_progress_first_monitoring_redrives_consumed_ai_reviewer_record_with_different_identity() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.progress_first_monitoring")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "lane": "review",
            },
            "work_unit_fingerprint": "domain-transition::review::current-manuscript-v2",
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": "publication-eval::003-dpcc::previous",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "domain-transition::review::previous-inputs",
                "owner_route_currentness_basis": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "domain-transition::review::previous-inputs",
                    "source_eval_id": "publication-eval::003-dpcc::previous",
                },
                "next_action": "honor_ai_reviewer_publication_eval_authority",
            },
        },
    }

    projection = module.build_progress_first_monitoring_summary(payload)

    assert projection["execution_state_kind"] == "executable_owner_action"
    assert projection["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert projection["typed_blocker"] is None
    assert projection["dispatch_consumption"]["consumption_status"] == "consumed"


def test_progress_first_monitoring_does_not_redrive_executed_gate_clearing_batch() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.progress_first_monitoring")
    source_eval_id = "publication-eval::003-dpcc::ai-reviewer-record::current"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "route_target": "finalize",
            "owner": "gate_clearing_batch",
            "controller_action": "run_gate_clearing_batch",
            "next_work_unit": {
                "unit_id": work_unit_id,
                "lane": "review",
            },
            "source_refs": {
                "owner_route_currentness_basis": {
                    "source_eval_id": source_eval_id,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
                }
            },
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "source_eval_id": source_eval_id,
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": "truth-snapshot::reviewer-record",
            },
        },
        "gate_clearing_batch_followthrough": {
            "surface_kind": "gate_clearing_batch_followthrough",
            "status": "executed",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": "truth-snapshot::gate-replay-current",
            "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    }

    projection = module.build_progress_first_monitoring_summary(payload)

    assert projection["execution_state_kind"] == "receipt_consumed"
    assert projection["dispatch_consumption"]["receipt_kind"] == "gate_clearing_batch"
    assert projection["dispatch_consumption"]["receipt_ref"] == "artifacts/controller/gate_clearing_batch/latest.json"
    assert projection["dispatch_consumption"]["work_unit_id"] == work_unit_id


def test_progress_first_monitoring_does_not_redrive_same_scalar_consumed_ai_reviewer_record() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.progress_first_monitoring")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": "publication-eval::003-dpcc::current",
                "next_action": "honor_ai_reviewer_publication_eval_authority",
            },
        },
    }

    projection = module.build_progress_first_monitoring_summary(payload)

    assert projection["execution_state_kind"] == "receipt_consumed"
    assert projection["next_owner"] == "ai_reviewer"
    assert projection["controller_action"] == "return_to_ai_reviewer_workflow"
    assert projection["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    assert projection["dispatch_consumption"]["consumption_status"] == "consumed"


def test_progress_first_monitoring_keeps_consumed_ai_reviewer_closeout_blocker_blocked() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.progress_first_monitoring")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_id": "typed_closeout_packet_required",
                "blocker_type": "provider_completed_without_typed_closeout",
                "owner": "one-person-lab",
            },
            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
        },
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "completion_receipt_consumption": {
                "status": "consumed",
                "receipt_kind": "ai_reviewer_publication_eval",
                "receipt_ref": "artifacts/publication_eval/latest.json",
                "eval_id": "publication-eval::003-dpcc::current",
                "next_action": "honor_ai_reviewer_publication_eval_authority",
            },
        },
    }

    projection = module.build_progress_first_monitoring_summary(payload)

    assert projection["execution_state_kind"] == "typed_blocker"
    assert projection["next_owner"] == "ai_reviewer"
    assert projection["controller_action"] == "return_to_ai_reviewer_workflow"
    assert projection["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    assert projection["current_blockers"] == [
        "typed_closeout_packet_required",
        "provider_completed_without_typed_closeout",
    ]
    assert projection["dispatch_consumption"]["consumption_status"] == "consumed"


def test_redrive_projection_keeps_mas_transition_over_explicit_opl_handoff_owner() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "conditions": [
                {
                    "type": "DomainTransitionRedrive",
                    "status": "true",
                    "summary": "current domain transition names an owner work unit",
                }
            ],
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "quest_status": "waiting_for_user",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "blocked_reason": "opl_stage_attempt_admission_required",
            "why_not_applied": ["opl_stage_attempt_admission_required"],
            "action_queue": [],
            "latest_terminal_stage_log": {
                "surface_kind": "mas_latest_terminal_stage_log_projection",
                "action_type": "return_to_ai_reviewer_workflow",
                "status": "handoff_ready",
                "paper_stage_log": {
                    "current_owner": "ai_reviewer",
                    "problem_summary": "Stale terminal log should not override explicit OPL handoff owner.",
                },
            },
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "operator_verdict": {
            "surface_kind": "study_operator_verdict",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "reason_summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "recovery_contract": {
            "contract_kind": "study_recovery_contract",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "autonomy_contract": {
            "contract_kind": "study_autonomy_contract",
            "next_signal": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "ai_reviewer owner" in result["next_system_action"]
    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert "external_supervisor owner" not in result["next_system_action"]
    assert "request_opl_handoff_hydration" not in result["next_system_action"]
    assert "return_to_ai_reviewer_workflow" not in result["next_system_action"]
    assert result["user_visible_projection"].get("next_owner") != "external_supervisor"
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"]["route_key_question"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert result["operator_verdict"]["route_target"] == "review"
    assert result["recovery_contract"]["route_target"] == "review"
    assert result["autonomy_contract"]["next_signal"] != result["next_system_action"]


def test_redrive_projection_ignores_handoff_older_than_current_controller_truth() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "latest_events": [
            {
                "timestamp": "2026-05-30T06:50:18+00:00",
                "category": "controller_decision",
                "source": "controller_decision",
                "summary": "控制面正式决定：route back same line。",
            },
            {
                "timestamp": "2026-05-30T06:50:08+00:00",
                "category": "publication_eval",
                "source": "publication_eval",
                "summary": "最新 task intake 已明确要求回到待修订状态。",
            },
            {
                "timestamp": "2026-05-30T03:44:25+00:00",
                "category": "opl_runtime_owner_handoff",
                "source": "opl_runtime_owner_handoff",
                "summary": "OPL runtime owner handoff was recorded as a refs-only boundary artifact.",
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
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "conditions": [
                {
                    "type": "DomainTransitionRedrive",
                    "status": "true",
                    "summary": "current domain transition names an owner work unit",
                }
            ],
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "generated_at": "2026-05-30T06:28:48+00:00",
            "quest_status": "waiting_for_user",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "blocked_reason": "opl_stage_attempt_admission_required",
            "why_not_applied": ["opl_stage_attempt_admission_required"],
            "action_queue": [],
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "operator_verdict": {
            "surface_kind": "study_operator_verdict",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "reason_summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert "request_opl_handoff_hydration" not in result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] != "external_supervisor"
    assert result["intervention_lane"]["route_target"] == "review"
