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


def test_execute_noop_runtime_decision_ignores_repair_report_older_than_current_decision(
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
        decision_id="decision-analysis-redrive",
        emitted_at="2026-05-07T15:01:34+00:00",
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
        payload={"delivery_mode": "managed_runtime_chat", "message_id": "msg-old", "active_run_id": "run-old"},
        recorded_at="2026-05-07T11:41:18+00:00",
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
            "status": "running",
            "active_run_id": None,
            "pending_user_message_count": 0,
            "continuation_reason": "same_fingerprint_no_artifact_delta",
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    chats: list[dict[str, object]] = []

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            chats.append({"quest_id": quest_id, "text": text, "source": source})
            return {"ok": True, "message": {"id": "msg-redrive"}}

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    event_types = [event["event_type"] for event in control_intent.read_events(study_root=study_root)]

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert "artifact_written" not in event_types
    assert len(chats) == 1
    assert "decision-analysis-redrive" in str(chats[0]["text"])
