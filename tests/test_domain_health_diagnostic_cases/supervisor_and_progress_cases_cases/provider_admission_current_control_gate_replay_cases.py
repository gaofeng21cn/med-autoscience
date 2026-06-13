from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_current_control_study_finalize_gate_replay_action_becomes_provider_admission(
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
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    work_unit_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::run_gate_clearing_batch"
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
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-previous-ai-reviewer-record",
                        "runtime_health_epoch": "runtime-health-event-previous-gate",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    },
                },
            },
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
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                        },
                    },
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current-ai-reviewer-record",
                            "runtime_health_epoch": "runtime-health-event-current-gate",
                            "work_unit_id": work_unit_id,
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
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["next_executable_owner"] == "finalize"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == work_unit_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)


def test_current_control_study_gate_replay_uses_current_ai_reviewer_eval_identity(
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
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T155750Z::sat_619d680b6dc5c74022af4a3b"
    )
    coarse_ticket = (
        f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::run_gate_clearing_batch"
    )
    expected_fingerprint = (
        f"current-ai-reviewer-gate-replay::{study_id}::{work_unit_id}::{source_eval_id}"
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
            "owner_route": {
                "next_owner": "gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_refs": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-previous-ai-reviewer-record",
                        "runtime_health_epoch": "runtime-health-event-previous-gate",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": "sha256:legacy-gate-replay-dispatch",
                    },
                },
            },
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
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "schema_version": 1,
                        "status": "ready",
                        "source": "study_progress.next_forced_delta.owner_action",
                        "next_owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "allowed_actions": ["run_gate_clearing_batch"],
                        "target_surface": {
                            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json"
                        },
                    },
                    "current_work_unit": {
                        "status": "executable_owner_action",
                        "study_id": study_id,
                        "owner": "finalize",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": coarse_ticket,
                        "action_fingerprint": coarse_ticket,
                        "currentness_basis": {
                            "truth_epoch": "truth-event-current-ai-reviewer-record",
                            "runtime_health_epoch": "runtime-health-event-current-gate",
                            "source_eval_id": source_eval_id,
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": coarse_ticket,
                        },
                    },
                    "intervention_lane": {
                        "route_back_checklist": {
                            "source_eval_id": source_eval_id,
                            "evidence_refs": [
                                (
                                    "/workspace/studies/003/artifacts/publication_eval/"
                                    "ai_reviewer_responses/20260610T160042Z_publication_eval_record.json"
                                )
                            ],
                        }
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
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["next_executable_owner"] == "finalize"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["work_unit_fingerprint"] == expected_fingerprint
    assert candidate["action_fingerprint"] == expected_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["currentness_basis"]["source_eval_id"] == source_eval_id
