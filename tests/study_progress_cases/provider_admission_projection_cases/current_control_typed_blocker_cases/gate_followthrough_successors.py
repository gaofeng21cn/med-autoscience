from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study
from tests.study_progress_cases.provider_admission_projection_cases.current_control_typed_blocker import (
    _current_executable_quality_repair_payload,
    _quality_repair_consumed_typed_blocker_handoff,
    _write_ready_quality_repair_dispatch,
)


def test_existing_projection_refresh_promotes_progress_first_gate_followthrough_successor_over_consumed_gate_blocker(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "publication_gate",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting and manuscript voice.",
                },
                "latest_record_path": str(
                    study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                ),
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "blocked_reason": "publication_gate_replay_blocked",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "blocked_reason": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                    "source_ref": (
                        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                        "sat_d2b4c700b31294ab17c225d4.closeout.json"
                    ),
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "accepted_closeout_consumed_pending",
                        "typed_blocker": {
                            "blocker_type": "publication_gate_replay_blocked",
                            "owner": "publication_gate",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": gate_fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "publication_gate",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "publication_gate",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                    },
                },
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                },
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
                "blocked_reason": "publication_gate_replay_blocked",
            },
        },
        status={
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_liveness_audit": {},
            "runtime_health_snapshot": {},
        },
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
        attach_delivery_inspection_projection_fn=lambda payload, **_: payload,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["work_unit_fingerprint"] == repair_fingerprint
    assert result["paper_recovery_state"]["phase"] in {"owner_action_ready", "admission_pending"}


def test_existing_projection_refresh_promotes_selected_gate_successor_over_stale_selector_residue(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.existing_projection_refresh"
    )
    reconcile = importlib.import_module(
        "med_autoscience.controllers.study_progress.current_owner_action_projection_reconcile"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stale_fingerprint = "publication-blockers::0915410f804b3697"
    selected_fingerprint = "publication-blockers::2a234f3e48d8beb5"
    derived_fingerprint = "publication-blockers::5d99b7c4019bd601"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-20T05:46:03+00:00"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    payload = {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
            },
            "publication_eval": {
                "recommended_actions": [
                    {
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                            "summary": (
                                "Repair claim-evidence, story, figure, and results traceability blockers."
                            ),
                        },
                        "action_type": "route_back_same_line",
                        "priority": "now",
                        "work_unit_fingerprint": selected_fingerprint,
                        "blockers": [
                            "stale_submission_minimal_authority",
                            "medical_publication_surface_blocked",
                            "reviewer_first_concerns_unresolved",
                            "submission_hardening_incomplete",
                        ],
                        "specificity_targets": [
                            {
                                "target_kind": "table",
                                "target_id": "submission_minimal_authority",
                                "source_path": "/tmp/submission_manifest.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                            {
                                "target_kind": "claim",
                                "target_id": "review_ledger",
                                "source_path": "/tmp/review_ledger.json",
                                "blocking_reason": "reviewer_first_concerns_unresolved",
                            },
                            {
                                "target_kind": "figure",
                                "target_id": "figure_catalog",
                                "source_path": "/tmp/figure_catalog.json",
                                "blocking_reason": "stale_submission_minimal_authority",
                            },
                        ],
                    },
                ],
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": selected_fingerprint,
                    "current_work_unit_fingerprint": stale_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": False,
                    "fingerprint_or_source_signature_unchanged": False,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting and manuscript voice.",
                },
                "explicit_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                },
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": str(
                    study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                ),
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "active_workflow_id": None,
                "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": stale_fingerprint,
                    "action_fingerprint": stale_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "accepted_closeout_consumed_pending",
                        "typed_blocker": {
                            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                            "owner": "one-person-lab",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": stale_fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": stale_fingerprint,
                    },
                },
                "typed_blocker": {
                    "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": stale_fingerprint,
                    "action_fingerprint": stale_fingerprint,
                },
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
            },
        }
    result = module.refresh_existing_projection_current_owner_surfaces(
        payload=payload,
        status={
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_liveness_audit": {},
            "runtime_health_snapshot": {},
        },
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
        attach_delivery_inspection_projection_fn=lambda payload, **_: payload,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "analysis-campaign"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "analysis_claim_evidence_repair"
    assert action["work_unit_fingerprint"] == selected_fingerprint
    assert action["owner_route_currentness_basis"]["selected_publication_work_unit_id"] == (
        "analysis_claim_evidence_repair"
    )
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "analysis-campaign"
    assert result["current_work_unit"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert result["current_work_unit"]["work_unit_fingerprint"] == selected_fingerprint

    derived_action = {
        **action,
        "work_unit_fingerprint": derived_fingerprint,
        "action_fingerprint": derived_fingerprint,
        "owner_route_currentness_basis": {
            **action["owner_route_currentness_basis"],
            "work_unit_fingerprint": derived_fingerprint,
        },
    }
    assert reconcile.current_control_typed_blocker_successor_action(
        derived_action,
        typed_blocker=payload["opl_current_control_state_handoff"]["typed_blocker"],
        progress=payload,
    )


def test_existing_projection_refresh_promotes_gate_followthrough_successor_over_opl_authorization_residue(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:6423b231114cbec0e8d1ccb0b69adb117d0f2d8fa58d72751627c049a0dc10e4"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(
        study_root,
        study_id=study_id,
        fingerprint=repair_fingerprint,
    )

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Repair structured medical reporting and manuscript voice.",
                },
                "gate_replay_blockers": [
                    "stale_submission_minimal_authority",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": str(
                    study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                ),
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "active_workflow_id": None,
                "next_owner": "write",
                "blocked_reason": "opl_execution_authorization_required",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "blocked_reason": "opl_execution_authorization_required",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "terminal_closeout_typed_blocker",
                        "typed_blocker": {
                            "blocker_type": "executed",
                            "blocked_reason": "executed",
                            "blocker_id": "executed",
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": gate_fingerprint,
                            "action_fingerprint": gate_fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "source": "terminal_closeout_typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "executed",
                        "blocked_reason": "executed",
                        "blocker_id": "executed",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "action_fingerprint": gate_fingerprint,
                    },
                },
                "action_queue": [],
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
            },
        },
        status={
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_liveness_audit": {},
            "runtime_health_snapshot": {},
        },
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
        attach_delivery_inspection_projection_fn=lambda payload, **_: payload,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["work_unit_id"] == "medical_prose_write_repair"
    assert result["current_work_unit"]["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["transition_request_candidates"][0]["work_unit_id"] == "medical_prose_write_repair"


def test_existing_projection_refresh_keeps_paper_recovery_successor_over_stage_readiness_residue(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:6423b231114cbec0e8d1ccb0b69adb117d0f2d8fa58d72751627c049a0dc10e4"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(
        study_root,
        study_id=study_id,
        fingerprint=repair_fingerprint,
    )

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_owner_delta": {
                "stage_id": "publication_package_handoff",
                "desired_delta": "complete_medical_paper_readiness_surface",
                "source_kind": "typed_blocker",
                "source_ref": str(
                    study_root
                    / "artifacts"
                    / "stage_outputs"
                    / "08-publication_package_handoff"
                    / "receipts"
                    / "typed_blocker.json"
                ),
                "reason": "medical_paper_readiness_missing",
                "owner": "MedAutoScience",
                "hard_gate": {
                    "state": "domain_owner_answer_recorded",
                    "owner_answer_kind": "typed_blocker",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "supervisor_decision": {
                    "surface_kind": "paper_autonomy_supervisor_decision",
                    "decision": "materialize_recovery_action",
                    "identity_match": True,
                    "decision_id": "supervisor-decision::gate-followthrough-successor",
                    "evidence_refs": ["provider_admission_pending_count=0"],
                },
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": True,
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": str(
                            study_root
                            / "artifacts"
                            / "controller"
                            / "gate_clearing_batch"
                            / "latest.json"
                        ),
                    },
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "medical_prose_write_repair",
                    "selected_publication_work_unit_id": "medical_prose_write_repair",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "explicit_work_unit_fingerprint": repair_fingerprint,
                    "current_work_unit_fingerprint": repair_fingerprint,
                    "explicit_work_unit_fingerprint_matches_current": True,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "latest_record_path": str(
                    study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                ),
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "active_workflow_id": None,
                "next_owner": "write",
                "blocked_reason": "opl_execution_authorization_required",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "blocked_reason": "opl_execution_authorization_required",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "terminal_closeout_typed_blocker",
                        "typed_blocker": {
                            "blocker_type": "executed",
                            "blocked_reason": "executed",
                            "blocker_id": "executed",
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": gate_fingerprint,
                            "action_fingerprint": gate_fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "source": "terminal_closeout_typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "executed",
                        "blocked_reason": "executed",
                        "blocker_id": "executed",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                        "action_fingerprint": gate_fingerprint,
                    },
                },
                "action_queue": [],
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
            },
        },
        status={
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_liveness_audit": {},
            "runtime_health_snapshot": {},
        },
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
        attach_delivery_inspection_projection_fn=lambda payload, **_: payload,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["source_surface"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["work_unit_id"] == "medical_prose_write_repair"
    assert result["current_work_unit"]["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["transition_request_candidates"][0]["work_unit_id"] == "medical_prose_write_repair"
