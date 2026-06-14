from __future__ import annotations

import importlib

from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
    _typed_blocker_work_unit,
)


def test_typed_blocker_owns_recovery_even_when_residual_action_exists() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_work_unit": _typed_blocker_work_unit(),
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"action_type": "run_quality_repair_batch"}],
        }
    )

    assert state["surface_kind"] == "paper_recovery_state"
    assert state["phase"] == "domain_blocked"
    assert state["recovery_obligation_id"] == (
        "paper-recovery::002-dm-cvd-mortality-risk::run_gate_clearing_batch::"
        "publication_gate_replay::stage_packet_not_current_selected_dispatch"
    )
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["suppressed_surfaces"] == ["current_executable_owner_action", "provider_admission_candidates"]


def test_matching_owner_gate_event_supersedes_current_typed_blocker() -> None:
    fingerprint = "publication-blockers::497d1260db522f01"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="002-dm-china-us-mortality-attribution",
                action_type="run_quality_repair_batch",
                work_unit_id="analysis_claim_evidence_repair",
                blocker_type="stage_packet_not_current_selected_dispatch",
            )
            | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "study_intervention_events": [
                {
                    "surface": "study_intervention_event",
                    "intent": "owner_gate_decision",
                    "event_id": "intervention-event-000001-13263a6ca77a1066",
                    "recorded_at": "2026-06-14T02:27:19+00:00",
                    "payload": {
                        "decision": "route_back_to_mas_packet_materialization_bug",
                        "current_owner_identity": {
                            "study_id": "002-dm-china-us-mortality-attribution",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "analysis_claim_evidence_repair",
                            "work_unit_fingerprint": fingerprint,
                            "blocker_type": "stage_packet_not_current_selected_dispatch",
                        },
                        "human_gate_ref": "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
                        "owner_gate_decision_ref": "owner-gate-decision:c7027de42ca336cfe0782428",
                        "route_back_evidence_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
                        "provider_admission_allowed": False,
                    },
                }
            ],
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"action_type": "run_quality_repair_batch"}],
        }
    )

    assert state["phase"] == "human_gate"
    assert state["conditions"] == [
        {
            "condition": "accepted_owner_gate_decision",
            "decision": "route_back_to_mas_packet_materialization_bug",
        }
    ]
    assert state["current_authority"]["owner"] == "MedAutoScience"
    assert state["next_safe_action"]["kind"] == "route_back_to_owner_or_repair_materialization"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [
        "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
        "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
        "owner-gate-decision:c7027de42ca336cfe0782428",
    ]


def test_observe_only_provider_admission_is_classified_as_blocked_with_reason() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
        },
        diagnostic_report={
            "action_class": "observe_only",
            "will_start_llm": False,
            "codex_dispatch_count": 0,
            "provider_admission_pending_count": 1,
        },
    )

    assert state["phase"] == "admission_blocked"
    assert state["conditions"] == [
        {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "dhd_report_observe_only",
        }
    ]
    assert state["next_safe_action"]["kind"] == "run_admission_apply_or_report_operator_gate"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_runtime_retry_exhausted_provider_admission_fails_closed() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                owner="gate_clearing_batch",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                fingerprint="sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
                }
            ],
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "retry_budget_remaining": 0,
            },
        }
    )

    assert state["phase"] == "admission_blocked"
    assert state["conditions"] == [
        {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "runtime_recovery_retry_budget_exhausted",
        }
    ]
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_projection_contradiction_fails_closed() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["current_authority"]["owner"] == "MedAutoScience"
    assert state["next_safe_action"]["kind"] == "repair_projection_before_admission"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_matching_provider_admission_supersedes_stale_parked_projection() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "status": "provider_admission_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "action_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
        }
    )

    assert state["phase"] == "admission_pending"
    assert state["conditions"] == [{"condition": "provider_admission_pending"}]
    assert state["next_safe_action"]["kind"] == "admit_provider_attempt"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["current_authority"]["owner"] == "write"


def test_current_work_unit_provider_admission_pending_supersedes_stale_parked_projection() -> None:
    current_work_unit = _executable_work_unit(
        owner="gate_clearing_batch",
        action_type="run_gate_clearing_batch",
        work_unit_id="publication_gate_replay",
        fingerprint="sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
    )
    current_work_unit["state"] = {
        "state_kind": "executable_owner_action",
        "provider_admission_pending": True,
        "pending_provider_admission_evidence": {
            "running_provider_attempt": False,
            "provider_attempt_or_lease_required": False,
        },
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        }
    )

    assert state["phase"] == "admission_pending"
    assert state["conditions"] == [{"condition": "provider_admission_pending"}]
    assert state["next_safe_action"]["kind"] == "admit_provider_attempt"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["current_authority"]["owner"] == "gate_clearing_batch"


def test_current_work_unit_provider_admission_pending_observe_only_is_admission_blocked() -> None:
    current_work_unit = _executable_work_unit(
        owner="gate_clearing_batch",
        action_type="run_gate_clearing_batch",
        work_unit_id="publication_gate_replay",
        fingerprint="sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f",
    )
    current_work_unit["state"] = {
        "state_kind": "executable_owner_action",
        "provider_admission_pending": True,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        },
        diagnostic_report={
            "action_class": "observe_only",
            "will_start_llm": False,
            "codex_dispatch_count": 0,
            "provider_admission_pending_count": 0,
        },
    )

    assert state["phase"] == "admission_blocked"
    assert state["conditions"] == [
        {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "dhd_report_observe_only",
        }
    ]
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_provider_admission_without_study_identity_does_not_suppress_projection_contradiction() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "status": "provider_admission_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["conditions"][0]["condition"] == "operator_card_contradicts_auto_runtime_parked"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_accepted_closeout_typed_blocker_owns_recovery_before_admission_blocked() -> None:
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    current_work_unit = _executable_work_unit(
        owner="gate_clearing_batch",
        action_type="run_gate_clearing_batch",
        work_unit_id="publication_gate_replay",
        fingerprint=fingerprint,
    )
    current_work_unit["state"] = {
        "state_kind": "executable_owner_action",
        "provider_admission_pending": False,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "accepted_closeout_evidence": [
                {
                    "surface_kind": "stage_attempt_closeout_packet",
                    "status": "blocked",
                    "stage_closeout_status": "blocked",
                    "stage_attempt_id": "sat_e1063d97901cc3d70424fc5c",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "typed_blocker_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "supervision/consumer/default_executor_execution/"
                        "sat_e1063d97901cc3d70424fc5c.closeout.json#domain_blocker"
                    ),
                    "typed_blocker": {},
                    "paper_stage_log": {
                        "outcome": "typed_blocker",
                        "progress_delta_classification": "typed_blocker",
                        "remaining_blockers": ["opl_execution_authorization_required"],
                    },
                    "owner_result": {
                        "status": "blocked",
                        "blocked_reason": "opl_execution_authorization_required",
                    },
                    "closeout_refs": [
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "supervision/consumer/default_executor_execution/"
                        "sat_e1063d97901cc3d70424fc5c.closeout.json"
                    ],
                }
            ],
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "retry_budget_remaining": 0,
            },
        },
        diagnostic_report={
            "action_class": "observe_only",
            "will_start_llm": False,
            "codex_dispatch_count": 0,
            "provider_admission_pending_count": 0,
        },
    )

    assert state["phase"] == "domain_blocked"
    assert state["conditions"] == [
        {
            "condition": "accepted_closeout_typed_blocker",
            "blocker_type": "opl_execution_authorization_required",
        }
    ]
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["current_authority"]["obligation"]["owner"] == "gate_clearing_batch"
    assert state["next_safe_action"]["kind"] == "provide_opl_execution_authorization_or_human_gate"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_provider_admission_without_current_obligation_fingerprint_does_not_suppress_projection_contradiction() -> None:
    current_work_unit = _executable_work_unit()
    current_work_unit.pop("work_unit_fingerprint")
    current_work_unit.pop("action_fingerprint")
    current_work_unit["currentness_basis"] = {
        "truth_epoch": "truth::current",
        "runtime_health_epoch": "runtime::current",
        "work_unit_id": "medical_prose_write_repair",
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "status": "provider_admission_pending",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["conditions"][0]["condition"] == "operator_card_contradicts_auto_runtime_parked"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_paper_recovery_state_supersedes_stale_operator_parked_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "auto_runtime_parked",
            "current_blockers": [],
            "next_system_action": "Wait for explicit resume.",
            "paper_recovery_state": state,
            "auto_runtime_parked": {
                "surface_kind": "auto_runtime_parked",
                "parked": True,
                "parked_state": "explicit_resume_pending",
                "parked_owner": "user",
                "resource_release_expected": True,
                "awaiting_explicit_wakeup": True,
                "auto_execution_complete": False,
                "summary": "Waiting for explicit resume.",
            },
            "parked_state": "explicit_resume_pending",
            "parked_owner": "user",
            "resource_release_expected": True,
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
            "needs_user_decision": True,
            "user_decision_summary": "Resume the parked runtime.",
            "intervention_lane": {
                "lane_id": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
                "awaiting_explicit_wakeup": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
                "current_focus": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
                "awaiting_explicit_wakeup": True,
            },
            "operator_verdict": {
                "decision_mode": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
            },
            "recovery_contract": {
                "action_mode": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
            },
            "autonomy_contract": {
                "autonomy_state": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
            },
            "user_visible_projection": {
                "next_step": "Wait for explicit resume.",
                "why_not_progressing": "explicit_resume_pending",
            },
        }
    )

    assert result["current_stage"] == "publication_supervision"
    assert result["current_blockers"] == ["projection_inconsistent"]
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["superseded_by_paper_recovery_state"] is True
    assert result["parked_state"] is None
    assert result["parked_owner"] is None
    assert result["awaiting_explicit_wakeup"] is False
    assert result["needs_user_decision"] is False
    assert result["intervention_lane"]["lane_id"] == "paper_recovery_projection_inconsistent"
    assert "parked_state" not in result["intervention_lane"]
    assert result["operator_status_card"]["handling_state"] == (
        "paper_recovery_projection_inconsistent"
    )
    assert "parked_state" not in result["operator_status_card"]
    assert result["operator_verdict"]["decision_mode"] == "paper_recovery_state"
    assert result["recovery_contract"]["action_mode"] == "repair_projection_before_admission"
    assert result["autonomy_contract"]["autonomy_state"] == (
        "paper_recovery_projection_inconsistent"
    )
    assert result["user_visible_projection"]["why_not_progressing"] == "projection_inconsistent"


def test_paper_recovery_admission_blocked_suppresses_active_provider_admission_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "retry_budget_remaining": 0,
            },
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "current_blockers": [],
            "next_system_action": "admit_provider_attempt",
            "paper_recovery_state": state,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                }
            ],
            "owner_action_admission": {
                "admission_pending": True,
                "provider_attempt_start_requested": True,
            },
            "user_visible_projection": {
                "next_step": "admit_provider_attempt",
                "why_not_progressing": "admission_pending",
            },
        }
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    assert len(result["blocked_provider_admission_candidates"]) == 1
    assert result["owner_action_admission"]["admission_pending"] is False
    assert result["owner_action_admission"]["provider_attempt_start_requested"] is False
    assert result["user_visible_projection"]["why_not_progressing"] == "admission_blocked"


def test_paper_recovery_human_gate_keeps_user_decision_signal() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_work_unit": _typed_blocker_work_unit(
                owner="user",
                blocker_type="human_confirmation_required",
            ),
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_blockers": [],
            "paper_recovery_state": state,
            "needs_user_decision": False,
            "needs_physician_decision": False,
            "operator_status_card": {},
        }
    )

    assert result["current_blockers"] == []
    assert result["needs_user_decision"] is True
    assert result["needs_physician_decision"] is True
    assert result["user_decision_summary"] == (
        "Resolve the current typed blocker through its owner before starting another provider attempt."
    )
    assert result["intervention_lane"]["lane_id"] == "paper_recovery_human_gate"
    assert result["operator_verdict"]["needs_intervention"] is True


def test_running_attempt_requires_strong_identity_binding() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-unbound",
                "active_stage_attempt_id": "sat-unbound",
                "active_workflow_id": "wf-unbound",
            },
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["conditions"][0]["condition"] == "running_attempt_missing_obligation_identity"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_running_attempt_accepts_matching_recovery_obligation_identity() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-current",
                "active_stage_attempt_id": "sat-current",
                "active_workflow_id": "wf-current",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "recovery_obligation_id": (
                    "paper-recovery::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "run_quality_repair_batch::medical_prose_write_repair::"
                    "publication-blockers::0915410f804b3697"
                ),
            },
        }
    )

    assert state["phase"] == "attempt_running"
    assert state["next_safe_action"]["kind"] == "watch_running_attempt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_terminal_closeout_matching_obligation_waits_for_owner_consumption() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "terminal_closeout_precedence_evidence": {
                "status": "completed",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "stage_attempt_id": "sat-complete",
                "closeout_ref": "artifacts/supervision/consumer/default_executor_execution/sat-complete.closeout.json",
            },
        }
    )

    assert state["phase"] == "terminal_closeout_ready"
    assert state["next_safe_action"]["kind"] == "consume_terminal_closeout"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [
        "artifacts/supervision/consumer/default_executor_execution/sat-complete.closeout.json"
    ]


def test_terminal_closeout_with_stale_fingerprint_does_not_match_current_obligation() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "terminal_closeout_precedence_evidence": {
                "status": "completed",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::old",
                "action_fingerprint": "publication-blockers::old",
                "stage_attempt_id": "sat-stale",
                "closeout_ref": "artifacts/supervision/consumer/default_executor_execution/sat-stale.closeout.json",
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["next_safe_action"]["kind"] == "materialize_provider_admission_or_owner_callable"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert not state.get("evidence_refs")


def test_foreground_file_delta_without_owner_receipt_is_unadopted() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "manual_foreground_delta": {
                "changed": True,
                "paths": ["manuscript/main.tex"],
                "owner_receipt_ref": None,
            },
        }
    )

    assert state["phase"] == "manual_foreground_unadopted"
    assert state["next_safe_action"]["kind"] == "adopt_manual_delta_through_mas_owner_receipt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_runtime_report_marks_observe_only_provider_admission_as_blocked() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"

    result = report_aggregation.build_runtime_report(
        runtime_root=__import__("pathlib").Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[
            {
                "study_id": study_id,
                "status": "provider_admission_pending",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            }
        ],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": _executable_work_unit(
                    study_id=study_id,
                    fingerprint=fingerprint,
                ),
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    assert result["provider_admission_pending_count"] == 1
    assert result["will_start_llm"] is False
    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    assert result["paper_recovery_states"][study_id]["phase"] == "admission_blocked"
    action = result["managed_study_actions"][0]
    assert len(action["provider_admission_candidates"]) == 1
    assert action["provider_admission_candidates"][0]["study_id"] == study_id
    assert action["provider_admission_candidates"][0]["action_type"] == "run_quality_repair_batch"
    assert action["provider_admission_candidates"][0]["work_unit_id"] == "medical_prose_write_repair"
    assert action["provider_admission_candidates"][0]["work_unit_fingerprint"] == fingerprint
    assert action["paper_recovery_state"]["phase"] == "admission_blocked"
    assert action["current_work_unit"]["status"] == "executable_owner_action"
    assert action["current_execution_envelope"]["state_kind"] == "executable_owner_action"
    assert action["provider_admission_state"] == {
        "status": "blocked_by_paper_recovery_state",
        "candidate_count": 1,
        "running_provider_attempt": False,
        "paper_recovery_phase": "admission_blocked",
        "paper_recovery_reason": "provider_admission_pending_without_startable_dispatch",
    }


def test_runtime_report_owner_gate_event_supersedes_managed_action_typed_blocker() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    fingerprint = "publication-blockers::497d1260db522f01"

    result = report_aggregation.build_runtime_report(
        runtime_root=__import__("pathlib").Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "stage_packet_not_current_selected_dispatch",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": _typed_blocker_work_unit(
                    study_id=study_id,
                    action_type="run_quality_repair_batch",
                    work_unit_id="analysis_claim_evidence_repair",
                    blocker_type="stage_packet_not_current_selected_dispatch",
                )
                | {
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "study_intervention_events": [
                    {
                        "surface": "study_intervention_event",
                        "intent": "owner_gate_decision",
                        "event_id": "intervention-event-000001-13263a6ca77a1066",
                        "recorded_at": "2026-06-14T02:27:19+00:00",
                        "payload": {
                            "decision": "route_back_to_mas_packet_materialization_bug",
                            "current_owner_identity": {
                                "study_id": study_id,
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "analysis_claim_evidence_repair",
                                "work_unit_fingerprint": fingerprint,
                                "blocker_type": "stage_packet_not_current_selected_dispatch",
                            },
                            "human_gate_ref": "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
                            "owner_gate_decision_ref": "owner-gate-decision:c7027de42ca336cfe0782428",
                            "route_back_evidence_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
                            "provider_admission_allowed": False,
                        },
                    }
                ],
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    recovery = result["paper_recovery_states"][study_id]
    assert recovery["phase"] == "human_gate"
    assert recovery["conditions"][0]["condition"] == "accepted_owner_gate_decision"
    action = result["managed_study_actions"][0]
    assert action["paper_recovery_state"]["phase"] == "human_gate"
    assert action["decision"] == "human_gate"
    assert action["reason"] == "accepted_owner_gate_decision"
    assert action["running_provider_attempt"] is False


def test_runtime_scan_fresh_currentness_carries_owner_gate_events(monkeypatch, tmp_path) -> None:
    runtime_scan_support = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan_support"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    study_id = "002-dm-china-us-mortality-attribution"
    event = {
        "surface": "study_intervention_event",
        "intent": "owner_gate_decision",
        "event_id": "intervention-event-000001",
        "payload": {"decision": "route_back_to_mas_packet_materialization_bug"},
    }

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "study_intervention_events": [event],
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = runtime_scan_support._with_fresh_progress_currentness(
        profile=object(),
        study_root=tmp_path / study_id,
        status_payload={"study_id": study_id},
    )

    assert result["study_intervention_events"] == [event]


def test_same_tick_report_currentness_carries_owner_gate_events(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    study_id = "002-dm-china-us-mortality-attribution"
    event = {
        "surface": "study_intervention_event",
        "intent": "owner_gate_decision",
        "event_id": "intervention-event-000001",
        "payload": {"decision": "route_back_to_mas_packet_materialization_bug"},
    }

    def fake_read_study_progress(**kwargs):
        assert kwargs["study_id"] == study_id
        return {
            "generated_at": "2026-06-14T02:30:00+00:00",
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
            },
            "study_intervention_events": [event],
        }

    monkeypatch.setattr(study_progress, "read_study_progress", fake_read_study_progress)

    result = module._fresh_progress_currentness_for_report(
        profile=object(),
        study_ids=(study_id,),
    )

    assert result[study_id]["study_intervention_events"] == [event]
