from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.runtime_protocol.quest_state import (
    QuestRuntimeLivenessStatus,
    QuestRuntimeSnapshot,
    find_latest_main_result_path,
    inspect_quest_runtime,
    iter_active_quests,
    load_runtime_state,
    read_recent_stdout_lines,
    resolve_active_stdout_path,
)


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_load_runtime_state_reads_ds_runtime_json(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    dump_json(quest_root / ".ds" / "runtime_state.json", {"status": "running", "active_run_id": "run-1"})

    result = load_runtime_state(quest_root)

    assert result["status"] == "running"
    assert result["active_run_id"] == "run-1"


def test_find_latest_main_result_path_prefers_latest_candidate(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    first = quest_root / ".ds" / "worktrees" / "run-a" / "experiments" / "main" / "001" / "RESULT.json"
    second = quest_root / "experiments" / "main" / "002" / "RESULT.json"
    dump_json(first, {"run_id": "001"})
    dump_json(second, {"run_id": "002"})
    second.touch()

    latest = find_latest_main_result_path(quest_root)

    assert latest == second


def test_resolve_active_stdout_path_reads_active_run_id(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    stdout_path = quest_root / ".ds" / "runs" / "run-123" / "stdout.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text("", encoding="utf-8")

    resolved = resolve_active_stdout_path(quest_root=quest_root, runtime_state={"active_run_id": "run-123"})

    assert resolved == stdout_path


def test_read_recent_stdout_lines_filters_bad_json_and_limits_count(tmp_path: Path) -> None:
    stdout_path = tmp_path / "stdout.jsonl"
    stdout_path.write_text(
        "\n".join(
            [
                '{"line":"first"}',
                "not-json",
                '{"line":"second"}',
                '{"line":""}',
                '{"line":"third"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = read_recent_stdout_lines(stdout_path, limit=3)

    assert result == ["second", "third"]


def test_inspect_quest_runtime_reads_local_status_from_protocol_surface(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("quest_id: q001\n", encoding="utf-8")
    dump_json(quest_root / ".ds" / "runtime_state.json", {"status": "running"})

    result = inspect_quest_runtime(quest_root)

    assert result == QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit=None,
        runtime_liveness_audit=None,
    )


def test_inspect_quest_runtime_reports_missing_quest_when_quest_yaml_is_absent(tmp_path: Path) -> None:
    quest_root = tmp_path / "q001"
    dump_json(quest_root / ".ds" / "runtime_state.json", {"status": "running"})

    result = inspect_quest_runtime(quest_root)

    assert result == QuestRuntimeSnapshot(
        quest_exists=False,
        quest_status=None,
        bash_session_audit=None,
        runtime_liveness_audit=None,
    )


def test_quest_runtime_snapshot_tracks_runtime_and_bash_audits_independently() -> None:
    snapshot = QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit=None,
        runtime_liveness_audit=None,
    )

    updated = snapshot.with_runtime_liveness_audit(
        {
            "status": "live",
            "active_run_id": "run-1",
        }
    ).with_bash_session_audit(
        {
            "status": "live",
            "live_session_ids": ["sess-1"],
        }
    )

    assert updated == QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit={
            "status": "live",
            "live_session_ids": ["sess-1"],
        },
        runtime_liveness_audit={
            "status": "live",
            "active_run_id": "run-1",
        },
    )
    assert updated.runtime_liveness_status is QuestRuntimeLivenessStatus.LIVE


def test_quest_runtime_snapshot_normalizes_runtime_liveness_status_values() -> None:
    live_snapshot = QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit=None,
        runtime_liveness_audit={"status": "live"},
    )
    none_snapshot = QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit=None,
        runtime_liveness_audit={"status": "none"},
    )
    unknown_snapshot = QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit=None,
        runtime_liveness_audit={"status": "unknown"},
    )
    other_snapshot = QuestRuntimeSnapshot(
        quest_exists=True,
        quest_status="running",
        bash_session_audit=None,
        runtime_liveness_audit={"status": "paused"},
    )

    assert live_snapshot.runtime_liveness_status is QuestRuntimeLivenessStatus.LIVE
    assert none_snapshot.runtime_liveness_status is QuestRuntimeLivenessStatus.NONE
    assert unknown_snapshot.runtime_liveness_status is QuestRuntimeLivenessStatus.UNKNOWN
    assert other_snapshot.runtime_liveness_status is QuestRuntimeLivenessStatus.OTHER


def test_iter_active_quests_includes_waiting_for_user_for_outer_loop_arbitration(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime" / "quests"
    statuses = {
        "q-running": "running",
        "q-active": "active",
        "q-waiting": "waiting_for_user",
        "q-stopped": "stopped",
        "q-completed": "completed",
    }

    for quest_id, status in statuses.items():
        dump_json(
            runtime_root / quest_id / ".ds" / "runtime_state.json",
            {
                "quest_id": quest_id,
                "status": status,
            },
        )

    quests = iter_active_quests(runtime_root)

    assert [quest_root.name for quest_root in quests] == ["q-active", "q-running", "q-waiting"]
