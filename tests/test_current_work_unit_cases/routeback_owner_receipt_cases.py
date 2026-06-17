from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_routeback_successor_consumes_prior_owner_receipt() -> None:
    module = _module()

    fingerprint = "publication-blockers::0915410f804b3697"
    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_progress_delta": {"count": 5},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
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
                    "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                },
                "evidence_refs": ["artifacts/controller/repair_execution_receipts/latest.json"],
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                    "work_unit_fingerprint": (
                        "domain-transition::ai_reviewer_re_eval::"
                        "ai_reviewer_medical_prose_quality_review"
                    ),
                    "next_action": "honor_ai_reviewer_publication_eval_authority",
                },
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "medical_prose_write_repair",
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "medical_prose_write_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "owner_route_currentness_basis": {
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_current_work_unit_projects_recovery_successor_without_current_action() -> None:
    module = _module()

    fingerprint = "publication-blockers::0915410f804b3697"
    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "obligation": {
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "conditions": [
                    {
                        "condition": "consumed_owner_receipt_routeback_successor",
                        "source_condition": "repair_progress_followup_owner_receipt_recorded",
                    }
                ],
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": (
                            "gate_clearing_batch_followthrough.actionable_current_work_unit"
                        ),
                        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
            },
        }
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert work_unit["currentness_basis"] == {
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
    }


def test_current_work_unit_projects_owner_action_ready_successor_over_repair_receipt() -> None:
    module = _module()

    fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "owner_receipt_required": True,
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "paper_recovery_successor": {
            "phase": "owner_action_ready",
            "source_next_safe_action_kind": "materialize_successor_owner_action",
            "provider_admission_allowed": False,
            "provider_admission_requires_opl_runtime_result": True,
            "opl_transition_runtime_required": True,
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        },
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
        },
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_receipt_ref": receipt_ref,
                "gate_replay_done": True,
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "schema_version": 1,
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "obligation": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "conditions": [
                    {
                        "condition": "consumed_owner_receipt_routeback_successor",
                        "source_condition": "current_work_unit_owner_receipt_recorded",
                    }
                ],
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
            },
        },
        current_executable_owner_action=action,
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"


def test_current_work_unit_projects_recovery_successor_over_unsupported_dispatch_closeout() -> None:
    module = _module()

    fingerprint = "publication-blockers::0915410f804b3697"
    closeout_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
        "supervision/consumer/default_executor_execution/sat_ff29f3cd92715d39043b1342.closeout.json"
    )
    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "schema_version": 1,
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "obligation": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "conditions": [
                    {
                        "condition": "consumed_owner_receipt_routeback_successor",
                        "source_condition": "current_work_unit_owner_receipt_recorded",
                    }
                ],
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "identity_match": True,
                },
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "status": "blocked",
                    "outcome": "blocked:unsupported_dispatch_surface",
                    "progress_delta_classification": "typed_blocker",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "source_path": closeout_ref,
                    "typed_blocker": {
                        "blocker_type": (
                            "No MAS owner receipt, artifact delta, or handler-owned typed blocker "
                            "was produced for the canonical manuscript story-surface target."
                        ),
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                    },
                }
            },
        }
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
