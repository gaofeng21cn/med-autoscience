from __future__ import annotations

import importlib
from pathlib import Path


closeout_identity = importlib.import_module(
    "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity"
)


def _provider_candidate(profile, study_id: str, *, action_fingerprint: str) -> dict[str, object]:
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dispatch_path = (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    route_key = f"provider-admission::{study_id}::{action_fingerprint}"
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
        "dispatch_path": str(dispatch_path),
        "stage_packet_ref": str(dispatch_path),
        "stage_packet_refs": [str(dispatch_path)],
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
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


def _with_current_admission_identity(
    candidate: dict[str, object],
    *,
    study_id: str,
    fingerprint: str,
    stage_packet_ref: str,
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return {
        **candidate,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
    }


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
                        "owner_receipt_ref": (
                            "artifacts/supervision/consumer/default_executor_execution/"
                            "sat-record-only.closeout.json#owner_receipt"
                        ),
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


def test_provider_admission_current_control_suppresses_record_only_owner_refs_closeout_without_fingerprint_when_currentness_matches(
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
                        "owner_route_currentness_basis": {
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-event-current",
                            "work_unit_id": candidate["work_unit_id"],
                            "work_unit_fingerprint": action_fingerprint,
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


def test_provider_admission_current_control_retains_pending_for_record_only_owner_refs_without_currentness_identity(
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
        generated_at="2026-06-13T09:20:00+00:00",
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
                        "stage_attempt_id": "sat-record-only-without-currentness",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": candidate["work_unit_id"],
                        "owner_result": {
                            "status": "closed_with_domain_owner_refs",
                            "owner": "ai_reviewer",
                            "owner_receipt_ref": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                                "supervision/consumer/default_executor_execution/"
                                "sat-record-only-without-currentness.closeout.json#owner_receipt"
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
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"


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


def test_consumed_domain_blocker_closeout_projects_current_typed_blocker(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    stage_packet_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/run_gate_clearing_batch/"
        "6e3e5a94951b7c405a834292.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(profile.workspace_root / stage_packet_ref),
        "dispatch_ref": stage_packet_ref,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "route_identity_key": f"owner-route::{study_id}::truth-current::gate_clearing_batch::replay",
        "attempt_idempotency_key": f"owner-route::{study_id}::truth-current::gate_clearing_batch::replay",
        "next_executable_owner": "gate_clearing_batch",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "truth_epoch": "truth-current",
            "runtime_health_epoch": "runtime-current",
            "source_eval_id": "publication-eval::003::current-gate",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-13T20:20:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_closeout_status": "blocked",
                        "execution_status": "blocked",
                        "stage_attempt_id": "sat_e1063d97901cc3d70424fc5c",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "dispatch_ref": stage_packet_ref,
                        "stage_packet_ref": stage_packet_ref,
                        "stage_packet_refs": [stage_packet_ref],
                        "owner_route_currentness_basis": {
                            "truth_epoch": "truth-current",
                            "runtime_health_epoch": "runtime-current",
                            "source_eval_id": "publication-eval::003::current-gate",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                        },
                        "typed_blocker_ref": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                            "supervision/consumer/default_executor_execution/"
                            "sat_e1063d97901cc3d70424fc5c.closeout.json#domain_blocker"
                        ),
                        "typed_blocker": {},
                        "paper_stage_log": {
                            "outcome": "typed_blocker",
                            "progress_delta_classification": "typed_blocker",
                            "remaining_blockers": ["opl_execution_authorization_required"],
                        },
                        "owner_result": {
                            "status": "blocked",
                            "blocked_reason": "opl_execution_authorization_required",
                        },
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    study = result["studies"][0]
    assert study["current_work_unit"]["status"] == "typed_blocker"
    blocker = study["current_work_unit"]["state"]["typed_blocker"]
    assert blocker["blocker_type"] == "opl_execution_authorization_required"
    assert blocker["owner"] == "gate_clearing_batch"
    assert study["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert study["blocked_reason"] == "opl_execution_authorization_required"


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


def test_record_only_closeout_does_not_consume_new_source_eval_write_repair(
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
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "source_eval_id": (
                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                "003-dpcc-primary-care-phenotype-treatment-gap::2026-06-13T00:48:48+00:00"
            ),
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006790-ae857144b128100c",
        },
    }
    candidate = _with_current_admission_identity(
        candidate,
        study_id=study_id,
        fingerprint=fingerprint,
        stage_packet_ref=str(candidate["dispatch_path"]),
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-13T00:57:39+00:00",
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
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": dict(candidate["currentness_basis"]),
                },
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": dict(candidate["currentness_basis"]),
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": work_unit_id,
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "execution_status": "executed",
                        "stage_attempt_id": "sat_f8e1cfe49a3aa3cf95d0584d",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "source_eval_id": (
                            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                            "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
                        ),
                        "owner_route_currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "source_eval_id": (
                                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
                            ),
                        },
                        "owner_result": {
                            "status": "closed_with_domain_owner_refs",
                            "owner": "quality_repair_batch",
                            "owner_receipt_ref": (
                                "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                                "controller/repair_execution_evidence/latest.json#repair_execution_evidence"
                            ),
                            "quality_authorized": False,
                            "submission_authorized": False,
                        },
                    }
                ],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"


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
    candidate = _with_current_admission_identity(
        candidate,
        study_id=study_id,
        fingerprint=action_fingerprint,
        stage_packet_ref=str(dispatch_path),
    )

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
    candidate = _with_current_admission_identity(
        candidate,
        study_id=study_id,
        fingerprint=action_fingerprint,
        stage_packet_ref=str(dispatch_path),
    )
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
