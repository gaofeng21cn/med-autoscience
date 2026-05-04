from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_runtime_supervisor_scan_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_supervisor_scan(
        *,
        profile,
        study_ids,
        apply_safe_actions: bool,
        developer_supervisor_mode: str | None = None,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["study_ids"] = study_ids
        called["apply_safe_actions"] = apply_safe_actions
        called["developer_supervisor_mode"] = developer_supervisor_mode
        return {"surface": "portable_runtime_supervisor_scan", "study_count": len(study_ids)}

    monkeypatch.setattr(cli.runtime_supervisor_scan, "supervisor_scan", fake_supervisor_scan)

    exit_code = cli.main(
        [
            "runtime",
            "supervisor-scan",
            "--profile",
            str(profile_path),
            "--studies",
            "NF003",
            "DM002",
            "--apply-safe-actions",
            "--developer-supervisor-mode",
            "developer_apply_safe",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_ids"] == ("NF003", "DM002")
    assert called["apply_safe_actions"] is True
    assert called["developer_supervisor_mode"] == "developer_apply_safe"
    assert json.loads(captured.out)["surface"] == "portable_runtime_supervisor_scan"
