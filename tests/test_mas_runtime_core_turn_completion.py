from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.runtime_transport.mas_runtime_core_turn_completion import (
    inspect_runner_completion,
    inspect_logical_turn_completion,
    stale_runner_completion_result,
)


def test_logical_turn_completion_requires_closeout(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "turn.completed"},
        ],
    )

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is None


def test_logical_turn_completion_requires_closed_stdout_items(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "turn.completed"},
        ],
    )

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is None


def test_runner_completion_rejects_success_without_turn_closeout(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "turn.started"},
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "incomplete"
    assert result["reason"] == "missing_turn_closeout"
    assert result["normalized_runner_status"] == "runner_incomplete"


def test_runner_completion_accepts_turn_closeout_without_turn_completed_event(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "completed"
    assert result["reason"] == "turn_closeout_present"
    assert result["normalized_runner_status"] == "succeeded"
    assert result["stdout_turn_completed"] is False


def test_runner_completion_rejects_closeout_that_marks_owner_request_as_meaningful_delta(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(
        quest_root=quest_root,
        run_id="run-001",
        payload={
            "quest_id": "quest-001",
            "run_id": "run-001",
            "status": "completed",
            "meaningful_artifact_delta": True,
            "artifact_refs": ["artifacts/runtime/owner_progress_requests/run-001.json"],
        },
    )
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "incomplete"
    assert result["reason"] == "invalid_meaningful_artifact_delta"
    assert result["normalized_runner_status"] == "runner_incomplete"
    assert result["invalid_artifact_refs"] == ["artifacts/runtime/owner_progress_requests/run-001.json"]


def test_runner_completion_rejects_closeout_that_only_marks_repair_packet_as_meaningful_delta(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(
        quest_root=quest_root,
        run_id="run-001",
        payload={
            "quest_id": "quest-001",
            "run_id": "run-001",
            "status": "completed",
            "meaningful_artifact_delta": True,
            "artifact_refs": [
                "artifacts/reports/analysis_claim_evidence_repair/latest.json",
                "artifacts/supervision/controller_consumption/latest.json",
                "artifacts/controller/gate_clearing_batch/latest.json",
            ],
        },
    )
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "incomplete"
    assert result["reason"] == "invalid_meaningful_artifact_delta"
    assert result["normalized_runner_status"] == "runner_incomplete"
    assert result["invalid_artifact_refs"] == [
        "artifacts/reports/analysis_claim_evidence_repair/latest.json",
        "artifacts/supervision/controller_consumption/latest.json",
        "artifacts/controller/gate_clearing_batch/latest.json",
    ]


def test_runner_completion_rejects_closeout_that_only_marks_delivery_surfaces_as_meaningful_delta(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "quest-001"
    refs = [
        "artifacts/reports/publishability_gate/2026-05-11T133207Z.json",
        "../../../studies/001-paper/artifacts/controller/quality_repair_batch/latest.json",
        "../../../studies/001-paper/artifacts/controller/current_package_freshness/latest.json",
        "../../../studies/001-paper/paper/submission_minimal/audit/submission_manifest.json",
        "../../../studies/001-paper/manuscript/delivery_manifest.json",
        "../../../studies/001-paper/manuscript/current_package.zip",
    ]
    _write_closeout(
        quest_root=quest_root,
        run_id="run-001",
        payload={
            "quest_id": "quest-001",
            "run_id": "run-001",
            "status": "completed",
            "meaningful_artifact_delta": True,
            "artifact_refs": refs,
        },
    )
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "incomplete"
    assert result["reason"] == "invalid_meaningful_artifact_delta"
    assert result["normalized_runner_status"] == "runner_incomplete"
    assert result["invalid_artifact_refs"] == refs


def test_runner_completion_treats_same_owner_manuscript_story_blocked_closeout_as_incomplete(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(
        quest_root=quest_root,
        run_id="run-001",
        payload={
            "quest_id": "quest-001",
            "run_id": "run-001",
            "status": "blocked",
            "meaningful_artifact_delta": False,
            "artifact_refs": [],
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "next_owner": "write",
        },
    )
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
        ],
    )

    result = inspect_runner_completion(quest_root=quest_root, run_id="run-001", runner_status="succeeded")

    assert result["state"] == "incomplete"
    assert result["reason"] == "same_owner_manuscript_story_followthrough_required"
    assert result["normalized_runner_status"] == "runner_incomplete"
    assert result["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert result["next_owner"] == "write"


def test_logical_turn_completion_keeps_same_owner_manuscript_story_closeout_active(
    tmp_path: Path,
) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(
        quest_root=quest_root,
        run_id="run-001",
        payload={
            "quest_id": "quest-001",
            "run_id": "run-001",
            "status": "blocked",
            "meaningful_artifact_delta": False,
            "artifact_refs": [],
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "next_owner": "write",
        },
    )
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
            {"type": "turn.completed"},
        ],
    )

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is not None
    assert result["state"] == "completed"
    assert result["reason"] == "same_owner_manuscript_story_followthrough_required"
    assert result["completion_runner_status"] == "runner_incomplete"
    assert result["target_status"] == "active"
    assert result["blocked_reason"] == "manuscript_story_surface_delta_missing"
    assert result["next_owner"] == "write"


def test_logical_turn_completion_reports_stale_nonterminal_receipt(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(
        quest_root=quest_root,
        run_id="run-001",
        events=[
            {"type": "item.started", "item": {"id": "item-1"}},
            {"type": "item.completed", "item": {"id": "item-1"}},
            {"type": "turn.completed"},
        ],
    )
    _write_latest_receipt(quest_root=quest_root, run_id="run-001", status="queued")

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is not None
    assert result["state"] == "completed"
    assert result["reason"] == "logical_turn_completed"
    assert result["latest_receipt_status"] == "queued"
    assert result["latest_receipt_terminal"] is False


def test_logical_turn_completion_keeps_terminal_receipt_flag(tmp_path: Path) -> None:
    quest_root = tmp_path / "quest-001"
    _write_closeout(quest_root=quest_root, run_id="run-001")
    _write_stdout(quest_root=quest_root, run_id="run-001", events=[])
    _write_latest_receipt(quest_root=quest_root, run_id="run-001", status="finished")

    result = inspect_logical_turn_completion(quest_root=quest_root, run_id="run-001")

    assert result is not None
    assert result["latest_receipt_terminal"] is True


def test_stale_runner_completion_result_ignores_old_run_while_active_worker_exists() -> None:
    result = stale_runner_completion_result(
        previous={
            "active_run_id": "run-new",
            "worker_running": True,
        },
        quest_id="quest-001",
        run_id="run-old",
        runner_status="succeeded",
        source="test-runner",
        recorded_at="2026-05-09T00:00:00+00:00",
        backend_id="mas_runtime_core",
        snapshot_payload={"status": "running", "active_run_id": "run-new"},
    )

    assert result is not None
    assert result["status"] == "stale_completion_ignored"
    assert result["next_turn"] is None
    assert result["active_run_id"] == "run-new"
    assert result["snapshot"] == {"status": "running", "active_run_id": "run-new"}
    assert result["ignored_completion"] == {
        "event": "stale_runner_completion_ignored",
        "source": "test-runner",
        "recorded_at": "2026-05-09T00:00:00+00:00",
        "quest_id": "quest-001",
        "run_id": "run-old",
        "active_run_id": "run-new",
        "runner_status": "succeeded",
        "runtime_status": None,
        "worker_running": True,
    }


def test_stale_runner_completion_result_accepts_matching_active_run() -> None:
    result = stale_runner_completion_result(
        previous={
            "active_run_id": "run-current",
            "worker_running": True,
        },
        quest_id="quest-001",
        run_id="run-current",
        runner_status="succeeded",
        source="test-runner",
        recorded_at="2026-05-09T00:00:00+00:00",
        backend_id="mas_runtime_core",
        snapshot_payload={},
    )

    assert result is None


def test_stale_runner_completion_result_accepts_idle_state_without_active_run() -> None:
    result = stale_runner_completion_result(
        previous={
            "active_run_id": None,
            "worker_running": False,
        },
        quest_id="quest-001",
        run_id="run-old",
        runner_status="succeeded",
        source="test-runner",
        recorded_at="2026-05-09T00:00:00+00:00",
        backend_id="mas_runtime_core",
        snapshot_payload={},
    )

    assert result is None


def _write_closeout(*, quest_root: Path, run_id: str, payload: dict | None = None) -> None:
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(payload or {"quest_id": quest_root.name, "run_id": run_id}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_stdout(*, quest_root: Path, run_id: str, events: list[dict]) -> None:
    stdout_path = quest_root / ".ds" / "runs" / run_id / "stdout.jsonl"
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(
        "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
        encoding="utf-8",
    )


def _write_latest_receipt(*, quest_root: Path, run_id: str, status: str) -> None:
    receipt_path = quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps({"quest_id": quest_root.name, "run_id": run_id, "status": status}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
