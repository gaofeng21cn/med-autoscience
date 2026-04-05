from __future__ import annotations

import importlib

import pytest


def test_runtime_escalation_trigger_from_payload_round_trips_minimal_shape() -> None:
    module = importlib.import_module("med_autoscience.runtime_escalation_record")

    payload = {
        "trigger_id": "startup_boundary_not_ready_for_resume",
        "source": "startup_boundary_gate",
    }

    trigger = module.RuntimeEscalationTrigger.from_payload(payload)

    assert trigger == module.RuntimeEscalationTrigger(
        trigger_id="startup_boundary_not_ready_for_resume",
        source="startup_boundary_gate",
    )
    assert trigger.to_dict() == payload


def test_runtime_escalation_record_from_payload_round_trips_minimal_shape() -> None:
    module = importlib.import_module("med_autoscience.runtime_escalation_record")

    payload = {
        "schema_version": 1,
        "record_id": "runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "trigger": {
            "trigger_id": "startup_boundary_not_ready_for_resume",
            "source": "startup_boundary_gate",
        },
        "scope": "quest",
        "severity": "quest",
        "reason": "startup_boundary_not_ready_for_resume",
        "recommended_actions": ["refresh_startup_hydration", "controller_review_required"],
        "evidence_refs": [
            "/tmp/runtime/quests/quest-001/artifacts/reports/startup/hydration_report.json",
            "/tmp/runtime/quests/quest-001/artifacts/reports/startup/hydration_validation_report.json",
        ],
        "runtime_context_refs": {
            "launch_report_path": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"
        },
        "summary_ref": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
        "artifact_path": "/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
    }

    record = module.RuntimeEscalationRecord.from_payload(payload)

    assert record == module.RuntimeEscalationRecord(
        schema_version=1,
        record_id="runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T06:00:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-04-05T06:00:00+00:00",
        trigger=module.RuntimeEscalationTrigger(
            trigger_id="startup_boundary_not_ready_for_resume",
            source="startup_boundary_gate",
        ),
        scope="quest",
        severity="quest",
        reason="startup_boundary_not_ready_for_resume",
        recommended_actions=("refresh_startup_hydration", "controller_review_required"),
        evidence_refs=(
            "/tmp/runtime/quests/quest-001/artifacts/reports/startup/hydration_report.json",
            "/tmp/runtime/quests/quest-001/artifacts/reports/startup/hydration_validation_report.json",
        ),
        runtime_context_refs={
            "launch_report_path": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"
        },
        summary_ref="/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
        artifact_path="/tmp/runtime/quests/quest-001/artifacts/reports/escalation/runtime_escalation_record.json",
    )
    assert record.to_dict() == payload
    assert record.ref() == module.RuntimeEscalationRecordRef(
        record_id=payload["record_id"],
        artifact_path=payload["artifact_path"],
        summary_ref=payload["summary_ref"],
    )
    assert record.ref().to_dict() == {
        "record_id": payload["record_id"],
        "artifact_path": payload["artifact_path"],
        "summary_ref": payload["summary_ref"],
    }


def test_runtime_escalation_record_requires_summary_ref() -> None:
    module = importlib.import_module("med_autoscience.runtime_escalation_record")

    with pytest.raises(ValueError, match="runtime escalation record payload missing summary_ref"):
        module.RuntimeEscalationRecord.from_payload(
            {
                "schema_version": 1,
                "record_id": "runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T06:00:00+00:00",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": "2026-04-05T06:00:00+00:00",
                "trigger": {
                    "trigger_id": "startup_boundary_not_ready_for_resume",
                    "source": "startup_boundary_gate",
                },
                "scope": "quest",
                "severity": "quest",
                "reason": "startup_boundary_not_ready_for_resume",
                "recommended_actions": ["refresh_startup_hydration", "controller_review_required"],
                "runtime_context_refs": {"launch_report_path": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json"},
            }
        )


def test_runtime_escalation_record_requires_recommended_actions() -> None:
    module = importlib.import_module("med_autoscience.runtime_escalation_record")

    with pytest.raises(ValueError, match="runtime escalation record payload missing recommended_actions"):
        module.RuntimeEscalationRecord.from_payload(
            {
                "schema_version": 1,
                "record_id": "runtime-escalation::001-risk::quest-001::startup_boundary_not_ready_for_resume::2026-04-05T06:00:00+00:00",
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "emitted_at": "2026-04-05T06:00:00+00:00",
                "trigger": {
                    "trigger_id": "startup_boundary_not_ready_for_resume",
                    "source": "startup_boundary_gate",
                },
                "scope": "quest",
                "severity": "quest",
                "reason": "startup_boundary_not_ready_for_resume",
                "summary_ref": "/tmp/workspace/studies/001-risk/artifacts/runtime/last_launch_report.json",
            }
        )
