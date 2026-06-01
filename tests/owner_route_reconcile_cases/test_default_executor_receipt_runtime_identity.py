from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.study_transition_receipt_consumption import (
    default_executor_execution_followthrough_receipt_consumption,
    default_executor_execution_receipt_consumption,
)

from tests.owner_route_reconcile_cases.test_default_executor_receipt_consumption import _write_json


def test_default_executor_receipt_consumes_same_work_unit_after_runtime_health_tick(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    current_route = {
        "idempotency_key": "owner-route::current-runtime-health",
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "source_fingerprint": "truth-snapshot::current-runtime-health",
        "runtime_health_epoch": "runtime-health-event-006254-fresh",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::"
            "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
        ),
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006254-fresh",
                "work_unit_fingerprint": (
                    "domain-transition::route_back_same_line::"
                    "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
                ),
                "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
            },
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-006254-fresh",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::"
                "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass"
            ),
            "work_unit_id": "dm002_current_manuscript_methods_model_reporting_and_package_currentness_write_pass",
        },
    }
    execution_route = {
        **current_route,
        "idempotency_key": "owner-route::previous-runtime-health",
        "source_fingerprint": "truth-snapshot::previous-runtime-health",
        "runtime_health_epoch": "runtime-health-event-006253-previous",
        "source_refs": {
            **current_route["source_refs"],
            "owner_route_currentness_basis": {
                **current_route["source_refs"]["owner_route_currentness_basis"],
                "runtime_health_epoch": "runtime-health-event-006253-previous",
            },
            "runtime_health_epoch": "runtime-health-event-006253-previous",
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::same-work-unit",
                    "idempotency_key": execution_route["idempotency_key"],
                    "current_owner_route": execution_route,
                    "prompt_contract": {"owner_route": execution_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=current_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt["status"] == "consumed"
    assert receipt["execution_id"] == "execution::dm002::run_quality_repair_batch::same-work-unit"
    assert receipt["consumed_owner_route_idempotency_key"] == current_route["idempotency_key"]


def test_default_executor_receipt_rejects_different_work_unit_after_runtime_health_tick(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    current_route = {
        "idempotency_key": "owner-route::current-work-unit",
        "route_epoch": "truth-event-000024-daa5883571a64a07",
        "truth_epoch": "truth-event-000024-daa5883571a64a07",
        "source_fingerprint": "truth-snapshot::current-work-unit",
        "runtime_health_epoch": "runtime-health-event-006254-fresh",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::current-work-unit",
        "next_owner": "write",
        "owner_reason": "quest_waiting_opl_runtime_owner_route",
        "allowed_actions": ["run_quality_repair_batch"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "owner_reason": "quest_waiting_opl_runtime_owner_route",
                "truth_epoch": "truth-event-000024-daa5883571a64a07",
                "runtime_health_epoch": "runtime-health-event-006254-fresh",
                "work_unit_fingerprint": "domain-transition::route_back_same_line::current-work-unit",
                "work_unit_id": "current-work-unit",
            },
            "study_truth_epoch": "truth-event-000024-daa5883571a64a07",
            "runtime_health_epoch": "runtime-health-event-006254-fresh",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::current-work-unit",
            "work_unit_id": "current-work-unit",
        },
    }
    execution_route = {
        **current_route,
        "idempotency_key": "owner-route::previous-work-unit",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::previous-work-unit",
        "source_refs": {
            **current_route["source_refs"],
            "owner_route_currentness_basis": {
                **current_route["source_refs"]["owner_route_currentness_basis"],
                "work_unit_fingerprint": "domain-transition::route_back_same_line::previous-work-unit",
                "work_unit_id": "previous-work-unit",
            },
            "work_unit_fingerprint": "domain-transition::route_back_same_line::previous-work-unit",
            "work_unit_id": "previous-work-unit",
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": "002-dm-china-us-mortality-attribution",
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "002-dm-china-us-mortality-attribution",
                    "quest_id": "002-dm-china-us-mortality-attribution",
                    "action_type": "run_quality_repair_batch",
                    "execution_status": "executed",
                    "execution_id": "execution::dm002::run_quality_repair_batch::previous-work-unit",
                    "idempotency_key": execution_route["idempotency_key"],
                    "current_owner_route": execution_route,
                    "prompt_contract": {"owner_route": execution_route},
                    "owner_result": {
                        "status": "executed",
                        "ok": True,
                        "repair_execution_evidence": {
                            "status": "progress_delta_candidate",
                            "changed_artifact_refs": [
                                {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                            ],
                        },
                        "quality_authorized": False,
                        "submission_authorized": False,
                        "current_package_write_authorized": False,
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_receipt_consumption(
        study_root=study_root,
        owner_route=current_route,
        actions=[{"action_type": "run_quality_repair_batch"}],
    )

    assert receipt == {}


def test_specificity_followthrough_receipt_rejects_different_work_unit(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    current_route = {
        "idempotency_key": "owner-route::dm003::current-package-freshness",
        "route_epoch": "truth-event-dm003-specificity",
        "truth_epoch": "truth-event-dm003-specificity",
        "source_fingerprint": "truth-snapshot::dm003-specificity",
        "runtime_health_epoch": "runtime-health-dm003-specificity",
        "work_unit_fingerprint": "gate-replay-route-back::finalize::current-submission-refresh",
        "next_owner": "artifact_os",
        "owner_reason": "current_package_freshness_required",
        "allowed_actions": ["current_package_freshness_required"],
        "source_refs": {
            "owner_route_currentness_basis": {
                "owner_reason": "current_package_freshness_required",
                "truth_epoch": "truth-event-dm003-specificity",
                "runtime_health_epoch": "runtime-health-dm003-specificity",
                "work_unit_fingerprint": "gate-replay-route-back::finalize::current-submission-refresh",
                "work_unit_id": "submission_minimal_refresh",
            },
            "study_truth_epoch": "truth-event-dm003-specificity",
            "runtime_health_epoch": "runtime-health-dm003-specificity",
            "work_unit_fingerprint": "gate-replay-route-back::finalize::current-submission-refresh",
            "work_unit_id": "submission_minimal_refresh",
            "blocked_reason": "current_package_freshness_required",
        },
    }
    execution_route = {
        **current_route,
        "idempotency_key": "owner-route::dm003::specificity-previous",
        "work_unit_fingerprint": "gate-replay-route-back::finalize::previous-submission-refresh",
        "next_owner": "publication_gate",
        "owner_reason": "publication_gate_specificity_required",
        "allowed_actions": ["publication_gate_specificity_required"],
        "source_refs": {
            **current_route["source_refs"],
            "owner_route_currentness_basis": {
                **current_route["source_refs"]["owner_route_currentness_basis"],
                "owner_reason": "publication_gate_specificity_required",
                "work_unit_fingerprint": "gate-replay-route-back::finalize::previous-submission-refresh",
            },
            "work_unit_fingerprint": "gate-replay-route-back::finalize::previous-submission-refresh",
            "blocked_reason": "publication_gate_specificity_required",
        },
    }
    _write_json(
        study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json",
        {
            "surface": "default_executor_dispatch_execution_study_latest",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "executed_count": 1,
            "blocked_count": 0,
            "executions": [
                {
                    "surface": "default_executor_dispatch_execution",
                    "schema_version": 1,
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "publication_gate_specificity_required",
                    "execution_status": "executed",
                    "execution_id": "execution::dm003::publication_gate_specificity_required::previous-work-unit",
                    "idempotency_key": execution_route["idempotency_key"],
                    "current_owner_route": execution_route,
                    "prompt_contract": {"owner_route": execution_route},
                    "owner_result": {
                        "status": "blocked",
                        "report_json": str(study_root / "runtime" / "specificity-report.json"),
                        "publication_eval": {
                            "eval_id": "publication-eval::dm003::specificity",
                            "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
                        },
                    },
                }
            ],
        },
    )

    receipt = default_executor_execution_followthrough_receipt_consumption(
        study_root=study_root,
        owner_route=current_route,
        actions=[{"action_type": "current_package_freshness_required"}],
    )

    assert receipt == {}
