from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _touch(path: Path, timestamp: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    os.utime(path, (timestamp, timestamp))


def test_study_cycle_profiler_builds_timing_profile_and_ignores_latest_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    study_root.mkdir(parents=True)
    quest_root.mkdir(parents=True)
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "study_id: 001-risk",
                "quest_id: quest-001",
                f"runtime_root: {workspace_root / 'ops' / 'med-deepscientist' / 'runtime' / 'quests'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "20260424T235500Z.json",
        {
            "emitted_at": "2026-04-24T23:55:00+00:00",
            "task_id": "task-001",
            "study_id": "001-risk",
            "task_intent": "revision intake",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "20260425T000000Z.json",
        {
            "recorded_at": "2026-04-25T00:00:00+00:00",
            "health_status": "recovering",
            "runtime_reason": "quest_marked_running_but_no_live_session",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "20260425T001000Z.json",
        {
            "recorded_at": "2026-04-25T00:10:00+00:00",
            "health_status": "live",
            "runtime_reason": "quest_already_running",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:10:00+00:00",
            "health_status": "live",
            "runtime_reason": "quest_already_running",
        },
    )
    for index in range(2):
        _write_json(
            study_root / "artifacts" / "controller_decisions" / f"20260425T002{index}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:2{index}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "route back to analysis-campaign until claim evidence is clear",
            },
        )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:30:00+00:00",
            "status": "blocked",
            "blockers": ["claim_evidence_consistency_failed"],
            "recommended_actions": [
                {
                    "action_type": "bounded_analysis",
                    "route_target": "analysis-campaign",
                    "reason": "claim evidence repair",
                }
            ],
        },
    )
    _touch(study_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_000)

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="001-risk",
        study_root=None,
        since="2026-04-24T23:50:00+00:00",
    )

    assert profile_payload["study_id"] == "001-risk"
    assert profile_payload["quest_id"] == "quest-001"
    assert profile_payload["category_windows"]["runtime_supervision"]["event_count"] == 2
    assert profile_payload["runtime_transition_summary"]["health_status_counts"] == {
        "live": 1,
        "recovering": 1,
    }
    assert profile_payload["controller_decision_fingerprints"]["top_repeats"][0]["count"] == 2
    assert profile_payload["gate_blocker_summary"]["current_blockers"] == ["claim_evidence_consistency_failed"]
    assert profile_payload["package_currentness"]["status"] == "stale"
    assert profile_payload["step_latest_times"]["task_intake"] == "2026-04-24T23:55:00+00:00"
    assert profile_payload["step_timings"][0] == {
        "from_step": "task_intake",
        "to_step": "run_start",
        "from_at": "2026-04-24T23:55:00+00:00",
        "to_at": "2026-04-25T00:00:00+00:00",
        "duration_seconds": 300,
    }
    assert profile_payload["current_state_summary"]["runtime_health_status"] == "live"
    assert profile_payload["eta_confidence_band"]["classification"] == "claim_evidence"
    assert profile_payload["sli_summary"]["runtime_live_ratio"] == 0.5
    assert profile_payload["sli_summary"]["next_work_unit_id"] == "analysis_claim_evidence_repair"
    assert profile_payload["autonomy_incident_candidates"][0]["incident_type"] == "runtime_recovery_churn"
    assert [item["bottleneck_id"] for item in profile_payload["bottlenecks"]] == [
        "runtime_recovery_churn",
        "repeated_controller_decision",
        "publication_gate_blocked",
    ]


def test_study_cycle_profiler_uses_current_manual_finishing_state_over_window_churn(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "004-ready"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-004"
    study_root.mkdir(parents=True)
    quest_root.mkdir(parents=True)
    (study_root / "runtime_binding.yaml").write_text(
        "\n".join(
            [
                "study_id: 004-ready",
                "quest_id: quest-004",
                f"runtime_root: {workspace_root / 'ops' / 'med-deepscientist' / 'runtime' / 'quests'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "20260425T000000Z.json",
        {
            "recorded_at": "2026-04-25T00:00:00+00:00",
            "health_status": "recovering",
            "runtime_reason": "quest_marked_running_but_no_live_session",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:20:00+00:00",
            "health_status": "inactive",
            "runtime_decision": "blocked",
            "runtime_reason": "quest_waiting_for_submission_metadata",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:15:00+00:00",
            "gaps": [
                {
                    "severity": "optional",
                    "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                }
            ],
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "generated_at": "2026-04-25T00:20:00+00:00",
            "status": "clear",
            "allow_write": True,
            "blockers": [],
            "supervisor_phase": "bundle_stage_ready",
            "current_required_action": "continue_bundle_stage",
        },
    )
    _touch(study_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_000)

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="004-ready",
        study_root=None,
        since="2026-04-24T23:50:00+00:00",
    )

    assert profile_payload["current_state_summary"]["state"] == "manual_finishing"
    assert profile_payload["gate_blocker_summary"]["current_blockers"] == []
    assert profile_payload["eta_confidence_band"]["classification"] == "manual_finishing"
    assert profile_payload["bottlenecks"] == []


def test_study_cycle_profiler_does_not_treat_control_refresh_as_package_drift(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    control_report = workspace_root / "ops" / "runtime" / "quests" / "003-dpcc" / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    _write_json(control_report, {"generated_at": "2026-04-25T00:20:00+00:00"})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:30:00+00:00",
            "gaps": [{"summary": "claim_evidence_consistency_failed", "evidence_refs": [str(control_report)]}],
        },
    )
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_777_000_000)
    _touch(control_report, 1_777_000_100)
    _touch(study_root / "artifacts" / "publication_eval" / "latest.json", 1_777_000_100)

    profile_payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    assert profile_payload["package_currentness"]["status"] == "fresh"
    assert profile_payload["package_currentness"]["status_reason"] == "content_authority_not_newer_than_current_package"
    assert profile_payload["package_currentness"]["control_surface_latest_mtime"] == "2026-04-24T03:08:20+00:00"
    assert "stale_current_package" not in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }


def test_study_cycle_profiler_marks_package_stale_from_new_content_evidence_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    paper_root = workspace_root / "ops" / "runtime" / "quests" / "003-dpcc" / ".ds" / "worktrees" / "paper-main" / "paper"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:30:00+00:00",
            "gaps": [{"summary": "stale_submission_minimal_authority", "evidence_refs": [str(paper_root)]}],
        },
    )
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_777_000_000)
    _touch(paper_root / "paper_line_state.json", 1_777_000_180)
    _touch(study_root / "artifacts" / "publication_eval" / "latest.json", 1_777_000_020)

    profile_payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    assert profile_payload["package_currentness"]["status"] == "stale"
    assert profile_payload["package_currentness"]["status_reason"] == "content_authority_newer_than_current_package"
    assert profile_payload["package_currentness"]["stale_seconds"] == 180
    assert profile_payload["package_currentness"]["authority_source"]["path"] == str(paper_root.resolve())
    assert "stale_current_package" in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }


def test_study_cycle_profiler_suppresses_repeated_decision_after_work_unit_dedupe(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    for minute in (10, 11):
        _write_json(
            study_root / "artifacts" / "controller_decisions" / f"20260425T00{minute}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:{minute}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "same blocker fingerprint",
            },
        )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:12:00+00:00",
            "outcome": "skipped_matching_work_unit",
            "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
            "work_unit_dispatch_key": "publication-blockers::abc::analysis_claim_evidence_repair::run_gate_clearing_batch",
        },
    )

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="003-dpcc",
        study_root=None,
        since="2026-04-25T00:00:00+00:00",
    )

    assert profile_payload["controller_decision_fingerprints"]["top_repeats"][0]["count"] == 2
    assert profile_payload["runtime_watch_wakeup_dedupe_summary"]["status"] == "dedupe_confirmed"
    assert "repeated_controller_decision" not in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }
    assert "dedupe-controller-dispatch" not in {
        item["recommendation_id"] for item in profile_payload["optimization_recommendations"]
    }


def test_study_cycle_profiler_treats_concrete_work_unit_dispatch_as_not_controller_churn(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    for minute in (10, 11):
        _write_json(
            study_root / "artifacts" / "controller_decisions" / f"20260425T00{minute}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:{minute}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "same route but new blocker fingerprint",
            },
        )
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json",
        {
            "recorded_at": "2026-04-25T00:10:54+00:00",
            "outcome": "dispatched",
            "reason": "outer-loop wakeup dispatched an autonomous controller decision",
            "work_unit_dispatch_key": "publication-blockers::new::analysis_claim_evidence_repair::run_gate_clearing_batch",
            "work_unit_fingerprint": "publication-blockers::new",
        },
    )

    profile_payload = module.profile_study_cycle(
        profile=profile,
        study_id="003-dpcc",
        study_root=None,
        since="2026-04-25T00:00:00+00:00",
    )

    assert profile_payload["runtime_watch_wakeup_dedupe_summary"]["status"] == "work_unit_dispatched"
    assert "repeated_controller_decision" not in {
        item["bottleneck_id"] for item in profile_payload["bottlenecks"]
    }
    assert "dedupe-controller-dispatch" not in {
        item["recommendation_id"] for item in profile_payload["optimization_recommendations"]
    }


def test_study_cycle_profiler_renders_markdown(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")

    rendered = module.render_study_cycle_profile_markdown(
        {
            "study_id": "001-risk",
            "study_root": str(tmp_path / "study"),
            "quest_id": "quest-001",
            "quest_root": str(tmp_path / "quest"),
            "profiling_window": {"since": None, "until": "2026-04-25T00:00:00+00:00", "event_count": 0},
            "category_windows": {},
            "runtime_transition_summary": {"health_status_counts": {}},
            "controller_decision_fingerprints": {"top_repeats": []},
            "gate_blocker_summary": {"current_blockers": []},
            "package_currentness": {"status": "fresh"},
            "step_latest_times": {},
            "step_timings": [],
            "eta_confidence_band": {"classification": "delivery_only", "label": "delivery-only"},
            "bottlenecks": [],
            "optimization_recommendations": [],
        }
    )

    assert "# Study Cycle Profile: 001-risk" in rendered
    assert "Package currentness: fresh" in rendered


def test_workspace_cycle_profiler_profiles_active_studies_and_sorts_bottlenecks(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)

    active_root = workspace_root / "studies" / "001-risk"
    quieter_root = workspace_root / "studies" / "002-followup"
    inactive_root = workspace_root / "studies" / "draft-no-study-yaml"
    for study_root in (active_root, quieter_root, inactive_root):
        study_root.mkdir(parents=True)
    (active_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    (quieter_root / "study.yaml").write_text("study_id: 002-followup\n", encoding="utf-8")

    for index, status in enumerate(("live", "recovering", "live", "degraded")):
        _write_json(
            active_root / "artifacts" / "runtime" / "runtime_supervision" / f"20260425T000{index}00Z.json",
            {
                "recorded_at": f"2026-04-25T00:0{index}:00+00:00",
                "health_status": status,
                "runtime_reason": "runtime_flap" if status != "live" else "quest_already_running",
            },
        )
    for index in range(3):
        _write_json(
            active_root / "artifacts" / "controller_decisions" / f"20260425T001{index}00Z.json",
            {
                "emitted_at": f"2026-04-25T00:1{index}:00+00:00",
                "decision_type": "bounded_analysis",
                "route_target": "analysis-campaign",
                "reason": "same dispatch",
            },
        )
    _write_json(
        active_root / "artifacts" / "publication_eval" / "latest.json",
        {"emitted_at": "2026-04-25T00:20:00+00:00", "blockers": ["claim_evidence_consistency_failed"]},
    )
    _touch(active_root / "artifacts" / "publication_eval" / "latest.json", 1_777_000_000)
    _touch(active_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(active_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_900)

    _write_json(
        quieter_root / "artifacts" / "runtime" / "runtime_supervision" / "20260425T000000Z.json",
        {"recorded_at": "2026-04-25T00:00:00+00:00", "health_status": "live"},
    )
    _touch(quieter_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(quieter_root / "manuscript" / "current_package" / "manuscript.docx", 1_777_000_000)

    payload = module.profile_workspace_cycles(
        profile=profile,
        since="2026-04-25T00:00:00+00:00",
    )

    assert payload["workspace_root"] == str(workspace_root.resolve())
    assert payload["study_count"] == 2
    assert [item["study_id"] for item in payload["studies"]] == ["001-risk", "002-followup"]
    active_summary = payload["studies"][0]["cycle_summary"]
    assert active_summary["repeated_controller_dispatch_count"] == 2
    assert active_summary["runtime_recovery_churn_count"] == 2
    assert active_summary["runtime_flapping_transition_count"] == 3
    assert active_summary["package_stale_seconds"] == 100
    assert payload["workspace_totals"] == {
        "repeated_controller_dispatch_count": 2,
        "runtime_recovery_churn_count": 2,
        "runtime_flapping_transition_count": 3,
        "package_stale_seconds": 100,
        "non_actionable_gate_count": 0,
    }


def test_workspace_cycle_profiler_renders_markdown() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")

    rendered = module.render_workspace_cycle_profile_markdown(
        {
            "profile_name": "nfpitnet",
            "workspace_root": "/tmp/workspace",
            "study_count": 1,
            "workspace_totals": {
                "repeated_controller_dispatch_count": 2,
                "runtime_recovery_churn_count": 1,
                "runtime_flapping_transition_count": 3,
                "package_stale_seconds": 100,
                "non_actionable_gate_count": 0,
            },
            "studies": [
                {
                    "study_id": "001-risk",
                    "bottleneck_score": 10,
                    "cycle_summary": {
                        "repeated_controller_dispatch_count": 2,
                        "runtime_recovery_churn_count": 1,
                        "runtime_flapping_transition_count": 3,
                        "package_stale_seconds": 100,
                        "non_actionable_gate_count": 0,
                    },
                    "eta_confidence_band": {"classification": "runtime_recovering", "label": "runtime recovering"},
                    "bottlenecks": [{"bottleneck_id": "runtime_recovery_churn"}],
                }
            ],
            "optimization_action_units": [
                {
                    "action_unit_id": "optimization-action::001-risk::runtime_recovery_churn",
                    "study_id": "001-risk",
                    "action_type": "probe_runtime_recovery",
                    "controller_surface": "runtime_watch",
                    "priority": "now",
                }
            ],
            "workspace_scheduler": {
                "ready_count": 1,
                "ready_action_unit_ids": ["optimization-action::001-risk::runtime_recovery_churn"],
            },
        }
    )

    assert "# Workspace Cycle Profile: nfpitnet" in rendered
    assert "001-risk" in rendered
    assert "repeated dispatch: 2" in rendered
    assert "Optimization Action Queue" in rendered
    assert "probe_runtime_recovery" in rendered


def test_workspace_cycle_profiler_emits_action_units_and_scheduler_queue(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "20260425T000000Z.json",
        {
            "recorded_at": "2026-04-25T00:00:00+00:00",
            "health_status": "recovering",
            "runtime_reason": "quest_marked_running_but_no_live_session",
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "20260425T001000Z.json",
        {
            "emitted_at": "2026-04-25T00:10:00+00:00",
            "decision_type": "bounded_analysis",
            "route_target": "analysis-campaign",
            "reason": "same dispatch",
        },
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "20260425T001100Z.json",
        {
            "emitted_at": "2026-04-25T00:11:00+00:00",
            "decision_type": "bounded_analysis",
            "route_target": "analysis-campaign",
            "reason": "same dispatch",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {"emitted_at": "2026-04-25T00:20:00+00:00", "blockers": ["stale_submission_minimal_authority"]},
    )
    _touch(study_root / "paper" / "manuscript.md", 1_777_000_000)
    _touch(study_root / "manuscript" / "current_package" / "manuscript.docx", 1_776_999_900)

    payload = module.profile_workspace_cycles(profile=profile, since="2026-04-25T00:00:00+00:00")

    action_units = payload["optimization_action_units"]
    assert [item["action_type"] for item in action_units] == [
        "probe_runtime_recovery",
        "dedupe_controller_dispatch",
        "run_publication_work_unit",
        "refresh_current_package_after_settle",
    ]
    assert all(item["study_id"] == "001-risk" for item in action_units)
    assert action_units[0]["controller_surface"] == "runtime_watch"
    assert action_units[2]["controller_surface"] == "gate_clearing_batch"
    assert payload["workspace_scheduler"]["ready_action_unit_ids"] == [
        item["action_unit_id"] for item in action_units
    ]
    assert payload["workspace_scheduler"]["ready_count"] == 4


def test_study_cycle_profiler_marks_non_actionable_gate_and_eta_band(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / "003-dpcc"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 003-dpcc\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "emitted_at": "2026-04-25T00:20:00+00:00",
            "status": "blocked",
            "blockers": ["publication_gate_blocked", "submission_hardening_needed"],
        },
    )

    payload = module.profile_study_cycle(profile=profile, study_id="003-dpcc", study_root=None)

    assert payload["gate_blocker_summary"]["actionability_status"] == "blocked_by_non_actionable_gate"
    assert [item["bottleneck_id"] for item in payload["bottlenecks"]] == [
        "non_actionable_gate",
        "publication_gate_blocked",
    ]
    assert payload["eta_confidence_band"] == {
        "classification": "non_actionable_gate",
        "label": "non-actionable gate",
        "confidence": "blocked",
        "min_seconds": None,
        "max_seconds": None,
        "reason": "Gate blockers are label-only and must be narrowed to concrete claim, display, evidence, citation, metric, or package-artifact targets before automated execution.",
    }


def test_eta_classifies_submission_minimal_authority_as_delivery_not_human_admin() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler_eta")

    band = module.eta_confidence_band(
        runtime_transition_summary={"health_status_counts": {"live": 3}},
        gate_blocker_summary={
            "current_blockers": [
                "stale_submission_minimal_authority",
                "submission_surface_qc_failure_present",
            ],
            "actionability_status": "actionable",
        },
        package_currentness={"status": "stale"},
    )

    assert band["classification"] == "delivery_only"


def test_eta_keeps_runtime_recovering_when_latest_runtime_is_not_live() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler_eta")

    band = module.eta_confidence_band(
        runtime_transition_summary={"health_status_counts": {"live": 3, "recovering": 1}},
        gate_blocker_summary={
            "current_blockers": ["claim_evidence_consistency_failed"],
            "actionability_status": "actionable",
        },
        package_currentness={"status": "fresh"},
        current_state_summary={"state": "active_or_unresolved", "runtime_health_status": "recovering"},
    )

    assert band["classification"] == "runtime_recovering"


def test_eta_uses_claim_evidence_when_latest_runtime_is_live_despite_window_churn() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_cycle_profiler_eta")

    band = module.eta_confidence_band(
        runtime_transition_summary={"health_status_counts": {"live": 3, "recovering": 1, "degraded": 1}},
        gate_blocker_summary={
            "current_blockers": ["claim_evidence_consistency_failed"],
            "actionability_status": "actionable",
        },
        package_currentness={"status": "fresh"},
        current_state_summary={"state": "active_or_unresolved", "runtime_health_status": "live"},
    )

    assert band["classification"] == "claim_evidence"
