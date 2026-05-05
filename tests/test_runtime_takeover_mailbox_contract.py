from __future__ import annotations

import json
from pathlib import Path

import pytest

from med_autoscience.runtime_protocol.user_message import enqueue_user_message


pytestmark = pytest.mark.meta

def test_enqueue_user_message_records_mailbox_state_and_interaction_journal(tmp_path: Path) -> None:
    quest_root = tmp_path / "quests" / "001-risk"
    state_path = quest_root / ".ds" / "runtime_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps({"quest_id": "001-risk", "status": "running", "active_interaction_id": "turn-1"}) + "\n",
        encoding="utf-8",
    )

    record = enqueue_user_message(
        quest_root=quest_root,
        runtime_state={"quest_id": "001-risk", "active_interaction_id": "turn-1"},
        message="Please pause after the current evidence checkpoint.",
        source="test",
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    runtime_state = json.loads(state_path.read_text(encoding="utf-8"))
    journal_lines = (quest_root / ".ds" / "interaction_journal.jsonl").read_text(encoding="utf-8").splitlines()

    assert record["status"] == "queued"
    assert record["reply_to_interaction_id"] == "turn-1"
    assert queue["pending"] == [record]
    assert runtime_state["pending_user_message_count"] == 1
    assert len(journal_lines) == 1
    journal_event = json.loads(journal_lines[0])
    assert journal_event["type"] == "user_inbound"
    assert journal_event["quest_id"] == "001-risk"
    assert journal_event["message_id"] == record["message_id"]


def test_enqueue_user_message_is_idempotent_for_same_pending_content(tmp_path: Path) -> None:
    quest_root = tmp_path / "quests" / "001-risk"
    state_path = quest_root / ".ds" / "runtime_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text('{"quest_id":"001-risk","status":"running"}\n', encoding="utf-8")

    first = enqueue_user_message(
        quest_root=quest_root,
        runtime_state={"quest_id": "001-risk"},
        message="Add reviewer response details.",
        source="test",
    )
    second = enqueue_user_message(
        quest_root=quest_root,
        runtime_state={"quest_id": "001-risk"},
        message="Add reviewer response details.",
        source="test",
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    journal_lines = (quest_root / ".ds" / "interaction_journal.jsonl").read_text(encoding="utf-8").splitlines()

    assert second == first
    assert queue["pending"] == [first]
    assert len(journal_lines) == 1
