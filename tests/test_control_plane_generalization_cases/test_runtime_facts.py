from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    write_study,
    write_text,
)

def test_profile_sli_summary_separates_active_duplicate_dispatch_from_history() -> None:
    module = importlib.import_module("med_autoscience.controllers.profile_sli")

    summary = module.build_sli_summary(
        {
            "runtime_transition_summary": {
                "event_count": 10,
                "health_status_counts": {"live": 8, "recovering": 2},
                "transition_counts": {"live->recovering": 1, "recovering->live": 1},
            },
            "domain_health_diagnostic_wakeup_dedupe_summary": {
                "status": "dedupe_confirmed",
                "outcome": "skipped_matching_work_unit",
            },
            "gate_blocker_summary": {
                "current_blockers": ["claim_evidence_consistency_failed"],
                "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
            },
            "package_currentness": {"status": "stale"},
        }
    )

    assert summary["runtime_live_ratio"] == 0.8
    assert summary["runtime_recovery_observations"] == 2
    assert summary["duplicate_dispatch_active"] is False
    assert summary["next_work_unit_id"] == "analysis_claim_evidence_repair"
    assert summary["package_stale_is_current_bottleneck"] is False
def test_runtime_worker_activity_normalizes_runtime_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_worker_activity")

    live = module.normalize_activity(
        {
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-123",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-123"},
            },
            "autonomous_runtime_notice": {"browser_url": "http://127.0.0.1:20999"},
        }
    )
    recovering = module.normalize_activity(
        {
            "quest_status": "running",
            "runtime_liveness_status": None,
            "reason": "quest_marked_running_but_no_live_session",
        }
    )

    assert live["worker"] == "runtime_worker"
    assert live["activity_state"] == "running"
    assert live["heartbeat_state"] == "live"
    assert live["active_run_id"] == "run-123"
    assert live["monitoring_url"] == "http://127.0.0.1:20999"
    assert recovering["activity_state"] == "recovering"
    assert recovering["heartbeat_state"] == "missing_live_session"
def test_control_plane_facts_do_not_treat_stale_continuation_run_as_strict_live() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_facts")

    facts = module.resolve_control_plane_facts(
        {
            "quest_status": "active",
            "runtime_liveness_status": "unknown",
            "reason": "quest_marked_running_but_no_live_session",
            "continuation_state": {"quest_status": "running", "active_run_id": "run-stale"},
        },
        supervisor_tick_audit={"status": "stale"},
    )

    assert facts.active_run_id == "run-stale"
    assert facts.active_run_id_source == "continuation_state.active_run_id"
    assert facts.strict_live is False
    assert facts.missing_live_session is True
    assert facts.recovery_pending is True
def test_control_plane_facts_do_not_treat_completed_parked_run_as_strict_live(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_facts")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    run_root = quest_root / ".ds" / "runs" / "run-parked-001"
    run_root.mkdir(parents=True)
    (run_root / "command.json").write_text(
        json.dumps(
            {
                "turn_reason": "auto_continue",
                "turn_mode": "parked",
                "turn_intent": "continue_stage",
            }
        ),
        encoding="utf-8",
    )
    (run_root / "result.json").write_text(
        json.dumps(
            {
                "run_id": "run-parked-001",
                "exit_code": 0,
                "output_text": "No new user message or /resume; staying parked.",
            }
        ),
        encoding="utf-8",
    )

    facts = module.resolve_control_plane_facts(
        {
            "quest_status": "running",
            "quest_root": str(quest_root),
            "runtime_liveness_status": "live",
            "active_run_id": "run-parked-001",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-parked-001",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-parked-001",
                    "worker_running": True,
                },
            },
        },
        supervisor_tick_audit={"status": "fresh"},
    )

    assert facts.strict_live is False
    assert facts.runtime_liveness_status == "parked"
    assert facts.active_run_id is None
    assert facts.active_run_id_source == "completed_parked_auto_continue"
    assert facts.worker_running is False
    assert facts.missing_live_session is False
    assert facts.recovery_pending is False
    assert facts.to_runtime_worker_activity()["activity_state"] == "parked"
def test_control_plane_facts_treat_closeout_continuation_as_parked_not_recovery() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_plane_facts")

    facts = module.resolve_control_plane_facts(
        {
            "quest_status": "active",
            "decision": "lightweight",
            "reason": "entry_mode_not_managed",
            "runtime_liveness_status": "unknown",
            "active_run_id": None,
            "runtime_liveness_audit": {
                "status": "unknown",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "unknown",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_reason": "parked_after_checkpoint_no_new_message",
            },
        },
        supervisor_tick_audit={"status": "fresh"},
    )

    assert facts.runtime_liveness_status == "parked"
    assert facts.reason == "parked_after_checkpoint_no_new_message"
    assert facts.active_run_id is None
    assert facts.active_run_id_source == "continuation_state.parked_closeout"
    assert facts.strict_live is False
    assert facts.missing_live_session is False
    assert facts.recovery_pending is False
    assert facts.to_runtime_worker_activity()["activity_state"] == "parked"
def test_progress_projection_exposes_runtime_worker_activity(monkeypatch, tmp_path: Path) -> None:
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
        minimum_sci_ready_evidence_package=["external_validation", "decision_curve_analysis"],
    )
    study_root = profile.workspace_root / "studies" / "001-risk"
    write_text(study_root / "analysis" / "clean_room_execution" / "00_entry_validation" / "README.md", "# entry\n")
    quest_root = profile.runtime_root / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstudy_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"running","active_run_id":"run-live"}\n')
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
        module.managed_runtime_transport,
        "inspect_quest_live_execution",
        lambda *, runtime_root, quest_id: {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {"worker_running": True, "active_run_id": "run-live"},
            "bash_session_audit": {"status": "live"},
        },
    )

    result = module.progress_projection(profile=profile, study_id="001-risk", include_progress_projection=False)

    legacy_worker_activity_key = "mds" + "_worker_activity"
    assert legacy_worker_activity_key not in result
    assert result["runtime_worker_activity"] == {
        "worker": "runtime_worker",
        "activity_state": "running",
        "heartbeat_state": "live",
        "quest_status": "running",
        "active_run_id": "run-live",
        "monitoring_url": result["autonomous_runtime_notice"]["browser_url"],
        "reason": "quest_already_running",
    }
