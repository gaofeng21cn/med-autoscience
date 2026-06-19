from __future__ import annotations

import importlib
from pathlib import Path

from .shared import make_status_payload


def test_runtime_health_diagnostic_recovery_hint_cannot_rewrite_status_without_opl_readback(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.runtime_health_dominance"
    )
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    study_root = tmp_path / "studies" / "001-risk"
    status = typed_surface.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(study_root),
            quest_status="running",
            decision="noop",
            reason="quest_already_running",
            runtime_liveness_audit={
                "status": "live",
                "active_run_id": "local-run-without-opl-readback",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "local-run-without-opl-readback",
                    "worker_running": True,
                },
            },
            autonomy_slo={
                "state": "breach",
                "breach_types": ["no_meaningful_progress"],
                "active_run_id": "local-run-without-opl-readback",
                "generated_at": "2026-06-01T08:00:00+00:00",
            },
            progress_freshness={
                "activity_timeout": {
                    "state": "timed_out",
                    "new_run_grace": {"active_run_id": "local-run-without-opl-readback"},
                },
            },
        )
    )

    module._record_runtime_health_dominance(
        status=status,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        recorded_at="2026-06-01T09:00:00+00:00",
    )

    assert status.decision is typed_surface.StudyRuntimeDecision.NOOP
    assert status.reason is typed_surface.StudyRuntimeReason.QUEST_ALREADY_RUNNING
    gate = status.extras["runtime_health_decision_gate"]
    assert gate["surface_kind"] == "runtime_health_diagnostic_consumer_gate"
    assert gate["runtime_owner"] == "one-person-lab"
    assert gate["mas_role"] == "read_only_diagnostic_consumer"
    assert gate["decision_authorized"] is False
    assert gate["suppressed_reason"] == "opl_runtime_readback_required_for_runtime_health_decision"
    assert gate["identity_bound_opl_readback_required"] is True
    assert gate["required_runtime_identity"] == ["local-run-without-opl-readback"]
    assert gate["readback_runtime_identities"] == []
    assert gate["matched_runtime_identity"] == []
    assert gate["readback_sources"] == []
    assert gate["unbound_opl_ref_can_authorize_decision"] is False
    assert gate["runtime_health_hint_only"] is True
    assert gate["can_generate_next_action_authority"] is False
    assert gate["can_authorize_running_progress"] is False
    assert gate["can_authorize_runtime_currentness"] is False
    assert status.extras["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"
    assert status.extras["runtime_health_snapshot"]["canonical_runtime_action_is_authority"] is False
    assert "runtime_recovery_lifecycle" not in status.extras


def test_runtime_health_recovery_decision_rejects_cross_identity_opl_readback(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.runtime_health_dominance"
    )
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    study_root = tmp_path / "studies" / "001-risk"
    status = typed_surface.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(study_root),
            quest_status="running",
            decision="noop",
            reason="quest_already_running",
            runtime_liveness_status="live",
            worker_running=True,
            active_run_id="opl-stage-attempt://runtime-timeout-current",
            opl_current_control_state={
                "surface_kind": "opl_current_control_state_study_handoff",
                "status": "live",
                "active_stage_attempt_id": "opl-stage-attempt://runtime-timeout-stale",
                "running_provider_attempt": True,
            },
            autonomy_slo={
                "state": "breach",
                "breach_types": ["no_meaningful_progress"],
                "active_run_id": "opl-stage-attempt://runtime-timeout-current",
                "generated_at": "2026-06-01T08:00:00+00:00",
            },
            progress_freshness={
                "activity_timeout": {
                    "state": "timed_out",
                    "new_run_grace": {"active_run_id": "opl-stage-attempt://runtime-timeout-current"},
                },
            },
        )
    )

    module._record_runtime_health_dominance(
        status=status,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        recorded_at="2026-06-01T09:00:00+00:00",
    )

    assert status.decision is typed_surface.StudyRuntimeDecision.NOOP
    assert status.reason is typed_surface.StudyRuntimeReason.QUEST_ALREADY_RUNNING
    gate = status.extras["runtime_health_decision_gate"]
    assert gate["decision_authorized"] is False
    assert gate["suppressed_reason"] == "opl_runtime_readback_required_for_runtime_health_decision"
    assert gate["identity_bound_opl_readback_required"] is True
    assert gate["required_runtime_identity"] == [
        "opl-stage-attempt://runtime-timeout-current",
        "runtime-timeout-current",
    ]
    assert gate["readback_runtime_identities"] == [
        "opl-stage-attempt://runtime-timeout-stale",
        "runtime-timeout-stale",
    ]
    assert gate["matched_runtime_identity"] == []
    assert gate["readback_sources"] == ["opl_current_control_state"]
    assert gate["unbound_opl_ref_can_authorize_decision"] is False
    assert "runtime_recovery_lifecycle" not in status.extras


def test_runtime_health_recovery_decision_rejects_top_level_opl_readback_claim(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.runtime_health_dominance"
    )
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    study_root = tmp_path / "studies" / "001-risk"
    status = typed_surface.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(study_root),
            quest_status="running",
            decision="noop",
            reason="quest_already_running",
            runtime_liveness_status="live",
            worker_running=True,
            active_run_id="opl-stage-attempt://runtime-timeout-top-level",
            source="opl_current_control_state_provider_attempt",
            running_provider_attempt=True,
            active_stage_attempt_id="opl-stage-attempt://runtime-timeout-top-level",
            autonomy_slo={
                "state": "breach",
                "breach_types": ["no_meaningful_progress"],
                "active_run_id": "opl-stage-attempt://runtime-timeout-top-level",
                "generated_at": "2026-06-01T08:00:00+00:00",
            },
            progress_freshness={
                "activity_timeout": {
                    "state": "timed_out",
                    "new_run_grace": {"active_run_id": "opl-stage-attempt://runtime-timeout-top-level"},
                },
            },
        )
    )

    module._record_runtime_health_dominance(
        status=status,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        recorded_at="2026-06-01T09:00:00+00:00",
    )

    assert status.decision is typed_surface.StudyRuntimeDecision.NOOP
    assert status.reason is typed_surface.StudyRuntimeReason.QUEST_ALREADY_RUNNING
    gate = status.extras["runtime_health_decision_gate"]
    assert gate["decision_authorized"] is False
    assert gate["required_runtime_identity"] == [
        "opl-stage-attempt://runtime-timeout-top-level",
        "runtime-timeout-top-level",
    ]
    assert gate["readback_runtime_identities"] == []
    assert gate["matched_runtime_identity"] == []
    assert gate["readback_sources"] == []
    assert gate["unbound_opl_ref_can_authorize_decision"] is False
    assert "runtime_recovery_lifecycle" not in status.extras


def test_runtime_health_recovery_decision_requires_opl_current_control_readback(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.runtime_health_dominance"
    )
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    study_root = tmp_path / "studies" / "001-risk"
    status = typed_surface.ProgressProjectionStatus.from_payload(
        make_status_payload(
            study_root=str(study_root),
            quest_status="running",
            decision="noop",
            reason="quest_already_running",
            runtime_liveness_status="live",
            worker_running=True,
            active_run_id="opl-stage-attempt://runtime-timeout-001",
            opl_current_control_state={
                "surface_kind": "opl_current_control_state_study_handoff",
                "status": "live",
                "active_stage_attempt_id": "opl-stage-attempt://runtime-timeout-001",
                "running_provider_attempt": True,
            },
            autonomy_slo={
                "state": "breach",
                "breach_types": ["no_meaningful_progress"],
                "active_run_id": "opl-stage-attempt://runtime-timeout-001",
                "generated_at": "2026-06-01T08:00:00+00:00",
            },
            progress_freshness={
                "activity_timeout": {
                    "state": "timed_out",
                    "new_run_grace": {"active_run_id": "opl-stage-attempt://runtime-timeout-001"},
                },
            },
        )
    )

    module._record_runtime_health_dominance(
        status=status,
        study_root=study_root,
        study_id="001-risk",
        quest_id="quest-001",
        recorded_at="2026-06-01T09:00:00+00:00",
    )

    assert status.decision is typed_surface.StudyRuntimeDecision.BLOCKED
    assert status.reason is typed_surface.StudyRuntimeReason.QUEST_WAITING_OPL_RUNTIME_OWNER_ROUTE
    gate = status.extras["runtime_health_decision_gate"]
    assert gate["decision_authorized"] is True
    assert gate["decision_source"] == "opl_runtime_readback"
    assert gate["suppressed_reason"] is None
    assert gate["identity_bound_opl_readback_required"] is True
    assert gate["required_runtime_identity"] == [
        "opl-stage-attempt://runtime-timeout-001",
        "runtime-timeout-001",
    ]
    assert gate["readback_runtime_identities"] == [
        "opl-stage-attempt://runtime-timeout-001",
        "runtime-timeout-001",
    ]
    assert gate["matched_runtime_identity"] == [
        "opl-stage-attempt://runtime-timeout-001",
        "runtime-timeout-001",
    ]
    assert gate["readback_sources"] == ["opl_current_control_state"]
    assert gate["unbound_opl_ref_can_authorize_decision"] is False
    assert status.extras["runtime_recovery_lifecycle"]["state"] == "parked_requires_resume"
