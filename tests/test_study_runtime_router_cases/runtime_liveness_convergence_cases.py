from __future__ import annotations

from .shared import *  # noqa: F403

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import _clear_readiness_report, make_profile, write_study, write_text


def _managed_runtime_transport(module: object):
    return module.managed_runtime_transport


def test_progress_projection_projects_active_no_live_stale_tick_as_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"active"}\n')
    write_text(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "recorded_at": "2026-04-10T09:00:00+00:00",
                "health_status": "live",
                "runtime_decision": "noop",
                "runtime_reason": "quest_already_running",
                "quest_status": "running",
                "runtime_liveness_status": "live",
                "worker_running": True,
                "active_run_id": "run-old",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "none",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    _patch_decision_supervisor_tick_now(
        monkeypatch,
        decision_module,
        lambda: decision_module.datetime.fromisoformat("2026-04-10T09:30:00+00:00"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "publication gate remains blocked.",
        },
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    _assert_opl_runtime_owner_route_block(result)
    assert result["runtime_health_epoch"]
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"
    assert result["runtime_health_snapshot"]["worker_liveness_state"]["state"] == "missing_live_session"
    assert result["progress_projection"]["current_stage"] == "managed_runtime_recovering"
    assert result["progress_projection"]["runtime_health_epoch"] == result["runtime_health_epoch"]
    assert result["progress_projection"]["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"
    refreshed_runtime_supervision = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )
    assert refreshed_runtime_supervision["health_status"] == "recovering"
    assert refreshed_runtime_supervision["active_run_id"] is None
    assert refreshed_runtime_supervision["runtime_health_epoch"] == result["runtime_health_epoch"]
    assert refreshed_runtime_supervision["canonical_runtime_action"] == "recover_runtime"


def test_persisted_explicit_resume_runtime_health_blocks_active_no_live_recovery(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    runtime_health_kernel = importlib.import_module("med_autoscience.controllers.runtime_health_kernel")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "parked_after_checkpoint_no_new_message",
            }
        )
        + "\n",
    )
    runtime_health_kernel.reconcile_runtime_health_snapshot_from_status_payload(
        study_root=study_root,
        study_id="001-risk",
        quest_id="001-risk",
        status_payload={
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "study_root": str(study_root),
            "quest_status": "stopped",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
            "runtime_liveness_status": "unknown",
        },
        recorded_at="2026-04-10T08:00:00+00:00",
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "unknown",
                "source": "quest_session_runtime_audit",
                "active_run_id": None,
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    _patch_decision_supervisor_tick_now(
        monkeypatch,
        decision_module,
        lambda: decision_module.datetime.fromisoformat("2026-04-10T09:30:00+00:00"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "publication gate remains blocked.",
        },
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    assert result["decision"] == "blocked"
    assert result["reason"] == "quest_stopped_requires_explicit_rerun"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "await_explicit_resume"
    assert result["runtime_health_snapshot"]["attempt_state"] == "awaiting_explicit_resume"
    refreshed_runtime_supervision = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )
    assert refreshed_runtime_supervision["health_status"] == "inactive"
    assert refreshed_runtime_supervision["canonical_runtime_action"] == "await_explicit_resume"


def test_supervisor_status_preserves_preinspected_liveness_and_worker_activity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        '{"status":"running","active_run_id":"run-live"}\n',
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live",
            "runner_live": True,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "quest_session_runtime_audit",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    _patch_decision_supervisor_tick_now(
        monkeypatch,
        decision_module,
        lambda: decision_module.datetime.fromisoformat("2026-04-10T09:30:00+00:00"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "publication gate remains blocked.",
        },
    )

    result = module.progress_projection(profile=profile, study_id="001-risk", entry_mode="supervisor")

    assert result["decision"] == "lightweight"
    assert result["reason"] == "entry_mode_not_managed"
    assert result["active_run_id"] == "run-live"
    assert result["runtime_liveness_audit"]["status"] == "live"
    assert result["runtime_liveness_audit"]["active_run_id"] == "run-live"
    legacy_worker_activity_key = "mds" + "_worker_activity"
    assert legacy_worker_activity_key not in result
    assert result["runtime_worker_activity"]["activity_state"] == "running"
    assert result["runtime_worker_activity"]["active_run_id"] == "run-live"
    assert result["progress_projection"]["supervision"]["active_run_id"] == "run-live"


def test_live_worker_with_stale_artifact_delta_is_recovery_despite_live_audit(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps({"status": "running", "active_run_id": "run-live-stale"}) + "\n",
    )
    write_text(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        json.dumps(
            {
                "surface": "autonomy_progress_slo_status",
                "schema_version": 1,
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "state": "breach",
                "breach_types": ["read_churn_without_artifact_delta"],
                "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
                "mds_progress_markers": {
                    "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                    "meaningful_artifact_delta_kind": "paper_bundle",
                },
                "ai_doctor_request_required": True,
                "ai_doctor_state": "request_ready",
                "quality_gate_relaxation_allowed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": True,
            "status": "live",
            "source": "combined_runner_or_bash_session",
            "active_run_id": "run-live-stale",
            "runner_live": True,
            "bash_live": False,
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-stale",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    _patch_decision_supervisor_tick_now(
        monkeypatch,
        decision_module,
        lambda: decision_module.datetime.fromisoformat("2026-05-02T11:00:00+00:00"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "status": "blocked",
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": [],
            "controller_stage_note": "publication gate remains blocked.",
        },
    )

    result = module.progress_projection(profile=profile, study_id="001-risk")

    assert result["runtime_liveness_audit"]["status"] == "live"
    assert result["decision"] == "noop"
    assert result["reason"] == "quest_already_running"
    assert result["runtime_health_snapshot"]["worker_liveness_state"]["state"] == "activity_timeout"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"
    assert result["control_plane_snapshot"]["canonical_runtime_action"] == "continue_supervising_runtime"
    assert result["control_plane_snapshot"]["route_authorization"]["runtime_recovery_allowed"] is False
    assert result["control_plane_snapshot"]["activity_timeout_owner_action"] == "request_owner_progress"
    assert "recover_runtime" not in result["control_plane_snapshot"]["allowed_controller_actions"]
    assert result["progress_projection"]["current_stage"] == "managed_runtime_recovering"
    assert result["progress_projection"]["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"


def test_live_worker_missing_active_run_id_enters_controlled_recovery(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed around CVD-related mortality.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine", "Cardiovascular Diabetology"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"active"}\n')
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(
        _managed_runtime_transport(module),
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "ok": False,
            "status": "unknown",
            "source": "combined_runner_or_bash_session",
            "active_run_id": None,
            "runner_live": False,
            "bash_live": False,
            "liveness_guard_reason": "live_runtime_missing_active_run_id",
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": None,
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
            "bash_session_audit": {
                "ok": True,
                "status": "none",
                "session_count": 0,
                "live_session_count": 0,
                "live_session_ids": [],
            },
        },
    )
    result = module.progress_projection(profile=profile, study_id="001-risk")

    assert result["decision"] == "resume"
    assert result["reason"] == "quest_marked_running_but_no_live_session"
    assert result["runtime_health_snapshot"]["canonical_runtime_action"] == "recover_runtime"
