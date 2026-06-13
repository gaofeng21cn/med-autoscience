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


def _write_record_only_closeout(
    profile,
    study_id: str,
    candidate: dict[str, object],
    *,
    include_currentness_basis: bool = True,
    closeout_name: str = "sat-record-only-without-fingerprint",
) -> None:
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / f"{closeout_name}.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    owner_route_basis = (
        {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": candidate["work_unit_id"],
            "work_unit_fingerprint": candidate["work_unit_fingerprint"],
            "owner_reason": candidate["work_unit_id"],
        }
        if include_currentness_basis
        else {}
    )
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_id": "domain_owner/default-executor-dispatch",
                "status": "closed_with_domain_owner_refs",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_attempt_id": closeout_name,
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": candidate["work_unit_id"],
                **({"owner_route_basis": owner_route_basis} if owner_route_basis else {}),
                "owner_receipt": {
                    "status": "closed_with_domain_owner_refs",
                    "owner": "ai_reviewer",
                    "owner_callable_surface": "publication.materialize-ai-reviewer-record",
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
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_provider_admission_report_consumes_candidate_root_record_only_closeout_when_scan_lacks_study(
    tmp_path: Path,
) -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)
    _write_record_only_closeout(profile, study_id, candidate)

    result = report.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {"progress_currentness": {}},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "noop",
                    "reason": "quest_waiting_for_user",
                    "running_provider_attempt": False,
                }
            ],
        },
        apply=False,
        generated_at="2026-06-12T12:45:00+00:00",
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


def test_provider_admission_report_merges_candidate_root_closeout_when_scan_has_study(
    tmp_path: Path,
) -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)
    _write_record_only_closeout(profile, study_id, candidate)

    result = report.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {"progress_currentness": {}},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "noop",
                    "reason": "current_action_visible_without_closeout_projection",
                    "running_provider_attempt": False,
                    "current_executable_owner_action": {
                        "next_owner": "ai_reviewer",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": candidate["work_unit_id"],
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                    },
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "owner": "ai_reviewer",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": candidate["work_unit_id"],
                        "work_unit_fingerprint": action_fingerprint,
                    },
                }
            ],
        },
        apply=False,
        generated_at="2026-06-12T12:45:00+00:00",
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


def test_provider_admission_report_consumes_closeout_with_top_level_owner_route_currentness_basis(
    tmp_path: Path,
) -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
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
        "dispatch_path": str(
            profile.studies_root
            / study_id
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_dispatches"
            / "run_quality_repair_batch.json"
        ),
        "next_executable_owner": "write",
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
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat-quality-repair.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_id": "domain_owner/default-executor-dispatch",
                "status": "executed",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_attempt_id": "sat-quality-repair",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "owner": "write",
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/quality_repair_batch/latest.json"
                ),
                "owner_route_currentness_basis": {
                    "source_eval_id": "publication-eval::current-ai-reviewer",
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-closeout",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                },
                "artifact_delta": {
                    "status": "fresh",
                    "meaningful_artifact_delta": True,
                    "changed_artifact_refs": [
                        f"studies/{study_id}/paper/draft.md",
                        f"studies/{study_id}/paper/build/review_manuscript.md",
                    ],
                },
                "user_stage_log": {
                    "surface_kind": "mas_paper_facing_stage_log_summary",
                    "schema_version": 1,
                    "status": "available",
                    "stage_name": "run_quality_repair_batch",
                    "problem_summary": "Quality repair produced a story-surface delta.",
                    "stage_goal": "Execute the owner-authorized quality repair batch.",
                    "stage_work_done": ["Ran quality repair."],
                    "paper_work_done": ["Updated manuscript story surfaces."],
                    "changed_stage_surfaces": [],
                    "changed_paper_surfaces": [
                        f"studies/{study_id}/paper/draft.md",
                        f"studies/{study_id}/paper/build/review_manuscript.md",
                    ],
                    "outcome": "progress_delta:canonical_manuscript_story_surface_delta_recorded",
                    "remaining_blockers": [],
                    "duration": {"status": "not_available", "seconds": None},
                    "token_usage": {"status": "not_available", "total_tokens": None},
                    "cost": {"status": "not_available", "usd": None},
                    "usage_refs": [],
                    "cost_refs": [],
                    "progress_delta_classification": "deliverable_progress",
                    "deliverable_progress_delta": {"count": 2, "token_usage_total": None},
                    "paper_progress_delta": {"count": 2, "token_usage_total": None},
                    "platform_repair_delta": {"count": 0, "token_usage_total": None},
                    "next_forced_delta": {
                        "owner": "review",
                        "required_output_surface": "AI reviewer or publication gate owner verdict",
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-event-closeout",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "evidence_refs": [],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = report.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {"progress_currentness": {}},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "noop",
                    "reason": "quest_waiting_for_owner_route_closeout_consumption",
                    "running_provider_attempt": False,
                }
            ],
        },
        apply=False,
        generated_at="2026-06-13T09:20:00+00:00",
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
    assert decision["evidence_status"] == "executed"


def test_provider_admission_report_consumes_progress_currentness_candidate_root_closeout(
    tmp_path: Path,
) -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat-quality-repair.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_id": "domain_owner/default-executor-dispatch",
                "status": "executed",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_attempt_id": "sat-quality-repair",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "owner": "write",
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                    "artifacts/controller/quality_repair_batch/latest.json"
                ),
                "owner_route_currentness_basis": {
                    "source_eval_id": "publication-eval::current-ai-reviewer",
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-closeout",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                },
                "artifact_delta": {
                    "status": "fresh",
                    "meaningful_artifact_delta": True,
                    "changed_artifact_refs": [
                        f"studies/{study_id}/paper/draft.md",
                        f"studies/{study_id}/paper/build/review_manuscript.md",
                    ],
                },
                "user_stage_log": {
                    "surface_kind": "mas_paper_facing_stage_log_summary",
                    "schema_version": 1,
                    "status": "available",
                    "stage_name": "run_quality_repair_batch",
                    "problem_summary": "Quality repair produced a story-surface delta.",
                    "stage_goal": "Execute the owner-authorized quality repair batch.",
                    "stage_work_done": ["Ran quality repair."],
                    "paper_work_done": ["Updated manuscript story surfaces."],
                    "changed_stage_surfaces": [],
                    "changed_paper_surfaces": [
                        f"studies/{study_id}/paper/draft.md",
                        f"studies/{study_id}/paper/build/review_manuscript.md",
                    ],
                    "outcome": "progress_delta:canonical_manuscript_story_surface_delta_recorded",
                    "remaining_blockers": [],
                    "duration": {"status": "not_available", "seconds": None},
                    "token_usage": {"status": "not_available", "total_tokens": None},
                    "cost": {"status": "not_available", "usd": None},
                    "usage_refs": [],
                    "cost_refs": [],
                    "progress_delta_classification": "deliverable_progress",
                    "deliverable_progress_delta": {"count": 2, "token_usage_total": None},
                    "paper_progress_delta": {"count": 2, "token_usage_total": None},
                    "platform_repair_delta": {"count": 0, "token_usage_total": None},
                    "next_forced_delta": {
                        "owner": "review",
                        "required_output_surface": "AI reviewer or publication gate owner verdict",
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-event-closeout",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "evidence_refs": [],
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = report.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                            "currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-event-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "next_owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                            "allowed_actions": ["run_quality_repair_batch"],
                            "required_output_surface": (
                                "artifacts/controller/repair_execution_evidence/latest.json"
                            ),
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "write",
                            "next_work_unit": work_unit_id,
                        },
                    }
                }
            },
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "noop",
                    "reason": "quest_waiting_for_owner_route_closeout_consumption",
                    "running_provider_attempt": False,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                    },
                }
            ],
        },
        apply=False,
        generated_at="2026-06-13T09:20:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["stage_route_arbiter"]["pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {}
    assert result["stage_route_arbiter_decisions"] == []
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert len(study["accepted_closeout_evidence"]) == 1
    assert study["accepted_closeout_evidence"][0]["stage_attempt_id"] == "sat-quality-repair"


def test_provider_admission_report_merges_candidate_root_closeout_into_existing_scan(
    tmp_path: Path,
) -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat-record-only-existing-scan.closeout.json"
    )
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "surface_kind": "stage_attempt_closeout_packet",
                "stage_id": "domain_owner/default-executor-dispatch",
                "status": "closed_with_domain_owner_refs",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_attempt_id": "sat-record-only-existing-scan",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": candidate["work_unit_id"],
                "owner_route_basis": {
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_reason": candidate["work_unit_id"],
                },
                "owner_receipt": {
                    "status": "closed_with_domain_owner_refs",
                    "owner": "ai_reviewer",
                    "publication_eval_record_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                        "publication_eval/ai_reviewer_responses/"
                        "20260612T123416Z_publication_eval_record.json"
                    ),
                    "record_only_surface": True,
                    "quality_authorized": False,
                    "submission_authorized": False,
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = report.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "ai_reviewer",
                            "next_work_unit": candidate["work_unit_id"],
                        }
                    }
                }
            },
        },
        apply=False,
        generated_at="2026-06-12T12:45:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }


def test_provider_admission_report_keeps_candidate_root_record_only_closeout_without_currentness_as_pending(
    tmp_path: Path,
) -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    action_fingerprint = "sha256:current-ai-reviewer"
    candidate = _provider_candidate(profile, study_id, action_fingerprint=action_fingerprint)
    _write_record_only_closeout(
        profile,
        study_id,
        candidate,
        include_currentness_basis=False,
        closeout_name="sat-record-only-without-currentness",
    )

    result = report.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "managed_study_opl_provider_admission_candidates": [candidate],
            "current_execution_evidence": {"progress_currentness": {}},
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "noop",
                    "reason": "quest_waiting_for_user",
                    "running_provider_attempt": False,
                }
            ],
        },
        apply=False,
        generated_at="2026-06-13T09:20:00+00:00",
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
