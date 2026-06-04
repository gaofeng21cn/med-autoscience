from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_exposes_current_executable_owner_action_from_next_forced_delta() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "finalize",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "target_surface_specificity": "explicit_owner_route_target",
                "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert action == {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "study_progress.next_forced_delta.owner_action",
        "next_owner": "finalize",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "review_current_paper_delta",
        "target_surface": {
            "ref_kind": "route_obligation",
            "route_target": "finalize",
            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
        },
        "target_surface_specificity": "explicit_owner_route_target",
        "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"


def test_progress_first_monitoring_requests_admission_for_current_executable_owner_action_without_hard_gate() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_system_action": "观察自动运行推进。",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
                "owner_receipt_required": True,
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["surface_kind"] == "current_executable_owner_action_admission"
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_start_requested"] is True
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_blocked"] is False
    assert admission["hard_gate_reasons"] == []
    assert admission["next_owner"] == "finalize"
    assert admission["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert admission["allowed_actions"] == ["run_gate_clearing_batch"]
    assert admission["source"] == "progress_first_monitoring.current_executable_owner_action"


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
                    "refs": ["artifacts/supervision/opl_current_control_state/latest.json#read_model_hygiene"],
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


def test_progress_first_monitoring_blocks_owner_action_admission_on_hard_gate_forbidden_write_and_missing_callable() -> None:
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
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "interaction_arbitration": {
                "classification": "human_gate",
                "requires_user_input": True,
                "blocked_reason": "needs_physician_decision",
            },
            "execution_owner_guard": {
                "supervisor_only": True,
                "forbidden_write_refs": ["runtime/current_execution_envelope.json"],
            },
            "owner_callable_surface": {
                "status": "missing",
                "reason_code": "owner_callable_surface_missing",
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_blocked"] is True
    assert admission["hard_gate_reasons"] == [
        "human_gate_required",
        "forbidden_write_refs",
        "owner_callable_surface_missing",
    ]
    assert admission["blocked_by"] == {
        "human_gate": {
            "requires_user_input": True,
            "blocked_reason": "needs_physician_decision",
        },
        "forbidden_write_refs": ["runtime/current_execution_envelope.json"],
        "owner_callable_surface": {
            "status": "missing",
            "reason_code": "owner_callable_surface_missing",
        },
    }


def test_progress_first_monitoring_blocks_owner_action_admission_on_existing_owner_callable_missing_surfaces() -> None:
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
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_redrive",
                "action": "resume",
                "requires_user_input": False,
                "blocked_reason": "owner_callable_surface_missing",
            },
            "current_execution_envelope": {
                "typed_blocker": {
                    "blocker_id": "owner_callable_surface_missing",
                    "owner": "ai_reviewer",
                },
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_reasons"] == ["owner_callable_surface_missing"]
    assert admission["blocked_by"]["owner_callable_surface"] == {
        "status": "missing",
        "reason_code": "owner_callable_surface_missing",
        "sources": [
            "interaction_arbitration.blocked_reason",
            "current_execution_envelope.typed_blocker",
        ],
    }


def test_progress_first_monitoring_distinguishes_admission_request_from_running_provider_proof() -> None:
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
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "allowed_actions": ["run_quality_repair_batch"],
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-running",
                "active_workflow_id": "wf-running",
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is True
    assert admission["provider_attempt_started"] is True
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_proof"] == {
        "running_provider_attempt": True,
        "active_stage_attempt_id": "sat-running",
        "active_run_id": None,
        "active_workflow_id": "wf-running",
    }


def test_progress_first_monitoring_keeps_stale_active_run_id_out_of_running_fields() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-stale",
            "supervision": {"active_run_id": "opl-stage-attempt://sat-stale"},
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "opl_current_control_state_handoff": {
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "active_workflow_id": None,
                "running_provider_attempt": False,
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-stale"
    assert monitoring["owner_action_admission"]["admission_pending"] is True
    assert monitoring["owner_action_admission"]["provider_attempt_started"] is False


def test_progress_first_monitoring_shows_handoff_active_run_ref_without_running_provider_proof() -> None:
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
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "opl_current_control_state_handoff": {
                "active_run_id": "opl-stage-attempt://sat-handoff-ref",
                "active_stage_attempt_id": "sat-not-running",
                "active_workflow_id": "wf-not-running",
                "running_provider_attempt": False,
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] == "opl-stage-attempt://sat-handoff-ref"
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["owner_action_admission"]["provider_attempt_running_proven"] is False
    assert monitoring["owner_action_admission"]["provider_attempt_started"] is False


def test_user_visible_projection_prefers_current_executable_owner_action_over_stale_paper_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {
                    "route_owner": "ai_reviewer",
                    "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
                "conditions": [],
            },
            "paper_progress_state": {"next_owner": "ai_reviewer"},
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    )

    assert projection["next_owner"] == "finalize"
    assert projection["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert projection["current_executable_owner_action"]["next_owner"] == "finalize"


def test_user_visible_projection_does_not_mark_stale_live_macro_state_as_running_when_owner_action_is_pending() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "opl-stage-attempt://sat-stale"},
                "conditions": [],
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {"status": "stale"},
                "activity_timeout": {"state": "timed_out"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "artifact_delta": {"status": "stale"},
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    )

    assert projection["writer_state"] == "live"
    assert projection["actual_write_active"] is False
    assert projection["owner_resolution_state"] == "ready_for_owner_action"
    assert projection["next_owner"] == "gate_clearing_batch"
    assert projection["next_system_action"] == (
        "等待 gate_clearing_batch owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )


def test_current_owner_handoff_projection_prefers_current_executable_owner_action_next_step() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "next_system_action": "等待显式 resume、rerun 或 relaunch。",
        "status_narration_contract": {"next_step": "等待显式 resume、rerun 或 relaunch。"},
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        "user_visible_projection": {
            "surface_kind": "study_progress_user_visible_projection",
            "schema_version": 2,
            "next_owner": "ai_reviewer",
            "next_step": "等待旧 reviewer route。",
            "next_system_action": "等待旧 reviewer route。",
        },
    }

    result = module.apply_current_owner_handoff_user_visible_status(payload)

    assert result["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert result["user_visible_projection"]["next_system_action"] == result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "finalize"
    assert result["status_narration_contract"]["next_step"] == result["next_system_action"]


def test_current_owner_handoff_decision_uses_current_executable_owner_action_next_step() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {"decision_type": "current_owner_handoff"},
        "next_system_action": "等待显式 resume、rerun 或 relaunch。",
        "status_narration_contract": {"next_step": "等待显式 resume、rerun 或 relaunch。"},
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        "user_visible_projection": {
            "surface_kind": "study_progress_user_visible_projection",
            "schema_version": 2,
            "next_owner": "ai_reviewer",
            "next_step": "等待旧 reviewer route。",
            "next_system_action": "等待旧 reviewer route。",
        },
    }

    result = module.apply_current_owner_handoff_user_visible_status(payload)

    assert result["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert result["user_visible_projection"]["next_system_action"] == result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "finalize"
    assert result["status_narration_contract"]["next_step"] == result["next_system_action"]


def test_progress_first_monitoring_derives_owner_action_from_stage_artifact_index_before_stale_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": "review_and_quality_gate",
                "next_owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "required_delta_kind": "quality_gate_replay_after_artifact_delta",
                    "target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "finalize",
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                    "target_surface_specificity": "explicit_owner_route_target",
                    "acceptance_refs": [
                        "studies/003-dm/paper/review/story_surface_delta_20260603.json"
                    ],
                },
                "stale_platform_repairs": [
                    {
                        "surface": "current_execution_envelope.typed_blocker",
                        "reason_code": "progress_first_owner_redrive_budget_exhausted",
                    }
                ],
                "stages": [
                    {
                        "stage_id": "review_and_quality_gate",
                        "artifact_delta": {"status": "fresh"},
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "progress_first_owner_redrive_budget_exhausted",
                    "owner": "platform_repair",
                    "work_unit_id": "stale_read_model_reconcile",
                },
            },
            "domain_transition": {
                "typed_blocker": {
                    "blocker_id": "progress_first_owner_redrive_budget_exhausted",
                    "owner": "platform_repair",
                }
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == {
        "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    }
    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "stage_artifact_index.next_owner_action"
    assert action["artifact_first_precedence"]["stale_platform_repairs_superseded"] is True
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["owner_action_admission"]["admission_requested"] is True


def test_progress_first_monitoring_consumes_lane1_stage_artifact_index_action_shape() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "001-risk",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "idea",
                    "artifact_status": "missing",
                    "next_missing_surface": "artifacts/stage_outputs/idea/line_selection_note.md",
                },
                "next_owner_action": {
                    "owner": "idea",
                    "action_type": "materialize_stage_artifact_delta",
                    "required_output_surface": "artifacts/stage_outputs/idea/line_selection_note.md",
                    "artifact_native_contract_ref": "mas-opl-stage-native-artifact-contract.v1",
                    "manifest_ref": "artifacts/stage_outputs/idea/stage_artifact_manifest.json",
                    "receipt_ref": "artifacts/stage_outputs/idea/owner_receipt.json",
                    "authority_boundary": {
                        "artifact_first_can_determine_stage_progress": True,
                        "can_write_mas_truth": False,
                        "can_authorize_quality_verdict": False,
                        "can_authorize_publication_readiness": False,
                        "can_authorize_submission_readiness": False,
                        "provider_completion_is_paper_progress": False,
                    },
                    "artifact_first_authority": True,
                    "can_authorize_quality_verdict": False,
                    "can_authorize_submission_readiness": False,
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "scout",
                        "artifact_status": "partial",
                        "observed_artifact_refs": [
                            {"ref": "artifacts/stage_outputs/scout/route_recommendation.json"}
                        ],
                    }
                ],
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "stage_artifact_index.next_owner_action"
    assert action["next_owner"] == "idea"
    assert action["work_unit_id"] == "artifacts/stage_outputs/idea/line_selection_note.md"
    assert action["allowed_actions"] == ["materialize_stage_artifact_delta"]
    assert action["target_surface"] == {
        "ref_kind": "stage_artifact_index_required_output",
        "surface_ref": "artifacts/stage_outputs/idea/line_selection_note.md",
    }
    assert action["artifact_native_contract_ref"] == "mas-opl-stage-native-artifact-contract.v1"
    assert action["stage_artifact_contract_refs"] == {
        "manifest_ref": "artifacts/stage_outputs/idea/stage_artifact_manifest.json",
        "receipt_ref": "artifacts/stage_outputs/idea/owner_receipt.json",
    }
    assert action["authority_boundary"] == {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "stage_artifact_index_is_derived_projection": True,
    }
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "idea"
    assert monitoring["controller_action"] == "materialize_stage_artifact_delta"


def test_progress_first_monitoring_keeps_running_provider_liveness_from_overriding_artifact_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": "review_and_quality_gate",
                "next_owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "review_and_quality_gate",
                        "artifact_status": "partial",
                        "observed_artifact_refs": [
                            {"ref": "paper/review/story_surface_delta_20260603.json"}
                        ],
                    }
                ],
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "ai_reviewer",
                "active_stage_attempt_id": "sat-running",
                "active_workflow_id": "wf-running",
            },
        }
    )

    assert monitoring["running_provider_attempt"] is True
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    admission = monitoring["owner_action_admission"]
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_owner"] == "ai_reviewer"


def test_progress_first_monitoring_does_not_let_quality_gate_blocker_hide_artifact_next_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": "review_and_quality_gate",
                "next_owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "medical_prose_write_repair_after_reviewer_blocker",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "required_delta_kind": "paper_artifact_delta_before_gate_replay",
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "review_and_quality_gate",
                        "artifact_status": "partial",
                        "observed_artifact_refs": [
                            {"ref": "paper/review/story_surface_delta_20260603.json"}
                        ],
                    }
                ],
            },
            "domain_transition": {
                "typed_blocker": {
                    "blocker_id": "quality_gate_blocked",
                    "owner": "ai_reviewer",
                    "work_unit_id": "stale_quality_gate_replay",
                }
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["owner_action_admission"]["admission_requested"] is True


def test_progress_first_monitoring_keeps_publication_owner_gate_blocker_over_terminal_stage_folder_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "001-risk",
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
                    "authority_boundary": {
                        "artifact_first_can_determine_stage_progress": True,
                        "can_write_mas_truth": False,
                        "can_authorize_quality_verdict": False,
                        "can_authorize_publication_readiness": False,
                        "can_authorize_submission_readiness": False,
                        "provider_completion_is_paper_progress": False,
                    },
                    "terminal_publication_handoff": True,
                    "artifact_first_authority": True,
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "08-publication_package_handoff",
                        "artifact_status": "artifact_delta_present",
                        "observed_artifact_refs": [
                            {
                                "ref": "artifacts/stage_outputs/08-publication_package_handoff/owner_receipt.json"
                            }
                        ],
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "publishability_gate_blocked",
                    "owner": "ai_reviewer",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["typed_blocker"]["blocker_id"] == "publishability_gate_blocked"
    assert monitoring["next_owner"] == "ai_reviewer"
    assert monitoring["current_executable_owner_action"] is None
