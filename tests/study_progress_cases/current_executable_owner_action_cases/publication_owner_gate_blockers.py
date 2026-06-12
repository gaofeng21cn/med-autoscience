from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_keeps_publication_owner_gate_blocker_over_terminal_stage_folder_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "001-risk",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "artifact_delta_present",
                    "next_missing_surface": None,
                },
                "next_owner_action": {
                    "owner": "08-publication_package_handoff",
                    "next_owner": "publication_gate_owner",
                    "action_type": "publication_handoff_owner_gate",
                    "allowed_actions": ["publication_handoff_owner_gate"],
                    "required_delta_kind": "publication_handoff_owner_receipt_or_typed_blocker",
                    "work_unit_id": "publication_handoff_owner_gate",
                    "authority_boundary": {
                        "artifact_first_can_determine_stage_progress": True,
                        "can_write_mas_truth": False,
                        "can_authorize_quality_verdict": False,
                        "can_authorize_publication_readiness": False,
                        "can_authorize_submission_readiness": False,
                        "provider_completion_is_paper_progress": False,
                    },
                    "terminal_publication_handoff": True,
                    "artifact_first_authority": True,
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "08-publication_package_handoff",
                        "artifact_status": "artifact_delta_present",
                        "observed_artifact_refs": [
                            {
                                "ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json"
                            }
                        ],
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "publishability_gate_blocked",
                    "owner": "ai_reviewer",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["typed_blocker"]["blocker_id"] == "publishability_gate_blocked"
    assert monitoring["next_owner"] == "ai_reviewer"
    assert monitoring["current_executable_owner_action"] is None
