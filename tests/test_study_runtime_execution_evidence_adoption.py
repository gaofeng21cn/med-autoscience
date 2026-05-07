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
    report_path = quest_root / ".ds" / "cold_archive" / "report_history" / "artifacts" / "reports" / "report-e6142367.json"
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
