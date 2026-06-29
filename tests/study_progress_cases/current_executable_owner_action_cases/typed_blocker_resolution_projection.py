from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_action_projects_typed_blocker_resolution_next_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.package.submission_minimal",
                "action_type": "consume_submission_ready_package_authority_or_human_gate",
                "allowed_actions": [
                    "consume_submission_ready_package_authority_or_human_gate"
                ],
                "action_id": "next-action-typed-blocker",
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "owner": "mas_authority_kernel",
                "outcome_ref": (
                    "/workspace/ops/medautoscience/"
                    "paper_mission_typed_blocker_resolution/003/"
                    "typed_blocker_resolution.json"
                ),
                "work_unit_id": "submission_authority_owner_verdict",
                "work_unit_fingerprint": "sha256:resolution",
                "diagnostic_refs": [
                    {
                        "role": "typed_blocker_resolution",
                        "ref": "/workspace/ops/medautoscience/resolution.json",
                    }
                ],
            },
        }
    )

    assert action is not None
    assert action["surface_kind"] == "current_executable_owner_action"
    assert action["source"] == "paper_mission.next_action.owner_successor"
    assert action["next_owner"] == "mas_authority_kernel"
    assert action["action_type"] == "consume_submission_ready_package_authority_or_human_gate"
    assert action["allowed_actions"] == [
        "consume_submission_ready_package_authority_or_human_gate"
    ]
    assert action["work_unit_id"] == "submission_authority_owner_verdict"
    assert action["authority_boundary"]["can_write_owner_receipt"] is False
    assert action["authority_boundary"]["can_write_typed_blocker"] is False
    assert action["authority_boundary"]["can_write_human_gate"] is False
