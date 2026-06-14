from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_preserves_anti_loop_stop_loss_over_stage_readiness_blocker() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    canonical_work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                },
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_kind": "anti_loop_budget_exhausted",
            "reason": "anti_loop_budget_exhausted",
            "blocker_id": "opl_execution_authorization_required",
            "blocker_type": "anti_loop_budget_exhausted",
            "blocked_reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": canonical_work_unit_id,
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
                "work_unit_id": canonical_work_unit_id,
            },
        },
        blocked_reason="anti_loop_budget_exhausted",
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["work_unit_id"] == canonical_work_unit_id
    assert work_unit["state"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert work_unit["state"]["source"] == "typed_blocker"


def test_current_work_unit_routes_opl_authorization_typed_blocker_over_stage_readiness_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                },
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_type": "opl_execution_authorization_required",
            "blocked_reason": "opl_execution_authorization_required",
            "owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_e1063d97901cc3d70424fc5c.closeout.json"
            ),
            "typed_blocker_ref": (
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
                "consumer/default_executor_execution/sat_e1063d97901cc3d70424fc5c.closeout.json#domain_blocker"
            ),
            "stage_attempt_id": "sat_e1063d97901cc3d70424fc5c",
            "terminal_closeout_status": "blocked",
            "terminal_closeout_outcome": "typed_blocker",
            "progress_delta_classification": "typed_blocker",
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["state"]["source"] == "typed_blocker"
    assert work_unit["state"]["blocker_type"] == "opl_execution_authorization_required"
    assert work_unit["state"]["typed_blocker"]["owner"] == "gate_clearing_batch"


def test_current_work_unit_normalizes_structured_terminal_authorization_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "publication_gate_replay"
    fingerprint = "domain-transition::route_back_same_line::publication_gate_replay"
    blocker = {
        "blocker_id": "opl_execution_authorization_required",
        "owner": "one-person-lab",
        "write_permitted": False,
        "required_input": "OPL provider attempt, lease, or closeout receipt binding",
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": work_unit_id,
                    "outcome": f"blocked:{blocker}",
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": [str(blocker)],
                    "paper_stage_log": {
                        "stage_name": work_unit_id,
                        "outcome": f"blocked:{blocker}",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": [str(blocker)],
                        "next_forced_delta": {
                            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                            "reason": f"typed_blocker::{blocker}",
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "gate_clearing_batch",
                                "action_type": "run_gate_clearing_batch",
                                "work_unit_id": work_unit_id,
                            },
                        },
                    },
                    "source_path": (
                        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/supervision/consumer/default_executor_execution/latest.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["blocker_type"] == "opl_execution_authorization_required"
    assert work_unit["state"]["typed_blocker"]["blocker_id"] == "opl_execution_authorization_required"
    assert work_unit["state"]["typed_blocker"]["blocked_reason"] == "opl_execution_authorization_required"


def test_current_work_unit_terminal_rehydrate_blocker_keeps_opl_owner_over_domain_next_owner() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_medical_prose_quality_review"
    fingerprint = "ai-reviewer::rehydrate-required::current"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "blocked",
                    "blocked_reason": "medical_prose_review_request_rehydrate_required",
                    "stage_name": work_unit_id,
                    "progress_delta_classification": "typed_blocker",
                    "typed_blocker": {
                        "blocked_reason": "medical_prose_review_request_rehydrate_required",
                        "next_owner": "ai_reviewer",
                        "write_permitted": False,
                    },
                    "paper_stage_log": {
                        "stage_name": work_unit_id,
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": [
                            "medical_prose_review_request_rehydrate_required",
                        ],
                        "progress_delta_classification": "typed_blocker",
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "ai_reviewer",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
        },
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["blocker_type"] == "medical_prose_review_request_rehydrate_required"
    assert work_unit["state"]["typed_blocker"]["owner"] == "one-person-lab"
