from __future__ import annotations

import importlib

from tests.provider_admission_current_control_helpers import (
    opl_transition_readback,
)
from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
)


def _opl_transition_request(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    transition_kind: str = "StartProviderAttempt",
) -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "target_runtime_owner": "one-person-lab",
        "request_owner": "med-autoscience",
        "authority_role": "domain_policy_request_only",
        "mas_can_create_opl_outbox_record": False,
        "runtime_kind": "DomainProgressTransitionRuntime",
        "recommended_transition_kind": transition_kind,
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": f"{study_id}::{work_unit_id}",
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "idempotency_key": f"paper-policy-request::{study_id}::{work_unit_id}::{fingerprint}",
        "source_generation": fingerprint,
        "expected_version": fingerprint,
        "required_postcondition": {
            "kind": "provider_admission_enqueued_or_blocked",
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
    }


def _opl_transition_result(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    stage_run_id: str = "stage-run-003-medical-prose",
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=f"paper-policy-request::{study_id}::{work_unit_id}::{fingerprint}",
        stage_run_id=stage_run_id,
    )


def test_naked_provider_admission_candidate_is_diagnostic_not_pending_recovery() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "status": "provider_admission_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
        }
    )

    assert state["phase"] != "admission_pending"
    assert state["phase"] == "owner_action_ready"
    assert state["next_safe_action"]["kind"] == "materialize_mas_transition_request_or_owner_callable"
    assert state["next_safe_action"]["provider_admission_allowed"] is True


def test_provider_admission_candidate_with_clean_mas_transition_request_waits_for_opl_readback() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "current_work_unit": _executable_work_unit(study_id=study_id, fingerprint=fingerprint),
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "status": "provider_admission_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                        "target_runtime_kind": "DomainProgressTransitionRuntime",
                        "target_runtime_owner": "one-person-lab",
                        "request_owner": "med-autoscience",
                        "authority_role": "domain_policy_request_only",
                        "mas_can_create_opl_outbox_record": False,
                        "runtime_kind": "DomainProgressTransitionRuntime",
                        "recommended_transition_kind": "StartProviderAttempt",
                        "aggregate_identity": {
                            "aggregate_kind": "study_work_unit",
                            "aggregate_id": f"{study_id}::{work_unit_id}",
                            "study_id": study_id,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                        },
                        "idempotency_key": "paper-policy-request::003::medical-prose",
                        "source_generation": fingerprint,
                        "expected_version": fingerprint,
                        "required_postcondition": {
                            "kind": "provider_admission_enqueued_or_blocked",
                            "outcome_owner": "one-person-lab",
                            "domain_state_owner": "med-autoscience",
                        },
                    },
                }
            ],
        }
    )

    assert state["phase"] == "transition_request_pending"
    assert state["conditions"] == [
        {
            "condition": "mas_transition_request_pending_opl_readback",
            "required_runtime": "DomainProgressTransitionRuntime",
        }
    ]
    assert state["next_safe_action"]["kind"] == "await_opl_transition_readback_or_non_advancing_apply"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_provider_admission_candidate_with_opl_runtime_readback_stays_pending() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "current_work_unit": _executable_work_unit(study_id=study_id, fingerprint=fingerprint),
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": study_id,
                    "status": "provider_admission_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "opl_domain_progress_transition_request": _opl_transition_request(
                        study_id=study_id,
                        work_unit_id=work_unit_id,
                        fingerprint=fingerprint,
                    ),
                    "opl_domain_progress_transition_result": _opl_transition_result(),
                }
            ],
        }
    )

    assert state["phase"] == "admission_pending"
    assert state["next_safe_action"]["kind"] == "consume_opl_provider_admission_readback"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["mas_can_authorize_provider_admission"] is False
    assert state["next_safe_action"]["requires_claimable_live_readback_source"] is True


def test_runtime_report_keeps_observe_only_transition_request_pending_until_opl_readback() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"

    result = report_aggregation.build_runtime_report(
        runtime_root=__import__("pathlib").Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[
            {
                "study_id": study_id,
                "status": "provider_admission_pending",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "opl_domain_progress_transition_request": _opl_transition_request(
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
            }
        ],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": _executable_work_unit(
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    assert result["will_start_llm"] is False
    assert result["paper_recovery_provider_admission_blocked_count"] == 0
    assert result["paper_recovery_states"][study_id]["phase"] == "owner_action_ready"
    action = result["managed_study_actions"][0]
    assert action.get("provider_admission_candidates") in (None, [])
    assert action["paper_recovery_state"]["phase"] == "owner_action_ready"
    assert action["current_work_unit"]["status"] == "executable_owner_action"
    assert action["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert action["supervisor_decision"]["decision"] == "opl_supervisor_decision_readback_required"
    assert action["supervisor_decision"]["read_model_can_build_supervisor_decision"] is False
    assert action["supervisor_decision"]["mas_can_run_supervisor_decision_engine"] is False
    assert action["provider_admission_state"]["status"] == "none"
    assert action["provider_admission_state"]["candidate_count"] == 0
    assert action["provider_admission_state"]["running_provider_attempt"] is False
