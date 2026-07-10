from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_control_provider_admission_allows_write_owner_gate_clearing_target(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "ai_reviewer_record_gate_consumption"
    action_fingerprint = "route-currentness::dm002-write-gate-clearing-current"
    dump_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_owner_callable_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
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
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "write",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "owner_route_currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
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
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_rejects_write_owner_gate_clearing_without_strong_identity(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "ai_reviewer_record_gate_consumption"
    dump_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_owner_callable_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
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
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "write",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
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
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": work_unit_id,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_current_control_provider_admission_allows_write_quality_repair_from_study_current_action(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_quality_repair_batch.json"
    )
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    dump_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
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
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "currentness_basis": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "truth_epoch": "truth-event-current",
                            "runtime_health_epoch": "runtime-health-current",
                        },
                    },
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "write",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_quality_repair_batch"],
                        "target_surface": {
                            "surface_ref": (
                                "canonical manuscript story-surface delta or "
                                "typed blocker:manuscript_story_surface_delta_missing"
                            ),
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
        status_payload={"study_id": study_id},
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert result == []


def test_provider_admission_candidate_never_promotes_provider_completion_to_domain_completion(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    dispatch_path = tmp_path / "dispatches" / "return_to_ai_reviewer_workflow.json"
    action_fingerprint = "sha256:current-provider-admission-boundary"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    execution = {
        "source": "owner_callable_adapter_receipt",
        "execution_status": "handoff_ready",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": True,
        "owner_route_current": True,
        "owner_route": {
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

    candidate = provider_admission.provider_admission_candidate_from_execution(
        execution,
        execution_ref="runtime/artifacts/supervision/consumer/owner_callable_adapter_receipt/latest.json",
        status_study_id=study_id,
        current_action_identity={
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    )

    assert candidate is not None
    assert candidate["provider_completion_is_domain_completion"] is False
    assert candidate["authority_boundary"]["provider_completion_is_domain_completion"] is False
    assert (
        candidate["stage_transition_authority_boundary"]["provider_completion_counts_as_stage_transition"]
        is False
    )
