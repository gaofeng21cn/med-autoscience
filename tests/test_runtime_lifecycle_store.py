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
    }


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
