from __future__ import annotations

import importlib


def _readiness_action() -> dict[str, object]:
    return {
        "action_type": "complete_medical_paper_readiness_surface",
        "owner": "MedAutoScience",
        "next_work_unit": "complete_medical_paper_readiness_surface",
        "allowed_actions": ["complete_medical_paper_readiness_surface"],
        "work_unit_fingerprint": "sha256:medical-readiness-current-action",
        "action_fingerprint": "sha256:medical-readiness-current-action",
        "source_surface": "stage_kernel_projection.current_owner_delta",
    }


def _waiting_user_decision_park() -> dict[str, object]:
    return {
        "parked": True,
        "parked_state": "waiting_user_decision",
        "parked_owner": "user",
        "awaiting_explicit_wakeup": True,
        "auto_execution_complete": False,
        "source_reason": "quest_waiting_for_user",
        "runtime_failure_classification": {
            "requires_human_gate": True,
            "auto_recovery_allowed": False,
            "blocker_class": "publication_gate_recheck",
        },
    }


def test_envelope_requires_human_gate_authority_ref_before_parking_current_owner_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": _waiting_user_decision_park(),
            "runtime_health_snapshot": {
                "canonical_runtime_action": "continue_supervising_runtime",
                "runtime_liveness_status": "idle",
            },
        },
        progress={
            "auto_runtime_parked": _waiting_user_decision_park(),
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
        },
        actions=[_readiness_action()],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "MedAutoScience"
    assert envelope["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


def test_envelope_preserves_authorized_human_gate_over_current_owner_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": _waiting_user_decision_park(),
            "family_human_gates": [
                {
                    "gate_id": "status-waiting-dm003-publication-gate-recheck",
                    "evidence_refs": [
                        {
                            "ref_kind": "repo_path",
                            "ref": "artifacts/controller_decisions/latest.json",
                            "label": "controller_human_gate_decision",
                        }
                    ],
                }
            ],
        },
        progress={
            "auto_runtime_parked": _waiting_user_decision_park(),
            "parked_state": "waiting_user_decision",
            "parked_owner": "user",
        },
        actions=[_readiness_action()],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    assert envelope["state_kind"] == "parked"
    assert envelope["owner"] == "user"
    assert envelope["next_work_unit"] is None
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] == "waiting_user_decision"
