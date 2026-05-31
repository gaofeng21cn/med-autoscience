from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_study_state_matrix_reports_progress_first_tick_accounting(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_ids = (
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    )
    for study_id in study_ids:
        study_root = workspace_root / "studies" / study_id
        study_root.mkdir(parents=True)
        (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def fake_progress_projection(*, study_id: str, **_: object) -> dict[str, object]:
        study_root = workspace_root / "studies" / study_id
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "active_run_id": None,
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "active_run_id": None,
                "running_provider_attempt": False,
                "worker_liveness": {"health_status": "ready"},
                "execution_state_kind": "executable_owner_action",
                "next_owner": "write",
                "route_target": "write",
                "controller_action": "run_quality_repair_batch",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "dispatch_consumption": {
                    "consumption_status": "unconsumed",
                    "action_fingerprint": f"domain-transition::{study_id}::medical_prose_write_repair",
                    "unconsumed_duration_hours": 3.5,
                },
                "current_blockers": [],
                "progress_delta_classification": "typed_blocker",
                "paper_progress_delta_counted": False,
                "platform_repair_delta_counted": False,
            },
        }

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fake_progress_projection)

    exit_code = cli.main(
        [
            "study-state-matrix",
            "--profile",
            str(profile_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    accounting = payload["progress_first_tick_accounting"]
    assert accounting["expected_owner_action_count"] == 2
    assert accounting["ready_for_owner_action_count"] == 2
    assert accounting["unconsumed_owner_action_count"] == 2
    assert accounting["overdue_owner_pickup_count"] == 2
    assert accounting["running_provider_attempt_count"] == 0
    assert accounting["typed_blocker_count"] == 0
    by_study = {item["study_id"]: item for item in accounting["studies"]}
    assert set(by_study) == set(study_ids)
    for study_id in study_ids:
        assert by_study[study_id]["monitoring_status"] == "stalled_unconsumed_action"
        assert by_study[study_id]["next_owner"] == "write"
        assert by_study[study_id]["controller_action"] == "run_quality_repair_batch"
        assert by_study[study_id]["dispatch_consumption"]["consumption_status"] == "unconsumed"


def test_study_state_matrix_does_not_count_stale_active_run_id_as_running(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def fake_progress_projection(*, study_id: str, **_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "waiting_for_user",
            "active_run_id": "opl-stage-attempt://sat_closed_or_stale",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "active_run_id": "opl-stage-attempt://sat_closed_or_stale",
                "running_provider_attempt": False,
                "worker_liveness": {"health_status": "ready"},
                "execution_state_kind": "observability_only",
                "next_owner": "ai_reviewer",
                "route_target": "review",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                    "lane": "review",
                },
                "dispatch_consumption": {},
                "current_blockers": [],
            },
        }

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fake_progress_projection)

    exit_code = cli.main(
        [
            "study-state-matrix",
            "--profile",
            str(profile_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    accounting = payload["progress_first_tick_accounting"]
    assert accounting["running_provider_attempt_count"] == 0
    assert accounting["ready_for_owner_action_count"] == 1
    study = accounting["studies"][0]
    assert study["active_run_id"] == "opl-stage-attempt://sat_closed_or_stale"
    assert study["running_provider_attempt"] is False
    assert study["monitoring_status"] == "ready_for_dispatch"
