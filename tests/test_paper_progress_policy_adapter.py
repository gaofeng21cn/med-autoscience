from __future__ import annotations

import importlib


def test_policy_adapter_emits_opl_transition_request_without_claiming_runtime_authority() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "currentness_basis": {
                    "truth_epoch": "truth-event-1",
                    "runtime_health_epoch": "runtime-event-1",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    },
                },
            },
        },
        source="test",
    )

    assert result["surface_kind"] == "paper_progress_policy_adapter_result"
    assert result["authority"] == "med_autoscience.paper_progress_policy_adapter"
    assert result["authority_role"] == "paper_domain_policy_adapter_only"
    assert result["recommended_opl_transition_kind"] == "StartProviderAttempt"
    assert result["policy_outcome_kind"] == "provider_admission_requested"
    assert result["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert result["authority_boundary"]["opl_owns_transition_runtime"] is True
    assert result["authority_boundary"]["mas_can_create_opl_outbox_record"] is False
    assert result["provider_completion_is_domain_completion"] is False
    assert result["projection_metadata"]["authority"] is False
    assert result["projection_metadata"]["fixed_point_runtime_owner"] == "one-person-lab"
    assert result["paper_policy_verdict"]["accepted_result_families"] == [
        "provider_admission_request",
        "opl_runtime_readback_required",
    ]
    assert "opl_domain_progress_command" not in result
    assert "opl_domain_progress_command_outbox_record" not in result
    forbidden_fields = result["forbidden_runtime_fields"]
    assert "opl_domain_progress_transition_event" in forbidden_fields
    assert "opl_domain_progress_transition_outbox_item" in forbidden_fields
    assert "projection_metadata" in forbidden_fields
    assert "read_model_generation_metadata" in forbidden_fields
    assert "stage_run_identity" in forbidden_fields
    request = result["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["mas_can_create_opl_outbox_record"] is False
    assert request["recommended_transition_kind"] == "StartProviderAttempt"
    assert request["required_postcondition"]["kind"] == "provider_admission_enqueued_or_blocked"
    assert "projection_metadata" not in request
    assert "opl_domain_progress_transition_event" not in request
    assert "opl_domain_progress_transition_outbox_item" not in request
    assert "stage_run_identity" not in request


def test_policy_adapter_rejects_provider_admission_for_owner_callable_recovery() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "run_mas_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": False,
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "MaterializeOwnerAction"
    assert result["policy_outcome_kind"] == "owner_action_requested"
    assert result["paper_policy_verdict"]["provider_admission_allowed"] is False
    assert result["authority_boundary"]["mas_can_run_fixed_point_reconciler"] is False
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == "owner_action_ref"
    assert "opl_domain_progress_command_outbox_record" not in result


def test_policy_adapter_materializes_executable_owner_action_as_mas_transition_request() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_mas_transition_request_or_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": True,
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "MaterializeOwnerAction"
    assert result["policy_outcome_kind"] == "owner_action_requested"
    assert result["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert result["authority_boundary"]["mas_can_create_opl_outbox_record"] is False
    request = result["opl_domain_progress_transition_request"]
    assert request["recommended_transition_kind"] == "MaterializeOwnerAction"
    assert request["required_postcondition"]["kind"] == "owner_action_ref"
    assert "opl_domain_progress_transition_outbox_item" not in request
    assert "stage_run_identity" not in request


def test_policy_adapter_classifies_domain_owner_results_without_runtime_fields() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "typed_blocker_ref": "typed_blocker:003",
                },
            },
        },
        source="test",
    )

    assert result["recommended_opl_transition_kind"] == "RecordTypedBlocker"
    assert result["policy_outcome_kind"] == "typed_blocker"
    assert result["paper_policy_verdict"]["typed_blocker_ref"] == "typed_blocker:003"
    assert result["paper_policy_verdict"]["paper_progress_credit_allowed"] is True
    assert result["authority_boundary"]["mas_can_create_domain_typed_blocker"] is True
    assert "opl_domain_progress_transition_event" not in result
    assert "opl_domain_progress_transition_outbox_item" not in result


def test_policy_adapter_non_advancing_apply_requires_typed_blocker_projection() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_non_advancing_policy_blocker(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
        }
    )

    assert result["recommended_opl_transition_kind"] == "NonAdvancingApply"
    assert result["policy_outcome_kind"] == "non_advancing_apply_typed_blocker"
    assert result["paper_policy_verdict"]["typed_blocker_type"] == "non_advancing_apply"
    assert result["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "non_advancing_apply_typed_blocker_ref"
    )
    assert result["projection_metadata"]["authority"] is False
    assert "projection_metadata" not in result["opl_domain_progress_transition_request"]
    assert "opl_domain_progress_transition_event" not in result
