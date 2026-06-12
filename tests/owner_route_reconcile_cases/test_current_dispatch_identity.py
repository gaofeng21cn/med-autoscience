from __future__ import annotations

import importlib


def test_canonical_dispatch_identity_suppresses_residual_action_when_current_work_unit_is_typed_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.current_dispatch_identity"
    )

    identity = module.canonical_current_dispatch_identity(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        current_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "next_owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay-current",
        },
        current_work_unit={
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "sha256:gate-replay-current",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                },
            },
        },
        current_execution_envelope={"state_kind": "typed_blocker"},
    )

    assert identity == {
        "blocked": True,
        "source": "current_work_unit",
        "state_kind": "typed_blocker",
    }
