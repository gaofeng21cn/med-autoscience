from __future__ import annotations

import importlib
import json
from pathlib import Path


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
