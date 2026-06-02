from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def test_study_state_matrix_running_provider_attempt_suppresses_stale_owner_pickup_overdue(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-dm"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 002-dm\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "active_run_id": "opl-stage-attempt://sat-current",
                "active_stage_attempt_id": "sat-current",
                "active_workflow_id": "wf-current",
                "running_provider_attempt": True,
                "worker_liveness": {"health_status": "running"},
                "next_owner": "ai_reviewer",
                "route_target": "review",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": "ai_reviewer_medical_prose_quality_review",
                "dispatch_consumption": {
                    "consumption_status": "overdue",
                    "owner_pickup_overdue": True,
                    "unconsumed_duration_hours": 2,
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    accounting = json.loads(captured.out)["progress_first_tick_accounting"]
    study = accounting["studies"][0]

    assert exit_code == 0
    assert accounting["running_provider_attempt_count"] == 1
    assert accounting["overdue_owner_pickup_count"] == 0
    assert accounting["throughput_bottleneck_counts"] == {"running_provider_attempt": 1}
    assert study["monitoring_status"] == "running"
    assert study["running_provider_attempt"] is True
    assert study["owner_pickup_overdue"] is False
    assert study["throughput_bottleneck"] == "running_provider_attempt"
