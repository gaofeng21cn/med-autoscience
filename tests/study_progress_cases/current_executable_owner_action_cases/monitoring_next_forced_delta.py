from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


SOURCE_EVAL_ID = (
    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
    "ai-reviewer-record::20260612T123416Z"
)


def test_progress_first_monitoring_exposes_current_executable_owner_action_from_next_forced_delta() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "source_eval_id": SOURCE_EVAL_ID,
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
                    "source_eval_id": SOURCE_EVAL_ID,
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
        "work_unit_fingerprint": (
            "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
            f"dpcc_publication_gate_replay_after_current_ai_reviewer_record::{SOURCE_EVAL_ID}"
        ),
        "action_fingerprint": (
            "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
            f"dpcc_publication_gate_replay_after_current_ai_reviewer_record::{SOURCE_EVAL_ID}"
        ),
        "source_eval_id": SOURCE_EVAL_ID,
        "owner_route_currentness_basis": {
            "source_eval_id": SOURCE_EVAL_ID,
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": (
                "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
                f"dpcc_publication_gate_replay_after_current_ai_reviewer_record::{SOURCE_EVAL_ID}"
            ),
            "source": "study_progress.next_forced_delta.owner_action",
        },
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
                "source_eval_id": SOURCE_EVAL_ID,
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
                    "source_eval_id": SOURCE_EVAL_ID,
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
    assert action["work_unit_fingerprint"].startswith("current-ai-reviewer-gate-replay::")
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
                "source_eval_id": SOURCE_EVAL_ID,
                "allowed_actions": ["run_gate_clearing_batch"],
                "owner_receipt_required": True,
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "source_eval_id": SOURCE_EVAL_ID,
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "source_eval_id": SOURCE_EVAL_ID,
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


def test_progress_first_monitoring_does_not_request_gate_replay_admission_without_eval_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
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

    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["owner_action_admission"] is None
