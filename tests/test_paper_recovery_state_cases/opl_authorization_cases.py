from __future__ import annotations

from tests.test_paper_recovery_state_cases.shared import _module, _typed_blocker_work_unit


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
        "required_input": "OPL provider attempt, lease, or closeout receipt binding",
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
        "kind": "materialize_provider_admission_or_owner_callable",
        "owner": "gate_clearing_batch",
        "provider_admission_allowed": True,
    }
