from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

from tests.test_study_runtime_execution_control_intent_cases.helpers import (
    _base_status_payload,
    _write_controller_decision_authorization,
    _write_publication_eval_authority,
    _write_publication_eval_gate_replay_with_specificity_targets,
    _write_publication_eval_work_unit_authority,
    _write_runtime_state,
)

def test_execute_noop_runtime_decision_defers_long_authorization_while_awaiting_artifact_delta(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root)
    _write_publication_eval_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
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
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("ordinary analysis authorization must wait for artifact delta or gate replay")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    events = importlib.import_module("med_autoscience.controllers.control_intent").read_events(study_root=study_root)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    deferred = status.to_dict()["controller_decision_authorization_deferred"]
    assert deferred["reason"] == "await_artifact_delta_or_gate_replay"
    assert deferred["control_intent_key"] == authorization_context["control_intent_key"]
    assert [event["event_type"] for event in events] == ["skipped_duplicate"]

def test_execute_noop_runtime_decision_allows_gate_replay_while_awaiting_artifact_delta(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root, action_type="run_gate_clearing_batch")
    _write_publication_eval_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
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
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    status.record_publication_supervisor_state(
        {
            "supervisor_phase": "publishability_gate_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": True,
            "current_required_action": "return_to_publishability_gate",
            "deferred_downstream_actions": ["submission_minimal_refresh"],
            "controller_stage_note": "bundle/build/proofing remains downstream of upstream quality repair.",
        }
    )
    chats: list[dict[str, object]] = []

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            chats.append({"quest_id": quest_id, "text": text, "source": source})
            return {"ok": True, "message": {"id": "msg-gate-replay-001"}}

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert len(chats) == 1
    assert "run_gate_clearing_batch" in str(chats[0]["text"])
    assert status.to_dict()["controller_decision_authorization_relay"]["message_id"] == "msg-gate-replay-001"

def test_execute_noop_runtime_decision_allows_quality_repair_while_awaiting_artifact_delta(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root, action_type="run_quality_repair_batch")
    _write_publication_eval_work_unit_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
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
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    chats: list[dict[str, object]] = []

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            chats.append({"quest_id": quest_id, "text": text, "source": source})
            return {"ok": True, "message": {"id": "msg-quality-repair-001"}}

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert len(chats) == 1
    assert "run_quality_repair_batch" in str(chats[0]["text"])
    assert status.to_dict()["controller_decision_authorization_relay"]["message_id"] == "msg-quality-repair-001"


def test_execute_noop_runtime_decision_defers_quality_repair_without_current_work_unit(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root, action_type="run_quality_repair_batch")
    _write_publication_eval_authority(study_root)
    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert authorization_context is not None
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
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("quality repair authorization without a current work unit must wait")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    deferred = status.to_dict()["controller_decision_authorization_deferred"]
    assert deferred["reason"] == "await_artifact_delta_or_gate_replay"

def test_relayed_controller_authorization_marker_includes_lifecycle_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root)
    _write_publication_eval_work_unit_authority(study_root)
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-live-001",
            "pending_user_message_count": 0,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("ordinary controller authorization must be projected to the OPL owner route")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    module._execute_runtime_decision(status=status, context=context)
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    owner_route_ref = status.to_dict()["controller_decision_authorization_owner_route_ref"]

    assert owner_route_ref["queue_owner"] == "one-person-lab"
    assert owner_route_ref["authority_boundary"]["mas_submits_runtime_chat"] is False
    assert owner_route_ref["specificity_targets"][0]["target_kind"] == "claim"
    assert "last_controller_decision_authorization" not in runtime_state


def test_execute_noop_runtime_decision_skips_closed_publication_work_unit_authorization(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    source_eval_id = "publication-eval::001-risk::quest-001::latest"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_gate_clearing_batch",
        work_unit_fingerprint="publication-blockers::authority-sync",
        next_work_unit={
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
            "summary": "Regenerate submission authority signatures, then replay the publication gate.",
        },
    )
    _write_publication_eval_authority(study_root)
    lifecycle_path = study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_eval_id": source_eval_id,
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "status": "done",
                "work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                },
                "unit_statuses": [
                    {"unit_id": "create_submission_minimal_package", "status": "ok"},
                    {"unit_id": "sync_submission_minimal_delivery", "status": "updated"},
                ],
                "gate_replay_status": "clear",
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
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("closed publication work unit authorization must not be relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    payload = status.to_dict()

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert "controller_decision_authorization_relay" not in payload
    assert payload["controller_decision_authorization_closed"]["reason"] == "publication_work_unit_lifecycle_done"
    assert payload["controller_decision_authorization_closed"]["work_unit_id"] == "submission_authority_sync_closure"

def test_execute_noop_runtime_decision_relay_authorization_for_unsettled_authority_lifecycle(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    source_eval_id = "publication-eval::001-risk::quest-001::latest"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_gate_clearing_batch",
        work_unit_fingerprint="publication-blockers::authority-sync",
        next_work_unit={
            "unit_id": "submission_authority_sync_closure",
            "lane": "controller",
            "summary": "Regenerate submission authority signatures, then replay the publication gate.",
        },
    )
    _write_publication_eval_authority(study_root)
    lifecycle_path = study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json"
    lifecycle_path.parent.mkdir(parents=True, exist_ok=True)
    lifecycle_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_eval_id": source_eval_id,
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "status": "done",
                "work_unit": {
                    "unit_id": "submission_authority_sync_closure",
                    "lane": "controller",
                },
                "unit_statuses": [
                    {"unit_id": "create_submission_minimal_package", "status": "ok"},
                    {"unit_id": "sync_submission_minimal_delivery", "status": "skipped_authority_not_settled"},
                ],
                "gate_replay_status": "clear",
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
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("unsettled authority work remains an OPL owner-route projection")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    payload = status.to_dict()

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    assert "controller_decision_authorization_closed" not in payload
    owner_route_ref = payload["controller_decision_authorization_owner_route_ref"]
    assert owner_route_ref["work_unit_id"] == "submission_authority_sync_closure"
    assert owner_route_ref["queue_owner"] == "one-person-lab"
    assert owner_route_ref["authority_boundary"]["mas_submits_runtime_chat"] is False

def test_execute_noop_runtime_decision_refreshes_marker_when_specificity_targets_were_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
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
    stale_marker = {
        "decision_id": authorization_context["decision_id"],
        "route_target": authorization_context["route_target"],
        "route_key_question": authorization_context["route_key_question"],
        "work_unit_id": authorization_context["work_unit_id"],
        "work_unit_fingerprint": authorization_context["work_unit_fingerprint"],
        "control_intent_key": authorization_context["control_intent_key"],
        "delivery_mode": "managed_runtime_chat",
        "message_id": "msg-old-without-targets",
    }
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-live-001",
            "pending_user_message_count": 0,
            "last_controller_decision_authorization": stale_marker,
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("target refresh is exposed through owner-route projection, not runtime chat")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    module._execute_runtime_decision(status=status, context=context)
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    owner_route_ref = status.to_dict()["controller_decision_authorization_owner_route_ref"]
    assert owner_route_ref["specificity_targets"][0]["source_path"].endswith("claim_evidence_map.json")
    assert runtime_state["last_controller_decision_authorization"] == stale_marker

def test_execute_noop_runtime_decision_resets_same_fingerprint_count_for_source_signature_change(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_execution")
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quest-001"
    _write_controller_decision_authorization(study_root)
    _write_publication_eval_authority(study_root, evaluated_signature="source::old")
    old_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert old_context is not None
    _write_publication_eval_authority(study_root, evaluated_signature="source::new")
    new_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)
    assert new_context is not None
    assert old_context["control_intent_key"] != new_context["control_intent_key"]
    _write_runtime_state(
        quest_root,
        {
            "status": "running",
            "active_run_id": "run-live-001",
            "pending_user_message_count": 0,
            "same_fingerprint_auto_turn_count": 8,
            "control_intent_lifecycle": {
                "state": "await_artifact_delta_or_gate_replay",
                "control_intent_key": old_context["control_intent_key"],
            },
        },
    )
    status_payload = _base_status_payload()
    status_payload["study_root"] = str(study_root)
    status_payload["quest_root"] = str(quest_root)
    status = module.StudyRuntimeStatus.from_payload(status_payload)
    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            raise AssertionError("source-signature changes must be projected, not directly relayed")

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    outcome = module._execute_runtime_decision(status=status, context=context)
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))

    assert outcome.binding_last_action is module.StudyRuntimeBindingAction.NOOP
    owner_route_ref = status.to_dict()["controller_decision_authorization_owner_route_ref"]
    assert owner_route_ref["control_intent_key"] == new_context["control_intent_key"]
    assert runtime_state["same_fingerprint_auto_turn_count"] == 8
    assert runtime_state["control_intent_lifecycle"]["control_intent_key"] == old_context["control_intent_key"]
