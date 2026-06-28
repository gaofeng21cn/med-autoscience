from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def _identity_key(study_id: str, fingerprint: str) -> str:
    return f"provider-admission::{study_id}::{fingerprint}"


def _dispatch_refs(
    profile,
    *,
    study_id: str,
    action_type: str,
    packet_name: str,
    fingerprint: str,
) -> dict[str, object]:
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        f"immutable/{action_type}/{packet_name}.json"
    )
    identity_key = _identity_key(study_id, fingerprint)
    return {
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "route_identity_key": identity_key,
        "attempt_idempotency_key": identity_key,
        "refs": {
            "dispatch_path": str(
                profile.studies_root
                / study_id
                / "artifacts"
                / "supervision"
                / "consumer"
                / "default_executor_dispatches"
                / f"{action_type}.json"
            ),
            "stage_packet_path": str(profile.workspace_root / stage_packet_ref),
            "immutable_dispatch_path": str(profile.workspace_root / stage_packet_ref),
        },
    }


def test_domain_health_diagnostic_retains_owner_gate_transition_request_over_accepted_closeout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}"
        "::run_gate_clearing_batch"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dispatch_refs = _dispatch_refs(
        profile,
        study_id=study_id,
        action_type="run_gate_clearing_batch",
        packet_name="owner-gate-current",
        fingerprint=fingerprint,
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            **dispatch_refs,
        },
    )

    def fake_impl(**_: object) -> dict[str, object]:
        transition_request = {
            "kind": "StartProviderAttempt",
            "idempotency_key": "paper-policy-request:owner-gate-dm003",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        }
        candidate = {
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "transition_request_pending",
            "source": "opl_current_control_state.study_current_executable_owner_action",
            "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "stage_packet_ref": dispatch_refs["stage_packet_ref"],
            "stage_packet_refs": dispatch_refs["stage_packet_refs"],
            "route_identity_key": dispatch_refs["route_identity_key"],
            "attempt_idempotency_key": dispatch_refs["attempt_idempotency_key"],
            "currentness_basis": {
                "source": "paper_recovery_state.accepted_owner_gate_decision",
                "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "provider_admission_pending": False,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": True,
            "opl_domain_progress_transition_request": transition_request,
            "paper_progress_policy_result": {
                "opl_domain_progress_transition_request": transition_request,
            },
        }
        accepted_closeout = {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "stage_attempt_id": "sat_owner_gate_previous",
            "stage_id": "domain_owner/default-executor-dispatch",
            "status": "accepted_typed_closeout",
            "execution_status": "executed",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "owner_route_currentness_basis": {
                "source": "paper_recovery_state.accepted_owner_gate_decision",
                "truth_epoch": fingerprint,
                "runtime_health_epoch": fingerprint,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "typed_blocker": {
                "blocker_type": "stage_packet_not_current_selected_dispatch",
                "reason": "stage_packet_not_current_selected_dispatch",
            },
        }
        paper_recovery_state = {
            "surface_kind": "paper_recovery_state",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "phase": "admission_pending",
            "current_authority": {
                "owner": "one-person-lab",
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                },
            },
            "conditions": [
                {
                    "condition": "accepted_owner_gate_decision",
                    "decision": "admit_identity_bound_stage_packet",
                },
            ],
            "next_safe_action": {
                "kind": "admit_identity_bound_stage_packet",
                "owner": "one-person-lab",
                "provider_admission_allowed": True,
            },
            "evidence_refs": [
                "owner-gate-decision:owner-gate-current",
                dispatch_refs["stage_packet_ref"],
            ],
            "supervisor_decision": {
                "decision": "stop_with_stable_typed_blocker",
                "next_safe_action": {
                    "kind": "consume_opl_supervisor_decision_readback",
                    "provider_admission_allowed": False,
                },
            },
        }
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-19T17:45:00+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_opl_provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 0,
            "action_fingerprints": [],
            "current_execution_evidence": {
                "provider_admission_candidates": [],
                "transition_request_candidates": [],
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "typed_blocker",
                            "study_id": study_id,
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "state": {
                                "typed_blocker": {
                                    "blocker_type": "stale_closeout_consumed_pending",
                                    "reason": "stale_closeout_consumed_pending",
                                    "action_type": "run_gate_clearing_batch",
                                    "work_unit_id": work_unit_id,
                                    "work_unit_fingerprint": fingerprint,
                                }
                            },
                            "currentness_basis": {
                                "source": "paper_recovery_state.accepted_owner_gate_decision",
                                "truth_epoch": fingerprint,
                                "runtime_health_epoch": fingerprint,
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                        },
                        "paper_recovery_state": paper_recovery_state,
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "schema_version": 1,
                            "status": "ready",
                            "source": "paper_recovery_state.accepted_owner_gate_decision",
                            "authority": "paper_recovery_state.accepted_owner_gate_decision",
                            "next_owner": "gate_clearing_batch",
                            "owner": "gate_clearing_batch",
                            "action_type": "run_gate_clearing_batch",
                            "allowed_actions": ["run_gate_clearing_batch"],
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                            "owner_route_currentness_basis": {
                                "source": "paper_recovery_state.accepted_owner_gate_decision",
                                "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
                                "truth_epoch": fingerprint,
                                "runtime_health_epoch": fingerprint,
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                        },
                        "transition_request_candidates": [candidate],
                        "accepted_closeout_evidence": [accepted_closeout],
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": work_unit_id,
                        },
                    },
                },
            },
        }

    monkeypatch.setattr(module, "_run_domain_health_diagnostic_for_runtime_impl", fake_impl)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    assert result["managed_study_opl_provider_admission_candidates"] == []
    candidates = result["managed_study_opl_transition_request_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidates[0]["mas_owner_action_source"] == "paper_recovery_state.accepted_owner_gate_decision"
    assert candidates[0]["work_unit_id"] == work_unit_id
    assert candidates[0]["provider_admission_requires_opl_runtime_result"] is True
    assert result["current_execution_evidence"]["transition_request_candidates"] == candidates
    control = result["provider_admission_current_control_state"]
    assert control["transition_request_pending_count"] == 1
    assert control["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    assert (
        control["stage_route_arbiter_decisions"][0]["decision"]
        == "opl_transition_readback_required"
    )
    assert (
        control["stage_route_arbiter_decisions"][0]["mas_owner_action_source"]
        == "paper_recovery_state.accepted_owner_gate_decision"
    )


def test_domain_health_diagnostic_retains_owner_gate_transition_request_over_owner_receipt_current_work_unit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_refs = _dispatch_refs(
        profile,
        study_id=study_id,
        action_type=action_type,
        packet_name="accepted-owner-gate-receipt",
        fingerprint=fingerprint,
    )
    dump_json(
        profile.workspace_root / dispatch_refs["stage_packet_ref"],
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            **dispatch_refs,
        },
    )

    def fake_impl(**_: object) -> dict[str, object]:
        transition_request = {
            "surface_kind": "mas_domain_progress_transition_request",
            "recommended_transition_kind": "StartProviderAttempt",
            "idempotency_key": "paper-policy-request:owner-gate-dm003-receipt",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        }
        candidate = {
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "transition_request_pending",
            "source": "opl_current_control_state.study_current_executable_owner_action",
            "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(profile.workspace_root / dispatch_refs["stage_packet_ref"]),
            "stage_packet_ref": dispatch_refs["stage_packet_ref"],
            "stage_packet_refs": dispatch_refs["stage_packet_refs"],
            "route_identity_key": dispatch_refs["route_identity_key"],
            "attempt_idempotency_key": dispatch_refs["attempt_idempotency_key"],
            "currentness_basis": {
                "source": "paper_recovery_state.accepted_owner_gate_decision",
                "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
                "truth_epoch": "truth-event-000035",
                "runtime_health_epoch": "runtime-health-event-006980",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "provider_admission_pending": False,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": True,
            "opl_domain_progress_transition_request": transition_request,
            "paper_progress_policy_result": {
                "opl_domain_progress_transition_request": transition_request,
            },
        }
        paper_recovery_state = {
            "surface_kind": "paper_recovery_state",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "phase": "admission_pending",
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": action_type,
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "conditions": [
                {
                    "condition": "accepted_owner_gate_decision",
                    "decision": "admit_identity_bound_stage_packet",
                },
            ],
            "next_safe_action": {
                "kind": "admit_identity_bound_stage_packet",
                "owner": "write",
                "provider_admission_allowed": True,
            },
            "evidence_refs": [
                "owner-gate-decision:owner-gate-dm003-receipt",
                dispatch_refs["stage_packet_ref"],
            ],
            "supervisor_decision": {
                "decision": "opl_supervisor_decision_readback_required",
                "next_safe_action": {
                    "kind": "opl_supervisor_decision_readback_required",
                    "provider_admission_allowed": False,
                },
            },
        }
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-20T00:42:00+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_opl_provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "transition_request_pending_count": 0,
            "action_fingerprints": [],
            "current_execution_evidence": {
                "provider_admission_candidates": [],
                "transition_request_candidates": [],
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "study_root": str(study_root),
                        "study_intervention_events": [
                            {
                                "surface": "study_intervention_event",
                                "intent": "owner_gate_decision",
                                "event_id": "intervention-event-accepted-owner-gate",
                                "payload": {
                                    "decision": "admit_identity_bound_stage_packet",
                                    "provider_admission_allowed": True,
                                    "owner_gate_decision_ref": (
                                        "owner-gate-decision:owner-gate-dm003-receipt"
                                    ),
                                    "current_owner_identity": {
                                        "study_id": study_id,
                                        "action_type": action_type,
                                        "work_unit_id": work_unit_id,
                                        "work_unit_fingerprint": fingerprint,
                                        "blocker_type": (
                                            "no_selected_dispatch_for_authorized_stage_packet"
                                        ),
                                    },
                                    "stage_packet_ref": dispatch_refs["stage_packet_ref"],
                                    "stage_packet_refs": dispatch_refs["stage_packet_refs"],
                                },
                            }
                        ],
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "owner_receipt_recorded",
                            "study_id": study_id,
                            "owner": "write",
                            "action_type": action_type,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "currentness_basis": {
                                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                                "truth_epoch": "truth-event-000035",
                                "runtime_health_epoch": "runtime-health-event-006980",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                            "state": {
                                "state_kind": "owner_receipt_recorded",
                                "owner_receipt_ref": (
                                    "artifacts/controller/repair_execution_receipts/latest.json"
                                ),
                            },
                        },
                        "paper_recovery_state": paper_recovery_state,
                        "transition_request_candidates": [candidate],
                        "current_execution_envelope": {
                            "state_kind": "owner_receipt_recorded",
                            "owner": "write",
                            "next_work_unit": work_unit_id,
                        },
                    },
                },
            },
        }

    monkeypatch.setattr(module, "_run_domain_health_diagnostic_for_runtime_impl", fake_impl)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    assert result["managed_study_opl_provider_admission_candidates"] == []
    candidates = result["managed_study_opl_transition_request_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["work_unit_id"] == work_unit_id
    assert candidates[0]["mas_owner_action_source"] == "paper_recovery_state.accepted_owner_gate_decision"
    assert candidates[0]["provider_admission_requires_opl_runtime_result"] is True
    assert result["current_execution_evidence"]["transition_request_candidates"] == candidates
    control = result["provider_admission_current_control_state"]
    assert control["provider_admission_pending_count"] == 0
    assert control["transition_request_pending_count"] == 1
    assert control["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    assert (
        control["stage_route_arbiter_decisions"][0]["decision"]
        == "opl_transition_readback_required"
    )


def test_provider_admission_report_sync_keeps_owner_gate_transition_request_over_typed_blocker() -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    transition_request = {
        "surface_kind": "mas_domain_progress_transition_request",
        "recommended_transition_kind": "StartProviderAttempt",
        "idempotency_key": "paper-policy-request:owner-gate-dm003",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "status": "transition_request_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "stage_packet_ref": (
            f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
            "immutable/run_quality_repair_batch/33abc53e0c18295f5fa03738.json"
        ),
        "route_identity_key": f"paper-recovery::{study_id}::{action_type}::{fingerprint}",
        "attempt_idempotency_key": f"paper-recovery::{study_id}::{action_type}::{fingerprint}",
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_attempt_or_lease_required": False,
        "currentness_basis": {
            "source": "paper_recovery_state.accepted_owner_gate_decision",
            "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
        },
        "opl_domain_progress_transition_request": transition_request,
        "paper_progress_policy_result": {
            "opl_domain_progress_transition_request": transition_request,
        },
    }
    report = {
        "current_execution_evidence": {
            "progress_currentness": {
                study_id: {
                    "transition_request_candidates": [dict(candidate)],
                    "current_work_unit": {
                        "status": "typed_blocker",
                        "owner": "one-person-lab",
                        "action_type": action_type,
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "state": {
                            "typed_blocker": {
                                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                                "action_type": action_type,
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            }
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "owner": "one-person-lab",
                        "typed_blocker": {
                            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                            "action_type": action_type,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                }
            },
        },
        "managed_study_actions": [],
    }
    current_control_state = {
        "transition_request_candidates": [dict(candidate)],
        "provider_admission_candidates": [],
        "stage_route_arbiter_decisions": [
            {
                "decision": "current_typed_blocker_precedes_provider_admission",
                "evidence_status": "typed_blocker",
                "study_id": study_id,
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            }
        ],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state=current_control_state,
    )

    assert report["provider_admission_pending_count"] == 0
    assert report["transition_request_pending_count"] == 1
    assert report["managed_study_opl_provider_admission_candidates"] == []
    candidates = report["managed_study_opl_transition_request_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["mas_owner_action_source"] == "paper_recovery_state.accepted_owner_gate_decision"
    assert candidates[0]["provider_admission_requires_opl_runtime_result"] is True
