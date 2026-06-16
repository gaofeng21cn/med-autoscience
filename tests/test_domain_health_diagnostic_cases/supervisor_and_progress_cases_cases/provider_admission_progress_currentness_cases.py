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


def test_runtime_scan_preserves_fresh_progress_provider_admission_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_scan = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = helpers.write_study(profile.workspace_root, study_id, quest_id=study_id)
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:current-progress-provider-admission"
    dispatch_path = (
        study_root
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
        "next_executable_owner": "gate_clearing_batch",
        "dispatch_path": str(dispatch_path),
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": True,
        "owner_route_current": True,
        "authority_boundary": {
            "can_write_current_owner_delta": True,
            "legacy_diagnostic": "kept",
        },
        "stage_transition_authority_boundary": {
            "stage_transition_authority": "legacy-local-runner",
            "intent_can_write_stage_current_pointer": True,
            "legacy_diagnostic": "kept",
        },
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
        ),
    }

    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": work_unit_id,
            },
            "current_executable_owner_action": {
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "provider_admission_candidates": [candidate],
            "provider_admission_pending_count": 1,
            "paper_recovery_state": {
                "phase": "admission_pending",
                "next_safe_action": {
                    "kind": "admit_provider_attempt",
                    "provider_admission_allowed": True,
                },
            },
        },
    )

    result = runtime_scan._provider_admission_candidates_for_status(
        profile=profile,
        study_root=study_root,
        status_payload={"study_id": study_id, "quest_id": study_id},
        refresh_currentness=True,
    )

    assert len(result) == 1
    retained = result[0]
    assert retained["study_id"] == candidate["study_id"]
    assert retained["action_type"] == candidate["action_type"]
    assert retained["work_unit_id"] == candidate["work_unit_id"]
    assert retained["work_unit_fingerprint"] == candidate["work_unit_fingerprint"]
    assert retained["provider_completion_is_domain_completion"] is False
    authority_boundary = retained["authority_boundary"]
    assert authority_boundary["legacy_diagnostic"] == "kept"
    assert authority_boundary["surface_kind"] == "opl_provider_admission_candidate"
    assert authority_boundary["can_write_current_owner_delta"] is False
    assert authority_boundary["can_mark_provider_attempt_running"] is False
    stage_boundary = retained["stage_transition_authority_boundary"]
    assert stage_boundary["legacy_diagnostic"] == "kept"
    assert stage_boundary["producer_kind"] == "runtime_provider"
    assert stage_boundary["intent_kind"] == "provider_observation"
    assert stage_boundary["stage_transition_authority"] == "one-person-lab"
    assert stage_boundary["intent_can_write_stage_current_pointer"] is False
    assert stage_boundary["intent_can_write_stage_run_terminal_state"] is False
    assert stage_boundary["intent_can_publish_current_owner_delta"] is False
    assert stage_boundary["intent_can_write_domain_truth"] is False
    assert stage_boundary["intent_can_create_owner_receipt"] is False
    assert stage_boundary["intent_can_create_typed_blocker"] is False


def test_runtime_scan_preserves_fresh_progress_transition_request_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_scan = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = helpers.write_study(profile.workspace_root, study_id, quest_id=study_id)
    work_unit_id = "complete_medical_paper_readiness_surface"
    fingerprint = "sha256:current-progress-transition-request"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "complete_medical_paper_readiness_surface.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "complete_medical_paper_readiness_surface",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "MedAutoScience",
        "dispatch_path": str(dispatch_path),
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
        "provider_completion_is_domain_completion": False,
        "owner_route_current": True,
    }

    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "MedAutoScience",
                "next_work_unit": work_unit_id,
            },
            "current_executable_owner_action": {
                "status": "ready",
                "next_owner": "MedAutoScience",
                "action_type": "complete_medical_paper_readiness_surface",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "transition_request_candidates": [candidate],
            "transition_request_pending_count": 1,
            "provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
        },
    )

    result = runtime_scan._provider_admission_candidates_for_status(
        profile=profile,
        study_root=study_root,
        status_payload={"study_id": study_id, "quest_id": study_id},
        refresh_currentness=True,
    )

    assert len(result) == 1
    retained = result[0]
    assert retained["status"] == "transition_request_pending"
    assert retained["study_id"] == study_id
    assert retained["action_type"] == "complete_medical_paper_readiness_surface"
    assert retained["work_unit_id"] == work_unit_id
    assert retained["work_unit_fingerprint"] == fingerprint
    assert retained["provider_attempt_or_lease_required"] is False
    assert retained["provider_admission_requires_opl_runtime_result"] is True
    assert retained["provider_completion_is_domain_completion"] is False
