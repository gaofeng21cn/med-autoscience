from __future__ import annotations

import importlib
import json
from pathlib import Path
import sqlite3


def test_runtime_session_projection_prefers_study_runtime_status_and_enforces_strict_live_active_run(
    tmp_path: Path,
) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    _write_runtime_event(
        db_path=db_path,
        quest_root=tmp_path / "runtime" / "quests" / "quest-001",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-05-08T00:00:00+00:00",
        active_run_id="run-from-sqlite",
    )
    status_payload = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "active_run_id": "run-from-status",
        "last_known_run_id": "run-previous",
        "runtime_liveness_status": "unknown",
        "worker_running": True,
        "worker_state": "activity_timeout",
        "started_at": "2026-05-08T00:01:00+00:00",
        "last_seen_at": "2026-05-08T00:03:00+00:00",
        "last_event_cursor": "cursor-from-status",
        "last_stdout_ref": "stdout://run-from-status",
        "runtime_liveness_audit": {
            "status": "unknown",
            "active_run_id": "run-from-audit",
            "runtime_audit": {
                "worker_running": True,
                "worker_state": "activity_timeout",
            },
        },
    }

    projection = read_model.build_runtime_session_read_model(
        study_runtime_status=status_payload,
        quest_root=tmp_path / "runtime" / "quests" / "quest-001",
        db_path=db_path,
        generated_at="2026-05-08T00:05:00+00:00",
        freshness_ttl_seconds=300,
    )

    session = projection["runtime_session"]
    assert projection["surface_kind"] == "runtime_session_read_model"
    assert projection["read_only"] is True
    assert session["source_priority"] == "study_runtime_status"
    assert session["study_id"] == "001-risk"
    assert session["quest_id"] == "quest-001"
    assert session["active_run_id"] is None
    assert session["last_known_run_id"] == "run-from-status"
    assert session["worker_state"] == "activity_timeout"
    assert session["worker_running"] is True
    assert session["runtime_liveness_status"] == "unknown"
    assert session["last_event_cursor"] == "cursor-from-status"
    assert session["last_stdout_ref"] == "stdout://run-from-status"
    assert session["freshness_state"] == "fresh"
    assert session["freshness_age_seconds"] == 120
    assert session["evidence_refs"] == [{"source": "study_runtime_status"}]
    assert session["generated_at"] == "2026-05-08T00:05:00+00:00"


def test_runtime_session_projection_includes_watchdog_fields_without_relaxing_strict_live() -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    status_payload = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "active_run_id": "run-wrapper",
        "runtime_liveness_status": "unknown",
        "worker_running": True,
        "worker_state": "stale",
        "last_seen_at": "2026-05-08T00:03:00+00:00",
        "worker_watchdog": {
            "monitor_kind": "mas_per_run_worker_wrapper",
            "monitor_pid": 4242,
            "child_pid": 4343,
            "heartbeat_age_seconds": 360,
            "last_output_at": "2026-05-08T00:02:30+00:00",
            "stdout_cursor": 2048,
            "monitor_state": "stale",
            "stale_reason": "heartbeat_ttl_exceeded",
            "last_stdout_ref": "stdout://run-wrapper",
            "will_start_llm": False,
        },
    }

    projection = read_model.build_runtime_session_read_model(
        study_runtime_status=status_payload,
        generated_at="2026-05-08T00:10:00+00:00",
    )

    session = projection["runtime_session"]
    assert session["active_run_id"] is None
    assert session["last_known_run_id"] == "run-wrapper"
    assert session["monitor_kind"] == "mas_per_run_worker_wrapper"
    assert session["monitor_pid"] == 4242
    assert session["child_pid"] == 4343
    assert session["heartbeat_age_seconds"] == 360
    assert session["last_output_at"] == "2026-05-08T00:02:30+00:00"
    assert session["stdout_cursor"] == 2048
    assert session["monitor_state"] == "stale"
    assert session["stale_reason"] == "heartbeat_ttl_exceeded"
    assert session["last_stdout_ref"] == "stdout://run-wrapper"
    assert session["will_start_llm"] is False


def test_runtime_session_projection_reads_runtime_worker_activity() -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    status_payload = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "runtime_liveness_status": "live",
        "runtime_worker_activity": {
            "activity_state": "running",
            "heartbeat_state": "live",
            "active_run_id": "run-live",
            "worker_running": True,
        },
    }

    projection = read_model.build_runtime_session_read_model(
        study_runtime_status=status_payload,
        generated_at="2026-05-08T00:10:00+00:00",
    )

    session = projection["runtime_session"]
    assert session["active_run_id"] == "run-live"
    assert session["last_known_run_id"] is None
    assert session["worker_state"] == "running"
    assert session["worker_running"] is True


def test_runtime_session_projection_reads_latest_lifecycle_event_when_status_is_absent(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    _write_runtime_event(
        db_path=db_path,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-05-08T00:00:00+00:00",
        active_run_id="run-old",
    )
    _write_runtime_event(
        db_path=db_path,
        quest_root=quest_root,
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-05-08T00:10:00+00:00",
        active_run_id="run-live",
        event_id="event-live",
        artifact_name="event-live.json",
    )

    projection = read_model.build_runtime_session_read_model(
        quest_root=quest_root,
        db_path=db_path,
        generated_at="2026-05-08T00:12:00+00:00",
    )

    session = projection["runtime_session"]
    assert session["source_priority"] == "runtime_lifecycle_store"
    assert session["study_id"] == "001-risk"
    assert session["quest_id"] == "quest-001"
    assert session["active_run_id"] == "run-live"
    assert session["last_known_run_id"] is None
    assert session["worker_state"] == "running"
    assert session["worker_running"] is True
    assert session["runtime_liveness_status"] == "live"
    assert session["last_seen_at"] == "2026-05-08T00:10:00+00:00"
    assert session["last_event_cursor"] == "2026-05-08T00:10:00+00:00::event-live"
    assert session["freshness_state"] == "measured"
    assert session["freshness_age_seconds"] == 120
    assert {ref["source"] for ref in session["evidence_refs"]} == {
        "runtime_lifecycle_store",
        "runtime_event_artifact",
        "runtime_event_latest",
        "runtime_event_summary",
    }


def test_runtime_session_projection_falls_back_to_owner_route_receipts_without_claiming_live_worker(
    tmp_path: Path,
) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    study_root = tmp_path / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    _write_owner_and_dispatch_receipts(
        db_path=db_path,
        study_root=study_root,
        quest_root=quest_root,
        owner_source_path=study_root / "artifacts" / "runtime" / "owner_route" / "latest.json",
        dispatch_source_path=quest_root / "artifacts" / "runtime" / "dispatch" / "dispatch-001.json",
    )

    projection = read_model.build_runtime_session_read_model(
        study_root=study_root,
        quest_root=quest_root,
        db_path=db_path,
        generated_at="2026-05-08T00:15:00+00:00",
    )

    session = projection["runtime_session"]
    assert session["source_priority"] == "owner_route_receipts"
    assert session["study_id"] == "001-risk"
    assert session["quest_id"] == "quest-001"
    assert session["active_run_id"] is None
    assert session["last_known_run_id"] is None
    assert session["worker_state"] == "dispatched"
    assert session["worker_running"] is None
    assert session["runtime_liveness_status"] == "unknown"
    assert session["last_seen_at"] == "2026-05-08T00:11:00+00:00"
    assert session["evidence_refs"] == [
        {
            "source": "owner_route_receipts",
            "path": str((study_root / "artifacts" / "runtime" / "owner_route" / "latest.json").resolve()),
        },
        {
            "source": "dispatch_receipts",
            "path": str((quest_root / "artifacts" / "runtime" / "dispatch" / "dispatch-001.json").resolve()),
        },
        {"source": "runtime_lifecycle_store", "path": str(db_path.resolve())},
    ]


def test_runtime_session_projection_reads_explicit_historical_fixture_last(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    fixture_path = tmp_path / "fixtures" / "runtime_state.json"
    fixture_path.parent.mkdir(parents=True)
    fixture_path.write_text(
        json.dumps(
            {
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "status": "running",
                "active_run_id": "run-legacy",
                "last_seen_at": "2026-05-08T00:20:00+00:00",
                "stdout_path": "stdout.jsonl",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    projection = read_model.build_runtime_session_read_model(
        historical_fixture_path=fixture_path,
        generated_at="2026-05-08T00:25:00+00:00",
        freshness_ttl_seconds=60,
    )

    session = projection["runtime_session"]
    assert session["source_priority"] == "historical_fixture_ref"
    assert session["study_id"] == "001-risk"
    assert session["quest_id"] == "quest-001"
    assert session["active_run_id"] is None
    assert session["last_known_run_id"] == "run-legacy"
    assert session["worker_state"] == "running"
    assert session["worker_running"] is None
    assert session["runtime_liveness_status"] == "unknown"
    assert session["last_stdout_ref"] == "stdout.jsonl"
    assert session["freshness_state"] == "stale"
    assert session["freshness_age_seconds"] == 300
    assert session["evidence_refs"] == [
        {"source": "historical_fixture_ref", "path": str(fixture_path.resolve())}
    ]


def test_runtime_session_projection_is_read_only_for_authority_files(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_session_read_model")
    status_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    status_path.parent.mkdir(parents=True)
    status_path.write_text(
        json.dumps(
            {
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "active_run_id": "run-live",
                "runtime_liveness_status": "live",
                "worker_running": True,
                "recorded_at": "2026-05-08T00:00:00+00:00",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    before_mtime = status_path.stat().st_mtime_ns

    projection = read_model.build_runtime_session_read_model(
        study_runtime_status_path=status_path,
        generated_at="2026-05-08T00:01:00+00:00",
    )

    assert projection["runtime_session"]["active_run_id"] == "run-live"
    assert status_path.stat().st_mtime_ns == before_mtime


def _write_runtime_event(
    *,
    db_path: Path,
    quest_root: Path,
    study_id: str,
    quest_id: str,
    emitted_at: str,
    active_run_id: str,
    event_id: str = "event-001",
    artifact_name: str = "event-001.json",
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    event_payload = {
        "schema_version": 1,
        "event_id": event_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": emitted_at,
        "event_source": "study_runtime_status",
        "event_kind": "status_observed",
        "summary_ref": str((quest_root / "artifacts" / "runtime" / "last_launch_report.json").resolve()),
        "status_snapshot": {
            "quest_status": "running",
            "decision": "continue",
            "reason": "runtime_watch",
            "active_run_id": active_run_id,
            "runtime_liveness_status": "live",
            "worker_running": True,
            "worker_state": "running",
            "continuation_policy": "auto",
            "continuation_reason": "runtime_watch",
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": None,
            "last_stdout_ref": f"stdout://{active_run_id}",
        },
        "outer_loop_input": {
            "quest_status": "running",
            "decision": "continue",
            "reason": "runtime_watch",
            "active_run_id": active_run_id,
            "runtime_liveness_status": "live",
            "worker_running": True,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": None,
        },
    }
    artifact_path = quest_root / "artifacts" / "reports" / "runtime_events" / artifact_name
    latest_path = artifact_path.parent / "latest.json"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runtime_events(
                quest_root TEXT NOT NULL,
                event_id TEXT NOT NULL,
                quest_id TEXT NOT NULL,
                study_id TEXT NOT NULL,
                emitted_at TEXT NOT NULL,
                event_source TEXT NOT NULL,
                event_kind TEXT NOT NULL,
                status TEXT NOT NULL,
                active_run_id TEXT,
                summary_ref TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                latest_path TEXT NOT NULL,
                cursor TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (quest_root, event_id)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO runtime_events(
                quest_root, event_id, quest_id, study_id, emitted_at, event_source,
                event_kind, status, active_run_id, summary_ref, artifact_path,
                latest_path, cursor, payload_sha256, payload_json, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(quest_root.resolve()),
                event_id,
                quest_id,
                study_id,
                emitted_at,
                "study_runtime_status",
                "status_observed",
                "running",
                active_run_id,
                event_payload["summary_ref"],
                str(artifact_path.resolve()),
                str(latest_path.resolve()),
                f"{emitted_at}::{event_id}",
                "sha256",
                json.dumps(event_payload, ensure_ascii=False, sort_keys=True),
                emitted_at,
            ),
        )


def _write_owner_and_dispatch_receipts(
    *,
    db_path: Path,
    study_root: Path,
    quest_root: Path,
    owner_source_path: Path,
    dispatch_source_path: Path,
) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    owner_receipt = {
        "surface": "domain_route_owner_route",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "idempotency_key": "route-001",
        "route_epoch": "truth-epoch-001",
        "current_owner": "runtime",
        "next_owner": "mas_controller",
        "owner_reason": "runtime_controller_redrive_required",
    }
    dispatch_receipt = {
        "surface": "domain_owner_action_dispatch_receipt",
        "dispatch_id": "dispatch-001",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "created_at": "2026-05-08T00:11:00+00:00",
        "owner_route": owner_receipt,
        "status": "dispatched",
    }
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE owner_route_receipts(
                study_root TEXT NOT NULL,
                study_id TEXT NOT NULL,
                quest_id TEXT,
                idempotency_key TEXT NOT NULL,
                route_epoch TEXT,
                current_owner TEXT,
                next_owner TEXT,
                owner_reason TEXT,
                allowed_actions_json TEXT NOT NULL,
                source_refs_json TEXT NOT NULL,
                source_path TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (study_root, idempotency_key)
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
            INSERT INTO owner_route_receipts(
                study_root, study_id, quest_id, idempotency_key, route_epoch,
                current_owner, next_owner, owner_reason, allowed_actions_json,
                source_refs_json, source_path, payload_sha256, payload_json, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(study_root.resolve()),
                "001-risk",
                "quest-001",
                "route-001",
                "truth-epoch-001",
                "runtime",
                "mas_controller",
                "runtime_controller_redrive_required",
                "[]",
                "{}",
                str(owner_source_path.resolve()),
                "sha256",
                json.dumps(owner_receipt, ensure_ascii=False, sort_keys=True),
                "2026-05-08T00:10:00+00:00",
            ),
        )
        conn.execute(
            """
            INSERT INTO dispatch_receipts(
                quest_root, dispatch_id, study_id, quest_id, action_type,
                created_at, status, idempotency_key, owner_route_json,
                source_path, payload_sha256, payload_json, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(quest_root.resolve()),
                "dispatch-001",
                "001-risk",
                "quest-001",
                "resume",
                "2026-05-08T00:11:00+00:00",
                "dispatched",
                "route-001",
                json.dumps(owner_receipt, ensure_ascii=False, sort_keys=True),
                str(dispatch_source_path.resolve()),
                "sha256",
                json.dumps(dispatch_receipt, ensure_ascii=False, sort_keys=True),
                "2026-05-08T00:11:00+00:00",
            ),
        )
