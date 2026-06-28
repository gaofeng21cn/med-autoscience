from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.provider_admission_current_control_helpers import (
    opl_transition_readback as _opl_transition_readback,
    provider_candidate as _provider_candidate,
    provider_candidate_with_opl_readback as _provider_candidate_with_opl_readback,
)


def test_provider_admission_current_control_records_retained_pending_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
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
    assert decision["evidence_status"] == "opl_transition_consumed"
    consumption = decision["evidence"]["opl_transition_event_consumption"]
    readback = candidate["opl_domain_progress_transition_live_readback"]
    identity = readback["identity"]
    causality = readback["causality"]
    latest_transaction = readback["latest_transaction_readback"]
    stage_identity = identity["stage_run_identity"]
    assert consumption["surface_kind"] == "mas_opl_transition_event_consumption"
    assert consumption["status"] == "opl_transition_consumed"
    assert consumption["runtime_owner"] == "one-person-lab"
    assert consumption["runtime_kind"] == "DomainProgressTransitionRuntime"
    assert consumption["readback_surface_kind"] == (
        "opl_domain_progress_transition_runtime_live_readback"
    )
    assert consumption["event_id"] == identity["latest_event_id"]
    assert consumption["event_id"] == causality["event_id"]
    assert consumption["event_id"] == latest_transaction["event_id"]
    assert consumption["outbox_item_id"] == identity["latest_outbox_item_id"]
    assert consumption["outbox_item_id"] == causality["outbox_item_id"]
    assert consumption["outbox_item_id"] == latest_transaction["outbox_item_id"]
    assert consumption["transaction_id"] == identity["latest_transaction_id"]
    assert consumption["transaction_id"] == causality["transaction_id"]
    assert consumption["transaction_id"] == latest_transaction["transaction_id"]
    assert consumption["stage_run_id"] == stage_identity["stage_run_id"]
    assert consumption["route_identity_key"] == stage_identity["route_identity_key"]
    assert (
        consumption["attempt_idempotency_key"]
        == stage_identity["attempt_idempotency_key"]
    )
    assert consumption["request_idempotency_key"] == identity["idempotency_key"]
    assert consumption["same_transaction_event_and_outbox"] is True
    assert consumption["transaction_complete"] is True
    assert consumption["mas_can_authorize_provider_admission"] is False
    assert consumption["mas_can_create_opl_event"] is False
    assert consumption["mas_can_create_opl_outbox_record"] is False
    assert consumption["mas_can_create_opl_stage_run"] is False
    assert consumption["event_or_outbox_fragment_is_provider_admission_authority"] is False


def test_provider_admission_current_control_provider_readback_consumes_same_identity_transition_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    provider_candidate = _provider_candidate_with_opl_readback(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
        work_unit_id=work_unit_id,
        action_type="run_quality_repair_batch",
        next_executable_owner="write",
        required_output_surface="canonical manuscript story-surface delta",
    )
    provider_candidate["route_identity_key"] = idempotency_key
    provider_candidate["attempt_idempotency_key"] = idempotency_key
    provider_candidate["idempotency_key"] = idempotency_key
    provider_candidate["opl_domain_progress_transition_live_readback"] = _opl_transition_readback(
        study_id,
        action_fingerprint=action_fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=idempotency_key,
        attempt_idempotency_key=idempotency_key,
        request_idempotency_key=idempotency_key,
    )
    transition_request = {
        **_provider_candidate(
            profile,
            study_id,
            action_fingerprint=action_fingerprint,
        ),
        "status": "transition_request_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "idempotency_key": idempotency_key,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "idempotency_key": idempotency_key,
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[transition_request, provider_candidate],
        generated_at="2026-06-20T09:45:00+00:00",
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
                    "status": "typed_blocker",
                    "owner": "one-person-lab",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "source": "accepted_closeout_consumed_pending",
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["transition_request_pending_count"] == 0
    assert len(result["provider_admission_candidates"]) == 1
    assert result["transition_request_candidates"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    study = next(item for item in result["studies"] if item["study_id"] == study_id)
    assert study["provider_admission_pending_count"] == 1
    assert study.get("transition_request_pending_count", 0) == 0


def test_provider_admission_current_control_suppresses_candidate_blocked_by_paper_recovery_state(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(
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
        "med_autoscience.controllers.provider_admission_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = _provider_candidate_with_opl_readback(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
        work_unit_id=work_unit_id,
        action_type="run_quality_repair_batch",
        next_executable_owner="write",
        required_output_surface="artifacts/controller/repair_execution_evidence/latest.json",
    )

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
