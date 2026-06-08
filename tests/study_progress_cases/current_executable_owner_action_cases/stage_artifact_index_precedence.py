from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_derives_owner_action_from_stage_artifact_index_before_stale_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": "review_and_quality_gate",
                "next_owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "required_delta_kind": "quality_gate_replay_after_artifact_delta",
                    "target_surface": {
                        "ref_kind": "route_obligation",
                        "route_target": "finalize",
                        "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                    "target_surface_specificity": "explicit_owner_route_target",
                    "acceptance_refs": [
                        "studies/003-dm/paper/review/story_surface_delta_20260603.json"
                    ],
                },
                "stale_platform_repairs": [
                    {
                        "surface": "current_execution_envelope.typed_blocker",
                        "reason_code": "progress_first_owner_redrive_budget_exhausted",
                    }
                ],
                "stages": [
                    {
                        "stage_id": "review_and_quality_gate",
                        "artifact_delta": {"status": "fresh"},
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_id": "progress_first_owner_redrive_budget_exhausted",
                    "owner": "platform_repair",
                    "work_unit_id": "stale_read_model_reconcile",
                },
            },
            "domain_transition": {
                "typed_blocker": {
                    "blocker_id": "progress_first_owner_redrive_budget_exhausted",
                    "owner": "platform_repair",
                }
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == {
        "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    }
    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "stage_artifact_index.next_owner_action"
    assert action["artifact_first_precedence"]["stale_platform_repairs_superseded"] is True
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["owner_action_admission"]["admission_requested"] is True

def test_progress_first_monitoring_consumes_lane1_stage_artifact_index_action_shape() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "001-risk",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "idea",
                    "artifact_status": "missing",
                    "next_missing_surface": "artifacts/stage_outputs/idea/line_selection_note.md",
                },
                "next_owner_action": {
                    "owner": "idea",
                    "action_type": "materialize_stage_artifact_delta",
                    "required_output_surface": "artifacts/stage_outputs/idea/line_selection_note.md",
                    "artifact_native_contract_ref": "mas-opl-stage-native-artifact-contract.v1",
                    "manifest_ref": "artifacts/stage_outputs/idea/stage_manifest.json",
                    "receipt_ref": "artifacts/stage_outputs/idea/receipts/owner_receipt.json",
                    "authority_boundary": {
                        "artifact_first_can_determine_stage_progress": True,
                        "can_write_mas_truth": False,
                        "can_authorize_quality_verdict": False,
                        "can_authorize_publication_readiness": False,
                        "can_authorize_submission_readiness": False,
                        "provider_completion_is_paper_progress": False,
                    },
                    "artifact_first_authority": True,
                    "can_authorize_quality_verdict": False,
                    "can_authorize_submission_readiness": False,
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "scout",
                        "artifact_status": "partial",
                        "observed_artifact_refs": [
                            {"ref": "artifacts/stage_outputs/scout/route_recommendation.json"}
                        ],
                    }
                ],
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "stage_artifact_index.next_owner_action"
    assert action["next_owner"] == "idea"
    assert action["work_unit_id"] == "artifacts/stage_outputs/idea/line_selection_note.md"
    assert action["allowed_actions"] == ["materialize_stage_artifact_delta"]
    assert action["target_surface"] == {
        "ref_kind": "stage_artifact_index_required_output",
        "surface_ref": "artifacts/stage_outputs/idea/line_selection_note.md",
    }
    assert action["artifact_native_contract_ref"] == "mas-opl-stage-native-artifact-contract.v1"
    assert action["stage_artifact_contract_refs"] == {
        "manifest_ref": "artifacts/stage_outputs/idea/stage_manifest.json",
        "receipt_ref": "artifacts/stage_outputs/idea/receipts/owner_receipt.json",
    }
    assert action["authority_boundary"] == {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "stage_artifact_index_is_derived_projection": True,
    }
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "idea"
    assert monitoring["controller_action"] == "materialize_stage_artifact_delta"


def test_progress_first_monitoring_does_not_let_artifact_index_override_medical_readiness_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_not_ready",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                },
            },
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
                    "required_output_surface": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                    "work_unit_id": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                },
                "stale_platform_repairs": [
                    {"surface": "stage_artifact_index.next_owner_action"}
                ],
                "stages": [
                    {
                        "stage_id": "08-publication_package_handoff",
                        "observed_artifact_refs": [
                            {
                                "ref": (
                                    "artifacts/stage_outputs/08-publication_package_handoff/"
                                    "stage_manifest.json"
                                )
                            }
                        ],
                    }
                ],
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["typed_blocker"]["blocker_type"] == "medical_paper_readiness_not_ready"


def test_progress_first_monitoring_keeps_running_provider_liveness_from_overriding_artifact_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": "review_and_quality_gate",
                "next_owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "review_and_quality_gate",
                        "artifact_status": "partial",
                        "observed_artifact_refs": [
                            {"ref": "paper/review/story_surface_delta_20260603.json"}
                        ],
                    }
                ],
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "ai_reviewer",
                "active_stage_attempt_id": "sat-running",
                "active_workflow_id": "wf-running",
            },
        }
    )

    assert monitoring["running_provider_attempt"] is True
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    admission = monitoring["owner_action_admission"]
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_owner"] == "ai_reviewer"

def test_progress_first_monitoring_does_not_let_quality_gate_blocker_hide_artifact_next_owner_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": "review_and_quality_gate",
                "next_owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "medical_prose_write_repair_after_reviewer_blocker",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "required_delta_kind": "paper_artifact_delta_before_gate_replay",
                },
                "stale_platform_repairs": [],
                "stages": [
                    {
                        "stage_id": "review_and_quality_gate",
                        "artifact_status": "partial",
                        "observed_artifact_refs": [
                            {"ref": "paper/review/story_surface_delta_20260603.json"}
                        ],
                    }
                ],
            },
            "domain_transition": {
                "typed_blocker": {
                    "blocker_id": "quality_gate_blocked",
                    "owner": "ai_reviewer",
                    "work_unit_id": "stale_quality_gate_replay",
                }
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["typed_blocker"] is None
    assert monitoring["current_blockers"] == []
    assert monitoring["owner_action_admission"]["admission_requested"] is True

__all__ = [name for name in globals() if name.startswith("test_")]
