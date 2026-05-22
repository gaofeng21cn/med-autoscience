from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_study_runtime_execution_control_intent_cases.helpers import (
    _base_status_payload,
    _write_controller_decision_authorization,
    _write_publication_eval_authority,
    _write_publication_eval_gate_replay_with_specificity_targets,
    _write_publication_eval_work_unit_authority,
    _write_runtime_state,
)

@pytest.mark.parametrize("report_location", ["current", "cold_archive"])
def test_execute_noop_runtime_decision_adopts_analysis_repair_report_without_relay(
    tmp_path: Path,
    report_location: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        work_unit_fingerprint="publication-blockers::claim-story-figure",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
    )
    _write_publication_eval_work_unit_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={
            "delivery_mode": "managed_runtime_chat",
            "message_id": "msg-quality-repair-previous",
            "active_run_id": "run-live-001",
            "source": "medautosci-test",
        },
        recorded_at="2026-04-25T06:22:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={
            "reason": "same_fingerprint_no_artifact_delta",
            "active_run_id": "run-live-001",
            "source": "medautosci-test",
        },
        recorded_at="2026-04-25T06:23:00+00:00",
    )
    report_suffix = Path(
        "artifacts",
        "reports",
        "analysis_claim_evidence_repair",
        "specificity_target_traceability_reaudit.json",
    )
    if report_location == "cold_archive":
        report_path = (
            quest_root
            / ".ds"
            / "cold_archive"
            / "report_history"
            / "run-live-001"
            / report_suffix
        )
    else:
        report_path = quest_root / report_suffix
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "created_at": "2026-04-25T06:24:00+00:00",
                "work_unit_id": "analysis_claim_evidence_repair",
                "route_target": "analysis-campaign",
                "action": "run_quality_repair_batch",
                "result": {
                    "local_traceability_repair_complete": True,
                    "unresolved_local_defect_count": 0,
                    "gate_owned_or_nonlocal_defect_count": 0,
                    "recommended_next_route": "return_to_publication_gate_recheck",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-live-001",
            "pending_user_message_count": 0,
            "same_fingerprint_auto_turn_count": 4,
            "control_intent_lifecycle": {
                "state": "await_artifact_delta_or_gate_replay",
                "control_intent_key": authorization_context["control_intent_key"],
            },
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("existing controlled analysis repair report must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    status_payload = status.to_dict()

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate", "artifact_written"]
    assert lifecycle["artifact_delta_observed"] is True
    adoption = status_payload["controller_work_unit_evidence_adoption"]
    assert adoption["report_ref"] == str(report_path)
    assert adoption["created_at"] == "2026-04-25T06:24:00+00:00"
    assert adoption["active_run_id"] == "run-live-001"
    assert adoption["work_unit_id"] == "analysis_claim_evidence_repair"
    assert adoption["route_target"] == "analysis-campaign"
    assert adoption["recommended_next_route"] == "return_to_publication_gate_recheck"
    deduped = status_payload["controller_decision_authorization_deduped"]
    assert deduped["lifecycle"]["artifact_delta_observed"] is True
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    marker = runtime_state["last_controller_decision_authorization"]
    assert marker["active_run_id"] == "run-live-001"
    assert marker["delivery_mode"] == "controller_work_unit_evidence_adoption"
    assert marker["source"] == "medautosci-test"
    assert marker["controller_work_unit_lifecycle"]["lifecycle_state"] == "artifact_written"

    module._execute_runtime_decision(status=status, context=context)
    events_after_replay = control_intent.read_events(study_root=study_root)
    assert [event["event_type"] for event in events_after_replay] == [
        "delivered",
        "skipped_duplicate",
        "artifact_written",
    ]

def test_execute_noop_runtime_decision_adopts_legacy_repair_report_bound_by_current_authorization(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        work_unit_fingerprint="publication-blockers::claim-story-figure",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
        },
    )
    _write_publication_eval_work_unit_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={
            "delivery_mode": "managed_runtime_chat",
            "message_id": "msg-quality-repair-previous",
            "active_run_id": "run-dee40a6a",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-07T11:40:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={
            "reason": "same_fingerprint_no_artifact_delta",
            "active_run_id": "run-dee40a6a",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-07T12:06:00+00:00",
    )
    report_path = (
        quest_root
        / ".ds"
        / "cold_archive"
        / "report_history"
        / "artifacts"
        / "reports"
        / "analysis_claim_evidence_repair"
        / "specificity_target_traceability_reaudit.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "report_type": "analysis_claim_evidence_repair_specificity_target_traceability_reaudit",
                "created_at": "2026-05-07T11:57:12+00:00",
                "result": {
                    "changed_files_count": 4,
                    "fatal_local_defect": False,
                    "unresolved_local_defect_count": 0,
                    "gate_owned_or_nonlocal_defect_count": 0,
                    "local_traceability_repair_complete": True,
                    "recommended_next_route": "return_to_publication_gate_recheck",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-dee40a6a",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("legacy controlled report must be adopted through current authorization")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate", "artifact_written"]
    assert events[-1]["payload"]["report_ref"] == str(report_path)
    assert events[-1]["payload"]["created_at"] == "2026-05-07T11:57:12+00:00"
    assert events[-1]["payload"]["recommended_next_route"] == "return_to_publication_gate_recheck"
