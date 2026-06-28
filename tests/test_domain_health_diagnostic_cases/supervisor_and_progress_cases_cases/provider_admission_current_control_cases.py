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
    assert candidate["paper_progress_policy_result"]["authority_role"] == "paper_domain_policy_adapter_only"
    assert "current_control_command" not in candidate
    assert "current_control_command_outbox_record" not in candidate
    request = candidate["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["mas_can_create_opl_outbox_record"] is False


def test_paper_recovery_ai_reviewer_successor_without_dispatch_surfaces_transition_request_candidate(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    action_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
    )
    currentness_basis = {
        "truth_epoch": "truth-event-dm002-successor",
        "runtime_health_epoch": "runtime-health-dm002-successor",
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
    }
    successor_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "next_owner": "ai_reviewer",
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "owner_route_currentness_basis": currentness_basis,
        "currentness_basis": currentness_basis,
    }
    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "handoff_scan_status": "scanned",
        "quest_status": "active",
        "running_provider_attempt": False,
        "action_queue": [],
        "current_executable_owner_action": successor_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "currentness_basis": currentness_basis,
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "ai_reviewer",
            "next_work_unit": work_unit_id,
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "ai_reviewer",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
                "successor_owner_action": {
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                    "required_output_surface": "artifacts/publication_eval/latest.json",
                    "currentness_basis": currentness_basis,
                },
            },
        },
    }

    result = provider_admission.current_control_provider_admission_candidates(
        {"surface": "opl_current_control_state_handoff", "studies": [scanned_study]},
        study_root=study_root,
        status_payload=scanned_study,
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "return_to_ai_reviewer_workflow"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == action_fingerprint
    assert candidate["next_executable_owner"] == "ai_reviewer"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_attempt_or_lease_required"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["opl_transition_runtime_required"] is True
    assert "dispatch_path" not in candidate
    assert "current_control_command" not in candidate
    assert "current_control_command_outbox_record" not in candidate
    request = candidate["opl_domain_progress_transition_request"]
    assert request["surface_kind"] == "mas_domain_progress_transition_request"
    assert request["target_runtime_owner"] == "one-person-lab"
    assert request["mas_can_create_opl_outbox_record"] is False


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
    assert candidate["paper_progress_policy_result"]["authority_boundary"]["mas_can_authorize_provider_admission"] is False
    assert candidate["opl_domain_progress_transition_request"]["required_postcondition"]["kind"] == (
        "provider_admission_enqueued_or_blocked"
    )


def test_provider_admission_candidate_from_quality_repair_current_work_unit_without_action(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    action_fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "write",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": action_fingerprint,
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route_currentness_basis": {
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                        "runtime_health_epoch": "runtime-health-event-006952-83815946e9b50f62",
                        "source_eval_id": (
                            "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                            "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
                        ),
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
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
                            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                            "runtime_health_epoch": "runtime-health-event-006952-83815946e9b50f62",
                            "source_eval_id": (
                                "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
                                "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
                            ),
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                    "paper_recovery_state": {
                        "surface_kind": "paper_recovery_state",
                        "phase": "owner_action_ready",
                        "next_safe_action": {
                            "kind": "materialize_successor_owner_action",
                            "owner": "write",
                            "provider_admission_allowed": True,
                            "successor_owner_action": {
                                "owner": "write",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
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
    assert candidate["source"] == "opl_current_control_state.study_current_work_unit"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["next_executable_owner"] == "write"
    assert candidate["required_output_surface"] == "artifacts/controller/repair_execution_evidence/latest.json"
    assert candidate["paper_progress_policy_result"]["authority_boundary"]["opl_owns_transition_runtime"] is True
    assert candidate["opl_domain_progress_transition_request"]["recommended_transition_kind"] == "StartProviderAttempt"
    assert "current_control_command_outbox_record" not in candidate


def test_provider_admission_candidate_from_owner_receipt_successor_action(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    stage_packet_path = (
        dispatch_path.parent
        / "immutable"
        / "run_quality_repair_batch"
        / "0915410f804b3697.json"
    )
    action_fingerprint = "publication-blockers::0915410f804b3697"
    work_unit_id = "medical_prose_write_repair"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {
                "dispatch_path": str(dispatch_path),
                "immutable_dispatch_path": str(stage_packet_path),
                "stage_packet_path": str(stage_packet_path),
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-16T04:15:51+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "owner_receipt_recorded",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                            "currentness_basis": {
                                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                                "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                                "runtime_health_epoch": "runtime-health-event-006965-287bc62eae272ff9",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "owner_receipt_recorded",
                            "owner": "write",
                            "next_work_unit": None,
                            "typed_blocker": None,
                            "parked_state": None,
                        },
                        "paper_recovery_state": {
                            "surface_kind": "paper_recovery_state",
                            "phase": "owner_action_ready",
                            "current_authority": {
                                "owner": "write",
                                "authority": "med-autoscience",
                                "obligation": {
                                    "study_id": study_id,
                                    "quest_id": study_id,
                                    "owner": "write",
                                    "action_type": "run_quality_repair_batch",
                                    "work_unit_id": work_unit_id,
                                    "work_unit_fingerprint": action_fingerprint,
                                    "currentness_basis": {
                                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                                        "truth_epoch": "truth-event-000035-39f0b8e96689a623",
                                        "runtime_health_epoch": "runtime-health-event-006965-287bc62eae272ff9",
                                        "work_unit_id": work_unit_id,
                                        "work_unit_fingerprint": action_fingerprint,
                                    },
                                },
                            },
                            "next_safe_action": {
                                "kind": "materialize_successor_owner_action",
                                "owner": "write",
                                "provider_admission_allowed": True,
                                "successor_owner_action": {
                                    "owner": "write",
                                    "action_type": "run_quality_repair_batch",
                                    "work_unit_id": work_unit_id,
                                    "work_unit_fingerprint": action_fingerprint,
                                    "source_surface": (
                                        "gate_clearing_batch_followthrough.actionable_current_work_unit"
                                    ),
                                    "source_ref": (
                                        str(study_root)
                                        + "/artifacts/controller/gate_clearing_batch/latest.json"
                                    ),
                                },
                            },
                        },
                    },
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    candidate = result["transition_request_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == action_fingerprint
    assert candidate["next_executable_owner"] == "write"
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["opl_domain_progress_transition_request"]["surface_kind"] == (
        "mas_domain_progress_transition_request"
    )
    assert candidate["opl_domain_progress_transition_request"]["target_runtime_owner"] == "one-person-lab"
    assert "current_control_command_outbox_record" not in candidate
    assert result["action_queue"]


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
                "stop_reason": "provider_handoff_written_transition_request_pending",
                "materialize": {
                    "owner_callable_adapters": [
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


from .provider_admission_current_control_cases_cases.test_materialized_closeout_cases import *  # noqa: F403,F401,E402
