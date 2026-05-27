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
            "opl_runtime_owner_handoff_summary": {
                "event_count": 10,
                "status_counts": {"clear": 8, "handoff_required": 2},
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

    assert summary["opl_runtime_owner_handoff_clear_ratio"] == 0.8
    assert summary["opl_runtime_owner_handoff_required_count"] == 2
    assert summary["opl_runtime_owner_handoff_event_count"] == 10
    assert "runtime_live_ratio" not in summary
    assert "runtime_recovery_observations" not in summary
    assert summary["duplicate_dispatch_active"] is False
    assert summary["next_work_unit_id"] == "analysis_claim_evidence_repair"
    assert summary["package_stale_is_current_bottleneck"] is False
def test_opl_runtime_refs_normalizes_domain_activity() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")

    live = module.resolve_opl_runtime_refs(
        {
            "quest_status": "running",
            "opl_current_control_state": {
                "status": "attempt_running",
                "active_run_id": "run-opl-123",
                "supervisor_tick_status": "fresh",
            },
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-123",
                "runtime_audit": {"worker_running": True, "active_run_id": "run-123"},
            },
            "autonomous_runtime_notice": {"browser_url": "http://127.0.0.1:20999"},
        }
    ).to_domain_activity_ref()
    recovering = module.resolve_opl_runtime_refs(
        {
            "quest_status": "running",
            "runtime_liveness_status": None,
            "reason": "quest_marked_running_but_no_live_session",
        }
    ).to_domain_activity_ref()

    assert live["provider_owner"] == "one-person-lab"
    assert live["source"] == "opl_runtime_refs"
    assert live["activity_state"] == "running"
    assert live["heartbeat_state"] == "attempt_running"
    assert live["active_run_id"] == "run-opl-123"
    assert live["monitoring_url"] == "http://127.0.0.1:20999"
    assert recovering["activity_state"] == "recovering"
    assert recovering["heartbeat_state"] == "missing_live_session"
def test_opl_runtime_refs_do_not_treat_stale_continuation_run_as_strict_live() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")

    facts = module.resolve_opl_runtime_refs(
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


def test_opl_runtime_refs_preserve_current_opl_stage_attempt_without_strict_live() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")

    facts = module.resolve_opl_runtime_refs(
        {
            "quest_status": "active",
            "runtime_liveness_status": "live",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": None,
                "runtime_audit": {"worker_running": None, "active_run_id": None},
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": "opl-stage-attempt://sat-current-write",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
        },
        supervisor_tick_audit={"status": "stale"},
    )

    assert facts.active_run_id == "opl-stage-attempt://sat-current-write"
    assert facts.active_run_id_source == "continuation_state.active_run_id"
    assert facts.strict_live is False
    assert facts.missing_live_session is True
    assert facts.recovery_pending is True
    assert facts.to_domain_activity_ref()["active_run_id"] == "opl-stage-attempt://sat-current-write"

def test_opl_runtime_refs_do_not_treat_completed_parked_run_as_strict_live(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")
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

    facts = module.resolve_opl_runtime_refs(
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
    assert facts.to_domain_activity_ref()["activity_state"] == "parked"
def test_opl_runtime_refs_treat_closeout_continuation_as_parked_not_recovery() -> None:
    module = importlib.import_module("med_autoscience.controllers.opl_runtime_refs")

    facts = module.resolve_opl_runtime_refs(
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
    assert facts.to_domain_activity_ref()["activity_state"] == "parked"
def test_progress_projection_exposes_opl_domain_activity_ref(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
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
    result = module.progress_projection(profile=profile, study_id="001-risk", include_progress_projection=False)

    legacy_worker_activity_key = "mds" + "_worker_activity"
    assert legacy_worker_activity_key not in result
    assert not hasattr(module, "managed_runtime" + "_transport")
    assert result["opl_domain_activity_ref"] == {
        "provider_owner": "one-person-lab",
        "source": "opl_runtime_refs",
        "activity_state": "recovering",
        "heartbeat_state": "missing_live_session",
        "quest_status": "running",
        "active_run_id": None,
        "monitoring_url": None,
        "reason": "quest_marked_running_but_no_live_session",
    }
