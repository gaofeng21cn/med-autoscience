from __future__ import annotations

import importlib
from pathlib import Path


def test_provider_admission_current_control_does_not_consume_new_stage_packet_with_old_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    old_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    current_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/77fa1796dc1d50c2b7687a9f.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "stage_packet_ref": current_stage_packet_ref,
        "stage_packet_refs": [current_stage_packet_ref],
        "dispatch_ref": old_stage_packet_ref,
        "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
        "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "source_eval_id": "publication-eval::003::ai-reviewer-record::20260612T142918Z::sat_433",
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-13T18:30:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "execution_status": "executed",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_eval_id": "publication-eval::003::ai-reviewer-record::20260612T142918Z::sat_433",
                        "stage_attempt_id": "sat_f8e1cfe49a3aa3cf95d0584d",
                        "stage_packet_ref": old_stage_packet_ref,
                        "closeout_refs": [
                            f"studies/{study_id}/artifacts/supervision/consumer/"
                            "default_executor_execution/sat_f8e1cfe49a3aa3cf95d0584d.closeout.json",
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                            "artifacts/controller/repair_execution_evidence/latest.json",
                        ],
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                },
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


def test_accepted_closeout_matching_requires_current_stage_packet_identity() -> None:
    receipts = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_receipts"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = "publication-eval::003::ai-reviewer-record::20260612T142918Z::sat_433"
    old_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_quality_repair_batch.json"
    )
    current_stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/77fa1796dc1d50c2b7687a9f.json"
    )

    receipt = {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": "closed_with_domain_owner_refs",
        "execution_status": "executed",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "stage_attempt_id": "sat_f8e1cfe49a3aa3cf95d0584d",
        "stage_packet_ref": old_stage_packet_ref,
        "owner_result": {
            "owner_receipt_ref": (
                f"studies/{study_id}/artifacts/controller/repair_execution_evidence/latest.json"
            ),
        },
    }
    identity = {
        "surface": "opl_provider_admission_candidate",
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "stage_packet_ref": current_stage_packet_ref,
        "stage_packet_refs": [current_stage_packet_ref],
        "dispatch_ref": old_stage_packet_ref,
        "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
        "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "currentness_basis": {
            "source_eval_id": source_eval_id,
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    assert (
        receipts.accepted_closeout_matches_candidate_identity(
            receipt,
            identity=identity,
        )
        is False
    )
