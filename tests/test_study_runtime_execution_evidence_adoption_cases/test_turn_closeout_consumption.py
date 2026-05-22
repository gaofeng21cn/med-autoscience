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
    status = module.ProgressProjectionStatus.from_payload(status_payload)

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
    assert [event["event_type"] for event in events] == ["delivered", "artifact_written", "owner_handoff"]
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
    status = module.ProgressProjectionStatus.from_payload(status_payload)

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


def test_execute_noop_runtime_decision_adopts_prior_delivered_run_closeout_after_next_run_starts(
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
            "paper/draft.md",
            "paper/build/review_manuscript.md",
            "artifacts/controller/quality_repair_batch/latest.json",
        ],
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-next",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["active_run_id"] = "run-next"
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("completed delivered-run closeout must be adopted instead of redriving")

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
    assert [event["event_type"] for event in events] == ["delivered", "artifact_written", "owner_handoff"]
    assert adoption["report_ref"] == str(closeout_path)
    assert adoption["active_run_id"] == "run-story"
    assert adoption["work_unit_id"] == "manuscript_story_repair"
    assert adoption["result"]["completed"] is True
    assert adoption["result"]["meaningful_artifact_delta"] is True
    assert adoption["result"]["artifact_refs_count"] == 3
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    marker = runtime_state["last_controller_decision_authorization"]
    assert marker["delivery_mode"] == "controller_work_unit_evidence_adoption"
    assert marker["active_run_id"] == "run-story"


def test_execute_noop_runtime_decision_refreshes_prior_adoption_with_newer_delivered_closeout(
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
            "message_id": "msg-story-repair-1",
            "active_run_id": "run-story-1",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T02:39:00+00:00",
    )
    _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-story-1",
        artifact_refs=[
            "paper/draft.md",
            "paper/build/review_manuscript.md",
        ],
        completed_at="2026-05-20T03:08:12Z",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={
            "active_run_id": "run-story-1",
            "report_ref": str(
                quest_root
                / "artifacts"
                / "runtime"
                / "turn_closeouts"
                / "run-story-1.json"
            ),
            "created_at": "2026-05-20T03:08:12+00:00",
            "work_unit_id": "manuscript_story_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "return_to_publication_gate_recheck",
            "source": "medautosci-test",
            "next_owner": "publication_gate",
            "result": {
                "completed": True,
                "meaningful_artifact_delta": True,
                "artifact_refs_count": 2,
                "publication_gate_recheck_required": True,
            },
        },
        recorded_at="2026-05-20T03:09:00+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="delivered",
        payload={
            "delivery_mode": "managed_runtime_chat",
            "message_id": "msg-story-repair-2",
            "active_run_id": "run-story-2",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T04:21:00+00:00",
    )
    closeout_path = _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-story-2",
        artifact_refs=[
            "paper/draft.md",
            "paper/build/review_manuscript.md",
            "artifacts/reports/manuscript_story_repair/latest.json",
            "artifacts/controller/repair_execution_evidence/latest.json",
        ],
        completed_at="2026-05-20T04:32:38Z",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-next",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["active_run_id"] = "run-next"
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("newer delivered-run closeout must refresh prior evidence adoption")

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
    assert [event["event_type"] for event in events] == [
        "delivered",
        "artifact_written",
        "delivered",
        "artifact_written",
        "owner_handoff",
    ]
    assert adoption["report_ref"] == str(closeout_path)
    assert adoption["created_at"] == "2026-05-20T04:32:38+00:00"
    assert adoption["result"]["artifact_refs_count"] == 4


def test_execute_noop_runtime_decision_adopts_post_authorization_story_closeout_without_delivery_event(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_story_repair_authorization(study_root, emitted_at="2026-05-20T04:42:17+00:00")
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
            "message_id": "msg-story-repair-old",
            "active_run_id": "run-story-old",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T02:54:17+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={
            "active_run_id": "run-story-old",
            "report_ref": str(
                quest_root
                / "artifacts"
                / "runtime"
                / "turn_closeouts"
                / "run-story-old.json"
            ),
            "created_at": "2026-05-20T02:56:20+00:00",
            "work_unit_id": "manuscript_story_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "return_to_publication_gate_recheck",
            "source": "medautosci-test",
            "next_owner": "publication_gate",
            "result": {
                "completed": True,
                "meaningful_artifact_delta": True,
                "artifact_refs_count": 2,
                "publication_gate_recheck_required": True,
            },
        },
        recorded_at="2026-05-20T04:21:54+00:00",
    )
    closeout_path = _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-story-no-ledger-delivery",
        artifact_refs=[
            "../../../studies/001-risk/paper/draft.md",
            "../../../studies/001-risk/paper/build/review_manuscript.md",
        ],
        completed_at="2026-05-20T04:47:57Z",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-next",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["active_run_id"] = "run-next"
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("post-authorization story closeout must be adopted even if delivery ledger is missing")

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
    assert [event["event_type"] for event in events] == [
        "delivered",
        "artifact_written",
        "artifact_written",
        "owner_handoff",
    ]
    assert adoption["report_ref"] == str(closeout_path)
    assert adoption["created_at"] == "2026-05-20T04:47:57+00:00"
    assert adoption["result"]["artifact_refs_count"] == 2


def test_completed_story_repair_adoption_closes_publication_work_unit_lifecycle(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    runtime_auth = importlib.import_module("med_autoscience.runtime_transport.mas_runtime_core_turn_authorization")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    _write_story_repair_authorization(study_root)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("study_id: 001-risk\nquest_id: quest-001\n", encoding="utf-8")
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
            "active_run_id": "run-story-closed",
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T04:42:20+00:00",
    )
    _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-story-closed",
        artifact_refs=[
            "../../../studies/001-risk/paper/draft.md",
            "../../../studies/001-risk/paper/build/review_manuscript.md",
        ],
        completed_at="2026-05-20T04:47:57Z",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-next",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["active_run_id"] = "run-next"
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("completed story repair closeout must be adopted instead of redelivered")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    lifecycle = json.loads(
        (
            study_root
            / "artifacts"
            / "controller"
            / "publication_work_unit_lifecycle"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert lifecycle["status"] == "owner_handoff"
    assert lifecycle["terminal_consumed"] is True
    assert lifecycle["next_owner"] == "publication_gate"
    assert lifecycle["work_unit"]["unit_id"] == "manuscript_story_repair"
    assert lifecycle["unit_statuses"] == [{"unit_id": "manuscript_story_repair", "status": "owner_handoff"}]

    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    assert "last_controller_decision_authorization" in runtime_state
    sanitized = runtime_auth._sanitize_runtime_state_before_turn(
        runtime_state=runtime_state,
        quest_root=quest_root,
        quest_id="quest-001",
    )
    assert "last_controller_decision_authorization" not in sanitized
    assert sanitized["last_runtime_turn_state_sanitization"]["reason"] == "publication_work_unit_lifecycle_done"


def test_existing_completed_adoption_before_decision_refreshes_publication_work_unit_lifecycle(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    control_intent = importlib.import_module("med_autoscience.controllers.control_intent")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    _write_story_repair_authorization(study_root, emitted_at="2026-05-20T06:42:29+00:00")
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text("study_id: 001-risk\nquest_id: quest-001\n", encoding="utf-8")
    _write_publication_eval_work_unit_authority(study_root)
    _write_blocked_publication_work_unit_lifecycle(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
    identity = auth_module._controller_decision_authorization_identity(authorization_context)
    closeout_path = _write_turn_closeout(
        quest_root=quest_root,
        run_id="run-story-closed",
        artifact_refs=[
            "../../../studies/001-risk/paper/draft.md",
            "../../../studies/001-risk/paper/build/review_manuscript.md",
        ],
        completed_at="2026-05-20T06:34:49Z",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="artifact_written",
        payload={
            "active_run_id": "run-story-closed",
            "report_ref": str(closeout_path),
            "created_at": "2026-05-20T06:34:49+00:00",
            "work_unit_id": "manuscript_story_repair",
            "route_target": "analysis-campaign",
            "recommended_next_route": "return_to_publication_gate_recheck",
            "source": "medautosci-test",
            "next_owner": "publication_gate",
            "status": "completed",
            "result": {
                "completed": True,
                "meaningful_artifact_delta": True,
                "artifact_refs_count": 2,
                "publication_gate_recheck_required": True,
            },
        },
        recorded_at="2026-05-20T06:42:16+00:00",
    )
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="owner_handoff",
        payload={
            "reason": "completed_work_unit_evidence_adopted",
            "next_owner": "publication_gate",
            "next_work_unit": None,
            "report_ref": str(closeout_path),
            "source": "medautosci-test",
        },
        recorded_at="2026-05-20T06:42:16+00:00",
    )
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": None,
            "worker_running": False,
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status_payload["active_run_id"] = None
    status = module.ProgressProjectionStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("completed existing adoption must refresh lifecycle instead of redelivering")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    adoption = status.to_dict()["controller_work_unit_evidence_adoption"]
    assert adoption["already_recorded"] is True
    assert adoption["report_ref"] == str(closeout_path)
    lifecycle = json.loads(
        (
            study_root
            / "artifacts"
            / "controller"
            / "publication_work_unit_lifecycle"
            / "latest.json"
        ).read_text(encoding="utf-8")
    )
    assert lifecycle["status"] == "owner_handoff"
    assert lifecycle["gate_replay_status"] == "pending_recheck"
    assert lifecycle["terminal_consumed"] is True
    assert lifecycle["next_owner"] == "publication_gate"
    assert lifecycle["evidence_adoption"]["report_ref"] == str(closeout_path)
    assert lifecycle["work_unit"]["unit_id"] == "manuscript_story_repair"
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    marker_lifecycle = runtime_state["last_controller_decision_authorization"]["controller_work_unit_lifecycle"]
    assert marker_lifecycle["lifecycle_state"] == "owner_handoff"
    assert marker_lifecycle["latest_event_type"] == "owner_handoff"
    assert marker_lifecycle["terminal_consumed"] is True


def _write_story_repair_authorization(
    study_root: Path,
    *,
    emitted_at: str = "2026-05-20T02:38:29+00:00",
) -> None:
    _write_controller_decision_authorization(
        study_root,
        action_type="run_quality_repair_batch",
        decision_id="decision-story-repair",
        emitted_at=emitted_at,
        work_unit_fingerprint="publication-blockers::story",
        next_work_unit={
            "unit_id": "manuscript_story_repair",
            "lane": "write",
            "summary": "Repair the paper story around the current evidence and claim boundary.",
        },
    )


def _write_turn_closeout(
    *,
    quest_root: Path,
    run_id: str,
    artifact_refs: list[str],
    completed_at: str = "2026-05-20T03:08:12Z",
) -> Path:
    closeout_path = quest_root / "artifacts" / "runtime" / "turn_closeouts" / f"{run_id}.json"
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "quest_id": "quest-001",
                "run_id": run_id,
                "status": "completed",
                "completed_at": completed_at,
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


def _write_blocked_publication_work_unit_lifecycle(study_root: Path) -> None:
    path = study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_eval_id": "publication-eval::001-risk::quest-001::latest",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "status": "blocked",
                "work_unit": {"unit_id": "manuscript_story_repair"},
                "unit_statuses": [
                    {"unit_id": "repair_paper_live_paths", "status": "current"},
                    {"unit_id": "materialize_display_surface", "status": "materialized"},
                ],
                "gate_replay_status": "blocked",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
