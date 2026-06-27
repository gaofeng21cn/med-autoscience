from __future__ import annotations

from .test_obligation_actuator_postcondition import _assert_exactly_one_dhd_apply_outcome


from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_obligation_actuator_readback_validator_is_not_supervisor_decision_engine() -> None:
    validator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts."
        "obligation_actuator_parts.readback_result_validator"
    )

    boundary = validator.readback_result_validator_boundary()
    assert boundary["validator_role"] == "accepted_owner_answer_or_opl_readback_shape_validator"
    assert boundary["local_allowed_outcome_table_role"] == (
        "contract_bound_result_shape_validation_not_supervisor_decision_engine"
    )
    assert boundary["mas_can_choose_supervisor_decision"] is False
    assert boundary["mas_can_run_supervisor_decision_engine"] is False
    assert boundary["mas_can_store_recovery_obligation"] is False
    assert boundary["mas_can_replay_obligation"] is False
    assert boundary["mas_can_create_opl_command_event_or_outbox"] is False
    assert boundary["mas_can_generate_human_gate_resume_token"] is False
    assert boundary["postcondition_success_requires_consumed_readback_identity"] is True
    assert boundary["consumed_readback_identity_surface_kind"] == (
        "consumed_obligation_readback_identity"
    )
    assert boundary["mas_domain_authority_readback_requires_authority_boundary"] is True
    assert boundary["read_model_evidence_refs_can_satisfy_success"] is False
    tail_requirement = validator.opl_obligation_actuator_tail_readback_requirement()
    forbidden_completion_claims = set(tail_requirement["forbidden_completion_claims"])
    assert {
        "repo_no_authority_guard_as_obligation_actuator_tail_readback",
        "mas_policy_projection_as_opl_recovery_obligation_store_readback",
        "mas_transition_request_as_supervisor_decision_engine_readback",
        "focused_tests_green_as_no_active_obligation_actuator_caller",
        "typed_blocker_authority_result_as_opl_supervisor_decision_engine_readback",
    } <= forbidden_completion_claims
    assert tail_requirement["mas_policy_projection_can_satisfy_readback"] is False
    assert tail_requirement["mas_request_projection_can_satisfy_readback"] is False
    assert tail_requirement["repo_no_authority_guard_can_satisfy_readback"] is False
    assert tail_requirement["focused_tests_can_satisfy_readback"] is False

    assert validator.allowed_outcomes_for_policy_label("consume_terminal_closeout") == {
        "owner_receipt_ref",
        "typed_blocker_ref",
    }
    assert "owner_receipt_ref" not in validator.allowed_outcomes_for_policy_label(
        "execute_current_owner_delta"
    )
    request_foundation = validator.opl_foundation_readback_boundary(
        source_family="mas_policy_request_projection"
    )
    assert request_foundation["success_source_family_required"] is False
    assert validator.outcome_has_required_foundation_readback(
        source_family="mas_policy_request_projection",
        opl_foundation=request_foundation,
    ) is False


def test_obligation_actuator_transition_request_is_projection_not_success(
    tmp_path: Path,
) -> None:
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(profile.studies_root / study_id),
        "current_executable_owner_action": {
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "fingerprint-current",
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_mas_transition_request_or_owner_callable",
                "provider_admission_allowed": True,
            },
            "current_authority": {
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "fingerprint-current",
                }
            },
            "supervisor_decision": {"decision": "execute_current_owner_delta"},
        },
        "provider_admission_candidates": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-current",
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "target_runtime_owner": "one-person-lab",
                    "target_runtime_kind": "DomainProgressTransitionRuntime",
                    "idempotency_key": "transition-request-current",
                    "mas_can_create_opl_outbox_record": False,
                    "aggregate_identity": {
                        "aggregate_kind": "paper_recovery_obligation",
                        "aggregate_id": f"{study_id}:medical_prose_write_repair:fingerprint-current",
                        "study_id": study_id,
                        "work_unit_id": "medical_prose_write_repair",
                    },
                    "source_generation": "source-generation-current",
                    "expected_version": 1,
                    "required_postcondition": {
                        "kind": "owner_receipt_or_typed_blocker",
                        "work_unit_fingerprint": "fingerprint-current",
                    },
                },
            }
        ],
    }
    report = {"managed_study_actions": [action]}

    actuator.apply_managed_study_obligation_actuator(
        report=report,
        profile=profile,
        study_ids=(study_id,),
        current_control_state={},
        fail_closed=True,
        phase="apply",
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    _assert_exactly_one_dhd_apply_outcome(outcome, "transition_request_pending")
    postcondition = report["managed_study_actions"][0]["dhd_apply_postcondition"]
    assert postcondition["ok"] is False
    assert postcondition["outcome_source_family"] == "mas_policy_request_projection"
    assert postcondition["request_projection_only"] is True
    assert postcondition["dhd_apply_success_proof"] == {}
    assert postcondition["success_requires_opl_foundation_readback_boundary"] is True
    foundation = postcondition["opl_foundation_readback_boundary"]
    assert foundation["source_family"] == "mas_policy_request_projection"
    assert foundation["mas_policy_request_projection_can_satisfy_success"] is False
    assert foundation["success_source_family_required"] is False
    consume_only = postcondition["consume_only_readback_boundary"]
    assert consume_only["surface_kind"] == "domain_health_diagnostic_apply_consume_only_readback"
    assert consume_only["opl_recovery_obligation_store_owner"] == "one-person-lab"
    assert consume_only["opl_supervisor_decision_engine_owner"] == "one-person-lab"
    assert consume_only["mas_can_store_recovery_obligation"] is False
    assert consume_only["mas_can_run_fixed_point_runtime"] is False
    assert consume_only["request_projection_is_success_outcome"] is False
    tail_requirement = consume_only["opl_obligation_actuator_tail_readback_requirement"]
    assert tail_requirement["mas_request_projection_can_satisfy_readback"] is False
    assert tail_requirement["focused_tests_can_satisfy_readback"] is False
    assert {
        "repo_no_authority_guard_as_obligation_actuator_tail_readback",
        "mas_policy_projection_as_opl_recovery_obligation_store_readback",
        "mas_transition_request_as_supervisor_decision_engine_readback",
        "focused_tests_green_as_no_active_obligation_actuator_caller",
        "typed_blocker_authority_result_as_opl_supervisor_decision_engine_readback",
    } <= set(tail_requirement["forbidden_completion_claims"])


def test_obligation_actuator_disallowed_supervisor_outcome_fails_postcondition(
    tmp_path: Path,
) -> None:
    actuator = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action = {
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(profile.studies_root / study_id),
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "run_mas_owner_callable",
                "provider_admission_allowed": False,
            },
            "current_authority": {
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "fingerprint-current",
                }
            },
            "supervisor_decision": {"decision": "execute_current_owner_delta"},
        },
    }
    report = {
        "managed_study_actions": [action],
        "managed_study_mas_owner_callable_actions": [
            {
                "study_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_fingerprint": "fingerprint-current",
                "ok": True,
                "status": "executed",
                "record_path": "artifacts/controller/quality_repair_batch/latest.json",
            }
        ],
    }

    actuator.apply_managed_study_obligation_actuator(
        report=report,
        profile=profile,
        study_ids=(study_id,),
        current_control_state={},
        fail_closed=True,
        phase="apply",
    )

    outcome = report["managed_study_obligation_actuator_outcomes"][0]
    assert outcome["outcome_kind"] == "owner_receipt_ref"
    assert outcome["paper_autonomy_supervisor_outcome_allowed"] is False
    assert outcome["postcondition_ok"] is False
    assert "success_outcome_source_family" not in outcome
    assert "dhd_apply_success_proof" not in outcome
    assert outcome["success_requires_opl_foundation_readback_boundary"] is True
    assert outcome["opl_foundation_readback_boundary"]["success_source_family"] == (
        "mas_owner_answer_readback"
    )
    assert outcome["consume_only_readback_boundary"]["supervisor_disallowed_outcome_is_success"] is False
    postcondition = report["managed_study_actions"][0]["dhd_apply_postcondition"]
    assert postcondition["ok"] is False
    assert postcondition["paper_autonomy_supervisor_outcome_allowed"] is False
    assert postcondition["dhd_apply_success_proof"] == {}
    assert postcondition["consume_only_readback_boundary"] == outcome["consume_only_readback_boundary"]
