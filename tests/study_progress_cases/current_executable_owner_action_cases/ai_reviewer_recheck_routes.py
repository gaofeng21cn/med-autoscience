from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_consumes_ai_reviewer_recheck_terminal_write_route() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "repair-source-current",
                "repair_execution_evidence_ref": (
                    "studies/003/artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": (
                    "studies/003/artifacts/controller/repair_execution_receipts/latest.json"
                ),
                "ai_reviewer_recheck_request_ref": (
                    "studies/003/artifacts/supervision/requests/ai_reviewer/latest.json"
                ),
                "gate_replay_refs": [
                    "runtime/quests/003/artifacts/reports/publishability_gate/current.json"
                ],
            },
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "status": "closed_with_domain_owner_refs",
                    "outcome": "owner_receipt",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "stage_attempt_id": "sat-current-ai-reviewer",
                    "source_path": (
                        "studies/003/default_executor_execution/"
                        "sat-current-ai-reviewer.closeout.json"
                    ),
                    "paper_stage_log": {
                        "progress_delta_classification": "deliverable_progress",
                        "changed_paper_surfaces": [
                            "studies/003/artifacts/publication_eval/ai_reviewer_responses/"
                            "20260612T123416Z_publication_eval_record.json"
                        ],
                    },
                    "next_forced_delta": {
                        "action_type": "run_quality_repair_batch",
                        "required_delta_kind": "same_line_write_repair_or_gate_replay_route",
                        "work_unit_id": "medical_prose_write_repair",
                        "target_surface": {
                            "ref_kind": "route_obligation",
                            "route_target": "write",
                            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                            "publication_eval_latest_ref": (
                                "studies/003/artifacts/publication_eval/ai_reviewer_responses/"
                                "20260612T123416Z_publication_eval_record.json"
                            ),
                        },
                        "owner_action": {
                            "action_type": "run_quality_repair_batch",
                            "next_owner": "write",
                            "work_unit_id": "medical_prose_write_repair",
                        },
                    },
                }
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["terminal_stage_next_forced_delta"] is True
