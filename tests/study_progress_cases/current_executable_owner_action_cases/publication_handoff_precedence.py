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

def test_progress_first_monitoring_prefers_handoff_typed_blocker_readiness_followup_over_terminal_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {
                "overall_status": "blocked",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "literature_provider_runtime",
                    "summary": "运行联网 literature provider runtime 并写入可审计来源后再继续。",
                },
            },
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
                    "terminal_publication_handoff": True,
                    "artifact_first_authority": True,
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_not_ready",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                }
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["controller_action"] == "complete_medical_paper_readiness_surface"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert action["source"] == "stage_kernel_projection.current_owner_delta"
    assert action["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert action["blocked_surface"] == "publication_handoff_owner_gate"
    assert action["surface_key"] == "literature_provider_runtime"
    assert action["next_action"]["surface_key"] == "literature_provider_runtime"
    assert action["target_surface"]["surface_key"] == "literature_provider_runtime"
    assert action["artifact_first_precedence"]["typed_blocker_followup_takes_precedence"] is True


def test_progress_first_monitoring_accepts_current_stage_run_typed_blocker_answer() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "missing_manifest_or_receipt",
                    "next_missing_surface": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                },
                "next_owner_action": {
                    "owner": "08-publication_package_handoff",
                    "next_owner": "08-publication_package_handoff",
                    "action_type": "materialize_stage_artifact_delta",
                    "allowed_actions": ["materialize_stage_artifact_delta"],
                    "required_delta_kind": "stage_artifact_delta",
                    "work_unit_id": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                    "source_kind": "typed_blocker",
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "receipts/typed_blocker.json"
                    ),
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["controller_action"] == "complete_medical_paper_readiness_surface"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert action["source"] == "stage_kernel_projection.current_owner_delta"
    assert action["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert action["source_ref"] == (
        "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    )
    assert action["artifact_first_precedence"] == {
        "superseded_stage_artifact_action": "publication_handoff_owner_gate",
        "reason": "medical_paper_readiness_missing",
        "typed_blocker_followup_takes_precedence": True,
    }

__all__ = [name for name in globals() if name.startswith("test_")]
