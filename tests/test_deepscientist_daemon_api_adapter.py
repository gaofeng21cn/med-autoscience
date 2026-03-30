from __future__ import annotations

import importlib
import json
from pathlib import Path


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_resolve_daemon_url_reads_runtime_config_and_normalizes_localhost(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 0.0.0.0\n  port: 21999\n",
    )

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == "http://127.0.0.1:21999"


def test_create_quest_posts_payload_to_daemon(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
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


def test_resume_quest_posts_control_action(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: localhost\n  port: 20999\n",
    )
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "status": "running"}'

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["method"] = http_request.get_method()
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.resume_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    assert result == {"ok": True, "status": "running"}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/control"
    assert seen["method"] == "POST"
    assert seen["timeout"] == 10
    assert seen["payload"] == {"action": "resume", "source": "medautosci-test"}
