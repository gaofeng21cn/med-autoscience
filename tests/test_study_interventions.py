from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def _module():
    return importlib.import_module("med_autoscience.controllers.study_interventions")


def test_append_only_intervention_events_are_file_primary_and_truth_event_ready(tmp_path: Path) -> None:
    module = _module()
    study_root = tmp_path / "studies" / "003-endocrine"

    event = module.append_intervention_event(
        study_root=study_root,
        study_id="003-endocrine",
        intent="new_plan",
        payload={
            "summary": "user supplied a reviewer-revision plan",
            "current_required_action": "resume_same_study_line",
            "reactivation_policy": {"same_study_line": True},
        },
        recorded_at="2026-05-06T01:00:00+00:00",
        actor="user",
        source="codex",
        agent_handoff={
            "next_agent": "mas_controller",
            "memory": "resume with supplied revision plan",
        },
    )

    path = module.intervention_events_path(study_root=study_root)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    truth_event_input = module.build_truth_event_input(event)

    assert path == study_root / "artifacts" / "interventions" / "events.jsonl"
    assert rows == [event]
    assert event["surface"] == "study_intervention_event"
    assert event["storage_policy"] == {"primary_store": "file", "sqlite_role": "index_only"}
    assert event["intent"] == "new_plan"
    assert event["agent_handoff"]["memory"] == "resume with supplied revision plan"
    assert truth_event_input == {
        "study_id": "003-endocrine",
        "event_type": "task_intake",
        "payload": {
            "intervention_event_id": event["event_id"],
            "intervention_intent": "new_plan",
            "actor": "user",
            "source": "codex",
            "summary": "user supplied a reviewer-revision plan",
            "current_required_action": "resume_same_study_line",
            "reactivation_policy": {"same_study_line": True},
            "agent_handoff": {
                "next_agent": "mas_controller",
                "memory": "resume with supplied revision plan",
            },
        },
        "recorded_at": "2026-05-06T01:00:00+00:00",
        "source_signature": f"intervention::{event['event_id']}",
    }
    assert not (study_root / "artifacts" / "truth" / "events.jsonl").exists()


def test_intervention_event_log_preserves_order_for_user_decision_submit_info_and_abandon(
    tmp_path: Path,
) -> None:
    module = _module()
    study_root = tmp_path / "studies" / "004-dpcc"

    decision = module.append_intervention_event(
        study_root=study_root,
        study_id="004-dpcc",
        intent="user_decision",
        payload={"decision": "continue_watch", "summary": "user chose to keep monitoring"},
        recorded_at="2026-05-06T01:00:00+00:00",
    )
    submit_info = module.append_intervention_event(
        study_root=study_root,
        study_id="004-dpcc",
        intent="submit_info",
        payload={"submission_info": {"funding": "none"}, "summary": "funding metadata supplied"},
        recorded_at="2026-05-06T01:01:00+00:00",
    )
    abandon = module.append_intervention_event(
        study_root=study_root,
        study_id="004-dpcc",
        intent="abandon",
        payload={"summary": "user abandoned this study line"},
        recorded_at="2026-05-06T01:02:00+00:00",
    )

    events = module.read_intervention_events(study_root=study_root)
    truth_inputs = [module.build_truth_event_input(event) for event in events]

    assert events == [decision, submit_info, abandon]
    assert [event["sequence"] for event in events] == [1, 2, 3]
    assert [event["intent"] for event in events] == ["user_decision", "submit_info", "abandon"]
    assert [item["event_type"] for item in truth_inputs] == ["human_gate", "human_gate", "human_gate"]
    assert truth_inputs[1]["payload"]["submission_info"] == {"funding": "none"}
    assert truth_inputs[2]["payload"]["current_required_action"] == "abandon_study_line"


def test_unknown_intervention_intent_is_rejected_without_writing(tmp_path: Path) -> None:
    module = _module()
    study_root = tmp_path / "studies" / "bad-intent"

    with pytest.raises(ValueError, match="unknown study intervention intent"):
        module.append_intervention_event(
            study_root=study_root,
            study_id="bad-intent",
            intent="maybe_later",
            payload={"summary": "ambiguous user message"},
            recorded_at="2026-05-06T01:00:00+00:00",
        )

    assert not module.intervention_events_path(study_root=study_root).exists()
