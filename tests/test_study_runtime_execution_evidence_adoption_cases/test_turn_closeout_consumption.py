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


def test_execute_noop_runtime_decision_adopts_active_run_completed_turn_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_story_repair_authorization(study_root)
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
            "message_id": "msg-story-repair",
            "active_run_id": "run-story",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T02:39:00+00:00",
    )
    closeout_path = _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-story",
        artifact_refs=[
            "../../../studies/001-risk/paper/draft.md",
            "../../../studies/001-risk/paper/build/review_manuscript.md",
            "../../../studies/001-risk/artifacts/controller/quality_repair_batch/latest.json",
        ],
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-story",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("completed active-run turn closeout must be adopted instead of relayed")

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
    assert [event["event_type"] for event in events] == ["delivered", "artifact_written"]
    assert adoption["report_ref"] == str(closeout_path)
    assert adoption["created_at"] == "2026-05-20T03:08:12+00:00"
    assert adoption["work_unit_id"] == "manuscript_story_repair"
    assert adoption["result"]["completed"] is True
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert adoption["result"]["artifact_refs_count"] == 3
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    marker = runtime_state["last_controller_decision_authorization"]
    assert marker["delivery_mode"] == "controller_work_unit_evidence_adoption"
    assert marker["active_run_id"] == "run-story"


def test_execute_noop_runtime_decision_ignores_non_active_turn_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_story_repair_authorization(study_root)
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
            "message_id": "msg-story-repair",
            "active_run_id": "run-current",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T02:39:00+00:00",
    )
    _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-stale",
        artifact_refs=["../../../studies/001-risk/paper/draft.md"],
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-current",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            return {
                "status": "queued",
                "active_run_id": "run-current",
                "message_id": "msg-redrive",
            }

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    module._execute_runtime_decision(status=status, context=context)
    events = control_intent.read_events(study_root=study_root)

    assert [event["event_type"] for event in events] == ["delivered", "skipped_duplicate"]
    assert all(event["event_type"] != "artifact_written" for event in events)
    assert "controller_work_unit_evidence_adoption" not in status.to_dict()


def _write_story_repair_authorization(study_root: Path) -> None:
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        decision_id="decision-story-repair",
        emitted_at="2026-05-20T02:38:29+00:00",
        work_unit_fingerprint="publication-blockers::story",
        next_work_unit={
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Repair the paper story around the current evidence and claim boundary.",
        },
    )


def _write_turn_closeout(*, quest_root: Path, run_id: str, artifact_refs: list[str]) -> Path:
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "quest_id": "quest-001",
                "run_id": run_id,
                "status": "completed",
                "completed_at": "2026-05-20T03:08:12Z",
                "meaningful_artifact_delta": True,
                "artifact_refs": artifact_refs,
                "blocked_reason": None,
                "next_owner": None,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return closeout_path
