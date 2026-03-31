from __future__ import annotations

import importlib
from pathlib import Path

def test_resolve_daemon_url_delegates_to_runtime_transport(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_resolve_daemon_url(*, runtime_root: Path) -> str:
        seen["runtime_root"] = runtime_root
        return "http://127.0.0.1:21999"

    monkeypatch.setattr(module.medicaldeepscientist_transport, "resolve_daemon_url", fake_resolve_daemon_url)

    result = module.resolve_daemon_url(runtime_root=runtime_root)

    assert result == "http://127.0.0.1:21999"
    assert seen == {"runtime_root": runtime_root}


def test_create_quest_delegates_to_runtime_transport(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}
    payload = {
        "goal": "Launch study 001",
        "quest_id": "001-risk",
        "auto_start": True,
    }

    def fake_create_quest(*, runtime_root: Path, payload: dict[str, object]) -> dict[str, object]:
        seen["runtime_root"] = runtime_root
        seen["payload"] = payload
        return {"ok": True, "snapshot": {"quest_id": "001-risk"}}

    monkeypatch.setattr(module.medicaldeepscientist_transport, "create_quest", fake_create_quest)

    result = module.create_quest(
        runtime_root=runtime_root,
        payload=payload,
    )

    assert result == {"ok": True, "snapshot": {"quest_id": "001-risk"}}
    assert seen == {
        "runtime_root": runtime_root,
        "payload": payload,
    }


def test_resume_quest_delegates_to_runtime_transport(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        seen["runtime_root"] = runtime_root
        seen["quest_id"] = quest_id
        seen["source"] = source
        return {"ok": True, "status": "running"}

    monkeypatch.setattr(module.medicaldeepscientist_transport, "resume_quest", fake_resume_quest)

    result = module.resume_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    assert result == {"ok": True, "status": "running"}
    assert seen == {
        "runtime_root": runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }


def test_pause_quest_delegates_to_runtime_transport(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.adapters.deepscientist.daemon_api")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    def fake_pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, object]:
        seen["runtime_root"] = runtime_root
        seen["quest_id"] = quest_id
        seen["source"] = source
        return {"ok": True, "status": "paused"}

    monkeypatch.setattr(module.medicaldeepscientist_transport, "pause_quest", fake_pause_quest)

    result = module.pause_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    assert result == {"ok": True, "status": "paused"}
    assert seen == {
        "runtime_root": runtime_root,
        "quest_id": "001-risk",
        "source": "medautosci-test",
    }
