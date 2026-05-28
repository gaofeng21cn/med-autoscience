from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def test_scan_domain_routes_apply_safe_actions_releases_idle_workspace_daemon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "stopped",
            "runtime_health_snapshot": {"attempt_state": "idle"},
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "current_stage": "publication_supervision",
            "paper_stage": "bundle_stage_ready",
            "supervision": {"active_run_id": None},
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
    )

    assert result["workspace_daemon_lifecycle"]["released"] is False
    assert result["workspace_daemon_lifecycle"]["reason"] == "opl_provider_liveness_owner_required"
    assert result["workspace_daemon_lifecycle"]["typed_blocker"]["owner"] == "one-person-lab"


def test_scan_domain_routes_projects_opl_provider_readiness_from_owner_surface(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "active",
            "runtime_health_snapshot": {"attempt_state": "escalated"},
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "current_stage": "publication_supervision",
            "paper_stage": "publishability_gate_blocked",
            "supervision": {"active_run_id": None},
        },
    )
    monkeypatch.setattr(
        module.opl_provider_attempts,
        "current_provider_readiness",
        lambda **_: {
            "surface_kind": "opl_provider_readiness_projection",
            "source": "opl_family_runtime_status",
            "provider_kind": "temporal",
            "provider_ready": True,
            "worker_ready": True,
            "managed_worker_source_current": True,
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    readiness = result["provider_readiness"]
    assert readiness["source"] == "opl_family_runtime_status"
    assert readiness["provider_ready"] is True
    assert readiness["worker_ready"] is True
    assert readiness["managed_worker_source_current"] is True
    assert readiness["provider_completion_is_domain_ready"] is False
    assert readiness["can_write_domain_truth"] is False
    assert readiness["can_authorize_publication_ready"] is False


def test_scan_domain_routes_uses_current_provider_readiness_for_same_tick_runtime_health(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    for sequence in range(1, 4):
        runtime_health_kernel.append_runtime_health_event(
            study_root=study_root,
            study_id=study_id,
            quest_id=study_id,
            event_type="recover_attempt",
            payload={
                "attempt_state": "failed",
                "decision": "resume",
                "failure_reason": "quest_marked_running_but_no_live_session",
                "active_run_id": None,
            },
            recorded_at=f"2026-05-28T10:4{sequence}:00+00:00",
        )
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(
        json.dumps(
            {
                "surface": "opl_current_control_state_handoff",
                "generated_at": "2026-05-28T10:45:00+00:00",
                "studies": [
                    {
                        "study_id": study_id,
                        "runtime_health": {
                            "attempt_state": "escalated",
                            "retry_budget_remaining": 0,
                            "canonical_runtime_action": "external_supervisor_required",
                            "blocking_reasons": [
                                "quest_marked_running_but_no_live_session",
                                "runtime_recovery_retry_budget_exhausted",
                            ],
                        },
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "quest_status": "active",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "parked",
                "runtime_audit": {"worker_running": False},
            },
            "supervisor_tick_audit": {
                "status": "stale",
                "required": True,
                "latest_recorded_at": "2026-05-28T10:49:00+00:00",
                "seconds_since_latest_recorded_at": 1880,
                "reason": "opl_current_control_state_handoff_stale",
            },
            "runtime_health_snapshot": {
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
            },
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": study_id,
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None},
            "authority_snapshot": {
                "control_state": "blocked_runtime_escalation",
                "canonical_runtime_action": "external_supervisor_required",
                "blocking_reasons": [
                    "quest_marked_running_but_no_live_session",
                    "runtime_recovery_retry_budget_exhausted",
                ],
                "dispatch_gate": {
                    "state": "blocked",
                    "dispatch_allowed": False,
                    "blocking_reasons": [
                        "quest_marked_running_but_no_live_session",
                        "runtime_recovery_retry_budget_exhausted",
                    ],
                },
                "route_authorization": {"runtime_recovery_allowed": False},
            },
            "ai_repair_lifecycle": {
                "surface": "ai_repair_lifecycle",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": study_id,
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "top_action": {
                    "action_type": "controller_repair",
                    "owner": "mas_controller",
                    "repair_kind": "analysis_claim_evidence_redrive",
                    "auto_apply_allowed": True,
                },
            },
        },
    )
    monkeypatch.setattr(module.opl_provider_attempts, "live_provider_attempt_for_study", lambda **_: None)
    monkeypatch.setattr(
        module.opl_provider_attempts,
        "current_provider_readiness",
        lambda **_: {
            "surface_kind": "opl_provider_readiness_projection",
            "source": "opl_family_runtime_status",
            "provider_kind": "temporal",
            "provider_ready": True,
            "worker_ready": True,
            "managed_worker_source_current": True,
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    health = result["studies"][0]["runtime_health"]
    assert health["attempt_state"] == "recovering"
    assert health["retry_budget_remaining"] == 2
    assert health["canonical_runtime_action"] == "recover_runtime"
    assert health["blocking_reasons"] == ["quest_marked_running_but_no_live_session"]
    assert health["supervisor_state"]["status"] == "fresh"
    assert health["supervisor_state"]["latest_recorded_at"] == result["generated_at"]
    assert result["studies"][0]["blocked_reason"] != "runtime_recovery_retry_budget_exhausted"
    assert result["studies"][0]["blocked_reason"] == "opl_stage_attempt_admission_required"
    assert result["studies"][0]["owner_route"]["owner_reason"] == "opl_stage_attempt_admission_required"


def test_scan_domain_routes_observe_mode_does_not_release_workspace_daemon(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "003-endocrine-burden-followup", quest_id="quest-nf")

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "quest_id": "quest-nf",
            "quest_status": "stopped",
            "publication_eval": {"assessment_provenance": {"owner": "ai_reviewer"}},
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": "003-endocrine-burden-followup",
            "paper_stage": "bundle_stage_ready",
            "supervision": {"active_run_id": None},
        },
    )
    result = module.scan_domain_routes(
        profile=profile,
        study_ids=("003-endocrine-burden-followup",),
        apply_safe_actions=False,
    )

    assert result["workspace_daemon_lifecycle"]["released"] is False
    assert result["workspace_daemon_lifecycle"]["reason"] == "safe_actions_not_enabled"
