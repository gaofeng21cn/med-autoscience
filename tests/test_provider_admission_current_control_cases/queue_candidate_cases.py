from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_domain_health_diagnostic_cases.shared import dump_json


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
    boundary = candidate["authority_boundary"]
    assert boundary["stage_transition_authority"] == "OPL Stage Transition Authority"
    assert boundary["stage_authority_role"] == "non_authoritative_observation_and_intent_producer"
    assert boundary["can_write_stage_current_pointer"] is False
    assert boundary["can_write_current_owner_delta"] is False
    assert boundary["can_write_stage_terminal_state"] is False
    assert boundary["can_mark_provider_attempt_running"] is False
    stage_boundary = candidate["stage_transition_authority_boundary"]
    assert stage_boundary["producer_kind"] == "runtime_provider"
    assert stage_boundary["intent_kind"] == "provider_observation"
    assert stage_boundary["stage_transition_authority"] == "one-person-lab"
    assert stage_boundary["intent_can_write_stage_current_pointer"] is False
    assert stage_boundary["intent_can_write_stage_run_terminal_state"] is False
    assert stage_boundary["intent_can_publish_current_owner_delta"] is False
    assert stage_boundary["intent_can_write_domain_truth"] is False


def test_provider_admission_candidate_from_current_control_gate_clearing_queue_survives_stale_blocker(
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
        / "run_gate_clearing_batch.json"
    )
    action_fingerprint = "sha256:current-repair-progress-gate-replay"
    work_unit_id = "publication_gate_replay"
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
            "action_fingerprint": "study-progress-current-owner-ticket::stale-gate-dispatch",
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
                        "next_owner": "gate_clearing_batch",
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
                    "blocker_type": "quest_waiting_for_user",
                    "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                },
            },
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "allowed_actions": ["run_gate_clearing_batch"],
                "repair_progress_precedence": {"source_fingerprint": action_fingerprint},
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["source"] == "opl_current_control_state.action_queue"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["next_executable_owner"] == "gate_clearing_batch"
    boundary = candidate["authority_boundary"]
    assert boundary["stage_transition_authority"] == "OPL Stage Transition Authority"
    assert boundary["stage_authority_role"] == "non_authoritative_observation_and_intent_producer"
    assert boundary["can_write_stage_current_pointer"] is False
    assert boundary["can_write_current_owner_delta"] is False
    assert boundary["can_write_stage_terminal_state"] is False
    assert boundary["can_mark_provider_attempt_running"] is False
    stage_boundary = candidate["stage_transition_authority_boundary"]
    assert stage_boundary["producer_kind"] == "runtime_provider"
    assert stage_boundary["intent_kind"] == "provider_observation"
    assert stage_boundary["stage_transition_authority"] == "one-person-lab"
    assert stage_boundary["intent_can_write_stage_current_pointer"] is False
    assert stage_boundary["intent_can_write_stage_run_terminal_state"] is False
    assert stage_boundary["intent_can_publish_current_owner_delta"] is False
    assert stage_boundary["intent_can_write_domain_truth"] is False
