from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared
from .provider_admission_current_control_cases import _currentness_basis

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_materialized_current_control_keeps_publication_eval_write_repair_after_old_ai_reviewer_closeout(
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
    stale_fingerprint = "sha256:stale-ai-reviewer-closeout"
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
            "dispatch_authority": None,
            "next_executable_owner": "write",
            "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
            "refs": {"dispatch_path": str(dispatch_path)},
            "owner_route": {
                "next_owner": "write",
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "run_quality_repair_batch",
                    "work_unit_fingerprint": "stage-native-next-action::stale-dispatch",
                    "owner_route_currentness_basis": {
                        "truth_epoch": "truth-event-stale",
                        "runtime_health_epoch": "runtime-health-stale",
                        "work_unit_id": "run_quality_repair_batch",
                        "work_unit_fingerprint": "stage-native-next-action::stale-dispatch",
                    },
                },
            },
        },
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
        "dispatch_authority": None,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::003::current-write-repair",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T08:40:00+00:00",
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
                        "status": "closed_with_domain_owner_refs",
                        "stage_closeout_status": "closed_with_domain_owner_refs",
                        "stage_attempt_id": "sat_576b2b902ea0ef671d2764ab",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": "return_to_ai_reviewer_workflow",
                        "work_unit_fingerprint": stale_fingerprint,
                        "action_fingerprint": stale_fingerprint,
                        "outcome": (
                            "closed_with_domain_owner_refs; ai_reviewer_record_materialized; "
                            "provider_completion_is_not_domain_ready"
                        ),
                    }
                ],
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "target_surface": {
                        "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                        "route_target": "write",
                    },
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": _currentness_basis(
                        work_unit_id=work_unit_id,
                        fingerprint=fingerprint,
                        source_eval_id="publication-eval::003::current-write-repair",
                    ),
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
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
    assert result["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert result["provider_admission_candidates"][0]["work_unit_fingerprint"] == fingerprint
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert result["current_execution_envelopes"][study_id]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelopes"][study_id]["next_work_unit"] == work_unit_id


def test_materialized_current_control_retains_publication_eval_write_repair_after_stale_same_identity_closeout(
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
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
            source_eval_id="publication-eval::003::current-write-repair",
        ),
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-12T09:05:00+00:00",
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
                        "execution_status": "blocked",
                        "stage_closeout_status": "blocked",
                        "stage_attempt_id": "sat_f2a9c348f6115825a47715e4",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "outcome": "typed_blocker",
                        "blocked_reason": "medical_paper_readiness_missing",
                        "typed_blocker_reason": "medical_paper_readiness_missing",
                        "typed_blocker": {
                            "blocker_id": "medical_paper_readiness_missing",
                            "blocker_type": "medical_paper_readiness_missing",
                            "owner": "one-person-lab",
                            "write_permitted": False,
                        },
                    }
                ],
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "schema_version": 1,
                    "status": "ready",
                    "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "source_eval_id": "publication-eval::003::current-write-repair",
                    "target_surface": {
                        "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                        "route_target": "write",
                    },
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "currentness_basis": _currentness_basis(
                        work_unit_id=work_unit_id,
                        fingerprint=fingerprint,
                        source_eval_id="publication-eval::003::current-write-repair",
                    ),
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
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
    assert result["provider_admission_candidates"][0]["work_unit_id"] == work_unit_id
    assert result["provider_admission_candidates"][0]["work_unit_fingerprint"] == fingerprint
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "pending_provider_admission": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "pending_provider_admission"
    assert decision["effect"] == "retain_provider_admission_pending"
    assert result["current_execution_envelopes"][study_id]["state_kind"] == "executable_owner_action"
    assert result["current_execution_envelopes"][study_id]["next_work_unit"] == work_unit_id
