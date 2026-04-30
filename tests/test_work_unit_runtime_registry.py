from __future__ import annotations

import importlib


def _valid_payload(tmp_path):
    workspace = tmp_path / "runtime" / "workspaces" / "study-001"
    cwd = workspace / "attempt"
    cwd.mkdir(parents=True, exist_ok=True)
    return {
        "program_id": "program-001",
        "study_id": "study-001",
        "quest_id": "quest-001",
        "active_run_id": "run-001",
        "work_unit_id": "wu-001",
        "route_id": "analysis-campaign",
        "attempt_state": "running",
        "attempt_count": 1,
        "run_attempt_phase": "bounded_analysis",
        "failure_reason": "",
        "workspace_root": str(workspace),
        "cwd": str(cwd),
    }


def test_work_unit_attempt_record_validates_runtime_identity_and_boundary(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.work_unit_runtime_registry")

    record = module.build_work_unit_attempt_record(_valid_payload(tmp_path))
    validation = module.validate_work_unit_attempt_record(record)

    assert record["surface"] == "work_unit_runtime_attempt_record"
    assert record["attempt_state"] == "running"
    assert record["attempt_count"] == 1
    assert record["workspace_boundary"]["inside_root"] is True
    assert record["retry_policy"]["research_authority"] is False
    assert record["authority_boundary"] == {
        "orchestration_record_only": True,
        "can_create_study_truth": False,
        "can_override_publication_eval": False,
        "requires_controller_decision_for_release": False,
    }
    assert validation["ok"] is True


def test_work_unit_attempt_record_fails_closed_on_workspace_escape(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.work_unit_runtime_registry")
    payload = _valid_payload(tmp_path)
    payload["cwd"] = str(tmp_path / "other-study" / "attempt")

    record = module.build_work_unit_attempt_record(payload)
    validation = module.validate_work_unit_attempt_record(record)

    assert record["failure_reason"] == "workspace_boundary_violation"
    assert record["workspace_boundary"]["fail_closed"] is True
    assert validation["ok"] is False
    assert {"code": "workspace_boundary_violation"} in validation["issues"]


def test_work_unit_attempt_registry_summary_is_observability_only(tmp_path) -> None:
    module = importlib.import_module("med_autoscience.controllers.work_unit_runtime_registry")
    running = module.build_work_unit_attempt_record(_valid_payload(tmp_path))
    retry_payload = _valid_payload(tmp_path)
    retry_payload.update(
        {
            "work_unit_id": "wu-002",
            "attempt_state": "retry_queued",
            "attempt_count": 2,
            "failure_reason": "runtime_stalled",
            "backoff_until": "2026-04-30T12:00:00+00:00",
            "retry_budget_remaining": 1,
        }
    )
    retry = module.build_work_unit_attempt_record(retry_payload)

    summary = module.summarize_work_unit_attempts([running, retry])

    assert summary["attempt_state_counts"]["running"] == 1
    assert summary["attempt_state_counts"]["retry_queued"] == 1
    assert summary["retry_queue"] == [
        {
            "work_unit_id": "wu-002",
            "attempt_count": 2,
            "failure_reason": "runtime_stalled",
            "backoff_until": "2026-04-30T12:00:00+00:00",
            "retry_budget_remaining": 1,
        }
    ]
    assert summary["observability_only"] is True
    assert summary["study_truth_authority"] is False
    assert summary["publication_authority"] is False
