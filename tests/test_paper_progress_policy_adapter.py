from __future__ import annotations

import importlib


def test_policy_adapter_emits_opl_command_without_claiming_transition_authority() -> None:
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
    assert result["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert result["authority_boundary"]["opl_owns_transition_runtime"] is True
    assert "opl_domain_progress_command" not in result
    command = result["opl_domain_progress_command_outbox_record"]
    assert command["surface_kind"] == "opl_generic_current_control_command_outbox_record"
    assert command["runtime_kind"] == "DomainProgressTransitionRuntime"
    assert command["runtime_owner"] == "one-person-lab"
    assert command["transition_kind"] == "StartProviderAttempt"
    assert command["postcondition"]["kind"] == "provider_admission_enqueued_or_blocked"


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
    assert result["paper_policy_verdict"]["provider_admission_allowed"] is False
    assert result["authority_boundary"]["mas_can_run_fixed_point_reconciler"] is False
    assert result["opl_domain_progress_command_outbox_record"]["postcondition"]["kind"] == "owner_action_ref"
