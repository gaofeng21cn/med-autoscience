from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def test_study_state_matrix_reads_nested_progress_projection_monitoring_summary(
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
            "active_run_id": "raw-status-run",
            "progress_projection": {
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
                    "next_owner": "ai_reviewer",
                    "route_target": "review",
                    "controller_action": "return_to_ai_reviewer_workflow",
                    "next_work_unit": {
                        "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                        "lane": "review",
                    },
                    "dispatch_consumption": {
                        "consumption_status": "receipt_consumed",
                        "receipt_ref": "artifacts/publication_eval/ai_reviewer_responses/current.json",
                    },
                    "latest_terminal_stage": {
                        "stage_id": "domain_owner/default-executor-dispatch",
                        "status": "handoff_ready",
                    },
                    "progress_delta_classification": "mixed",
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    study = payload["studies"][0]
    accounting_study = payload["progress_first_tick_accounting"]["studies"][0]

    assert exit_code == 0
    assert study["active_run_id"] == "opl-stage-attempt://sat-current"
    assert study["monitoring"]["running_provider_attempt"] is True
    assert study["monitoring"]["latest_terminal_stage"]["status"] == "handoff_ready"
    assert study["monitoring"]["dispatch_consumption"]["consumption_status"] == "receipt_consumed"
    assert accounting_study["monitoring_status"] == "running"
    assert payload["progress_first_tick_accounting"]["running_provider_attempt_count"] == 1


def test_study_state_matrix_exposes_supervisor_monitoring_bundle_without_writes(
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
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "eval_id": "publication-eval::002-dm::current",
            "status": "blocked",
            "verdict": {
                "overall_verdict": "mixed",
                "primary_claim_status": "partial",
            },
            "reviewer_operating_system": {
                "currentness_checks": {
                    "current_manuscript": {
                        "status": "current",
                        "ref": "paper/current/manuscript.md",
                    },
                    "medical_prose_review": {
                        "status": "stale",
                        "reason": "stale_for_live_manuscript",
                    },
                }
            },
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
            },
        },
    )

    monkeypatch.setattr(
        cli.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "active",
            "current_stage": "publication_supervision",
            "paper_stage": "ai_reviewer_currentness_recheck",
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "schema_version": 1,
                "authority": "refs_only_observability",
                "current_stage": "publication_supervision",
                "paper_stage": "ai_reviewer_currentness_recheck",
                "active_run_id": "opl-stage-attempt://sat-dm002",
                "active_stage_attempt_id": "sat-dm002",
                "active_workflow_id": "wf-dm002",
                "running_provider_attempt": False,
                "worker_liveness": {
                    "health_status": "stale",
                    "worker_liveness_state": "not_observed",
                    "supervisor_tick_status": "fresh",
                },
                "execution_state_kind": "blocked_typed_owner",
                "typed_blocker": {
                    "blocker_id": "typed_closeout_packet_required",
                    "blocker_type": "provider_completed_without_typed_closeout",
                    "summary": "Provider completion needs a typed closeout packet.",
                },
                "next_owner": "one-person-lab",
                "controller_action": "request_typed_closeout_packet",
                "next_work_unit": {
                    "unit_id": "typed_closeout_packet_required",
                    "lane": "runtime-closeout",
                    "summary": "Return a typed closeout packet for the completed provider attempt.",
                },
                "stage_progress_log": {
                    "attempt_count": 1,
                    "completed_attempt_count": 1,
                    "runner_progress_event_count": 4,
                    "attempt_refs": [
                        "artifacts/supervision/current_control_state/stage_attempts/sat-dm002.json"
                    ],
                },
                "latest_terminal_stage": {
                    "stage_attempt_id": "sat-dm002",
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "status": "completed_without_typed_closeout",
                    "outcome": "typed_blocker",
                    "remaining_blockers": ["typed_closeout_packet_required"],
                    "closeout_refs": [
                        "artifacts/supervision/consumer/default_executor_execution/sat-dm002.closeout.json"
                    ],
                    "source_path": "artifacts/supervision/current_control_state/latest_terminal_stage.json",
                },
                "source_refs": [
                    "artifacts/supervision/current_control_state/latest.json",
                    "artifacts/supervision/current_control_state/last_24h_stage_timeline.json",
                ],
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    bundle = json.loads(captured.out)["studies"][0]["supervisor_monitoring_bundle"]

    assert exit_code == 0
    assert bundle["current_stage"] == "publication_supervision"
    assert bundle["active_run_id"] == "opl-stage-attempt://sat-dm002"
    assert bundle["active_stage_attempt_id"] == "sat-dm002"
    assert bundle["provider_status"]["status"] == "provider_not_running"
    assert bundle["worker_liveness"]["health_status"] == "stale"
    assert bundle["latest_24h_timeline_refs"]["window_hours"] == 24
    assert "artifacts/supervision/current_control_state/last_24h_stage_timeline.json" in (
        bundle["latest_24h_timeline_refs"]["refs"]
    )
    assert bundle["latest_closeout"]["ref"] == (
        "artifacts/supervision/consumer/default_executor_execution/sat-dm002.closeout.json"
    )
    assert bundle["publication_eval"]["observed"] is True
    assert bundle["publication_eval"]["eval_id"] == "publication-eval::002-dm::current"
    assert bundle["verdict"]["overall_verdict"] == "mixed"
    assert bundle["currentness"]["current_manuscript"]["status"] == "current"
    assert bundle["typed_blocker"]["blocker_id"] == "typed_closeout_packet_required"
    assert bundle["next_work_unit"]["unit_id"] == "typed_closeout_packet_required"
    assert bundle["authority_boundary"]["can_write_study_truth"] is False
    assert bundle["authority_boundary"]["can_authorize_quality_verdict"] is False
