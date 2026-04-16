from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_cli_time_to_event_direct_migration_emits_result_json(tmp_path, monkeypatch, capsys) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    controller_module = importlib.import_module("med_autoscience.controllers.time_to_event_direct_migration")
    study_root = tmp_path / "studies" / "001-dm"
    paper_root = tmp_path / "paper"

    def fake_run_time_to_event_direct_migration(*, study_root: Path, paper_root: Path) -> dict[str, object]:
        return {
            "status": "synced",
            "study_root": str(study_root),
            "paper_root": str(paper_root),
            "written_files": ["a.json", "b.json"],
            "blockers": [],
        }

    monkeypatch.setattr(
        controller_module,
        "run_time_to_event_direct_migration",
        fake_run_time_to_event_direct_migration,
    )

    exit_code = cli_module.main(
        [
            "publication",
            "time-to-event-migration",
            "--study-root",
            str(study_root),
            "--paper-root",
            str(paper_root),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "synced"
    assert payload["study_root"] == str(study_root)
    assert payload["paper_root"] == str(paper_root)
