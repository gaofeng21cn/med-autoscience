from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_materialized_currentness_current_action_becomes_provider_admission_candidate(
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
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-09T05:55:00+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "owner": "gate_clearing_batch",
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
                            "schema_version": 1,
                            "status": "ready",
                            "source": "study_progress.next_forced_delta.owner_action",
                            "next_owner": "gate_clearing_batch",
                            "work_unit_id": work_unit_id,
                            "allowed_actions": ["run_gate_clearing_batch"],
                            "target_surface": {
                                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": work_unit_id,
                        },
                    },
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    candidate = result["provider_admission_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert result["studies"][0]["handoff_scan_status"] == "provider_admission_from_mas_handoff"
    assert result["action_queue"][0]["work_unit_fingerprint"] == action_fingerprint


def test_domain_health_diagnostic_syncs_materialized_currentness_candidate_to_top_level_report(
    tmp_path: Path,
    monkeypatch,
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
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    def fake_impl(**_: object) -> dict[str, object]:
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-09T05:56:00+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_opl_provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "action_fingerprints": [],
            "current_execution_evidence": {
                "provider_admission_candidates": [],
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "owner": "gate_clearing_batch",
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
                            "schema_version": 1,
                            "status": "ready",
                            "source": "study_progress.next_forced_delta.owner_action",
                            "next_owner": "gate_clearing_batch",
                            "work_unit_id": work_unit_id,
                            "allowed_actions": ["run_gate_clearing_batch"],
                            "target_surface": {
                                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "gate_clearing_batch",
                            "next_work_unit": work_unit_id,
                        },
                    },
                },
            },
        }

    monkeypatch.setattr(module, "_run_domain_health_diagnostic_for_runtime_impl", fake_impl)

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        study_ids=(study_id,),
        request_opl_stage_attempts=True,
    )

    assert result["provider_admission_pending_count"] == 1
    candidates = result["managed_study_opl_provider_admission_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidates[0]["work_unit_id"] == work_unit_id
    assert result["provider_admission_current_control_state"]["provider_admission_pending_count"] == 1
    assert result["current_execution_evidence"]["provider_admission_candidates"] == candidates
    assert result["action_fingerprints"] == [action_fingerprint]
