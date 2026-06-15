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


def test_current_work_unit_projects_repair_progress_gate_replay_over_stale_stage_packet_blocker() -> None:
    module = _module()
    gate_replay_fingerprint = "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_replay_fingerprint,
            "action_fingerprint": gate_replay_fingerprint,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": [
                "artifacts/controller/repair_execution_evidence/latest.json",
                "artifacts/controller/repair_execution_receipts/latest.json",
                "artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": "complete_medical_paper_readiness_surface",
                "source_work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": gate_replay_fingerprint,
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "status": "blocked",
            "blocker_id": "stage_packet_not_current_selected_dispatch",
            "blocker_type": "stage_packet_not_current_selected_dispatch",
            "reason": "stage_packet_not_current_selected_dispatch",
            "owner": "one-person-lab",
            "write_permitted": False,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": (
                "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch"
            ),
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_cfb833131bfa30d6661c26c2.closeout.json"
            ),
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_replay_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_paper_recovery_successor_over_opl_authorization_blocker() -> None:
    module = _module()
    repair_fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": True,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "status": "blocked",
            "blocker_id": "opl_execution_authorization_required",
            "blocker_type": "opl_execution_authorization_required",
            "blocked_reason": "opl_execution_authorization_required",
            "owner": "one-person-lab",
            "write_permitted": False,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9",
            "typed_blocker_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_same_work_unit_owner_receipt_over_current_action() -> None:
    module = _module()
    fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "paper_stage": "analysis-campaign",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_receipt_recorded",
                "current_authority": {
                    "obligation": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "next_safe_action": {
                    "kind": "consume_owner_receipt",
                    "owner": "write",
                    "provider_admission_allowed": False,
                    "owner_receipt_ref": receipt_ref,
                },
                "evidence_refs": [receipt_ref],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "owner_receipt_recorded"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"] == {
        "state_kind": "owner_receipt_recorded",
        "source": "paper_recovery_state.owner_receipt_recorded",
        "owner_receipt_ref": receipt_ref,
        "next_safe_action_kind": "consume_owner_receipt",
        "provider_admission_pending": False,
        "owner_answer_binding": {
            "answer_kind": "owner_receipt_ref",
            "owner_receipt_ref": receipt_ref,
        },
        "mas_owner_authority_preserved": True,
        "stale_queue_or_handoff_can_override": False,
    }
    assert work_unit["required_output_contract"] == {
        "owner_receipt_consumed": True,
        "owner_receipt_ref": receipt_ref,
        "provider_completion_is_domain_completion": False,
        "domain_ready_authorized": False,
    }


def test_current_work_unit_projects_paper_recovery_successor_over_terminal_opl_authorization_blocker() -> None:
    module = _module()
    repair_fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_old_auth_blocker",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                    "status": "blocked",
                    "outcome": "blocked_with_domain_typed_blocker",
                    "progress_delta_classification": "typed_blocker",
                    "typed_blocker": {
                        "blocker_id": "opl_execution_authorization_required",
                        "blocker_type": "opl_execution_authorization_required",
                        "blocked_reason": "opl_execution_authorization_required",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                    },
                    "source_path": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_old_auth_blocker.closeout.json"
                    ),
                }
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": True,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "status": "blocked",
            "blocker_id": "medical_publication_surface_blocked",
            "blocker_type": "medical_publication_surface_blocked",
            "blocked_reason": "medical_publication_surface_blocked",
            "owner": "one-person-lab",
            "write_permitted": False,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:old-publication-gate-replay",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_keeps_paper_recovery_successor_over_repair_progress_followup() -> None:
    module = _module()
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": True,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"


def test_current_work_unit_consumes_current_paper_recovery_successor_repair_receipt() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    gate_fingerprint = "sha256:6908b5fd4189779bc39fa7f869aeedd978159a73644c90b6ec2cf90b39d7a643"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": True,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"


def test_current_work_unit_repair_progress_followup_supersedes_same_gate_stall_closeout() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    gate_fingerprint = "sha256:6908b5fd4189779bc39fa7f869aeedd978159a73644c90b6ec2cf90b39d7a643"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/reports/publishability_gate/2026-06-15T121635Z.json",
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "stage_attempt_id": "sat_old_stall",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "outcome": "blocked:paper_progress_stall_terminal",
                    "progress_delta_classification": "typed_blocker",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "source_path": "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    "typed_blocker": {
                        "blocker_id": "paper_progress_stall_terminal",
                        "blocker_type": "paper_progress_stall_terminal",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": True,
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_keeps_provider_handoff_over_repair_progress_followup() -> None:
    module = _module()
    repair_fingerprint = "publication-blockers::provider-handoff-current"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "owner_route_reconcile.current_executable_owner_action",
        "next_owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "action_fingerprint": repair_fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "source_ref": "artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
    }
    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": repair_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
        },
        current_executable_owner_action=current_action,
        provider_admission={
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [current_action],
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == repair_fingerprint
    assert work_unit["state"]["source"] == "owner_route_reconcile.current_executable_owner_action"


def test_current_work_unit_ignores_refs_only_handoff_over_consumed_repair_successor() -> None:
    module = _module()
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    gate_fingerprint = "sha256:6908b5fd4189779bc39fa7f869aeedd978159a73644c90b6ec2cf90b39d7a643"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "action_fingerprint": repair_fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
        "paper_recovery_successor": {
            "phase": "owner_action_ready",
            "source_next_safe_action_kind": "materialize_successor_owner_action",
            "provider_admission_allowed": True,
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        },
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "runtime/quests/003/artifacts/reports/publishability_gate/current.json",
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
        },
        current_executable_owner_action=current_action,
        provider_admission={
            "surface_kind": "opl_current_control_state_study_handoff",
            "authority": "observability_only",
            "running_provider_attempt": False,
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "action_queue": [],
            "current_executable_owner_action": current_action,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "action_fingerprint": repair_fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"


def test_current_work_unit_prefers_repair_progress_owner_receipt_over_stale_terminal_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:7ede1907479d87ea1a88c4468749d0e63017d93b7b2d518cdcd9be95d4ee0e96"
    gate_receipt_ref = "artifacts/controller/gate_clearing_batch/latest.json"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": "publication-eval::003::current-ai-reviewer",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    gate_receipt_ref,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "stage_attempt_id": "sat_stale_gate_replay",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": "publication_gate_replay",
                    "outcome": "blocked:paper_progress_stall_terminal",
                    "progress_delta_classification": "typed_blocker",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "source_path": "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    "typed_blocker": {
                        "blocker_type": "paper_progress_stall_terminal",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "typed_blocker_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_fingerprint,
            "action_fingerprint": gate_fingerprint,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": [
                "artifacts/controller/repair_execution_evidence/latest.json",
                "artifacts/controller/repair_execution_receipts/latest.json",
                gate_receipt_ref,
            ],
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "owner_receipt_recorded"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert work_unit["state"]["owner_receipt_ref"] == gate_receipt_ref
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_repair_progress_gate_replay_over_zero_selected_dispatch_blocker() -> None:
    module = _module()
    gate_replay_fingerprint = "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_replay_fingerprint,
            "action_fingerprint": gate_replay_fingerprint,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
            "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "acceptance_refs": [
                "artifacts/controller/repair_execution_evidence/latest.json",
                "artifacts/controller/repair_execution_receipts/latest.json",
                "artifacts/controller/gate_clearing_batch/latest.json",
            ],
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": "complete_medical_paper_readiness_surface",
                "source_work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": gate_replay_fingerprint,
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "status": "blocked",
            "blocker_id": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
            "blocker_type": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
            "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
            "owner": "one-person-lab",
            "write_permitted": False,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_9bbb471b55ad5ceda9d8495e.closeout.json"
            ),
            "terminal_closeout_status": "blocked",
            "terminal_closeout_outcome": "typed_blocker",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_replay_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_publication_eval_repair_over_stale_gate_selector_blocker() -> None:
    module = _module()
    fingerprint = "publication-blockers::0915410f804b3697"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "publication_eval": {
                "eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "2026-06-12T20:06:05+00:00"
                ),
                "verdict": {"overall_verdict": "blocked"},
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": (
                    "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "2026-06-12T20:06:05+00:00"
                ),
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:8d94eccab0e8236ff9c5b46ae36f90251473f0da6b8b23e0392286976bb8f415",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "gate_replay_status": "blocked",
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_eval_recommended_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_eval_recommended_action",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_id": "no_selected_dispatch_for_requested_action_types",
            "blocker_type": "no_selected_dispatch_for_requested_action_types",
            "blocked_reason": "no_selected_dispatch_for_requested_action_types",
            "owner": "MedAutoScience",
            "write_permitted": False,
            "required_input": (
                "current selected MAS dispatch for action_type run_gate_clearing_batch "
                "or an accepted owner receipt for the already materialized gate_clearing_batch artifact"
            ),
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:8d94eccab0e8236ff9c5b46ae36f90251473f0da6b8b23e0392286976bb8f415",
            "action_fingerprint": "sha256:8d94eccab0e8236ff9c5b46ae36f90251473f0da6b8b23e0392286976bb8f415",
            "source_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat_556faaef7e4a16f309819eb3.closeout.json"
            ),
        },
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_projects_repair_progress_gate_replay_after_same_work_unit_repair_receipt() -> None:
    module = _module()
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_stage": "analysis-campaign",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "gate_replay_status": "blocked",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": repair_fingerprint,
            "action_fingerprint": repair_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": "write",
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "gate_clearing_batch_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
            "acceptance_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["work_unit_fingerprint"] == gate_fingerprint
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"


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
