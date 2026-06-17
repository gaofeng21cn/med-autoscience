from __future__ import annotations

import importlib
from pathlib import Path

from tests.provider_admission_current_control_helpers import (
    provider_candidate as _provider_candidate,
)


def test_provider_admission_current_control_treats_mas_request_without_opl_readback_as_non_advancing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "sha256:current-ai-reviewer-no-opl-readback"
    candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-17T08:40:00+00:00",
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
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    [transition_request_candidate] = result["transition_request_candidates"]
    assert transition_request_candidate["provider_admission_pending"] is False
    assert (
        transition_request_candidate["provider_admission_requires_opl_runtime_result"]
        is True
    )
    action = result["action_queue"][0]
    assert action["status"] == "transition_request_pending"
    assert action["provider_admission_pending"] is False
    assert action["provider_attempt_or_lease_required"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is True
    assert "opl_domain_progress_transition_result" not in action
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"
    assert decision["anti_loop_classification"] == "non_advancing_apply_required"
    assert decision["evidence"]["required_runtime"] == "DomainProgressTransitionRuntime"
    assert (
        decision["evidence"]["required_readback_surface_kind"]
        == "opl_domain_progress_transition_runtime_live_readback"
    )
    assert decision["evidence"]["missing_readback_sections"] == [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ]
    assert decision["evidence"]["mas_can_authorize_provider_admission"] is False
    assert decision["evidence"]["mas_can_create_opl_outbox_record"] is False
    assert decision["evidence"]["mas_can_create_opl_event"] is False
    assert decision["evidence"]["mas_can_create_opl_stage_run"] is False
    assert (
        decision["evidence"]["event_or_outbox_fragment_is_provider_admission_authority"]
        is False
    )
    assert decision["evidence"]["no_progress_signal"] == "transition_request_waits_for_opl_runtime"


def test_provider_admission_current_control_keeps_same_tick_materialized_recovery_request_consume_only(
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
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "source": "same_tick_materialized_dispatch",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "same_tick_materialized_provider_admission": True,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-16T00:25:00+00:00",
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
                    "supervisor_decision": {
                        "surface_kind": "paper_autonomy_supervisor_decision",
                        "decision": "materialize_recovery_action",
                        "next_owner": "write",
                        "next_safe_action": {
                            "kind": "materialize_recovery_work_unit_or_receipt",
                            "recovery_kind": "mas_control_plane_repair",
                            "source_next_safe_action": {
                                "kind": "run_mas_owner_callable",
                                "owner": "write",
                                "provider_admission_allowed": False,
                            },
                        },
                        "forbidden_interpretations": [
                            "provider_admission_pending_count=0",
                            "observe_only",
                        ],
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert len(result["transition_request_candidates"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"
    assert decision["anti_loop_classification"] == "non_advancing_apply_required"
    assert result["action_queue"][0]["action_type"] == "run_quality_repair_batch"
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["provider_admission_pending"] is False
    assert result["action_queue"][0]["provider_attempt_or_lease_required"] is False
    assert result["action_queue"][0]["provider_admission_requires_opl_runtime_result"] is True
