from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_provider_admission_candidate_from_current_control_ai_reviewer_queue_cannot_self_clear_readiness_blocker(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "return_to_ai_reviewer_workflow.json"
    )
    action_fingerprint = "sha256:current-repair-progress-ai-reviewer"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dump_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
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
                    "stage_packet_ref": str(dispatch_path),
                    "stage_packet_refs": [str(dispatch_path)],
                    "owner_route": {
                        "next_owner": "ai_reviewer",
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "stage_packet_ref": str(dispatch_path),
                            "stage_packet_refs": [str(dispatch_path)],
                            "owner_route_currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                    "refs": {
                        "dispatch_path": str(dispatch_path),
                        "stage_packet_path": str(dispatch_path),
                    },
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
                            "stage_packet_ref": str(dispatch_path),
                            "stage_packet_refs": [str(dispatch_path)],
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

    assert result == []


def test_provider_admission_candidate_from_current_control_gate_clearing_queue_cannot_self_clear_stale_blocker(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    )
    action_fingerprint = "sha256:current-repair-progress-gate-replay"
    work_unit_id = "publication_gate_replay"
    dump_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_owner_callable_dispatch",
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

    assert result == []


def test_provider_admission_candidate_carries_top_level_work_unit_identity_from_transition_request(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission"
    )
    handoffs = importlib.import_module(
        "med_autoscience.controllers.provider_admission_parts.provider_admission_handoffs"
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
    stale_route_work_unit = "publication_gate_replay"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    dump_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_owner_callable_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "owner_route": {
                "next_owner": "write",
                "source_refs": {
                    "work_unit_id": stale_route_work_unit,
                    "work_unit_fingerprint": "stage-native-next-action::stale-dispatch-basis",
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-stale",
                        "runtime_health_epoch": "runtime-health-stale",
                        "work_unit_id": stale_route_work_unit,
                        "work_unit_fingerprint": "stage-native-next-action::stale-dispatch-basis",
                    },
                },
            },
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    action = {
        "study_id": study_id,
        "quest_id": study_id,
        "source_surface": "opl_current_control_state.study_current_executable_owner_action",
        "action_type": "run_quality_repair_batch",
        "status": "transition_request_pending",
        "owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "refs": {"dispatch_path": str(dispatch_path)},
    }
    current_action_identity = {
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }

    candidate = provider_admission.provider_admission_candidate_from_current_control_action(
        action,
        study_root=study_root,
        status_study_id=study_id,
        current_action_identity=current_action_identity,
        status_payload={"study_id": study_id},
        current_control_ref=(
            "/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json"
        ),
    )

    assert candidate is not None
    assert handoffs.handoff_work_unit_id({**action, "owner_route": {}}) == work_unit_id
    assert candidate["status"] == "transition_request_pending"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["currentness_basis"]["work_unit_id"] == work_unit_id
    assert candidate["currentness_basis"]["work_unit_fingerprint"] == action_fingerprint
    assert candidate["source_refs"]["work_unit_id"] == work_unit_id
    assert candidate["source_refs"]["work_unit_fingerprint"] == action_fingerprint
    policy_request = candidate["opl_domain_progress_transition_request"]
    assert policy_request["work_unit_id"] == work_unit_id
    assert policy_request["work_unit_fingerprint"] == action_fingerprint
