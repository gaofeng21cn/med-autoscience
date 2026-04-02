from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_daemon_url_prefers_runtime_daemon_state(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "runtime" / "daemon.json",
        json.dumps({"url": "http://127.0.0.1:21999/"}) + "\n",
    )
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 0.0.0.0\n  port: 20999\n",
    )

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"status": "ok", "home": str(runtime_root.resolve())}).encode("utf-8")

    def fake_urlopen(http_request, timeout: int):
        assert http_request.full_url == "http://127.0.0.1:21999/api/health"
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == "http://127.0.0.1:21999"


def test_resolve_daemon_url_falls_back_to_runtime_config_and_normalizes_localhost(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 0.0.0.0\n  port: 21999\n",
    )

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == "http://127.0.0.1:21999"


def test_resolve_daemon_url_ignores_stale_daemon_state_when_health_home_mismatches_runtime_root(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "runtime" / "daemon.json",
        json.dumps({"url": "http://127.0.0.1:21999/"}) + "\n",
    )
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 0.0.0.0\n  port: 21001\n",
    )

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"status": "ok", "home": "/tmp/other-workspace/runtime"}).encode("utf-8")

    def fake_urlopen(http_request, timeout: int):
        assert http_request.full_url == "http://127.0.0.1:21999/api/health"
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == "http://127.0.0.1:21001"


def test_create_quest_posts_payload_to_daemon(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "snapshot": {"quest_id": "001-risk"}}'

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["method"] = http_request.get_method()
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.create_quest(
        runtime_root=runtime_root,
        payload={
            "goal": "Launch study 001",
            "quest_id": "001-risk",
            "auto_start": True,
        },
    )

    assert result == {"ok": True, "snapshot": {"quest_id": "001-risk"}}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests"
    assert seen["method"] == "POST"
    assert seen["timeout"] == 10
    assert seen["payload"] == {"goal": "Launch study 001", "quest_id": "001-risk", "auto_start": True}


def test_chat_quest_posts_text_and_reply_target(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "message": {"id": "msg-001"}}'

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.chat_quest(
        runtime_root=runtime_root,
        quest_id="001-risk",
        text="同意",
        source="medautosci-test",
        reply_to_interaction_id="decision-001",
    )

    assert result == {"ok": True, "message": {"id": "msg-001"}}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/chat"
    assert seen["timeout"] == 10
    assert seen["payload"] == {
        "text": "同意",
        "source": "medautosci-test",
        "reply_to_interaction_id": "decision-001",
    }


def test_artifact_interact_posts_payload(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"status": "ok", "interaction_id": "decision-001"}'

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.artifact_interact(
        runtime_root=runtime_root,
        quest_id="001-risk",
        payload={"kind": "decision_request", "reply_schema": {"decision_type": "quest_completion_approval"}},
    )

    assert result == {"status": "ok", "interaction_id": "decision-001"}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/artifact/interact"
    assert seen["timeout"] == 10
    assert seen["payload"] == {
        "kind": "decision_request",
        "reply_schema": {"decision_type": "quest_completion_approval"},
    }


def test_artifact_complete_quest_posts_summary(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "status": "completed"}'

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.artifact_complete_quest(
        runtime_root=runtime_root,
        quest_id="001-risk",
        summary="Study completed.",
    )

    assert result == {"ok": True, "status": "completed"}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/artifact/complete"
    assert seen["timeout"] == 10
    assert seen["payload"] == {"summary": "Study completed."}


def test_sync_completion_with_approval_chains_transport_calls(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        module,
        "artifact_interact",
        lambda *, runtime_root, quest_id, payload: calls.append(("request", payload))
        or {
            "status": "ok",
            "interaction_id": "decision-001",
        },
    )
    monkeypatch.setattr(
        module,
        "chat_quest",
        lambda *, runtime_root, quest_id, text, source, reply_to_interaction_id=None: calls.append(
            (
                "approve",
                {
                    "text": text,
                    "source": source,
                    "reply_to_interaction_id": reply_to_interaction_id,
                },
            )
        )
        or {"ok": True, "message": {"id": "msg-approval"}},
    )
    monkeypatch.setattr(
        module,
        "artifact_complete_quest",
        lambda *, runtime_root, quest_id, summary: calls.append(("complete", summary))
        or {
            "ok": True,
            "status": "completed",
            "snapshot": {"quest_id": quest_id, "status": "completed"},
        },
    )

    result = module.sync_completion_with_approval(
        runtime_root=runtime_root,
        quest_id="001-risk",
        decision_request_payload={"kind": "decision_request", "message": "approve completion"},
        approval_text="同意",
        summary="Study completed.",
        source="medautosci-test",
    )

    assert result == {
        "completion_request": {
            "status": "ok",
            "interaction_id": "decision-001",
        },
        "approval_message": {
            "ok": True,
            "message": {"id": "msg-approval"},
        },
        "completion": {
            "ok": True,
            "status": "completed",
            "snapshot": {"quest_id": "001-risk", "status": "completed"},
        },
    }
    assert calls == [
        ("request", {"kind": "decision_request", "message": "approve completion"}),
        (
            "approve",
            {
                "text": "同意",
                "source": "medautosci-test",
                "reply_to_interaction_id": "decision-001",
            },
        ),
        ("complete", "Study completed."),
    ]


def test_sync_completion_with_approval_rejects_invalid_transport_sequence(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"

    monkeypatch.setattr(
        module,
        "artifact_interact",
        lambda *, runtime_root, quest_id, payload: {"status": "ok"},
    )

    with pytest.raises(RuntimeError, match="failed to create quest completion approval request"):
        module.sync_completion_with_approval(
            runtime_root=runtime_root,
            quest_id="001-risk",
            decision_request_payload={"kind": "decision_request"},
            approval_text="同意",
            summary="Study completed.",
            source="medautosci-test",
        )


def test_post_quest_control_posts_json_payload(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
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


def test_resume_quest_posts_resume_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_post_quest_control(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "status": "running"}

    monkeypatch.setattr(module, "post_quest_control", fake_post_quest_control)

    result = module.resume_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    assert result == {"ok": True, "status": "running"}
    assert seen == {
        "runtime_root": runtime_root,
        "quest_id": "001-risk",
        "action": "resume",
        "source": "medautosci-test",
    }


def test_pause_quest_posts_pause_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_post_quest_control(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module, "post_quest_control", fake_post_quest_control)

    result = module.pause_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    assert result == {"ok": True, "status": "paused"}
    assert seen == {
        "runtime_root": runtime_root,
        "quest_id": "001-risk",
        "action": "pause",
        "source": "medautosci-test",
    }


def test_stop_quest_posts_stop_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_post_quest_control(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "status": "stopped"}

    monkeypatch.setattr(module, "post_quest_control", fake_post_quest_control)

    result = module.stop_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    assert result == {"ok": True, "status": "stopped"}
    assert seen == {
        "runtime_root": runtime_root,
        "quest_id": "001-risk",
        "action": "stop",
        "source": "medautosci-test",
    }


def test_list_quest_bash_sessions_reads_daemon_sessions(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                [
                    {"bash_id": "s1", "status": "running"},
                    {"bash_id": "s2", "status": "completed"},
                ]
            ).encode("utf-8")

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["method"] = http_request.get_method()
        seen["timeout"] = timeout
        seen["accept"] = http_request.headers["Accept"]
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.list_quest_bash_sessions(runtime_root=runtime_root, quest_id="001-risk")

    assert result == [
        {"bash_id": "s1", "status": "running"},
        {"bash_id": "s2", "status": "completed"},
    ]
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/bash/sessions?limit=200"
    assert seen["method"] == "GET"
    assert seen["timeout"] == 10
    assert seen["accept"] == "application/json"


def test_inspect_quest_live_bash_sessions_reports_live_and_none(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "list_quest_bash_sessions",
        lambda **kwargs: [
            {"bash_id": "s1", "status": "completed"},
            {"bash_id": "s2", "status": "terminating"},
        ],
    )
    live_result = module.inspect_quest_live_bash_sessions(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert live_result == {
        "ok": True,
        "status": "live",
        "session_count": 2,
        "live_session_count": 1,
        "live_session_ids": ["s2"],
    }

    monkeypatch.setattr(
        module,
        "list_quest_bash_sessions",
        lambda **kwargs: [
            {"bash_id": "s1", "status": "completed"},
        ],
    )
    none_result = module.inspect_quest_live_bash_sessions(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert none_result == {
        "ok": True,
        "status": "none",
        "session_count": 1,
        "live_session_count": 0,
        "live_session_ids": [],
    }


def test_inspect_quest_live_bash_sessions_reports_unknown_when_daemon_probe_fails(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "list_quest_bash_sessions",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("daemon unavailable")),
    )

    result = module.inspect_quest_live_bash_sessions(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result == {
        "ok": False,
        "status": "unknown",
        "session_count": None,
        "live_session_count": None,
        "live_session_ids": [],
        "error": "daemon unavailable",
    }


def test_inspect_quest_runtime_reads_local_status_and_live_sessions(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: 001-risk\n", encoding="utf-8")

    monkeypatch.setattr(module.quest_state, "quest_status", lambda path: "running")
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda *, runtime_root, quest_id, timeout=10: {
            "ok": True,
            "status": "live",
            "session_count": 1,
            "live_session_count": 1,
            "live_session_ids": ["sess-1"],
        },
    )

    result = module.inspect_quest_runtime(
        runtime_root=tmp_path / "runtime",
        quest_root=quest_root,
        quest_id="001-risk",
    )

    assert result == {
        "quest_exists": True,
        "quest_status": "running",
        "bash_session_audit": {
            "ok": True,
            "status": "live",
            "session_count": 1,
            "live_session_count": 1,
            "live_session_ids": ["sess-1"],
        },
    }


def test_inspect_quest_runtime_skips_live_probe_for_non_running_states(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: 001-risk\n", encoding="utf-8")

    monkeypatch.setattr(module.quest_state, "quest_status", lambda path: "paused")
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("live probe should not run")),
    )

    result = module.inspect_quest_runtime(
        runtime_root=tmp_path / "runtime",
        quest_root=quest_root,
        quest_id="001-risk",
    )

    assert result == {
        "quest_exists": True,
        "quest_status": "paused",
    }
