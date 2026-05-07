from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def test_ai_first_observability_snapshots_read_real_study_runtime_artifacts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")
    study_root = tmp_path / "studies" / "001-risk"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "reviewer_operating_system": {"trace_id": "reviewer-os-001"},
            "recommended_actions": [
                {"action_type": "route_back_same_line", "route_target": "medical_prose_review"}
            ],
            "gaps": [{"severity": "must_fix", "summary": "Claim-evidence map needs tightening."}],
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "health" / "latest.json",
        {"canonical_runtime_action": "recover_runtime", "retry_budget_remaining": 2},
    )
    _write_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "source_signature": "sig-001",
            "authority_source_signature": "sig-001",
            "delivery_source_signature": "sig-001",
            "surface_roles": {
                "controller_authorized_package_source_root": str(study_root / "paper" / "submission_minimal")
            },
            "blocking_artifact_refs": [],
        },
    )

    snapshots = module.build_ai_first_observability_snapshots_from_study_root(study_root=study_root)

    assert snapshots["surface"] == "ai_first_runtime_observability_snapshots"
    assert snapshots["runtime_snapshot"] == {
        "canonical_runtime_action": "recover_runtime",
        "retry_budget_remaining": 2,
    }
    assert snapshots["quality_snapshot"]["ai_reviewer_trace_complete"] is True
    assert snapshots["quality_snapshot"]["publication_eval_fresh"] is True
    assert snapshots["quality_snapshot"]["route_back_count"] == 1
    assert snapshots["quality_snapshot"]["route_back_target"] == "medical_prose_review"
    assert snapshots["quality_snapshot"]["quality_toil_items"] == ["Claim-evidence map needs tightening."]
    assert snapshots["artifact_snapshot"] == {
        "stale_artifact_count": 0,
        "current_package_from_canonical_source": True,
    }


def test_ai_first_observability_snapshots_fail_closed_without_ai_reviewer_trace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")
    study_root = tmp_path / "studies" / "001-risk"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            "recommended_actions": [],
            "gaps": [],
        },
    )

    snapshots = module.build_ai_first_observability_snapshots_from_study_root(study_root=study_root)

    assert snapshots["quality_snapshot"]["ai_reviewer_trace_complete"] is False
    assert snapshots["quality_snapshot"]["publication_eval_fresh"] is True
    assert "ai_reviewer_trace_missing" in snapshots["quality_snapshot"]["quality_toil_items"]
    assert snapshots["artifact_snapshot"] == {
        "stale_artifact_count": 1,
        "current_package_from_canonical_source": False,
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


def test_operations_dashboard_summary_projects_shared_user_and_maintainer_read_model() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")

    summary = module.build_ai_first_operations_dashboard_summary(
        drift_audit={"status": "pass", "summary": {"fail_count": 0}},
        progress_snapshot={
            "current_stage": "revision_required",
            "current_blockers": ["AI reviewer trace incomplete"],
            "next_system_action": "return_to_ai_reviewer",
            "autonomy_contract": {"restore_point": {"human_gate_required": True}},
        },
        runtime_snapshot={"canonical_runtime_action": "continue_current_route", "retry_budget_remaining": 3},
        quality_snapshot={
            "ai_reviewer_trace_complete": False,
            "route_back_count": 2,
            "route_back_target": "ai_reviewer",
            "publication_eval_fresh": False,
            "gate_cache_fresh": True,
            "quality_toil_items": ["rerun reviewer handoff check"],
        },
        artifact_snapshot={"stale_artifact_count": 1, "current_package_from_canonical_source": True},
    )

    assert summary["surface"] == "ai_first_operations_dashboard_summary"
    assert summary["read_model"] == "ai_first_operations_dashboard_read_model"
    assert summary["contract"]["shared_read_model_consumers"] == [
        "product_entry_status",
        "workspace_cockpit",
        "study_progress",
    ]
    assert summary["user_view"] == {
        "current_stage": "revision_required",
        "blockers": ["AI reviewer trace incomplete"],
        "next_step": "return_to_ai_reviewer",
        "human_review_required": True,
    }
    assert summary["maintainer_view"]["ai_reviewer_trace"]["complete"] is False
    assert summary["maintainer_view"]["cache_freshness"] == {
        "publication_eval_fresh": False,
        "gate_cache_fresh": True,
    }
    assert summary["maintainer_view"]["route_back"] == {
        "count": 2,
        "target": "ai_reviewer",
    }
    assert summary["maintainer_view"]["artifact_stale"] == {
        "stale_artifact_count": 1,
        "current_package_from_canonical_source": True,
    }
    assert summary["maintainer_view"]["quality_toil"] == {
        "toil_items": ["rerun reviewer handoff check"],
        "toil_count": 1,
    }
    assert summary["authority"]["observability_can_authorize_quality"] is False
    assert summary["authority"]["observability_can_mutate_runtime"] is False


def test_operations_dashboard_summary_keeps_user_view_free_of_logs_prompts_and_tokens() -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_observability")

    summary = module.build_ai_first_operations_dashboard_summary(
        drift_audit={"status": "pass", "summary": {"fail_count": 0}},
        progress_snapshot={
            "current_stage": "bundle_stage_ready",
            "current_blockers": [],
            "next_system_action": "continue_bundle_stage",
        },
        runtime_snapshot={
            "canonical_runtime_action": "continue_bundle_stage",
            "raw_terminal_log": "internal log",
            "token_stream": "token details",
        },
        quality_snapshot={"ai_reviewer_trace_complete": True, "full_prompt": "internal prompt"},
        artifact_snapshot={"stale_artifact_count": 0, "secret": "internal secret"},
    )

    assert summary["user_view"] == {
        "current_stage": "bundle_stage_ready",
        "blockers": [],
        "next_step": "continue_bundle_stage",
        "human_review_required": False,
    }
    assert "raw_terminal_log" not in str(summary["user_view"])
    assert "full_prompt" not in str(summary["user_view"])
    assert "token_stream" not in str(summary["user_view"])
    assert sorted(summary["maintainer_view"]["redacted_fields"]) == [
        "full_prompt",
        "raw_terminal_log",
        "secret",
        "token_stream",
    ]


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
