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


def test_existing_projection_refresh_honors_current_control_executable_handoff_over_stale_gate_replay(
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
    assert result["current_execution_envelope"]["owner"] == "write"
    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == "medical_prose_write_repair"


def test_existing_projection_refresh_promotes_paper_recovery_successor_after_consumed_gate_replay(
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.existing_projection_refresh"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    old_repair_followup_fingerprint = "sha256:old-repair-progress-followup"
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
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "write"
    assert action["action_type"] == "run_quality_repair_batch"
    assert action["work_unit_id"] == "medical_prose_write_repair"
    assert action["work_unit_fingerprint"] == repair_fingerprint
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["owner"] == "write"
    assert result["current_work_unit"]["work_unit_id"] == "medical_prose_write_repair"
    assert result["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == "medical_prose_write_repair"


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
