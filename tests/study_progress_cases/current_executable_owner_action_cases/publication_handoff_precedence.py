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
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "typed_blocked",
                    "stage_progress_status": "typed_blocked",
                    "manifest_present": True,
                    "typed_blocker_ref": typed_blocker_ref,
                },
                "next_owner_action": {},
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"
    assert monitoring["typed_blocker"]["source_ref"] == typed_blocker_ref


def test_progress_first_monitoring_keeps_stage_native_repair_action_with_current_readiness_blocker() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {"overall_status": "blocked"},
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_native_current_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "stage_native_workspace_next_action",
                "status": "ready",
                "next_owner": "write",
                "work_unit_id": "run_quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "required_delta_kind": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
                "source_ref": (
                    "studies/002-dm-china-us-mortality-attribution/control/"
                    "next_action.json"
                ),
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "run_quality_repair_batch"
    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "stage_native_workspace_next_action"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["source_ref"].endswith("control/next_action.json")
    assert monitoring["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"


def test_progress_first_monitoring_routes_repair_delta_to_ai_reviewer_over_stale_stage_native_write_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )
    repair_evidence_ref = (
        "artifacts/controller/repair_execution_evidence/latest.json"
    )
    repair_receipt_ref = (
        "artifacts/controller/repair_execution_receipts/latest.json"
    )
    ai_reviewer_request_ref = (
        "artifacts/supervision/requests/ai_reviewer/latest.json"
    )
    gate_replay_request_ref = (
        "artifacts/controller/gate_replay_requests/latest.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_progress_delta": {
                "count": 1,
                "sources": ["repair_progress_projection.mas_owner_repair_execution_evidence"],
                "refs": [
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                    repair_evidence_ref,
                    repair_receipt_ref,
                    ai_reviewer_request_ref,
                    gate_replay_request_ref,
                ],
            },
            "progress_first_sprint_state": {
                "paper_progress_delta_counted": True,
                "classification": "deliverable_progress",
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "progress_delta_candidate": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "repair-source-current",
                "repair_execution_evidence_ref": repair_evidence_ref,
                "owner_receipt_ref": repair_receipt_ref,
                "ai_reviewer_recheck_request_ref": ai_reviewer_request_ref,
                "gate_replay_refs": [gate_replay_request_ref],
                "changed_artifact_refs": [
                    {
                        "path": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                            "paper/draft.md"
                        ),
                        "artifact_role": "canonical_manuscript_story_surface",
                    }
                ],
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_native_current_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "source": "stage_native_workspace_next_action",
                "status": "ready",
                "next_owner": "write",
                "work_unit_id": "run_quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "required_delta_kind": "canonical manuscript story-surface delta",
                    "source_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/control/"
                        "next_action.json"
                    ),
                },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "typed_blocked",
                    "stage_progress_status": "typed_blocked",
                    "manifest_present": True,
                    "typed_blocker_ref": typed_blocker_ref,
                },
                "next_owner_action": {
                    "owner": "08-publication_package_handoff",
                    "next_owner": "08-publication_package_handoff",
                    "action_type": "materialize_stage_artifact_delta",
                    "allowed_actions": ["materialize_stage_artifact_delta"],
                    "work_unit_id": (
                        "artifacts/stage_outputs/08-publication_package_handoff/"
                        "publication_package_manifest.json"
                    ),
                    "required_delta_kind": "stage_artifact_delta",
                },
                "stages": [
                    {
                        "stage_id": "08-publication_package_handoff",
                        "stage_progress_status": "typed_blocked",
                        "manifest_present": True,
                        "typed_blocker_ref": typed_blocker_ref,
                    }
                ],
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {
                        "state": "domain_owner_answer_recorded",
                        "owner_answer_ref": typed_blocker_ref,
                    },
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "ai_reviewer"
    assert monitoring["controller_action"] == "return_to_ai_reviewer_workflow"
    assert monitoring["next_work_unit"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert action["work_unit_fingerprint"] == "repair-source-current"
    assert action["action_fingerprint"] == "repair-source-current"
    assert action["source_ref"] == repair_evidence_ref
    assert action["target_surface"]["surface_ref"] == "artifacts/publication_eval/latest.json"
    assert action["target_surface"]["request_ref"] == ai_reviewer_request_ref
    assert action["target_surface"]["gate_replay_request_ref"] == gate_replay_request_ref


def test_current_executable_owner_action_skips_consumed_repair_progress_followup() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:consumed-ai-reviewer",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_refs": [
                    "runtime/quests/002/artifacts/reports/publishability_gate/current.json"
                ],
            },
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                    "canonical_work_unit_identity": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                    },
                }
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dm002_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
                "owner_action": {
                    "next_owner": "gate_clearing_batch",
                    "work_unit_id": "dm002_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["work_unit_id"] == "dm002_publication_gate_replay_after_current_ai_reviewer_record"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]


def test_current_executable_owner_action_keeps_ai_reviewer_followup_when_eval_lacks_repair_binding() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:repair-route-request",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_refs": [
                    "runtime/quests/002/artifacts/reports/publishability_gate/current.json"
                ],
            },
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_ref": "artifacts/publication_eval/latest.json",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:reviewer-output-record",
                    "canonical_work_unit_identity": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        "work_unit_fingerprint": "sha256:reviewer-output-record",
                        "source_eval_id": (
                            "publication-eval::002-dm-china-us-mortality-attribution::"
                            "stage-attempt-sat_current::2026-06-10T08:04:48+00:00"
                        ),
                    },
                }
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "next_owner": "write",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "allowed_actions": ["run_gate_clearing_batch"],
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "ai_reviewer"
    assert action["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert action["allowed_actions"] == ["return_to_ai_reviewer_workflow"]
    assert action["work_unit_fingerprint"] == "sha256:repair-route-request"


def test_current_executable_owner_action_consumes_ai_reviewer_followup_when_eval_binds_repair_source() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:repair-route-request",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_refs": [
                    "runtime/quests/002/artifacts/reports/publishability_gate/current.json"
                ],
            },
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_ref": "artifacts/publication_eval/latest.json",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:reviewer-output-record",
                    "canonical_work_unit_identity": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        "work_unit_fingerprint": "sha256:reviewer-output-record",
                        "source_eval_id": (
                            "publication-eval::002-dm-china-us-mortality-attribution::"
                            "stage-attempt-sat_current::2026-06-10T08:04:48+00:00"
                        ),
                        "repair_source_fingerprint": "sha256:repair-route-request",
                        "repair_execution_evidence_ref": (
                            "artifacts/controller/repair_execution_evidence/latest.json"
                        ),
                        "ai_reviewer_recheck_request_ref": (
                            "artifacts/supervision/requests/ai_reviewer/latest.json"
                        ),
                    },
                }
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "next_owner": "write",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "allowed_actions": ["run_gate_clearing_batch"],
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "write"
    assert action["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]


def test_current_executable_owner_action_consumes_record_only_ai_reviewer_terminal_closeout() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:fc2032327815ef9ab106e4ca972923ae2f18b3e3da019cf257298e2b3e3bc08a",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_refs": [
                    "runtime/quests/003/artifacts/reports/publishability_gate/current.json"
                ],
            },
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat_576b2b902ea0ef671d2764ab",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "closed_with_domain_owner_refs",
                    "source_path": (
                        "artifacts/supervision/consumer/stage_attempt_closeouts/"
                        "sat_576b2b902ea0ef671d2764ab.json"
                    ),
                    "paper_stage_log": {
                        "next_forced_delta": {
                            "required_delta_kind": (
                                "mas_owner_route_reconcile_or_typed_blocker_consumption"
                            ),
                            "owner": "mas_controller",
                            "action_type": (
                                "consume_record_only_ai_reviewer_closeout_or_route_next_owner"
                            ),
                            "work_unit_id": (
                                "after_produce_ai_reviewer_publication_eval_record_against_current_inputs"
                            ),
                            "reviewer_record_ref": (
                                "studies/003/artifacts/publication_eval/ai_reviewer_responses/"
                                "20260612T065527Z_publication_eval_record.json"
                            ),
                            "source_eval_id": (
                                "publication-eval::003::ai-reviewer-record::"
                                "20260612T065501Z::sat_576b2b902ea0ef671d2764ab"
                            ),
                        }
                    },
                }
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "mas_controller"
    assert action["action_type"] == "consume_record_only_ai_reviewer_closeout_or_route_next_owner"
    assert action["work_unit_id"] == (
        "after_produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert action["allowed_actions"] == [
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner"
    ]


def test_current_executable_owner_action_skips_consumed_repair_progress_from_domain_transition() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "domain_transition": {
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:consumed-ai-reviewer",
                }
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:consumed-ai-reviewer",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
            },
            "next_forced_delta": {
                "next_owner": "write",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "allowed_actions": ["request_opl_stage_attempt"],
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["request_opl_stage_attempt"],
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "write"
    assert action["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    assert action["allowed_actions"] == ["request_opl_stage_attempt"]


def test_progress_first_monitoring_materializes_stable_readiness_followup_without_domain_transition() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {
                "overall_status": "blocked",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "authoring_runtime_authorization",
                },
            },
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "required_input": "complete_medical_paper_readiness_surface",
                    "blocked_surface": "publication_handoff_owner_gate",
                    "surface_key": "authoring_runtime_authorization",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                }
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert action["source"] == "stage_kernel_projection.current_owner_delta"
    assert action["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert action["allowed_actions"] == ["complete_medical_paper_readiness_surface"]
    assert action["target_surface"]["surface_key"] == "authoring_runtime_authorization"


def test_progress_first_monitoring_keeps_manifest_backed_readiness_answer_closed() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "medical_paper_readiness": {
                "overall_status": "blocked",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "authoring_runtime_authorization",
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "MedAutoScience",
                "typed_blocker": {
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "source_ref": typed_blocker_ref,
                },
            },
            "stage_artifact_index": {
                "surface_kind": "stage_artifact_index",
                "current_stage": {
                    "stage_id": "08-publication_package_handoff",
                    "artifact_status": "typed_blocked",
                    "stage_progress_status": "typed_blocked",
                    "manifest_present": True,
                    "typed_blocker_ref": typed_blocker_ref,
                },
                "next_owner_action": {
                    "owner": "08-publication_package_handoff",
                    "next_owner": "08-publication_package_handoff",
                    "action_type": "materialize_stage_artifact_delta",
                    "allowed_actions": ["materialize_stage_artifact_delta"],
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
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                },
                "stage_run_kernel": {
                    "status": "TypedBlocked",
                    "typed_blocker_ref": typed_blocker_ref,
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["next_work_unit"] == "complete_medical_paper_readiness_surface"
    assert monitoring["current_executable_owner_action"] is None
    assert monitoring["typed_blocker"]["source_ref"] == typed_blocker_ref


def test_progress_first_monitoring_suppresses_residual_domain_transition_when_envelope_is_typed_blocker() -> None:
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
                    "blocker_id": "medical_paper_readiness_missing",
                    "owner": "MedAutoScience",
                },
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "finalize",
                "owner": "finalize",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "finalize",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                },
            },
        }
    )

    assert monitoring["execution_state_kind"] == "typed_blocker"
    assert monitoring["next_owner"] == "MedAutoScience"
    assert monitoring["next_work_unit"] is None
    assert monitoring["typed_blocker"]["blocker_id"] == "medical_paper_readiness_missing"
    assert monitoring["current_executable_owner_action"] is None


def test_progress_first_monitoring_routes_back_after_stable_readiness_answer() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    typed_blocker_ref = (
        "artifacts/stage_outputs/08-publication_package_handoff/"
        "receipts/typed_blocker.json"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "medical_paper_readiness": {
                "overall_status": "blocked",
                "next_action": {
                    "action_id": "complete_medical_paper_readiness_surface",
                    "surface_key": "authoring_runtime_authorization",
                    "summary": "补齐目标期刊写作层后再授权完整写作。",
                },
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "finalize",
                "owner": "finalize",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "lane": "finalize",
                    "summary": (
                        "Replay MAS publication gate and package/currentness checks against the "
                        "current AI reviewer record."
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
                    "surface_key": "authoring_runtime_authorization",
                    "source_ref": typed_blocker_ref,
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                }
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert action["source"] == "domain_transition"
    assert action["next_owner"] == "finalize"
    assert action["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert action["allowed_actions"] == ["request_opl_stage_attempt"]
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "request_opl_stage_attempt"
    assert monitoring["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"

__all__ = [name for name in globals() if name.startswith("test_")]
