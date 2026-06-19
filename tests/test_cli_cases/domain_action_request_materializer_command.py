from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

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


def test_domain_owner_refresh_controller_decisions_command_dispatches_controller(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_refresh_controller_decisions_for_current_publication_eval(
        *,
        profile,
        study_ids,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["mode"] = mode
        called["apply"] = apply
        return {
            "surface": "domain_owner_action_controller_decision_refresh",
            "refresh_count": len(study_ids),
        }

    original_load_controller = cli._load_controller
    fake_controller = SimpleNamespace(
        refresh_controller_decisions_for_current_publication_eval=(
            fake_refresh_controller_decisions_for_current_publication_eval
        )
    )

    def fake_load_controller(module_name: str):
        if module_name == "domain_owner_action_dispatch":
            return fake_controller
        return original_load_controller(module_name)

    monkeypatch.setattr(cli, "_load_controller", fake_load_controller)

    exit_code = cli.main(
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

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("DM002", "DM003")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert json.loads(captured.out)["surface"] == "domain_owner_action_controller_decision_refresh"


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
