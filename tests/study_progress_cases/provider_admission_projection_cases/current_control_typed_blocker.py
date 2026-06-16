from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study

from ..provider_admission_projection import (
    _quality_repair_current_work_unit,
    _write_ready_quality_repair_dispatch,
)


def _quality_repair_consumed_typed_blocker_handoff(
    *,
    study_id: str,
    fingerprint: str,
    source: str = "accepted_closeout_consumed_pending",
) -> dict:
    return {
        "surface_kind": "opl_current_control_state_study_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "med-autoscience",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "typed_blocker",
                "source": source,
                "typed_blocker": {
                    "blocker_type": "provider_completion_is_not_domain_ready",
                    "owner": "med-autoscience",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "typed_blocker_ref": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_f8e1cfe49a3aa3cf95d0584d.closeout.json"
                    ),
                },
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "med-autoscience",
            "typed_blocker": {
                "blocker_type": "provider_completion_is_not_domain_ready",
                "owner": "med-autoscience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            },
            "source": source,
        },
        "provider_admission_candidates": [],
        "provider_admission_pending_count": 0,
        "action_queue": [],
    }


def _current_executable_quality_repair_payload(*, study_id: str, fingerprint: str) -> dict:
    return {
        "study_id": study_id,
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": "write",
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
        "current_work_unit": _quality_repair_current_work_unit(
            study_id=study_id,
            fingerprint=fingerprint,
            status="executable_owner_action",
        ),
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": "medical_prose_write_repair",
        },
    }


def test_provider_admission_projection_honors_handoff_consumed_typed_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload=_current_executable_quality_repair_payload(study_id=study_id, fingerprint=fingerprint),
        handoff=_quality_repair_consumed_typed_blocker_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }


def test_existing_projection_refresh_keeps_current_control_typed_blocker_over_stale_action(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            **_current_executable_quality_repair_payload(study_id=study_id, fingerprint=fingerprint),
            "quest_id": study_id,
            "opl_current_control_state_handoff": _quality_repair_consumed_typed_blocker_handoff(
                study_id=study_id,
                fingerprint=fingerprint,
                source="opl_current_control_state.current_work_unit",
            ),
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_pending": True,
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
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

    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["owner"] == "med-autoscience"
    assert result["current_work_unit"]["work_unit_fingerprint"] == fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert result["current_executable_owner_action"] is None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["owner_action_admission"]["admission_pending"] is False
    assert result["paper_recovery_state"]["phase"] == "domain_blocked"


def test_existing_projection_refresh_promotes_progress_first_gate_followthrough_successor_over_consumed_gate_blocker(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
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
                        "artifacts/supervision/consumer/default_executor_execution/"
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


def test_existing_projection_refresh_promotes_gate_followthrough_successor_over_opl_authorization_residue(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
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
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
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


def test_existing_projection_refresh_ignores_current_control_executable_residue_without_opl_readback(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
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
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": repair_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/latest.json"],
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    },
                },
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                    "owner_receipt_required": True,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
                "provider_admission_pending_count": 1,
                "provider_admission_candidates": [
                    {
                        "study_id": study_id,
                        "source": "opl_current_control_state.study_current_executable_owner_action",
                        "next_executable_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": repair_fingerprint,
                    }
                ],
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
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["current_work_unit"]["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelope"]["owner"] == "gate_clearing_batch"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []


def test_existing_projection_refresh_consumes_current_repair_progress_over_stale_gate_replay(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    old_repair_followup_fingerprint = repair_fingerprint
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
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": old_repair_followup_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": str(
                    study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
                ),
                "owner_receipt_ref": str(
                    study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
                ),
                "gate_replay_refs": [
                    str(study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json")
                ],
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
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
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "next_owner": "publication_gate",
                "blocked_reason": "publication_gate_replay_blocked",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "provider_admission_pending": False,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
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
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["work_unit_fingerprint"] == old_repair_followup_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []


def test_existing_projection_refresh_consumes_current_repair_successor_over_refs_only_handoff(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:6908b5fd4189779bc39fa7f869aeedd978159a73644c90b6ec2cf90b39d7a643"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    paper_recovery_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "action_fingerprint": repair_fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "source_ref": str(
            study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
        ),
        "paper_recovery_successor": {
            "phase": "owner_action_ready",
            "source_next_safe_action_kind": "materialize_successor_owner_action",
            "provider_admission_allowed": True,
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        },
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }
    paper_recovery_work_unit = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "action_fingerprint": repair_fingerprint,
        "state": {
            "state_kind": "executable_owner_action",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "provider_admission_pending": False,
        },
    }

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "publication_eval": {"eval_id": source_eval_id, "study_id": study_id, "quest_id": study_id},
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": str(
                    study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
                ),
                "owner_receipt_ref": str(
                    study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
                ),
                "gate_replay_refs": [
                    str(
                        profile.runtime_root
                        / study_id
                        / "artifacts"
                        / "reports"
                        / "publishability_gate"
                        / "2026-06-15T121635Z.json"
                    ),
                    str(study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"),
                    str(study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"),
                ],
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
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
                        "work_unit_fingerprint": repair_fingerprint,
                        "source_eval_id": source_eval_id,
                        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_ref": str(
                            study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                        ),
                    },
                },
                "supervisor_decision": {
                    "decision": "materialize_recovery_action",
                    "next_owner": "write",
                },
            },
            "current_work_unit": paper_recovery_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "current_executable_owner_action": paper_recovery_action,
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "authority": "observability_only",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "next_owner": "write",
                "blocked_reason": "opl_execution_authorization_required",
                "current_work_unit": paper_recovery_work_unit,
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
                "current_executable_owner_action": paper_recovery_action,
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
        publication_eval_payload={"eval_id": source_eval_id, "study_id": study_id, "quest_id": study_id},
        attach_delivery_inspection_projection_fn=lambda payload, **_: payload,
    )

    action = result["current_executable_owner_action"]
    assert action["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert action["next_owner"] == "gate_clearing_batch"
    assert action["action_type"] == "run_gate_clearing_batch"
    assert action["work_unit_id"] == "publication_gate_replay"
    assert action["work_unit_fingerprint"] == gate_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    recovery_next = result["paper_recovery_state"]["next_safe_action"]
    assert recovery_next["owner"] == "gate_clearing_batch"
    assert recovery_next["kind"] in {
        "consume_owner_receipt",
        "materialize_mas_transition_request_or_owner_callable",
    }
    assert recovery_next.get("successor_owner_action", {}).get("work_unit_id") != (
        "medical_prose_write_repair"
    )


def test_existing_projection_refresh_promotes_domain_transition_after_consumed_provider_completion_blocker(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)

    result = module.refresh_existing_projection_current_owner_surfaces(
        payload={
            **_current_executable_quality_repair_payload(study_id=study_id, fingerprint=fingerprint),
            "quest_id": study_id,
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "opl_current_control_state_handoff": _quality_repair_consumed_typed_blocker_handoff(
                study_id=study_id,
                fingerprint=fingerprint,
            ),
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
    assert action["source"] == "domain_transition"
    assert action["next_owner"] == "ai_reviewer"
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "ai_reviewer"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []


def test_provider_admission_projection_ignores_unconsumed_handoff_typed_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload=_current_executable_quality_repair_payload(study_id=study_id, fingerprint=fingerprint),
        handoff=_quality_repair_consumed_typed_blocker_handoff(
            study_id=study_id,
            fingerprint=fingerprint,
            source="current_work_unit.typed_blocker",
        ),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == "medical_prose_write_repair"
    assert candidate["work_unit_fingerprint"] == fingerprint


def test_existing_projection_refresh_honors_current_control_typed_blocker(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    fingerprint = "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"
    stale_fingerprint = "publication-blockers::497d1260db522f01"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(
        study_root,
        study_id=study_id,
        fingerprint=stale_fingerprint,
    )
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"status": "stale"}],
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "analysis-campaign",
                "next_work_unit": "analysis_claim_evidence_repair",
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "accepted_closeout_consumed_pending",
                        "typed_blocker": {
                            "blocker_type": "publication_gate_replay_blocked",
                            "owner": "gate_clearing_batch",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "gate_clearing_batch",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                },
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
                "blocked_reason": "publication_gate_replay_blocked",
            },
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["current_work_unit"]["work_unit_fingerprint"] == fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []


def test_current_execution_refresh_keeps_handoff_current_typed_blocker_over_gate_followthrough_residue() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    gate_fingerprint = "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"
    stale_fingerprint = "publication-blockers::497d1260db522f01"

    result = module.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "queued",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "source_eval_id": (
                    "publication-eval::002-dm-china-us-mortality-attribution::"
                    "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
                ),
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": stale_fingerprint,
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "selected_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                    "explicit_work_unit_fingerprint": "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917",
                    "current_work_unit_fingerprint": stale_fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
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
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": gate_fingerprint,
                "action_fingerprint": gate_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": {
                        "blocker_type": "publication_gate_replay_blocked",
                        "owner": "gate_clearing_batch",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": gate_fingerprint,
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "gate_clearing_batch",
                "source": "accepted_closeout_consumed_pending",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                },
            },
        },
        runtime_health_snapshot={},
    )

    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["owner"] == "gate_clearing_batch"
    assert result["current_work_unit"]["action_type"] == "run_gate_clearing_batch"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["current_work_unit"]["work_unit_fingerprint"] == gate_fingerprint
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
