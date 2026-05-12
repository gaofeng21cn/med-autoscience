from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    write_study,
    write_text,
)

def test_publication_work_unit_identity_ignores_downstream_delivery_churn() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_identity")

    with_delivery_churn = module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=[
            "claim_evidence_consistency_failed",
            "medical_publication_surface_blocked",
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "submission_surface_qc_failure_present",
        ],
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
        },
        action_type="run_gate_clearing_batch",
    )
    claim_only = module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=[
            "claim_evidence_consistency_failed",
            "medical_publication_surface_blocked",
        ],
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
        },
        action_type="run_gate_clearing_batch",
    )

    assert with_delivery_churn.effective_blockers == ("claim_evidence_consistency_failed",)
    assert with_delivery_churn.fingerprint == claim_only.fingerprint
    assert with_delivery_churn.dispatch_key == (
        f"{claim_only.fingerprint}::analysis_claim_evidence_repair::run_gate_clearing_batch"
    )
def test_work_unit_ledger_appends_replayable_events(tmp_path: Path) -> None:
    identity_module = importlib.import_module("med_autoscience.controllers.control_identity")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    identity = identity_module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=["claim_evidence_consistency_failed"],
        next_work_unit={"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        action_type="run_gate_clearing_batch",
    )
    study_root = tmp_path / "studies" / "003-dpcc"

    proposed = ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="proposed",
        payload={"source": "publication_gate"},
        recorded_at="2026-04-26T00:00:00+00:00",
    )
    dispatched = ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "runtime_watch"},
        recorded_at="2026-04-26T00:01:00+00:00",
    )

    events = ledger.read_events(study_root=study_root)

    assert [event["event_type"] for event in events] == ["proposed", "dispatched"]
    assert proposed["event_id"] != dispatched["event_id"]
    assert events[-1]["identity"]["dispatch_key"] == identity.dispatch_key
    assert ledger.latest_event(study_root=study_root, dispatch_key=identity.dispatch_key)["event_type"] == "dispatched"
def test_control_intent_identity_excludes_delivery_attempt_metadata() -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    first = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="revision checklist mapping",
        blocker_authority_fingerprint="runtime_escalation:fp-1",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )
    replay = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="revision checklist mapping",
        blocker_authority_fingerprint="runtime_escalation:fp-1",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )
    superseding_feedback = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="new reviewer feedback mapping",
        blocker_authority_fingerprint="runtime_escalation:fp-2",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )

    assert first.business_key == replay.business_key
    assert first.business_key != superseding_feedback.business_key
    assert "active_run_id" not in first.to_dict()
def test_control_intent_ledger_records_latest_business_key_event(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "001-risk"
    identity = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="write",
        work_unit_id="manuscript repair",
        blocker_authority_fingerprint="task-intake:fp-1",
        controller_actions=("submit_study_task",),
        source_kind="study_task_intake",
    )

    module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"active_run_id": "run-001"},
        recorded_at="2026-04-29T00:00:00+00:00",
    )
    module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="replayed",
        payload={"active_run_id": "run-002"},
        recorded_at="2026-04-29T00:01:00+00:00",
    )

    latest = module.latest_event(study_root=study_root, business_key=identity.business_key)

    assert latest["event_type"] == "replayed"
    assert latest["identity"]["business_key"] == identity.business_key
    assert latest["payload"]["active_run_id"] == "run-002"
def test_control_intent_lifecycle_blocks_same_fingerprint_without_artifact_delta(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "001-risk"
    identity = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="revision checklist mapping",
        blocker_authority_fingerprint="publication-gate::fp-1",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )

    module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"active_run_id": "run-001"},
        recorded_at="2026-04-29T00:00:00+00:00",
    )

    lifecycle = module.lifecycle_state(study_root=study_root, identity=identity)
    skipped = module.append_skipped_duplicate_if_needed(
        study_root=study_root,
        identity=identity,
        payload={"reason": lifecycle["block_reason"]},
        recorded_at="2026-04-29T00:01:00+00:00",
    )

    assert lifecycle["delivery_blocked"] is True
    assert lifecycle["artifact_delta_observed"] is False
    assert lifecycle["block_reason"] == "same_fingerprint_no_artifact_delta"
    assert skipped["event_type"] == "skipped_duplicate"
    assert module.lifecycle_state(study_root=study_root, identity=identity)["delivery_blocked"] is True
def test_control_intent_lifecycle_blocks_terminal_platform_work_unit_states(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "001-risk"
    terminal_event_expectations = {
        "closed": "closed",
        "needs_specificity": "needs_specificity",
        "platform_repair_required": "platform_repair_required",
        "await_artifact_delta_or_gate_replay": "await_artifact_delta_or_gate_replay",
    }

    for index, (event_type, block_reason) in enumerate(terminal_event_expectations.items(), start=1):
        identity = module.build_control_intent_identity(
            study_id="001-risk",
            quest_id="quest-001",
            route_target="analysis-campaign",
            work_unit_id=f"analysis_claim_evidence_repair_{index}",
            blocker_authority_fingerprint="publication-blockers::497d1260db522f01",
            controller_actions=("ensure_study_runtime",),
            source_kind="controller_decision_authorization",
        )
        module.append_event(
            study_root=study_root,
            identity=identity,
            event_type="delivered",
            payload={"active_run_id": f"run-{index:03d}"},
            recorded_at=f"2026-05-02T00:0{index}:00+00:00",
        )
        module.append_event(
            study_root=study_root,
            identity=identity,
            event_type=event_type,
            payload={"reason": block_reason},
            recorded_at=f"2026-05-02T00:1{index}:00+00:00",
        )

        lifecycle = module.lifecycle_state(study_root=study_root, identity=identity)

        assert lifecycle["delivery_blocked"] is True
        assert lifecycle["block_reason"] == block_reason
def test_control_intent_skipped_duplicate_does_not_reopen_terminal_handoff(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "003-dpcc"
    identity = module.build_control_intent_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        route_target="analysis-campaign",
        work_unit_id="analysis_claim_evidence_repair",
        blocker_authority_fingerprint="publication-blockers::497d1260db522f01",
        controller_actions=("run_quality_repair_batch",),
        source_kind="controller_decision_authorization",
    )
    module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="owner_handoff",
        payload={
            "reason": "exhausted_for_current_fingerprint",
            "next_owner": "write/ai_reviewer",
            "next_work_unit": "manuscript_story_repair",
        },
        recorded_at="2026-05-09T15:06:43+00:00",
    )

    skipped = module.append_skipped_duplicate_if_needed(
        study_root=study_root,
        identity=identity,
        payload={"reason": "owner_handoff"},
        recorded_at="2026-05-09T16:27:24+00:00",
    )
    lifecycle = module.lifecycle_state(study_root=study_root, identity=identity)

    assert skipped is None
    assert [event["event_type"] for event in module.read_events(study_root=study_root)] == ["owner_handoff"]
    assert lifecycle["latest_event_type"] == "owner_handoff"
    assert lifecycle["terminal_consumed"] is True
    assert lifecycle["block_reason"] == "owner_handoff"
def test_control_intent_delivered_does_not_reopen_terminal_handoff(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "003-dpcc"
    identity = module.build_control_intent_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        route_target="analysis-campaign",
        work_unit_id="analysis_claim_evidence_repair",
        blocker_authority_fingerprint="publication-blockers::497d1260db522f01",
        controller_actions=("run_quality_repair_batch",),
        source_kind="controller_decision_authorization",
    )
    module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="owner_handoff",
        payload={
            "reason": "exhausted_for_current_fingerprint",
            "next_owner": "write/ai_reviewer",
            "next_work_unit": "manuscript_story_repair",
        },
        recorded_at="2026-05-09T15:06:43+00:00",
    )

    delivered = module.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={"active_run_id": "run-003", "message_id": "msg-repeat"},
        recorded_at="2026-05-09T16:38:02+00:00",
    )
    lifecycle = module.lifecycle_state(study_root=study_root, identity=identity)

    assert delivered["event_type"] == "skipped_duplicate"
    assert delivered["payload"]["reason"] == "owner_handoff"
    assert [event["event_type"] for event in module.read_events(study_root=study_root)] == [
        "owner_handoff",
        "skipped_duplicate",
    ]
    assert lifecycle["latest_event_type"] == "skipped_duplicate"
    assert lifecycle["terminal_consumed"] is False
    assert lifecycle["block_reason"] == "owner_handoff"
def test_control_intent_lifecycle_supersedes_prior_fingerprint_and_resets_series(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "studies" / "001-risk"
    first = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="revision checklist mapping",
        blocker_authority_fingerprint="publication-gate::source-a",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )
    source_signature_changed = module.build_control_intent_identity(
        study_id="001-risk",
        quest_id="quest-001",
        route_target="analysis-campaign",
        work_unit_id="revision checklist mapping",
        blocker_authority_fingerprint="publication-gate::source-b",
        controller_actions=("ensure_study_runtime",),
        source_kind="controller_decision_authorization",
    )

    module.append_event(
        study_root=study_root,
        identity=first,
        event_type="delivered",
        payload={"active_run_id": "run-001"},
        recorded_at="2026-04-29T00:00:00+00:00",
    )
    module.append_event(
        study_root=study_root,
        identity=source_signature_changed,
        event_type="delivered",
        payload={"active_run_id": "run-002"},
        recorded_at="2026-04-29T00:02:00+00:00",
    )

    events = module.read_events(study_root=study_root)
    first_latest = module.latest_event(study_root=study_root, business_key=first.business_key)

    assert first.supersession_key == source_signature_changed.supersession_key
    assert first.business_key != source_signature_changed.business_key
    assert [event["event_type"] for event in events] == ["delivered", "superseded", "delivered"]
    assert first_latest["event_type"] == "superseded"
    assert first_latest["payload"]["superseding_business_key"] == source_signature_changed.business_key
def test_work_unit_ledger_coalesces_lifecycle_and_enforces_single_writer(tmp_path: Path) -> None:
    identity_module = importlib.import_module("med_autoscience.controllers.control_identity")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    identity = identity_module.publication_work_unit_identity(
        study_id="003-dpcc",
        quest_id="quest-003",
        blockers=["claim_evidence_consistency_failed"],
        next_work_unit={"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        action_type="run_gate_clearing_batch",
    )
    study_root = tmp_path / "studies" / "003-dpcc"

    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="planned",
        payload={"source": "publication_gate"},
        recorded_at="2026-04-26T00:00:00+00:00",
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "runtime_watch"},
        recorded_at="2026-04-26T00:01:00+00:00",
    )
    accepted = ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="accepted",
        payload={"writer_id": "run-1"},
        recorded_at="2026-04-26T00:02:00+00:00",
    )
    superseded = ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="accepted",
        payload={"writer_id": "run-2"},
        recorded_at="2026-04-26T00:03:00+00:00",
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={"writer_id": "run-1", "artifact_ref": "paper/analysis.md"},
        recorded_at="2026-04-26T00:04:00+00:00",
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="gate_replayed",
        payload={"writer_id": "run-1", "publication_eval_ref": "artifacts/publication_eval/latest.json"},
        recorded_at="2026-04-26T00:05:00+00:00",
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"writer_id": "run-1"},
        recorded_at="2026-04-26T00:06:00+00:00",
    )

    summary = ledger.lifecycle_summary(study_root=study_root)

    assert accepted["event_type"] == "accepted"
    assert superseded["event_type"] == "superseded"
    assert superseded["payload"]["superseded_writer_id"] == "run-2"
    assert summary["units"][0]["lifecycle_state"] == "closed"
    assert summary["units"][0]["accepted_writer_id"] == "run-1"
    assert summary["units"][0]["event_types"] == [
        "planned",
        "dispatched",
        "accepted",
        "superseded",
        "artifact_written",
        "gate_replayed",
        "closed",
    ]
    assert summary["totals"]["replay_count"] == 1
