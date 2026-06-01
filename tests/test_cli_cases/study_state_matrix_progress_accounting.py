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
                "next_forced_delta": {
                    "target_surface_specificity": "explicit_owner_route_target",
                    "missing_explicit_target_surface": False,
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
    assert accounting["missing_closeout_semantics_count"] == 0
    assert accounting["generic_target_surface_count"] == 0
    assert accounting["throughput_bottleneck_counts"] == {"owner_pickup_overdue": 2}
    assert [item["throughput_bottleneck"] for item in accounting["throughput_bottlenecks"]] == [
        "owner_pickup_overdue",
        "owner_pickup_overdue",
    ]
    by_study = {item["study_id"]: item for item in accounting["studies"]}
    assert set(by_study) == set(study_ids)
    for study_id in study_ids:
        assert by_study[study_id]["priority_rank"] in {1, 2}
        assert by_study[study_id]["monitoring_status"] == "stalled_unconsumed_action"
        assert by_study[study_id]["throughput_bottleneck"] == "owner_pickup_overdue"
        assert by_study[study_id]["target_surface_specificity"] == "explicit_owner_route_target"
        assert by_study[study_id]["missing_explicit_target_surface"] is False
        assert by_study[study_id]["missing_closeout_semantics"] is False
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
    assert study["priority_rank"] == 1
    assert study["throughput_bottleneck"] == "ready_owner_action"
    assert study["target_surface_specificity"] is None


def test_study_state_matrix_fail_closes_generic_target_surface_owner_action(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-generic-target-surface"
    study_root = workspace_root / "studies" / study_id
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def fake_progress_projection(*, study_id: str, **_: object) -> dict[str, object]:
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "active",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "study_id": study_id,
                "running_provider_attempt": False,
                "execution_state_kind": "executable_owner_action",
                "owner_action_current": True,
                "next_owner": "ai_reviewer",
                "route_target": "review",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "lane": "review",
                },
                "next_forced_delta": {
                    "target_surface_specificity": "generic_route_obligation_fallback",
                    "missing_explicit_target_surface": True,
                    "target_surface_fallback_reason": "owner_route_missing_explicit_target_surface",
                },
                "dispatch_consumption": {},
            },
        }

    monkeypatch.setattr(cli.domain_status_projection, "progress_projection", fake_progress_projection)

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    accounting = payload["progress_first_tick_accounting"]
    study = accounting["studies"][0]

    assert exit_code == 0
    assert accounting["expected_owner_action_count"] == 0
    assert accounting["ready_for_owner_action_count"] == 0
    assert accounting["owner_route_contract_blocker_count"] == 1
    assert accounting["generic_target_surface_count"] == 1
    assert accounting["throughput_bottleneck_counts"] == {"generic_target_surface": 1}
    assert study["monitoring_status"] == "blocked_owner_route_contract"
    assert study["owner_route_contract_blocker"] == "owner_route_target_surface_required"
    assert study["throughput_bottleneck"] == "generic_target_surface"
    assert study["missing_explicit_target_surface"] is True
