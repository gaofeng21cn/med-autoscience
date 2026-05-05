from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace


def _base_status_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": "/tmp/workspace/studies/001-risk",
        "entry_mode": "full_research",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "quest_id": "quest-001",
        "quest_root": "/tmp/runtime/quests/quest-001",
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": "/tmp/workspace/studies/001-risk/runtime_binding.yaml",
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "noop",
        "reason": "quest_already_running",
    }


def _write_controller_decision_authorization(
    study_root: Path,
    *,
    action_type: str = "ensure_study_runtime",
    next_work_unit: dict[str, object] | None = None,
    blocking_work_units: list[dict[str, object]] | None = None,
    work_unit_fingerprint: str | None = None,
) -> None:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    decision_path.parent.mkdir(parents=True, exist_ok=True)
    decision_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "decision_id": "decision-analysis-001",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": "2026-04-25T06:20:00+00:00",
                "decision_type": "bounded_analysis",
                "charter_ref": {
                    "charter_id": "charter::001-risk::v1",
                    "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                },
                "runtime_escalation_ref": {
                    "record_id": "runtime-escalation::001-risk::quest-001::controller-gap",
                    "artifact_path": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                    "summary_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
                },
                "publication_eval_ref": {
                    "eval_id": "publication-eval::001-risk::quest-001::latest",
                    "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                },
                "requires_human_confirmation": False,
                "controller_actions": [{"action_type": action_type, "payload_ref": str(decision_path)}],
                "reason": "Route bounded revision analysis back into the active runtime.",
                "route_target": "analysis-campaign",
                "route_key_question": (
                    "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
                ),
                "route_rationale": "The revision line needs a bounded quality pass under the same manuscript route.",
                **({"work_unit_fingerprint": work_unit_fingerprint} if work_unit_fingerprint else {}),
                **({"next_work_unit": next_work_unit} if next_work_unit else {}),
                **({"blocking_work_units": blocking_work_units} if blocking_work_units else {}),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_eval_authority(
    study_root: Path,
    *,
    evaluated_signature: str = "source::evaluated",
) -> None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::quest-001::latest",
                "emitted_at": "2026-04-25T06:21:00+00:00",
                "gate_fingerprint": "publication-gate::stable",
                "blockers": ["claim_evidence_consistency_failed"],
                "current_required_action": "return_to_publishability_gate",
                "submission_minimal_evaluated_source_signature": evaluated_signature,
                "submission_minimal_authority_source_signature": "source::authority",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_publication_eval_work_unit_authority(study_root: Path) -> None:
    path = study_root / "artifacts" / "publication_eval" / "latest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::quest-001::latest",
                "emitted_at": "2026-04-25T06:21:00+00:00",
                "recommended_actions": [
                    {
                        "action_type": "bounded_analysis",
                        "route_target": "analysis-campaign",
                        "route_key_question": "broad reviewer revision checklist",
                        "route_rationale": "Gate requires controller-owned analysis repair.",
                        "work_unit_fingerprint": "publication-blockers::claim-story-figure",
                        "next_work_unit": {
                            "unit_id": "analysis_claim_evidence_repair",
                            "lane": "analysis-campaign",
                            "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                        },
                        "blocking_work_units": [
                            {
                                "unit_id": "analysis_claim_evidence_repair",
                                "lane": "analysis-campaign",
                                "summary": "Repair claim-evidence, story, figure, and results traceability blockers.",
                            },
                            {
                                "unit_id": "submission_minimal_refresh",
                                "lane": "finalize",
                                "summary": "Refresh the stale submission package after gate clearance.",
                            },
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_runtime_state(quest_root: Path, payload: dict[str, object]) -> None:
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_controller_authorization_prefers_publication_work_unit_over_stale_route_text(tmp_path: Path) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(study_root)
    _write_publication_eval_work_unit_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["work_unit_id"] == "analysis_claim_evidence_repair"
    assert authorization_context["work_unit_fingerprint"] == "publication-blockers::claim-story-figure"
    assert authorization_context["route_target"] == "analysis-campaign"
    assert authorization_context["route_key_question"].startswith("analysis_claim_evidence_repair:")
    assert authorization_context["source_route_key_question"] == (
        "revision checklist mapping each user comment to manuscript/table/figure/reference changes"
    )
    assert authorization_context["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert authorization_context["blocking_work_units"][1]["unit_id"] == "submission_minimal_refresh"
    assert authorization_context["control_intent_identity"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert (
        authorization_context["control_intent_identity"]["blocker_authority_fingerprint"]
        == "publication-blockers::claim-story-figure"
    )


def test_controller_authorization_prefers_current_decision_work_unit_over_stale_publication_eval(
    tmp_path: Path,
) -> None:
    auth_module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_execution_parts.controller_authorization"
    )
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision_authorization(
        study_root,
        action_type="run_gate_clearing_batch",
        work_unit_fingerprint="publication-blockers::current",
        next_work_unit={
            "unit_id": "submission_minimal_refresh",
            "lane": "finalize",
            "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
        },
        blocking_work_units=[
            {
                "unit_id": "manuscript_story_repair",
                "lane": "write",
                "summary": "Repair the paper story around the current evidence and claim boundary.",
            },
            {
                "unit_id": "submission_minimal_refresh",
                "lane": "finalize",
                "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
            },
        ],
    )
    _write_publication_eval_work_unit_authority(study_root)

    authorization_context = auth_module._load_controller_decision_authorization_context(study_root=study_root)

    assert authorization_context is not None
    assert authorization_context["work_unit_id"] == "submission_minimal_refresh"
    assert authorization_context["work_unit_fingerprint"] == "publication-blockers::current"
    assert authorization_context["route_target"] == "finalize"
    assert authorization_context["next_work_unit"]["unit_id"] == "submission_minimal_refresh"
    assert authorization_context["blocking_work_units"][0]["unit_id"] == "manuscript_story_repair"
    assert authorization_context["control_intent_identity"]["work_unit_id"] == "submission_minimal_refresh"


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
            return {"ok": True, "message": {"id": "msg-auth-lifecycle-001"}}

    context = SimpleNamespace(
        study_root=study_root,
        quest_root=quest_root,
        runtime_root=tmp_path / "runtime",
        runtime_backend=FakeBackend(),
        source="medautosci-test",
    )

    module._execute_runtime_decision(status=status, context=context)
    runtime_state = json.loads((quest_root / ".ds" / "runtime_state.json").read_text(encoding="utf-8"))
    marker = runtime_state["last_controller_decision_authorization"]

    assert marker["controller_work_unit_lifecycle"] == {
        "lifecycle_state": "new",
        "latest_event_type": None,
        "delivery_blocked": False,
        "block_reason": None,
        "terminal_consumed": False,
    }


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
    chats: list[dict[str, object]] = []

    class FakeBackend:
        def chat_quest(self, *, runtime_root: Path, quest_id: str, text: str, source: str) -> dict[str, object]:
            chats.append({"quest_id": quest_id, "text": text, "source": source})
            return {"ok": True, "message": {"id": "msg-auth-reset-001"}}

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
    assert len(chats) == 1
    assert runtime_state["same_fingerprint_auto_turn_count"] == 0
    assert "control_intent_lifecycle" not in runtime_state
    assert runtime_state["last_controller_decision_authorization"]["control_intent_key"] == new_context["control_intent_key"]
