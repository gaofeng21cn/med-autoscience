from __future__ import annotations

from tests.provider_admission_current_control_helpers import opl_transition_readback
from tests.test_paper_recovery_state_cases.shared import _executable_work_unit, _module


STUDY_ID = "003-dpcc-primary-care-phenotype-treatment-gap"
WORK_UNIT_ID = "medical_prose_write_repair"
WORK_UNIT_FINGERPRINT = "publication-blockers::0915410f804b3697"
ACTION_TYPE = "run_quality_repair_batch"


def _transition_request() -> dict[str, object]:
    return {
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
            "aggregate_id": f"{STUDY_ID}::{WORK_UNIT_ID}",
            "study_id": STUDY_ID,
            "work_unit_id": WORK_UNIT_ID,
            "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
        },
        "idempotency_key": (
            f"paper-policy-request::{STUDY_ID}::{WORK_UNIT_ID}::{WORK_UNIT_FINGERPRINT}"
        ),
        "source_generation": WORK_UNIT_FINGERPRINT,
        "expected_version": WORK_UNIT_FINGERPRINT,
        "required_postcondition": {
            "kind": "provider_admission_enqueued_or_blocked",
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
    }


def _live_readback() -> dict[str, object]:
    route_key = f"provider-admission::{STUDY_ID}::{WORK_UNIT_FINGERPRINT}"
    return opl_transition_readback(
        STUDY_ID,
        action_fingerprint=WORK_UNIT_FINGERPRINT,
        work_unit_id=WORK_UNIT_ID,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=(
            f"paper-policy-request::{STUDY_ID}::{WORK_UNIT_ID}::{WORK_UNIT_FINGERPRINT}"
        ),
        stage_run_id="stage-run-003-medical-prose",
    )


def test_request_only_provider_admission_candidate_does_not_suppress_projection_contradiction() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": STUDY_ID,
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": WORK_UNIT_ID,
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {"handling_state": "explicit_resume_pending"},
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": STUDY_ID,
                    "status": "provider_admission_pending",
                    "action_type": ACTION_TYPE,
                    "work_unit_id": WORK_UNIT_ID,
                    "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
                    "action_fingerprint": WORK_UNIT_FINGERPRINT,
                    "opl_domain_progress_transition_request": _transition_request(),
                }
            ],
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["next_safe_action"]["kind"] == "repair_projection_before_admission"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_opl_live_readback_provider_admission_candidate_suppresses_stale_projection() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": STUDY_ID,
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": WORK_UNIT_ID,
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {"handling_state": "explicit_resume_pending"},
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": STUDY_ID,
                    "status": "provider_admission_pending",
                    "action_type": ACTION_TYPE,
                    "work_unit_id": WORK_UNIT_ID,
                    "work_unit_fingerprint": WORK_UNIT_FINGERPRINT,
                    "action_fingerprint": WORK_UNIT_FINGERPRINT,
                    "opl_domain_progress_transition_request": _transition_request(),
                    "opl_domain_progress_transition_runtime_live_readback": _live_readback(),
                }
            ],
        }
    )

    assert state["phase"] == "admission_pending"
    assert state["next_safe_action"]["kind"] == "consume_opl_provider_admission_readback"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["mas_can_authorize_provider_admission"] is False
