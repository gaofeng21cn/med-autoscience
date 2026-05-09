from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.test_study_runtime_execution_control_intent import (
    _base_status_payload,
    _write_controller_decision_authorization,
    _write_publication_eval_work_unit_authority,
    _write_runtime_state,
)


def test_execute_noop_runtime_decision_adopts_mas_quality_repair_report(
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
            "active_run_id": "run-003",
            "source": "medautosci-test",
        },
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={
            "reason": "same_fingerprint_no_artifact_delta",
            "active_run_id": None,
            "source": "medautosci-test",
        },
    )
    report_path = (
        quest_root
        / ".ds"
        / "cold_archive"
        / "report_history"
        / "artifacts"
        / "reports"
        / "report-e6142367.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "mas_quality_repair_batch",
                "created_at": "2026-05-07T12:06:55+00:00",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::claim-story-figure",
                "route_target": "analysis-campaign",
                "metrics_summary": {
                    "specificity_targets_repaired_or_classified": 1,
                    "missing_target_files_after_repair": 0,
                    "targets_with_repair_markers": 1,
                    "publication_gate_cleared": 0,
                    "writing_ready_after_repair": 0,
                    "finalize_ready_after_repair": 0,
                },
                "remaining_blockers": [
                    "Publication gate remains blocked; traceability repair is not writing/finalize clearance."
                ],
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
            "active_run_id": None,
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("MAS quality repair report must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate", "artifact_written"]
    assert adoption["report_ref"] == str(report_path)
    assert adoption["recommended_next_route"] == "return_to_publication_gate_recheck"
    assert adoption["result"]["specificity_targets_repaired_or_classified"] == 1
    assert adoption["result"]["publication_gate_cleared"] is False
    assert status.to_dict()["controller_work_unit_next_route"] == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "publication_gate",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }


def test_execute_noop_runtime_decision_adopts_mas_quality_repair_latest_specificity_targets(
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
        emitted_at="2026-05-07T15:01:35+00:00",
        work_unit_fingerprint="publication-blockers::497d1260db522f01",
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
        payload={"message_id": "msg-quality-repair-previous", "active_run_id": "run-003"},
        recorded_at="2026-05-07T15:02:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": None},
        recorded_at="2026-05-07T15:03:00+00:00",
    )
    report_path = quest_root / "artifacts" / "reports" / "mas_quality_repair" / "latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_kind": "mas_quality_repair_batch",
                "updated_at": "2026-05-07T12:05:05+00:00",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "route_target": "analysis-campaign",
                "specificity_targets": [
                    {
                        "target_id": "claim_evidence_map",
                        "target_kind": "claim",
                        "status": "repaired_traceability_marker_added",
                        "remaining_gate_status": {
                            "writing_ready": False,
                            "finalize_ready": False,
                            "publication_gate_clear": False,
                        },
                    }
                ],
                "remaining_blockers": ["Publication gate remains blocked."],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": None, "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("MAS quality repair latest report must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert adoption["report_ref"] == str(report_path)
    assert adoption["created_at"] == "2026-05-07T12:05:05+00:00"
    assert adoption["result"]["specificity_targets_repaired_or_classified"] == 1
    assert adoption["result"]["publication_gate_cleared"] is False


def test_execute_noop_runtime_decision_adopts_analysis_claim_evidence_repair_batch_report(
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
        emitted_at="2026-05-07T15:01:34+00:00",
        work_unit_fingerprint="publication-blockers::497d1260db522f01",
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
        payload={"message_id": "msg-quality-repair-previous", "active_run_id": "run-002"},
        recorded_at="2026-05-07T15:02:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": None},
        recorded_at="2026-05-07T15:03:00+00:00",
    )
    report_path = (
        quest_root
        / ".ds"
        / "cold_archive"
        / "report_history"
        / "artifacts"
        / "reports"
        / "report-bb7fa10d.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "report_type": "analysis_claim_evidence_repair",
                "created_at": "2026-05-07T12:01:57+00:00",
                "updated_at": "2026-05-07T12:01:57+00:00",
                "status": "completed",
                "controller": {
                    "active_work_unit_id": "analysis_claim_evidence_repair",
                    "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                    "controller_actions": "run_quality_repair_batch",
                    "route_target": "analysis-campaign",
                },
                "repair_counts": {
                    "changed_files_count": 4,
                    "unresolved_local_defect_count": 0,
                    "gate_owned_or_nonlocal_defect_count": 0,
                },
                "recommended_next_route": "return_to_publication_gate_recheck",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": None, "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("analysis repair batch report must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert adoption["report_ref"] == str(report_path)
    assert adoption["created_at"] == "2026-05-07T12:01:57+00:00"
    assert adoption["result"]["changed_files_count"] == 4
    assert adoption["result"]["unresolved_local_defect_count"] == 0


def test_execute_noop_runtime_decision_adopts_analysis_lane_exhausted_handoff(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    quest_root = tmp_path / "runtime" / "quest-003"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-09T12:09:27+00:00",
        work_unit_fingerprint="publication-blockers::497d1260db522f01",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
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
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-003"},
        recorded_at="2026-05-09T11:41:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": "run-003"},
        recorded_at="2026-05-09T11:50:00+00:00",
    )
    handoff_path = quest_root / "artifacts" / "supervision" / "controller_consumption" / "latest.json"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "surface": "controller_consumption_receipt_latest",
                "study_id": "003-dpcc",
                "quest_id": "quest-003",
                "run_id": "run-003",
                "updated_at": "2026-05-09T11:58:53Z",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "repair_packet_ref": "artifacts/reports/analysis_claim_evidence_repair/20260509T115853Z.json",
                "repair_packet_type": "analysis_claim_evidence_current_run_handoff",
                "analysis_lane_status": "exhausted_for_current_fingerprint",
                "meaningful_artifact_delta": True,
                "next_owner": "write/ai_reviewer",
                "next_work_unit": "manuscript_story_repair",
                "dedupe_recommendation": (
                    "Do not requeue publication-blockers::497d1260db522f01 to analysis-campaign "
                    "unless a new target, new evidence source, or explicit analysis-authorized "
                    "repair surface changes the repair boundary."
                ),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": "run-003", "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["quest_id"] = "quest-003"
    status_payload["execution"]["quest_id"] = "quest-003"
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("analysis-exhausted handoff must be adopted instead of relayed")

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
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    next_route = status.to_dict()["controller_work_unit_next_route"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == [
        "delivered",
        "skipped_duplicate",
        "artifact_written",
        "owner_handoff",
    ]
    assert lifecycle["terminal_consumed"] is True
    assert lifecycle["block_reason"] == "owner_handoff"
    assert adoption["report_ref"] == str(handoff_path)
    assert adoption["analysis_lane_status"] == "exhausted_for_current_fingerprint"
    assert adoption["next_owner"] == "write/ai_reviewer"
    assert adoption["next_work_unit"] == "manuscript_story_repair"
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert next_route == {
        "recommended_next_route": "handoff_to_next_owner",
        "owner": "write/ai_reviewer",
        "next_work_unit": "manuscript_story_repair",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": False,
    }


def test_execute_noop_runtime_decision_adopts_current_run_repair_control_packet(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "002-dm"
    quest_root = tmp_path / "runtime" / "quest-002"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-09T11:47:20+00:00",
        work_unit_fingerprint="publication-blockers::497d1260db522f01",
        next_work_unit={
            "unit_id": "analysis_claim_evidence_repair",
            "lane": "analysis-campaign",
            "summary": "Repair claim-evidence blockers.",
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
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-002"},
        recorded_at="2026-05-09T11:47:30+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta", "active_run_id": "run-002"},
        recorded_at="2026-05-09T11:50:00+00:00",
    )
    report_path = quest_root / "artifacts" / "reports" / "analysis_claim_evidence_repair" / "latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "002-dm",
                "quest_id": "quest-002",
                "run_id": "run-002",
                "created_at": "2026-05-09T11:58:53Z",
                "artifact_kind": "analysis_claim_evidence_current_run_repair_control_packet",
                "status": "completed_as_current_run_repair_control_packet",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "meaningful_artifact_delta": True,
                "next_work_unit": {
                    "unit_id": "analysis_claim_evidence_repair",
                    "lane": "analysis-campaign",
                    "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                },
                "specificity_target_results": [
                    {
                        "target_id": "claim_evidence_map",
                        "target_kind": "claim",
                        "status": "repaired_traceability_marker_added",
                    }
                ],
                "delta_summary": "Current run produced a controller repair packet that must be consumed.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": "run-002", "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["quest_id"] = "quest-002"
    status_payload["execution"]["quest_id"] = "quest-002"
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("current-run repair control packet must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    next_route = status.to_dict()["controller_work_unit_next_route"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate", "artifact_written"]
    assert adoption["report_ref"] == str(report_path)
    assert adoption["recommended_next_route"] == "return_to_publication_gate_recheck"
    assert adoption["artifact_kind"] == "analysis_claim_evidence_current_run_repair_control_packet"
    assert adoption["status"] == "completed_as_current_run_repair_control_packet"
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert adoption["result"]["specificity_targets_repaired_or_classified"] == 1
    assert next_route == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "publication_gate",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }


def test_execute_noop_runtime_decision_adopts_analysis_source_repair_packet(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "002-dm"
    quest_root = tmp_path / "runtime" / "quest-002"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-09T16:49:15+00:00",
        work_unit_fingerprint="publication-blockers::497d1260db522f01",
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
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-002"},
        recorded_at="2026-05-09T16:49:44+00:00",
    )
    report_path = quest_root / "artifacts" / "reports" / "analysis_claim_evidence_repair" / "latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "study_id": "002-dm",
                "quest_id": "quest-002",
                "run_id": "run-002",
                "created_at": "2026-05-09T15:01:53Z",
                "artifact_kind": "analysis_claim_evidence_source_repair",
                "status": "completed",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "meaningful_artifact_delta": True,
                "specificity_target_results": [
                    {
                        "target_id": "claim_evidence_map",
                        "target_kind": "claim",
                        "blocking_reason": "claim_evidence_consistency_failed",
                        "result": "repaired",
                    },
                    {
                        "target_id": "publication_gate_source_path",
                        "target_kind": "source_path",
                        "blocking_reason": "stale_submission_minimal_authority",
                        "result": "fresh_receipt_written",
                    },
                ],
                "source_repairs": [
                    {"path": "studies/002-dm/paper/claim_evidence_map.json"},
                    {"path": "studies/002-dm/paper/results_narrative_map.json"},
                ],
                "remaining_blockers": {
                    "medical_publication_surface_status": "blocked",
                    "medical_publication_surface_blockers": ["methods_completeness_incomplete"],
                    "next_owner": "mas_controller_methods_reporting_and_prose_repair",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": "run-002", "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["quest_id"] = "quest-002"
    status_payload["execution"]["quest_id"] = "quest-002"
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("source repair packet must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    next_route = status.to_dict()["controller_work_unit_next_route"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert [event["event_type"] for event in events] == ["delivered", "artifact_written"]
    assert adoption["report_ref"] == str(report_path)
    assert adoption["artifact_kind"] == "analysis_claim_evidence_source_repair"
    assert adoption["next_owner"] == "mas_controller_methods_reporting_and_prose_repair"
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert adoption["result"]["specificity_targets_repaired_or_classified"] == 2
    assert adoption["result"]["source_repairs_count"] == 2
    assert next_route == {
        "recommended_next_route": "return_to_publication_gate_recheck",
        "owner": "mas_controller_methods_reporting_and_prose_repair",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": True,
    }


def test_execute_noop_runtime_decision_adopts_retry_backoff_handoff_for_current_decision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc"
    quest_root = tmp_path / "runtime" / "quest-003"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        emitted_at="2026-05-09T16:32:51+00:00",
        work_unit_fingerprint="publication-blockers::497d1260db522f01",
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
        payload={"message_id": "msg-analysis-repair", "active_run_id": "run-003"},
        recorded_at="2026-05-09T15:01:00+00:00",
    )
    control_intent.append_event(
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
    handoff_path = quest_root / "artifacts" / "supervision" / "controller_consumption" / "latest.json"
    handoff_path.parent.mkdir(parents=True, exist_ok=True)
    handoff_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "surface": "controller_consumption_receipt_latest",
                "study_id": "003-dpcc",
                "quest_id": "quest-003",
                "run_id": "run-003",
                "updated_at": "2026-05-09T16:34:21Z",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "repair_packet_type": "analysis_claim_evidence_retry_backoff_dedupe_handoff",
                "analysis_lane_status": "exhausted_for_current_fingerprint",
                "meaningful_artifact_delta": True,
                "next_owner": "write/ai_reviewer",
                "next_work_unit": "manuscript_story_repair",
                "dedupe_recommendation": "Do not requeue this fingerprint to analysis-campaign.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_runtime_state(quest_root, {"status": "running", "active_run_id": "run-003", "pending_user_message_count": 0})
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["quest_id"] = "quest-003"
    status_payload["execution"]["quest_id"] = "quest-003"
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("retry-backoff handoff must be adopted instead of relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    next_route = status.to_dict()["controller_work_unit_next_route"]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert adoption["report_ref"] == str(handoff_path)
    assert adoption["analysis_lane_status"] == "exhausted_for_current_fingerprint"
    assert adoption["next_owner"] == "write/ai_reviewer"
    assert adoption["next_work_unit"] == "manuscript_story_repair"
    assert next_route == {
        "recommended_next_route": "handoff_to_next_owner",
        "owner": "write/ai_reviewer",
        "next_work_unit": "manuscript_story_repair",
        "quality_gate_relaxation_allowed": False,
        "runtime_relaunch_required": False,
    }


def test_execute_resume_runtime_decision_stops_after_work_unit_evidence_adoption(
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
    control_intent.append_event(study_root=study_root, identity=identity, event_type="delivered", payload={})
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="skipped_duplicate",
        payload={"reason": "same_fingerprint_no_artifact_delta"},
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
            "status": "active",
            "active_run_id": None,
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["decision"] = "resume"
    status_payload["reason"] = "quest_marked_running_but_no_live_session"
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("adopted work unit evidence must stop duplicate controller relay")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert status.decision is module.StudyRuntimeDecision.NOOP
    assert status.reason is module.StudyRuntimeReason.CONTROLLER_WORK_UNIT_EVIDENCE_ADOPTED
    assert "resume_postcondition" not in status.to_dict()
