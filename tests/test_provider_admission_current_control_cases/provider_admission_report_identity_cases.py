from __future__ import annotations

import importlib


closeout_identity = importlib.import_module(
    "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity"
)


def test_provider_admission_report_accepts_record_only_owner_refs_closeout_without_top_level_fingerprint_when_currentness_matches() -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    identity = {
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": "sha256:current-ai-reviewer",
        "action_fingerprint": "sha256:current-ai-reviewer",
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:current-ai-reviewer",
        },
    }

    closeout = report._closeout_evidence_with_identity(
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "closed_with_domain_owner_refs",
            "stage_attempt_id": "sat-record-only-without-fingerprint",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-current",
                "runtime_health_epoch": "runtime-health-event-current",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:current-ai-reviewer",
            },
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
    assert closeout_identity.closeout_identity_matches_current(closeout, identity=identity)


def test_provider_admission_report_preserves_action_fingerprint_from_owner_route_basis() -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    identity = {
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": "sha256:current-ai-reviewer",
        "action_fingerprint": "sha256:current-ai-reviewer",
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-event-current",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "work_unit_fingerprint": "sha256:current-ai-reviewer",
        },
    }

    closeout = report._closeout_evidence_with_identity(
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "closed_with_domain_owner_refs",
            "stage_attempt_id": "sat-action-fingerprint-basis",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-event-current",
                "runtime_health_epoch": "runtime-health-event-current",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "action_fingerprint": "sha256:current-ai-reviewer",
            },
            "owner_result": {
                "status": "closed_with_domain_owner_refs",
                "owner": "ai_reviewer",
                "owner_receipt_ref": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "supervision/consumer/default_executor_execution/"
                    "sat-action-fingerprint-basis.closeout.json#owner_receipt"
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

    assert closeout["action_fingerprint"] == "sha256:current-ai-reviewer"
    assert "work_unit_fingerprint" not in closeout
    assert closeout.get("identity_binding_status") != "inferred_from_current_work_unit"
    assert closeout_identity.closeout_identity_matches_current(closeout, identity=identity)


def test_provider_admission_report_identity_prefers_identity_different_current_owner_action() -> None:
    report = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )

    identity = report._progress_currentness_current_identity(
        {
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
                ),
                "currentness_basis": {
                    "truth_epoch": "truth-event-old",
                    "runtime_health_epoch": "runtime-health-old",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
                    ),
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                    "work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                },
            },
        }
    )

    assert identity == {
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
        "action_fingerprint": "publication-blockers::497d1260db522f01",
        "truth_epoch": "truth-event-current",
        "runtime_health_epoch": "runtime-health-current",
    }
