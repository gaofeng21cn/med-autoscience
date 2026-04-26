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
    assert profile_payload["eta_confidence_band"]["classification"] == "runtime_recovering"
    assert [item["bottleneck_id"] for item in profile_payload["bottlenecks"]] == [
        "runtime_recovery_churn",
        "repeated_controller_decision",
        "publication_gate_blocked",
        "stale_current_package",
    ]


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
        {"emitted_at": "2026-04-25T00:20:00+00:00", "blockers": ["claim_evidence_consistency_failed"]},
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
