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


def test_study_state_matrix_does_not_let_stale_redrive_budget_mask_deliverable_delta(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_id = "002-redrive-budget-after-deliverable-delta"
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
                "next_owner": "write",
                "route_target": "review",
                "controller_action": "run_quality_repair_batch",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "lane": "review",
                },
                "typed_blocker": {
                    "blocker_type": "progress_first_owner_redrive_budget_exhausted",
                    "owner": "med-autoscience",
                },
                "current_blockers": ["progress_first_owner_redrive_budget_exhausted"],
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "canonical_work_unit_identity": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    },
                },
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_quality_repair_batch",
                    "status": "executed",
                    "stage_name": "consume_current_inputs_ai_reviewer_record_then_gate_replay",
                    "problem_summary": "run_quality_repair_batch produced manuscript review ledgers.",
                    "stage_goal": "Produce canonical manuscript story-surface delta.",
                    "outcome": "executed",
                    "progress_delta_classification": "deliverable_progress",
                    "stage_work_done": ["Updated the evidence ledger."],
                    "changed_stage_surfaces": [
                        str(study_root / "paper" / "claim_evidence_map.json"),
                        str(study_root / "paper" / "evidence_ledger.json"),
                        str(study_root / "paper" / "review" / "review_ledger.json"),
                    ],
                    "changed_paper_surfaces": [
                        str(study_root / "paper" / "claim_evidence_map.json"),
                        str(study_root / "paper" / "evidence_ledger.json"),
                        str(study_root / "paper" / "review" / "review_ledger.json"),
                    ],
                    "remaining_blockers": [],
                    "evidence_refs": [
                        "artifacts/controller/quality_repair_batch/latest.json",
                        "artifacts/publication_eval/latest.json",
                    ],
                    "semantic_completeness": {
                        "status": "complete",
                        "missing_fields": [],
                    },
                    "terminal_closeout_semantic_completeness": {
                        "status": "complete",
                        "progress_delta_classification": "deliverable_progress",
                    },
                },
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)
    accounting = payload["progress_first_tick_accounting"]
    study = accounting["studies"][0]

    assert exit_code == 0
    assert accounting["typed_blocker_count"] == 0
    assert accounting["expected_owner_action_count"] == 1
    assert accounting["ready_for_owner_action_count"] == 1
    assert study["monitoring_status"] == "ready_for_dispatch"
    assert study["throughput_bottleneck"] == "ready_owner_action"
    assert study["typed_blocker"] is None
    assert payload["studies"][0]["monitoring"]["typed_blocker"] is None
