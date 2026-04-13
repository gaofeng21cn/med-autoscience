from __future__ import annotations

import importlib

import pytest


MODULE_NAME = "med_autoscience.study_decision_record"


def _load_module() -> object:
    return importlib.import_module(MODULE_NAME)


def _minimal_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "decision_id": "study-decision::001-risk::quest-001::continue_same_line::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "decision_type": "continue_same_line",
        "charter_ref": {
            "charter_id": "charter::001-risk::v1",
            "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
        },
        "runtime_escalation_ref": {
            "record_id": "runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T05:55:00+00:00",
            "artifact_path": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
            "summary_ref": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
        },
        "publication_eval_ref": {
            "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
        },
        "requires_human_confirmation": False,
        "controller_actions": [
            {
                "action_type": "ensure_study_runtime",
                "payload_ref": "/tmp/workspace/studies/001-risk/artifacts/controller_decisions/latest.json",
            }
        ],
        "reason": "Publication eval keeps the study on the same line.",
    }


def test_study_decision_record_from_payload_round_trips_minimal_shape() -> None:
    module = _load_module()
    payload = _minimal_payload()

    record = module.StudyDecisionRecord.from_payload(payload)

    assert record == module.StudyDecisionRecord(
        schema_version=1,
        decision_id="study-decision::001-risk::quest-001::continue_same_line::2026-04-05T06:00:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T06:00:00+00:00",
        decision_type="continue_same_line",
        charter_ref=module.StudyDecisionCharterRef(
            charter_id="charter::001-risk::v1",
            artifact_path="/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
        ),
        runtime_escalation_ref=module.RuntimeEscalationRecordRef(
            record_id="runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T05:55:00+00:00",
            artifact_path="/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
            summary_ref="/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
        ),
        publication_eval_ref=module.StudyDecisionPublicationEvalRef(
            eval_id="publication-eval::001-risk::quest-001::2026-04-05T05:58:00+00:00",
            artifact_path="/tmp/workspace/studies/001-risk/artifacts/publication_eval/latest.json",
        ),
        requires_human_confirmation=False,
        controller_actions=(
            module.StudyDecisionControllerAction(
                action_type="ensure_study_runtime",
                payload_ref="/tmp/workspace/studies/001-risk/artifacts/controller_decisions/latest.json",
            ),
        ),
        reason="Publication eval keeps the study on the same line.",
    )
    assert record.to_dict() == payload


def test_study_decision_record_rejects_missing_runtime_escalation_ref() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload.pop("runtime_escalation_ref")

    with pytest.raises(ValueError, match="study decision record payload missing runtime_escalation_ref"):
        module.StudyDecisionRecord.from_payload(payload)


def test_study_decision_record_rejects_full_payload_backflow_in_charter_ref() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["charter_ref"] = {
        "charter_id": "charter::001-risk::v1",
        "artifact_path": "/tmp/workspace/studies/001-risk/artifacts/controller/study_charter.json",
        "publication_objective": "should-not-backflow",
    }

    with pytest.raises(ValueError, match="study decision charter ref payload contains unknown fields: publication_objective"):
        module.StudyDecisionRecord.from_payload(payload)


def test_study_decision_record_requires_non_empty_controller_actions() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["controller_actions"] = []

    with pytest.raises(ValueError, match="study decision record controller_actions must not be empty"):
        module.StudyDecisionRecord.from_payload(payload)


def test_study_decision_record_rejects_unsupported_rerun_decision_type() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["decision_type"] = "rerun_same_line"

    with pytest.raises(ValueError, match="unknown study decision type"):
        module.StudyDecisionRecord.from_payload(payload)


def test_study_decision_record_rejects_unsupported_stop_after_current_step_action() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["controller_actions"] = [
        {
            "action_type": "stop_after_current_step",
            "payload_ref": "/tmp/workspace/studies/001-risk/artifacts/controller_decisions/latest.json",
        }
    ]

    with pytest.raises(ValueError, match="unknown study decision controller action"):
        module.StudyDecisionRecord.from_payload(payload)


def test_study_decision_record_accepts_family_orchestration_companion_fields() -> None:
    module = _load_module()
    payload = _minimal_payload()
    payload["family_event_envelope"] = {
        "version": "family-event-envelope.v1",
        "envelope_id": "evt-001",
    }
    payload["family_checkpoint_lineage"] = {
        "version": "family-checkpoint-lineage.v1",
        "lineage_id": "lineage-001",
    }
    payload["family_human_gates"] = [
        {
            "version": "family-human-gate.v1",
            "gate_id": "gate-001",
            "status": "requested",
        }
    ]

    record = module.StudyDecisionRecord.from_payload(payload)

    assert record.to_dict()["family_event_envelope"]["envelope_id"] == "evt-001"
    assert record.to_dict()["family_checkpoint_lineage"]["lineage_id"] == "lineage-001"
    assert record.to_dict()["family_human_gates"] == [
        {
            "version": "family-human-gate.v1",
            "gate_id": "gate-001",
            "status": "requested",
        }
    ]
