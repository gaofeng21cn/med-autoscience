from __future__ import annotations

import importlib
import json
from pathlib import Path
import sqlite3
import subprocess


def test_report_store_indexes_watch_state_and_reports_without_changing_file_surfaces(tmp_path: Path) -> None:
    report_store = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    state = {"schema_version": 1, "updated_at": "2026-05-05T00:00:00+00:00", "controllers": {"gate": {}}}
    report = {
        "schema_version": 1,
        "scanned_at": "2026-05-05T00:00:00+00:00",
        "quest_status": "running",
    }

    report_store.save_watch_state(quest_root, state)
    json_path, md_path = report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp="2026-05-05T00:00:00+00:00",
        report=report,
        markdown="# Runtime Watch\n",
    )

    assert json.loads((quest_root / "artifacts" / "reports" / "runtime_watch" / "state.json").read_text()) == state
    assert json.loads((quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").read_text()) == report
    assert md_path.read_text(encoding="utf-8") == "# Runtime Watch\n"
    db_path = lifecycle_store.quest_lifecycle_store_path(quest_root)
    assert db_path.is_file()
    with sqlite3.connect(db_path) as conn:
        watch_row = conn.execute(
            "SELECT updated_at, payload_json FROM watch_states WHERE quest_root = ?",
            (str(quest_root.resolve()),),
        ).fetchone()
        report_row = conn.execute(
            """
            SELECT report_group, timestamp, status, json_path, md_path
            FROM runtime_reports
            WHERE quest_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert watch_row[0] == "2026-05-05T00:00:00+00:00"
    assert json.loads(watch_row[1]) == state
    assert report_row == (
        "runtime_watch",
        "2026-05-05T00:00:00+00:00",
        "running",
        str(json_path.resolve()),
        str(md_path.resolve()),
    )
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"] == {
        "watch_states": 1,
        "runtime_reports": 1,
        "workspace_storage_audits": 0,
        "runtime_events": 0,
        "report_index": 1,
    }
    with sqlite3.connect(db_path) as conn:
        report_index_row = conn.execute(
            """
            SELECT object_scope, report_group, timestamp, status, json_path, latest_json_path, latest_md_path
            FROM report_index
            WHERE object_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert report_index_row == (
        "quest",
        "runtime_watch",
        "2026-05-05T00:00:00+00:00",
        "running",
        str(json_path.resolve()),
        str((quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").resolve()),
        str((quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md").resolve()),
    )


def test_workspace_storage_audit_indexes_summary_in_workspace_lifecycle_store(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    runtime_storage = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = importlib.import_module("tests.study_runtime_test_helpers").make_profile(tmp_path)

    result = runtime_storage.audit_workspace_storage(profile=profile, all_studies=True, apply=False)

    db_path = lifecycle_store.workspace_lifecycle_store_path(profile.workspace_root)
    assert result["runtime_lifecycle_index"] == {
        "surface_kind": "runtime_lifecycle_sqlite_index",
        "schema_version": 1,
        "status": "indexed",
        "scope": "workspace",
        "db_path": str(db_path),
        "indexed_table": "workspace_storage_audits",
        "indexed_count": 1,
    }
    assert json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))["runtime_lifecycle_index"] == result[
        "runtime_lifecycle_index"
    ]
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT mode, study_count, estimated_release_bytes, actual_release_bytes,
                   runtime_total_bytes, study_artifact_total_bytes, summary_json
            FROM workspace_storage_audits
            WHERE workspace_root = ?
            """,
            (str(profile.workspace_root.resolve()),),
        ).fetchone()

    assert row[0] == "dry-run"
    assert row[1] == result["summary"]["study_count"]
    assert row[2] == result["summary"]["estimated_release_bytes"]
    assert row[3] == 0
    assert row[4] == result["summary"]["runtime_total_bytes"]
    assert row[5] == result["summary"]["study_artifact_total_bytes"]
    assert json.loads(row[6]) == result["summary"]
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"] == {
        "watch_states": 0,
        "runtime_reports": 0,
        "workspace_storage_audits": 1,
        "runtime_events": 0,
        "report_index": 1,
    }


def test_lifecycle_store_fails_closed_when_sqlite_sidecar_is_git_tracked(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, text=True, capture_output=True)
    db_path = repo_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("tracked placeholder\n", encoding="utf-8")
    subprocess.run(["git", "add", str(db_path.relative_to(repo_root))], cwd=repo_root, check=True, text=True)

    try:
        lifecycle_store.record_watch_state(
            quest_root=repo_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "q001",
            payload={"updated_at": "2026-05-05T00:00:00+00:00"},
            db_path=db_path,
        )
    except RuntimeError as exc:
        assert "runtime lifecycle SQLite sidecar must not be tracked by Git" in str(exc)
        assert "artifacts/runtime/runtime_lifecycle.sqlite" in str(exc)
    else:
        raise AssertionError("tracked lifecycle DB sidecar must fail closed")


def test_runtime_event_record_indexes_event_without_replacing_latest_authority(tmp_path: Path) -> None:
    record_module = importlib.import_module("med_autoscience.runtime_event_record")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    record = record_module.RuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::001-risk::quest-001::status_observed::2026-05-05T00:00:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-05-05T00:00:00+00:00",
        event_source="study_runtime_status",
        event_kind="status_observed",
        summary_ref=str(launch_report_path),
        status_snapshot={
            "quest_status": "running",
            "decision": "continue",
            "reason": "runtime_watch",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "continuation_policy": "auto",
            "continuation_reason": "runtime_watch",
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": None,
        },
        outer_loop_input={
            "quest_status": "running",
            "decision": "continue",
            "reason": "runtime_watch",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": None,
        },
    )

    written = protocol.write_runtime_event_record(quest_root=quest_root, record=record)

    event_path = Path(written.artifact_path)
    latest_path = event_path.parent / "latest.json"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_payload == written.to_dict()
    db_path = lifecycle_store.quest_lifecycle_store_path(quest_root)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT event_id, quest_id, study_id, emitted_at, event_source, event_kind,
                   status, active_run_id, summary_ref, artifact_path, latest_path, cursor, payload_json
            FROM runtime_events
            WHERE quest_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert row[:-1] == (
        record.event_id,
        "quest-001",
        "001-risk",
        "2026-05-05T00:00:00+00:00",
        "study_runtime_status",
        "status_observed",
        "running",
        "run-001",
        str(launch_report_path),
        str(event_path.resolve()),
        str(latest_path.resolve()),
        f"2026-05-05T00:00:00+00:00::{record.event_id}",
    )
    assert json.loads(row[-1]) == latest_payload
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"]["runtime_events"] == 1


def test_lifecycle_read_model_exports_sqlite_runtime_report_without_touching_latest_files(tmp_path: Path) -> None:
    report_store = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    report = {
        "schema_version": 1,
        "scanned_at": "2026-05-05T00:00:00+00:00",
        "quest_status": "running",
    }
    report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp="2026-05-05T00:00:00+00:00",
        report=report,
        markdown="# Runtime Watch\n",
    )
    latest_json = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    latest_mtime = latest_json.stat().st_mtime_ns

    projection = read_model.read_compatibility_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
    )
    export_path = tmp_path / "exports" / "runtime_watch_latest.json"
    export = read_model.export_compatibility_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
        export_format="json",
        output_path=export_path,
    )

    assert projection["surface_kind"] == "runtime_lifecycle_compatibility_read_model"
    assert projection["payload"] == report
    assert projection["compatibility_fallback_used"] is False
    assert projection["read_only"] is True
    assert "ORDER BY timestamp DESC LIMIT 1" in projection["source_query"]
    assert export["surface_kind"] == "runtime_lifecycle_compatibility_export"
    assert export["compatibility_fallback_used"] is False
    assert export["output_path"] == str(export_path.resolve())
    assert json.loads(export_path.read_text(encoding="utf-8")) == report
    assert latest_json.stat().st_mtime_ns == latest_mtime


def test_lifecycle_read_model_marks_legacy_fallback_and_read_does_not_create_files(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    legacy_latest = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    legacy_latest.parent.mkdir(parents=True, exist_ok=True)
    legacy_payload = {"schema_version": 1, "quest_status": "stopped"}
    legacy_latest.write_text(json.dumps(legacy_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    db_path = quest_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"

    projection = read_model.read_compatibility_projection(
        surface="runtime_report",
        quest_root=quest_root,
    )
    inventory = read_model.build_lifecycle_inventory(quest_root=quest_root)

    assert projection["status"] == "fallback"
    assert projection["payload"] == legacy_payload
    assert projection["compatibility_fallback_used"] is True
    assert projection["source_paths"] == [str(legacy_latest)]
    assert inventory["status"] == "missing"
    assert inventory["compatibility_fallback_used"] is True
    assert not db_path.exists()


def test_lifecycle_inventory_lists_workspace_storage_audit_from_sqlite(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    runtime_storage = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = importlib.import_module("tests.study_runtime_test_helpers").make_profile(tmp_path)

    runtime_storage.audit_workspace_storage(profile=profile, all_studies=True, apply=False)

    db_path = lifecycle_store.workspace_lifecycle_store_path(profile.workspace_root)
    inventory = read_model.build_lifecycle_inventory(workspace_root=profile.workspace_root)
    projection = read_model.read_compatibility_projection(
        surface="workspace_storage_audit",
        workspace_root=profile.workspace_root,
    )

    assert inventory["status"] == "ready"
    assert inventory["db_path"] == str(db_path)
    assert inventory["available_surfaces"] == ["workspace_storage_audit"]
    assert inventory["tables"]["workspace_storage_audits"] == 1
    assert inventory["tables"]["report_index"] == 1
    assert projection["compatibility_fallback_used"] is False
    assert projection["payload"]["workspace_root"] == str(profile.workspace_root.resolve())
