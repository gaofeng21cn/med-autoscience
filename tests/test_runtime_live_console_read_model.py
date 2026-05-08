from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_live_console_read_model_projects_runtime_session_and_stream_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    stdout_path = tmp_path / "runtime" / "quests" / "quest-002" / ".ds" / "runs" / "run-002" / "stdout.jsonl"
    stderr_path = stdout_path.with_name("stderr.txt")
    _write_text(
        stdout_path,
        "\n".join(
            [
                '{"line":"first terminal line"}',
                '{"line":"second terminal line"}',
                '{"line":"third terminal line"}',
            ]
        )
        + "\n",
    )
    _write_text(stderr_path, "first log line\nsecond log line\n")

    read_model = module.build_live_console_read_model(
        profile_name="dm-cvd",
        workspace_root=tmp_path,
        study_id="002-dm-china-us-mortality-attribution",
        study_runtime_status={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-002",
            "active_run_id": "run-002",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "worker_state": "running",
            "last_seen_at": "2026-05-08T02:04:00+00:00",
            "last_event_cursor": "cursor-002",
            "last_stdout_ref": str(stdout_path),
        },
        runtime_health={"status": "recovering", "summary": "worker heartbeat is fresh"},
        runtime_supervision={"supervisor_tick_status": "fresh", "latest_event_at": "2026-05-08T02:04:30+00:00"},
        terminal_sources=[{"source": "codex_stdout", "path": stdout_path}],
        log_sources=[{"source": "codex_stderr", "path": stderr_path}],
        artifact_delta={"refs": ["studies/002/artifacts/runtime/runtime_supervision/latest.json"]},
        generated_at="2026-05-08T02:05:00+00:00",
        freshness_ttl_seconds=300,
    )

    assert read_model["surface_kind"] == "mas_live_console_read_model"
    assert read_model["read_only"] is True
    assert read_model["authority"] == {
        "kind": "read_only_runtime_projection",
        "writes_authority_surface": False,
        "controller_action_execution_allowed": False,
        "quality_authority_allowed": False,
        "publication_authority_allowed": False,
        "submission_authority_allowed": False,
    }
    assert read_model["workspace"]["profile_name"] == "dm-cvd"
    assert read_model["study"]["study_id"] == "002-dm-china-us-mortality-attribution"
    assert read_model["session"]["active_run_id"] == "run-002"
    assert read_model["session"]["worker_running"] is True
    assert read_model["runtime_health"]["status"] == "recovering"
    assert read_model["runtime_supervision"]["supervisor_tick_status"] == "fresh"
    assert read_model["terminal_sources"][0]["tail"] == ["first terminal line", "second terminal line", "third terminal line"]
    assert read_model["log_sources"][0]["tail"] == ["first log line", "second log line"]
    assert read_model["artifact_delta"]["refs"] == ["studies/002/artifacts/runtime/runtime_supervision/latest.json"]
    assert {topic["topic"] for topic in read_model["stream_topics"]} == {
        "workspace.status",
        "study.status",
        "runtime.health",
        "runtime.supervision",
        "terminal.tail",
        "log.tail",
        "artifact.delta",
    }
    assert all(topic["read_only"] is True for topic in read_model["stream_topics"])
    assert read_model["controller_action_links"][0]["direct_execution_allowed"] is False


def test_live_console_materialization_writes_only_live_console_read_model(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    status_path = tmp_path / "studies" / "002" / "artifacts" / "runtime" / "status.json"
    _write_json(
        status_path,
        {
            "study_id": "002",
            "quest_id": "quest-002",
            "runtime_liveness_status": "unknown",
            "worker_running": True,
            "active_run_id": "run-stale",
            "last_seen_at": "2026-05-08T02:00:00+00:00",
        },
    )
    before = status_path.stat().st_mtime_ns

    result = module.materialize_live_console_read_model(
        workspace_root=tmp_path,
        profile_name="dm-cvd",
        study_id="002",
        study_runtime_status_path=status_path,
        generated_at="2026-05-08T02:05:00+00:00",
    )

    latest_path = tmp_path / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json"
    assert result["read_model_ref"] == str(latest_path)
    assert json.loads(latest_path.read_text(encoding="utf-8"))["surface_kind"] == "mas_live_console_read_model"
    assert status_path.stat().st_mtime_ns == before
    assert not (tmp_path / "artifacts" / "controller_decisions").exists()
    assert not (tmp_path / "artifacts" / "publication_eval").exists()


def test_live_console_stream_events_are_read_only_and_ordered() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")

    events = module.build_live_console_stream_events(
        {
            "surface_kind": "mas_live_console_read_model",
            "generated_at": "2026-05-08T02:05:00+00:00",
            "workspace": {"workspace_root": "/workspace"},
            "study": {"study_id": "002"},
            "session": {"active_run_id": "run-002"},
            "runtime_health": {"status": "recovering"},
            "runtime_supervision": {"supervisor_tick_status": "fresh"},
            "terminal_sources": [{"source_ref": "/tmp/stdout.jsonl", "tail": ["terminal line"]}],
            "log_sources": [{"source_ref": "/tmp/stderr.txt", "tail": ["log line"]}],
            "artifact_delta": {"refs": ["artifact.json"]},
        }
    )

    assert [event["sequence"] for event in events] == list(range(1, len(events) + 1))
    assert {event["topic"] for event in events} == {
        "workspace.status",
        "study.status",
        "runtime.health",
        "runtime.supervision",
        "terminal.tail",
        "log.tail",
        "artifact.delta",
    }
    assert all(event["read_only"] is True for event in events)
    assert all(event["source_ref"] for event in events)


def test_runtime_live_console_controller_exposes_cli_snapshot_alias() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")

    snapshot = module.read_live_console_snapshot(
        profile_name="dm-cvd",
        workspace_root="/workspace",
        study_id="002",
        study_runtime_status={
            "study_id": "002",
            "quest_id": "quest-002",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-002",
        },
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert snapshot["surface_kind"] == "mas_live_console_read_model"
    assert snapshot["study"]["study_id"] == "002"
    assert snapshot["session"]["active_run_id"] == "run-002"
