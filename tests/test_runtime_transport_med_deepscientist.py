from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess
from urllib import error

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


def test_ensure_managed_daemon_restarts_stale_launcher_state(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "ops" / "med-deepscientist" / "runtime"
    launcher_path = tmp_path / "bin" / "ds.js"
    write_text(
        runtime_root.parent / "config.env",
        f'MED_DEEPSCIENTIST_LAUNCHER="{launcher_path}"\n',
    )
    write_text(launcher_path, "#!/usr/bin/env bash\nexit 0\n")
    launcher_path.chmod(0o755)

    status_stale = {
        "healthy": False,
        "identity_match": False,
        "managed": True,
        "home": str(runtime_root),
        "url": "http://127.0.0.1:21001",
        "daemon": {"pid": 77838},
        "health": None,
    }
    status_healthy = {
        "healthy": True,
        "identity_match": True,
        "managed": True,
        "home": str(runtime_root),
        "url": "http://127.0.0.1:21001",
        "daemon": {"pid": 88991},
        "health": {"status": "ok", "home": str(runtime_root), "daemon_id": "daemon-001"},
    }
    calls: list[list[str]] = []

    def fake_run(args, capture_output, text, check, timeout):
        calls.append(list(args))
        if args[-1] == "--status":
            payload = status_stale if len([item for item in calls if item[-1] == "--status"]) == 1 else status_healthy
            return subprocess.CompletedProcess(args, 1 if payload is status_stale else 0, json.dumps(payload), "")
        if "--daemon-only" in args:
            return subprocess.CompletedProcess(args, 0, "", "")
        raise AssertionError(f"unexpected launcher args: {args}")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.ensure_managed_daemon(runtime_root=runtime_root)

    assert result == status_healthy
    assert calls == [
        [str(launcher_path), "--home", str(runtime_root), "--status"],
        [str(launcher_path), "--home", str(runtime_root), "--daemon-only", "--no-browser", "--skip-update-check"],
        [str(launcher_path), "--home", str(runtime_root), "--status"],
    ]


def test_create_quest_posts_payload_to_daemon(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
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
    monkeypatch.setattr(module, "ensure_managed_daemon", lambda *, runtime_root: {"url": "http://127.0.0.1:20999"})

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

def test_create_quest_ensures_managed_daemon_before_posting(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    monkeypatch.setattr(module, "ensure_managed_daemon", lambda *, runtime_root: {"url": "http://127.0.0.1:21999"})
    monkeypatch.setattr(
        module,
        "_post_json",
        lambda *, url, payload, timeout=10: seen.update({"url": url, "payload": payload, "timeout": timeout})
        or {"ok": True, "snapshot": {"quest_id": "001-risk"}},
    )
    monkeypatch.setattr(
        module,
        "resolve_daemon_url",
        lambda *, runtime_root: (_ for _ in ()).throw(AssertionError("create_quest should ensure daemon first")),
    )

    result = module.create_quest(
        runtime_root=runtime_root,
        payload={"quest_id": "001-risk", "auto_start": False},
    )

    assert result == {"ok": True, "snapshot": {"quest_id": "001-risk"}}
    assert seen == {
        "url": "http://127.0.0.1:21999/api/quests",
        "payload": {"quest_id": "001-risk", "auto_start": False},
        "timeout": 10,
    }


def test_create_quest_wraps_http_error_as_runtime_error(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"

    class FakeHttpError(error.HTTPError):
        def __init__(self) -> None:
            super().__init__(
                url="http://127.0.0.1:21999/api/quests",
                code=503,
                msg="Service Unavailable",
                hdrs=None,
                fp=None,
            )

        def read(self) -> bytes:
            return b'{"error":"daemon rejected create"}'

    monkeypatch.setattr(module, "ensure_managed_daemon", lambda *, runtime_root: {"url": "http://127.0.0.1:21999"})
    monkeypatch.setattr(module, "_post_json", lambda **kwargs: (_ for _ in ()).throw(FakeHttpError()))

    with pytest.raises(RuntimeError, match='Quest create request failed with HTTP 503: \\{"error":"daemon rejected create"\\}'):
        module.create_quest(runtime_root=runtime_root, payload={"quest_id": "001-risk"})


def test_ensure_managed_daemon_wraps_launcher_contract_errors(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "ops" / "med-deepscientist" / "runtime"

    monkeypatch.setattr(
        module,
        "_run_launcher",
        lambda *, runtime_root, args, timeout=120: (_ for _ in ()).throw(
            ValueError("MED_DEEPSCIENTIST_LAUNCHER is not configured")
        ),
    )

    with pytest.raises(RuntimeError, match="launcher contract failed"):
        module.ensure_managed_daemon(runtime_root=runtime_root)


def test_create_quest_rejects_missing_stable_snapshot_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    monkeypatch.setattr(module, "ensure_managed_daemon", lambda *, runtime_root: {"url": "http://127.0.0.1:20999"})

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true}'

    monkeypatch.setattr(module.request, "urlopen", lambda http_request, timeout: FakeResponse())

    with pytest.raises(RuntimeError, match="missing stable quest create contract"):
        module.create_quest(
            runtime_root=runtime_root,
            payload={"goal": "Launch study 001", "quest_id": "001-risk"},
        )


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


def test_chat_quest_posts_typed_decision_response_when_provided(monkeypatch, tmp_path: Path) -> None:
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
            return b'{"ok": true, "message": {"id": "msg-typed"}}'

    def fake_urlopen(http_request, timeout: int):
        seen["payload"] = json.loads(http_request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.chat_quest(
        runtime_root=runtime_root,
        quest_id="001-risk",
        text="structured approval",
        source="medautosci-test",
        reply_to_interaction_id="decision-001",
        decision_response={"decision_type": "quest_completion_approval", "approved": True},
    )

    assert result == {"ok": True, "message": {"id": "msg-typed"}}
    assert seen["payload"] == {
        "text": "structured approval",
        "source": "medautosci-test",
        "reply_to_interaction_id": "decision-001",
        "decision_response": {
            "decision_type": "quest_completion_approval",
            "approved": True,
        },
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
            return b'{"ok": true, "status": "completed", "snapshot": {"quest_id": "001-risk", "status": "completed"}, "summary_refresh": {"ok": true}}'

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

    assert result == {
        "ok": True,
        "status": "completed",
        "snapshot": {"quest_id": "001-risk", "status": "completed"},
        "summary_refresh": {"ok": True},
    }
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
        lambda *, runtime_root, quest_id, text, source, reply_to_interaction_id=None, decision_response=None: calls.append(
            (
                "approve",
                {
                    "text": text,
                    "source": source,
                    "reply_to_interaction_id": reply_to_interaction_id,
                    "decision_response": decision_response,
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
            "summary_refresh": {"ok": True},
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
            "summary_refresh": {"ok": True},
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
                "decision_response": {
                    "decision_type": "quest_completion_approval",
                    "approved": True,
                },
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
            return b'{"ok": true, "quest_id": "q001", "action": "stop", "status": "stopped", "snapshot": {"status": "stopped"}}'

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

    assert result == {
        "ok": True,
        "quest_id": "q001",
        "action": "stop",
        "status": "stopped",
        "snapshot": {"status": "stopped"},
    }
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


def test_post_quest_control_ensures_managed_daemon_before_resume(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    monkeypatch.setattr(module, "ensure_managed_daemon", lambda *, runtime_root: {"url": "http://127.0.0.1:21999"})
    monkeypatch.setattr(
        module,
        "_post_json",
        lambda *, url, payload, timeout=10: seen.update({"url": url, "payload": payload, "timeout": timeout})
        or {
            "ok": True,
            "quest_id": "001-risk",
            "action": "resume",
            "status": "running",
            "snapshot": {"status": "running"},
        },
    )
    monkeypatch.setattr(
        module,
        "resolve_daemon_url",
        lambda *, runtime_root: (_ for _ in ()).throw(AssertionError("resume should ensure daemon first")),
    )

    result = module.post_quest_control(
        runtime_root=runtime_root,
        quest_id="001-risk",
        action="resume",
        source="medautosci-test",
    )

    assert result == {
        "ok": True,
        "quest_id": "001-risk",
        "action": "resume",
        "status": "running",
        "snapshot": {"status": "running"},
    }
    assert seen == {
        "url": "http://127.0.0.1:21999/api/quests/001-risk/control",
        "payload": {"action": "resume", "source": "medautosci-test"},
        "timeout": 10,
    }


def test_update_quest_startup_context_patches_payload(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)

    def fake_patch_json(**kwargs):
        seen.update(kwargs)
        return {"ok": True, "snapshot": {"quest_id": "001-risk", "startup_contract": {"scope": "full_research"}}}

    monkeypatch.setattr(module, "_patch_json", fake_patch_json)
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    result = handler(
        runtime_root=runtime_root,
        quest_id="001-risk",
        startup_contract={"scope": "full_research"},
    )

    assert result == {"ok": True, "snapshot": {"quest_id": "001-risk", "startup_contract": {"scope": "full_research"}}}
    assert seen == {
        "url": "http://127.0.0.1:20999/api/quests/001-risk/startup-context",
        "payload": {"startup_contract": {"scope": "full_research"}},
    }


def test_update_quest_startup_context_rejects_unclassified_startup_contract_keys_before_patch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")
    monkeypatch.setattr(
        module,
        "_patch_json",
        lambda **kwargs: pytest.fail("startup-context patch should reject undeclared keys before transport"),
    )

    with pytest.raises(ValueError, match="unclassified startup contract keys: unexpected_field"):
        handler(
            runtime_root=runtime_root,
            quest_id="001-risk",
            startup_contract={
                "scope": "full_research",
                "unexpected_field": {"should": "not-become-stable"},
            },
        )


def test_update_quest_startup_context_rejects_missing_stable_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)

    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda http_request, timeout: type(
            "FakeResponse",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: None,
                "read": lambda self: b'{"ok": true, "snapshot": {}}',
            },
        )(),
    )

    with pytest.raises(RuntimeError, match="missing stable startup-context contract"):
        handler(
            runtime_root=runtime_root,
            quest_id="001-risk",
            startup_contract={"scope": "full_research"},
        )


def test_update_quest_startup_context_rejects_unclassified_roundtrip_keys(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )

    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda http_request, timeout: type(
            "FakeResponse",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: None,
                "read": lambda self: (
                    b'{"ok": true, "quest_id": "001-risk", "snapshot": {"quest_id": "001-risk", '
                    b'"startup_contract": {"scope": "full_research", "unexpected_field": "should-fail"}}}'
                ),
            },
        )(),
    )

    with pytest.raises(RuntimeError, match="unclassified startup contract keys: unexpected_field"):
        module.update_quest_startup_context(
            runtime_root=runtime_root,
            quest_id="001-risk",
            startup_contract={"scope": "full_research"},
        )


def test_update_quest_startup_context_requires_echoed_startup_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)

    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda http_request, timeout: type(
            "FakeResponse",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: None,
                "read": lambda self: b'{"ok": true, "quest_id": "001-risk", "snapshot": {"quest_id": "001-risk"}}',
            },
        )(),
    )

    with pytest.raises(RuntimeError, match="missing stable startup-context contract"):
        handler(
            runtime_root=runtime_root,
            quest_id="001-risk",
            startup_contract={"scope": "full_research"},
        )


def test_update_quest_startup_context_requires_requested_baseline_ref_roundtrip(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)

    monkeypatch.setattr(
        module.request,
        "urlopen",
        lambda http_request, timeout: type(
            "FakeResponse",
            (),
            {
                "__enter__": lambda self: self,
                "__exit__": lambda self, exc_type, exc, tb: None,
                "read": lambda self: b'{"ok": true, "quest_id": "001-risk", "snapshot": {"quest_id": "001-risk", "startup_contract": {"schema_version": 4}}}',
            },
        )(),
    )

    with pytest.raises(RuntimeError, match="requested_baseline_ref roundtrip"):
        handler(
            runtime_root=runtime_root,
            quest_id="001-risk",
            requested_baseline_ref={"baseline_id": "demo-baseline"},
        )


def test_update_quest_startup_context_patches_requested_baseline_ref_without_create_side_effects(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")
    monkeypatch.setattr(
        module,
        "_patch_json",
        lambda **kwargs: seen.update(kwargs)
        or {
            "ok": True,
            "quest_id": "001-risk",
            "snapshot": {
                "quest_id": "001-risk",
                "startup_contract": {"schema_version": 4},
                "requested_baseline_ref": {"baseline_id": "demo-baseline"},
            },
        },
    )

    result = handler(
        runtime_root=runtime_root,
        quest_id="001-risk",
        requested_baseline_ref={"baseline_id": "demo-baseline"},
    )

    assert result["snapshot"]["requested_baseline_ref"] == {"baseline_id": "demo-baseline"}
    assert seen == {
        "url": "http://127.0.0.1:20999/api/quests/001-risk/startup-context",
        "payload": {"requested_baseline_ref": {"baseline_id": "demo-baseline"}},
    }


def test_update_quest_startup_context_fails_closed_when_daemon_is_unreachable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(
        quest_root / "quest.yaml",
        "quest_id: 001-risk\nstatus: paused\nstartup_contract:\n  scope: scout\n",
    )

    def fake_patch_json(**kwargs):
        raise error.URLError(ConnectionRefusedError(61, "Connection refused"))

    monkeypatch.setattr(module, "_patch_json", fake_patch_json)
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    with pytest.raises(RuntimeError, match="startup-context request failed"):
        module.update_quest_startup_context(
            runtime_root=runtime_root,
            quest_id="001-risk",
            startup_contract={"scope": "full_research"},
        )

    quest_payload = module._load_yaml_dict(quest_root / "quest.yaml")
    assert quest_payload["startup_contract"] == {"scope": "scout"}
    assert "updated_at" not in quest_payload


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

def test_pause_quest_fails_closed_when_daemon_is_unreachable_even_without_active_run_id(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: active\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "active",
                "display_status": "active",
                "active_run_id": None,
                "stop_reason": None,
            }
        )
        + "\n",
    )

    def fake_post_json(**kwargs):
        raise error.URLError(ConnectionRefusedError(61, "Connection refused"))

    monkeypatch.setattr(module, "_post_json", fake_post_json)
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    with pytest.raises(RuntimeError, match="Quest control request failed"):
        module.pause_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    runtime_state = module._load_json_dict(quest_root / ".ds" / "runtime_state.json")
    quest_payload = module._load_yaml_dict(quest_root / "quest.yaml")
    assert runtime_state["status"] == "active"
    assert runtime_state["display_status"] == "active"
    assert runtime_state["active_run_id"] is None
    assert runtime_state["stop_reason"] is None
    assert quest_payload["status"] == "active"
    assert "updated_at" not in quest_payload


def test_pause_quest_fails_closed_when_daemon_is_unreachable_with_active_run_id_present(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: active\nactive_run_id: run-live\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "active",
                "display_status": "active",
                "active_run_id": "run-live",
            }
        )
        + "\n",
    )

    def fake_post_json(**kwargs):
        raise error.URLError(ConnectionRefusedError(61, "Connection refused"))

    monkeypatch.setattr(module, "_post_json", fake_post_json)
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    with pytest.raises(RuntimeError, match="Quest control request failed"):
        module.pause_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")

    runtime_state = module._load_json_dict(quest_root / ".ds" / "runtime_state.json")
    quest_payload = module._load_yaml_dict(quest_root / "quest.yaml")
    assert runtime_state["status"] == "active"
    assert runtime_state["display_status"] == "active"
    assert runtime_state["active_run_id"] == "run-live"
    assert quest_payload["status"] == "active"
    assert quest_payload["active_run_id"] == "run-live"


def test_stop_quest_fails_closed_when_daemon_is_unreachable(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: active\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "active",
                "display_status": "active",
                "active_run_id": None,
                "stop_reason": None,
            }
        )
        + "\n",
    )

    monkeypatch.setattr(module, "_post_json", lambda **kwargs: (_ for _ in ()).throw(error.URLError(ConnectionRefusedError(61, "Connection refused"))))
    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    with pytest.raises(RuntimeError, match="Quest control request failed"):
        module.stop_quest(runtime_root=runtime_root, quest_id="001-risk", source="medautosci-test")


def test_post_quest_control_rejects_missing_stable_control_contract(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return b'{"ok": true, "quest_id": "q001"}'

    monkeypatch.setattr(module.request, "urlopen", lambda http_request, timeout: FakeResponse())

    with pytest.raises(RuntimeError, match="missing stable quest control contract"):
        module.post_quest_control(
            daemon_url="http://127.0.0.1:20999",
            quest_id="q001",
            action="stop",
            source="codex-test",
        )


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


def test_list_quest_bash_sessions_rejects_entries_missing_stable_fields(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "config" / "config.yaml",
        "ui:\n  host: 127.0.0.1\n  port: 20999\n",
    )

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps([{"status": "running"}]).encode("utf-8")

    monkeypatch.setattr(module.request, "urlopen", lambda http_request, timeout: FakeResponse())

    with pytest.raises(RuntimeError, match="stable bash session contract"):
        module.list_quest_bash_sessions(runtime_root=runtime_root, quest_id="001-risk")


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


def test_get_quest_session_reads_session_payload(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    seen: dict[str, object] = {}

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "ok": True,
                    "quest_id": "001-risk",
                    "snapshot": {"quest_id": "001-risk", "active_run_id": "run-1"},
                    "runtime_audit": {
                        "ok": True,
                        "status": "none",
                        "source": "daemon_turn_worker",
                        "active_run_id": "run-1",
                        "worker_running": False,
                        "worker_pending": False,
                        "stop_requested": False,
                    },
                }
            ).encode("utf-8")

    def fake_urlopen(http_request, timeout: int):
        seen["url"] = http_request.full_url
        seen["method"] = http_request.get_method()
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.get_quest_session(daemon_url="http://127.0.0.1:20999", quest_id="001-risk")

    assert result == {
        "ok": True,
        "quest_id": "001-risk",
        "snapshot": {"quest_id": "001-risk", "active_run_id": "run-1"},
        "runtime_audit": {
            "ok": True,
            "status": "none",
            "source": "daemon_turn_worker",
            "active_run_id": "run-1",
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
        },
    }
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/session"
    assert seen["method"] == "GET"
    assert seen["timeout"] == 10


def test_get_quest_session_rejects_missing_runtime_audit_contract(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps({"ok": True, "quest_id": "001-risk", "snapshot": {}}).encode("utf-8")

    monkeypatch.setattr(module.request, "urlopen", lambda http_request, timeout: FakeResponse())

    with pytest.raises(RuntimeError, match="missing stable quest session contract"):
        module.get_quest_session(daemon_url="http://127.0.0.1:20999", quest_id="001-risk")


def test_inspect_quest_live_runtime_reports_live_and_none(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {"active_run_id": "run-live"},
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )
    live_result = module.inspect_quest_live_runtime(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert live_result == {
        "ok": True,
        "status": "live",
        "source": "daemon_turn_worker",
        "active_run_id": "run-live",
        "worker_running": True,
        "worker_pending": False,
        "stop_requested": False,
    }

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {"active_run_id": "run-stale"},
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": "run-stale",
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )
    none_result = module.inspect_quest_live_runtime(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert none_result == {
        "ok": True,
        "status": "none",
        "source": "daemon_turn_worker",
        "active_run_id": "run-stale",
        "worker_running": False,
        "worker_pending": False,
        "stop_requested": False,
    }


def test_inspect_quest_live_execution_combines_runtime_and_bash_audits(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "session_count": 1,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    )

    live_result = module.inspect_quest_live_execution(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert live_result == {
        "ok": True,
        "status": "live",
        "source": "combined_runner_or_bash_session",
        "active_run_id": "run-live",
        "runner_live": True,
        "bash_live": False,
        "runtime_audit": {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
        "bash_session_audit": {
            "ok": True,
            "status": "none",
            "session_count": 1,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    }

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "source": "daemon_turn_worker",
            "active_run_id": "run-stale",
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    )

    none_result = module.inspect_quest_live_execution(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert none_result == {
        "ok": True,
        "status": "none",
        "source": "combined_runner_or_bash_session",
        "active_run_id": "run-stale",
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": True,
            "status": "none",
            "source": "daemon_turn_worker",
            "active_run_id": "run-stale",
            "worker_running": False,
            "worker_pending": False,
            "stop_requested": False,
        },
        "bash_session_audit": {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
    }


def test_inspect_quest_live_execution_falls_back_to_local_runtime_state_contract(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: active\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "active",
                "display_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
            }
        )
        + "\n",
    )

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
    )

    result = module.inspect_quest_live_execution(runtime_root=runtime_root, quest_id="001-risk")

    assert result == {
        "ok": True,
        "status": "none",
        "source": "local_runtime_state_contract",
        "active_run_id": None,
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
        "bash_session_audit": {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
        "local_runtime_state": {
            "status": "active",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "decision",
        },
        "probe_error": "daemon unavailable | daemon unavailable",
    }


def test_inspect_quest_live_execution_keeps_unknown_when_local_runtime_state_is_running(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    quest_root = runtime_root / "quests" / "001-risk"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\nstatus: running\n")
    write_text(
        quest_root / ".ds" / "runtime_state.json",
        json.dumps(
            {
                "quest_id": "001-risk",
                "status": "running",
                "display_status": "running",
                "active_run_id": None,
            }
        )
        + "\n",
    )

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
    )
    monkeypatch.setattr(
        module,
        "inspect_quest_live_bash_sessions",
        lambda **kwargs: {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
    )

    result = module.inspect_quest_live_execution(runtime_root=runtime_root, quest_id="001-risk")

    assert result == {
        "ok": False,
        "status": "unknown",
        "source": "combined_runner_or_bash_session",
        "active_run_id": None,
        "runner_live": False,
        "bash_live": False,
        "runtime_audit": {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "daemon unavailable",
        },
        "bash_session_audit": {
            "ok": False,
            "status": "unknown",
            "session_count": None,
            "live_session_count": None,
            "live_session_ids": [],
            "error": "daemon unavailable",
        },
        "error": "daemon unavailable | daemon unavailable",
    }
