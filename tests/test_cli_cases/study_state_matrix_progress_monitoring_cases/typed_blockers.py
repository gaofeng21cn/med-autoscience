from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_cli_cases.shared import write_profile


def test_study_state_matrix_keeps_typed_closeout_packet_as_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-typed-closeout"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "blocked_typed_owner",
                "typed_blocker": {
                    "blocker_id": "typed_closeout_packet_required",
                    "blocker_type": "provider_completed_without_typed_closeout",
                    "summary": "Provider completion needs a typed closeout packet.",
                },
                "current_blockers": ["typed_closeout_packet_required"],
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "status": "completed_without_typed_closeout",
                    "terminal_closeout_semantic_completeness": {
                        "status": "typed_blocker",
                        "typed_blocker": "typed_closeout_packet_required",
                    },
                    "semantic_completeness": {
                        "status": "missing_required_fields",
                        "missing_fields": ["stage_goal"],
                    },
                    "telemetry_completeness": {
                        "status": "missing_required_fields",
                        "missing_fields": ["duration", "token_usage", "cost"],
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    accounting = json.loads(capsys.readouterr().out)["progress_first_tick_accounting"]
    study = accounting["studies"][0]

    assert exit_code == 0
    assert accounting["typed_blocker_count"] == 1
    assert study["monitoring_status"] == "blocked_typed_owner"
    assert study["throughput_bottleneck"] == "typed_blocker"
    assert study["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    assert study["missing_closeout_semantics"] is True


def test_study_state_matrix_keeps_redrive_budget_exhausted_as_typed_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-redrive-budget-exhausted"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "active_run_id": "stale-run",
                "running_provider_attempt": False,
                "execution_state_kind": "typed_blocker",
                "owner_action_current": True,
                "next_owner": "med-autoscience",
                "controller_action": "resume",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "lane": "review",
                },
                "typed_blocker": {
                    "blocker_type": "progress_first_owner_redrive_budget_exhausted",
                    "owner": "med-autoscience",
                },
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "status": "handoff_ready",
                    "semantic_completeness": {
                        "status": "missing_required_fields",
                        "missing_fields": ["changed_stage_surfaces", "remaining_blockers"],
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    accounting = json.loads(capsys.readouterr().out)["progress_first_tick_accounting"]
    study = accounting["studies"][0]

    assert exit_code == 0
    assert accounting["expected_owner_action_count"] == 0
    assert accounting["ready_for_owner_action_count"] == 0
    assert accounting["typed_blocker_count"] == 1
    assert study["monitoring_status"] == "blocked_typed_owner"
    assert study["throughput_bottleneck"] == "typed_blocker"
    assert study["typed_blocker"]["blocker_type"] == "progress_first_owner_redrive_budget_exhausted"
