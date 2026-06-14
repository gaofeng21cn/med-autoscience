from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_domain_health_diagnostic_cases.shared import dump_json


def test_current_control_provider_admission_rejects_action_self_identity_when_canonical_identity_missing_but_envelope_exists(
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
    action_fingerprint = "sha256:queue-self-identity"
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
            "action_fingerprint": action_fingerprint,
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
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_rejects_action_self_identity_when_typed_blocker_has_current_action(
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
    action_fingerprint = "sha256:queue-self-identity-typed-blocker"
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
            "action_fingerprint": action_fingerprint,
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
                "owner": "one-person-lab",
                "next_work_unit": work_unit_id,
                "typed_blocker": {
                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                },
            },
            "current_executable_owner_action": {
                "source": "canonical_current_work_unit",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_rejects_retained_queue_when_current_work_unit_conflicts(
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
        / "return_to_ai_reviewer_workflow.json"
    )
    stale_fingerprint = "sha256:stale-ai-reviewer-recheck"
    current_fingerprint = "sha256:current-gate-replay"
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
            "required_output_surface": "artifacts/publication_eval/latest.json",
            "action_fingerprint": stale_fingerprint,
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
                    "next_work_unit": "stale_ai_reviewer_recheck",
                    "action_fingerprint": stale_fingerprint,
                    "work_unit_fingerprint": stale_fingerprint,
                    "refs": {"dispatch_path": str(dispatch_path)},
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "source_refs": {
                            "work_unit_id": "stale_ai_reviewer_recheck",
                            "work_unit_fingerprint": stale_fingerprint,
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-stale",
                                "runtime_health_epoch": "runtime-health-stale",
                                "work_unit_id": "stale_ai_reviewer_recheck",
                                "work_unit_fingerprint": stale_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_fingerprint,
                "action_fingerprint": current_fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_filters_synthetic_current_owner_ticket_from_identity(
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
    work_unit_id = "medical_prose_write_repair"
    ticket = (
        "study-progress-current-owner-ticket::003-dpcc-primary-care-phenotype-treatment-gap::"
        "medical_prose_write_repair::run_quality_repair_batch"
    )
    strong_fingerprint = "publication-blockers::0915410f804b3697"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [],
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": ticket,
                        "action_fingerprint": ticket,
                        "currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": strong_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": ticket,
                        "action_fingerprint": ticket,
                        "owner_route_currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": strong_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "write",
                        "next_work_unit": work_unit_id,
                    },
                }
            ],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": ticket,
                "action_fingerprint": ticket,
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": strong_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["work_unit_fingerprint"] == strong_fingerprint
    assert ticket not in candidate["work_unit_fingerprints"]
