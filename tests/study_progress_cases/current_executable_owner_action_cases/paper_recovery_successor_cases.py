from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_action_uses_paper_recovery_successor_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "authority": "med-autoscience",
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_quality_repair_batch",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "source_surface": (
                            "gate_clearing_batch_followthrough.actionable_current_work_unit"
                        ),
                        "source_ref": (
                            "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                            "artifacts/controller/gate_clearing_batch/latest.json"
                        ),
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "next_owner": "write",
                    "paper_autonomy_obligation_ref": (
                        "paper-autonomy::003-dpcc-primary-care-phenotype-treatment-gap::"
                        "publication_supervision::run_gate_clearing_batch::publication_gate_replay::"
                        "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
                    ),
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": (
                    "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
                ),
                "state": {
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                    }
                },
            },
            "publication_eval": {
                "eval_id": source_eval_id,
            },
        }
    )

    assert action is not None
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert action["source_eval_id"] == source_eval_id
    assert action["owner_route_currentness_basis"]["work_unit_id"] == "medical_prose_write_repair"
