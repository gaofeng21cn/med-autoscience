from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def _identity_key(study_id: str, fingerprint: str) -> str:
    return f"provider-admission::{study_id}::{fingerprint}"


def _dispatch_refs(
    profile,
    *,
    study_id: str,
    action_type: str,
    packet_name: str,
    fingerprint: str,
) -> dict[str, object]:
    stage_packet_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        f"immutable/{action_type}/{packet_name}.json"
    )
    identity_key = _identity_key(study_id, fingerprint)
    return {
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": [stage_packet_ref],
        "route_identity_key": identity_key,
        "attempt_idempotency_key": identity_key,
        "refs": {
            "dispatch_path": str(
                profile.studies_root
                / study_id
                / "artifacts"
                / "supervision"
                / "consumer"
                / "default_executor_dispatches"
                / f"{action_type}.json"
            ),
            "stage_packet_path": str(profile.workspace_root / stage_packet_ref),
            "immutable_dispatch_path": str(profile.workspace_root / stage_packet_ref),
        },
    }


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
            **_dispatch_refs(
                profile,
                study_id=study_id,
                action_type="run_gate_clearing_batch",
                packet_name="current",
                fingerprint=action_fingerprint,
            ),
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
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    candidate = result["transition_request_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["status"] == "transition_request_pending"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert result["studies"][0]["handoff_scan_status"] == "provider_admission_from_mas_handoff"
    assert result["studies"][0]["quest_status"] == "transition_request_pending"
    assert result["action_queue"][0]["work_unit_fingerprint"] == action_fingerprint
    assert result["action_queue"][0]["provider_attempt_or_lease_required"] is False


def test_materialized_currentness_ignores_study_root_closeout_without_native_current_identity(
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
    closeout_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "stage_attempt_closeouts"
        / "sat_old.json"
    )
    immutable_dispatch_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
        "immutable/run_quality_repair_batch/old.json"
    )
    immutable_dispatch_path = profile.workspace_root / immutable_dispatch_ref
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
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
            **_dispatch_refs(
                profile,
                study_id=study_id,
                action_type="run_quality_repair_batch",
                packet_name="current",
                fingerprint=action_fingerprint,
            ),
        },
    )
    dump_json(
        immutable_dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "owner_route": {
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": action_fingerprint,
                    },
                },
            },
        },
    )
    dump_json(
        closeout_path,
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "status": "executed",
            "study_id": study_id,
            "quest_id": study_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_attempt_id": "sat_old",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "stage_packet_ref": immutable_dispatch_ref,
            "closeout_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/stage_attempt_closeouts/sat_old.json",
                immutable_dispatch_ref,
            ],
            "domain_execution": {
                "action_type": "run_quality_repair_batch",
                "domain_owner": "write",
                "execution_status": "executed",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
            "owner_receipt": {
                "status": "executed",
                "owner": "write",
                "quality_authorized": False,
                "submission_authorized": False,
                "current_package_write_authorized": False,
            },
            "route_outcome": "write_repair_delta_recorded",
            "artifact_delta": {
                "status": "executed",
                "meaningful_artifact_delta": True,
                "story_surface_delta_present": True,
                "changed_artifact_refs": [
                    {"path": f"studies/{study_id}/paper/draft.md"},
                ],
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-12T09:12:00+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
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
                            "schema_version": 1,
                            "status": "ready",
                            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                            "next_owner": "write",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "action_fingerprint": action_fingerprint,
                            "allowed_actions": ["run_quality_repair_batch"],
                            "target_surface": {
                                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "write",
                            "next_work_unit": work_unit_id,
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
    assert result["transition_request_candidates"][0]["work_unit_id"] == work_unit_id
    assert result["transition_request_candidates"][0]["work_unit_fingerprint"] == action_fingerprint
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    assert result["stage_route_arbiter_decisions"][0]["decision"] == "opl_transition_readback_required"
    assert result["action_queue"][0]["status"] == "transition_request_pending"


def test_opl_route_owner_gate_current_action_becomes_provider_admission_candidate(
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
    action_fingerprint = f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::run_gate_clearing_batch"
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
            **_dispatch_refs(
                profile,
                study_id=study_id,
                action_type="run_gate_clearing_batch",
                packet_name="owner-gate-current",
                fingerprint=action_fingerprint,
            ),
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-10T10:24:56+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": work_unit_id,
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
                            "next_owner": "one-person-lab",
                            "work_unit_id": work_unit_id,
                            "allowed_actions": ["run_gate_clearing_batch"],
                            "target_surface": {
                                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                                "route_target": "one-person-lab",
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "one-person-lab",
                            "next_work_unit": work_unit_id,
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
    assert candidate["status"] == "transition_request_pending"
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["dispatch_path"] == str(dispatch_path)
    assert candidate["next_executable_owner"] == "gate_clearing_batch"
    assert result["action_queue"][0]["owner"] == "gate_clearing_batch"
    assert result["action_queue"][0]["work_unit_fingerprint"] == action_fingerprint
    assert result["action_queue"][0]["provider_attempt_or_lease_required"] is False


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
            **_dispatch_refs(
                profile,
                study_id=study_id,
                action_type="run_gate_clearing_batch",
                packet_name="top-level-current",
                fingerprint=action_fingerprint,
            ),
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

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    candidates = result["managed_study_opl_transition_request_candidates"]
    assert len(candidates) == 1
    assert candidates[0]["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidates[0]["work_unit_id"] == work_unit_id
    assert candidates[0]["status"] == "transition_request_pending"
    assert candidates[0]["provider_admission_requires_opl_runtime_result"] is True
    assert result["provider_admission_current_control_state"]["provider_admission_pending_count"] == 0
    assert result["provider_admission_current_control_state"]["transition_request_pending_count"] == 1
    assert result["current_execution_evidence"]["transition_request_candidates"] == candidates
    assert result["action_fingerprints"] == [action_fingerprint]


def test_domain_health_diagnostic_retains_pending_over_stale_authorization_closeout_in_top_level_report(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
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
        },
    )
    dump_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "sat_82a2b164657c9b4d0c312db9.closeout.json",
        {
            "surface_kind": "stage_attempt_closeout_packet",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "stage_attempt_id": "sat_82a2b164657c9b4d0c312db9",
            "stage_id": "domain_owner/default-executor-dispatch",
            "status": "closed_with_typed_blocker",
            "outcome": "repeat_suppressed_with_typed_blocker",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "typed_blocker": {
                "surface_kind": "mas_domain_typed_blocker",
                "blocker_kind": "anti_loop_budget_exhausted",
                "reason": "anti_loop_budget_exhausted",
                "blocker_id": "opl_execution_authorization_required",
                "owner": "one-person-lab",
                "write_permitted": False,
            },
            "paper_stage_log": {
                "progress_delta_classification": "typed_blocker",
                "outcome": "typed_blocker_anti_loop_budget_exhausted",
                "changed_paper_surfaces": [],
            },
        },
    )

    def fake_impl(**_: object) -> dict[str, object]:
        candidate = {
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "provider_admission_pending",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "stage_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
                "immutable/run_quality_repair_batch/current.json"
            ),
            "stage_packet_refs": [
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/"
                "immutable/run_quality_repair_batch/current.json"
            ],
            "route_identity_key": _identity_key(study_id, fingerprint),
            "attempt_idempotency_key": _identity_key(study_id, fingerprint),
            "currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "truth_epoch": "truth-event-current",
                "runtime_health_epoch": "runtime-health-current",
            },
            "next_executable_owner": "analysis-campaign",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
        }
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-11T21:28:34+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_opl_provider_admission_candidates": [candidate],
            "provider_admission_pending_count": 1,
            "action_fingerprints": [fingerprint],
            "current_execution_evidence": {
                "provider_admission_candidates": [candidate],
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "owner": "analysis-campaign",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "currentness_basis": {
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "next_owner": "analysis-campaign",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "allowed_actions": ["run_quality_repair_batch"],
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "analysis-campaign",
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

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 1
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert len(result["managed_study_opl_transition_request_candidates"]) == 1
    assert len(result["current_execution_evidence"]["transition_request_candidates"]) == 1
    control = result["provider_admission_current_control_state"]
    assert control["provider_admission_pending_count"] == 0
    assert control["transition_request_pending_count"] == 1
    assert control["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }

from .provider_admission_report_stale_currentness_cases import *  # noqa: F403,F401,E402
