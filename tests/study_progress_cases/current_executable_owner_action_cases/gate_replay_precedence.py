from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_action_uses_gate_replay_after_ai_reviewer_record_consumed() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_current"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": "sha256:current-ai-reviewer-record",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/latest.json"],
            },
            "domain_transition": {
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                    "canonical_work_unit_identity": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                        "work_unit_fingerprint": "sha256:current-ai-reviewer-record",
                    },
                }
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "eval_id": source_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "gate_clearing_batch",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "target_surface_specificity": "explicit_owner_route_target",
                "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
                "owner_action": {
                    "next_owner": "gate_clearing_batch",
                    "work_unit_id": "ai_reviewer_record_gate_consumption",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "stage_native_current_owner_action": {
                "source": "stage_native_workspace_next_action",
                "next_owner": "write",
                "work_unit_id": "medical_publication_surface_blocked_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["work_unit_id"] == "ai_reviewer_record_gate_consumption"
    expected_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"ai_reviewer_record_gate_consumption::{source_eval_id}"
    )
    assert action["work_unit_fingerprint"] == expected_fingerprint
    assert action["action_fingerprint"] == expected_fingerprint
    assert action["source_eval_id"] == source_eval_id
    assert action["owner_route_currentness_basis"]["source_eval_id"] == source_eval_id
    assert action["owner_route_currentness_basis"]["work_unit_fingerprint"] == expected_fingerprint


def test_current_owner_action_uses_actionable_gate_followthrough_repair_work_unit() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T122549Z::sat_64c5fb484e8ee7b3971786ee"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": (
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair medical journal prose and reviewer-first reporting concerns.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/gate_clearing_batch/latest.json"
                ),
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "eval_id": source_eval_id,
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["allowed_actions"] == ["run_quality_repair_batch"]
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert action["source_eval_id"] == source_eval_id
    assert action["owner_route_currentness_basis"]["work_unit_id"] == "medical_prose_write_repair"


def test_current_owner_action_preserves_same_eval_repair_progress_gate_replay() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    gate_record_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/gate_clearing_batch/latest.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "publication-blockers::0915410f804b3697",
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": (
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
                "gate_replay_refs": [
                    (
                        "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/reports/publishability_gate/2026-06-14T075221Z.json"
                    ),
                    gate_record_ref,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting.",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": gate_record_ref,
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["repair_progress_precedence"]["source_work_unit_id"] == "medical_prose_write_repair"


def test_current_owner_action_gate_followthrough_supersedes_consumed_repair_progress_gate_replay() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    gate_record_ref = (
        f"/workspace/studies/{study_id}/artifacts/controller/"
        "gate_clearing_batch/latest.json"
    )
    fingerprint = "publication-blockers::0915410f804b3697"

    action = module.build_current_executable_owner_action(
        {
            "study_id": study_id,
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:6908b5fd",
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": (
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
                "gate_replay_refs": [
                    (
                        f"runtime/quests/{study_id}/artifacts/reports/"
                        "publishability_gate/2026-06-15T121635Z.json"
                    ),
                    gate_record_ref,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": fingerprint,
                    "current_work_unit_fingerprint": fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
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
                "latest_record_path": gate_record_ref,
            },
        }
    )

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == fingerprint


def test_current_owner_action_uses_newer_gate_replay_delta_over_stale_gate_followthrough() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    stale_followthrough_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T191558Z::sat_69f93a256b45113b077ab71a"
    )
    current_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": stale_followthrough_eval_id,
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": (
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["medical_publication_surface_blocked"],
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "eval_id": current_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "finalize",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "study_progress.next_forced_delta.owner_action"
    assert action["next_owner"] == "finalize"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    assert action["source_eval_id"] == current_eval_id


def test_terminal_gate_replay_closeout_does_not_reemit_same_gate_clearing_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    fingerprint = "current-ai-reviewer-gate-replay::003::publication_gate_replay::eval-current"

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "latest_terminal_stage_log": {
                "status": "completed",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "source_path": (
                    "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/stage_runs/sat-gate-replay/closeout.json"
                ),
                "next_forced_delta": {
                    "required_delta_kind": "paper_progress_delta_or_typed_blocker",
                    "work_unit_id": "publication_gate_replay",
                    "source_eval_id": "eval-current",
                    "owner_action": {
                        "next_owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "owner_receipt_required": True,
                    },
                },
            },
        }
    )

    assert action is None


def test_current_owner_action_prefers_gate_replay_after_ai_reviewer_recheck_done() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:current-ai-reviewer-record",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_required": True,
                "ai_reviewer_recheck_done": True,
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
                "gate_replay_done": True,
                "gate_replay_refs": [
                    "artifacts/supervision/requests/gate_clearing_batch/latest.json"
                ],
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["allowed_actions"] == ["run_gate_clearing_batch"]
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["required_delta_kind"] == "publication_gate_replay_delta_or_typed_blocker"


def test_repair_progress_gate_replay_supersedes_zero_selected_dispatch_stop_loss() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    gate_replay_fingerprint = (
        "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "state": {
                    "state_kind": "typed_blocker",
                    "blocker_type": (
                        "domain_owner_dispatch_zero_selected_after_materialized_current_request"
                    ),
                    "typed_blocker": {
                        "blocker_type": (
                            "domain_owner_dispatch_zero_selected_after_materialized_current_request"
                        ),
                        "reason": "anti_loop_budget_exhausted",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "analysis_claim_evidence_repair",
                        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                        "terminal_closeout_status": "blocked",
                        "terminal_closeout_outcome": "typed_blocker",
                    },
                },
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "source_fingerprint": gate_replay_fingerprint,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "ai_reviewer_recheck_required": True,
                "ai_reviewer_recheck_done": True,
                "ai_reviewer_recheck_request_ref": (
                    "artifacts/supervision/requests/ai_reviewer/latest.json"
                ),
                "gate_replay_done": True,
                "gate_replay_refs": [
                    "artifacts/supervision/requests/gate_clearing_batch/latest.json"
                ],
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["work_unit_fingerprint"] == gate_replay_fingerprint


def test_gate_followthrough_action_survives_zero_selected_materialized_dispatch_blocker() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )

    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "analysis-campaign",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
        "action_fingerprint": "publication-blockers::497d1260db522f01",
        "source_eval_id": (
            "publication-eval::002-dm-china-us-mortality-attribution::"
            "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
        ),
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
        },
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "analysis-campaign",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
        "target_surface_specificity": "gate_followthrough_actionable_publication_work_unit",
    }

    aligned = surfaces.current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "source_ref": (
                    "artifacts/supervision/consumer/default_executor_execution/"
                    "sat_9bbb471b55ad5ceda9d8495e.closeout.json"
                ),
            },
        },
    )

    assert aligned == action


def test_refresh_current_execution_surfaces_promotes_live_gate_followthrough_over_gate_replay_blocker() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
        },
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "write",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
        },
        "target_surface_specificity": "gate_followthrough_actionable_publication_work_unit",
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "current_executable_owner_action": action,
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        },
        status={"study_id": study_id},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "blocked_reason": "publication_gate_replay_blocked",
            "next_owner": "publication_gate",
            "latest_typed_default_executor_closeout": {
                "stage_attempt_id": "sat_d2b4c700b31294ab17c225d4",
                "status": "typed_blocker",
                "blocked_reason": "publication_gate_replay_blocked",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "action_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                "source_fingerprint": "truth-snapshot::eb10e8316639d4839970dc15",
                "idempotency_key": "idem_c84ba9b663a6b466165b652f",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                },
            },
        },
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006833-7bb5776c1cb9e961"
        },
    )

    assert result["current_executable_owner_action"] == action
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["action_type"] == "run_quality_repair_batch"
    assert result["current_work_unit"]["work_unit_id"] == "medical_prose_write_repair"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelope"]["owner"] == "write"


def test_publication_eval_repair_action_survives_zero_selected_materialized_dispatch_blocker() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )

    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source_surface": "publication_eval.recommended_actions.readiness_blocker_repair",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "quality_re_review",
        "work_unit_fingerprint": "publication-blockers::quality-re-review",
        "action_fingerprint": "publication-blockers::quality-re-review",
        "target_surface": {
            "ref_kind": "publication_eval_recommended_action",
            "route_target": "write",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "next_work_unit": {
                "unit_id": "quality_re_review",
                "lane": "write",
            },
        },
        "target_surface_specificity": "publication_eval_readiness_blocker_derived_repair",
    }

    aligned = surfaces.current_action_aligned_with_execution_envelope(
        action=action,
        envelope={
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "quality_re_review",
                "work_unit_fingerprint": "publication-blockers::quality-re-review",
            },
        },
    )

    assert aligned == action


def test_existing_projection_refresh_promotes_gate_followthrough_over_terminal_gate_blocker(
    monkeypatch,
    tmp_path,
) -> None:
    projection = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    fingerprint = "publication-blockers::497d1260db522f01"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dispatch_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "analysis-campaign",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
        },
    )
    monkeypatch.setattr(
        projection,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = projection._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": "analysis_claim_evidence_repair",
                "owner_action": {
                    "next_owner": "analysis-campaign",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                },
            },
            "gate_clearing_batch_followthrough": {
                "status": "executed",
                "gate_replay_status": "blocked",
                "gate_replay_blockers": ["claim_evidence_consistency_failed"],
                "latest_record_path": (
                    str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json")
                ),
                "source_eval_id": "eval-current",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_work_unit_fingerprint": fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence blockers.",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:gate-replay-old",
                "action_fingerprint": "sha256:gate-replay-old",
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:gate-replay-old",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-old",
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "running_provider_attempt": False,
                "blocked_reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                "next_owner": "one-person-lab",
                "latest_typed_default_executor_closeout": {
                    "stage_attempt_id": "sat_gate",
                    "status": "typed_blocker",
                    "blocked_reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-old",
                    "action_fingerprint": "sha256:gate-replay-old",
                    "typed_blocker": {
                        "blocker_type": "stage_packet_not_current_selected_dispatch",
                        "reason": "domain_owner_dispatch_zero_selected_after_materialized_current_request",
                        "owner": "one-person-lab",
                    },
                },
            },
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "analysis-campaign"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "analysis-campaign"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["transition_request_candidates"][0]["work_unit_id"] == "analysis_claim_evidence_repair"


def test_gate_followthrough_same_explicit_current_work_unit_still_routes_to_repair() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    fingerprint = "publication-blockers::0915410f804b3697"
    gate_record = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/gate_clearing_batch/latest.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::003::current",
                "latest_record_path": gate_record,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
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
                "blocking_issue_count": 4,
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:old-repair-progress-followup",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": [gate_record],
                "ai_reviewer_recheck_done": True,
            },
        }
    )

    assert action is not None
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == fingerprint


def test_same_eval_repair_delta_routes_to_gate_replay_not_repeat_write_repair() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    fingerprint = "sha256:repair-execution-evidence-current"
    gate_record = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
        "artifacts/controller/gate_clearing_batch/latest.json"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "latest_record_path": gate_record,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": fingerprint,
                    "current_work_unit_fingerprint": fingerprint,
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
                "source_fingerprint": fingerprint,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/quality_repair_batch/latest.json",
                "gate_replay_done": True,
                "gate_replay_refs": [
                    gate_record,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "ai_reviewer_recheck_required": True,
                "ai_reviewer_recheck_done": True,
                "ai_reviewer_recheck_request_ref": "artifacts/supervision/requests/ai_reviewer/latest.json",
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["repair_progress_precedence"]["source_work_unit_id"] == "medical_prose_write_repair"


def test_gate_followthrough_does_not_supersede_different_repair_progress_gate_ref() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::003::current",
                "latest_record_path": "artifacts/controller/gate_clearing_batch/current.json",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
            },
            "repair_progress_projection": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": "sha256:old-repair-progress-followup",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/previous.json"],
                "ai_reviewer_recheck_done": True,
            },
        }
    )

    assert action is not None
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["action_type"] == "run_gate_clearing_batch"
