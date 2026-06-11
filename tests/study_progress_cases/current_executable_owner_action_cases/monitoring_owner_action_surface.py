from __future__ import annotations

from .. import shared as _shared


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
        "action_type": "run_gate_clearing_batch",
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


def test_progress_first_monitoring_routes_next_forced_delta_over_stale_readiness_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "medical_paper_readiness": {"overall_status": "not_ready"},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "source_kind": "typed_blocker",
                    "action": "complete_medical_paper_readiness_surface",
                    "owner": "MedAutoScience",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "latest_owner_answer_kind": "typed_blocker",
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "reason": "paper_progress_delta_observed",
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
                "route_target": "finalize",
                "owner": "finalize",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "finalize",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]
    assert monitoring["owner_action_admission"]["admission_requested"] is True


def test_progress_first_monitoring_routes_next_forced_delta_over_stale_owner_route_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
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

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": study_id,
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "write",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:stale-publication-gate-replay",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "owner_route_stale",
                        "blocked_reason": "owner_route_stale",
                        "owner": "write",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:stale-publication-gate-replay",
                    },
                },
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "target_surface_specificity": "explicit_owner_route_target",
                "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "current_executable_owner_action": {
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
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["owner_action_current"] is True
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == work_unit_id
    assert monitoring["current_executable_owner_action"]["work_unit_fingerprint"] == fingerprint


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


def test_current_owner_action_uses_gate_replay_after_ai_reviewer_record_consumed() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_current"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:current-ai-reviewer-record",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/latest.json"],
            },
            "domain_transition": {
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                    "canonical_work_unit_identity": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                    },
                }
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "eval_id": source_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "gate_clearing_batch",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "target_surface_specificity": "explicit_owner_route_target",
                "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
                "owner_action": {
                    "next_owner": "gate_clearing_batch",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_native_current_owner_action": {
                "source": "stage_native_workspace_next_action",
                "next_owner": "write",
                "work_unit_id": "medical_publication_surface_blocked_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    expected_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"ai_reviewer_record_gate_consumption::{source_eval_id}"
    )
    assert action["work_unit_fingerprint"] == expected_fingerprint
    assert action["action_fingerprint"] == expected_fingerprint
    assert action["source_eval_id"] == source_eval_id
    assert action["owner_route_currentness_basis"]["source_eval_id"] == source_eval_id
    assert action["owner_route_currentness_basis"]["work_unit_fingerprint"] == expected_fingerprint


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

    assert monitoring["running_provider_attempt"] is True
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


__all__ = [name for name in globals() if name.startswith("test_")]
