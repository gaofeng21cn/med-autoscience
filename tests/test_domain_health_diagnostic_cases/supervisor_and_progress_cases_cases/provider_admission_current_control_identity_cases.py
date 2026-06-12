from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_materialized_current_control_suppresses_weak_provider_admission_identity(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[
            {
                "surface": "opl_provider_admission_candidate",
                "schema_version": 1,
                "status": "provider_admission_pending",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::weak",
                "action_fingerprint": "publication-blockers::weak",
                "next_executable_owner": "analysis-campaign",
                "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
                "provider_attempt_or_lease_required": True,
                "provider_completion_is_domain_completion": False,
            }
        ],
        generated_at="2026-06-12T10:12:00+00:00",
        apply=False,
        scanned_studies=[],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "weak_provider_admission_identity": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "weak_provider_admission_identity"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "weak_provider_admission_identity"


def test_materialized_current_control_ignores_stale_not_running_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
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
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "truth_epoch": "truth-event-current",
            "runtime_health_epoch": "runtime-health-current",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T10:18:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": True,
                "active_stage_attempt_id": "sat_stale_not_running",
                "active_workflow_id": "wf_stale_not_running",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "runtime_health": {
                    "health_status": "stopped",
                    "runtime_liveness_status": "not_running",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    assert result["stage_route_arbiter_decisions"][0]["decision"] == "pending_provider_admission"


def test_fingerprintless_stop_loss_closeout_does_not_consume_new_currentness_identity(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    fingerprint = "current-ai-reviewer-gate-replay::003::new-source-eval"
    dispatch_path = (
        profile.workspace_root
        / "studies"
        / study_id
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "dispatch_path": str(dispatch_path),
        "next_executable_owner": "gate_clearing_batch",
        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "truth_epoch": "truth-event-new",
            "runtime_health_epoch": "runtime-health-new",
            "source_eval_id": "publication-eval::003::new-source-eval",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T10:24:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_closeout_status": "blocked",
                        "execution_status": "blocked",
                        "outcome": "typed_blocker_anti_loop_budget_exhausted",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "typed_blocker": {
                            "blocker_id": "anti_loop_budget_exhausted",
                            "owner": "one-person-lab",
                            "write_permitted": False,
                        },
                        "owner_route_currentness_basis": {
                            "truth_epoch": "truth-event-old",
                            "runtime_health_epoch": "runtime-health-old",
                            "source_eval_id": "publication-eval::003::old-source-eval",
                            "work_unit_id": work_unit_id,
                        },
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "progress_currentness.current_executable_owner_action",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    assert result["stage_route_arbiter_decisions"][0]["decision"] == "pending_provider_admission"
