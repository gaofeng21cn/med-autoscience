from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _currentness_basis(
    *,
    work_unit_id: str,
    fingerprint: str,
    source_eval_id: str = "publication-eval::current",
) -> dict[str, str]:
    return {
        "truth_epoch": f"truth::{fingerprint}",
        "runtime_health_epoch": f"runtime-health::{fingerprint}",
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }


def test_provider_admission_candidate_from_current_control_ai_reviewer_queue_survives_readiness_blocker(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    action_fingerprint = "sha256:current-repair-progress-ai-reviewer"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
            "action_fingerprint": "study-progress-current-owner-ticket::stale-dispatch-fingerprint",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "return_to_ai_reviewer_workflow",
                    "status": "queued",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "work_unit_fingerprint": action_fingerprint,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                },
            },
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {"source_fingerprint": action_fingerprint},
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.action_queue"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "return_to_ai_reviewer_workflow"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["next_executable_owner"] == "ai_reviewer"


def test_provider_admission_candidate_from_analysis_campaign_quality_repair_current_action(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    action_fingerprint = "publication-blockers::497d1260db522f01"
    work_unit_id = "analysis_claim_evidence_repair"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "analysis-campaign",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "analysis-campaign",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": action_fingerprint,
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route_currentness_basis": {
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "source_eval_id": "publication-eval::002::current",
                    },
                },
            },
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "next_owner": "analysis-campaign",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "source_eval_id": "publication-eval::002::current",
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
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
                }
            ],
        },
        study_root=study_root,
        status_payload={"study_id": study_id},
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == action_fingerprint
    assert candidate["next_executable_owner"] == "analysis-campaign"
    assert candidate["required_output_surface"] == "artifacts/controller/repair_execution_evidence/latest.json"


def test_stale_current_control_gate_queue_is_suppressed_by_fresh_ai_reviewer_current_action(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "status": "queued",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                    "action_fingerprint": "sha256:stale-gate-replay",
                    "work_unit_fingerprint": "sha256:stale-gate-replay",
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "typed_blocker": {
                    "blocker_type": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                },
            },
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:fresh-ai-reviewer-recheck",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_same_tick_materialized_gate_dispatch_is_suppressed_by_fresh_ai_reviewer_progress_currentness(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-09T04:34:00+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "schema_version": 1,
                            "status": "ready",
                            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                            "next_owner": "ai_reviewer",
                            "action_type": "return_to_ai_reviewer_workflow",
                            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                            "work_unit_fingerprint": "sha256:fresh-ai-reviewer-recheck",
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                        },
                    },
                },
            },
            "developer_supervisor_same_tick": {
                "stop_reason": "provider_handoff_written_admission_pending",
                "materialize": {
                    "default_executor_dispatches": [
                        {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "action_type": "run_gate_clearing_batch",
                            "dispatch_status": "ready",
                            "dispatch_authority": "consumer_default_executor_dispatch",
                            "dispatch_path": str(dispatch_path),
                            "next_executable_owner": "gate_clearing_batch",
                            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": "sha256:stale-gate-replay",
                            "action_fingerprint": "sha256:stale-gate-replay",
                        },
                    ],
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["studies"][0]["study_id"] == study_id
    assert result["studies"][0]["handoff_scan_status"] == "scanned_no_provider_admission"
    assert result["current_execution_envelopes"][study_id] == {
        "state_kind": "executable_owner_action",
        "owner": "ai_reviewer",
        "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "typed_blocker": None,
        "parked_state": None,
        "source": "progress_currentness.current_executable_owner_action",
    }


def test_materialized_current_control_clears_candidate_after_accepted_typed_closeout(
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
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "mas_opl_runtime_owner_handoff.provider_admission_identity",
        "execution_ref": str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::003::current-ai-reviewer",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-10T21:45:15+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "default_executor_execution_receipt_consumption": {
                    "action_type": "return_to_ai_reviewer_workflow",
                    "execution_status": "accepted_typed_closeout",
                    "closeout_receipt_status": "accepted_typed_closeout",
                    "current_attempt_state": "accepted_typed_closeout",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "dispatch_path": str(dispatch_path),
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["studies"][0]["study_id"] == study_id
    assert result["studies"][0]["provider_admission_pending_count"] == 0
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["action_type"] == "return_to_ai_reviewer_workflow"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint
    assert result["current_execution_envelopes"][study_id]["source"] == (
        "progress_currentness.current_executable_owner_action"
    )


def test_terminal_closeout_suppresses_stale_running_but_preserves_next_handoff(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    old_work_unit_id = "medical_prose_write_repair"
    old_fingerprint = "publication-blockers::0915410f804b3697"
    next_work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    next_fingerprint = "sha256:fc2032327815ef9ab106e4ca972923ae2f18b3e3da019cf257298e2b3e3bc08a"
    old_dispatch_path = str(
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    next_dispatch_path = str(
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": next_work_unit_id,
        "work_unit_fingerprint": next_fingerprint,
        "action_fingerprint": next_fingerprint,
        "dispatch_path": next_dispatch_path,
        "stage_packet_ref": next_dispatch_path,
        "stage_packet_refs": [next_dispatch_path],
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=next_work_unit_id,
            fingerprint=next_fingerprint,
            source_eval_id="publication-eval::003::ai-reviewer-followup",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T09:50:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "running",
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat_3c7846886384a7166c4dd7a6",
                "active_workflow_id": "wf_724c6f21d7d4a3d32d0e3e5d",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": old_work_unit_id,
                "work_unit_fingerprint": old_fingerprint,
                "action_fingerprint": old_fingerprint,
                "dispatch_path": old_dispatch_path,
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "closed_with_domain_owner_refs",
                        "execution_status": "executed",
                        "stage_attempt_id": "sat_3c7846886384a7166c4dd7a6",
                        "active_workflow_id": "wf_724c6f21d7d4a3d32d0e3e5d",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": old_work_unit_id,
                        "work_unit_fingerprint": old_fingerprint,
                        "action_fingerprint": old_fingerprint,
                        "dispatch_path": old_dispatch_path,
                        "owner_receipt_ref": (
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                            "controller/repair_execution_receipts/latest.json"
                        ),
                        "owner_route_currentness_basis": _currentness_basis(
                            work_unit_id=old_work_unit_id,
                            fingerprint=old_fingerprint,
                            source_eval_id="publication-eval::003::write-repair",
                        ),
                        "closeout_refs": [
                            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/repair_execution_evidence/latest.json"
                        ],
                    }
                ],
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                    "next_owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": next_work_unit_id,
                    "work_unit_fingerprint": next_fingerprint,
                    "action_fingerprint": next_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": next_work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == next_work_unit_id
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert study["quest_status"] == "provider_admission_pending"
    assert study["running_provider_attempt"] is False
    assert study["active_stage_attempt_id"] is None
    assert study["terminal_closeout_precedence_evidence"]["stage_attempt_id"] == (
        "sat_3c7846886384a7166c4dd7a6"
    )
    assert study["action_queue"][0]["work_unit_id"] == next_work_unit_id
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }

def test_materialized_current_control_clears_candidate_after_executed_typed_blocker_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record::"
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T215426Z::sat_55f14ca934dd33c5287aecff"
    )
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "mas_opl_runtime_owner_handoff.provider_admission_identity",
        "execution_ref": str(
            profile.workspace_root
            / "runtime"
            / "artifacts"
            / "supervision"
            / "opl_current_control_state"
            / "latest.json"
        ),
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "consumer_default_executor_dispatch",
        "next_executable_owner": "gate_clearing_batch",
        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::003::current-gate-replay",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-10T23:36:08+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "default_executor_execution_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "default_executor_execution",
                    "receipt_ref": (
                        "artifacts/supervision/consumer/default_executor_execution/"
                        "sat_efe4fb48feb300595e5aade7.closeout.json"
                    ),
                    "stage_attempt_id": "sat_efe4fb48feb300595e5aade7",
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "executed",
                    "outcome": "typed_blocker",
                    "typed_blocker_reason": "publication_gate_replay_blocked",
                    "typed_blocker_ref": (
                        "runtime/quests/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/reports/publishability_gate/2026-06-10T233125Z.json"
                    ),
                    "owner_receipt_ref": (
                        "studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/controller/gate_clearing_batch/latest.json"
                    ),
                    "owner_route_currentness_basis": _currentness_basis(
                        work_unit_id=work_unit_id,
                        fingerprint=fingerprint,
                        source_eval_id="publication-eval::003::current-gate-replay",
                    ),
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "dispatch_path": str(dispatch_path),
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "mas_provider_admission_identity",
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "mas_provider_admission_identity",
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "accepted_closeout_consumed_pending": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "accepted_closeout_consumed_pending"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["action_type"] == "run_gate_clearing_batch"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == fingerprint
    envelope = result["current_execution_envelopes"][study_id]
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "gate_clearing_batch"
    assert envelope["next_work_unit"] == work_unit_id


def test_materialized_current_control_keeps_progress_first_live_attempt_over_old_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record::"
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
    )
    live_stage_attempt_id = "sat_a48379bbe63bcd5e86b5d6db"
    live_workflow_id = "wf_2b1e0398943b4922112354f8"

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[],
        generated_at="2026-06-11T20:42:12+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "quest_status": "active",
                "provider_admission_pending_count": 0,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "work_unit_id": work_unit_id,
                    "currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_eval_id": (
                            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                            "ai-reviewer-record::20260611T203520Z::sat_a48379bbe63bcd5e86b5d6db"
                        ),
                    },
                    "state": {
                        "state_kind": "typed_blocker",
                        "source": "accepted_closeout_consumed_pending",
                        "strict_running_proof": True,
                        "provider_attempt_proof": {
                            "running_provider_attempt": True,
                            "active_run_id": f"opl-stage-attempt://{live_stage_attempt_id}",
                            "active_stage_attempt_id": live_stage_attempt_id,
                            "active_workflow_id": live_workflow_id,
                            "runtime_health": {
                                "health_status": "running",
                                "runtime_liveness_status": "live",
                            },
                        },
                    },
                },
                "progress_first_monitoring_summary": {
                    "running_provider_attempt": True,
                    "active_run_id": f"opl-stage-attempt://{live_stage_attempt_id}",
                    "active_stage_attempt_id": live_stage_attempt_id,
                    "active_workflow_id": live_workflow_id,
                    "next_owner": "med-autoscience",
                    "next_work_unit": work_unit_id,
                    "worker_liveness": {
                        "health_status": "live",
                        "runtime_liveness_status": "live",
                    },
                },
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "executed",
                        "stage_closeout_status": "executed",
                        "execution_status": "executed",
                        "outcome": "executed",
                        "stage_attempt_id": "sat_cb5cc1d261fee2c397af8b05",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "typed_blocker_reason": "executed",
                        "typed_blocker_ref": "old-closeout.json",
                        "typed_blocker": {
                            "blocker_id": "executed",
                            "blocker_type": "executed",
                            "owner": "one-person-lab",
                            "write_permitted": False,
                        },
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "next_work_unit": None,
                    "typed_blocker": {"blocker_type": "executed", "owner": "one-person-lab"},
                    "parked_state": None,
                    "source": "accepted_closeout_consumed_pending",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    study = result["studies"][0]
    assert study["running_provider_attempt"] is True
    assert study["active_stage_attempt_id"] == live_stage_attempt_id
    assert study["active_workflow_id"] == live_workflow_id
    assert study["current_work_unit"]["status"] == "running_provider_attempt"
    envelope = result["current_execution_envelopes"][study_id]
    assert envelope["state_kind"] == "running_provider_attempt"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None
