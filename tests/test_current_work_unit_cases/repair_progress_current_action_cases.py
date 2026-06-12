from __future__ import annotations

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
