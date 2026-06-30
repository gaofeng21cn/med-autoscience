from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from .shared import write_profile


def test_study_owner_gate_decision_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    called: dict[str, object] = {}

    def fake_owner_gate_decision_record(**kwargs) -> dict[str, object]:
        called.update(kwargs)
        return {
            "surface": "study_owner_gate_decision_record",
            "record_status": "dry_run",
            "human_gate_ref": "human_gate:owner-gate-decision:test",
        }

    monkeypatch.setattr(cli.study_interventions, "owner_gate_decision_record", fake_owner_gate_decision_record)

    exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--action-type",
            "run_quality_repair_batch",
            "--work-unit-id",
            "analysis_claim_evidence_repair",
            "--work-unit-fingerprint",
            "publication-blockers::497d1260db522f01",
            "--blocker-type",
            "stage_packet_not_current_selected_dispatch",
            "--decision",
            "route_back_to_mas_packet_materialization_bug",
            "--reason",
            "current selected stage packet is missing",
            "--recorded-at",
            "2026-06-14T00:00:00+00:00",
            "--format",
            "json",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["study_root"] == workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    assert called["study_id"] == "002-dm-china-us-mortality-attribution"
    assert called["action_type"] == "run_quality_repair_batch"
    assert called["work_unit_id"] == "analysis_claim_evidence_repair"
    assert called["work_unit_fingerprint"] == "publication-blockers::497d1260db522f01"
    assert called["blocker_type"] == "stage_packet_not_current_selected_dispatch"
    assert called["decision"] == "route_back_to_mas_packet_materialization_bug"
    assert called["reason"] == "current selected stage packet is missing"
    assert called["recorded_at"] == "2026-06-14T00:00:00+00:00"
    assert called["apply"] is False
    assert called["supersedes_owner_gate_decision_ref"] is None
    assert called["replacement_typed_blocker_ref"] is None
    assert json.loads(captured.out)["human_gate_ref"] == "human_gate:owner-gate-decision:test"


def test_study_owner_gate_decision_command_dry_run_does_not_write(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--action-type",
            "run_quality_repair_batch",
            "--work-unit-id",
            "analysis_claim_evidence_repair",
            "--work-unit-fingerprint",
            "publication-blockers::497d1260db522f01",
            "--blocker-type",
            "stage_packet_not_current_selected_dispatch",
            "--decision",
            "route_back_to_mas_packet_materialization_bug",
            "--reason",
            "current selected stage packet is missing",
            "--recorded-at",
            "2026-06-14T00:00:00+00:00",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    event_log = (
        workspace_root
        / "studies"
        / "002-dm-china-us-mortality-attribution"
        / "artifacts"
        / "interventions"
        / "events.jsonl"
    )

    assert exit_code == 0
    assert payload["record_status"] == "dry_run"
    assert payload["human_gate_ref"].startswith("human_gate:owner-gate-decision:")
    assert payload["truth_event_input"]["event_type"] == "human_gate"
    assert not event_log.exists()
    assert not (
        workspace_root
        / "studies"
        / "002-dm-china-us-mortality-attribution"
        / "artifacts"
        / "truth"
        / "latest.json"
    ).exists()


def test_study_owner_gate_decision_command_apply_materializes_truth_closeout(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"

    exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "003-dpcc-primary-care-phenotype-treatment-gap",
            "--action-type",
            "materialize_submission_ready_owner_verdict_or_human_gate",
            "--work-unit-id",
            "submission_ready_authority_closeout",
            "--work-unit-fingerprint",
            "ebf3e5131f6ae95c6ea25409",
            "--blocker-type",
            "submission_ready_authority_closeout_required",
            "--decision",
            "accept_submission_ready_authority_closeout",
            "--reason",
            "current submission-ready package is quality-clear; record owner gate for final authority closeout",
            "--recorded-at",
            "2026-06-30T00:00:00+00:00",
            "--apply",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    snapshot = json.loads(
        (study_root / "artifacts" / "truth" / "latest.json").read_text(encoding="utf-8")
    )

    assert exit_code == 0
    assert payload["record_status"] == "applied"
    assert payload["truth_event"]["event_type"] == "human_gate"
    assert payload["truth_event"]["payload"]["owner_gate_kind"] == "submission_authority_gate"
    assert payload["event"]["payload"]["submission_authority_closeout"]["authority_materialized"] is False
    assert payload["event"]["payload"]["submission_authority_closeout"]["writes_owner_receipt"] is False
    assert snapshot["canonical_next_action"] == "await_submission_authority_or_human_gate_closeout"
    assert snapshot["blocking_reasons"] == [
        "submission_authority_or_human_gate_closeout_required"
    ]


def test_study_owner_gate_decision_command_syncs_existing_event_without_reapply(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"

    apply_exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--action-type",
            "await_human_or_mas_authority_decision_for_submission_blocker",
            "--work-unit-id",
            "submission_blocker_human_gate",
            "--work-unit-fingerprint",
            "533358e43f6bb6d7378e114d",
            "--blocker-type",
            "submission_blocker_human_gate_required",
            "--decision",
            "request_submission_blocker_human_gate",
            "--reason",
            "current package is not submittable and needs explicit owner or human gate",
            "--recorded-at",
            "2026-06-30T00:01:00+00:00",
            "--apply",
        ]
    )
    capsys.readouterr()
    truth_log = study_root / "artifacts" / "truth" / "events.jsonl"
    truth_log.unlink()

    sync_exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--sync-truth-from-existing",
            "--format",
            "json",
        ]
    )
    first = json.loads(capsys.readouterr().out)
    second_exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--sync-truth-from-existing",
        ]
    )
    second = json.loads(capsys.readouterr().out)
    snapshot = json.loads(
        (study_root / "artifacts" / "truth" / "latest.json").read_text(encoding="utf-8")
    )
    intervention_events = [
        json.loads(line)
        for line in (study_root / "artifacts" / "interventions" / "events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]

    assert apply_exit_code == 0
    assert sync_exit_code == 0
    assert second_exit_code == 0
    assert len(intervention_events) == 1
    assert first["surface"] == "study_intervention_truth_sync_result"
    assert first["appended_event_count"] == 1
    assert second["appended_event_count"] == 0
    assert first["authority_materialized"] is False
    assert first["writes_human_gate_authority"] is False
    assert snapshot["canonical_next_action"] == "await_submission_authority_or_human_gate_closeout"
    assert snapshot["blocking_reasons"] == [
        "submission_authority_or_human_gate_closeout_required"
    ]


def test_study_owner_gate_decision_command_routes_b003_governed_blocker_disposition(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    exit_code = cli.main(
        [
            "study-owner-gate-decision",
            "--profile",
            str(profile_path),
            "--study-id",
            "003-dpcc-primary-care-phenotype-treatment-gap",
            "--action-type",
            "publication_gate_replay",
            "--work-unit-id",
            "publication-blockers::0915410f804b3697",
            "--work-unit-fingerprint",
            "owner-gate-decision:d6d895635654560a85573c04",
            "--blocker-type",
            "medical_publication_surface_blocked",
            "--decision",
            "route_back_to_publication_owner",
            "--reason",
            "route back to the missing write repair owner route",
            "--supersedes-owner-gate-decision-ref",
            "owner-gate-decision:d6d895635654560a85573c04",
            "--route-back-evidence-ref",
            "route-back:b003-write-repair-owner-route-gap",
            "--recorded-at",
            "2026-06-22T00:00:00+00:00",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    event_log = (
        workspace_root
        / "studies"
        / "003-dpcc-primary-care-phenotype-treatment-gap"
        / "artifacts"
        / "interventions"
        / "events.jsonl"
    )

    assert exit_code == 0
    assert payload["record_status"] == "dry_run"
    assert payload["human_gate_ref"].startswith("human_gate:owner-gate-decision:")
    event_payload = payload["event"]["payload"]
    assert event_payload["decision"] == "route_back_to_publication_owner"
    assert event_payload["route_back_evidence_ref"] == (
        "route-back:b003-write-repair-owner-route-gap"
    )
    assert event_payload["provider_redrive_allowed"] is False
    assert event_payload["provider_admission_allowed"] is False
    assert event_payload["preserve_or_explicitly_supersede"] == (
        "owner-gate-decision:d6d895635654560a85573c04"
    )
    assert not event_log.exists()


def test_domain_owner_refresh_controller_decisions_command_is_retired(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "domain-owner-action-refresh-controller-decisions",
                "--profile",
                str(profile_path),
                "--studies",
                "DM002",
                "DM003",
                "--mode",
                "developer_apply_safe",
                "--apply",
            ]
        )
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "invalid choice" in captured.err
    assert "domain-owner-action-refresh-controller-decisions" in captured.err


def test_owner_callable_dispatch_residue_cleanup_command_is_retired(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    with pytest.raises(SystemExit) as excinfo:
        cli.main(
            [
                "owner-callable-adapter-residue-cleanup",
                "--profile",
                str(profile_path),
                "--studies",
                "DM002",
                "DM003",
                "--dry-run",
            ]
        )
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "invalid choice" in captured.err
    assert "owner-callable-adapter-residue-cleanup" in captured.err


def test_medical_paper_readiness_owner_blocker_command_materializes_controller_decision(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "study"

    exit_code = cli.main(
        [
            "medical-paper-readiness-owner-blocker",
            "--study-root",
            str(study_root),
            "--source",
            "test-cli",
            "--apply",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"

    assert exit_code == 0
    assert payload["surface"] == "medical_paper_readiness_owner_blocker"
    assert payload["status"] == "materialized"
    assert payload["applied"] is True
    assert payload["controller_decision_ref"] == str(decision_path.resolve())
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    assert decision["route_decision"] == "stable_blocker"
    assert decision["runtime_decision"] == "blocked"
    assert decision["quality_claim_authorized"] is False
    assert decision["submission_authorized"] is False
