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
    closeout_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat-record-only-without-fingerprint.closeout.json"
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
                "stage_attempt_id": "sat-record-only-without-fingerprint",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": candidate["work_unit_id"],
                "owner_route_basis": {
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-stage-packet",
                    "source_eval_id": (
                        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                        "ai-reviewer-record::20260612T122941Z::sat-record-only-without-fingerprint"
                    ),
                    "work_unit_id": candidate["work_unit_id"],
                    "work_unit_fingerprint": "sha256:stage-packet-recovered",
                    "owner_reason": candidate["work_unit_id"],
                },
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
