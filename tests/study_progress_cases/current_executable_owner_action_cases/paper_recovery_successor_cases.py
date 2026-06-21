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


def test_paper_recovery_successor_precedes_stale_repair_progress_gate_replay_action() -> None:
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
            "publication_eval": {"eval_id": source_eval_id},
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
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": (
                    "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
                ),
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": (
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
                "gate_replay_refs": [
                    "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/reports/publishability_gate/2026-06-14T174928Z.json",
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
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
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
                        "source_ref": gate_record_ref,
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "next_owner": "write",
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"


def test_paper_recovery_successor_survives_stale_repair_progress_during_fixed_point() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260616T042403Z::sat_07183cd27fc9f913b03dfcee"
    )
    successor_fingerprint = "publication-blockers::0915410f804b3697"
    stale_repair_fingerprint = "sha256:9a9e92dd13d055c1c869e7d1da0234ba88ea723e9bfe24c00075496011c19e0b"

    action = module.build_current_executable_owner_action(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "publication_eval": {"eval_id": source_eval_id},
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": successor_fingerprint,
                "action_fingerprint": successor_fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                },
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": successor_fingerprint,
                "action_fingerprint": successor_fingerprint,
                "source_fingerprint": stale_repair_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": (
                    "artifacts/controller/repair_execution_receipts/latest.json"
                ),
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
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
                "work_unit_fingerprint": successor_fingerprint,
                "work_unit_currentness": {
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": successor_fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "gate_replay_status": "blocked",
                "latest_record_path": (
                    "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/gate_clearing_batch/latest.json"
                ),
            },
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
                        "work_unit_fingerprint": successor_fingerprint,
                        "source_eval_id": source_eval_id,
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
                    "identity_match": True,
                },
            },
        }
    )

    assert action is not None
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == successor_fingerprint


def test_paper_recovery_refresh_materializes_dm002_anti_loop_successor() -> None:
    refresh_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "paper_recovery_execution_refresh"
    )
    action_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    provider_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    payload_sync = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.payload_sync"
    )
    recovery_state = importlib.import_module("med_autoscience.controllers.paper_recovery_state")
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    route_fingerprint = "route-currentness::002-dm-china-us-mortality-attribution::c7c03e191980c1cb"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
    )

    result = refresh_module.normalize_paper_recovery_execution_projection(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-event-007038"},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "status": "progress_delta_observed",
                "paper_delta_observed": True,
                "progress_delta_candidate": True,
                "accepted_owner_receipt": True,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "action_fingerprint": "publication-blockers::497d1260db522f01",
                "source_eval_id": source_eval_id,
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "publication_supervision",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
                "action_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": f"domain-transition::route_back_same_line::{work_unit_id}",
                    },
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {"owner": "write", "authority": "med-autoscience"},
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "action_type": "run_gate_clearing_batch",
                        "owner": "write",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": route_fingerprint,
                        "action_fingerprint": route_fingerprint,
                        "source_surface": "study_progress.next_forced_delta.owner_action",
                        "source_eval_id": source_eval_id,
                        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                        "owner_route_currentness_basis": {
                            "source": "study_progress.next_forced_delta.owner_action",
                            "source_eval_id": source_eval_id,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": route_fingerprint,
                            "action_fingerprint": route_fingerprint,
                        },
                    },
                },
            },
        },
        status={"study_id": study_id, "quest_id": study_id},
        handoff={},
        runtime_health_snapshot={"runtime_health_epoch": "runtime-health-event-007038"},
        study_root=Path("/workspace/studies") / study_id,
        build_current_executable_owner_action=action_module.build_current_executable_owner_action,
        refresh_current_execution_surfaces=surfaces.refresh_current_execution_surfaces,
        provider_admission_projection_fields=provider_projection.provider_admission_projection_fields,
        sync_progress_first_owner_action_admission=payload_sync.sync_progress_first_owner_action_admission,
        build_paper_recovery_state=recovery_state.build_paper_recovery_state,
    )

    assert result["paper_recovery_state"]["phase"] == "owner_action_ready"
    assert result["current_executable_owner_action"]["source"] == (
        "paper_recovery_state.next_safe_action.successor_owner_action"
    )
    assert result["current_executable_owner_action"]["next_owner"] == "write"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["action_type"] == "run_gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == work_unit_id
    assert result["current_work_unit"]["work_unit_fingerprint"] == route_fingerprint


def test_owner_gate_blocker_for_successor_work_unit_rebuilds_stale_recovery_successor() -> None:
    refresh_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "paper_recovery_execution_refresh"
    )
    action_module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_executable_owner_action"
    )
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    provider_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    payload_sync = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.payload_sync"
    )
    recovery_state = importlib.import_module("med_autoscience.controllers.paper_recovery_state")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    work_unit_fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"

    result = refresh_module.normalize_paper_recovery_execution_projection(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "runtime_health_snapshot": {"runtime_health_epoch": "runtime-health-event-006980"},
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "currentness_basis": {
                    "source": "opl_current_control_state.provider_admission_candidates",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "route_identity_key": "paper-policy-request:5c447e99601513e78e08ca8f",
                    "attempt_idempotency_key": "paper-policy-request:5c447e99601513e78e08ca8f",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "opl_current_control_state.provider_admission_candidates",
                    "provider_admission_pending": True,
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "opl_current_control_state.provider_admission_candidates",
                "source_surface": "opl_current_control_state.provider_admission_candidates",
                "next_owner": "write",
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "allowed_actions": ["request_opl_stage_attempt"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "action_fingerprint": work_unit_fingerprint,
                "provider_admission_pending": True,
                "provider_attempt_or_lease_required": True,
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "source": "opl_current_control_state_action_queue",
                    "study_id": study_id,
                    "action_type": "request_opl_stage_attempt",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": work_unit_fingerprint,
                    "action_fingerprint": work_unit_fingerprint,
                }
            ],
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "owner": "write",
                    "authority": "med-autoscience",
                    "obligation": {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    },
                },
                "conditions": [
                    {
                        "condition": "consumed_owner_receipt_domain_transition_successor",
                        "source_condition": "repair_progress_followup_owner_receipt_recorded",
                    }
                ],
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": False,
                    "successor_owner_action": {
                        "action_type": "request_opl_stage_attempt",
                        "owner": "write",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": work_unit_fingerprint,
                        "domain_transition_decision_type": "route_back_same_line",
                        "domain_transition_controller_action": "request_opl_stage_attempt",
                        "source_surface": "domain_transition",
                    },
                },
            },
            "study_intervention_events": [
                {
                    "surface": "study_intervention_event",
                    "intent": "owner_gate_decision",
                    "event_id": "intervention-event-000002-cd6e1991896a2d4d",
                    "recorded_at": "2026-06-21T01:58:30+00:00",
                    "payload": {
                        "decision": "deny_and_stable_typed_blocker",
                        "provider_admission_allowed": False,
                        "human_gate_ref": "human_gate:owner-gate-decision:d6d895635654560a85573c04",
                        "owner_gate_decision_ref": "owner-gate-decision:d6d895635654560a85573c04",
                        "stable_typed_blocker_ref": (
                            "stable_typed_blocker:owner-gate-decision:"
                            "d6d895635654560a85573c04"
                        ),
                        "current_owner_identity": {
                            "study_id": study_id,
                            "action_type": "request_opl_stage_attempt",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "blocker_type": "runtime_recovery_retry_budget_exhausted",
                        },
                    },
                }
            ],
        },
        status={"study_id": study_id, "quest_id": study_id},
        handoff={},
        runtime_health_snapshot={"runtime_health_epoch": "runtime-health-event-006980"},
        study_root=Path("/workspace/studies") / study_id,
        build_current_executable_owner_action=action_module.build_current_executable_owner_action,
        refresh_current_execution_surfaces=surfaces.refresh_current_execution_surfaces,
        provider_admission_projection_fields=provider_projection.provider_admission_projection_fields,
        sync_progress_first_owner_action_admission=payload_sync.sync_progress_first_owner_action_admission,
        build_paper_recovery_state=recovery_state.build_paper_recovery_state,
    )

    recovery = result["paper_recovery_state"]
    assert recovery["phase"] == "domain_blocked"
    assert recovery["conditions"] == [
        {
            "condition": "accepted_owner_gate_decision",
            "decision": "deny_and_stable_typed_blocker",
        }
    ]
    assert recovery["next_safe_action"]["kind"] == "honor_stable_typed_blocker"
    assert recovery["next_safe_action"]["provider_admission_allowed"] is False
    assert "stable_typed_blocker:owner-gate-decision:d6d895635654560a85573c04" in recovery[
        "evidence_refs"
    ]
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
