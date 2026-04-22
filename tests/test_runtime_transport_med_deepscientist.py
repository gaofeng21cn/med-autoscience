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


def _native_runtime_event_payload(*, quest_id: str, artifact_path: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "event_id": f"runtime-event::{quest_id}::runtime_control_applied::2026-04-11T00:00:00+00:00",
        "quest_id": quest_id,
        "emitted_at": "2026-04-11T00:00:00+00:00",
        "event_source": "daemon_app",
        "event_kind": "runtime_control_applied",
        "summary_ref": f"quest:{quest_id}:runtime_control_applied",
        "status_snapshot": {
            "quest_status": "paused",
            "display_status": "paused",
            "active_run_id": "run-native",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "stop_reason": "user_pause_requested",
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "paused_by_controller",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "outer_loop_input": {
            "quest_status": "paused",
            "display_status": "paused",
            "active_run_id": "run-native",
            "runtime_liveness_status": "none",
            "worker_running": False,
            "stop_reason": "user_pause_requested",
            "continuation_policy": "resume_allowed",
            "continuation_anchor": "decision",
            "continuation_reason": "paused_by_controller",
            "pending_user_message_count": 0,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "active_interaction_id": None,
            "last_transition_at": "2026-04-11T00:00:00+00:00",
        },
        "artifact_path": str(artifact_path),
        "summary": "runtime paused by controller",
    }


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


def test_launcher_command_prefers_explicit_node_binary_for_node_shebang(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "ops" / "med-deepscientist" / "runtime"
    launcher_path = tmp_path / "bin" / "ds.js"
    node_path = tmp_path / "bin" / "node"
    write_text(
        runtime_root.parent / "config.env",
        f'MED_DEEPSCIENTIST_LAUNCHER="{launcher_path}"\n',
    )
    write_text(launcher_path, "#!/usr/bin/env node\nconsole.log('launcher');\n")
    write_text(node_path, "#!/usr/bin/env bash\nexit 0\n")
    launcher_path.chmod(0o755)
    node_path.chmod(0o755)
    monkeypatch.setenv("MED_AUTOSCIENCE_NODE_BIN", str(node_path))

    command = module._launcher_command(runtime_root=runtime_root, args=("--status",))

    assert command == [str(node_path), str(launcher_path), "--home", str(runtime_root), "--status"]


def test_launcher_command_reads_node_binary_from_workspace_config_when_env_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    workspace_root = tmp_path / "workspace"
    runtime_root = workspace_root / "ops" / "med-deepscientist" / "runtime"
    launcher_path = tmp_path / "bin" / "ds.js"
    node_path = tmp_path / "bin" / "node"
    write_text(
        runtime_root.parent / "config.env",
        f'MED_DEEPSCIENTIST_LAUNCHER="{launcher_path}"\n',
    )
    write_text(
        workspace_root / "ops" / "medautoscience" / "config.env",
        f'MED_AUTOSCIENCE_NODE_BIN="{node_path}"\n',
    )
    write_text(launcher_path, "#!/usr/bin/env node\nconsole.log('launcher');\n")
    write_text(node_path, "#!/usr/bin/env bash\nexit 0\n")
    launcher_path.chmod(0o755)
    node_path.chmod(0o755)

    command = module._launcher_command(runtime_root=runtime_root, args=("--status",))

    assert command == [str(node_path), str(launcher_path), "--home", str(runtime_root), "--status"]


def test_launcher_command_switches_python_console_script_to_repo_js_launcher(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    workspace_root = tmp_path / "workspace"
    runtime_root = workspace_root / "ops" / "med-deepscientist" / "runtime"
    repo_root = tmp_path / "med-deepscientist"
    python_launcher_path = repo_root / ".venv" / "bin" / "ds"
    js_launcher_path = repo_root / "bin" / "ds.js"
    node_path = tmp_path / "bin" / "node"
    write_text(
        runtime_root.parent / "config.env",
        f'MED_DEEPSCIENTIST_LAUNCHER="{python_launcher_path}"\n',
    )
    write_text(
        workspace_root / "ops" / "medautoscience" / "config.env",
        f'MED_AUTOSCIENCE_NODE_BIN="{node_path}"\n',
    )
    write_text(
        python_launcher_path,
        "#!/tmp/python\n"
        "import sys\n"
        "from deepscientist.cli import main\n"
        "if __name__ == '__main__':\n"
        "    raise SystemExit(main())\n",
    )
    write_text(js_launcher_path, "#!/usr/bin/env node\nconsole.log('launcher');\n")
    write_text(node_path, "#!/usr/bin/env bash\nexit 0\n")
    python_launcher_path.chmod(0o755)
    js_launcher_path.chmod(0o755)
    node_path.chmod(0o755)

    command = module._launcher_command(runtime_root=runtime_root, args=("--status",))

    assert command == [str(node_path), str(js_launcher_path), "--home", str(runtime_root), "--status"]


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


def test_ensure_managed_daemon_recovers_from_truncated_launcher_status_using_runtime_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "ops" / "med-deepscientist" / "runtime"
    launcher_path = tmp_path / "bin" / "ds.js"
    write_text(
        runtime_root.parent / "config.env",
        f'MED_DEEPSCIENTIST_LAUNCHER="{launcher_path}"\n',
    )
    write_text(launcher_path, "#!/usr/bin/env bash\nexit 0\n")
    launcher_path.chmod(0o755)
    write_text(
        runtime_root / "runtime" / "daemon.json",
        json.dumps(
            {
                "pid": 77838,
                "host": "0.0.0.0",
                "port": 21001,
                "url": "http://127.0.0.1:21001",
                "bind_url": "http://0.0.0.0:21001",
                "log_path": str(runtime_root / "logs" / "daemon.log"),
                "started_at": "2026-04-08T00:00:00.000Z",
                "home": str(runtime_root),
                "daemon_id": "daemon-001",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    calls: list[tuple[str, ...]] = []

    def fake_run_launcher(*, runtime_root: Path, args: tuple[str, ...], timeout: int = 120):
        calls.append(args)
        assert args == ("--status",)
        return subprocess.CompletedProcess(
            [str(launcher_path), "--home", str(runtime_root), *args],
            0,
            '{"healthy": true, "identity_match": true, "managed": true, "home": "/tmp/truncated',
            "",
        )

    class FakeResponse:
        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {"status": "ok", "home": str(runtime_root.resolve()), "daemon_id": "daemon-001"}
            ).encode("utf-8")

    def fake_urlopen(http_request, timeout: int):
        assert http_request.full_url == "http://127.0.0.1:21001/api/health"
        return FakeResponse()

    monkeypatch.setattr(module, "_run_launcher", fake_run_launcher)
    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    result = module.ensure_managed_daemon(runtime_root=runtime_root)

    assert result["healthy"] is True
    assert result["identity_match"] is True
    assert result["url"] == "http://127.0.0.1:21001"
    assert result["daemon"]["daemon_id"] == "daemon-001"
    assert result["health"]["daemon_id"] == "daemon-001"
    assert calls == [("--status",)]


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
        decision_response={"decision_type": "external_secret_request", "provided": True},
    )

    assert result == {"ok": True, "message": {"id": "msg-typed"}}
    assert seen["payload"] == {
        "text": "structured approval",
        "source": "medautosci-test",
        "reply_to_interaction_id": "decision-001",
        "decision_response": {
            "decision_type": "external_secret_request",
            "provided": True,
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
        payload={"kind": "decision_request", "reply_schema": {"decision_type": "external_secret_request"}},
    )

    assert result == {"status": "ok", "interaction_id": "decision-001"}
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/artifact/interact"
    assert seen["timeout"] == 10
    assert seen["payload"] == {
        "kind": "decision_request",
        "reply_schema": {"decision_type": "external_secret_request"},
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
    assert seen["timeout"] == module.DAEMON_CONTROL_TIMEOUT_SECONDS
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
        "timeout": module.DAEMON_CONTROL_TIMEOUT_SECONDS,
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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    result = handler(
        runtime_root=runtime_root,
        quest_id="001-risk",
        startup_contract={"scope": "full_research"},
    )

    assert result == {"ok": True, "snapshot": {"quest_id": "001-risk", "startup_contract": {"scope": "full_research"}}}
    assert seen == {
        "url": "http://127.0.0.1:20999/api/quests/001-risk/startup-context",
        "payload": {"startup_contract": {"scope": "full_research"}},
        "timeout": module.DAEMON_CONTROL_TIMEOUT_SECONDS,
    }


def test_update_quest_startup_context_rejects_unclassified_startup_contract_keys_before_patch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    handler = getattr(module, "update_quest_startup_context", None)

    assert callable(handler)
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")
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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")
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
        "timeout": module.DAEMON_CONTROL_TIMEOUT_SECONDS,
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
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")

    with pytest.raises(RuntimeError, match="startup-context request failed"):
        module.update_quest_startup_context(
            runtime_root=runtime_root,
            quest_id="001-risk",
            startup_contract={"scope": "full_research"},
        )

    quest_payload = module._load_yaml_dict(quest_root / "quest.yaml")
    assert quest_payload["startup_contract"] == {"scope": "scout"}
    assert "updated_at" not in quest_payload


def test_update_quest_startup_context_uses_managed_daemon_url_for_resume_reentry(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    seen: dict[str, object] = {}

    monkeypatch.setattr(module, "resolve_daemon_url", lambda *, runtime_root: pytest.fail("resolve_daemon_url should not run"))
    monkeypatch.setattr(module, "_ensure_managed_daemon_url", lambda *, runtime_root: "http://127.0.0.1:20999")
    monkeypatch.setattr(
        module,
        "_patch_json",
        lambda **kwargs: seen.update(kwargs)
        or {
            "ok": True,
            "quest_id": "001-risk",
            "snapshot": {
                "quest_id": "001-risk",
                "startup_contract": {"scope": "full_research"},
            },
        },
    )

    result = module.update_quest_startup_context(
        runtime_root=runtime_root,
        quest_id="001-risk",
        startup_contract={"scope": "full_research"},
    )

    assert result["ok"] is True
    assert seen["url"] == "http://127.0.0.1:20999/api/quests/001-risk/startup-context"


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


def test_post_quest_control_wraps_daemon_timeout(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    def fake_urlopen(http_request, timeout: int):
        assert timeout == module.DAEMON_CONTROL_TIMEOUT_SECONDS
        raise TimeoutError("timed out")

    monkeypatch.setattr(module.request, "urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="Quest control request failed: timed out"):
        module.post_quest_control(
            daemon_url="http://127.0.0.1:20999",
            quest_id="q001",
            action="resume",
            source="codex-test",
        )


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


def test_get_quest_session_validates_and_exposes_native_runtime_event_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    artifact_path = tmp_path / "runtime" / "quests" / "001-risk" / "artifacts" / "reports" / "runtime_events" / "latest.json"
    native_event = _native_runtime_event_payload(quest_id="001-risk", artifact_path=artifact_path)

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
                    "snapshot": {"quest_id": "001-risk", "active_run_id": "run-native"},
                    "runtime_audit": {
                        "ok": True,
                        "status": "none",
                        "source": "daemon_turn_worker",
                        "active_run_id": "run-native",
                        "worker_running": False,
                        "worker_pending": False,
                        "stop_requested": False,
                    },
                    "runtime_event_ref": {
                        "event_id": str(native_event["event_id"]),
                        "artifact_path": str(artifact_path),
                        "summary_ref": str(native_event["summary_ref"]),
                    },
                    "runtime_event": native_event,
                }
            ).encode("utf-8")

    monkeypatch.setattr(module.request, "urlopen", lambda http_request, timeout: FakeResponse())

    result = module.get_quest_session(daemon_url="http://127.0.0.1:20999", quest_id="001-risk")

    assert result["runtime_event_ref"] == {
        "event_id": str(native_event["event_id"]),
        "artifact_path": str(artifact_path),
        "summary_ref": str(native_event["summary_ref"]),
    }
    assert result["runtime_event"] == native_event


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


def test_get_quest_session_preserves_live_runtime_audit_when_native_runtime_event_contract_is_invalid(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    artifact_path = tmp_path / "runtime" / "quests" / "001-risk" / "artifacts" / "reports" / "runtime_events" / "latest.json"
    native_event = _native_runtime_event_payload(quest_id="001-risk", artifact_path=artifact_path)
    native_event["status_snapshot"].pop("continuation_anchor")

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
                    "snapshot": {"quest_id": "001-risk", "active_run_id": "run-live"},
                    "runtime_audit": {
                        "ok": True,
                        "status": "live",
                        "source": "daemon_turn_worker",
                        "active_run_id": "run-live",
                        "worker_running": True,
                        "worker_pending": False,
                        "stop_requested": False,
                    },
                    "runtime_event_ref": {
                        "event_id": str(native_event["event_id"]),
                        "artifact_path": str(artifact_path),
                        "summary_ref": str(native_event["summary_ref"]),
                    },
                    "runtime_event": native_event,
                }
            ).encode("utf-8")

    monkeypatch.setattr(module.request, "urlopen", lambda http_request, timeout: FakeResponse())

    result = module.get_quest_session(daemon_url="http://127.0.0.1:20999", quest_id="001-risk")

    assert result["runtime_audit"] == {
        "ok": True,
        "status": "live",
        "source": "daemon_turn_worker",
        "active_run_id": "run-live",
        "worker_running": True,
        "worker_pending": False,
        "stop_requested": False,
    }
    assert "runtime_event_ref" not in result
    assert "runtime_event" not in result
    assert result["runtime_event_contract_error"] == "native runtime event status_snapshot missing continuation_anchor"


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


def test_inspect_quest_live_runtime_preserves_live_status_when_runtime_event_contract_is_invalid(
    monkeypatch,
) -> None:
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
            "runtime_event_contract_error": "native runtime event status_snapshot missing continuation_anchor",
        },
    )

    result = module.inspect_quest_live_runtime(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result == {
        "ok": True,
        "status": "live",
        "source": "daemon_turn_worker",
        "active_run_id": "run-live",
        "worker_running": True,
        "worker_pending": False,
        "stop_requested": False,
        "runtime_event_contract_error": "native runtime event status_snapshot missing continuation_anchor",
    }


def test_inspect_quest_live_runtime_passes_through_native_runtime_event_contract(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    artifact_path = tmp_path / "runtime" / "quests" / "001-risk" / "artifacts" / "reports" / "runtime_events" / "latest.json"
    native_event = _native_runtime_event_payload(quest_id="001-risk", artifact_path=artifact_path)

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {"active_run_id": "run-native"},
            "runtime_audit": {
                "ok": True,
                "status": "none",
                "source": "daemon_turn_worker",
                "active_run_id": "run-native",
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
            "runtime_event_ref": {
                "event_id": str(native_event["event_id"]),
                "artifact_path": str(artifact_path),
                "summary_ref": str(native_event["summary_ref"]),
            },
            "runtime_event": native_event,
        },
    )

    result = module.inspect_quest_live_runtime(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result["runtime_event_ref"] == {
        "event_id": str(native_event["event_id"]),
        "artifact_path": str(artifact_path),
        "summary_ref": str(native_event["summary_ref"]),
    }
    assert result["runtime_event"] == native_event


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


def test_inspect_quest_live_execution_degrades_stale_live_runtime_to_unknown(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "inspect_quest_live_runtime",
        lambda **kwargs: {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-stale",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "interaction_watchdog": {
                "last_artifact_interact_at": "2026-04-08T10:05:03+00:00",
                "seconds_since_last_artifact_interact": 3600,
                "tool_calls_since_last_artifact_interact": 0,
                "active_execution_window": True,
                "stale_visibility_gap": True,
                "inspection_due": True,
                "user_update_due": False,
            },
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
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

    result = module.inspect_quest_live_execution(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result == {
        "ok": False,
        "status": "unknown",
        "source": "combined_runner_or_bash_session",
        "active_run_id": "run-live-stale",
        "runner_live": True,
        "bash_live": False,
        "stale_progress": True,
        "liveness_guard_reason": "stale_progress_watchdog",
        "runtime_audit": {
            "ok": True,
            "status": "live",
            "source": "daemon_turn_worker",
            "active_run_id": "run-live-stale",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "interaction_watchdog": {
                "last_artifact_interact_at": "2026-04-08T10:05:03+00:00",
                "seconds_since_last_artifact_interact": 3600,
                "tool_calls_since_last_artifact_interact": 0,
                "active_execution_window": True,
                "stale_visibility_gap": True,
                "inspection_due": True,
                "user_update_due": False,
            },
            "stale_progress": True,
            "liveness_guard_reason": "stale_progress_watchdog",
        },
        "bash_session_audit": {
            "ok": True,
            "status": "none",
            "session_count": 0,
            "live_session_count": 0,
            "live_session_ids": [],
        },
        "error": "Live managed runtime exceeded the artifact interaction silence threshold.",
    }


def test_inspect_quest_live_runtime_flags_missing_first_progress_after_stale_run_start(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "active_run_id": "run-live-first-progress-missing",
                "last_transition_at": "2026-04-08T10:05:03+00:00",
                "interaction_watchdog": {
                    "last_artifact_interact_at": None,
                    "seconds_since_last_artifact_interact": None,
                    "tool_calls_since_last_artifact_interact": 0,
                    "last_tool_activity_at": None,
                    "seconds_since_last_tool_activity": None,
                    "active_execution_window": True,
                    "stale_visibility_gap": False,
                    "inspection_due": False,
                    "user_update_due": False,
                },
            },
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-first-progress-missing",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.inspect_quest_live_runtime(
        runtime_root=Path("/tmp/runtime"),
        quest_id="001-risk",
    )

    assert result == {
        "ok": True,
        "status": "live",
        "source": "daemon_turn_worker",
        "active_run_id": "run-live-first-progress-missing",
        "worker_running": True,
        "worker_pending": False,
        "stop_requested": False,
        "interaction_watchdog": {
            "last_artifact_interact_at": None,
            "seconds_since_last_artifact_interact": None,
            "tool_calls_since_last_artifact_interact": 0,
            "last_tool_activity_at": None,
            "seconds_since_last_tool_activity": None,
            "active_execution_window": True,
            "stale_visibility_gap": False,
            "inspection_due": False,
            "user_update_due": False,
        },
        "stale_progress": True,
        "liveness_guard_reason": "stale_progress_watchdog",
    }


def test_inspect_quest_live_runtime_falls_back_to_local_transition_timestamp_for_missing_first_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.runtime_transport.med_deepscientist")
    runtime_root = tmp_path / "runtime"
    write_text(
        runtime_root / "quests" / "001-risk" / ".ds" / "runtime_state.json",
        json.dumps({"last_transition_at": "2026-04-08T10:05:03+00:00"}) + "\n",
    )

    monkeypatch.setattr(
        module,
        "get_quest_session",
        lambda **kwargs: {
            "ok": True,
            "snapshot": {
                "active_run_id": "run-live-first-progress-missing",
                "last_transition_at": None,
                "interaction_watchdog": {
                    "last_artifact_interact_at": None,
                    "seconds_since_last_artifact_interact": None,
                    "tool_calls_since_last_artifact_interact": 0,
                    "last_tool_activity_at": None,
                    "seconds_since_last_tool_activity": None,
                    "active_execution_window": True,
                    "stale_visibility_gap": False,
                    "inspection_due": False,
                    "user_update_due": False,
                },
            },
            "runtime_audit": {
                "ok": True,
                "status": "live",
                "source": "daemon_turn_worker",
                "active_run_id": "run-live-first-progress-missing",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    )

    result = module.inspect_quest_live_runtime(
        runtime_root=runtime_root,
        quest_id="001-risk",
    )

    assert result["stale_progress"] is True
    assert result["liveness_guard_reason"] == "stale_progress_watchdog"


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
                "continuation_reason": "unchanged_finalize_state",
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
            "continuation_reason": "unchanged_finalize_state",
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
