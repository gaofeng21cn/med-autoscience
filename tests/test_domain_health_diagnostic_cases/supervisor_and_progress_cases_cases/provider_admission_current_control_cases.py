from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


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


def test_materialized_current_control_clears_previous_gate_queue_when_ai_reviewer_is_current(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    latest_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        latest_path,
        {
            "surface": "opl_current_control_state_handoff",
            "generated_at": "2026-06-09T04:53:07+00:00",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "handoff_scan_status": "previous_gate_queue",
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "run_gate_clearing_batch",
                            "status": "queued",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": "publication_gate_replay",
                        },
                    ],
                    "current_execution_envelope": {
                        "state_kind": "executable_owner_action",
                        "owner": "gate_clearing_batch",
                        "next_work_unit": "publication_gate_replay",
                        "source": "previous_current_control",
                    },
                }
            ],
            "action_queue": [
                {
                    "study_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "status": "queued",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:stale-gate",
                },
            ],
            "current_execution_envelopes": {
                study_id: {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": "publication_gate_replay",
                    "source": "previous_current_control",
                },
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=True,
        report={
            "scanned_at": "2026-06-09T05:16:53+00:00",
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
                            "next_executable_owner": "gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": "sha256:stale-gate",
                            "action_fingerprint": "sha256:stale-gate",
                        },
                    ],
                },
            },
        },
    )

    assert result is not None
    assert result["written"] is True
    assert result["action_queue"] == []
    assert result["provider_admission_pending_count"] == 0
    assert result["studies"][0]["handoff_scan_status"] == "scanned_no_provider_admission"
    assert result["current_execution_envelopes"][study_id]["owner"] == "ai_reviewer"

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["action_queue"] == []
    assert latest["provider_admission_candidates"] == []
    assert latest["current_execution_envelopes"][study_id]["owner"] == "ai_reviewer"


def test_runtime_report_prefers_fresh_progress_envelope_over_stale_user_waiting_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"

    result = report_aggregation._current_execution_envelopes(
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "continue_supervising_runtime",
                },
            }
        ],
        suppressions=[],
        progress_currentness={
            study_id: {
                "current_work_unit": {
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source_refs": [
                        "/workspace/studies/003/artifacts/controller/repair_execution_evidence/latest.json"
                    ],
                    "conflict_suppression_refs": [
                        "runtime_health:continue_supervising_runtime"
                    ],
                },
            }
        },
    )

    envelope = result[study_id]
    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == work_unit_id
    assert envelope["typed_blocker"] is None
    assert envelope["parked_state"] is None


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
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": work_unit_fingerprint,
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
    assert result["provider_admission_pending_count"] == 1
    assert result["action_queue"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["work_unit_fingerprint"] == work_unit_fingerprint


def test_domain_health_diagnostic_dry_run_surfaces_current_control_ai_reviewer_queue(
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
        / "return_to_ai_reviewer_workflow.json"
    )
    action_fingerprint = "sha256:current-control-ai-reviewer-recheck"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    dump_json(
        dispatch_path,
        {
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "return_to_ai_reviewer_workflow",
            "dispatch_status": "ready",
            "dispatch_authority": "ai_reviewer_record_production_handoff",
            "next_executable_owner": "ai_reviewer",
            "required_output_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )
    current_control_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    dump_json(
        current_control_path,
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
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="blocked",
            reason="quest_waiting_for_user",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(profile.runtime_root / "quests" / study_id),
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "medical_paper_readiness_missing",
                "source_ref": "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
            },
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-08T06:40:00+00:00",
            "current_execution_envelope": status_payload["current_execution_envelope"],
            "current_executable_owner_action": {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "repair_progress_precedence": {"source_fingerprint": action_fingerprint},
            },
        },
    )

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 1
    candidate = result["managed_study_opl_provider_admission_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.action_queue"
    assert candidate["action_type"] == "return_to_ai_reviewer_workflow"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert result["action_fingerprints"] == [action_fingerprint]


def test_request_opl_stage_attempt_carries_current_provider_admission_identity(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    typed_blocker_ref = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "08-publication_package_handoff"
        / "receipts"
        / "typed_blocker.json"
    )
    work_unit_fingerprint = (
        "stage-current-owner-delta::complete_medical_paper_readiness_surface::"
        f"authoring_runtime_authorization::{typed_blocker_ref}"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "complete_medical_paper_readiness_surface",
                    "execution_status": "handoff_ready",
                    "owner_callable_surface": "opl_default_executor.stage_attempt",
                    "provider_attempt_or_lease_required": True,
                    "dispatch_path": str(dispatch_path),
                    "action_fingerprint": work_unit_fingerprint,
                    "owner_route": {
                        "source_refs": {
                            "work_unit_id": "complete_medical_paper_readiness_surface",
                            "work_unit_fingerprint": work_unit_fingerprint,
                        }
                    },
                }
            ]
        },
    )
    status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "quest_id": study_id,
            "current_executable_owner_action": {
                "status": "ready",
                "source": "stage_kernel_projection.current_owner_delta",
                "next_owner": "MedAutoScience",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
                "surface_key": "authoring_runtime_authorization",
            "source_ref": str(typed_blocker_ref),
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "complete_medical_paper_readiness_surface"
    assert identity["work_unit_id"] == "complete_medical_paper_readiness_surface"
    assert identity["action_fingerprint"] == work_unit_fingerprint
    assert identity["dispatch_path"] == str(dispatch_path)
    assert result["provider_admission_identity"] == identity


def test_request_opl_stage_attempt_uses_fresh_progress_currentness_for_authorization_blocker(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": study_id})
    quest_root = profile.runtime_root / "quests" / study_id
    action_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::"
        "dm002_current_publication_hardening_after_current_ai_reviewer_eval::run_quality_repair_batch"
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    dump_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "study_id": study_id,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "write",
                    "required_output_surface": "canonical manuscript story-surface delta",
                    "dispatch_path": str(dispatch_path),
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ],
        },
    )
    stale_status_payload = {
        **make_progress_projection_payload(
            study_id=study_id,
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_id": study_id,
        "quest_root": str(quest_root),
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_type": "quest_marked_running_but_no_live_session",
                "owner": "med-autoscience",
            },
        },
    }
    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: stale_status_payload)
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "generated_at": "2026-06-08T05:40:00+00:00",
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
            },
            "current_executable_owner_action": {
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_fingerprint": action_fingerprint,
                "allowed_actions": ["run_quality_repair_batch"],
            },
        },
    )

    result = module._request_opl_stage_attempt(
        profile=profile,
        study_root=study_root,
        source="domain_health_diagnostic",
    )

    identity = result["opl_stage_attempt_request"]["provider_admission_identity"]
    assert identity["study_id"] == study_id
    assert identity["action_type"] == "run_quality_repair_batch"
    assert identity["work_unit_id"] == "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
    assert identity["action_fingerprint"] == action_fingerprint
    assert identity["blocked_reason"] == "opl_execution_authorization_required"
    assert result["provider_admission_identity"] == identity
