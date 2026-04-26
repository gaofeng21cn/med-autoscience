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
        since="2026-04-25T00:00:00+00:00",
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
            "bottlenecks": [],
            "optimization_recommendations": [],
        }
    )

    assert "# Study Cycle Profile: 001-risk" in rendered
    assert "Package currentness: fresh" in rendered
