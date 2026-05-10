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


def test_execute_resume_runtime_decision_redrives_platform_repair_instead_of_stopping_after_adoption(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    router = importlib.import_module("med_autoscience.controllers.study_runtime_router")
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
        event_type="artifact_written",
        payload={
            "active_run_id": "run-003-old",
            "report_ref": str(quest_root / "artifacts" / "supervision" / "controller_consumption" / "latest.json"),
            "created_at": "2026-05-09T11:58:53Z",
            "work_unit_id": "analysis_claim_evidence_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "handoff_to_next_owner",
            "source": "medautosci-test",
            "analysis_lane_status": "exhausted_for_current_fingerprint",
            "next_owner": "write/ai_reviewer",
            "next_work_unit": "manuscript_story_repair",
            "result": {"meaningful_artifact_delta": True},
        },
        recorded_at="2026-05-09T12:10:00+00:00",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "active",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "last_controller_decision_authorization": {
                "source": "runtime_supervisor_scan_platform_repair",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            },
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_id"] = "003-dpcc"
    status_payload["study_root"] = str(study_root)
    status_payload["quest_id"] = "quest-003"
    status_payload["quest_root"] = str(quest_root)
    status_payload["execution"]["quest_id"] = "quest-003"
    status_payload["decision"] = "resume"
    status_payload["reason"] = "quest_marked_running_but_no_live_session"
    status_payload["continuation_state"] = {
        "quest_status": "active",
        "active_run_id": None,
        "continuation_policy": "auto",
        "continuation_anchor": "decision",
        "continuation_reason": "controller_work_unit_pending",
        "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
    }
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    resume_calls: list[dict[str, object]] = []

    monkeypatch.setattr(router, "_build_context_create_payload", lambda context: {"startup_contract": {}})
    monkeypatch.setattr(
        router,
        "_sync_existing_quest_startup_context",
        lambda **kwargs: {
            "ok": True,
            "quest_id": kwargs["quest_id"],
            "snapshot": {
                "quest_id": kwargs["quest_id"],
                "startup_contract": {},
            },
        },
    )
    monkeypatch.setattr(
        router,
        "_resume_quest",
        lambda *, runtime_root, quest_id, source, runtime_backend: resume_calls.append(
            {
                "runtime_root": str(runtime_root),
                "quest_id": quest_id,
                "source": source,
            }
        )
        or {
            "ok": True,
            "status": "running",
            "started": True,
            "snapshot": {"status": "running", "active_run_id": "run-003-redrive"},
        },
    )

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=object(),
        source="runtime_supervisor_scan_platform_repair",
        execution={"quest_id": "quest-003", "auto_resume": True},
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.RESUME
    assert resume_calls == [
        {
            "runtime_root": str(tmp_path / "runtime"),
            "quest_id": "quest-003",
            "source": "runtime_supervisor_scan_platform_repair",
        }
    ]
    assert status.decision is module.StudyRuntimeDecision.RESUME
    assert status.quest_status is module.StudyRuntimeQuestStatus.RUNNING
    assert status.to_dict()["resume_postcondition"]["active_run_id"] == "run-003-redrive"
    assert "controller_work_unit_evidence_adoption" not in status.to_dict()
