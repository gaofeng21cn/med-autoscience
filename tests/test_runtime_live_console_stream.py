from __future__ import annotations

import importlib
import io
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
                        "source_ref": [{"surface": "progress_projection"}],
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


def test_runtime_live_console_serve_terminal_attach_endpoint_uses_mas_runtime_core(monkeypatch, tmp_path: Path) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    module = importlib.import_module("med_autoscience.cli_parts.live_console_commands")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    runtime_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"
    quest_root = runtime_root / "quest-001"
    run_root = quest_root / ".ds" / "runs" / "run-001"
    run_root.mkdir(parents=True)
    (quest_root / "quest.yaml").write_text("quest_id: quest-001\n", encoding="utf-8")
    (quest_root / ".ds" / "runtime_state.json").write_text(
        json.dumps(
            {
                "quest_id": "quest-001",
                "study_id": "study-001",
                "status": "running",
                "active_run_id": "run-001",
                "worker_running": True,
                "runtime_backend_id": "mas_runtime_core",
            }
        ),
        encoding="utf-8",
    )
    (run_root / "worker_lease.json").write_text(
        json.dumps({"run_id": "run-001", "terminal_attach_capable": True}),
        encoding="utf-8",
    )
    served: dict[str, object] = {}

    class FakeServer:
        def __init__(self, address, handler):
            self.server_address = address
            served["handler"] = handler

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def serve_forever(self):
            return None

    monkeypatch.setattr(module.http.server, "ThreadingHTTPServer", FakeServer)
    cli.main(
        [
            "runtime",
            "live-console",
            "--profile",
            str(profile_path),
            "--study-id",
            "study-001",
            "--serve",
            "--enable-terminal-attach",
            "--port",
            "4812",
            "--format",
            "json",
        ]
    )

    handler = served["handler"]

    class FakeRequest(handler):
        def __init__(self, *, path: str, payload: dict[str, object]) -> None:
            self.path = path
            self.headers = {"Content-Length": str(len(json.dumps(payload).encode("utf-8")))}
            self.rfile = io.BytesIO(json.dumps(payload).encode("utf-8"))
            self.wfile = io.BytesIO()
            self.status_code = None
            self.headers_sent: dict[str, str] = {}

        def send_response(self, status_code: int) -> None:
            self.status_code = status_code

        def send_header(self, key: str, value: str) -> None:
            self.headers_sent[key] = value

        def end_headers(self) -> None:
            return None

        def send_error(self, status_code: int) -> None:
            self.status_code = status_code

        def log_message(self, format: str, *args: object) -> None:
            return None

    attach_request = FakeRequest(path="/terminal/attach", payload={"idempotency_key": "attach-1"})
    attach_request.do_POST()
    attach_payload = json.loads(attach_request.wfile.getvalue().decode("utf-8"))
    input_request = FakeRequest(
        path="/terminal/input",
        payload={
            "idempotency_key": "input-1",
            "token": attach_payload["attach_token"],
            "lease_id": attach_payload["lease"]["lease_id"],
            "text": "hello\n",
        },
    )
    input_request.do_POST()
    input_payload = json.loads(input_request.wfile.getvalue().decode("utf-8"))

    assert attach_request.status_code == 200
    assert attach_payload["status"] == "attached"
    assert input_request.status_code == 200
    assert input_payload["status"] == "accepted"
    assert (run_root / "terminal_commands.jsonl").is_file()


def test_runtime_live_console_snapshot_materializes_workspace_session_model(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "diabetes.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    for study_id, quest_id, active_run_id in (
        ("002-dm-china-us-mortality-attribution", "quest-dm002", "run-dm002-live"),
        ("003-dpcc-primary-care-phenotype-treatment-gap", "quest-dpcc003", None),
    ):
        study_root = workspace_root / "studies" / study_id
        study_root.mkdir(parents=True)
        (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
        status_path = study_root / "artifacts" / "runtime" / "progress_projection" / "latest.json"
        status_path.parent.mkdir(parents=True)
        status_path.write_text(
            json.dumps(
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "quest_root": str(workspace_root / "runtime" / "quests" / quest_id),
                    "active_run_id": active_run_id,
                    "quest_status": "running" if active_run_id else "recovering",
                    "worker_running": active_run_id is not None,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    exit_code = cli.main(
        [
            "runtime",
            "live-console",
            "--profile",
            str(profile_path),
            "--snapshot",
            "--format",
            "json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    model = payload["session_read_model"]
    assert payload["status"] == "snapshot"
    assert model["selected_study_id"] is None
    assert [study["study_id"] for study in model["studies"]] == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert model["runs"] == [
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-dm002",
            "active_run_id": "run-dm002-live",
            "status": "running",
            "worker_running": True,
        }
    ]
    assert Path(payload["payload_path"]).is_file()
    assert Path(payload["html_path"]).is_file()
    assert "002-dm-china-us-mortality-attribution" in Path(payload["html_path"]).read_text(encoding="utf-8")
