from __future__ import annotations

import importlib
import json
import sqlite3
from pathlib import Path


def _intent(*, unit_id: str = "analysis_claim_evidence_repair", target: str = "claim:C1") -> dict[str, object]:
    return {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "unit_id": unit_id,
        "action_type": "run_publication_work_unit",
        "lane": "analysis-campaign",
        "source_fingerprint": "publication-blockers::same-source",
        "targets": [target],
        "payload": {
            "reason": "repair claim evidence",
            "target": target,
        },
    }


def test_enqueue_replays_semantically_equivalent_receipt_for_same_idempotency_key_and_intent(
    tmp_path: Path,
) -> None:
    outbox = importlib.import_module("med_autoscience.controllers.paper_work_unit_outbox")
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    db_path = lifecycle_store.workspace_lifecycle_store_path(tmp_path / "workspace")

    first = outbox.enqueue_paper_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(),
        worker_start_ref="worker::run-001",
        recorded_at="2026-05-10T00:00:00+00:00",
        db_path=db_path,
    )
    replay = outbox.enqueue_paper_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(),
        worker_start_ref="worker::run-002",
        recorded_at="2026-05-10T00:01:00+00:00",
        db_path=db_path,
    )

    assert replay["receipt_status"] == "replayed"
    assert replay["receipt_id"] == first["receipt_id"]
    assert replay["worker_start_ref"] == "worker::run-001"
    assert replay["intent_fingerprint"] == first["intent_fingerprint"]
    assert replay["semantic_receipt"] == first["semantic_receipt"]
    assert len(outbox.read_receipts(study_root=study_root)) == 1
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT idempotency_key, intent_fingerprint, source_fingerprint, worker_start_ref, payload_json
            FROM paper_work_unit_receipts
            WHERE study_root = ?
            """,
            (str(study_root.resolve()),),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][:4] == (
        "paper-work-unit::001",
        first["intent_fingerprint"],
        "publication-blockers::same-source",
        "worker::run-001",
    )
    assert json.loads(rows[0][4])["receipt_id"] == first["receipt_id"]


def test_enqueue_fails_closed_for_same_idempotency_key_with_different_intent(tmp_path: Path) -> None:
    outbox = importlib.import_module("med_autoscience.controllers.paper_work_unit_outbox")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"

    outbox.enqueue_paper_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(target="claim:C1"),
        worker_start_ref="worker::run-001",
        recorded_at="2026-05-10T00:00:00+00:00",
    )

    conflict = outbox.enqueue_paper_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(target="claim:C2"),
        worker_start_ref="worker::run-002",
        recorded_at="2026-05-10T00:01:00+00:00",
    )

    assert conflict["receipt_status"] == "failed_closed"
    assert conflict["fail_closed_reason"] == "idempotency_key_intent_conflict"
    assert conflict["started_worker"] is False
    assert conflict["worker_start_ref"] is None
    assert conflict["conflicting_receipt_id"] is not None
    assert len(outbox.read_receipts(study_root=study_root)) == 2


def test_enqueue_suppresses_duplicate_worker_start_for_same_source_fingerprint(tmp_path: Path) -> None:
    outbox = importlib.import_module("med_autoscience.controllers.paper_work_unit_outbox")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"

    first = outbox.enqueue_paper_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(target="claim:C1"),
        worker_start_ref="worker::run-001",
        recorded_at="2026-05-10T00:00:00+00:00",
    )
    duplicate_source = outbox.enqueue_paper_work_unit(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::002",
        intent=_intent(target="claim:C2"),
        worker_start_ref="worker::run-002",
        recorded_at="2026-05-10T00:01:00+00:00",
    )

    assert first["started_worker"] is True
    assert duplicate_source["receipt_status"] == "duplicate_source_fingerprint"
    assert duplicate_source["started_worker"] is False
    assert duplicate_source["worker_start_ref"] == "worker::run-001"
    assert duplicate_source["duplicate_of_receipt_id"] == first["receipt_id"]
    assert [item["worker_start_ref"] for item in outbox.worker_starts(study_root=study_root)] == ["worker::run-001"]


def test_repeat_suppression_does_not_block_owner_handoff_dispatch_or_execution() -> None:
    repeat_suppression = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")
    route = {
        "owner_reason": repeat_suppression.OWNER_HANDOFF_REASON,
        "work_unit_fingerprint": "publication-blockers::same-source",
    }
    dispatch = {
        "dispatch_status": "ready",
        "owner_route": route,
        "prompt_contract": {
            "do_not_repeat": True,
            "repeat_suppression_key": "publication-blockers::same-source",
        },
    }

    dispatch_guard = repeat_suppression.dispatch_repeat_suppression(
        dispatch=dispatch,
        current_study={"study_id": "001-risk", "meaningful_artifact_delta": False},
        existing_dispatch=dispatch,
    )
    execution_guard = repeat_suppression.execution_repeat_suppression(
        dispatch=dispatch,
        current_study={"study_id": "001-risk", "meaningful_artifact_delta": False},
        previous_execution_latest={"executions": [dispatch]},
    )

    assert dispatch_guard["repeat_suppressed"] is False
    assert dispatch_guard["work_unit_fingerprint"] == "publication-blockers::same-source"
    assert execution_guard["repeat_suppressed"] is False
    assert execution_guard["work_unit_fingerprint"] == "publication-blockers::same-source"
