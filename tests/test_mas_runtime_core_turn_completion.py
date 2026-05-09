from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.runtime_transport.mas_runtime_core_turn_completion import (
    inspect_runner_completion,
    inspect_logical_turn_completion,
)


def test_logical_turn_completion_requires_closeout(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "turn.completed"},
        ],
    )

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is None


def test_logical_turn_completion_requires_closed_stdout_items(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "turn.completed"},
        ],
    )

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is None


def test_runner_completion_rejects_success_without_turn_closeout(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "turn.started"},
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "incomplete"
    assert result["reason"] == "missing_turn_closeout"
    assert result["normalized_runner_status"] == "runner_incomplete"


def test_runner_completion_accepts_turn_closeout_without_turn_completed_event(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "completed"
    assert result["reason"] == "turn_closeout_present"
    assert result["normalized_runner_status"] == "succeeded"
    assert result["stdout_turn_completed"] is False


def test_logical_turn_completion_reports_stale_nonterminal_receipt(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
            {"type": "turn.completed"},
        ],
    )
    _write_latest_receipt(quest_root=quest_root, run_id="run-001", status="queued")

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is not None
    assert result["state"] == "completed"
    assert result["reason"] == "logical_turn_completed"
    assert result["latest_receipt_status"] == "queued"
    assert result["latest_receipt_terminal"] is False


def test_logical_turn_completion_keeps_terminal_receipt_flag(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(quest_root=quest_root, run_id="run-001", events=[])
    _write_latest_receipt(quest_root=quest_root, run_id="run-001", status="finished")

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is not None
    assert result["latest_receipt_terminal"] is True


def _write_closeout(*, quest_root: Path, run_id: str) -> None:
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps({"quest_id": quest_root.name, "run_id": run_id}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_stdout(*, quest_root: Path, run_id: str, events: list[dict]) -> None:
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )


def _write_latest_receipt(*, quest_root: Path, run_id: str, status: str) -> None:
    receipt_path = quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps({"quest_id": quest_root.name, "run_id": run_id, "status": status}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
