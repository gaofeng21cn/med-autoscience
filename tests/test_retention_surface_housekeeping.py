from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_retention_surface_housekeeping_removes_only_misplaced_receipt_dirs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.retention_surface_housekeeping")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    (workspace / "runtime" / "quests").mkdir(parents=True)
    misplaced = workspace / "archive" / "runtime" / "artifacts" / "historical_body_retention"
    misplaced.mkdir(parents=True)
    payload = {
        "surface_kind": "historical_body_retention",
        "status": "nothing_to_retain",
        "body_included": False,
    }
    (misplaced / "latest.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    (misplaced / "20260609T041501Z.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")
    canonical = workspace / "runtime" / "artifacts" / "historical_body_retention"
    canonical.mkdir(parents=True)
    (canonical / "latest.json").write_text(json.dumps(payload) + "\n", encoding="utf-8")

    planned = module.run_retention_surface_housekeeping(root=workspace, apply=False)

    assert planned["status"] == "planned"
    assert planned["candidate_count"] == 1
    assert misplaced.is_dir()
    assert canonical.is_dir()

    applied = module.run_retention_surface_housekeeping(root=workspace, apply=True)

    assert applied["status"] == "applied"
    assert applied["removed_count"] == 1
    assert not misplaced.exists()
    assert canonical.is_dir()
    assert applied["latest_receipt_path"] == str(
        workspace / "runtime" / "artifacts" / "retention_surface_housekeeping" / "latest.json"
    )


def test_retention_surface_housekeeping_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_retention_surface_housekeeping(
        *,
        root: Path,
        apply: bool,
        max_directories: int | None,
    ) -> dict[str, object]:
        called["root"] = root
        called["apply"] = apply
        called["max_directories"] = max_directories
        return {"surface_kind": "retention_surface_housekeeping", "status": "applied"}

    monkeypatch.setattr(
        cli.retention_surface_housekeeping,
        "run_retention_surface_housekeeping",
        fake_run_retention_surface_housekeeping,
    )

    exit_code = cli.main(
        [
            "retention-surface-housekeeping",
            "--root",
            str(tmp_path / "workspace"),
            "--apply",
            "--max-directories",
            "4",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": tmp_path / "workspace",
        "apply": True,
        "max_directories": 4,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"
