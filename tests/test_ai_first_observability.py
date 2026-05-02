from __future__ import annotations

import importlib
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def test_ai_first_observability_summary_exposes_quality_runtime_and_artifact_signals() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")

    summary = module.build_ai_first_observability_summary(
        drift_audit={"status": "pass", "summary": {"fail_count": 0, "skipped_count": 0}},
        runtime_snapshot={"canonical_runtime_action": "recover_runtime", "retry_budget_remaining": 1},
        quality_snapshot={
            "ai_reviewer_trace_complete": False,
            "route_back_count": 2,
            "publication_eval_fresh": False,
        },
        artifact_snapshot={"stale_artifact_count": 3, "current_package_from_canonical_source": True},
    )

    assert summary["surface"] == "ai_first_observability_summary"
    assert summary["operator_view"]["ai_first_drift_status"] == "pass"
    assert summary["operator_view"]["runtime_action"] == "recover_runtime"
    assert summary["operator_view"]["ai_reviewer_trace_complete"] is False
    assert summary["operator_view"]["route_back_count"] == 2
    assert summary["operator_view"]["stale_artifact_count"] == 3
    assert summary["user_view"] == {
        "status": "attention_required",
        "reason": (
            "AI reviewer trace incomplete; publication eval stale; artifact refresh pending; "
            "runtime recovery in progress"
        ),
        "next_action": "return_to_ai_reviewer_or_runtime_recovery",
    }


def test_ai_first_observability_summary_never_exposes_low_level_logs_to_user() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")

    summary = module.build_ai_first_observability_summary(
        drift_audit={"status": "pass", "summary": {"fail_count": 0}},
        runtime_snapshot={"canonical_runtime_action": "continue", "raw_terminal_log": "secret"},
        quality_snapshot={"ai_reviewer_trace_complete": True, "route_back_count": 0},
        artifact_snapshot={"stale_artifact_count": 0},
    )

    assert "raw_terminal_log" in summary["operator_view"]["redacted_fields"]
    assert "raw_terminal_log" not in str(summary["user_view"])
    assert summary["user_view"]["status"] == "on_track"


def test_doctor_observability_summary_exposes_contract_without_runtime_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")

    summary = module.build_doctor_ai_first_observability_summary(
        drift_audit={"status": "fail", "summary": {"fail_count": 1}}
    )

    assert summary["surface"] == "ai_first_observability_summary"
    assert summary["operator_view"]["ai_first_drift_status"] == "fail"
    assert summary["operator_view"]["runtime_action"] == "unknown"
    assert summary["operator_view"]["ai_reviewer_trace_complete"] is None
    assert summary["user_view"] == {
        "status": "informational",
        "reason": "doctor report exposes the observability contract without study-specific runtime traces",
        "next_action": "inspect_study_runtime_status_or_runtime_watch",
    }
    assert summary["authority"] == {
        "observability_can_authorize_quality": False,
        "observability_can_mutate_runtime": False,
        "user_view_excludes_low_level_logs": True,
    }
    assert summary["contract"]["authority"] == "observability_only"


def test_doctor_report_renders_ai_first_observability_contract(tmp_path: Path) -> None:
    doctor = importlib.import_module("med_autoscience.doctor")
    workspace_tests = importlib.import_module("tests.test_workspace_contracts")
    profile = workspace_tests.make_profile(tmp_path)

    rendered = doctor.render_doctor_report(doctor.build_doctor_report(profile))

    assert "ai_first_observability: " in rendered
    assert '"surface": "ai_first_observability_summary"' in rendered
    assert '"observability_can_authorize_quality": false' in rendered
    assert '"authority": "observability_only"' in rendered
