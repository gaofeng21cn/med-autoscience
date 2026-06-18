from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_blocks_same_identity_record_only_terminal_closeout() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    closeout_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_execution/sat_f22f2e9d25d336fa2a2a4306.closeout.json"
    )
    owner_receipt_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/"
        "repair_execution_receipts/latest.json"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "authority": "med-autoscience",
                    "obligation": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    },
                },
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_f22f2e9d25d336fa2a2a4306",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "status": "closed",
                    "outcome": "closed_with_existing_mas_owner_receipt_ref; provider_completion_is_not_domain_completion",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "owner_receipt_ref": owner_receipt_ref,
                    "owner_receipt": {
                        "surface_kind": "mas_owner_receipt_ref",
                        "owner": "write",
                        "status": "owner_receipt_recorded",
                        "owner_receipt_ref": owner_receipt_ref,
                        "record_only_surface": True,
                    },
                    "artifact_delta": {
                        "changed_stage_surfaces": [closeout_ref],
                        "changed_paper_surfaces": [],
                        "artifact_delta_refs": [
                            owner_receipt_ref,
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                            "controller/repair_execution_evidence/latest.json",
                        ],
                    },
                    "paper_stage_log": {
                        "stage_name": work_unit_id,
                        "current_owner": "write",
                        "outcome": "closed_with_existing_mas_owner_receipt_ref; "
                        "provider_completion_is_not_domain_completion",
                        "changed_paper_surfaces": [],
                        "remaining_blockers": [
                            "provider_completion_is_not_domain_completion",
                            "publication_gate_or_ai_reviewer_owner_must_consume_owner_receipt_before "
                            "any quality, submission, or readiness verdict",
                        ],
                        "progress_delta_classification": "platform_repair",
                        "paper_progress_delta": {"count": 0, "refs": []},
                        "deliverable_progress_delta": {"count": 0, "refs": []},
                        "platform_repair_delta": {"count": 1, "refs": [closeout_ref]},
                        "next_forced_delta": {
                            "required_delta_kind": (
                                "consume_existing_owner_receipt_or_route_to_publication_gate_or_ai_reviewer_owner"
                            ),
                            "work_unit_id": work_unit_id,
                            "owner_action": {
                                "next_owner": "MedAutoScience",
                                "action_type": "consume_owner_receipt",
                                "work_unit_id": work_unit_id,
                            },
                            "acceptance_refs": [
                                "ai_reviewer_or_publication_gate_ref",
                                "mas_owner_receipt_ref",
                                "typed_blocker_ref",
                            ],
                            "reason": (
                                "The provider attempt is closed with existing owner receipt refs only; "
                                "readiness remains owned by MAS publication, gate, or reviewer surfaces."
                            ),
                        },
                    },
                    "closeout_refs": [closeout_ref, owner_receipt_ref],
                    "source_path": closeout_ref,
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
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "owner_receipt_required": True,
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
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "terminal_closeout_typed_blocker"
    assert work_unit["state"]["blocker_type"] == "non_advancing_apply"
    blocker = work_unit["state"]["typed_blocker"]
    assert blocker["blocked_reason"] == "fresh_readback_did_not_advance_same_aggregate"
    assert blocker["non_advancing_apply"] is True
    assert blocker["provider_completion_is_domain_completion"] is False
    assert blocker["owner_receipt_ref"] == owner_receipt_ref
    assert blocker["terminal_closeout_status"] == "closed"
    assert blocker["progress_delta_classification"] == "platform_repair"
    assert closeout_ref in blocker["acceptance_refs"]
