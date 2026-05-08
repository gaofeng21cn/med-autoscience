from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.test_cli_cases.shared import write_profile


def _sse_data_lines(output: str) -> list[dict[str, object]]:
    payloads: list[dict[str, object]] = []
    for line in output.splitlines():
        if line.startswith("data: "):
            payloads.append(json.loads(line.removeprefix("data: ")))
    return payloads


def test_runtime_live_console_once_emits_read_only_sse_events(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    called: dict[str, object] = {}

    class FakeRuntimeLiveConsole:
        @staticmethod
        def read_live_console_snapshot(**kwargs):
            called.update(kwargs)
            return {
                "surface": "runtime_live_console",
                "events": [
                    {
                        "sequence": 1,
                        "topic": "workspace.status",
                        "observed_at": "2026-05-08T01:02:03+00:00",
                        "source_ref": [],
                        "payload": {"status": "ready"},
                    },
                    {
                        "sequence": 2,
                        "topic": "runtime.health",
                        "observed_at": "2026-05-08T01:02:04+00:00",
                        "source_ref": [{"surface": "study_runtime_status"}],
                        "payload": {"state": "live"},
                    },
                    {
                        "sequence": 3,
                        "topic": "terminal.tail",
                        "observed_at": "2026-05-08T01:02:05+00:00",
                        "source_ref": [],
                        "payload": {"lines": []},
                    },
                ],
            }

    monkeypatch.setattr(cli, "runtime_live_console", FakeRuntimeLiveConsole)

    exit_code = cli.main(["runtime", "live-console", "--profile", str(profile_path), "--once"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "profile": called["profile"],
        "profile_ref": profile_path,
    }
    assert called["profile"].name == "nfpitnet"
    assert "event: workspace.status" in captured.out
    assert "event: runtime.health" in captured.out
    assert "event: terminal.tail" in captured.out
    events = _sse_data_lines(captured.out)
    assert [event["sequence"] for event in events] == [1, 2, 3]
    assert all("source_ref" in event for event in events)
    assert all("observed_at" in event for event in events)


def test_runtime_live_console_once_fails_closed_when_core_event_contract_is_incomplete(
    monkeypatch,
    tmp_path: Path,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")

    class FakeRuntimeLiveConsole:
        @staticmethod
        def read_live_console_snapshot(**kwargs):
            return {
                "events": [
                    {
                        "sequence": 1,
                        "topic": "workspace.status",
                        "observed_at": "2026-05-08T01:02:03+00:00",
                        "payload": {"status": "ready"},
                    },
                ],
            }

    monkeypatch.setattr(cli, "runtime_live_console", FakeRuntimeLiveConsole)

    with pytest.raises(SystemExit, match="source_ref"):
        cli.main(["runtime", "live-console", "--profile", str(profile_path), "--once"])


def test_runtime_live_console_serve_binds_loopback_only(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    module = importlib.import_module("med_autoscience.cli_parts.live_console_commands")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    served: dict[str, object] = {}

    class FakeServer:
        def __init__(self, address, handler):
            self.server_address = address
            served["address"] = address
            served["handler"] = handler

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            served["closed"] = True

        def serve_forever(self):
            served["served"] = True

    monkeypatch.setattr(module.http.server, "ThreadingHTTPServer", FakeServer)

    exit_code = cli.main(
        [
            "runtime",
            "live-console",
            "--profile",
            str(profile_path),
            "--serve",
            "--port",
            "4812",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert served["address"] == ("127.0.0.1", 4812)
    assert served["served"] is True
    assert served["closed"] is True
    assert "http://127.0.0.1:4812/events" in captured.out
