from __future__ import annotations

import importlib

import pytest


pytestmark = pytest.mark.meta


def test_durable_workflow_contract_separates_runtime_health_from_study_quality() -> None:
    module = importlib.import_module("med_autoscience.controllers.durable_workflow_contract")

    contract = module.build_durable_workflow_contract()

    assert contract["surface"] == "durable_workflow_contract"
    assert contract["workflow_owner"] == "MedAutoScience Runtime OS"
    assert contract["runtime_health_can_override_quality_truth"] is False
    assert contract["runtime_health_can_override_study_truth"] is False
    assert contract["study_truth_can_be_mutated_by_read_model"] is False
    assert contract["runtime_health_role"] == "observability_and_recovery_only"
    assert contract["quality_truth_owner"] == "Quality OS"
    assert contract["study_truth_owner"] == "StudyTruthKernel"
    assert contract["durability_guarantees"] == [
        "pause_resume_from_restore_point",
        "event_sourced_replay",
        "idempotent_controller_tick",
        "human_gate_as_durable_decision",
        "retry_budget_before_escalation",
    ]
    assert [state["state_id"] for state in contract["state_machine"]] == [
        "queued",
        "running",
        "awaiting_artifact_delta",
        "route_back",
        "awaiting_human_gate",
        "recovering",
        "completed",
        "escalated",
    ]
    assert "artifacts/runtime/health/latest.json" in contract["runtime_truth_surfaces"]
    assert "artifacts/publication_eval/latest.json" in contract["study_truth_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in contract["study_truth_surfaces"]
    assert contract["event_replay"]["event_log_required"] is True
    assert contract["event_replay"]["dedupe_key"] == "event_id"
    assert contract["event_replay"]["replay_starts_from"] == "restore_point_id"
    assert "retry_budget_remaining" in contract["event_replay"]["replay_must_reconstruct"]
    assert "retry_budget_decremented" in contract["event_replay"]["event_classes"]
    assert contract["idempotent_tick"]["duplicate_tick_policy"] == "return_existing_decision_ref"
    assert "tick_sequence" in contract["idempotent_tick"]["idempotency_key_fields"]
    assert "override_quality_truth" in contract["idempotent_tick"]["forbidden_tick_effects"]
    assert contract["human_gate"]["decision_surface"] == "artifacts/controller_decisions/latest.json"
    assert contract["human_gate"]["resume_requires_decision_id"] is True
    assert contract["retry_budget"]["retry_budget_field"] == "retry_budget_remaining"
    assert contract["retry_budget"]["exhaustion_requires_surface"] == "runtime_escalation_record.json"


def test_durable_workflow_validation_blocks_missing_restore_or_replay() -> None:
    module = importlib.import_module("med_autoscience.controllers.durable_workflow_contract")
    contract = module.build_durable_workflow_contract()
    contract["durability_guarantees"].remove("event_sourced_replay")
    contract["state_machine"][0]["resume_action"] = ""
    contract["event_replay"]["dedupe_key"] = ""
    contract["idempotent_tick"]["idempotency_key_fields"].remove("tick_sequence")
    contract["human_gate"]["decision_is_required"] = False
    contract["retry_budget"]["exhaustion_requires_surface"] = ""

    validation = module.validate_durable_workflow_contract(contract)

    assert validation["ok"] is False
    assert {issue["code"] for issue in validation["issues"]} == {
        "event_replay_missing_dedupe_key",
        "human_gate_missing_durable_decision",
        "idempotent_tick_missing_key_field",
        "missing_durability_guarantee",
        "retry_budget_missing_exhaustion_surface",
        "state_missing_resume_action",
    }


def test_ai_first_drift_audit_tracks_durable_workflow_contract() -> None:
    module = importlib.import_module("med_autoscience.ai_first_drift_audit")

    result = module.run_ai_first_drift_audit()

    assert result["status"] == "pass"
    assert "durable_workflow_contract_separates_runtime_from_quality_truth" not in result["summary"][
        "failed_check_ids"
    ]
