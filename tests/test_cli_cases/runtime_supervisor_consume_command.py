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
