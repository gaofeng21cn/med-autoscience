from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any


def _stable_transition_step(payload: Mapping[str, Any]) -> dict[str, Any]:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_policy_result(payload, source="dm002_dm003.replay_fixture")
    assert result
    request = result["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert "projection_metadata" not in request
    assert "opl_domain_progress_transition_event" not in request
    assert "opl_domain_progress_transition_outbox_item" not in request
    assert "stage_run_identity" not in request
    return {
        "paper_progress_policy_result": result,
        "opl_domain_progress_transition_request": request,
        "transition_kind": result["recommended_opl_transition_kind"],
        "postcondition_kind": request["required_postcondition"]["kind"],
        "outcome_kind": result["policy_outcome_kind"],
        "authority_boundary": result["authority_boundary"],
        "projection_metadata": result["projection_metadata"],
    }


def _non_advancing_step(payload: Mapping[str, Any]) -> dict[str, Any]:
    adapter = importlib.import_module("med_autoscience.controllers.paper_progress_policy_adapter")
    result = adapter.build_non_advancing_policy_blocker(
        payload,
        reason="dm002_dm003_replay_no_stable_runtime_outcome",
    )
    request = result["opl_domain_progress_transition_request"]
    return {
        "paper_progress_policy_result": result,
        "opl_domain_progress_transition_request": request,
        "transition_kind": result["recommended_opl_transition_kind"],
        "postcondition_kind": request["required_postcondition"]["kind"],
        "outcome_kind": result["policy_outcome_kind"],
        "authority_boundary": result["authority_boundary"],
        "projection_metadata": result["projection_metadata"],
        "non_advancing_apply": True,
    }


def _assert_mas_adapter_only(step: Mapping[str, Any]) -> None:
    boundary = step["authority_boundary"]
    assert boundary["mas_can_authorize_provider_admission"] is False
    assert boundary["mas_can_run_fixed_point_reconciler"] is False
    assert boundary["mas_can_own_event_log_or_outbox"] is False
    assert boundary["mas_can_create_opl_outbox_record"] is False
    assert boundary["opl_owns_transition_runtime"] is True
    assert step["projection_metadata"]["authority"] is False
    assert step["projection_metadata"]["fixed_point_runtime_owner"] == "one-person-lab"


def test_dm002_replay_fixture_converges_to_exactly_one_stable_typed_blocker_transition() -> None:
    step = _stable_transition_step(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "ai_reviewer_record_gate_consumption"
                ),
                "typed_blocker": {
                    "blocker_type": "anti_loop_budget_exhausted",
                    "typed_blocker_ref": (
                        "studies/002-dm-china-us-mortality-attribution/artifacts/"
                        "supervision/consumer/default_executor_execution/"
                        "sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
                    ),
                },
                "currentness_basis": {
                    "observed_generation": "runtime-health-event-007034-9e7d25f9f14067b0",
                },
            },
        }
    )

    assert step["transition_kind"] == "RecordTypedBlocker"
    assert step["postcondition_kind"] == "typed_blocker_ref"
    assert step["outcome_kind"] == "typed_blocker"
    assert step["paper_progress_policy_result"]["paper_policy_verdict"]["typed_blocker_ref"].endswith(
        "sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
    )
    _assert_mas_adapter_only(step)


def test_dm003_replay_fixture_records_non_advancing_apply_when_owner_action_request_lacks_opl_readback() -> None:
    stable_request = _stable_transition_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "currentness_basis": {
                    "observed_generation": "runtime-health-event-006974-79380e0c39b23587",
                },
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "current_authority": {
                    "obligation": {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    }
                },
                "next_safe_action": {
                    "kind": "materialize_mas_transition_request_or_owner_callable",
                    "owner": "write",
                    "provider_admission_allowed": True,
                },
            },
        }
    )
    non_advancing = _non_advancing_step(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
        }
    )

    assert stable_request["transition_kind"] == "MaterializeOwnerAction"
    assert stable_request["postcondition_kind"] == "owner_action_ref"
    assert stable_request["outcome_kind"] == "owner_action_requested"
    assert non_advancing["transition_kind"] == "NonAdvancingApply"
    assert non_advancing["postcondition_kind"] == "non_advancing_apply_typed_blocker_ref"
    assert non_advancing["outcome_kind"] == "non_advancing_apply_typed_blocker"
    assert non_advancing["paper_progress_policy_result"]["paper_policy_verdict"] == {
        "verdict": "stable_typed_blocker_required",
        "typed_blocker_type": "non_advancing_apply",
        "reason": "dm002_dm003_replay_no_stable_runtime_outcome",
    }
    _assert_mas_adapter_only(stable_request)
    _assert_mas_adapter_only(non_advancing)
