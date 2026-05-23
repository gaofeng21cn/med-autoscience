from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.opl_pending_user_message_handoff import build_pending_user_message_handoff


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_pending_user_message_handoff_does_not_write_mas_runtime_queue(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    runtime_state = {
        "quest_id": "q001",
        "active_interaction_id": "progress-1",
        "pending_user_message_count": 0,
    }
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    dump_json(runtime_state_path, runtime_state)

    handoff = build_pending_user_message_handoff(
        quest_root=quest_root,
        runtime_state=runtime_state,
        message="stop current run",
        source="codex-test",
        evidence_refs=["artifacts/reports/test/latest.json"],
    )

    updated_runtime = json.loads(runtime_state_path.read_text(encoding="utf-8"))
    assert handoff["surface_kind"] == "mas_opl_pending_user_message_handoff"
    assert handoff["runtime_owner"] == "one-person-lab"
    assert handoff["queue_owner"] == "one-person-lab"
    assert handoff["mas_runtime_queue_retired"] is True
    assert handoff["message_body_included"] is False
    assert len(handoff["message_digest"]) == 64
    assert handoff["evidence_refs"] == ["artifacts/reports/test/latest.json"]
    assert handoff["runtime_state_mutated"] is False
    assert handoff["user_message_queue_mutated"] is False
    assert handoff["interaction_journal_mutated"] is False
    assert handoff["typed_blocker"]["owner"] == "one-person-lab"
    assert updated_runtime == runtime_state
    assert not (quest_root / ".ds" / "user_message_queue.json").exists()
    assert not (quest_root / ".ds" / "interaction_journal.jsonl").exists()


def test_pending_user_message_handoff_uses_dedupe_key_as_identity(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    handoff = build_pending_user_message_handoff(
        quest_root=quest_root,
        runtime_state={"quest_id": "q001"},
        message="task update emitted at 10:01",
        source="codex-test",
        dedupe_key="study-task-intake:abc123",
    )

    assert handoff["handoff_id"] == "study-task-intake:abc123"
    assert handoff["dedupe_key"] == "study-task-intake:abc123"
    assert not (quest_root / ".ds").exists()
