from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.opl_pending_user_message_handoff import build_pending_user_message_handoff


def test_pending_user_message_handoff_does_not_write_mas_runtime_queue(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    handoff = build_pending_user_message_handoff(
        quest_root=quest_root,
        message="stop current run",
        source="codex-test",
        evidence_refs=["artifacts/reports/test/latest.json"],
    )

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
    assert not (quest_root / ".ds").exists()


def test_pending_user_message_handoff_uses_dedupe_key_as_identity(tmp_path: Path) -> None:
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    handoff = build_pending_user_message_handoff(
        quest_root=quest_root,
        message="task update emitted at 10:01",
        source="codex-test",
        dedupe_key="study-task-intake:abc123",
    )

    assert handoff["handoff_id"] == "study-task-intake:abc123"
    assert handoff["dedupe_key"] == "study-task-intake:abc123"
    assert not (quest_root / ".ds").exists()
