from __future__ import annotations

import importlib


def _snapshot(payload: dict[str, object]) -> dict[str, object]:
    module = importlib.import_module("med_autoscience.controllers.domain_authority_snapshot")
    return module.build_authority_snapshot(payload)


def test_authority_snapshot_blocks_dispatch_without_truth_and_health_epochs() -> None:
    snapshot = _snapshot(
        {
            "study_id": "003-dpcc",
            "quest_id": "003-dpcc",
            "study_truth_snapshot": {"canonical_next_action": "resume_same_study_line"},
            "runtime_health_snapshot": {"canonical_runtime_action": "recover_runtime"},
        }
    )

    assert snapshot["surface"] == "authority_snapshot"
    assert snapshot["dispatch_gate"]["state"] == "blocked"
    assert snapshot["route_authorization"]["authorized"] is False
    assert snapshot["canonical_next_action"] == "read_runtime_status"
    assert snapshot["canonical_runtime_action"] == "probe_runtime_liveness"
    assert "study_truth_epoch_missing" in snapshot["blocking_reasons"]
    assert "runtime_health_epoch_missing" in snapshot["blocking_reasons"]


def test_authority_snapshot_fail_closes_non_ai_reviewer_publication_ready() -> None:
    snapshot = _snapshot(
        {
            "study_id": "003-dpcc",
            "quest_id": "003-dpcc",
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-1",
                "canonical_next_action": "finalize_ready",
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-1",
                "canonical_runtime_action": "continue_supervising_runtime",
            },
            "publication_eval": {
                "current_required_action": "submission_ready",
                "assessment_provenance": {"owner": "mechanical_projection"},
            },
        }
    )

    assert snapshot["control_state"] == "blocked_quality_review"
    assert snapshot["canonical_next_action"] == "review_required"
    assert snapshot["dispatch_gate"]["state"] == "blocked"
    assert "publication_eval.ai_reviewer_required" in snapshot["blocking_reasons"]


def test_authority_snapshot_splits_foreground_guard_from_managed_paper_write_authority() -> None:
    snapshot = _snapshot(
        {
            "study_id": "004-invasive",
            "quest_id": "004-invasive",
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-2",
                "canonical_next_action": "direct_paper_line_write",
                "blocking_reasons": [
                    "execution_owner_guard.supervisor_only",
                    "publication_supervisor_state.bundle_tasks_downstream_only",
                ],
                "allowed_controller_actions": [
                    "read_runtime_status",
                    "direct_paper_line_write",
                    "direct_bundle_build",
                ],
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-2",
                "canonical_runtime_action": "continue_supervising_runtime",
            },
        }
    )

    assert snapshot["dispatch_gate"]["state"] == "blocked"
    assert snapshot["route_authorization"]["paper_write_allowed"] is True
    assert snapshot["route_authorization"]["managed_worker_paper_write_allowed"] is True
    assert snapshot["route_authorization"]["foreground_paper_write_allowed"] is False
    assert snapshot["route_authorization"]["bundle_build_allowed"] is False
    assert snapshot["route_authorization"]["foreground_bundle_build_allowed"] is False
    assert "direct_paper_line_write" not in snapshot["allowed_controller_actions"]
    assert "direct_bundle_build" not in snapshot["allowed_controller_actions"]


def test_authority_snapshot_blocks_recovery_when_retry_budget_exhausted() -> None:
    snapshot = _snapshot(
        {
            "study_id": "004-invasive",
            "quest_id": "004-invasive",
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-3",
                "canonical_next_action": "resume_same_study_line",
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-3",
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
                "retry_budget_remaining": 0,
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
        }
    )

    assert snapshot["control_state"] == "blocked_runtime_escalation"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert snapshot["dispatch_gate"]["state"] == "blocked"
    assert snapshot["route_authorization"]["runtime_recovery_allowed"] is False
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]


def test_authority_snapshot_escalates_when_non_recovery_retry_budget_exhausted() -> None:
    snapshot = _snapshot(
        {
            "study_id": "004-invasive",
            "quest_id": "004-invasive",
            "study_truth_snapshot": {
                "truth_epoch": "truth-event-3",
                "canonical_next_action": "resume_same_study_line",
            },
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-3",
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
            },
        }
    )

    assert snapshot["control_state"] == "blocked_runtime_escalation"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert snapshot["dispatch_gate"]["state"] == "blocked"
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]


def test_authority_snapshot_is_embedded_in_status_projection(tmp_path) -> None:
    status_module = importlib.import_module("med_autoscience.controllers.progress_projection")

    status = status_module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "003-dpcc",
            "study_root": str(tmp_path / "studies" / "003-dpcc"),
            "entry_mode": "full_research",
            "execution": {"quest_id": "003-dpcc", "auto_resume": True},
            "quest_id": "003-dpcc",
            "quest_root": str(tmp_path / "runtime" / "quests" / "003-dpcc"),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(tmp_path / "studies" / "003-dpcc" / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
        }
    )
    status.extras["study_truth_snapshot"] = {
        "truth_epoch": "truth-event-4",
        "canonical_next_action": "resume_same_study_line",
    }
    status.extras["runtime_health_snapshot"] = {
        "runtime_health_epoch": "runtime-health-event-4",
        "canonical_runtime_action": "continue_supervising_runtime",
    }
    kernel = importlib.import_module("med_autoscience.controllers.domain_authority_snapshot")
    status.extras["authority_snapshot"] = kernel.build_authority_snapshot(status.to_dict())

    payload = status.to_dict()

    assert payload["authority_snapshot"]["surface"] == "authority_snapshot"
    assert payload["authority_snapshot"]["dispatch_gate"]["state"] == "open"
    assert payload["authority_snapshot"]["authority_refs"]["study_truth"]["epoch"] == "truth-event-4"


def test_retired_study_control_plane_kernel_module_is_not_importable() -> None:
    try:
        importlib.import_module("med_autoscience.controllers.study_control_plane_kernel")
    except ModuleNotFoundError:
        return
    raise AssertionError("retired study_control_plane_kernel compatibility alias must not be restored")
