from __future__ import annotations

from tests.test_current_work_unit_cases.guarded_apply_cases import *  # noqa: F403,F401
from tests.test_current_work_unit_cases.readiness_identity_cases import *  # noqa: F403,F401
from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_projects_repair_progress_ai_reviewer_followup() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "repair-progress::002::ai-reviewer",
                "action_fingerprint": "repair-progress::002::ai-reviewer",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "acceptance_refs": ["artifacts/supervision/requests/ai_reviewer/latest.json"],
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == "repair-progress::002::ai-reviewer"


def test_current_work_unit_rejects_synthetic_ticket_as_current_fingerprint() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": (
                    "study-progress-current-owner-ticket::002-dm-cvd-mortality-risk::"
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs::"
                    "return_to_ai_reviewer_workflow"
                ),
                "action_fingerprint": (
                    "study-progress-current-owner-ticket::002-dm-cvd-mortality-risk::"
                    "produce_ai_reviewer_publication_eval_record_against_current_inputs::"
                    "return_to_ai_reviewer_workflow"
                ),
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "current_work_unit_unresolved"


def test_current_work_unit_projects_live_repair_progress_precedence_over_stage_readiness_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
                    ),
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_kind": "typed_blocker",
                    },
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:repair-progress-current",
            "action_fingerprint": "sha256:repair-progress-current",
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "owner_receipt_required": True,
            "required_delta_kind": "ai_reviewer_publication_eval_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": [
                "artifacts/controller/repair_execution_evidence/latest.json",
                "artifacts/controller/repair_execution_receipts/latest.json",
                "artifacts/supervision/requests/ai_reviewer/latest.json",
            ],
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": "complete_medical_paper_readiness_surface",
                "source_work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:repair-progress-current",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert work_unit["state"]["state_kind"] == "executable_owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_keeps_reconciled_current_action_over_stale_gate_terminal_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_2af188d02fc0999c46931598",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": "ai_reviewer_record_gate_consumption",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "work_unit_fingerprint": "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption",
                    "blocked_reason": "opl_execution_authorization_required",
                    "source_eval_id": (
                        "publication-eval::002-dm-china-us-mortality-attribution::"
                        "stage-attempt-sat_73cbcf44529e4c3ed3cd2e9a::2026-06-10T08:04:48+00:00"
                    ),
                    "source_path": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_2af188d02fc0999c46931598.closeout.json"
                    ),
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "gate_clearing_batch",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            }
        ],
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
            "action_fingerprint": "sha256:current-ai-reviewer-record",
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
            "owner_receipt_required": True,
            "required_delta_kind": "ai_reviewer_publication_eval_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": [
                "artifacts/controller/repair_execution_evidence/latest.json",
                "artifacts/controller/repair_execution_receipts/latest.json",
                "artifacts/supervision/requests/ai_reviewer/latest.json",
            ],
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "source_work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:current-ai-reviewer-record",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["work_unit_fingerprint"] == "sha256:current-ai-reviewer-record"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_suppresses_consumed_current_owner_action_receipt() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "dispatch_consumption": {
                "consumption_status": "consumed",
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                "receipt_kind": "ai_reviewer_publication_eval",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                "canonical_work_unit_identity": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "ai_reviewer",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
            "action_fingerprint": "sha256:consumed-ai-reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "allowed_actions": ["return_to_ai_reviewer_workflow"],
        },
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["action_type"] is None
    assert work_unit["work_unit_id"] is None
    assert work_unit["state"]["blocker_type"] == "current_work_unit_unresolved"


def test_current_work_unit_suppresses_consumed_action_using_progress_current_action_identity() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                "action_fingerprint": "sha256:consumed-ai-reviewer",
            },
            "dispatch_consumption": {
                "consumption_status": "consumed",
                "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                "receipt_kind": "ai_reviewer_publication_eval",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                "canonical_work_unit_identity": {
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                },
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            }
        ],
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["action_type"] is None
    assert work_unit["work_unit_id"] is None


def test_current_work_unit_preserves_readiness_blocker_over_next_forced_delta_without_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": "manuscript_story_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "canonical manuscript story-surface delta or typed blocker:manuscript_story_surface_delta_missing",
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_gate_consumption_action_over_stage_readiness_blocker() -> None:
    module = _module()

    for work_unit_id in (
        "ai_reviewer_record_gate_consumption",
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "stage_kernel_projection": {
                    "current_owner_delta": {
                        "owner": "MedAutoScience",
                        "action": "complete_medical_paper_readiness_surface",
                        "reason": "medical_paper_readiness_missing",
                        "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                        "source_kind": "typed_blocker",
                        "latest_owner_answer_kind": "typed_blocker",
                        "hard_gate": {"state": "domain_owner_answer_recorded"},
                    }
                },
            },
            actions=[
                {
                    "source": "study_progress.next_forced_delta.owner_action",
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "action_type": "run_gate_clearing_batch",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "write",
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                }
            ],
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "executable_owner_action"
        assert work_unit["owner"] == "write"
        assert work_unit["action_type"] == "run_gate_clearing_batch"
        assert work_unit["work_unit_id"] == work_unit_id
        assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_publication_eval_repair_over_stage_readiness_blocker() -> None:
    module = _module()
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )
    repair_fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "auto_runtime_parked",
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
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_eval_recommended_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_eval_recommended_action",
                "route_target": "write",
                "stage_typed_blocker_ref": typed_blocker_ref,
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_gate_consumption_action_over_opl_authorization_residue_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "owner_action": {
                    "next_owner": "gate_clearing_batch",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "gate_clearing_batch",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            }
        ],
        typed_blocker={
            "blocker_type": "opl_execution_authorization_required",
            "owner": "write",
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_binds_anti_loop_typed_blocker_as_owner_answer_ref() -> None:
    module = _module()
    typed_blocker_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/consumer/"
        "default_executor_execution/sat_82a2b164657c9b4d0c312db9.closeout.json#typed_blocker"
    )
    closeout_ref = typed_blocker_ref.removesuffix("#typed_blocker")
    work_unit_id = "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    work_unit_fingerprint = "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
            "publication_eval": {
                "eval_id": (
                    "publication-eval::002-dm-china-us-mortality-attribution::"
                    "stage-attempt-sat_73cbcf44529e4c3ed3cd2e9a::2026-06-10T08:04:48+00:00"
                )
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "run_quality_repair_batch",
                "next_owner": "write",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "source_fingerprint": "mas_default_executor_source_77f18f8da1eb6e57139208c1",
                "idempotency_key": "idem_cd631f437e1e7f3be53f386e",
                "allowed_actions": ["run_quality_repair_batch"],
            }
        ],
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_kind": "anti_loop_budget_exhausted",
            "reason": "anti_loop_budget_exhausted",
            "blocker_id": "opl_execution_authorization_required",
            "blocker_type": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "write_permitted": False,
            "provider_completion_is_domain_completion": False,
            "required_next_owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_ref": closeout_ref,
            "typed_blocker_ref": closeout_ref,
            "closeout_refs": [closeout_ref, typed_blocker_ref],
            "currentness_basis": {
                "truth_epoch": "",
                "runtime_health_epoch": "",
                "source_eval_id": "",
                "work_unit_fingerprint": "",
                "work_unit_id": "analysis_claim_evidence_repair",
                "owner_reason": "",
            },
        },
        runtime_health={"runtime_health_epoch": "runtime-health-event-006909-9c3c5d628dfad1da"},
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == work_unit_fingerprint
    assert work_unit["currentness_basis"]["work_unit_id"] == work_unit_id
    assert work_unit["currentness_basis"]["truth_epoch"] == "truth-event-000040-1a4d1f9cfed66d87"
    assert work_unit["currentness_basis"]["runtime_health_epoch"] == (
        "runtime-health-event-006909-9c3c5d628dfad1da"
    )
    blocker = work_unit["state"]["typed_blocker"]
    assert blocker["typed_blocker_ref"] == typed_blocker_ref
    assert blocker["latest_owner_answer_ref"] == typed_blocker_ref
    assert blocker["latest_owner_answer_kind"] == "typed_blocker"
    assert blocker["owner_answer_shape"] == "typed_blocker_ref"
    assert blocker["currentness_basis"]["work_unit_id"] == work_unit_id
    assert blocker["currentness_basis"]["work_unit_fingerprint"] == work_unit_fingerprint
    assert blocker["currentness_basis"]["source_fingerprint"] == "mas_default_executor_source_77f18f8da1eb6e57139208c1"
    assert blocker["currentness_basis"]["idempotency_key"] == "idem_cd631f437e1e7f3be53f386e"
    binding = work_unit["state"]["owner_answer_binding"]
    assert binding["answer_kind"] == "typed_blocker_ref"
    assert binding["typed_blocker_ref"] == typed_blocker_ref
    assert binding["accepted_answer_shape"] == [
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ]
    assert binding["stage_run_closeout_policy"]["provider_completion_is_domain_completion"] is False
    assert work_unit["required_output_contract"]["typed_blocker_ref"] == typed_blocker_ref
    assert work_unit["required_output_contract"]["domain_ready_authorized"] is False


def test_current_work_unit_projects_gate_consumption_action_over_stale_currentness_mismatch_blocker() -> None:
    module = _module()
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::stage-attempt-sat_current::"
        "2026-06-11T11:30:58+00:00"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::002-dm-china-us-mortality-attribution::"
        f"ai_reviewer_record_gate_consumption::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "eval_id": source_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": "ai_reviewer_record_gate_consumption",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "review_current_paper_delta",
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "write",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
        typed_blocker={
            "blocker_id": "gate_clearing_batch_source_eval_currentness_mismatch",
            "blocker_type": "gate_clearing_batch_source_eval_currentness_mismatch",
            "owner": "gate_clearing_batch",
            "work_unit_id": "ai_reviewer_record_gate_consumption",
            "work_unit_fingerprint": fingerprint,
            "current_ai_reviewer_eval_id": source_eval_id,
            "publication_eval_latest_eval_id": "publication-eval::older",
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_next_forced_story_repair_over_stage_readiness_blocker_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "study_progress.next_forced_delta.owner_action",
                "next_owner": "write",
                "work_unit_id": "manuscript_story_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "canonical manuscript story-surface delta or typed blocker:manuscript_story_surface_delta_missing",
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_current_dpcc_gate_replay_over_stage_readiness_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
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
                }
            },
        },
        current_executable_owner_action={
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
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "finalize"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_matching_current_control_repair_over_stage_readiness_blocker_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "manuscript_story_repair",
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": (
                        "canonical manuscript story-surface delta or "
                        "typed blocker:manuscript_story_surface_delta_missing"
                    ),
                },
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "manuscript_story_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "next_work_unit": "manuscript_story_repair",
                "action_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                "authority": "observability_only",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "manuscript_story_repair"
    assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_preserves_readiness_blocker_over_mismatched_current_control_repair_after_paper_delta() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "manuscript_story_repair",
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "manuscript_story_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "stale_writer_repair",
                "next_work_unit": "stale_writer_repair",
                "authority": "observability_only",
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_projects_matching_current_control_repair_over_prior_action_blocker_after_paper_delta() -> None:
    module = _module()

    for blocked_reason in (
        "domain_owner_action_dispatch_execution_count_zero",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_superseded_by_current_consumed_domain_transition",
        "stale_stage_attempt_current_owner_route_superseded",
        "stale_stage_packet_current_owner_route_changed",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "reason": "paper_progress_delta_observed",
                    "work_unit_id": "manuscript_story_repair",
                    "owner_action": {
                        "next_owner": "write",
                        "work_unit_id": "manuscript_story_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "owner_receipt_required": True,
                    },
                },
                "stage_kernel_projection": {
                    "current_owner_delta": {
                        "owner": "MedAutoScience",
                        "action": "complete_medical_paper_readiness_surface",
                        "reason": "medical_paper_readiness_missing",
                        "source_ref": (
                            "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
                        ),
                        "source_kind": "typed_blocker",
                        "latest_owner_answer_kind": "typed_blocker",
                        "hard_gate": {"state": "domain_owner_answer_recorded"},
                    }
                },
            },
            actions=[
                {
                    "source": "opl_current_control_state_action_queue",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "manuscript_story_repair",
                    "next_work_unit": "manuscript_story_repair",
                    "action_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                    "work_unit_fingerprint": "gate-replay-route-back::write::publication-blockers::497d1260db522f01",
                    "authority": "observability_only",
                }
            ],
            blocked_reason=blocked_reason,
            next_owner="write",
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "executable_owner_action"
        assert work_unit["owner"] == "write"
        assert work_unit["action_type"] == "run_quality_repair_batch"
        assert work_unit["work_unit_id"] == "manuscript_story_repair"
        assert work_unit["state"]["source"] == "opl_current_control_state_action_queue"
        assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_gate_replay_when_stale_quality_repair_closeout_is_superseded() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "next_forced_delta": {
                "required_delta_kind": "current_owner_action_or_typed_blocker",
                "reason": "publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "owner_action": {
                    "next_owner": "finalize",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "action_fingerprint": (
                    "study-progress-current-owner-ticket::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
                ),
                "work_unit_fingerprint": (
                    "study-progress-current-owner-ticket::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
                ),
                "authority": "observability_only",
            }
        ],
        typed_blocker={
            "blocker_type": "stale_stage_packet_current_owner_route_changed",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == (
        "stale_stage_packet_current_owner_route_changed"
    )


def test_current_work_unit_preserves_prior_action_blocker_over_mismatched_current_control_repair() -> None:
    module = _module()

    for blocked_reason in (
        "domain_owner_action_dispatch_execution_count_zero",
        "no_selected_dispatch_for_requested_action_types",
        "stage_packet_superseded_by_current_consumed_domain_transition",
    ):
        work_unit = module.build_current_work_unit(
            progress={
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "current_stage": "publication_supervision",
                "progress_first_sprint_state": {"paper_progress_delta_counted": True},
                "next_forced_delta": {
                    "required_delta_kind": "review_current_paper_delta",
                    "reason": "paper_progress_delta_observed",
                    "work_unit_id": "manuscript_story_repair",
                    "owner_action": {
                        "next_owner": "write",
                        "work_unit_id": "manuscript_story_repair",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "owner_receipt_required": True,
                    },
                },
            },
            actions=[
                {
                    "source": "opl_current_control_state_action_queue",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "stale_writer_repair",
                    "next_work_unit": "stale_writer_repair",
                    "authority": "observability_only",
                }
            ],
            blocked_reason=blocked_reason,
            next_owner="write",
        )

        _assert_contract_shape(work_unit)
        assert work_unit["status"] == "typed_blocker"
        assert work_unit["owner"] == "write"
        assert work_unit["work_unit_id"] is None
        assert work_unit["state"]["typed_blocker"]["blocker_type"] == blocked_reason


def test_current_work_unit_treats_accepted_repair_progress_followup_reason_as_current_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "repair-source-current",
                "repair_progress_followup": {
                    "accepted_owner_receipt": True,
                    "source_fingerprint": "repair-source-current",
                },
            }
        ],
        blocked_reason="repair_progress_ai_reviewer_recheck_required",
        next_owner="ai_reviewer",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_fingerprint"] == "repair-source-current"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_accepts_strict_running_provider_proof() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="gate_clearing_batch",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live",
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "work_unit_id": "publication_gate_replay",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live"


def test_current_work_unit_running_attempt_supersedes_ai_reviewer_recheck_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
        },
        blocked_reason="repair_progress_ai_reviewer_recheck_required",
        next_owner="ai_reviewer",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-ai-review",
            "active_stage_attempt_id": "sat-live-ai-review",
            "active_workflow_id": "wf-live-ai-review",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_running_attempt_supersedes_provider_admission_current_control_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="one-person-lab",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
            "active_stage_attempt_id": "sat-live-gate-replay",
            "active_workflow_id": "wf-live-gate-replay",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "live",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["work_unit_fingerprint"] == "domain-transition::route_back_same_line::dpcc"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate-replay"


def test_current_work_unit_running_attempt_supersedes_prior_opl_authorization_terminal_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "outcome": (
                        "blocked:{'blocker_id': 'opl_execution_authorization_required', "
                        "'owner': 'one-person-lab'}"
                    ),
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "source_path": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "supervision/consumer/default_executor_execution/latest.json"
                    ),
                }
            },
        },
        actions=[
            {
                "source": "opl_current_control_state_action_queue",
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_owner": "gate_clearing_batch",
                "next_work_unit": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
                "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            }
        ],
        next_owner="one-person-lab",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
            "active_stage_attempt_id": "sat-live-gate-replay",
            "active_workflow_id": "wf-live-gate-replay",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_fingerprint": "domain-transition::route_back_same_line::dpcc",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::dpcc",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate-replay"
    assert "typed_blocker" not in work_unit["state"]


def test_running_provider_attempt_uses_currentness_work_unit_before_attempt_identity() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        owner_route={
            "next_work_unit": {
                "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "lane": "finalize",
            }
        },
        next_owner="med-autoscience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-current-gate",
            "active_stage_attempt_id": "sat-live-current-gate",
            "active_workflow_id": "wf-live-current-gate",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["currentness_basis"]["work_unit_id"] == (
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    )
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-current-gate"
    assert work_unit["work_unit_id"] != work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"]


def test_current_work_unit_running_attempt_supersedes_prior_dispatch_zero_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        blocked_reason="domain_owner_action_dispatch_execution_count_zero",
        next_owner="med-autoscience",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-current-gate",
            "active_stage_attempt_id": "sat-live-current-gate",
            "active_workflow_id": "wf-live-current-gate",
            "owner": "gate_clearing_batch",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "work_unit_fingerprint": (
                "study-progress-current-owner-ticket::003::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
            ),
            "action_fingerprint": (
                "study-progress-current-owner-ticket::003::"
                "dpcc_publication_gate_replay_after_current_ai_reviewer_record::run_gate_clearing_batch"
            ),
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "med-autoscience"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-current-gate"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_ignores_terminal_log_without_matching_attempt_id() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate",
            "active_stage_attempt_id": "sat-live-gate",
            "active_workflow_id": "wf-live-gate",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": None,
                "status": "blocked",
                "source_path": "studies/003/artifacts/supervision/consumer/default_executor_execution/latest.json",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate"


def test_current_work_unit_treats_handoff_ready_as_pending_evidence_not_running() -> None:
    module = _module()
    handoff = {
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                "work_unit_fingerprint": "provider-admission::002::repair",
                "action_fingerprint": "provider-admission::002::repair",
            }
        ],
        provider_admission=handoff,
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is True
    assert work_unit["state"]["pending_provider_admission_evidence"]["execution_status"] == "handoff_ready"
    assert work_unit["status"] != "running_provider_attempt"


def test_current_work_unit_keeps_canonical_readiness_blocker_over_stale_readiness_queue() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "current_work_unit": {
                "status": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
        },
        actions=[
            {
                "source": "opl_current_control_state.action_queue",
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
            }
        ],
        typed_blocker={
            "blocker_type": "medical_paper_readiness_missing",
            "owner": "MedAutoScience",
            "work_unit_id": "complete_medical_paper_readiness_surface",
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"
    assert work_unit["work_unit_id"] == "complete_medical_paper_readiness_surface"


def test_current_work_unit_does_not_turn_stage_kernel_readiness_blocker_into_self_authorized_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "medical_paper_readiness": {"overall_status": "not_ready"},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": "readiness-blocker::current",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["action_type"] == "complete_medical_paper_readiness_surface"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"


def test_current_work_unit_ignores_stale_terminal_closeout_for_new_current_identity() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "status": "blocked",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "source_eval_id": "publication-eval::old",
                    "typed_blocker": {
                        "blocker_type": "manuscript_story_surface_delta_missing",
                        "owner": "write",
                    },
                },
            },
        },
        actions=[
            {
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": "publication-blockers::new",
                "action_fingerprint": "publication-blockers::new",
                "source_eval_id": "publication-eval::new",
                "owner_route_currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::new",
                    "source_eval_id": "publication-eval::new",
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
                "target_surface": {
                    "next_work_unit": {
                        "unit_id": "medical_prose_write_repair",
                        "lane": "write",
                    }
                },
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["work_unit_fingerprint"] == "publication-blockers::new"
    assert "typed_blocker" not in work_unit["state"]
