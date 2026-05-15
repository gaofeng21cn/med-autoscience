from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_runtime_supervisor_consume_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_supervisor_consume(
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
        return {"surface": "runtime_supervisor_consumer", "repair_task_count": len(study_ids)}

    monkeypatch.setattr(cli.runtime_supervisor_consumer, "supervisor_consume", fake_supervisor_consume)

    exit_code = cli.main(
        [
            "runtime",
            "supervisor-consume",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--dry-run",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is False
    assert json.loads(captured.out)["surface"] == "runtime_supervisor_consumer"


def test_runtime_supervisor_consume_command_apply_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_supervisor_consume(
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
            "surface": "runtime_supervisor_consumer",
            "default_executor_dispatch_count": len(study_ids),
        }

    monkeypatch.setattr(cli.runtime_supervisor_consumer, "supervisor_consume", fake_supervisor_consume)

    exit_code = cli.main(
        [
            "runtime",
            "supervisor-consume",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert json.loads(captured.out)["default_executor_dispatch_count"] == 2


def test_runtime_supervisor_execute_dispatch_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_execute_default_executor_dispatches(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["action_types"] = action_types
        called["mode"] = mode
        called["apply"] = apply
        return {
            "surface": "default_executor_dispatch_executor",
            "execution_count": len(study_ids),
        }

    monkeypatch.setattr(
        cli.runtime_supervisor_dispatch_executor,
        "execute_default_executor_dispatches",
        fake_execute_default_executor_dispatches,
    )

    exit_code = cli.main(
        [
            "runtime",
            "supervisor-execute-dispatch",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--action-types",
            "runtime_platform_repair",
            "return_to_ai_reviewer_workflow",
            "--mode",
            "developer_apply_safe",
            "--apply",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["action_types"] == ("runtime_platform_repair", "return_to_ai_reviewer_workflow")
    assert called["mode"] == "developer_apply_safe"
    assert called["apply"] is True
    assert json.loads(captured.out)["surface"] == "default_executor_dispatch_executor"


def test_runtime_supervisor_refresh_controller_decisions_command_dispatches_controller(
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
            "surface": "runtime_supervisor_controller_decision_refresh",
            "refresh_count": len(study_ids),
        }

    monkeypatch.setattr(
        cli.runtime_supervisor_dispatch_executor,
        "refresh_controller_decisions_for_current_publication_eval",
        fake_refresh_controller_decisions_for_current_publication_eval,
    )

    exit_code = cli.main(
        [
            "runtime",
            "supervisor-refresh-controller-decisions",
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
    assert json.loads(captured.out)["surface"] == "runtime_supervisor_controller_decision_refresh"


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
