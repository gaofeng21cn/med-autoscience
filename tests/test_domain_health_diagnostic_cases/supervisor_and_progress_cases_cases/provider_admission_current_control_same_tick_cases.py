from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_same_tick_materialized_current_ai_reviewer_dispatch_survives_progress_currentness(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = "sha256:fresh-ai-reviewer-recheck"
    study_root = profile.studies_root / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
    )
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
            "refs": {
                "dispatch_path": str(dispatch_path),
                "stage_packet_path": str(dispatch_path),
            },
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
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                            "owner_route_currentness_basis": {
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": work_unit_fingerprint,
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                            },
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
                            "action_type": "return_to_ai_reviewer_workflow",
                            "dispatch_status": "ready",
                            "dispatch_authority": "ai_reviewer_record_production_handoff",
                            "dispatch_path": str(dispatch_path),
                            "stage_packet_ref": str(dispatch_path),
                            "stage_packet_refs": [str(dispatch_path)],
                            "next_executable_owner": "ai_reviewer",
                            "required_output_surface": (
                                "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
                            ),
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "action_fingerprint": work_unit_fingerprint,
                        },
                    ],
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["work_unit_fingerprint"] == work_unit_fingerprint
    expected_identity = f"provider-admission::{study_id}::{work_unit_fingerprint}"
    candidate = result["provider_admission_candidates"][0]
    action = result["action_queue"][0]
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == str(dispatch_path)
    assert candidate["stage_packet_refs"] == [str(dispatch_path)]
    assert action["route_identity_key"] == expected_identity
    assert action["attempt_idempotency_key"] == expected_identity
    assert action["stage_packet_ref"] == str(dispatch_path)
    assert action["stage_packet_refs"] == [str(dispatch_path)]


def test_same_tick_materialized_dispatch_without_stage_packet_fails_closed(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    work_unit_fingerprint = "sha256:fresh-ai-reviewer-recheck"
    study_root = profile.studies_root / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "return_to_ai_reviewer_workflow.json"
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
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "allowed_actions": ["return_to_ai_reviewer_workflow"],
                            "owner_route_currentness_basis": {
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": work_unit_fingerprint,
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                            },
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
                            "action_type": "return_to_ai_reviewer_workflow",
                            "dispatch_status": "ready",
                            "dispatch_authority": "ai_reviewer_record_production_handoff",
                            "dispatch_path": str(dispatch_path),
                            "next_executable_owner": "ai_reviewer",
                            "required_output_surface": (
                                "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
                            ),
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
                            "action_fingerprint": work_unit_fingerprint,
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


def test_same_tick_owner_route_apply_refreshes_report_currentness_before_provider_admission(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    action_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
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
            "refs": {
                "dispatch_path": str(dispatch_path),
                "stage_packet_path": str(dispatch_path),
            },
        },
    )

    def stale_impl(**_: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-11T20:54:00+00:00",
            "runtime_root": str(profile.runtime_root),
            "scanned_quests": [],
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "decision": "blocked",
                    "reason": "closed_with_domain_owner_refs",
                    "running_provider_attempt": False,
                }
            ],
            "managed_study_opl_provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "current_execution_evidence": {
                "managed_study_actions": [],
                "provider_admission_candidates": [],
                "progress_currentness": {},
            },
            "action_fingerprints": [],
            "reports": [],
        }

    monkeypatch.setattr(module, "_run_domain_health_diagnostic_for_runtime_impl", stale_impl)
    monkeypatch.setattr(
        module,
        "_run_developer_supervisor_same_tick",
        lambda **_: {
            "surface": "developer_supervisor_same_tick",
            "schema_version": 1,
            "stop_reason": "provider_handoff_written_admission_pending",
            "study_ids": [study_id],
            "iterations": [],
            "materialize": {
                "surface": "domain_action_request_materializer",
                "default_executor_dispatch_count": 1,
                "ready_default_executor_dispatch_count": 1,
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
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                        "action_fingerprint": action_fingerprint,
                        "stage_packet_ref": str(dispatch_path),
                        "stage_packet_refs": [str(dispatch_path)],
                    }
                ],
            },
        },
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "generated_at": "2026-06-11T20:54:31+00:00",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "currentness_basis": {
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "finalize",
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
                    "route_target": "finalize",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "finalize",
                "next_work_unit": work_unit_id,
            },
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
        request_opl_owner_route_reconcile=True,
    )

    currentness = result["current_execution_evidence"]["progress_currentness"][study_id]
    assert currentness["current_work_unit"]["work_unit_id"] == work_unit_id
    assert result["provider_admission_pending_count"] == 1
    candidate = result["managed_study_opl_provider_admission_candidates"][0]
    assert candidate["source"] == "same_tick_materialized_dispatch"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    expected_identity = f"provider-admission::{study_id}::{action_fingerprint}"
    assert candidate["route_identity_key"] == expected_identity
    assert candidate["attempt_idempotency_key"] == expected_identity
    assert candidate["stage_packet_ref"] == str(dispatch_path)
    assert candidate["stage_packet_refs"] == [str(dispatch_path)]
    action = result["provider_admission_current_control_state"]["action_queue"][0]
    assert action["route_identity_key"] == expected_identity
    assert action["attempt_idempotency_key"] == expected_identity
    assert action["stage_packet_ref"] == str(dispatch_path)
    assert action["stage_packet_refs"] == [str(dispatch_path)]
    assert result["provider_admission_current_control_state"]["provider_admission_pending_count"] == 1
    assert result["action_fingerprints"] == [action_fingerprint]
