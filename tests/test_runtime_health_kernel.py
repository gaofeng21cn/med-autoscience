from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _kernel():
    return importlib.import_module("med_autoscience.controllers.runtime_health_kernel")


def _opl_lifecycle_payload(sequence: int, payload: dict[str, object]) -> dict[str, object]:
    return {
        **payload,
        "opl_lifecycle_proof_ref": f"opl-stage-attempt://runtime-health-test-{sequence}",
    }


def test_runtime_health_rejects_lifecycle_event_without_opl_proof(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"

    with pytest.raises(ValueError, match="opl_lifecycle_proof_required_for_runtime_lifecycle_event"):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="002-dm-cvd",
            quest_id="002-dm-cvd",
            event_type="recover_attempt",
            payload={"attempt_state": "failed", "failure_reason": "no_live_session"},
            recorded_at="2026-05-01T00:00:00+00:00",
        )

    assert module.read_runtime_health_events(study_root=study_root) == []


def test_runtime_health_lifecycle_event_is_diagnostic_when_opl_proof_backed(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"

    event = module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="recover_attempt",
        payload=_opl_lifecycle_payload(
            1,
            {"attempt_state": "failed", "failure_reason": "no_live_session"},
        ),
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    assert event["payload"]["opl_lifecycle_proof_ref"] == "opl-stage-attempt://runtime-health-test-1"
    assert event["payload"]["lifecycle_authority_owner"] == "one-person-lab"
    assert event["payload"]["mas_runtime_health_event_role"] == "diagnostic_observation"
    assert event["payload"]["attempt_lifecycle_authority"] is False
    assert event["payload"]["retry_or_dead_letter_authority"] is False
    assert event["payload"]["worker_residency_authority"] is False


def test_runtime_health_strict_live_requires_worker_and_active_run_id(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": None,
            "reason": "live_runtime_missing_active_run_id",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="supervisor_tick",
        payload={"supervisor_tick_status": "fresh"},
        recorded_at="2026-05-01T00:01:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "unknown"
    assert snapshot["canonical_runtime_action"] == "probe_runtime_liveness"
    assert snapshot["active_run_id"] is None
    assert "live_worker_requires_active_run_id" in snapshot["blocking_reasons"]


def test_runtime_health_treats_opl_provider_attempt_as_live_worker_signal(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-risk"

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        recorded_at="2026-06-01T08:30:00+00:00",
        status_payload={
            "quest_status": "active",
            "runtime_liveness_audit": {
                "status": "live",
                "source": "opl_current_control_state_provider_attempt",
                "active_run_id": "opl-stage-attempt://sat-live",
                "running_provider_attempt": True,
            },
        },
    )

    assert snapshot["worker_liveness_state"]["state"] == "live"
    assert snapshot["worker_liveness_state"]["worker_running"] is True
    assert snapshot["active_run_id"] == "opl-stage-attempt://sat-live"
    assert snapshot["blocking_reasons"] == []
    assert snapshot["canonical_runtime_action"] == "continue_supervising_runtime"
    assert snapshot["projection_role"] == "mas_runtime_health_diagnostic_publisher"
    assert snapshot["authority"] is False
    projection_metadata = snapshot["projection_metadata"]
    assert projection_metadata["surface_kind"] == "runtime_health_diagnostic_projection_metadata"
    assert projection_metadata["authority"] is False
    assert projection_metadata["fixed_point_runtime_owner"] == "one-person-lab"
    assert projection_metadata["derived_from_event_id"] == snapshot["runtime_health_epoch"]
    assert projection_metadata["observed_generation"] == snapshot["source_signature"]
    assert projection_metadata["lag_status"] == "current"
    assert projection_metadata["runtime_health_epoch_is_currentness_authority"] is False
    assert projection_metadata["diagnostic_publisher_only"] is True
    assert snapshot["source_of_truth_chain"] == [
        "DomainIntent",
        "OPL Command/Event/Outbox/StageRun",
        "MAS OwnerAnswer",
        "Derived Projection",
    ]
    boundary = snapshot["authority_boundary"]
    assert boundary["surface_role"] == "mas_diagnostic_publisher_read_only_projection"
    assert boundary["can_authorize_runtime_currentness"] is False
    assert boundary["can_authorize_supervisor_action"] is False
    assert boundary["can_own_attempt_lifecycle"] is False
    assert boundary["can_own_retry_or_dead_letter"] is False
    assert boundary["can_authorize_worker_residency"] is False
    assert boundary["can_write_opl_current_control_state"] is False
    assert boundary["can_create_opl_outbox_record"] is False
    assert boundary["runtime_health_epoch_is_currentness_authority"] is False
    assert boundary["canonical_runtime_action_is_authority"] is False
    assert boundary["attempt_state_is_lifecycle_authority"] is False
    assert boundary["worker_liveness_is_residency_authority"] is False
    assert boundary["can_authorize_running_progress"] is False
    assert snapshot["projection_only"] is True
    assert snapshot["read_only_diagnostic_projection"] is True
    assert snapshot["body_free_diagnostic_projection"] is True
    assert snapshot["runtime_liveness_authority"] is False
    assert snapshot["reconcile_authority"] is False
    assert snapshot["supervisor_currentness_authority"] is False
    assert snapshot["canonical_runtime_action_is_authority"] is False
    assert snapshot["allowed_controller_actions_are_authority"] is False
    assert snapshot["runtime_action_hint"] == snapshot["canonical_runtime_action"]
    assert snapshot["runtime_action_hint_is_authority"] is False
    assert snapshot["allowed_controller_actions"] == ["read_runtime_status", "open_monitoring_entry"]
    assert snapshot["allowed_controller_action_hints"] != snapshot["allowed_controller_actions"]
    assert snapshot["allowed_controller_action_hints_are_authority"] is False
    assert snapshot["opl_observability_readback_required"] is True
    assert snapshot["opl_current_control_or_stage_run_readback_required"] is True
    assert snapshot["mas_private_attempt_loop_forbidden"] is True
    hint_contract = snapshot["diagnostic_hint_contract"]
    assert hint_contract["hint_only"] is True
    assert hint_contract["canonical_runtime_action_hint"] == snapshot["canonical_runtime_action"]
    assert hint_contract["canonical_runtime_action_is_authority"] is False
    assert hint_contract["opl_observability_readback_required"] is True
    assert hint_contract["opl_current_control_or_stage_run_readback_required"] is True
    assert hint_contract["mas_private_attempt_loop_forbidden"] is True


def test_runtime_health_attempt_retry_and_action_fields_are_diagnostic_hints(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-risk"

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        recorded_at="2026-06-01T08:30:00+00:00",
        status_payload={
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-live-001",
        },
    )

    hint_contract = snapshot["diagnostic_hint_contract"]
    assert hint_contract["hint_only"] is True
    assert hint_contract["attempt_state_hint"] == snapshot["attempt_state"]
    assert hint_contract["retry_budget_remaining_hint"] == snapshot["retry_budget_remaining"]
    assert hint_contract["canonical_runtime_action_hint"] == snapshot["canonical_runtime_action"]
    assert hint_contract["attempt_state_hint_is_lifecycle_authority"] is False
    assert hint_contract["retry_budget_hint_is_lifecycle_authority"] is False
    assert hint_contract["canonical_runtime_action_is_authority"] is False
    assert snapshot["attempt_state_hint"] == snapshot["attempt_state"]
    assert snapshot["retry_budget_remaining_hint"] == snapshot["retry_budget_remaining"]
    assert snapshot["attempt_state_hint_is_lifecycle_authority"] is False
    assert snapshot["retry_budget_remaining_hint_is_lifecycle_authority"] is False
    assert snapshot["canonical_runtime_action_is_authority"] is False
    assert snapshot["provider_admission_authority"] is False
    assert snapshot["provider_admission_pending_count"] == 0
    assert snapshot["provider_admission_candidates"] == []
    assert snapshot["current_executable_owner_action"] is None
    assert snapshot["current_executable_owner_action_authority"] is False
    assert snapshot["running_progress_claim_authority"] is False
    assert snapshot["can_generate_next_action_authority"] is False
    assert snapshot["can_authorize_running_progress"] is False
    assert snapshot["can_create_worker_attempt"] is False
    assert snapshot["can_retry_or_dead_letter"] is False


def test_runtime_health_missing_live_session_recovers_with_stale_run_as_last_known(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        event_type="launch_attempt",
        payload=_opl_lifecycle_payload(1, {"attempt_state": "succeeded", "active_run_id": "run-599e53e9"}),
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
        recorded_at="2026-05-01T00:03:00+00:00",
    )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        event_type="supervisor_tick",
        payload={"supervisor_tick_status": "fresh"},
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "missing_live_session"
    assert snapshot["active_run_id"] is None
    assert snapshot["last_known_run_id"] == "run-599e53e9"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert snapshot["retry_budget_remaining"] == 2


def test_runtime_health_recovery_budget_exhaustion_escalates(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "reason": "quest_marked_running_but_no_live_session",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="002-dm-cvd",
            quest_id="002-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {"attempt_state": "failed", "failure_reason": "no_live_session"},
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
    )

    assert snapshot["attempt_state"] == "escalated"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert snapshot["retry_budget_remaining"] == 0
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]


def test_runtime_health_explicit_relaunch_starts_new_recovery_budget_epoch(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="002-dm-cvd",
            quest_id="002-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "failed",
                    "failure_reason": "quest_marked_running_but_no_live_session",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "failed",
        "decision": "relaunch_stopped",
        "reason": "quest_stopped_explicit_relaunch_requested",
        "opl_lifecycle_proof_ref": "opl-stage-attempt://runtime-health-test-relaunch",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "status": "none",
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    assert snapshot["attempt_state"] == "idle"
    assert snapshot["attempt_count"] == 1
    assert snapshot["retry_budget_remaining"] == 2
    assert snapshot["canonical_runtime_action"] == "continue_supervising_runtime"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_submission_metadata_parking_dominates_stale_recovery_budget(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd-reentry",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "failed",
                    "failure_reason": "quest_marked_running_but_no_live_session",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd-reentry",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "paused",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
            "runtime_liveness_status": "unknown",
            "worker_running": False,
        },
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd-reentry",
    )

    assert snapshot["worker_liveness_state"]["state"] == "not_live"
    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_zero_retry_budget_blocks_recover_runtime_even_without_failed_attempts(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dpcc"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="003-dpcc",
            quest_id="003-dpcc",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "requested",
                    "decision": "resume",
                    "reason": "quest_marked_running_but_no_live_session",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="003-dpcc",
        quest_id="003-dpcc",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        },
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="003-dpcc",
        quest_id="003-dpcc",
    )

    assert snapshot["retry_budget_remaining"] == 0
    assert snapshot["attempt_state"] == "escalated"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]


def test_runtime_health_provider_ready_supervisor_tick_starts_new_recovery_budget_epoch(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="002-dm-cvd",
            quest_id="002-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "failed",
                    "decision": "resume",
                    "reason": "quest_marked_running_but_no_live_session",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "opl_lifecycle_proof_ref": "opl-stage-attempt://runtime-health-test-provider-ready",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "provider_ready": True,
            "worker_ready": True,
            "managed_worker_source_current": True,
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "missing_live_session"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert snapshot["retry_budget_remaining"] == 2
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]
    assert "recover_runtime" in snapshot["allowed_controller_action_hints"]
    assert "recover_runtime" not in snapshot["allowed_controller_actions"]


def test_runtime_health_provider_ready_handoff_starts_new_recovery_budget_epoch(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="002-dm-cvd",
            quest_id="002-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "failed",
                    "decision": "resume",
                    "reason": "quest_marked_running_but_no_live_session",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "opl_lifecycle_proof_ref": "opl-stage-attempt://runtime-health-test-provider-handoff",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_report_path": "/tmp/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_handoff",
            "provider_readiness": {
                "provider_ready": True,
                "worker_ready": True,
                "managed_worker_source_current": True,
                "source": "opl_family_runtime_status",
            },
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "missing_live_session"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert snapshot["retry_budget_remaining"] == 2
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]
    assert "recover_runtime" in snapshot["allowed_controller_action_hints"]
    assert "recover_runtime" not in snapshot["allowed_controller_actions"]


def test_runtime_health_zero_retry_budget_escalates_stopped_controller_guard_recovery_path(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "requested",
                    "decision": "resume",
                    "reason": "quest_stopped_by_controller_guard",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "stopped",
            "runtime_liveness_status": "unknown",
            "worker_running": False,
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
        },
        recorded_at="2026-05-01T00:04:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "not_live"
    assert snapshot["retry_budget_remaining"] == 0
    assert snapshot["attempt_state"] == "escalated"
    assert snapshot["canonical_runtime_action"] == "external_supervisor_required"
    assert "runtime_recovery_retry_budget_exhausted" in snapshot["blocking_reasons"]
    assert "recover_runtime" not in snapshot["allowed_controller_actions"]


def test_runtime_health_append_deduplicates_same_source_signature(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    first = module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="recover_attempt",
        payload=_opl_lifecycle_payload(1, {"attempt_state": "failed", "failure_reason": "same_recovery_attempt"}),
        recorded_at="2026-05-01T00:00:00+00:00",
        source_signature="recover-attempt::same",
    )
    second = module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="recover_attempt",
        payload=_opl_lifecycle_payload(1, {"attempt_state": "failed", "failure_reason": "same_recovery_attempt"}),
        recorded_at="2026-05-01T00:05:00+00:00",
        source_signature="recover-attempt::same",
    )

    events = module.read_runtime_health_events(study_root=study_root)

    assert len(events) == 1
    assert second["event_id"] == first["event_id"]
    assert second["duplicate_replay"] is True


def test_runtime_health_stopped_quest_waits_for_explicit_resume_without_probe(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "unknown",
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
    )

    assert snapshot["worker_liveness_state"]["state"] == "not_live"
    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_liveness_unknown" not in snapshot["blocking_reasons"]


def test_runtime_health_manual_hold_dominates_active_missing_live_session(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
        },
        recorded_at="2026-05-05T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
    )

    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_user_pause_dominates_active_missing_live_session(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_user_paused_requires_explicit_wakeup",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "active_run_id": None,
        },
        recorded_at="2026-05-05T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
    )

    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_explicit_resume_reason_dominates_active_missing_live_session(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "004-dm-cvd"
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "unknown",
            "worker_running": True,
            "active_run_id": None,
        },
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="004-dm-cvd",
        quest_id="004-dm-cvd",
    )

    assert snapshot["attempt_state"] == "awaiting_explicit_resume"
    assert snapshot["canonical_runtime_action"] == "await_explicit_resume"


def test_runtime_health_reconcile_materializes_snapshot_from_status_payload(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "running",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "supervisor_tick_audit": {"status": "fresh"},
        "launch_report_path": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
    }

    shadow = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    assert shadow["canonical_runtime_action"] == "recover_runtime"
    assert not module.runtime_health_snapshot_path(study_root=study_root).exists()

    result = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )

    snapshot_path = module.runtime_health_snapshot_path(study_root=study_root)
    assert snapshot_path.exists()
    persisted = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert result["runtime_health_epoch"] == persisted["runtime_health_epoch"]
    assert persisted["canonical_runtime_action"] == "recover_runtime"
    assert result["appended_event_count"] == 0
    assert result["suppressed_local_runtime_event_persistence"] is True
    assert persisted["suppressed_local_runtime_event_persistence"] is True
    assert module.read_runtime_health_events(study_root=study_root) == []
    assert persisted["projection_metadata"]["authority"] is False
    assert persisted["projection_metadata"]["lag_status"] == "current"
    assert persisted["projection_metadata"]["derived_from_event_id"] == persisted["runtime_health_epoch"]


def test_runtime_health_treats_strict_live_activity_timeout_as_recovery(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "002-dm-cvd"
    status_payload = {
        "study_id": "002-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "002-dm-cvd",
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live-stale",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-live-stale",
            },
        },
        "autonomy_slo": {
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta", "same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
            "last_meaningful_progress": {
                "seconds_since_last_meaningful_progress": 59841,
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_recorded_at": "2026-05-02T11:07:28+00:00",
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="002-dm-cvd",
        quest_id="002-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-02T11:07:29+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "activity_timeout"
    assert snapshot["worker_liveness_state"]["active_run_id"] == "run-live-stale"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert "live_worker_meaningful_artifact_delta_timeout" in snapshot["blocking_reasons"]
    assert "read_churn_without_artifact_delta" in snapshot["blocking_reasons"]


def test_runtime_health_live_new_run_does_not_inherit_stale_recovery_budget(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    for sequence in range(1, 4):
        module.append_runtime_health_event(
            study_root=study_root,
            study_id="001-dm-cvd",
            quest_id="001-dm-cvd",
            event_type="recover_attempt",
            payload=_opl_lifecycle_payload(
                sequence,
                {
                    "attempt_state": "failed",
                    "failure_reason": "quest_marked_running_but_no_live_session",
                    "active_run_id": "run-old",
                },
            ),
            recorded_at=f"2026-05-01T00:0{sequence}:00+00:00",
        )
    module.append_runtime_health_event(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        event_type="runtime_state_observed",
        payload={
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-new",
            "autonomy_slo": {
                "state": "breach",
                "breach_types": ["same_fingerprint_loop"],
            },
        },
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    snapshot = module.rebuild_runtime_health_snapshot(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
    )

    assert snapshot["active_run_id"] == "run-new"
    assert snapshot["last_known_run_id"] == "run-new"
    assert snapshot["worker_liveness_state"]["state"] == "activity_timeout"
    assert snapshot["attempt_state"] == "recovering"
    assert snapshot["canonical_runtime_action"] == "recover_runtime"
    assert snapshot["retry_budget_remaining"] == 3
    assert "runtime_recovery_retry_budget_exhausted" not in snapshot["blocking_reasons"]


def test_runtime_health_does_not_recover_new_live_run_from_stale_slo_window(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    status_payload = {
        "study_id": "001-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "001-dm-cvd",
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-new",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-new",
            },
        },
        "autonomy_slo": {
            "generated_at": "2026-05-01T00:00:00+00:00",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
        },
        "progress_freshness": {
            "activity_timeout": {
                "state": "watching_new_run",
                "new_run_grace": {
                    "active_run_id": "run-new",
                    "observed_at": "2026-05-01T00:05:00+00:00",
                },
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_recorded_at": "2026-05-01T00:05:00+00:00",
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "live"
    assert snapshot["attempt_state"] == "live"
    assert snapshot["canonical_runtime_action"] == "continue_supervising_runtime"
    assert "same_fingerprint_loop" not in snapshot["blocking_reasons"]


def test_runtime_health_uses_status_observation_time_for_new_run_grace(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "001-dm-cvd"
    status_payload = {
        "study_id": "001-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "001-dm-cvd",
        "quest_status": "running",
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-new",
            "runtime_audit": {
                "status": "live",
                "worker_running": True,
                "active_run_id": "run-new",
            },
        },
        "autonomy_slo": {
            "generated_at": "2026-05-01T00:00:00+00:00",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "latest_recorded_at": "2026-05-01T00:05:00+00:00",
        },
    }

    snapshot = module.derive_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-dm-cvd",
        quest_id="001-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert snapshot["worker_liveness_state"]["state"] == "live"
    assert snapshot["attempt_state"] == "live"
    assert snapshot["canonical_runtime_action"] == "continue_supervising_runtime"
    assert "same_fingerprint_loop" not in snapshot["blocking_reasons"]


def test_runtime_health_reconcile_publishes_projection_without_persisting_liveness_events(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dm-cvd"
    status_payload = {
        "study_id": "003-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "003-dm-cvd",
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "status": "none",
                "worker_running": False,
                "interaction_watchdog": {
                    "seconds_since_last_artifact_interact": 10,
                    "seconds_since_active_execution_start": 20,
                },
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "seconds_since_latest_recorded_at": 1,
        },
    }

    first = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    status_payload["runtime_liveness_audit"]["runtime_audit"]["interaction_watchdog"][
        "seconds_since_last_artifact_interact"
    ] = 100
    status_payload["supervisor_tick_audit"]["seconds_since_latest_recorded_at"] = 90
    second = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert first["appended_event_count"] == 0
    assert first["suppressed_local_runtime_event_persistence"] is True
    assert first["suppressed_transient_event_count"] == 2
    assert module.read_runtime_health_events(study_root=study_root) == []
    assert second["appended_event_count"] == 0
    assert second["suppressed_local_runtime_event_persistence"] is True
    assert second["snapshot"]["attempt_count"] == 0


def test_runtime_health_reconcile_suppresses_opl_proof_backed_lifecycle_event_persistence(tmp_path: Path) -> None:
    module = _kernel()
    study_root = tmp_path / "studies" / "003-dm-cvd"
    status_payload = {
        "study_id": "003-dm-cvd",
        "study_root": str(study_root),
        "quest_id": "003-dm-cvd",
        "quest_status": "active",
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "opl_lifecycle_proof_ref": "opl-stage-attempt://runtime-health-dedupe",
        "runtime_liveness_audit": {
            "status": "none",
            "runtime_audit": {
                "status": "none",
                "worker_running": False,
                "interaction_watchdog": {
                    "seconds_since_last_artifact_interact": 10,
                    "seconds_since_active_execution_start": 20,
                },
            },
        },
        "supervisor_tick_audit": {
            "status": "fresh",
            "seconds_since_latest_recorded_at": 1,
        },
    }

    first = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:00:00+00:00",
    )
    status_payload["runtime_liveness_audit"]["runtime_audit"]["interaction_watchdog"][
        "seconds_since_last_artifact_interact"
    ] = 100
    status_payload["supervisor_tick_audit"]["seconds_since_latest_recorded_at"] = 90
    second = module.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="003-dm-cvd",
        quest_id="003-dm-cvd",
        status_payload=status_payload,
        recorded_at="2026-05-01T00:05:00+00:00",
    )

    assert first["appended_event_count"] == 0
    assert first["suppressed_local_runtime_event_persistence"] is True
    assert first["suppressed_transient_event_count"] == 3
    assert "recover_attempt" in first["suppressed_transient_event_types"]
    assert module.read_runtime_health_events(study_root=study_root) == []
    assert second["appended_event_count"] == 0
    assert second["suppressed_local_runtime_event_persistence"] is True
    assert second["snapshot"]["attempt_count"] == 1
