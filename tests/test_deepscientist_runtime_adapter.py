from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_load_runtime_state_reads_ds_runtime_json(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    dump_json(quest_root / ".ds" / "runtime_state.json", {"status": "running", "active_run_id": "run-1"})

    result = module.load_runtime_state(quest_root)

    assert result["status"] == "running"
    assert result["active_run_id"] == "run-1"


def test_quest_status_normalizes_case_and_whitespace(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    dump_json(quest_root / ".ds" / "runtime_state.json", {"status": " Running "})

    assert module.quest_status(quest_root) == "running"


def test_iter_active_quests_filters_running_and_active(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    runtime_root = tmp_path / "runtime" / "quests"
    dump_json(runtime_root / "q-running" / ".ds" / "runtime_state.json", {"status": "running"})
    dump_json(runtime_root / "q-active" / ".ds" / "runtime_state.json", {"status": "active"})
    dump_json(runtime_root / "q-stopped" / ".ds" / "runtime_state.json", {"status": "stopped"})
    dump_json(runtime_root / "q-completed" / ".ds" / "runtime_state.json", {"status": "completed"})

    result = module.iter_active_quests(runtime_root)

    assert [path.name for path in result] == ["q-active", "q-running"]


def test_find_latest_main_result_prefers_latest_candidate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    older = quest_root / ".ds" / "worktrees" / "paper-run-1" / "experiments" / "main" / "run-1" / "RESULT.json"
    newer = quest_root / "experiments" / "main" / "run-2" / "RESULT.json"
    dump_json(older, {"run_id": "run-1"})
    newer.parent.mkdir(parents=True, exist_ok=True)
    newer.write_text('{"run_id":"run-2"}\n', encoding="utf-8")
    newer.touch()

    result = module.find_latest_main_result(quest_root)

    assert result == newer


def test_find_latest_prefers_latest_candidate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    older = tmp_path / "older.txt"
    newer = tmp_path / "newer.txt"
    older.write_text("older\n", encoding="utf-8")
    newer.write_text("newer\n", encoding="utf-8")
    newer.touch()

    result = module.find_latest([older, newer])

    assert result == newer


def test_read_recent_stdout_lines_filters_bad_json_and_limits_count(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    stdout_path = tmp_path / "stdout.jsonl"
    stdout_path.write_text(
        "\n".join(
            [
                '{"line":"first"}',
                "not-json",
                '{"line":"second"}',
                '{"line":""}',
                '{"line":"third"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.read_recent_stdout_lines(stdout_path, limit=3)

    assert result == ["second", "third"]


def test_resolve_active_stdout_path_uses_active_run_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.runtime")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    stdout_path = quest_root / ".ds" / "runs" / "run-1" / "stdout.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text("", encoding="utf-8")

    result = module.resolve_active_stdout_path(
        quest_root=quest_root,
        runtime_state={"active_run_id": "run-1"},
    )

    assert result == stdout_path
