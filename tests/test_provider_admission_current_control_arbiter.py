from __future__ import annotations

import importlib
import json
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
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
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
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)

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


def test_provider_admission_current_control_suppresses_record_only_owner_refs_closeout(
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
        generated_at="2026-06-12T07:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": candidate["work_unit_id"],
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "execution_status": "executed",
                        "stage_attempt_id": "sat-record-only",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": candidate["work_unit_id"],
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "owner_receipt_ref": "artifacts/supervision/consumer/default_executor_execution/sat-record-only.closeout.json#owner_receipt",
                        "record_ref": "artifacts/publication_eval/ai_reviewer_responses/record.json",
                        "owner_result": {
                            "status": "closed_with_domain_owner_refs",
                            "owner": "ai_reviewer",
                            "publication_eval_surface": "not_written",
                            "record_only_surface": True,
                            "quality_authorized": False,
                            "submission_authorized": False,
                        },
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "closed_with_domain_owner_refs"


def test_provider_admission_current_control_suppresses_record_only_owner_refs_closeout_without_fingerprint(
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
        generated_at="2026-06-12T12:45:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": candidate["work_unit_id"],
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "stage_attempt_id": "sat-record-only-without-fingerprint",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": candidate["work_unit_id"],
                        "owner_result": {
                            "status": "closed_with_domain_owner_refs",
                            "owner": "ai_reviewer",
                            "owner_receipt_ref": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                                "supervision/consumer/default_executor_execution/"
                                "sat-record-only-without-fingerprint.closeout.json#owner_receipt"
                            ),
                            "publication_eval_record_ref": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                                "publication_eval/ai_reviewer_responses/"
                                "20260612T123416Z_publication_eval_record.json"
                            ),
                            "publication_eval_surface": "not_written",
                            "record_only_surface": True,
                            "quality_authorized": False,
                            "submission_authorized": False,
                        },
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "closed_with_domain_owner_refs"


def test_provider_admission_currentness_basis_not_inherited_from_different_current_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": "sha256:stale-ai-reviewer",
        "action_fingerprint": "sha256:stale-ai-reviewer",
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
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T13:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_executable_owner_action": {
                    "status": "ready",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "currentness_basis": {
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "source_eval_id": "publication-eval::003::fresh-write",
                        "truth_epoch": "truth::fresh",
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "weak_provider_admission_identity": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "weak_provider_admission_identity"
    assert decision["effect"] == "suppress_provider_admission_pending"


def test_fingerprintless_stop_loss_closeout_does_not_consume_new_source_eval_identity(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=fingerprint)
    candidate["currentness_basis"] = {
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "source_eval_id": "publication-eval::003::new",
        "truth_epoch": "truth::shared",
        "runtime_health_epoch": "runtime::shared",
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T13:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "currentness_basis": dict(candidate["currentness_basis"]),
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_typed_domain_blocker",
                        "stage_closeout_status": "blocked",
                        "outcome": "repeat_suppressed_with_typed_blocker",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": work_unit_id,
                        "typed_blocker_reason": "anti_loop_budget_exhausted",
                        "owner_route_currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "source_eval_id": "publication-eval::003::old",
                            "truth_epoch": "truth::shared",
                            "runtime_health_epoch": "runtime::shared",
                        },
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
    assert result["stage_route_arbiter_decisions"][0]["decision"] == "pending_provider_admission"


def test_provider_admission_report_accepts_record_only_owner_refs_closeout_without_fingerprint() -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    identity = {
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": "sha256:current-ai-reviewer",
        "action_fingerprint": "sha256:current-ai-reviewer",
    }

    closeout = report._closeout_evidence_with_identity(
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "closed_with_domain_owner_refs",
            "stage_attempt_id": "sat-record-only-without-fingerprint",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "owner_result": {
                "status": "closed_with_domain_owner_refs",
                "owner": "ai_reviewer",
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "supervision/consumer/default_executor_execution/"
                    "sat-record-only-without-fingerprint.closeout.json#owner_receipt"
                ),
                "publication_eval_record_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "publication_eval/ai_reviewer_responses/20260612T123416Z_publication_eval_record.json"
                ),
                "publication_eval_surface": "not_written",
                "record_only_surface": True,
                "quality_authorized": False,
                "submission_authorized": False,
            },
        },
        identity=identity,
    )

    assert closeout.get("identity_binding_status") != "inferred_from_current_work_unit"
    assert report._closeout_identity_matches_current(closeout, identity=identity)


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
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
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
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
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


def test_provider_admission_candidate_inherits_current_action_currentness_basis() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_type = "run_quality_repair_batch"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"

    status_payload = {
        "study_id": study_id,
        "study_progress_generated_at": "2026-06-12T09:30:00+00:00",
        "current_executable_owner_action": {
            "status": "ready",
            "next_owner": "write",
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_eval_id": "publication-eval::003::current-ai-reviewer-record",
            "truth_epoch": "truth::003::current",
            "runtime_health_epoch": "runtime::003::current",
            "allowed_actions": [action_type],
        },
    }
    execution = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": (
            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
            "consumer/default_executor_dispatches/run_quality_repair_batch.json"
        ),
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "owner_route_current": True,
        "next_executable_owner": "write",
        "owner_route": {
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
        },
    }

    [candidate] = module.provider_admission_candidates_from_execution_payload(
        {"executions": [execution]},
        execution_ref="studies/003/default_executor_execution/latest.json",
        status_payload=status_payload,
    )

    assert candidate["currentness_basis"] == {
        "source_eval_id": "publication-eval::003::current-ai-reviewer-record",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "truth_epoch": "truth::003::current",
        "runtime_health_epoch": "runtime::003::current",
    }
