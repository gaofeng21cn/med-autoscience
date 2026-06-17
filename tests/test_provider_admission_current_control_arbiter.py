from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.provider_admission_current_control_helpers import (
    provider_candidate as _provider_candidate,
    provider_candidate_with_opl_readback as _provider_candidate_with_opl_readback,
)
from tests.test_provider_admission_current_control_cases.test_arbiter_decision_cases import *  # noqa: F403,F401
from tests.test_provider_admission_current_control_cases.transition_request_consume_only_cases import *  # noqa: F403,F401


def test_provider_admission_current_control_records_retained_pending_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate_with_opl_readback(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:00:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "mas_provider_admission_identity",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    boundary = result["stage_route_arbiter"]["authority_boundary"]
    assert boundary["authority"] is False
    assert boundary["transition_runtime_owner"] == "one-person-lab"
    assert boundary["runtime_kind"] == "DomainProgressTransitionRuntime"
    assert boundary["can_authorize_provider_admission"] is False
    assert boundary["provider_admission_requires_mas_transition_request"] is True
    assert boundary["provider_admission_readback_requires_opl_live_readback"] is True
    assert boundary["event_or_outbox_fragment_is_provider_admission_authority"] is False
    assert boundary["can_run_fixed_point_runtime"] is False
    retained = result["provider_admission_candidates"][0]
    transition_request = retained["opl_domain_progress_transition_request"]
    assert transition_request["surface_kind"] == "mas_domain_progress_transition_request"
    assert transition_request["target_runtime_owner"] == "one-person-lab"
    assert transition_request["target_runtime_kind"] == "DomainProgressTransitionRuntime"
    assert transition_request["recommended_transition_kind"] == "StartProviderAttempt"
    assert transition_request["aggregate_identity"]["study_id"] == study_id
    assert transition_request["aggregate_identity"]["work_unit_id"] == work_unit_id
    assert transition_request["idempotency_key"]
    assert transition_request["source_generation"]
    assert transition_request["expected_version"]
    assert transition_request["required_postcondition"]["kind"] == "provider_admission_enqueued_or_blocked"
    assert transition_request["mas_can_create_opl_outbox_record"] is False
    action = result["action_queue"][0]
    assert action["paper_progress_policy_result"]["authority_role"] == "paper_domain_policy_adapter_only"
    assert action["opl_domain_progress_transition_request"] == transition_request
    assert action["handoff_packet"]["opl_domain_progress_transition_request"] == transition_request
    assert "current_control_command_outbox_record" not in action
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["study_id"] == study_id
    assert decision["action_type"] == "return_to_ai_reviewer_workflow"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == action_fingerprint


def test_provider_admission_current_control_suppresses_candidate_blocked_by_paper_recovery_state(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate_with_opl_readback(
            profile,
            study_id,
            action_fingerprint=action_fingerprint,
        ),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-14T12:40:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "paper_recovery_state": {
                    "surface_kind": "paper_recovery_state",
                    "phase": "owner_action_ready",
                    "current_authority": {"owner": "write"},
                    "conditions": [
                        {
                            "condition": "current_mas_owner_callable_ready",
                            "reason": "runtime_recovery_retry_budget_exhausted",
                        }
                    ],
                    "next_safe_action": {
                        "kind": "run_mas_owner_callable",
                        "owner": "write",
                        "provider_admission_allowed": False,
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "paper_recovery_state_blocks_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "paper_recovery_state_blocks_provider_admission"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "owner_action_ready"


def test_provider_admission_current_control_requires_execute_supervisor_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate_with_opl_readback(
            profile,
            study_id,
            action_fingerprint=action_fingerprint,
        ),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-14T12:40:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "paper_recovery_state": {
                    "surface_kind": "paper_recovery_state",
                    "phase": "admission_pending",
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
                        "kind": "admit_provider_attempt",
                        "owner": "write",
                        "provider_admission_allowed": True,
                    },
                    "supervisor_decision": {
                        "surface_kind": "paper_autonomy_supervisor_decision",
                        "decision": "materialize_recovery_action",
                        "next_safe_action": {
                            "kind": "materialize_recovery_work_unit_or_receipt",
                            "recovery_kind": "opl_runtime_repair",
                        },
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert result["action_queue"][0]["action_type"] == "run_quality_repair_batch"
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id


def test_provider_admission_report_suppresses_candidate_blocked_by_report_paper_recovery_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
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
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
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
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
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
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
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


def test_provider_admission_report_sync_keeps_transition_request_out_of_managed_admission_surface(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
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


def test_provider_admission_report_sync_consumes_transition_request_after_terminal_closeout(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
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
        "source": "opl_current_control_state.study_current_executable_owner_action",
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
    report = {
        "current_execution_evidence": {
            "progress_currentness": {
                study_id: {
                    "provider_admission_pending_count": 0,
                    "transition_request_pending_count": 0,
                    "provider_admission_candidates": [],
                    "transition_request_candidates": [],
                    "current_executable_owner_action": {
                        "status": "ready",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                    "opl_current_control_state_handoff": {
                        "provider_admission_terminal_closeout_consumed": {
                            "surface_kind": "provider_admission_terminal_closeout_consumed",
                            "stage_attempt_id": "sat-terminal",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": fingerprint,
                            "owner_receipt_ref": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                                "artifacts/controller/repair_execution_receipts/latest.json"
                            ),
                        },
                    },
                },
            },
            "transition_request_candidates": [dict(transition_request)],
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "provider_admission_candidates": [dict(transition_request)],
                    "provider_admission_state": {
                        "status": "none",
                        "candidate_count": 0,
                        "running_provider_attempt": False,
                    },
                }
            ],
        },
        "managed_study_actions": [
            {
                "study_id": study_id,
                "provider_admission_candidates": [dict(transition_request)],
                "provider_admission_state": {
                    "status": "none",
                    "candidate_count": 0,
                    "running_provider_attempt": False,
                },
            }
        ],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "transition_request_candidates": [dict(transition_request)],
        },
    )

    assert report["transition_request_pending_count"] == 0
    assert report["managed_study_opl_transition_request_candidates"] == []
    assert report["current_execution_evidence"]["transition_request_candidates"] == []
    action = report["managed_study_actions"][0]
    assert action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in action


def test_provider_admission_report_sync_clears_pending_when_managed_action_is_running(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint="publication-blockers::0915410f804b3697",
        ),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "action_fingerprint": "publication-blockers::0915410f804b3697",
    }
    running_action = {
        "study_id": study_id,
        "running_provider_attempt": True,
        "active_stage_attempt_id": "sat-running",
        "active_run_id": "opl-stage-attempt://sat-running",
        "active_workflow_id": "wf-running",
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "running_provider_attempt",
            "owner": "publication_gate",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        },
        "provider_admission_candidates": [candidate],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
            "running_provider_attempt": True,
        },
        "paper_recovery_state": {
            "phase": "attempt_running",
            "next_safe_action": {
                "kind": "watch_running_attempt",
                "owner": "publication_gate",
                "provider_admission_allowed": False,
            },
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [candidate],
            "managed_study_actions": [dict(running_action)],
        },
        "managed_study_actions": [dict(running_action)],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [candidate],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    assert report["current_execution_evidence"]["provider_admission_candidates"] == []
    synced_action = report["managed_study_actions"][0]
    assert synced_action["running_provider_attempt"] is True
    assert synced_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in synced_action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["running_provider_attempt"] is True
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action


def test_provider_admission_current_control_runtime_health_live_attempt_suppresses_pending(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-14T13:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "runtime_health_snapshot": {
                    "worker_liveness_state": {
                        "state": "live",
                        "runtime_liveness_status": "live",
                        "worker_running": True,
                        "active_run_id": "opl-stage-attempt://sat-running",
                        "active_stage_attempt_id": "sat-running",
                        "active_workflow_id": "wf-running",
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "running_identity_observed": 1,
    }
    study = result["studies"][0]
    assert study["running_provider_attempt"] is True
    assert study["active_stage_attempt_id"] == "sat-running"
    assert study["current_work_unit"]["status"] == "running_provider_attempt"
    assert study["current_execution_envelope"]["state_kind"] == "running_provider_attempt"


def test_provider_admission_report_sync_clears_domain_blocked_recovery_pending_state(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    candidate = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint="publication-blockers::497d1260db522f01",
        ),
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
        "action_fingerprint": "publication-blockers::497d1260db522f01",
    }
    action = {
        "study_id": study_id,
        "decision": "blocked",
        "reason": "stage_packet_not_current_selected_dispatch",
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "analysis-campaign",
            "state": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                    "owner": "analysis-campaign",
                },
            },
        },
        "provider_admission_candidates": [candidate],
        "provider_admission_state": {
            "status": "pending",
            "candidate_count": 1,
            "running_provider_attempt": False,
        },
        "paper_recovery_state": {
            "phase": "domain_blocked",
            "conditions": [
                {
                    "condition": "current_work_unit_typed_blocker",
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                }
            ],
            "next_safe_action": {
                "kind": "resolve_typed_blocker",
                "owner": "analysis-campaign",
                "provider_admission_allowed": False,
            },
            "suppressed_surfaces": [
                "current_executable_owner_action",
                "provider_admission_candidates",
            ],
        },
    }
    report = {
        "managed_study_opl_provider_admission_candidates": [candidate],
        "provider_admission_pending_count": 1,
        "current_execution_evidence": {
            "provider_admission_candidates": [candidate],
            "managed_study_actions": [dict(action)],
        },
        "managed_study_actions": [dict(action)],
    }

    report_module.sync_report_provider_admission_current_control_state(
        report,
        current_control_state={
            "provider_admission_candidates": [candidate],
        },
    )

    assert report["managed_study_opl_provider_admission_candidates"] == []
    assert report["provider_admission_pending_count"] == 0
    assert report["current_execution_evidence"]["provider_admission_candidates"] == []
    synced_action = report["managed_study_actions"][0]
    assert synced_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in synced_action
    evidence_action = report["current_execution_evidence"]["managed_study_actions"][0]
    assert evidence_action["provider_admission_candidates"] == []
    assert "provider_admission_state" not in evidence_action


def test_provider_admission_report_refreshes_scanned_typed_blocker_without_candidates(
    tmp_path: Path,
) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    blocker_ref = "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    stale_candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint="sha256:stale-ai-reviewer",
    )
    latest_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "surface": "opl_current_control_state_handoff",
                "schema_version": 1,
                "studies": [
                    {
                        "study_id": study_id,
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "ai_reviewer",
                            "next_work_unit": stale_candidate["work_unit_id"],
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "next_owner": "ai_reviewer",
                            "action_type": stale_candidate["action_type"],
                            "work_unit_id": stale_candidate["work_unit_id"],
                            "work_unit_fingerprint": stale_candidate["work_unit_fingerprint"],
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                    }
                ],
                "action_queue": [stale_candidate],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [],
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
                        "work_unit_fingerprint": f"current-readiness-typed-blocker::{study_id}::fresh",
                        "state": {
                            "state_kind": "typed_blocker",
                            "source": "stage_owner_answer",
                            "typed_blocker": {
                                "blocker_type": "medical_paper_readiness_missing",
                                "owner": "MedAutoScience",
                                "source_ref": blocker_ref,
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
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["candidate_count"] == 0
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert study["current_work_unit"]["status"] == "typed_blocker"
    assert study["current_work_unit"]["owner"] == "MedAutoScience"
    assert study["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert (
        result["current_execution_envelopes"][study_id]["typed_blocker"]["blocker_type"]
        == "medical_paper_readiness_missing"
    )
