from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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
