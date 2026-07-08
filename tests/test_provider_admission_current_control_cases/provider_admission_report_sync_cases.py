from __future__ import annotations

from tests.test_provider_admission_current_control_cases.provider_admission_report_sync_cases_cases.transition_runtime_readback_cases import (
    test_provider_admission_report_sync_consumes_transition_request_after_terminal_closeout,
    test_provider_admission_report_sync_preserves_non_advancing_transition_request,
    test_provider_admission_report_sync_clears_pending_when_managed_action_is_running,
    test_provider_admission_current_control_runtime_health_live_attempt_suppresses_pending,
    test_provider_admission_current_control_runtime_health_live_attempt_suppresses_transition_request,
    test_provider_admission_report_sync_clears_domain_blocked_recovery_pending_state,
    test_provider_admission_report_refreshes_scanned_typed_blocker_without_candidates,
    test_provider_admission_report_sync_lifts_study_level_provider_readback_to_top_level,
)
import importlib
import json
from pathlib import Path

from tests.provider_admission_current_control_helpers import (
    opl_transition_readback as _opl_transition_readback,
    provider_candidate as _provider_candidate,
    provider_candidate_with_opl_readback as _provider_candidate_with_opl_readback,
)


def test_provider_admission_report_suppresses_candidate_blocked_by_report_paper_recovery_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
    }

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                        },
                    },
                },
            },
            "paper_recovery_states": {
                study_id: {
                    "surface_kind": "paper_recovery_state",
                    "phase": "owner_action_ready",
                    "current_authority": {
                        "owner": "write",
                        "obligation": {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "next_safe_action": {
                        "kind": "run_mas_owner_callable",
                        "owner": "write",
                        "provider_admission_allowed": False,
                    },
                },
            },
        },
        apply=False,
        generated_at="2026-06-14T12:55:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "paper_recovery_state_blocks_provider_admission": 1,
    }
    study = result["studies"][0]
    assert study["paper_recovery_state"]["phase"] == "owner_action_ready"


def test_provider_admission_report_retains_matching_current_action_candidate_over_stale_scan_blocker(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate_with_opl_readback(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "quest_id": study_id,
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "next_owner": "ai_reviewer",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": candidate["work_unit_id"],
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "owner": "ai_reviewer",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": candidate["work_unit_id"],
                            "work_unit_fingerprint": action_fingerprint,
                            "currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-event-current",
                                "work_unit_id": candidate["work_unit_id"],
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                },
            },
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "decision": "blocked",
                    "reason": "medical_paper_readiness_missing",
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "typed_blocker",
                        "owner": "MedAutoScience",
                        "action_type": "complete_medical_paper_readiness_surface",
                        "work_unit_id": "complete_medical_paper_readiness_surface",
                        "state": {
                            "state_kind": "typed_blocker",
                            "typed_blocker": {
                                "blocker_type": "medical_paper_readiness_missing",
                                "owner": "MedAutoScience",
                            },
                        },
                    },
                    "current_executable_owner_action": None,
                    "running_provider_attempt": False,
                }
            ],
        },
        apply=False,
        generated_at="2026-06-12T07:30:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    retained = result["provider_admission_candidates"][0]
    assert retained["study_id"] == study_id
    assert retained["action_type"] == "return_to_ai_reviewer_workflow"
    assert retained["work_unit_id"] == candidate["work_unit_id"]
    assert retained["work_unit_fingerprint"] == action_fingerprint
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }


def test_provider_admission_report_sync_updates_managed_action_candidate_surface(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    current_candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint="sha256:current-ai-reviewer",
    )
    stale_candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint="sha256:stale-gate-replay",
        ),
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [stale_candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [stale_candidate],
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "provider_admission_candidates": [stale_candidate],
                    "provider_admission_state": {
                        "status": "pending",
                        "candidate_count": 1,
                    },
                }
            ],
        },
        "managed_study_actions": [
            {
                "study_id": study_id,
                "provider_admission_candidates": [stale_candidate],
                "provider_admission_state": {
                    "status": "pending",
                    "candidate_count": 1,
                },
            }
        ],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [current_candidate],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == [current_candidate]
    assert report["current_execution_evidence"]["provider_admission_candidates"] == [current_candidate]
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == [current_candidate]
    assert action["provider_admission_state"]["candidate_count"] == 1
    assert action["provider_admission_state"]["running_provider_attempt"] is False
    assert action["provider_admission_state"]["status"] == "pending"
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == [current_candidate]
    assert evidence_action["provider_admission_state"]["candidate_count"] == 1


def test_provider_admission_report_sync_clears_stale_managed_action_pending_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stale_candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint="sha256:stale-ai-reviewer",
    )
    stale_action = {
        "study_id": study_id,
        "provider_admission_candidates": [stale_candidate],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [stale_candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [stale_candidate],
            "managed_study_actions": [stale_action],
        },
        "managed_study_actions": [stale_action],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action


def test_provider_admission_report_sync_consumes_terminal_readback_in_managed_action(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    fingerprint = "sha256:c82b52d55725eb89ed014ff1f805c07d6a6c2ee25a47c5e5713367a54fd88917"
    route_key = "paper-policy-request:4ad0ec722ffd3cb666e615ac"
    stale_candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint=fingerprint,
        ),
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "provider_admission_pending": True,
        "opl_domain_progress_transition_runtime_live_readback": _opl_transition_readback(
            study_id,
            action_fingerprint=fingerprint,
            work_unit_id=work_unit_id,
            route_identity_key=route_key,
            attempt_idempotency_key=route_key,
            request_idempotency_key=route_key,
        ),
    }
    stale_action = {
        "study_id": study_id,
        "quest_id": study_id,
        "provider_admission_candidates": [dict(stale_candidate)],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
        },
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "opl_current_control_state.provider_admission_candidates",
            "study_id": study_id,
            "quest_id": study_id,
            "next_owner": "gate_clearing_batch",
            "owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
            "provider_admission_pending": True,
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "opl_current_control_state.provider_admission_candidates",
                "provider_admission_pending": True,
                "transition_request_pending": False,
                "provider_attempt_or_lease_required": True,
            },
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "admission_pending",
            "next_safe_action": {
                "kind": "consume_opl_provider_admission_readback",
                "provider_admission_allowed": True,
            },
        },
    }
    terminal_readback = {
        "surface_kind": "opl_current_control_provider_admission_terminal_consumed_readback",
        "status": "provider_admission_terminal_consumed",
        "reason": "terminal_stage_attempt_consumed_same_transition_identity",
        "terminal_stage_attempt_id": "sat_d00368adb115dbeba62a7e41",
        "terminal_stage_attempt_status": "completed",
        "terminal_provider_status": "completed",
        "closeout_refs": [
            "runtime/artifacts/opl_family_domain_handler/dispatch_receipts/1b3ff330ad0e62476a78.json",
            f"mas://current-work-unit/{study_id}/{work_unit_id}/stage-packet",
            "temporal://attempt/sat_d00368adb115dbeba62a7e41",
        ],
        "currentness_identity": {
            "task_id": "frt_f3103ddf54ddde2fd07ca747",
            "stage_attempt_id": "sat_d00368adb115dbeba62a7e41",
            "study_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
        },
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [dict(stale_candidate)],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [dict(stale_candidate)],
            "managed_study_actions": [dict(stale_action)],
        },
        "managed_study_actions": [dict(stale_action)],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [],
            "transition_request_candidates": [],
            "studies": [
                {
                    "study_id": study_id,
                    "provider_admission_pending_count": 0,
                    "provider_admission_candidates": [],
                    "transition_request_pending_count": 0,
                    "transition_request_candidates": [],
                    "provider_admission_terminal_closeout_consumed": dict(terminal_readback),
                }
            ],
            "latest_provider_admission_terminal_consumed_readback": dict(terminal_readback),
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == []
    assert action["provider_admission_pending_count"] == 0
    assert "provider_admission_state" not in action
    assert "current_executable_owner_action" not in action
    assert action["provider_admission_terminal_closeout_consumed"] == terminal_readback
    assert action["current_work_unit"]["state"]["provider_admission_pending"] is False
    assert action["current_work_unit"]["state"]["provider_admission_terminal_consumed"] is True
    assert action["paper_recovery_state"]["phase"] == "terminal_closeout_ready"
    assert action["paper_recovery_state"]["next_safe_action"]["kind"] == "consume_terminal_closeout"
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["paper_recovery_state"]["phase"] == "terminal_closeout_ready"


def test_provider_admission_report_sync_keeps_transition_request_out_of_managed_admission_surface(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    transition_request = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint=fingerprint,
        ),
        "status": "transition_request_pending",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "provider_attempt_or_lease_required": False,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "same_tick_materialized_provider_admission": True,
        "same_tick_materialization_source": "dry_run_preview",
        "dispatch_status": "transition_request_pending",
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
        },
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
            "recommended_transition_kind": "StartProviderAttempt",
            "idempotency_key": "paper-policy-request:1a379264039c75d0e9cfd8f5",
            "aggregate_identity": {
                "aggregate_kind": "study_work_unit",
                "aggregate_id": f"{study_id}::medical_prose_write_repair",
                "study_id": study_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            },
        },
    }
    stale_action = {
        "study_id": study_id,
        "provider_admission_candidates": [dict(transition_request)],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
            "running_provider_attempt": False,
        },
        "current_work_unit": {
            "status": "owner_receipt_recorded",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [dict(transition_request)],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "progress_currentness": {
                study_id: {
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [],
                    "transition_request_candidates": [],
                    "current_work_unit": {
                        "status": "owner_receipt_recorded",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                },
            },
            "provider_admission_candidates": [dict(transition_request)],
            "managed_study_actions": [dict(stale_action)],
        },
        "managed_study_actions": [dict(stale_action)],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [dict(transition_request)],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    assert report["transition_request_pending_count"] == 0
    assert report["managed_study_opl_transition_request_candidates"] == []
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action
