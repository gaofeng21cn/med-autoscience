from __future__ import annotations

import importlib
from pathlib import Path


def _provider_candidate(profile, study_id: str, *, action_fingerprint: str) -> dict[str, object]:
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    return {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(
            profile.studies_root
            / study_id
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "return_to_ai_reviewer_workflow.json"
        ),
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }


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
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

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
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["study_id"] == study_id
    assert decision["action_type"] == "return_to_ai_reviewer_workflow"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == action_fingerprint


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


def test_provider_admission_current_control_retains_pending_when_closeout_identity_was_inferred(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    action_fingerprint = "publication-blockers::497d1260db522f01"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(dispatch_path),
        "next_executable_owner": "analysis-campaign",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T22:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "analysis-campaign",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "analysis-campaign",
                    "next_work_unit": work_unit_id,
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_closeout_status": "blocked",
                        "blocked_reason": "paper_progress_stall_fingerprint_stale",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "stage_attempt_id": "sat_fd3ea6271b172b0aa05bb4f0",
                        "identity_binding_status": "inferred_from_current_work_unit",
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"


def test_provider_admission_current_control_retains_pending_when_legacy_closeout_identity_was_action_only(
    tmp_path: Path,
) -> None:
    control = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    action_fingerprint = "publication-blockers::497d1260db522f01"
    identity = {
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "source_eval_id": "publication-eval::002::stage-attempt-sat-a9::2026-06-11T12:41:21+00:00",
    }
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(dispatch_path),
        "next_executable_owner": "analysis-campaign",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }
    action_only_closeout = report._closeout_evidence_with_identity(
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "blocked",
            "stage_closeout_status": "blocked",
            "execution_status": "blocked",
            "action_type": "run_quality_repair_batch",
            "blocked_reason": "paper_progress_stall_fingerprint_stale",
            "stage_attempt_id": "sat_fd3ea6271b172b0aa05bb4f0",
            "typed_blocker_ref": (
                "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                "consumer/default_executor_execution/sat_fd3ea6271b172b0aa05bb4f0.closeout.json#domain_blocker"
            ),
        },
        identity=identity,
    )

    result = control.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T22:55:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "analysis-campaign",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "analysis-campaign",
                    "next_work_unit": work_unit_id,
                },
                "accepted_closeout_evidence": [action_only_closeout],
            }
        ],
    )

    assert action_only_closeout["identity_binding_status"] == "inferred_from_current_work_unit"
    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    assert result["stage_route_arbiter_decisions"][0]["decision"] == "pending_provider_admission"
