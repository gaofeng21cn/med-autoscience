from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_study_state_matrix_prefers_progress_first_monitoring_active_run_and_next_work_unit(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "003-dm"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 003-dm\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "003-dm",
            "study_root": str(study_root),
            "quest_status": "active",
            "active_run_id": "stale-status-run",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "active_run_id": "opl-stage-attempt://sat-current",
                "active_stage_attempt_id": "sat-current",
                "active_workflow_id": "wf-current",
                "running_provider_attempt": True,
                "worker_liveness": {"health_status": "running"},
                "execution_state_kind": "executable_owner_action",
                "next_owner": "publication_gate",
                "route_target": "review",
                "controller_action": "run_gate_clearing_batch",
                "next_work_unit": {
                    "unit_id": "publication_gate_replay",
                    "lane": "publication_gate",
                    "summary": "Replay publication gate against current evidence.",
                },
                "current_blockers": ["publication_gate_blocked"],
                "progress_delta_classification": "typed_blocker",
                "paper_progress_delta_counted": False,
                "platform_repair_delta_counted": False,
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]

    assert exit_code == 0
    assert study["active_run_id"] == "opl-stage-attempt://sat-current"
    assert study["monitoring"]["active_run_id"] == "opl-stage-attempt://sat-current"
    assert study["monitoring"]["running_provider_attempt"] is True
    assert study["monitoring"]["next_owner"] == "publication_gate"
    assert study["monitoring"]["controller_action"] == "run_gate_clearing_batch"
    assert study["monitoring"]["next_work_unit"]["unit_id"] == "publication_gate_replay"
    assert study["monitoring"]["current_blockers"] == ["publication_gate_blocked"]
