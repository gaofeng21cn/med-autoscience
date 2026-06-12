from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _currentness_basis(
    *,
    work_unit_id: str,
    fingerprint: str,
    source_eval_id: str = "publication-eval::current",
) -> dict[str, str]:
    return {
        "truth_epoch": f"truth::{fingerprint}",
        "runtime_health_epoch": f"runtime-health::{fingerprint}",
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }


def test_materialized_current_control_retains_pending_after_opl_authorization_work_unit_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
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
        "next_executable_owner": "analysis-campaign",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::002::current-analysis-repair",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T18:35:16+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_closeout_status": "blocked",
                        "execution_status": "blocked",
                        "outcome": "typed_blocker",
                        "stage_attempt_id": "sat_8fb0009e8384954d24ab28cf",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "blocked_reason": "opl_execution_authorization_required",
                        "typed_blocker_reason": "opl_execution_authorization_required",
                        "typed_blocker": {
                            "blocker_id": "opl_execution_authorization_required",
                            "owner": "one-person-lab",
                            "write_permitted": False,
                        },
                        "blocker_context": {
                            "observed_stage_attempt_work_unit_id": work_unit_id,
                            "dispatch_canonical_work_unit_id": (
                                "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                            ),
                            "work_unit_id_matched": False,
                        },
                        "remaining_blockers": [
                            "opl_work_unit_binding_mismatch",
                        ],
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "analysis-campaign",
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
    assert len(result["provider_admission_candidates"]) == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["studies"][0]["provider_admission_pending_count"] == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"


def test_materialized_current_control_retains_pending_after_opl_authorization_blocker_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
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
        "next_executable_owner": "analysis-campaign",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::002::current-analysis-repair",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-11T18:48:30+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": [
                    {
                        "surface_kind": "stage_attempt_closeout_packet",
                        "status": "blocked",
                        "stage_closeout_status": "blocked",
                        "execution_status": "blocked",
                        "outcome": (
                            "blocked:{'blocker_id': 'opl_execution_authorization_required', "
                            "'owner': 'one-person-lab'}"
                        ),
                        "stage_attempt_id": None,
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "typed_blocker": {
                            "blocker_id": "blocked",
                            "owner": "one-person-lab",
                            "write_permitted": False,
                        },
                        "problem_summary": (
                            "run_quality_repair_batch ended with typed blocker "
                            "{'blocker_id': 'opl_execution_authorization_required', "
                            "'owner': 'one-person-lab'}."
                        ),
                        "remaining_blockers": [
                            "{'blocker_id': 'opl_execution_authorization_required', "
                            "'owner': 'one-person-lab', 'write_permitted': False}"
                        ],
                    }
                ],
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "analysis-campaign",
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
    assert len(result["provider_admission_candidates"]) == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    expected_identity_key = f"provider-admission::{study_id}::{fingerprint}"
    candidate = result["provider_admission_candidates"][0]
    assert candidate["route_identity_key"] == expected_identity_key
    assert candidate["attempt_idempotency_key"] == expected_identity_key
    action = result["action_queue"][0]
    assert action["action_id"] == f"provider-admission::{study_id}::run_quality_repair_batch"
    assert action["route_identity_key"] == expected_identity_key
    assert action["attempt_idempotency_key"] == expected_identity_key
    assert action["idempotency_key"] == expected_identity_key
    assert action["owner_route"]["idempotency_key"] == expected_identity_key
    assert action["owner_route"]["source_refs"]["route_identity_key"] == expected_identity_key
    assert action["handoff_packet"]["route_identity_key"] == expected_identity_key
    assert action["handoff_packet"]["attempt_idempotency_key"] == expected_identity_key
    assert result["studies"][0]["provider_admission_identity_key"] == expected_identity_key
    assert result["studies"][0]["current_execution_envelope"]["route_identity_key"] == expected_identity_key
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert decision["route_identity_key"] == expected_identity_key


def test_report_current_control_retains_pending_after_opl_authorization_work_unit_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
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
            "owner_route": {
                "next_owner": "analysis-campaign",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": fingerprint,
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "owner_route_currentness_basis": {
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_eval_id": "publication-eval::002::current",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth-event-000040",
                        "runtime_health_epoch": "runtime-health-event-006843",
                    },
                },
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-11T18:35:16+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "analysis-campaign",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "currentness_basis": {
                                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                                "source_eval_id": "publication-eval::002::current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "truth_epoch": "truth-event-000040",
                                "runtime_health_epoch": "runtime-health-event-006843",
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                            "next_owner": "analysis-campaign",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "source_eval_id": "publication-eval::002::current",
                            "action_type": "run_quality_repair_batch",
                            "allowed_actions": ["run_quality_repair_batch"],
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "analysis-campaign",
                            "next_work_unit": work_unit_id,
                        },
                        "progress_first_monitoring_summary": {
                            "latest_terminal_stage": {
                                "stage_attempt_id": "sat_8fb0009e8384954d24ab28cf",
                                "stage_id": "domain_owner/default-executor-dispatch",
                                "action_type": "run_quality_repair_batch",
                                "status": "blocked",
                                "stage_name": (
                                    "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                                ),
                                "outcome": "typed_blocker",
                                "progress_delta_classification": "typed_blocker",
                                "blocked_reason": "opl_execution_authorization_required",
                                "remaining_blockers": [
                                    "opl_work_unit_binding_mismatch",
                                ],
                                "blocker_context": {
                                    "observed_stage_attempt_work_unit_id": work_unit_id,
                                    "dispatch_canonical_work_unit_id": (
                                        "dm002_current_publication_hardening_after_current_ai_reviewer_eval"
                                    ),
                                    "work_unit_id_matched": False,
                                },
                                "source_path": (
                                    "/workspace/studies/002-dm-china-us-mortality-attribution/"
                                    "artifacts/supervision/consumer/default_executor_execution/latest.json"
                                ),
                            },
                        },
                    }
                }
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert result["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"


def test_report_current_control_marks_opl_authorization_blocker_closeout_as_mismatch(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::497d1260db522f01"
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
            "owner_route": {
                "next_owner": "analysis-campaign",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": fingerprint,
                "source_refs": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "owner_route_currentness_basis": {
                        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                        "source_eval_id": "publication-eval::002::current",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth-event-000040",
                        "runtime_health_epoch": "runtime-health-event-006843",
                    },
                },
            },
        },
    )

    result = module._materialize_report_provider_admission_current_control_state(
        profile=profile,
        apply=False,
        report={
            "scanned_at": "2026-06-11T18:48:30+00:00",
            "managed_study_opl_provider_admission_candidates": [],
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "study_id": study_id,
                        "quest_id": study_id,
                        "current_work_unit": {
                            "surface_kind": "current_work_unit",
                            "status": "executable_owner_action",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "analysis-campaign",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "currentness_basis": {
                                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                                "source_eval_id": "publication-eval::002::current",
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "truth_epoch": "truth-event-000040",
                                "runtime_health_epoch": "runtime-health-event-006843",
                            },
                        },
                        "current_executable_owner_action": {
                            "surface_kind": "current_executable_owner_action",
                            "status": "ready",
                            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                            "next_owner": "analysis-campaign",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "source_eval_id": "publication-eval::002::current",
                            "action_type": "run_quality_repair_batch",
                            "allowed_actions": ["run_quality_repair_batch"],
                        },
                        "current_execution_envelope": {
                            "state_kind": "executable_owner_action",
                            "owner": "analysis-campaign",
                            "next_work_unit": work_unit_id,
                        },
                        "progress_first_monitoring_summary": {
                            "latest_terminal_stage": {
                                "stage_attempt_id": None,
                                "stage_id": "domain_owner/default-executor-dispatch",
                                "action_type": "run_quality_repair_batch",
                                "status": "blocked",
                                "stage_name": "analysis_claim_evidence_repair",
                                "outcome": (
                                    "blocked:{'blocker_id': "
                                    "'opl_execution_authorization_required'}"
                                ),
                                "progress_delta_classification": "typed_blocker",
                                "problem_summary": (
                                    "run_quality_repair_batch ended with typed blocker "
                                    "{'blocker_id': 'opl_execution_authorization_required'}."
                                ),
                                "remaining_blockers": [
                                    "{'blocker_id': 'opl_execution_authorization_required', "
                                    "'owner': 'one-person-lab'}"
                                ],
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": fingerprint,
                                "action_fingerprint": fingerprint,
                                "source_path": (
                                    "/workspace/studies/002-dm-china-us-mortality-attribution/"
                                    "artifacts/supervision/consumer/default_executor_execution/latest.json"
                                ),
                            },
                        },
                    }
                }
            },
        },
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 1
    assert len(result["provider_admission_candidates"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
