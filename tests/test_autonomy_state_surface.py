from __future__ import annotations

import importlib


def _surface(payload: dict[str, object]) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.controllers.autonomy_state_surface")
    return module.build_autonomy_state_surface(payload)


def test_retired_control_plane_modules_are_not_importable() -> None:
    retired_modules = (
        "med_autoscience.controllers.control_plane_state",
        "med_autoscience.controllers.control_plane_reconciler",
        "med_autoscience.controllers.control_plane_facts",
        "med_autoscience.controllers.runtime_worker_activity",
    )
    for module_name in retired_modules:
        try:
            importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        raise AssertionError(f"retired module compatibility alias must not be restored: {module_name}")


def test_autonomy_state_surface_matrix_exposes_canonical_fields() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_state_surface")

    catalog = module.autonomy_state_surface_catalog()

    assert {
        "live",
        "running",
        "no_live",
        "recovering",
        "blocked_human",
        "blocked_external",
        "blocked_opl_runtime",
    } <= set(catalog)
    for state, spec in catalog.items():
        assert spec["state"] == state
        assert isinstance(spec["owner"], str)
        assert isinstance(spec["auto_recovery_allowed"], bool)
        assert isinstance(spec["resource_release_expected"], bool)
        assert isinstance(spec["long_write_turn_allowed"], bool)
        assert "MAS/MDS" not in spec["operator_summary"]
        assert "MedDeepScientist" not in spec["operator_summary"]


def test_autonomy_state_surface_uses_opl_runtime_refs_for_strict_live_projection() -> None:
    surface = _surface(
        {
            "study_id": "001-live",
            "quest_id": "quest-001",
            "quest_status": "running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-live-001",
        }
    )

    assert surface["current_state"] == "live"
    assert surface["owner"] == "mas_controller"
    assert surface["long_write_turn_allowed"] is True
    assert surface["opl_runtime_refs"]["strict_live"] is True
    assert surface["opl_runtime_refs"]["active_run_id"] == "run-live-001"


def test_autonomy_state_surface_uses_opl_runtime_refs_for_no_live_projection() -> None:
    surface = _surface(
        {
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "reason": "quest_marked_running_but_no_live_session",
        }
    )

    assert surface["current_state"] == "no_live"
    assert surface["owner"] == "mas_controller"
    assert surface["auto_recovery_allowed"] is True
    assert surface["resource_release_expected"] is False
    assert surface["opl_runtime_refs"]["missing_live_session"] is True
    assert surface["canonical_next_action"] == surface["authority_snapshot"]["canonical_next_action"]
    assert surface["canonical_next_action"] == "read_runtime_status"
    assert surface["domain_next_action_projection"]["canonical_next_action"] == "request_opl_runtime_owner"


def test_domain_next_action_projection_prioritizes_recovery_over_pending_work_unit() -> None:
    surface = _surface(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_status": "active",
            "runtime_liveness_status": "none",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
            },
            "continuation_state": {
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "parked_after_checkpoint_no_new_message",
                "active_run_id": None,
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                },
            },
        }
    )

    assert surface["current_state"] == "no_live"
    assert surface["canonical_next_action"] == surface["authority_snapshot"]["canonical_next_action"]
    assert surface["canonical_next_action"] == "read_runtime_status"
    assert surface["domain_next_action_projection"]["work_unit_pending"] is True
    assert surface["domain_next_action_projection"]["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert surface["domain_next_action_projection"]["canonical_next_action"] == "request_opl_runtime_owner"
    assert surface["auto_runtime_parked"]["parked"] is False


def test_autonomy_state_surface_canonical_action_uses_authority_snapshot() -> None:
    surface = _surface(
        {
            "study_id": "003-control-plane",
            "quest_id": "quest-control-plane",
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "reason": "quest_marked_running_but_no_live_session",
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-control-plane",
                "canonical_next_action": "resume_same_study_line",
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-control-plane",
                "canonical_runtime_action": "recover_runtime",
            },
        }
    )

    assert surface["authority_snapshot"]["canonical_next_action"] == "resume_same_study_line"
    assert surface["canonical_next_action"] == "resume_same_study_line"
    assert surface["authority_epoch"] == "truth-event-control-plane"
    assert surface["domain_next_action_projection"]["canonical_next_action"] == "request_opl_runtime_owner"


def test_autonomy_state_surface_maps_user_parked_to_blocked_human() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "active",
        }
    )

    assert surface["current_state"] == "blocked_human"
    assert surface["owner"] == "human_operator"
    assert surface["auto_recovery_allowed"] is False
    assert surface["resource_release_expected"] is True
    assert surface["auto_runtime_parked"]["parked_state"] == "package_ready_handoff"


def test_autonomy_state_surface_maps_external_upstream_to_external_owner() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "quest_status": "retrying",
            "mds_failure_diagnosis": {
                "diagnosis_code": "codex_upstream_quota_error",
                "retriable": False,
                "problem": "account balance is negative",
            },
        }
    )

    assert surface["current_state"] == "blocked_external"
    assert surface["owner"] == "external_runtime_or_operator"
    assert surface["auto_recovery_allowed"] is False
    assert surface["resource_release_expected"] is True
    assert surface["runtime_failure_classification"]["external_blocker"] is True


def test_autonomy_state_surface_maps_runtime_handoff_to_opl_owner() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "quest_status": "failed",
            "mds_failure_diagnosis": {
                "diagnosis_code": "provider_invalid_params",
                "retriable": False,
            },
        }
    )

    assert surface["current_state"] == "blocked_opl_runtime"
    assert surface["owner"] == "one_person_lab_runtime_owner"
    assert surface["auto_recovery_allowed"] is False
    assert surface["resource_release_expected"] is True


def test_autonomy_state_surface_does_not_project_gate_blocker_as_user_parked() -> None:
    surface = _surface(
        {
            "decision": "blocked",
            "reason": "quest_completion_requested_before_publication_gate_clear",
            "quest_status": "stopped",
            "current_state_summary": {
                "runtime_health_status": "inactive",
                "runtime_decision": "blocked",
                "runtime_reason": "quest_completion_requested_before_publication_gate_clear",
            },
        }
    )

    assert surface["current_state"] == "queued"
    assert surface["owner"] == "mas_controller"
    assert surface["auto_runtime_parked"]["parked"] is False
