from __future__ import annotations

import importlib
from pathlib import Path

from tests.provider_admission_current_control_helpers import provider_candidate as _provider_candidate


def test_provider_admission_current_control_terminal_closeout_precedes_stale_live_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:10:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "running",
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-terminal-wins",
                "active_run_id": "run-terminal-wins",
                "active_workflow_id": "wf-terminal-wins",
                "opl_provider_attempt": {
                    "execution_status": "running",
                    "current_attempt_state": "running",
                    "running_provider_attempt": True,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-terminal-wins",
                    "active_run_id": "run-terminal-wins",
                    "active_workflow_id": "wf-terminal-wins",
                    "dispatch_path": candidate["dispatch_path"],
                },
                "default_executor_execution_receipt_consumption": {
                    "execution_status": "executed",
                    "current_attempt_state": "completed",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-terminal-wins",
                    "active_run_id": "run-terminal-wins",
                    "dispatch_path": candidate["dispatch_path"],
                    "typed_blocker_reason": "owner_output_already_current",
                    "typed_blocker_ref": "artifacts/closeouts/sat-terminal-wins.json",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "terminal_closeout_precedes_live_projection": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "terminal_closeout_precedes_live_projection"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "executed"
    assert decision["active_stage_attempt_id"] == "sat-terminal-wins"


def test_provider_admission_current_control_records_running_identity_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat-running",
                "active_run_id": "run-running",
                "active_workflow_id": "wf-running",
                "opl_provider_attempt": {
                    "execution_status": "running",
                    "current_attempt_state": "running",
                    "running_provider_attempt": True,
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "active_stage_attempt_id": "sat-running",
                    "active_run_id": "run-running",
                    "active_workflow_id": "wf-running",
                    "dispatch_path": candidate["dispatch_path"],
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "running_identity_observed": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "running_identity_observed"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["active_stage_attempt_id"] == "sat-running"


def test_provider_admission_current_control_records_accepted_closeout_arbiter_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T03:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "default_executor_execution_receipt_consumption": {
                    "execution_status": "executed",
                    "current_attempt_state": "completed",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "dispatch_path": candidate["dispatch_path"],
                    "typed_blocker_reason": "owner_output_already_current",
                    "typed_blocker_ref": "artifacts/closeouts/sat-closeout.json",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "executed"
