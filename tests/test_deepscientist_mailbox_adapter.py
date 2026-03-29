from __future__ import annotations

import importlib
import json
from io import BytesIO
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_enqueue_user_message_updates_queue_runtime_state_and_journal(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.mailbox")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    runtime_state = {
        "quest_id": "q001",
        "active_interaction_id": "progress-1",
        "pending_user_message_count": 0,
    }
    dump_json(quest_root / ".ds" / "runtime_state.json", runtime_state)
    dump_json(quest_root / ".ds" / "user_message_queue.json", {"version": 1, "pending": [], "completed": []})
    (quest_root / ".ds" / "interaction_journal.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / ".ds" / "interaction_journal.jsonl").write_text("", encoding="utf-8")

    record = module.enqueue_user_message(
        quest_root=quest_root,
        runtime_state=runtime_state,
        message="stop current run",
        source="codex-test",
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    updated_runtime = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    journal_lines = (quest_root / ".ds" / "interaction_journal.jsonl").read_text(encoding="utf-8").splitlines()

    assert record["content"] == "stop current run"
    assert record["source"] == "codex-test"
    assert len(queue["pending"]) == 1
    assert queue["pending"][0]["content"] == "stop current run"
    assert updated_runtime["pending_user_message_count"] == 1
    assert len(journal_lines) == 1
    assert json.loads(journal_lines[0])["type"] == "user_inbound"


def test_enqueue_user_message_deduplicates_same_content(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.mailbox")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    runtime_state = {
        "quest_id": "q001",
        "active_interaction_id": "progress-1",
        "pending_user_message_count": 1,
    }
    existing = {
        "message_id": "msg-0001",
        "source": "codex-test",
        "conversation_id": "local:default",
        "content": "stop current run",
        "created_at": "2026-03-29T00:00:00+00:00",
        "reply_to_interaction_id": "progress-1",
        "attachments": [],
        "status": "queued",
    }
    dump_json(quest_root / ".ds" / "runtime_state.json", runtime_state)
    dump_json(quest_root / ".ds" / "user_message_queue.json", {"version": 1, "pending": [existing], "completed": []})
    (quest_root / ".ds" / "interaction_journal.jsonl").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / ".ds" / "interaction_journal.jsonl").write_text("", encoding="utf-8")

    record = module.enqueue_user_message(
        quest_root=quest_root,
        runtime_state=runtime_state,
        message="stop current run",
        source="codex-test",
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    journal_lines = (quest_root / ".ds" / "interaction_journal.jsonl").read_text(encoding="utf-8").splitlines()

    assert record == existing
    assert len(queue["pending"]) == 1
    assert journal_lines == []


def test_post_quest_control_posts_json_payload(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.mailbox")
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "status": "stopped"}'

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["method"] = http_request.get_method()
        seen["timeout"] = timeout
        seen["content_type"] = http_request.headers["Content-Type"]
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.post_quest_control(
        daemon_url="http://127.0.0.1:20999",
        quest_id="q001",
        action="stop",
        source="codex-test",
    )

    assert result == {"ok": True, "status": "stopped"}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/q001/control"
    assert seen["method"] == "POST"
    assert seen["timeout"] == 10
    assert seen["content_type"] == "application/json"
    assert seen["payload"] == {"action": "stop", "source": "codex-test"}
