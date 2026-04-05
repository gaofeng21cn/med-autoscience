from __future__ import annotations

import importlib

import pytest


def test_runtime_escalation_record_from_payload_round_trips_minimal_shape() -> None:
    module = importlib.import_module("med_autoscience.runtime_escalation_record")

    payload = {
        "recorded_at": "2026-04-05T06:00:00+00:00",
        "quest_root": "/tmp/runtime/quests/001-risk",
        "reason": "startup_boundary_not_ready_for_resume",
        "summary_ref": "paper/review/runtime_escalation_summary.md",
        "record_path": "/tmp/runtime/quests/001-risk/artifacts/reports/runtime/escalation_record.json",
    }

    record = module.RuntimeEscalationRecord.from_payload(payload)

    assert record == module.RuntimeEscalationRecord(
        recorded_at="2026-04-05T06:00:00+00:00",
        quest_root="/tmp/runtime/quests/001-risk",
        reason="startup_boundary_not_ready_for_resume",
        summary_ref="paper/review/runtime_escalation_summary.md",
        record_path="/tmp/runtime/quests/001-risk/artifacts/reports/runtime/escalation_record.json",
    )
    assert record.to_dict() == payload


def test_runtime_escalation_record_requires_summary_ref_to_remain_separate_from_full_record() -> None:
    module = importlib.import_module("med_autoscience.runtime_escalation_record")

    with pytest.raises(ValueError, match="runtime escalation record payload missing summary_ref"):
        module.RuntimeEscalationRecord.from_payload(
            {
                "recorded_at": "2026-04-05T06:00:00+00:00",
                "quest_root": "/tmp/runtime/quests/001-risk",
                "reason": "startup_boundary_not_ready_for_resume",
            }
        )
