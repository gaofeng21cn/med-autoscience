from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


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


def _write_study_status(
    *,
    profile,
    study_id: str,
    quest_id: str,
    active_run_id: str | None,
    quest_status: str,
) -> None:
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "active_run_id": active_run_id,
            "quest_status": quest_status,
            "worker_running": active_run_id is not None,
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "health_status": quest_status,
            "active_run_id": active_run_id,
            "worker_running": active_run_id is not None,
            "artifact_delta": {"status": "fresh" if active_run_id else "missing"},
        },
    )


def test_live_console_profile_session_read_model_does_not_default_select_first_study(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    for study_id in (
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ):
        study_root = profile.studies_root / study_id
        _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")

    payload = module.build_live_console_session_read_model(profile, generated_at="2026-05-08T02:05:00+00:00")

    assert payload["surface_kind"] == "mas_live_console_session_read_model"
    assert payload["selected_study_id"] is None
    assert {study["study_id"] for study in payload["studies"]} == {
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    }
    assert all(study["selected"] is False for study in payload["studies"])


def test_live_console_session_read_model_distinguishes_dm002_and_dpcc003(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    _write_study_status(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_study_status(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id=None,
        quest_status="recovering",
    )

    payload = module.build_live_console_session_read_model(
        profile,
        study_id="002-dm-china-us-mortality-attribution",
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert [study["study_id"] for study in payload["studies"]] == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert payload["selected_study_id"] == "002-dm-china-us-mortality-attribution"
    assert payload["runs"] == [
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "quest-dm002",
            "active_run_id": "run-dm002-live",
            "status": "running",
            "worker_running": True,
        }
    ]


def test_live_console_session_read_model_ignores_file_runtime_artifact_ref_for_terminal_source(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    quest_root = profile.runtime_root / study_id
    study_root = profile.studies_root / study_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        {
            "study_id": study_id,
            "quest_id": study_id,
            "runtime_artifact_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
        },
    )
    _write_json(
        quest_root / ".ds" / "bash_exec" / "summary.json",
        {"status": "available", "tail": ["real quest terminal tail"]},
    )

    payload = module.build_live_console_session_read_model(profile, generated_at="2026-05-08T02:05:00+00:00")

    stream_by_topic = {(source["topic"], source["study_id"]): source for source in payload["stream_sources"]}
    terminal = stream_by_topic[("terminal.tail", study_id)]
    assert terminal["status"] == "available"
    assert terminal["source_ref"] == str(quest_root / ".ds" / "bash_exec" / "summary.json")
    assert "last_launch_report.json/.ds" not in json.dumps(payload, ensure_ascii=False)


def test_live_console_profile_snapshot_materializes_current_ui_payload_and_html(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_live_console")
    profile = make_profile(tmp_path)
    _write_study_status(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_study_status(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id=None,
        quest_status="recovering",
    )

    result = module.serve_live_console_stream(
        profile,
        profile_ref=tmp_path / "profile.toml",
        host="127.0.0.1",
        port=4812,
        interval_seconds=30,
    )

    html_path = profile.workspace_root / "ops" / "mas" / "live-console" / "index.html"
    ui_payload_path = profile.workspace_root / "artifacts" / "runtime" / "live_console" / "ui_payload" / "latest.json"
    assert result["html_path"] == str(html_path)
    assert result["ui_payload_path"] == str(ui_payload_path)
    assert json.loads(ui_payload_path.read_text(encoding="utf-8"))["surface_kind"] == "mas_live_console_ui"
    html = html_path.read_text(encoding="utf-8")
    assert "diabetes" in html
    assert "002-dm-china-us-mortality-attribution" in html
    assert "003-dpcc-primary-care-phenotype-treatment-gap" in html
    assert "run-dm002-live" in html
    assert "http://127.0.0.1:4812/events" in html
    assert "generated_at local" in html
    assert "med-deepscientist" not in html.lower()


def test_portal_console_soak_materializes_read_only_evidence_without_truth_writes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portal_console_soak")
    profile = make_profile(tmp_path)
    _write_soak_study(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="quest-dm002",
        active_run_id="run-dm002-live",
        quest_status="running",
    )
    _write_soak_study(
        profile=profile,
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        quest_id="quest-dpcc003",
        active_run_id="run-dpcc003-recovering",
        quest_status="recovering",
    )

    report = module.run_portal_console_soak(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert report["surface_kind"] == "mas_portal_console_soak"
    assert report["status"] == "passed"
    evidence = report["evidence"]
    assert evidence["portal_refresh"]["status"] == "passed"
    assert evidence["live_console_study_run_disambiguation"]["study_ids"] == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert evidence["live_console_study_run_disambiguation"]["run_ids"] == [
        "run-dm002-live",
        "run-dpcc003-recovering",
    ]
    assert evidence["terminal_log_refs"]["status"] == "passed"
    assert evidence["source_ref_cleanliness"]["forbidden_refs"] == []
    assert evidence["product_identity"]["forbidden_identity_tokens"] == []
    assert Path(report["report_path"]).is_file()
    assert (profile.workspace_root / "ops" / "mas" / "progress" / "index.html").is_file()
    assert (profile.workspace_root / "ops" / "mas" / "live-console" / "index.html").is_file()
    assert not (profile.workspace_root / "publication_eval" / "latest.json").exists()
    assert not (profile.workspace_root / "controller_decisions" / "latest.json").exists()
    assert not (profile.workspace_root / "runtime_lifecycle.sqlite").exists()


def test_portal_console_soak_blocks_legacy_identity_and_mds_truth_refs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portal_console_soak")
    profile = make_profile(tmp_path)
    portal_payload = {
        "source_refs": [
            str(profile.workspace_root / "ops" / "med-deepscientist" / "runtime" / "truth.json"),
        ],
    }
    console_payload = {"source_refs": []}
    console_ui_payload = {"source_refs": []}
    portal_payload_path = profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    console_payload_path = (
        profile.workspace_root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json"
    )
    console_ui_payload_path = (
        profile.workspace_root / "artifacts" / "runtime" / "live_console" / "ui_payload" / "latest.json"
    )
    portal_html_path = profile.workspace_root / "ops" / "mas" / "progress" / "index.html"
    console_html_path = profile.workspace_root / "ops" / "mas" / "live-console" / "index.html"
    _write_json(portal_payload_path, portal_payload)
    _write_json(console_payload_path, console_payload)
    _write_json(console_ui_payload_path, console_ui_payload)
    _write_text(portal_html_path, "Med Auto Science\n")
    _write_text(console_html_path, "MDS WebUI\n")

    report = module.build_portal_console_soak_report(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
        portal_result={
            "status": "materialized",
            "payload_path": str(portal_payload_path),
            "html_path": str(portal_html_path),
            "hosted_package_path": str(
                profile.workspace_root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"
            ),
        },
        console_result={
            "payload_path": str(console_payload_path),
            "ui_payload_path": str(console_ui_payload_path),
            "html_path": str(console_html_path),
            "session_read_model": {"studies": [], "stream_sources": []},
        },
        generated_at="2026-05-08T02:05:00+00:00",
    )

    assert report["status"] == "blocked"
    assert report["evidence"]["source_ref_cleanliness"]["forbidden_refs"] == portal_payload["source_refs"]
    assert report["evidence"]["product_identity"]["forbidden_identity_tokens"] == ["MDS WebUI"]


def _write_soak_study(
    *,
    profile,
    study_id: str,
    quest_id: str,
    active_run_id: str,
    quest_status: str,
) -> None:
    study_root = profile.studies_root / study_id
    quest_root = profile.runtime_root / quest_id
    _write_text(study_root / "study.yaml", f"study_id: {study_id}\n")
    _write_json(
        study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "active_run_id": active_run_id,
            "quest_status": quest_status,
            "worker_running": True,
            "last_seen_at": "2026-05-08T02:04:00+00:00",
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {
            "study_id": study_id,
            "health_status": quest_status,
            "active_run_id": active_run_id,
            "worker_running": True,
            "last_seen_at": "2026-05-08T02:04:00+00:00",
            "artifact_delta": {
                "status": "fresh",
                "latest_meaningful_delta_at": "2026-05-08T02:03:00+00:00",
                "artifact_kind": "read_model_fixture",
            },
        },
    )
    _write_json(
        quest_root / ".ds" / "bash_exec" / "summary.json",
        {"status": "available", "tail": [f"{study_id} terminal tail"]},
    )
    _write_text(quest_root / "logs" / "worker.log", f"{study_id} worker log\n")
