from __future__ import annotations

import importlib
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


def test_transition_ref_replays_semantically_equivalent_receipt_for_same_idempotency_key_and_intent(
    tmp_path: Path,
) -> None:
    refs = importlib.import_module("med_autoscience.controllers.paper_progress_transition_refs")
    refs_index = importlib.import_module("med_autoscience.runtime_protocol.domain_authority_refs_index")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"
    db_path = refs_index.workspace_authority_refs_index_path(tmp_path / "workspace")

    first = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(),
        recorded_at="2026-05-10T00:00:00+00:00",
        db_path=db_path,
    )
    replay = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(),
        recorded_at="2026-05-10T00:01:00+00:00",
        db_path=db_path,
    )

    assert first["receipt_status"] == "transition_request_pending_opl_runtime_required"
    assert first["refs_only"] is True
    assert first["started_worker"] is False
    assert first["worker_start_ref"] is None
    assert first["mas_can_create_opl_outbox_record"] is False
    assert replay["receipt_status"] == "replayed_transition_request_ref"
    assert replay["receipt_id"] == first["receipt_id"]
    assert replay["worker_start_ref"] is None
    assert replay["intent_fingerprint"] == first["intent_fingerprint"]
    assert replay["semantic_receipt"] == first["semantic_receipt"]
    assert len(refs.read_transition_refs(study_root=study_root)) == 1
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT idempotency_key, intent_fingerprint, source_fingerprint, started_worker, worker_start_ref, payload_json
            FROM paper_work_unit_receipts
            WHERE study_root = ?
            """,
            (str(study_root.resolve()),),
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][:5] == (
        "paper-work-unit::001",
        first["intent_fingerprint"],
        "publication-blockers::same-source",
        0,
        "",
    )


def test_transition_ref_fails_closed_for_same_idempotency_key_with_different_intent(tmp_path: Path) -> None:
    refs = importlib.import_module("med_autoscience.controllers.paper_progress_transition_refs")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"

    refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(target="claim:C1"),
        recorded_at="2026-05-10T00:00:00+00:00",
    )

    conflict = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(target="claim:C2"),
        recorded_at="2026-05-10T00:01:00+00:00",
    )

    assert conflict["receipt_status"] == "failed_closed"
    assert conflict["fail_closed_reason"] == "idempotency_key_intent_conflict"
    assert conflict["started_worker"] is False
    assert conflict["worker_start_ref"] is None
    assert conflict["conflicting_receipt_id"] is not None
    assert len(refs.read_transition_refs(study_root=study_root)) == 2


def test_transition_ref_dedupes_same_source_without_worker_start_or_queue_claim(tmp_path: Path) -> None:
    refs = importlib.import_module("med_autoscience.controllers.paper_progress_transition_refs")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "workspace" / "runtime" / "quests" / "quest-001"

    first = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::001",
        intent=_intent(target="claim:C1"),
        recorded_at="2026-05-10T00:00:00+00:00",
    )
    duplicate_source = refs.record_paper_progress_transition_ref(
        study_root=study_root,
        quest_root=quest_root,
        idempotency_key="paper-work-unit::002",
        intent=_intent(target="claim:C2"),
        recorded_at="2026-05-10T00:01:00+00:00",
    )

    assert first["started_worker"] is False
    assert first["worker_start_ref"] is None
    assert duplicate_source["receipt_status"] == "duplicate_source_fingerprint_ref"
    assert duplicate_source["started_worker"] is False
    assert duplicate_source["worker_start_ref"] is None
    assert duplicate_source["duplicate_of_receipt_id"] == first["receipt_id"]


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


def test_dispatch_repeat_suppression_blocks_repeated_progress_first_owner_action_without_delta() -> None:
    repeat_suppression = importlib.import_module("med_autoscience.runtime_control.repeat_suppression")
    route = {
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "work_unit_fingerprint": "publication-blockers::same-source",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {"work_unit_id": "same-source-work-unit"},
    }
    dispatch = {
        "dispatch_status": "ready",
        "owner_route": route,
        "prompt_contract": {
            "do_not_repeat": True,
            "repeat_suppression_key": "publication-blockers::same-source",
            "owner_route": route,
        },
    }

    guard = repeat_suppression.dispatch_repeat_suppression(
        dispatch=dispatch,
        current_study={"study_id": "001-risk", "meaningful_artifact_delta": False},
        existing_dispatch={
            **dispatch,
            "dispatch_status": "repeat_suppressed",
            "repeat_suppression_key": "publication-blockers::same-source",
        },
    )

    assert guard["repeat_suppressed"] is True
    assert guard["why_not_applied"] == "repeat_suppressed"
    assert guard["suppression_source"] == "existing_dispatch_same_work_unit_without_artifact_delta"
