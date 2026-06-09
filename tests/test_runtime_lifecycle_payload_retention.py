from __future__ import annotations

import hashlib
import importlib
import json
import sqlite3
from pathlib import Path


def test_runtime_lifecycle_payload_retention_externalizes_large_payload_columns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_lifecycle_payload_retention")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    payload = {"categories": {"runtime": [{"path": f"file-{index}", "payload": "x" * 1024} for index in range(128)]}}
    payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    _create_runtime_lifecycle_fixture(db_path=db_path, payload_json=payload_json, payload_sha=payload_sha)

    planned = module.run_runtime_lifecycle_payload_retention(
        db_path=db_path,
        apply=False,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
        compact=False,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_count"] == 4
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("SELECT payload_json FROM report_index").fetchone()[0] == payload_json

    applied = module.run_runtime_lifecycle_payload_retention(
        db_path=db_path,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
        compact=True,
    )

    assert applied["status"] == "applied"
    assert applied["moved_count"] + applied["deduped_count"] == 4
    assert applied["compact"]["status"] == "compacted"
    with sqlite3.connect(db_path) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        report_payload = conn.execute("SELECT payload_json FROM report_index").fetchone()[0]
        categories_payload = conn.execute("SELECT categories_json FROM workspace_storage_audits").fetchone()[0]
    assert integrity == "ok"
    report_ref = json.loads(report_payload)
    categories_ref = json.loads(categories_payload)
    assert report_ref["surface_kind"] == "runtime_lifecycle_payload_retention_ref"
    assert report_ref["original_sha256"] == payload_sha
    assert Path(report_ref["cold_ref_path"]).is_file()
    assert Path(report_ref["cold_object_path"]).is_file()
    assert categories_ref["column"] == "categories_json"


def test_runtime_lifecycle_payload_retention_compact_removes_stale_sqlite_sidecars(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_lifecycle_payload_retention")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    payload_json = json.dumps({"payload": "x" * 4096}, sort_keys=True)
    payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    _create_runtime_lifecycle_fixture(db_path=db_path, payload_json=payload_json, payload_sha=payload_sha)
    _write_sqlite_sidecars(db_path)

    applied = module.run_runtime_lifecycle_payload_retention(
        db_path=db_path,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
        compact=True,
        max_rows=1,
    )

    assert applied["status"] == "applied"
    assert applied["compact"]["status"] == "compacted"
    assert {Path(item["path"]).name for item in applied["compact"]["sidecar_cleanup"]} == {
        "runtime_lifecycle.sqlite-shm",
        "runtime_lifecycle.sqlite-wal",
    }
    assert not Path(f"{db_path}-wal").exists()
    assert not Path(f"{db_path}-shm").exists()
    with sqlite3.connect(db_path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_runtime_lifecycle_sqlite_sidecar_repair_blocks_live_readable_sidecars(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_lifecycle_payload_retention")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    payload_json = json.dumps({"payload": "x" * 4096}, sort_keys=True)
    payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    _create_runtime_lifecycle_fixture(db_path=db_path, payload_json=payload_json, payload_sha=payload_sha)
    _write_sqlite_sidecars(db_path)

    applied = module.repair_runtime_lifecycle_sqlite_sidecars(db_path=db_path, apply=True)

    assert applied["status"] == "blocked"
    assert applied["blockers"][0]["status"] == "blocked_live_sqlite_sidecars_may_hold_checkpoint_data"
    assert Path(f"{db_path}-wal").exists()
    assert Path(f"{db_path}-shm").exists()


def test_runtime_lifecycle_sqlite_sidecar_repair_removes_stale_sidecars_after_immutable_integrity_ok(
    monkeypatch, tmp_path: Path
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_lifecycle_payload_retention")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    payload_json = json.dumps({"payload": "x" * 4096}, sort_keys=True)
    payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    _create_runtime_lifecycle_fixture(db_path=db_path, payload_json=payload_json, payload_sha=payload_sha)
    Path(f"{db_path}-wal").write_bytes(b"stale wal")
    Path(f"{db_path}-shm").write_bytes(b"stale shm")

    def fake_integrity_check(db_path: Path, *, immutable: bool) -> dict[str, str]:
        if immutable or not Path(f"{db_path}-wal").exists():
            return {"status": "ok", "mode": "immutable", "result": "ok"}
        return {"status": "error", "mode": "normal_readonly", "error": "database disk image is malformed"}

    monkeypatch.setattr(module, "_sqlite_integrity_check", fake_integrity_check)

    planned = module.repair_runtime_lifecycle_sqlite_sidecars(db_path=db_path, apply=False)

    assert planned["status"] == "planned"
    assert planned["sidecar_count"] == 2
    assert Path(f"{db_path}-wal").exists()
    assert planned["immutable_integrity_check"]["status"] == "ok"

    applied = module.repair_runtime_lifecycle_sqlite_sidecars(db_path=db_path, apply=True)

    assert applied["status"] == "applied"
    assert {item["status"] for item in applied["sidecars"]} == {"removed_stale_sqlite_sidecar"}
    assert not Path(f"{db_path}-wal").exists()
    assert not Path(f"{db_path}-shm").exists()
    assert applied["normal_integrity_check_after"]["status"] == "ok"


def test_runtime_lifecycle_payload_retention_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_runtime_lifecycle_payload_retention(
        *,
        db_path: Path,
        apply: bool,
        cold_store_root: Path,
        min_mb: int,
        max_rows: int | None,
        compact: bool,
    ) -> dict[str, object]:
        called["db_path"] = db_path
        called["apply"] = apply
        called["cold_store_root"] = cold_store_root
        called["min_mb"] = min_mb
        called["max_rows"] = max_rows
        called["compact"] = compact
        return {"surface_kind": "runtime_lifecycle_payload_retention", "status": "applied"}

    monkeypatch.setattr(
        cli.runtime_lifecycle_payload_retention,
        "run_runtime_lifecycle_payload_retention",
        fake_run_runtime_lifecycle_payload_retention,
    )

    exit_code = cli.main(
        [
            "runtime-lifecycle-payload-retention",
            "--db",
            str(tmp_path / "runtime_lifecycle.sqlite"),
            "--apply",
            "--cold-store-root",
            str(tmp_path / "cold-store"),
            "--min-mb",
            "2",
            "--max-rows",
            "5",
            "--compact",
        ]
    )

    assert exit_code == 0
    assert called == {
        "db_path": tmp_path / "runtime_lifecycle.sqlite",
        "apply": True,
        "cold_store_root": tmp_path / "cold-store",
        "min_mb": 2,
        "max_rows": 5,
        "compact": True,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"


def test_runtime_lifecycle_payload_retention_cli_repairs_stale_sidecars(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_repair_runtime_lifecycle_sqlite_sidecars(
        *,
        db_path: Path,
        apply: bool,
    ) -> dict[str, object]:
        called["db_path"] = db_path
        called["apply"] = apply
        return {"surface_kind": "runtime_lifecycle_sqlite_sidecar_repair", "status": "applied"}

    monkeypatch.setattr(
        cli.runtime_lifecycle_payload_retention,
        "repair_runtime_lifecycle_sqlite_sidecars",
        fake_repair_runtime_lifecycle_sqlite_sidecars,
    )

    exit_code = cli.main(
        [
            "runtime-lifecycle-payload-retention",
            "--db",
            str(tmp_path / "runtime_lifecycle.sqlite"),
            "--repair-stale-sidecars",
            "--apply",
        ]
    )

    assert exit_code == 0
    assert called == {
        "db_path": tmp_path / "runtime_lifecycle.sqlite",
        "apply": True,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"


def test_runtime_lifecycle_payload_retention_namespaces_cold_store_by_workspace_or_quest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_lifecycle_payload_retention")
    root_db = tmp_path / "DM-CVD" / "runtime" / "artifacts" / "runtime_lifecycle.sqlite"
    quest_db = tmp_path / "DM-CVD" / "runtime" / "quests" / "002-study" / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    payload_json = json.dumps({"payload": "x" * 4096}, sort_keys=True)
    payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
    _create_runtime_lifecycle_fixture(db_path=root_db, payload_json=payload_json, payload_sha=payload_sha)
    _create_runtime_lifecycle_fixture(db_path=quest_db, payload_json=payload_json, payload_sha=payload_sha)

    root_result = module.run_runtime_lifecycle_payload_retention(
        db_path=root_db,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
        compact=False,
        max_rows=1,
    )
    quest_result = module.run_runtime_lifecycle_payload_retention(
        db_path=quest_db,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
        compact=False,
        max_rows=1,
    )

    assert "/cold-store/DM-CVD/" in root_result["candidate_samples"][0]["cold_object_path"]
    assert "/cold-store/002-study/" in quest_result["candidate_samples"][0]["cold_object_path"]


def _create_runtime_lifecycle_fixture(*, db_path: Path, payload_json: str, payload_sha: str) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE workspace_storage_audits(
                workspace_root TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                mode TEXT NOT NULL,
                report_path TEXT NOT NULL,
                latest_report_path TEXT NOT NULL,
                study_count INTEGER NOT NULL,
                estimated_release_bytes INTEGER NOT NULL,
                actual_release_bytes INTEGER NOT NULL,
                runtime_total_bytes INTEGER NOT NULL,
                study_artifact_total_bytes INTEGER NOT NULL,
                summary_json TEXT NOT NULL,
                categories_json TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (workspace_root, recorded_at)
            );
            CREATE TABLE report_index(
                object_root TEXT NOT NULL,
                object_scope TEXT NOT NULL,
                report_group TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                json_path TEXT NOT NULL,
                md_path TEXT,
                latest_json_path TEXT NOT NULL,
                latest_md_path TEXT,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (object_root, object_scope, report_group, timestamp)
            );
            CREATE TABLE dispatch_receipts(
                quest_root TEXT NOT NULL,
                dispatch_id TEXT NOT NULL,
                study_id TEXT NOT NULL,
                quest_id TEXT,
                action_type TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                idempotency_key TEXT,
                owner_route_json TEXT NOT NULL,
                source_path TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (quest_root, dispatch_id)
            );
            """
        )
        conn.execute(
            """
            INSERT INTO workspace_storage_audits VALUES (
                '/workspace', '2026-05-05T09:00:00+00:00', 'dry-run',
                '/workspace/audit.json', '/workspace/latest.json',
                3, 0, 0, 1, 1, '{"summary": true}', ?, ?, ?
            )
            """,
            (payload_json, payload_sha, payload_json),
        )
        conn.execute(
            """
            INSERT INTO report_index VALUES (
                '/workspace', 'workspace', 'storage_audit', '20260505T090000Z',
                'planned', '/workspace/audit.json', NULL, '/workspace/latest.json', NULL,
                ?, ?, '2026-05-05T09:00:00+00:00'
            )
            """,
            (payload_sha, payload_json),
        )
        conn.execute(
            """
            INSERT INTO dispatch_receipts VALUES (
                '/quest', 'dispatch-1', 'study-1', 'quest-1', 'return_to_ai_reviewer_workflow',
                '2026-05-05T09:00:00+00:00', 'ready', 'idem-1', '{}',
                '/workspace/dispatch.json', ?, ?, '2026-05-05T09:00:00+00:00'
            )
            """,
            (payload_sha, payload_json),
        )


def _write_sqlite_sidecars(db_path: Path) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("INSERT INTO report_index VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            "/workspace",
            "workspace",
            "storage_audit",
            "20260505T090001Z",
            "planned",
            "/workspace/audit-2.json",
            None,
            "/workspace/latest.json",
            None,
            "sidecar-sha",
            '{"sidecar": true}',
            "2026-05-05T09:00:01+00:00",
        ))
        conn.commit()
        assert Path(f"{db_path}-wal").exists()
        assert Path(f"{db_path}-shm").exists()
