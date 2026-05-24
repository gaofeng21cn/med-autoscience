from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_platform_incident_learning_loop_records_only_allowed_platform_events() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_incidents")

    payload = module.build_platform_incident_learning_loop(
        {
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "platform_incident_types": [
                "no-live",
                "stalled",
                "status drift",
                "wrong milestone claim",
                "quality reopen",
                "publication gate failure",
                "runtime recovery failure",
                "surface ownership drift",
            ],
            "bottlenecks": [
                {"bottleneck_id": "publication_gate_blocked", "severity": "high"},
                {"bottleneck_id": "non_actionable_gate", "severity": "high"},
            ],
        }
    )

    assert payload["surface"] == "autonomy_incident_learning_loop"
    assert payload["incident_scope"] == "platform_only"
    assert payload["gate_relaxation_allowed"] is False
    assert [incident["incident_type"] for incident in payload["incidents"]] == [
        "no_live",
        "stalled",
        "status_drift",
        "wrong_milestone_claim",
        "quality_reopen",
        "publication_gate_failure",
        "runtime_recovery_failure",
        "surface_ownership_drift",
    ]
    assert payload["prevention_action_contract"] == {
        "must_be_one_of": [
            "guard",
            "test",
            "contract",
                "runbook",
                "runtime_taxonomy",
                "strangler_rule",
                "truth_kernel_rule",
            ],
        "prose_only_note_allowed": False,
        "gate_relaxation_allowed": False,
        "allowed_targets": (
            "guard",
            "test",
            "contract",
            "runbook",
            "runtime_taxonomy",
            "strangler_rule",
            "truth_kernel_rule",
        ),
    }
    for incident in payload["incidents"]:
        assert incident["scope"] == "platform"
        assert incident["gate_relaxation_allowed"] is False
        assert incident["prevention_action"]["action_type"] in payload["allowed_prevention_action_types"]
        assert incident["prevention_action"]["gate_relaxation_allowed"] is False


def test_platform_incident_learning_loop_derives_runtime_events_from_state_surface() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_incidents")

    payload = module.build_platform_incident_learning_loop(
        {
            "study_id": "003-dpcc",
            "autonomy_state_machine": {"current_state": "no_live"},
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "authority": "observability_only",
                "runtime_health": {
                    "health_status": "escalated",
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                },
            },
        }
    )

    assert [incident["incident_type"] for incident in payload["incidents"]] == [
        "no_live",
        "runtime_recovery_failure",
    ]
    assert payload["incidents"][0]["prevention_action"]["action_type"] == "runtime_taxonomy"
    assert payload["incidents"][1]["prevention_action"]["action_type"] == "runbook"


def test_platform_incident_learning_loop_derives_publication_gate_failures() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_incidents")

    payload = module.build_platform_incident_learning_loop(
        {
            "study_id": "003-dpcc",
            "publication_eval": {"gate_status": "blocked"},
            "publication_gate": {"verdict": "blocked"},
        }
    )

    assert [incident["incident_type"] for incident in payload["incidents"]] == [
        "publication_gate_failure",
    ]
    assert payload["incidents"][0]["prevention_action"] == {
        "action_type": "contract",
        "controller_surface": "publication_eval/latest.json",
        "summary": "Convert publication gate failures into concrete route-back or repair contracts before any readiness claim.",
        "gate_relaxation_allowed": False,
    }


def test_write_incident_record_persists_prevention_action(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_incidents")
    loop = module.build_platform_incident_learning_loop(
        {
            "study_id": "003-dpcc",
            "platform_incident_types": ["surface ownership drift"],
        }
    )

    written = module.write_incident_record(
        study_root=tmp_path / "studies" / "003-dpcc",
        candidate=loop["incidents"][0],
        recorded_at="2026-04-26T00:00:00+00:00",
    )

    payload = json.loads(written.read_text(encoding="utf-8"))
    assert payload["incident_type"] == "surface_ownership_drift"
    assert payload["prevention_action"]["action_type"] == "strangler_rule"
    assert payload["gate_relaxation_allowed"] is False


def test_truth_authority_incident_requires_reducer_fixture_and_runbook_artifacts() -> None:
    module = importlib.import_module("med_autoscience.controllers.autonomy_incidents")

    payload = module.build_platform_incident_learning_loop(
        {
            "study_id": "003-dpcc",
            "platform_incident_types": ["truth authority drift"],
        }
    )

    assert payload["incidents"][0]["incident_type"] == "truth_authority_drift"
    assert payload["incidents"][0]["prevention_action"] == {
        "action_type": "truth_kernel_rule",
        "controller_surface": "artifacts/truth/latest.json",
        "summary": "Convert the drift into a StudyTruthKernel dominance rule, a golden fixture, and a runbook entry before retrying.",
        "required_artifacts": ["reducer_rule", "fixture_test", "runbook_entry"],
        "gate_relaxation_allowed": False,
    }
