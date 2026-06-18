from __future__ import annotations

from tests.provider_admission_current_control_helpers import opl_transition_readback
from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
    _typed_blocker_work_unit,
)


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
        "idempotency_key": f"paper-policy-request::{STUDY_ID}::{WORK_UNIT_ID}::{WORK_UNIT_FINGERPRINT}",
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
        request_idempotency_key=f"paper-policy-request::{STUDY_ID}::{WORK_UNIT_ID}::{WORK_UNIT_FINGERPRINT}",
        stage_run_id="stage-run-003-medical-prose",
    )


def test_current_typed_blocker_supersedes_stale_operator_projection() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="gate_clearing_batch",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                blocker_type="opl_execution_authorization_required",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "gate_clearing_batch",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                },
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        }
    )

    assert state["phase"] == "domain_blocked"
    assert state["conditions"] == [
        {
            "condition": "current_work_unit_typed_blocker",
            "blocker_type": "opl_execution_authorization_required",
        }
    ]
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["current_authority"]["obligation"]["owner"] == "gate_clearing_batch"
    assert state["next_safe_action"]["kind"] == "provide_opl_execution_authorization_or_human_gate"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


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
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
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
    assert state["conditions"] == [
        {
            "condition": "operator_card_contradicts_auto_runtime_parked",
            "operator_handling_state": "explicit_resume_pending",
            "auto_runtime_parked": False,
        }
    ]
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
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
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
    assert state["conditions"] == [{"condition": "provider_admission_pending"}]
    assert state["next_safe_action"]["kind"] == "admit_provider_attempt"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["current_authority"]["owner"] == "write"


def test_opl_execution_authorization_blocker_routes_to_opl_runtime_owner() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="gate_clearing_batch",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                blocker_type="opl_execution_authorization_required",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "gate_clearing_batch",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                },
            },
        }
    )

    assert state["phase"] == "domain_blocked"
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["current_authority"]["authority"] == "one-person-lab"
    assert state["current_authority"]["obligation"]["owner"] == "gate_clearing_batch"
    assert state["next_safe_action"] == {
        "kind": "provide_opl_execution_authorization_or_human_gate",
        "owner": "one-person-lab",
        "provider_admission_allowed": False,
        "required_input": "OPL provider attempt, active lease, and execution authorization decision",
    }


def test_opl_execution_authorization_obligation_keeps_blocked_domain_owner() -> None:
    current_work_unit = _typed_blocker_work_unit(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        owner="one-person-lab",
        action_type="run_gate_clearing_batch",
        work_unit_id="publication_gate_replay",
        blocker_type="opl_execution_authorization_required",
    )
    current_work_unit["state"]["typed_blocker"]["owner"] = "gate_clearing_batch"

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
        }
    )

    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["current_authority"]["obligation"]["owner"] == "gate_clearing_batch"


def test_opl_authorization_blocker_yields_owner_action_ready_when_repair_followup_is_current() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="gate_clearing_batch",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                blocker_type="opl_execution_authorization_required",
            ),
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "action_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "repair_progress_precedence": {
                    "paper_delta_observed": True,
                    "accepted_owner_receipt": True,
                    "source_work_unit_id": "medical_prose_write_repair",
                    "source_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "gate_clearing_batch",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                },
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["current_authority"]["owner"] == "gate_clearing_batch"
    assert state["conditions"] == [{"condition": "current_owner_action_ready"}]
    assert state["next_safe_action"] == {
        "kind": "materialize_mas_transition_request_or_owner_callable",
        "owner": "gate_clearing_batch",
        "provider_admission_allowed": True,
    }


def test_opl_authorization_blocker_yields_recovery_successor_when_current_action_supersedes_it() -> None:
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="one-person-lab",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                blocker_type="opl_execution_authorization_required",
            )
            | {
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
                "currentness_basis": {
                    "source_eval_id": source_eval_id,
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                },
            },
            "current_executable_owner_action": {
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
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "owner_receipt_required": True,
                "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
                "paper_recovery_successor": {
                    "phase": "owner_action_ready",
                    "source_next_safe_action_kind": "materialize_successor_owner_action",
                    "provider_admission_allowed": True,
                    "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                },
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "current_owner_action_supersedes_typed_blocker",
            "blocker_type": "opl_execution_authorization_required",
        }
    ]
    assert state["current_authority"]["owner"] == "write"
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
    }
