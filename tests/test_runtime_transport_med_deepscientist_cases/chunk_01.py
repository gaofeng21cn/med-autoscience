from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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
