from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_load_watch_state_returns_default_when_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    result = module.load_watch_state(quest_root)

    assert result == {"schema_version": 1, "controllers": {}}


def test_save_watch_state_persists_state_json(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    payload = {"schema_version": 1, "updated_at": "2026-03-29T00:00:00+00:00", "controllers": {"gate": {}}}

    module.save_watch_state(quest_root, payload)

    state_path = quest_root / "artifacts" / "reports" / "runtime_watch" / "state.json"
    assert json.loads(state_path.read_text(encoding="utf-8")) == payload


def test_write_timestamped_report_writes_json_and_markdown(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    report = {"schema_version": 1, "status": "blocked"}

    json_path, md_path = module.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp="2026-03-29T03:50:50+00:00",
        report=report,
        markdown="# Report\n",
    )

    assert json_path.name == "2026-03-29T035050Z.json"
    assert md_path.name == "2026-03-29T035050Z.md"
    assert json.loads(json_path.read_text(encoding="utf-8")) == report
    assert md_path.read_text(encoding="utf-8") == "# Report\n"
