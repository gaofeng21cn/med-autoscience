from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_blocked_terminal_gate_replay_routes_to_publication_eval_repair_successor() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_attempt_id = "sat_d2b4c700b31294ab17c225d4"
    gate_report_ref = (
        "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/reports/publishability_gate/2026-06-14T080316Z.json"
    )
    gate_record_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/gate_clearing_batch/latest.json"
    )
    closeout_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        f"artifacts/supervision/consumer/default_executor_execution/{gate_attempt_id}.closeout.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": study_id,
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
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "stage_attempt_id": gate_attempt_id,
                        "typed_blocker_ref": closeout_ref,
                    },
                },
            },
            "current_owner_delta": {
                "source_ref": closeout_ref,
                "hard_gate": {"owner_answer_ref": closeout_ref},
            },
            "latest_terminal_stage_log": {
                "status": "blocked",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "stage_attempt_id": gate_attempt_id,
                "source_path": closeout_ref,
                "paper_stage_log": {
                    "outcome": "blocked:publication_gate_replay_blocked",
                    "remaining_blockers": [
                        "stale_submission_minimal_authority",
                        "medical_publication_surface_blocked",
                        "reviewer_first_concerns_unresolved",
                        "submission_hardening_incomplete",
                    ],
                    "next_forced_delta": {
                        "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
                        "work_unit_id": "publication_gate_replay",
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            "gate_replay_report_ref": gate_report_ref,
                        },
                        "owner_action": {
                            "next_owner": "publication_gate",
                            "action_type": "return_to_publishability_gate",
                            "work_unit_id": "publication_gate_replay",
                        },
                        "acceptance_refs": [
                            "owner_receipt_ref",
                            "typed_blocker_ref",
                            "changed_surface_ref",
                        ],
                        "reason": "typed_blocker::publication_gate_replay_blocked",
                    },
                },
                "closeout_refs": [closeout_ref, gate_record_ref, gate_report_ref],
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "publication-blockers::0915410f804b3697",
                "source_eval_id": "publication-eval::003::current",
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": "artifacts/controller/quality_repair_batch/latest.json",
                "gate_replay_done": True,
                "gate_replay_refs": [gate_record_ref, gate_report_ref],
            },
            "publication_eval": {
                "schema_version": 1,
                "eval_id": "publication-eval::003::post-gate-replay-blocked",
                "study_id": study_id,
                "recommended_actions": [
                    {
                        "action_id": (
                            "publication-eval-action::route_back_same_line::"
                            "publication-blockers::0915410f804b3697"
                        ),
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "route_target": "write",
                        "reason": "Recommended route-back: return_to_write.",
                        "route_key_question": (
                            "What is the narrowest same-line manuscript repair required now?"
                        ),
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "evidence_refs": [gate_report_ref],
                        "next_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                            "summary": (
                                "Repair structured medical reporting, manuscript voice, "
                                "and paper-facing methods documentation."
                            ),
                        },
                        "blocking_work_units": [
                            {
                                "unit_id": "medical_prose_write_repair",
                                "lane": "write",
                            }
                        ],
                    }
                ],
            },
        }
    )

    assert action is not None
    assert action["source"] == "publication_eval.recommended_actions.readiness_blocker_repair"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert action["stage_typed_blocker_ref"] == closeout_ref
    assert action["target_surface"]["next_work_unit"]["unit_id"] == "medical_prose_write_repair"


def test_terminal_gate_blocker_does_not_reopen_same_eval_write_repair() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_record = (
        f"/workspace/studies/{study_id}/artifacts/controller/"
        "gate_clearing_batch/latest.json"
    )
    gate_report = (
        f"/workspace/runtime/quests/{study_id}/artifacts/reports/"
        "publishability_gate/2026-06-14T080316Z.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": study_id,
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "latest_record_path": gate_record,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "lacks_specific_blocker_object": False,
                    "current_actionability_status": "actionable",
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_eval_id": source_eval_id,
                "source_fingerprint": (
                    "sha256:3cb39d2a1499dec8d5fcb57a6cd4f535897db1c7382da9d3d290f329f8f4ba50"
                ),
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "gate_replay_refs": [
                    gate_report,
                    gate_record,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "ai_reviewer_recheck_required": True,
                "ai_reviewer_recheck_done": True,
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat_d2b4c700b31294ab17c225d4",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "blocked",
                    "stage_name": "run_gate_clearing_batch",
                    "outcome": "blocked:publication_gate_replay_blocked",
                    "remaining_blockers": [
                        "stale_submission_minimal_authority",
                        "medical_publication_surface_blocked",
                        "reviewer_first_concerns_unresolved",
                        "submission_hardening_incomplete",
                    ],
                    "next_forced_delta": {
                        "required_delta_kind": "publication_gate_replay_delta_or_typed_blocker",
                        "reason": "typed_blocker::publication_gate_replay_blocked",
                        "work_unit_id": "publication_gate_replay",
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            "gate_replay_report_ref": gate_report,
                        },
                        "owner_action": {
                            "next_owner": "publication_gate",
                            "action_type": "return_to_publishability_gate",
                            "work_unit_id": "publication_gate_replay",
                        },
                    },
                    "closeout_refs": [
                        gate_record,
                        gate_report,
                        f"studies/{study_id}/artifacts/supervision/consumer/"
                        "default_executor_execution/sat_d2b4c700b31294ab17c225d4.closeout.json",
                    ],
                }
            },
        }
    )

    assert action is None
