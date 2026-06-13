from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_stale_report_provider_admission_candidate_is_suppressed_by_fresh_progress_currentness(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = profile.studies_root / study_id
    write_dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    current_work_unit_id = "medical_prose_write_repair"
    current_fingerprint = "gate-replay-route-back::write::publication-blockers::0915410f804b3697"
    dump_json(
        write_dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "write",
            "required_output_surface": (
                "canonical manuscript story-surface delta or "
                "typed blocker:manuscript_story_surface_delta_missing"
            ),
            "refs": {"dispatch_path": str(write_dispatch_path)},
        },
    )
    stale_gate_work_unit = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    stale_gate_fingerprint = (
        f"study-progress-current-owner-ticket::{study_id}::{stale_gate_work_unit}::"
        "run_gate_clearing_batch"
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-10T11:55:00+00:00",
            "managed_study_opl_provider_admission_candidates": [
                {
                    "surface": "opl_provider_admission_candidate",
                    "schema_version": 1,
                    "status": "provider_admission_pending",
                    "source": "mas_opl_runtime_owner_handoff.provider_admission_identity",
                    "execution_ref": str(
                        profile.workspace_root
                        / "runtime"
                        / "artifacts"
                        / "supervision"
                        / "opl_current_control_state"
                        / "latest.json"
                    ),
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": stale_gate_work_unit,
                    "work_unit_fingerprint": stale_gate_fingerprint,
                    "action_fingerprint": stale_gate_fingerprint,
                    "dispatch_path": str(
                        study_root
                        / "artifacts"
                        / "supervision"
                        / "consumer"
                        / "default_executor_dispatches"
                        / "run_gate_clearing_batch.json"
                    ),
                    "next_executable_owner": "finalize",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "provider_attempt_or_lease_required": True,
                    "provider_completion_is_domain_completion": False,
                    "owner_route_current": True,
                }
            ],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "schema_version": 1,
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "stage_id": "publication_supervision",
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": current_work_unit_id,
                            "work_unit_fingerprint": current_fingerprint,
                            "action_fingerprint": current_fingerprint,
                            "currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": current_work_unit_id,
                                "work_unit_fingerprint": current_fingerprint,
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "schema_version": 1,
                            "status": "ready",
                            "source": "study_progress.next_forced_delta.owner_action",
                            "next_owner": "write",
                            "work_unit_id": current_work_unit_id,
                            "action_type": "run_quality_repair_batch",
                            "allowed_actions": ["run_quality_repair_batch"],
                            "required_delta_kind": "review_current_paper_delta",
                            "target_surface": {
                                "route_target": "write",
                                "surface_ref": (
                                    "canonical manuscript story-surface delta or "
                                    "typed blocker:manuscript_story_surface_delta_missing"
                                ),
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "write",
                            "next_work_unit": current_work_unit_id,
                            "typed_blocker": None,
                            "parked_state": None,
                        },
                    },
                },
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert [candidate["action_type"] for candidate in result["provider_admission_candidates"]] == [
        "run_quality_repair_batch"
    ]
    assert result["provider_admission_candidates"][0]["work_unit_id"] == current_work_unit_id
    assert result["provider_admission_candidates"][0]["action_fingerprint"] == current_fingerprint
    assert [action["action_type"] for action in result["action_queue"]] == ["run_quality_repair_batch"]
    assert result["studies"][0]["handoff_scan_status"] == "provider_admission_from_mas_handoff"
    assert result["studies"][0]["current_execution_envelope"]["owner"] == "write"
    assert result["studies"][0]["current_execution_envelope"]["next_work_unit"] == current_work_unit_id


def test_domain_blocked_recovery_state_suppresses_progress_currentness_provider_admission(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = profile.studies_root / study_id
    action_type = "run_quality_repair_batch"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / f"{action_type}.json"
    )
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "analysis-campaign",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-13T13:18:02+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "schema_version": 1,
                            "status": "typed_blocker",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "analysis-campaign",
                            "state": {
                                "state_kind": "typed_blocker",
                                "typed_blocker": {
                                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                                    "owner": "analysis-campaign",
                                },
                            },
                            "currentness_basis": {
                                "truth_epoch": "truth-event-current",
                                "runtime_health_epoch": "runtime-health-current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "schema_version": 1,
                            "status": "ready",
                            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                            "next_owner": "analysis-campaign",
                            "action_type": action_type,
                            "allowed_actions": [action_type],
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                        },
                        "current_execution_envelope": {
                            "state_kind": "typed_blocker",
                            "owner": "analysis-campaign",
                            "next_work_unit": None,
                        },
                        "paper_recovery_state": {
                            "phase": "domain_blocked",
                            "conditions": [
                                {
                                    "condition": "current_work_unit_typed_blocker",
                                    "blocker_type": "stage_packet_not_current_selected_dispatch",
                                }
                            ],
                            "next_safe_action": {
                                "kind": "resolve_typed_blocker",
                                "owner": "analysis-campaign",
                                "provider_admission_allowed": False,
                            },
                            "suppressed_surfaces": [
                                "current_executable_owner_action",
                                "provider_admission_candidates",
                            ],
                        },
                    },
                },
            },
            "managed_study_actions": [
                {
                    "study_id": study_id,
                    "decision": "blocked",
                    "reason": "stage_packet_not_current_selected_dispatch",
                    "paper_recovery_state": {
                        "phase": "domain_blocked",
                        "next_safe_action": {
                            "kind": "resolve_typed_blocker",
                            "owner": "analysis-campaign",
                            "provider_admission_allowed": False,
                        },
                        "suppressed_surfaces": [
                            "current_executable_owner_action",
                            "provider_admission_candidates",
                        ],
                    },
                }
            ],
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["candidate_count"] == 0
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert study["current_work_unit"]["status"] == "typed_blocker"
    assert study["current_execution_envelope"]["state_kind"] == "typed_blocker"


def test_same_tick_materialized_candidate_requires_explicit_current_identity(
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
            "required_output_surface": "canonical manuscript story-surface delta",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-13T01:10:00+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "schema_version": 1,
                            "status": "ready",
                            "source": "study_progress.next_forced_delta.owner_action",
                            "next_owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "allowed_actions": ["run_quality_repair_batch"],
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "write",
                            "next_work_unit": "medical_prose_write_repair",
                            "source": "progress_currentness.current_executable_owner_action",
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
                            "action_type": "run_quality_repair_batch",
                            "dispatch_status": "ready",
                            "dispatch_authority": "consumer_default_executor_dispatch",
                            "dispatch_path": str(dispatch_path),
                            "next_executable_owner": "write",
                            "required_output_surface": "canonical manuscript story-surface delta",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": "publication-blockers::stale-or-unbound",
                            "action_fingerprint": "publication-blockers::stale-or-unbound",
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
    assert result["current_execution_envelopes"][study_id] | {
        "typed_blocker": None,
        "parked_state": None,
    } == {
        "state_kind": "executable_owner_action",
        "owner": "write",
        "next_work_unit": "medical_prose_write_repair",
        "typed_blocker": None,
        "parked_state": None,
        "source": "progress_currentness.current_executable_owner_action",
    }


def test_provider_admission_current_control_retains_unscanned_handoff_as_audit_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    retained_study_id = "002-dm-china-us-mortality-attribution"
    scanned_study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    latest_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    retained_action = {
        "study_id": retained_study_id,
        "quest_id": retained_study_id,
        "action_id": "provider-admission::dm002::stale",
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "request_owner": "write",
        "work_unit_id": "stale_write_repair",
        "work_unit_fingerprint": "sha256:stale-dm002-write",
    }
    dump_json(
        latest_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-11T10:00:00+00:00",
            "studies": [
                {
                    "study_id": retained_study_id,
                    "quest_id": retained_study_id,
                    "handoff_scan_status": "provider_admission_from_mas_handoff",
                    "action_queue": [retained_action],
                }
            ],
            "action_queue": [retained_action],
            "provider_admission_pending_count": 1,
        },
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[],
        generated_at="2026-06-12T03:00:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": scanned_study_id,
                "quest_id": scanned_study_id,
                "handoff_scan_status": "scanned",
                "action_queue": [],
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["action_queue"] == []
    assert result["queue_history"]["provider_admission_pending_count"] == 0
    retained = next(
        study for study in result["studies"] if study["study_id"] == retained_study_id
    )
    assert retained["retained_unscanned_study"] is True
    assert retained["active_provider_admission_allowed"] is False
    assert retained["action_queue"] == []
    assert retained["unscanned_action_queue_retained_for_audit"] == [retained_action]
    assert result["unscanned_handoff_retention"] == {
        "surface_kind": "provider_admission_current_control_unscanned_handoff_retention",
        "retained_unscanned_study_ids": [retained_study_id],
        "active_action_suppressed_count": 2,
        "active_queue_semantics": "scanned_studies_only",
        "retention_semantics": "audit_only",
    }


def test_domain_health_diagnostic_suppresses_stale_candidate_when_fresh_current_work_unit_is_typed_blocker(
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
    stale_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
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
        candidate = {
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "provider_admission_pending",
            "source": "default_executor_execution",
            "execution_ref": str(
                study_root
                / "artifacts"
                / "supervision"
                / "consumer"
                / "default_executor_execution"
                / "latest.json"
            ),
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "dispatch_path": str(dispatch_path),
            "currentness_basis": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": stale_fingerprint,
                "truth_epoch": "truth-event-stale-candidate",
                "runtime_health_epoch": "runtime-health-stale-candidate",
            },
            "blocked_reason": "opl_execution_authorization_required",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
        }
        typed_blocker = {
            "blocker_id": "anti_loop_budget_exhausted",
            "blocker_type": "anti_loop_budget_exhausted",
            "blocked_reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "source_ref": str(
                study_root
                / "artifacts"
                / "supervision"
                / "consumer"
                / "default_executor_execution"
                / "latest.json"
            ),
        }
        return {
            "schema_version": 1,
            "scanned_at": "2026-06-12T04:17:57+00:00",
            "runtime_root": str(profile.runtime_root),
            "managed_study_opl_provider_admission_candidates": [candidate],
            "provider_admission_pending_count": 1,
            "action_fingerprints": [stale_fingerprint],
            "current_execution_evidence": {
                "provider_admission_candidates": [candidate],
                "progress_currentness": {
                    study_id: {
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "schema_version": 1,
                            "status": "typed_blocker",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": None,
                            "action_fingerprint": None,
                            "state": {
                                "state_kind": "typed_blocker",
                                "typed_blocker": typed_blocker,
                                "stale_queue_or_handoff_can_override": False,
                            },
                        },
                        "current_execution_envelope": {
                            "state_kind": "typed_blocker",
                            "owner": "one-person-lab",
                            "next_work_unit": None,
                            "typed_blocker": typed_blocker,
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
    assert result["managed_study_opl_provider_admission_candidates"] == []
    assert result["current_execution_evidence"]["provider_admission_candidates"] == []
    assert result["action_fingerprints"] == []
    control = result["provider_admission_current_control_state"]
    assert control["provider_admission_pending_count"] == 0
    assert control["provider_admission_candidates"] == []
    assert control["action_queue"] == []
    assert control["stage_route_arbiter"]["decision_counts"] == {
        "current_typed_blocker_precedes_provider_admission": 1,
    }
    assert control["stage_route_arbiter_decisions"][0]["effect"] == (
        "suppress_provider_admission_pending"
    )
